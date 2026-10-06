#!/usr/bin/env bash
# SmartLink — single entry point. Detects where it runs:
#   Linux (the VM)  installs directly
#   macOS           creates an Ubuntu VM with Multipass, copies the repo and installs inside it
#
#   ./scripts/install.sh           guided install, from zero to a working app
#   ./scripts/install.sh unseal    after every VM restart
#   ./scripts/install.sh secrets   reload the app secrets
#   ./scripts/install.sh configure re-apply Vault policies and roles
#   ./scripts/install.sh ghcr      private repo: access to the images (after the first CI run)
#   ./scripts/install.sh access    URLs, users and passwords (asks for the Vault root token)
#   ./scripts/install.sh k ...     kubectl on the cluster, e.g.  k get pods -A
#   ./scripts/install.sh v ...     Vault CLI, e.g.  v status
#   ./scripts/install.sh shell     macOS: open a shell in the VM (k and v ready)
#   ./scripts/install.sh ip        macOS: VM IP (browser: http://<ip>/app)
# Idempotent: if something fails, fix it and run it again. Uninstall: ./scripts/uninstall.sh
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
CMD="${1:-all}"
usage() { sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; }
[[ "$CMD" =~ ^(help|-h|--help)$ ]] && { usage; exit 0; }

# --- macOS: everything happens inside a Multipass VM ------------------------------
if [[ "$(uname -s)" == Darwin ]]; then
  VM="smartlink"
  REPO_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
  vm_ip() { multipass info "$VM" | awk '/IPv4/ {print $2; exit}'; }
  # The repo is copied (not mounted: macOS does not let Multipass read inside
  # Documents) before every command, so the VM always runs your version.
  sync_repo() {
    multipass umount "$VM" >/dev/null 2>&1 || true
    multipass exec "$VM" -- mkdir -p smartlink
    # No macOS metadata (xattrs, ._*): Ubuntu's tar would warn about every file.
    COPYFILE_DISABLE=1 tar -C "$REPO_DIR" --no-xattrs --no-mac-metadata \
        --exclude .venv --exclude site --exclude __pycache__ --exclude .pytest_cache \
        --exclude .ruff_cache --exclude scripts/config.env -czf - . 2>/dev/null \
      | multipass exec "$VM" -- tar --warning=no-unknown-keyword -xzf - -C smartlink \
      || fail "Could not copy the repo to the VM"
  }
  in_vm() { sync_repo; multipass exec "$VM" -- bash -c "cd ~/smartlink && ./scripts/install.sh $1"; }

  [[ "$CMD" == all ]] || command -v multipass >/dev/null || fail "There is no VM yet: run ./scripts/install.sh"
  case "$CMD" in
    shell)  # make sure k and v exist in the VM (also for VMs created before they were added)
            sync_repo
            multipass exec "$VM" -- bash -c 'cd ~/smartlink && source scripts/lib.sh && install_shortcuts'
            exec multipass shell "$VM" ;;
    # Runs inside the VM: your Mac's kubectl and its contexts are never involved.
    k)      shift; exec multipass exec "$VM" -- sudo k3s kubectl "$@" ;;
    v)      shift; exec multipass exec "$VM" -- sudo k3s kubectl -n vault exec -i vault-0 -- vault "$@" ;;
    ip)     vm_ip; exit ;;
    unseal|secrets|configure|ghcr|access) in_vm "$CMD"; exit ;;   # inside the VM
    all) ;;
    *) usage; exit 1 ;;
  esac

  banner "VM" "Multipass" "macOS detected: SmartLink runs in an Ubuntu VM"
  step "Multipass"
  if ! command -v multipass >/dev/null; then
    command -v brew >/dev/null || fail "Install Multipass from https://multipass.run and run this again"
    warn "brew will show 'Password:' → it is your Mac's password (the login one)"
    # reinstall: if brew has it registered but the installer never finished, this fixes it
    HOMEBREW_NO_AUTO_UPDATE=1 brew reinstall --cask multipass || true
    hash -r
  fi
  command -v multipass >/dev/null || fail "Multipass did not install. Try by hand: brew reinstall --cask multipass"
  ok "$(multipass version | head -1)"

  step "VM '$VM'"
  state="$(multipass info "$VM" 2>/dev/null | awk '/^State:/ {print $2}' || true)"
  case "$state" in
    Running) ok "already running" ;;
    Stopped|Suspended) multipass start "$VM" && ok "started" ;;
    "") info "creating it (1-2 min the first time)"
        # Right after install, multipassd takes a while to fetch the image list: retry.
        for try in 1 2 3 4 5; do
          multipass launch 24.04 --name "$VM" --cpus 2 --memory 4G --disk 30G && break
          ((try < 5)) || fail "Could not create the VM. Is there Internet access? Try: multipass find"
          info "retry $((try + 1))/5 in 15 s (Multipass is still starting)"
          sleep 15
        done
        ok "created (2 CPU · 4 GB · 30 GB)" ;;
    *) fail "Unexpected state: $state. Try: multipass restart $VM" ;;
  esac

  step "Repo → VM"
  sync_repo && ok "$REPO_DIR → ~/smartlink"

  in_vm all
  info "open a shell in the VM: ./scripts/install.sh shell"
  exit
