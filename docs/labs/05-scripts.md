🌐 [Leer en español](../es/labs/05-scripts.md) · 📖 [Docs index](../README.md)

# Lab 05 — Install scripts

**Goal:** Bring up the base of the platform with repeatable scripts and hand control over to GitOps.

## Idea

The scripts in `scripts/` install **only what GitOps cannot install by itself**: the cluster, Argo CD and the database. Everything else (Vault, VSO, SmartLink, observability) is deployed by Argo CD from Git.

## How it works

| Script | What it does | Why it is not GitOps |
| --- | --- | --- |
| `01-k3s.sh` | Packages, Helm and K3s (pinned versions, encrypted Secrets) | No cluster, no Argo CD |
| `02-argocd.sh` | Argo CD (from `deploy/components/argocd/`), repo credential, root Application | Argo CD cannot install itself. Afterwards it manages itself |
| `03-d1.sh` | Creates the D1 database in Cloudflare | It lives outside the cluster |
| `04-vault.sh` | Init, unseal, policies, roles and secrets | Vault's keys cannot be in Git |
| `05-ghcr-auth.sh` | GHCR credential on the node (private repo only) | It is node configuration, not cluster configuration |

`install.sh` is the entry point: with no arguments it is the **guided install** (7 stages: it runs 01 to 05 and guides you through Cloudflare and GitHub). `unseal`, `secrets`, `configure`, `ghcr` and `access` are the day-to-day shortcuts (`./scripts/install.sh help`).

On **macOS**, `install.sh` creates an Ubuntu VM with Multipass and runs inside it (`shell` and `ip` manage it). `uninstall.sh` uninstalls, also depending on the system. Scripts `01`–`05` refuse to run outside Linux.

There is nothing to configure by hand: they detect the repo from the clone (and ask you to confirm it), ask for what is missing and save it in **`scripts/config.env`** (non-secret values, outside Git). Tokens are asked for at run time, never shown; each prompt says where that secret ends up (Vault, GitHub, or memory only). They share `scripts/lib.sh`, which provides the output format and common functions.

All of them are **idempotent**: they check the state before acting, so running them again breaks nothing.

## Do it

Look at the output of any script: each step says what it did (`✔`) or why it stopped (`✖ ...`).

**Upgrades:**
- **Argo CD** is no longer upgraded with a script: its version lives in Git (`deploy/components/argocd/Chart.yaml`) and changes with a commit ([Lab 06](06-argocd.md)). `02-argocd.sh` stays as *break-glass*.
- **K3s and Helm** are pinned in `deploy/root/values.yaml` (`bootstrap` block). Today `01-k3s.sh` does not upgrade an already installed K3s.

## Break it

Run `./scripts/03-d1.sh` twice: the second time it says `already exists` and shows the same ID. If a script were not idempotent, it would create a second database or fail.

## Key points

- The scripts are the **bootstrap**; after that, everything goes through Git.
- Pinned versions: each chart in its folder's `Chart.yaml`; K3s and Helm in `deploy/root/values.yaml`.

⬅️ [04 — K3s](04-k3s.md) · 📚 [All labs](../README.md#labs) · ➡️ [06 — Argo CD](06-argocd.md)