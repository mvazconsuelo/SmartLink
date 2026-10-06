#!/usr/bin/env bash
# 01 · K3s — tools, Helm and K3s (pinned versions, Secrets encrypted at rest).
# Usage: ./scripts/01-k3s.sh        Idempotent: does not reinstall what exists.
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
load_config
K3S_VERSION="$(version k3s)"
HELM_VERSION="$(version helm)"

banner "01" "K3s" "Lightweight Kubernetes on this VM"
need_sudo "to install packages and K3s"

step "Tools (git, curl, jq)"
if command -v apt-get >/dev/null; then
  sudo apt-get update -qq && sudo apt-get install -y -qq git curl jq >/dev/null
  ok "installed"
else
  for c in git curl jq; do command -v "$c" >/dev/null || fail "Missing '$c': install it with your distro's package manager"; done
  ok "present"
fi

step "Helm $HELM_VERSION"
# Only 02-argocd.sh uses it, to install Argo CD the first time; after that
# Argo CD renders the charts by itself.
if command -v helm >/dev/null && [[ "$(helm version --short)" == "$HELM_VERSION"* ]]; then
  ok "already installed"
else
  case "$(uname -m)" in x86_64) arch=amd64 ;; aarch64|arm64) arch=arm64 ;; *) fail "Unsupported architecture: $(uname -m)" ;; esac
  curl -fsSL "https://get.helm.sh/helm-${HELM_VERSION}-linux-${arch}.tar.gz" | tar -xz -C /tmp "linux-${arch}/helm"
  sudo install -m 0755 "/tmp/linux-${arch}/helm" /usr/local/bin/helm && rm -rf "/tmp/linux-${arch}"
  ok "installed ($(helm version --short))"
fi

step "K3s $K3S_VERSION"
if command -v k3s >/dev/null; then
  ok "already installed: $(k3s --version | head -1 | awk '{print $3}')"
else
  curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="$K3S_VERSION" INSTALL_K3S_EXEC="--secrets-encryption" sh - >/dev/null
  ok "installed, with --secrets-encryption"
fi
wait_for "node Ready" 180 bash -c 'sudo k3s kubectl get nodes | grep -q " Ready"'

step "Shortcuts (k = kubectl, v = vault)"
install_shortcuts && ok "added to ~/.bashrc: available in every new shell"

step "Firewall"
if command -v ufw >/dev/null && sudo ufw status | grep -q "Status: active"; then
  sudo ufw allow 80/tcp >/dev/null && ok "port 80 open"
else
  info "ufw inactive: nothing to do"
fi

next "./scripts/02-argocd.sh"
