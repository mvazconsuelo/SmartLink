#!/usr/bin/env bash
# 04 · Vault — Argo CD installed it, but it starts sealed and empty.
#   ./scripts/04-vault.sh          first time: init → unseal → configure → secrets
#   ./scripts/04-vault.sh unseal   after every VM restart
#   ./scripts/04-vault.sh secrets  reload the app secrets
#   ./scripts/04-vault.sh configure re-apply policies and roles (e.g. after a namespace change)
# Reads what 03-d1.sh saved; asks for the Cloudflare token.
# Unseal key and root token: ~/.smartlink/vault-init.json (600, outside the repo)
# until install.sh shows them and you save them in your password manager.
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
load_config
INIT_FILE="${VAULT_INIT_FILE:-$HOME/.smartlink/vault-init.json}"
MODE="${1:-all}"

status() { k -n vault exec vault-0 -- vault status -format=json 2>/dev/null || true; }

# Runs a script inside the pod with the root token read from stdin:
# it never shows up in a command line, file or shell history.
ROOT_TOKEN=""   # asked once per run; lives only in memory
as_root() {
  if [[ -z "$ROOT_TOKEN" ]]; then
    [[ -f "$INIT_FILE" ]] && ROOT_TOKEN="$(jq -r .root_token "$INIT_FILE")"
    [[ -n "$ROOT_TOKEN" ]] || ROOT_TOKEN="$(ask_secret "Vault root token" "memory only, for this run; it stays in your password manager")"
  fi
  { printf '%s\n' "$ROOT_TOKEN"; cat; } | k -n vault exec -i vault-0 -- sh -c 'read -r VAULT_TOKEN; export VAULT_TOKEN; exec sh -s'
}

wait_vault() {
  # shellcheck disable=SC2016 # expanded inside bash -c
  wait_for "pod vault-0 (deployed by Argo CD)" 600 bash -c \
    '[ "$(sudo k3s kubectl -n vault get pod vault-0 -o jsonpath="{.status.containerStatuses[0].started}")" = true ]'
}

init() {
  step "Initialize"
  if [[ "$(status | jq -r .initialized)" == true ]]; then ok "already initialized"; return; fi
  umask 077; mkdir -p "$(dirname "$INIT_FILE")"
  k -n vault exec vault-0 -- vault operator init -key-shares=1 -key-threshold=1 -format=json > "$INIT_FILE"
  ok "unseal key and root token → $INIT_FILE"
  if [[ -n "${SMARTLINK_ALL:-}" ]]; then info "shown at the end, with the rest of your access details"
  else warn "copy them to your password manager: they cannot be recovered"
  fi
}

unseal() {
  step "Unseal"
  if [[ "$(status | jq -r .sealed)" == false ]]; then ok "already unsealed"; return; fi
  local key=""
  [[ -f "$INIT_FILE" ]] && key="$(jq -r '.unseal_keys_b64[0]' "$INIT_FILE")"
  [[ -n "$key" ]] || key="$(ask_secret "Unseal key" "memory only: sent straight to Vault, not stored here")"
  printf '%s' "$key" | k -n vault exec -i vault-0 -- vault write sys/unseal key=- >/dev/null
  [[ "$(status | jq -r .sealed)" == false ]] || fail "still sealed: is the unseal key right?"
  ok "unsealed"
}

configure() {
  step "Configure (KV, Kubernetes auth, policies, roles)"
  as_root <<'SH'
set -e
vault secrets list | grep -q '^secret/' || vault secrets enable -path=secret kv-v2 >/dev/null
vault auth list | grep -q '^kubernetes/' || vault auth enable kubernetes >/dev/null
vault write auth/kubernetes/config kubernetes_host=https://kubernetes.default.svc >/dev/null
printf 'path "secret/data/smartlink/backend" { capabilities = ["read"] }\n' | vault policy write smartlink-backend - >/dev/null
printf 'path "secret/data/grafana" { capabilities = ["read"] }\n' | vault policy write grafana - >/dev/null
vault write auth/kubernetes/role/smartlink-backend bound_service_account_names=smartlink-backend \
  bound_service_account_namespaces=smartlink-backend audience=vault token_policies=smartlink-backend token_ttl=10m >/dev/null
vault write auth/kubernetes/role/grafana bound_service_account_names=grafana \
  bound_service_account_namespaces=grafana audience=vault token_policies=grafana token_ttl=10m >/dev/null
SH
  ok "backend → reads only secret/smartlink/backend"
  ok "grafana → reads only secret/grafana"
}

secrets() {
  step "App secrets"
  if [[ "${1:-}" != force ]] && as_root <<<'vault kv get secret/smartlink/backend' >/dev/null 2>&1; then
    ok "already loaded (to replace them: $0 secrets)"; return
  fi
  require CLOUDFLARE_ACCOUNT_ID "written by 03-d1.sh"
  require D1_DATABASE_ID "written by 03-d1.sh"
  # The app is served on the VM's IP (install.sh saves it; here, in case this runs alone).
  [[ -n "${PUBLIC_URL:-}" ]] || { PUBLIC_URL="http://$(hostname -I | awk '{print $1}')"; save_config PUBLIC_URL "$PUBLIC_URL"; }
  PUBLIC_URL="${PUBLIC_URL%/}"
  local token backend gpass
  token="$(cf_token)"
  backend="$(jq -nc --arg a "$CLOUDFLARE_ACCOUNT_ID" --arg d "$D1_DATABASE_ID" --arg t "$token" \
    --arg u "$PUBLIC_URL" --arg j "$(openssl rand -hex 32)" \
    '{D1_ACCOUNT_ID:$a, D1_DATABASE_ID:$d, D1_API_TOKEN:$t, PUBLIC_BASE_URL:$u, JWT_SECRET:$j, LOG_LEVEL:"INFO"}')"
  # Values travel inside the script through stdin, never as arguments.
  as_root <<SH
vault kv put secret/smartlink/backend - >/dev/null <<'JSON'
${backend}
JSON
SH
  ok "secret/smartlink/backend (JWT_SECRET generated)"
  if ! as_root <<<'vault kv get secret/grafana' >/dev/null 2>&1; then
    gpass="$(openssl rand -base64 24)"
    as_root <<SH
vault kv put secret/grafana - >/dev/null <<'JSON'
$(jq -nc --arg p "$gpass" '{"admin-user":"admin", "admin-password":$p}')
JSON
SH
    ok "secret/grafana"
    # Inside install.sh, the final summary shows it with the rest of the access details.
    [[ -n "${SMARTLINK_ALL:-}" ]] || warn "Grafana password (user admin), save it now: $gpass"
  fi
}

case "$MODE" in
  all)
    banner "04" "Vault" "init → unseal → configure → secrets"
    wait_vault; init; unseal; configure; secrets
    wait_for "Secret smartlink-backend (created by VSO)" 180 sudo k3s kubectl -n smartlink-backend get secret smartlink-backend
    next "in GitHub, Actions › ci › Run workflow" ;;
  unseal)
    banner "04" "Vault" "unseal after a restart"
    wait_vault; unseal; next "nothing: the app keeps running" ;;
  configure)
    banner "04" "Vault" "re-apply policies and roles"
    wait_vault; configure; next "nothing: VSO logs in again on its next refresh" ;;
  secrets)
    banner "04" "Vault" "reload secrets"
    secrets force; next "VSO restarts the backend within 1 min" ;;
  *) sed -n '2,8p' "$0"; exit 1 ;;
esac
