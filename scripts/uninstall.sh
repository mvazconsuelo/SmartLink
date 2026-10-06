#!/usr/bin/env bash
# SmartLink — uninstall. Detects where it runs:
#   macOS          deletes the Multipass VM with everything in it
#   Linux (the VM) uninstalls K3s (and everything inside it), Helm and the config
# Usage: ./scripts/uninstall.sh    Asks for confirmation. Does not touch Cloudflare or GitHub.
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
VM="smartlink"

confirm() {  # confirm "what gets deleted" — you have to type "delete"
  local a
  warn "$1"
  printf "    Type 'delete' to confirm: " >/dev/tty; read -r a </dev/tty
  [[ "$a" == delete ]] || fail "Cancelled: nothing was deleted"
}

banner "✖" "Uninstall" "SmartLink from this machine"

if [[ "$(uname -s)" == Darwin ]]; then
  confirm "Deletes the VM '$VM' with everything in it: K3s, Argo CD, Vault and its secrets, logs."
  step "VM '$VM'"
  if command -v multipass >/dev/null && multipass info "$VM" >/dev/null 2>&1; then
    multipass delete --purge "$VM" && ok "deleted"
  else
    ok "no VM found"
  fi
  step "Configuration"
  rm -f "$CONFIG_FILE" && ok "scripts/config.env"
  if command -v multipass >/dev/null; then
    step "Multipass"
    printf '    Remove Multipass too (app + its data)? [y/N] ' >/dev/tty; read -r yn </dev/tty
    if [[ "$yn" =~ ^[yY] ]]; then
      warn "brew will show 'Password:' → it is your Mac's password (the login one)"
      HOMEBREW_NO_AUTO_UPDATE=1 brew uninstall --zap --cask multipass && ok "Multipass removed"
    else
      info "kept. To remove it later: brew uninstall --zap --cask multipass"
    fi
  fi
else
  confirm "Deletes K3s with everything inside it (Argo CD, Vault and its secrets, SmartLink, logs), the deploy key and config.env."
  need_sudo "to uninstall K3s"
  step "K3s"
  if [[ -x /usr/local/bin/k3s-uninstall.sh ]]; then
    sudo /usr/local/bin/k3s-uninstall.sh >/dev/null 2>&1 && ok "uninstalled (including /etc/rancher/k3s and the volumes)"
  else
    ok "not installed"
  fi
  step "Everything else"
  if [[ -f /usr/local/bin/helm ]]; then sudo rm -f /usr/local/bin/helm && ok "helm"; fi
  if command -v ufw >/dev/null && sudo ufw status | grep -q "^80/tcp"; then
    sudo ufw delete allow 80/tcp >/dev/null && ok "port 80 closed"
  fi
  rm -rf "$HOME/.smartlink" && ok "$HOME/.smartlink (deploy key, Vault init)"
  rm -f "$CONFIG_FILE" && ok "scripts/config.env"
fi

cat <<EOF

  Still outside this machine (delete it by hand if you no longer need it):
    · Cloudflare:        the D1 database "smartlink" and the API token
    · GitHub:            the "argocd" deploy key, the Actions secret and variable
    · Password manager:  unseal key, root token and Grafana password (no longer valid)

EOF
