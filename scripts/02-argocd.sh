#!/usr/bin/env bash
# 02 · Argo CD — Argo CD (pinned version), repo access and root Application.
# From here on, Argo CD deploys everything else from Git.
# Usage: ./scripts/02-argocd.sh   Detects the repo from this clone (public or
# private). Private: generates the deploy key and waits until it is in GitHub.
# Upgrade: change the version in deploy/components/argocd/Chart.yaml and commit
# (Argo CD updates itself). This script: bootstrap and break-glass.
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
load_config
REVISION="${REVISION:-main}"
SLUG="$(repo_slug)"
KEY="${SSH_KEY_FILE:-$HOME/.smartlink/argocd-key}"

banner "02" "Argo CD" "GitOps: the cluster follows Git"

step "Repo"
if [[ -z "${REPO_URL:-}" ]]; then
  # Readable over HTTPS without credentials → public.
  if GIT_TERMINAL_PROMPT=0 git ls-remote "https://github.com/${SLUG}.git" >/dev/null 2>&1; then
    REPO_URL="https://github.com/${SLUG}.git"
  else
    REPO_URL="git@github.com:${SLUG}.git"
  fi
  save_config REPO_URL "$REPO_URL"
fi
if [[ "$REPO_URL" == git@* ]]; then
  ok "private: $REPO_URL"
  # Argo CD's own deploy key: read-only, this repo only. Tested without the SSH
  # agent or ~/.ssh/config, so it is never confused with your personal key.
  if [[ ! -f "$KEY" ]]; then
    mkdir -p "$(dirname "$KEY")" && chmod 700 "$(dirname "$KEY")"
    ssh-keygen -q -t ed25519 -N "" -C argocd -f "$KEY"
  fi
  git_ssh="ssh -F /dev/null -i $KEY -o IdentitiesOnly=yes -o IdentityAgent=none -o StrictHostKeyChecking=accept-new"
  # With install.sh's temporary token, the deploy key is added automatically
  # (replacing old "argocd" keys).
  if [[ -n "${GH_TOKEN:-}" ]] && command -v gh >/dev/null \
     && ! GIT_SSH_COMMAND="$git_ssh" git ls-remote "$REPO_URL" >/dev/null 2>&1; then
    gh api "repos/${SLUG}/keys" -q '.[] | select(.title == "argocd") | .id' \
      | while read -r old; do gh api -X DELETE "repos/${SLUG}/keys/${old}" >/dev/null; done
    gh repo deploy-key add "$KEY.pub" -R "$SLUG" -t argocd >/dev/null && ok "deploy key added to GitHub (read-only)"
    for _ in 1 2 3 4 5; do GIT_SSH_COMMAND="$git_ssh" git ls-remote "$REPO_URL" >/dev/null 2>&1 && break; sleep 3; done
  fi
  until GIT_SSH_COMMAND="$git_ssh" git ls-remote "$REPO_URL" >/dev/null 2>&1; do
    warn "Argo CD cannot read the private repo yet: its deploy key is missing in GitHub."
    printf '\n'
    info "1. Open:  https://github.com/${SLUG}/settings/keys/new"
    info "          (your repo › Settings › Deploy keys › Add deploy key)"
    info "2. Title: argocd"
    info "3. Key:   paste this whole line"
    printf '\n      %s\n\n' "$(cat "$KEY.pub")"
    info "4. Leave 'Allow write access' UNCHECKED  →  Add key"
    printf '\n'
    pause "5. Press Enter once it is added…"
  done
  ok "deploy key with read access ($KEY)"
else
  ok "public: $REPO_URL (no credentials)"
fi

step "Argo CD (official chart)"
# The same chart folder as the "argocd" Application, which adopts it
# afterwards: the script installs, Argo CD manages itself.
COMPONENT="$SCRIPTS_DIR/../deploy/components/argocd"
CHART_VERSION="$(awk '$1 == "version:" {v=$2} END {print v}' "$COMPONENT/Chart.yaml")"   # the dependency's (last "version:")
k create namespace argocd --dry-run=client -o yaml | k apply -f - >/dev/null
helm dependency update "$COMPONENT" >/dev/null
helm template argocd "$COMPONENT" --namespace argocd \
  | k apply -n argocd --server-side --force-conflicts -f - >/dev/null
ok "chart argo-cd $CHART_VERSION applied"
for d in argocd-server argocd-repo-server argocd-applicationset-controller argocd-redis; do
  wait_for "$d" 300 sudo k3s kubectl -n argocd rollout status "deploy/$d" --timeout=5s
done
wait_for "argocd-application-controller" 300 sudo k3s kubectl -n argocd rollout status statefulset/argocd-application-controller --timeout=5s

if [[ "$REPO_URL" == git@* ]]; then
  step "Private repo credential"
  k -n argocd create secret generic repo-smartlink \
    --from-literal=type=git --from-literal=url="$REPO_URL" --from-file=sshPrivateKey="$KEY" \
    --dry-run=client -o yaml \
    | k label --local -f - -o yaml argocd.argoproj.io/secret-type=repository \
    | k apply -f - >/dev/null
  ok "Secret repo-smartlink (read-only deploy key)"
fi

step "Root Application"
# Renders the deploy/root chart (ApplicationSet + AppProject) with the repo URL and
# branch as values: no file in the repo contains your URL.
k apply -f - >/dev/null <<YAML
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: smartlink-root
  namespace: argocd
spec:
  project: default
  source:
    repoURL: ${REPO_URL}
    targetRevision: ${REVISION}
    path: deploy/root
    helm:
      valuesObject:
        repoURL: ${REPO_URL}
        revision: ${REVISION}
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
YAML
ok "smartlink-root → $REPO_URL ($REVISION)"
# shellcheck disable=SC2016 # expanded inside bash -c
wait_for "Applications created by the ApplicationSet" 300 bash -c '[ "$(sudo k3s kubectl -n argocd get applications --no-headers | wc -l)" -ge 9 ]'
info "status: k -n argocd get applications"

next "./scripts/03-d1.sh"