fi

# --- Linux: the VM ----------------------------------------------------------------
load_config
SLUG="$(repo_slug)"; OWNER="${SLUG%%/*}"
INIT_FILE="$HOME/.smartlink/vault-init.json"
N=7
vm_ip() { hostname -I | awk '{print $1}'; }

# Access details: Argo CD's password comes from its Secret; Grafana's, from Vault
# (with the root token). Unseal key and root token only exist until the end of
# the install; after that they live only in your password manager.
show_access() {  # show_access [quiet] — quiet: no root token, do not ask
  local root="" argo graf="(in your password manager)" ip
  [[ -f "$INIT_FILE" ]] && root="$(jq -r .root_token "$INIT_FILE")"
  [[ -n "$root" || "${1:-}" == quiet ]] || root="$(ask_secret "Vault root token (in your password manager)" "memory only, to read the Grafana password from Vault")"
  argo="$(k -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' 2>/dev/null | base64 -d || true)"
  if [[ -n "$root" ]]; then
    graf="$(printf '%s\n' "$root" | k -n vault exec -i vault-0 -- sh -c \
      'read -r VAULT_TOKEN; export VAULT_TOKEN; vault kv get -field=admin-password secret/grafana' 2>/dev/null || true)"
  fi
  ip="$(vm_ip)"
  cat <<EOF

    ${B}SmartLink${R}   http://${ip}/app
    ${B}API docs${R}    http://${ip}/docs              Swagger (also: /redoc)
    ${B}Argo CD${R}     http://argocd.${ip}.nip.io     admin / ${argo:-(not available)}
    ${B}Grafana${R}     http://grafana.${ip}.nip.io    admin / ${graf:-(not available: right root token? is Vault unsealed?)}
    ${B}Vault${R}       http://vault.${ip}.nip.io      method Token → root token
    ${B}Traefik${R}     http://traefik.${ip}.nip.io    read-only dashboard, no login: routes and services
EOF
  if [[ -f "$INIT_FILE" ]]; then
    cat <<EOF
                unseal key:  $(jq -r '.unseal_keys_b64[0]' "$INIT_FILE")
                root token:  ${root}
EOF
  else
    printf '                unseal key and root token: in your password manager\n'
  fi
  printf '\n'
}

