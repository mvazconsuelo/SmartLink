🌐 [Leer en español](../es/labs/07-vault.md) · 📖 [Docs index](../README.md)

# Lab 07 — Vault + VSO

**Goal:** Get secrets from Vault into the pod without them ever passing through Git.

## Idea

The values (tokens, `JWT_SECRET`, IDs) live in **Vault**. **VSO** copies them into a Kubernetes Secret, and the backend reads them as environment variables. Git only says *who* can read *what*; it never contains values.

## How it works

```text
Vault KV ─► VSO (with the backend's identity) ─► Secret smartlink-backend ─► FastAPI
```

| What | Who |
| --- | --- |
| Install Vault and VSO | Argo CD (official charts) |
| Init, unseal, policies, roles, values | A person, once (`scripts/04-vault.sh`) |
| Copy into Kubernetes and restart the backend when something changes | VSO |

**Identity:** VSO authenticates as the `smartlink-backend` ServiceAccount, with a token whose audience is `vault`. The role only accepts that SA in that namespace, and the policy only allows **reading** `secret/data/smartlink/backend`. Grafana uses the same pattern with `secret/grafana`.

**Why init is manual:** it generates the keys that open Vault. If a machine stored them, they would sit next to what they protect.

## Do it

Change a value and watch it propagate:

```bash
v kv patch secret/smartlink/backend LOG_LEVEL=DEBUG
k -n smartlink-backend get pods -w   # within 60 s, VSO updates the Secret and restarts the backend
```

A running pod does **not** see new variables: it needs a restart, and VSO does it.

> [!WARNING]
> **After every restart, Vault starts sealed**
>
> `./scripts/install.sh unseal`. Meanwhile the app keeps running with the last Secret.

## Break it

| Scenario | What it teaches |
| --- | --- |
| [💥 Sealed Vault](../break.md#8-sealed-vault) | The Secret works as a cache |
| [💥 Wrong role](../break.md#9-wrong-role) | Authentication: *who* gets in |
| [💥 Wrong policy](../break.md#10-wrong-policy) | Authorization: *what* it reads |
| [💥 Missing secret](../break.md#11-missing-secret) | A green component can sync something empty |

## Key points

- Git declares relationships; Vault stores values.
- Vault down stops **changes**, not the service.
- Data lives on a `local-path` PVC: if the disk is lost, the secrets are lost.

⬅️ [06 — Argo CD](06-argocd.md) · 📚 [All labs](../README.md#labs) · ➡️ [08 — GitHub Actions + GHCR](08-github-actions.md)