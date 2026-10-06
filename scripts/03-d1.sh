#!/usr/bin/env bash
# 03 · Cloudflare D1 — creates the "smartlink" database if missing and saves its
# ID in config.env. The schema is applied by the migrations in CI, not here.
# Usage: ./scripts/03-d1.sh     (asks for the Cloudflare token; the Account ID is derived or asked)
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
load_config
NAME="smartlink"

banner "03" "Cloudflare D1" "SmartLink's database"

step "Credential"
TOKEN="$(cf_token)"
cf() { curl -sS -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" "$@"; }

step "Account"
if [[ -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]]; then
  # The accounts the token can reach: if there is exactly one, that's it.
  ids="$(cf https://api.cloudflare.com/client/v4/accounts | jq -r '.result[]?.id' 2>/dev/null || true)"
  if [[ -n "$ids" && "$(wc -l <<<"$ids")" -eq 1 ]]; then
    CLOUDFLARE_ACCOUNT_ID="$ids"; save_config CLOUDFLARE_ACCOUNT_ID "$ids"
  else
    ask_value CLOUDFLARE_ACCOUNT_ID "Cloudflare Account ID (it is in the URL: dash.cloudflare.com/<ID>)"
  fi
fi
ok "Account ID: $CLOUDFLARE_ACCOUNT_ID"
API="https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/d1/database"

step "Database '$NAME'"
resp="$(cf "${API}?name=${NAME}")"
[[ "$(jq -r .success <<<"$resp")" == true ]] || fail "Cloudflare API: $(jq -c .errors <<<"$resp")"
id="$(jq -r --arg n "$NAME" '.result[] | select(.name == $n) | .uuid' <<<"$resp")"
if [[ -n "$id" ]]; then
  ok "already exists"
else
  resp="$(cf -X POST -d "{\"name\":\"${NAME}\"}" "$API")"
  [[ "$(jq -r .success <<<"$resp")" == true ]] || fail "Could not create it: $(jq -c .errors <<<"$resp")"
  id="$(jq -r .result.uuid <<<"$resp")"
  ok "created"
fi

save_config D1_DATABASE_ID "$id"
ok "D1_DATABASE_ID=$id → saved in scripts/config.env"

next "./scripts/04-vault.sh"