# --- GitHub with a temporary token (optional) -------------------------------------
# Fine-grained, 1 day, this repo only, no access to the code. Lives in memory
# (GH_TOKEN) while the install runs; it is never stored anywhere.
gh_check() {  # gh_check TOKEN → ok if it has the 4 permissions used
  local t="$1" miss=()
  GH_TOKEN="$t" gh api "repos/${SLUG}/actions/workflows" >/dev/null 2>&1        || miss+=("Actions")
  GH_TOKEN="$t" gh api "repos/${SLUG}/keys" >/dev/null 2>&1                     || miss+=("Administration")
  GH_TOKEN="$t" gh api "repos/${SLUG}/actions/secrets/public-key" >/dev/null 2>&1 || miss+=("Secrets")
  GH_TOKEN="$t" gh api "repos/${SLUG}/actions/variables" >/dev/null 2>&1        || miss+=("Variables")
  ((${#miss[@]} == 0)) && return 0
  warn "the token has no access to ${SLUG}, or is missing: ${miss[*]}"
  info "No need for a new one: https://github.com/settings/personal-access-tokens → smartlink-install"
  info "→ Repository permissions: ${miss[*]} → Read and write → Update. Then paste the same token."
  return 1
}

gh_setup() {
  local yn t
  info "With a 1-day GitHub token for this repo only, I set up GitHub for you:"
  info "deploy key, variable, secret, Actions and the first pipeline. Without it, I give you the links."
  printf '    Use it? [Y/n] ' >/dev/tty; read -r yn </dev/tty
  [[ "$yn" =~ ^[nN] ]] && { ok "GitHub by hand: I'll guide you with links"; return 0; }
  if ! command -v gh >/dev/null; then
    need_sudo "to install gh (GitHub CLI)"
    { sudo apt-get update -qq && sudo apt-get install -y -qq gh >/dev/null; } || fail "Could not install gh"
  fi
  printf '\n'
  todo "1. Open this link (name, owner, expiration and permissions come prefilled):"
  link "https://github.com/settings/personal-access-tokens/new?name=smartlink-install&description=SmartLink%20installer&target_name=${OWNER}&expires_in=1&actions=write&administration=write&secrets=write&actions_variables=write"
  todo "2. ${B}Repository access${R} section — the one thing you must change by hand:"
  todo "   ( ) Public repositories   ( ) All repositories   (•) ${B}Only select repositories${R}"
  todo "   → in 'Select repositories', pick ${B}${SLUG}${R}"
  todo "   Why: with any other option the token would reach ALL your repos."
  todo "3. ${B}Permissions${R} section (it appears once a repository is selected) → Repository permissions:"
  todo "   Actions · Administration · Secrets · Variables  →  Read and write   (prefilled: just check)"
  todo "   Metadata → Read-only (GitHub adds it). Everything else → No access, Contents included:"
  todo "   the token cannot touch your code."
  todo "4. Expiration: 1 day (prefilled)  →  ${B}Generate token${R}"
  todo "5. Paste it here (starts with github_pat_; no need to save it, it expires tomorrow)"
  until [[ -n "${GH_TOKEN:-}" ]]; do
    t="$(ask_secret "GitHub token (fine-grained, 1 day)" "memory only, for this run; it expires tomorrow anyway")"
    if gh_check "$t"; then GH_TOKEN="$t"; ok "token valid for ${SLUG}"; fi
  done
  export GH_TOKEN GH_PROMPT_DISABLED=1
}

gh_first_deploy() {
  local id="" start
  printf '%s' "$CLOUDFLARE_API_TOKEN" | gh secret set CLOUDFLARE_API_TOKEN -R "$SLUG" >/dev/null && ok "secret CLOUDFLARE_API_TOKEN"
  gh variable set CLOUDFLARE_ACCOUNT_ID -R "$SLUG" -b "$CLOUDFLARE_ACCOUNT_ID" >/dev/null && ok "variable CLOUDFLARE_ACCOUNT_ID"
  gh api -X PUT "repos/${SLUG}/actions/permissions" -F enabled=true -f allowed_actions=all >/dev/null && ok "Actions enabled"
  gh workflow enable ci.yaml -R "$SLUG" >/dev/null 2>&1 || true   # a fork starts with workflows disabled
  start="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  gh workflow run ci.yaml -R "$SLUG" --ref "${REVISION:-main}" >/dev/null && ok "pipeline started"
  for _ in $(seq 20); do
    id="$(gh run list -R "$SLUG" -w ci.yaml -e workflow_dispatch -L 1 --json databaseId,createdAt \
          -q ".[] | select(.createdAt >= \"$start\") | .databaseId")"
    [[ -n "$id" ]] && break; sleep 3
  done
  [[ -n "$id" ]] || fail "Could not find the CI run: check https://github.com/${SLUG}/actions"
  info "https://github.com/${SLUG}/actions/runs/${id}   (test → build → migrate → gitops, ~5-10 min)"
  if ! gh run watch "$id" -R "$SLUG" --exit-status --interval 15; then
    gh run view "$id" -R "$SLUG" --log-failed 2>/dev/null | tail -25
    fail "CI failed (error above). Fix it and run ./scripts/install.sh again"
  fi
  ok "CI finished successfully"
}

# The repo Argo CD will follow and CI will configure: detected from the clone,
# confirmed by you once (a clone of someone else's repo would point there).
confirm_repo() {
  local yn r
  [[ -n "${REPO_SLUG:-}" ]] && return 0
  info "Detected from this clone (git remote origin): ${B}${SLUG}${R}"
  info "Argo CD will deploy from it and CI will run there: it must be YOUR repo (your fork or copy)."
  printf '    Is %s your repo? [Y/n] ' "$SLUG" >/dev/tty; read -r yn </dev/tty
  if [[ "$yn" =~ ^[nN] ]]; then
    printf '    Your repo (owner/name, e.g. your-user/SmartLink): ' >/dev/tty; read -r r </dev/tty
    [[ "$r" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || fail "Not a valid owner/name: $r"
    SLUG="$r"; OWNER="${SLUG%%/*}"
    warn "Push this code to ${SLUG} first: Argo CD and CI use what is on GitHub"
  fi
  REPO_SLUG="$SLUG"; save_config REPO_SLUG "$SLUG"; export REPO_SLUG
  ok "repo: ${SLUG}"
}

guided_install() {
  banner "SmartLink" "Guided install" "Step by step. If you stop, run it again: it resumes where it left off."
  confirm_repo
  cat <<EOF

    Keep these open in your browser:
      · GitHub      (your repo: ${SLUG})
      · Cloudflare  https://dash.cloudflare.com
    And your password manager at hand. Time: ~20 minutes.
EOF
  pause

  # 1 · Cloudflare -----------------------------------------------------------------
  stage 1 $N "Cloudflare: token for the database"
  if [[ -n "${D1_DATABASE_ID:-}" && -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
    ok "the database already exists: the token is asked only if needed"
  else
    todo "Create a token (if you already have one with D1 Edit, use it):"
    link "https://dash.cloudflare.com/profile/api-tokens  →  Create Token › Create Custom Token"
    todo "Permissions: Account · D1 · Edit   ·   Account Resources: Include · your account"
    todo "Create Token → copy it to your password manager (Cloudflare shows it only once)"
    until [[ -n "${CLOUDFLARE_API_TOKEN:-}" ]]; do
      t="$(ask_secret "Paste the token" "memory only now; stored later in Vault (backend) and the GitHub secret (CI)")"
      if curl -fsS -H "Authorization: Bearer $t" https://api.cloudflare.com/client/v4/user/tokens/verify \
           | jq -e '.result.status == "active"' >/dev/null 2>&1; then
        CLOUDFLARE_API_TOKEN="$t"; ok "token valid"
      else
        warn "Cloudflare rejects it: check that it is complete and active"
      fi
    done
  fi
  # Passed to 03 and 04 through the environment; never written to disk.
  export CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN:-}"

  # 2 · GitHub ---------------------------------------------------------------------
  stage 2 $N "GitHub: set it up for you (optional)"
  if [[ -n "${GH_TOKEN:-}" ]]; then ok "GitHub token already loaded"; export GH_TOKEN GH_PROMPT_DISABLED=1
  else gh_setup
  fi

  # The app is served on the VM's IP; the dashboards on <name>.<ip>.nip.io.
  if [[ -z "${PUBLIC_URL:-}" ]]; then save_config PUBLIC_URL "http://$(vm_ip)"; fi

  # 3-5 · Cluster ------------------------------------------------------------------
  stage 3 $N "K3s and Argo CD"
  SMARTLINK_ALL=1 "$SCRIPTS_DIR/01-k3s.sh"
  SMARTLINK_ALL=1 "$SCRIPTS_DIR/02-argocd.sh"
  stage 4 $N "D1 database"
  SMARTLINK_ALL=1 "$SCRIPTS_DIR/03-d1.sh"
  stage 5 $N "Vault and secrets"
  SMARTLINK_ALL=1 "$SCRIPTS_DIR/04-vault.sh"
  load_config

  # 6 · GitHub Actions: first deploy -----------------------------------------------
  stage 6 $N "GitHub Actions: first deploy"
  image() { k -n smartlink-backend get deploy smartlink-api -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null; }
  # The schema is applied by CI (job "migrate"). A new or recreated D1 database is
  # empty even when an image is already deployed, so check D1 itself.
  migrated() {
    [[ -n "${CLOUDFLARE_API_TOKEN:-}" ]] || return 0   # no token at hand: cannot tell, assume yes
    curl -fsS -X POST -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" -H "Content-Type: application/json" \
      "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/d1/database/${D1_DATABASE_ID}/query" \
      -d '{"sql":"SELECT name FROM d1_migrations"}' 2>/dev/null \
      | jq -e '.success and (.result[0].results | length > 0)' >/dev/null 2>&1
  }
  # The image must be YOURS (ghcr.io/<your user>/...): a fork inherits the original author's
  # tag in values.yaml, and that is not a deploy of this repo. CI rewrites it on its first run.
  mine() { [[ "$(image)" == *"/${OWNER,,}/"* ]]; }
  deployed() { local i; i="$(image)"; [[ -n "$i" && "${i##*:}" != 0000000 ]] && mine && migrated; }
  if ! deployed; then
    if [[ -n "$(image)" && "$(image)" != *:0000000 ]] && ! mine; then
      info "the image in the repo is not yours ($(image)): CI will build and publish yours"
    elif [[ "$(image)" != *:0000000 && -n "$(image)" ]]; then
      warn "the D1 database has no schema yet: CI applies the migrations"
    fi
    if [[ -n "${GH_TOKEN:-}" ]]; then
      [[ -n "${CLOUDFLARE_API_TOKEN:-}" ]] || CLOUDFLARE_API_TOKEN="$(ask_secret "Cloudflare token (for the CI secret)" "sent to GitHub as an encrypted Actions secret; not stored here")"
      gh_first_deploy
      info "Argo CD deploys the new version (up to ~3 min)"
    else
      todo "1. Variable:  Name CLOUDFLARE_ACCOUNT_ID  ·  Value ${CLOUDFLARE_ACCOUNT_ID}"
      link "https://github.com/${SLUG}/settings/variables/actions/new"
      todo "2. Secret:    Name CLOUDFLARE_API_TOKEN   ·  Value the Cloudflare token (stage 1)"
      link "https://github.com/${SLUG}/settings/secrets/actions/new"
      todo "3. Enable Actions: 'Allow all actions' → Save"
      link "https://github.com/${SLUG}/settings/actions"
      todo "4. Run the pipeline: Run workflow → main"
      link "https://github.com/${SLUG}/actions/workflows/ci.yaml"
      pause "Press Enter once it is running…"
      info "CI: test → build → migrate → gitops (~5-10 min). Then Argo CD deploys by itself."
      info "If a job fails, check it in GitHub, fix it and re-run it: this keeps waiting."
    fi
    wait_for "schema in D1 and new version deployed by Argo CD" 1800 deployed
  fi
  ok "schema in D1 · image: $(image)"

  # 7 · Images and test ------------------------------------------------------------
  stage 7 $N "Image access and test"
  if [[ "$REPO_URL" == git@* ]]; then
    if sudo test -f /etc/rancher/k3s/registries.yaml; then ok "K3s already has access to GHCR"
    else
      info "CI published the images to GHCR (GitHub's registry). Since the repo is private,"
      info "they are private: K3s needs a GitHub token to download them."
      info "It is read-only (read:packages) and stays on the VM (/etc/rancher/k3s/registries.yaml)."
      printf '\n'
      todo "1. Open (the permission comes prefilled):"
      link "https://github.com/settings/tokens/new?scopes=read:packages&description=smartlink-ghcr"
      todo "2. Expiration: whatever you like (90 days is enough for the lab)"
      todo "3. ONLY read:packages checked  →  Generate token"
      todo "4. Copy it (starts with ghp_) to your password manager and paste it here:"
      t="$(ask_secret "GitHub token (classic, read:packages, starts with ghp_)" "stored on this VM in /etc/rancher/k3s/registries.yaml, root-only (600), so K3s can pull")"
      [[ "$t" == ghp_* ]] || warn "it does not start with ghp_: if K3s cannot pull, run ./scripts/install.sh ghcr"
      GHCR_TOKEN="$t" SMARTLINK_ALL=1 "$SCRIPTS_DIR/05-ghcr-auth.sh"
    fi
  else
    todo "Public repo: make both images public (Package settings › Change visibility › Public):"
    link "https://github.com/users/${OWNER}/packages/container/package/smartlink-api"
    link "https://github.com/users/${OWNER}/packages/container/package/smartlink-frontend"
    pause "Press Enter once they are public…"
  fi
  wait_for "backend Running" 600 sudo k3s kubectl -n smartlink-backend rollout status deploy/smartlink-api --timeout=5s
  wait_for "frontend Running" 600 sudo k3s kubectl -n smartlink-frontend rollout status deploy/smartlink-frontend --timeout=5s
  wait_for "GET /health → 200" 120 curl -fsS http://localhost/health

  banner "✔" "SmartLink is running" "Your access details: copy them to your password manager"
  show_access
  if [[ -f "$INIT_FILE" ]]; then
    warn "Vault does not store the unseal key (it is the key to its data): this is the only copy."
    info "You need it after every restart (./scripts/install.sh unseal). If it is lost, Vault"
    info "has to be reset from scratch and the secrets reloaded; the app data (D1) is not affected."
    until [[ "${a:-}" == saved ]]; do
      printf "    Type 'saved' once they are in your password manager: " >/dev/tty; read -r a </dev/tty
    done
    rm -f "$INIT_FILE"; ok "Vault keys deleted from the VM: they now live only in your password manager"
  fi
  cat <<EOF

    Day to day:
      ./scripts/install.sh access    show this again (asks for the root token)
      ./scripts/install.sh unseal    after restarting the VM
      ./scripts/install.sh secrets   change the secrets
      ./scripts/uninstall.sh         delete everything

EOF
}

case "$CMD" in
  all)     guided_install ;;
  unseal)  "$SCRIPTS_DIR/04-vault.sh" unseal ;;
  secrets) "$SCRIPTS_DIR/04-vault.sh" secrets ;;
  configure) "$SCRIPTS_DIR/04-vault.sh" configure ;;
  ghcr)    "$SCRIPTS_DIR/05-ghcr-auth.sh" ;;
  access)  show_access ;;
  k)       shift; exec sudo k3s kubectl "$@" ;;
  v)       shift; exec sudo k3s kubectl -n vault exec -i vault-0 -- vault "$@" ;;
  shell|ip) fail "'$CMD' is for macOS: you are already in the VM" ;;
  *) usage; exit 1 ;;
esac
