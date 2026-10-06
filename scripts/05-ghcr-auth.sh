#!/usr/bin/env bash
# 05 · GHCR (private repo only) — read-only credential on the node
# (/etc/rancher/k3s/registries.yaml): it never enters the cluster or Git.
# Usage: ./scripts/05-ghcr-auth.sh   (asks for a classic read:packages token, or reads GHCR_TOKEN)
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
load_config
GITHUB_USER="${GITHUB_USER:-$(repo_slug | cut -d/ -f1)}"

banner "05" "GHCR" "Private images: K3s authenticates to the registry"

step "Credential"
# install.sh asks for it right below its instructions and passes it here.
TOKEN="${GHCR_TOKEN:-}"
[[ -n "$TOKEN" ]] || TOKEN="$(ask_secret "GitHub token (classic, read:packages, starts with ghp_)" "stored on this VM in /etc/rancher/k3s/registries.yaml, root-only (600), so K3s can pull")"
sudo tee /etc/rancher/k3s/registries.yaml >/dev/null <<YAML
configs:
  "ghcr.io":
    auth:
      username: ${GITHUB_USER}
      password: ${TOKEN}
YAML
sudo chmod 600 /etc/rancher/k3s/registries.yaml
ok "/etc/rancher/k3s/registries.yaml (600)"

step "Restart K3s"
sudo systemctl restart k3s
wait_for "node Ready" 120 bash -c 'sudo k3s kubectl get nodes | grep -q " Ready"'
info "pods keep running during the restart"

next "wait ~3 min: k get pods -A | grep smartlink"
