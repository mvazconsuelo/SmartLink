🌐 [Leer en español](../es/labs/06-argocd.md) · 📖 [Docs index](../README.md)

# Lab 06 — Argo CD

**Goal:** Make the cluster follow Git, without CI touching it.

## Idea

Argo CD runs **inside** the cluster, reads Git and makes the cluster match what Git says. CI only writes to Git: it never needs cluster credentials.

## How it works

```text
scripts/02-argocd.sh ─► smartlink-root ─► argocd · smartlink-backend · smartlink-frontend · vault · vault-secrets-operator · loki · alloy · grafana
```

| Term | Meaning |
| --- | --- |
| Desired / live state | What Git says / what is in the cluster |
| OutOfSync | They differ |
| Sync | Apply Git to the cluster |
| Self-heal | Revert manual changes automatically |

The root (`smartlink-root`) is created by `scripts/02-argocd.sh` and points to `deploy/root/`, with the repo URL and branch as values: no file contains your URL. There, an **ApplicationSet** creates **one Application per folder** in `deploy/components/` (folder name = Application = namespace). Adding a component means adding a folder. Repo access depends on the mode: public over HTTPS, no credential; private over SSH, with a read-only deploy key.

**Its own AppProject.** The Applications use the `smartlink` project (`deploy/root/templates/project.yaml`), not `default`: only this repo and the official chart repos, and only SmartLink's namespaces. The root stays in `default` because it is the one that creates the project.

**Argo CD manages itself.** The `argocd` Application uses the `deploy/components/argocd/` folder (official `argo-cd` chart as a dependency + its values); the script installed exactly the same thing. Upgrade = change the version in its `Chart.yaml` and commit. It uses `prune: false`: it never deletes itself.

> [!WARNING]
> **If an upgrade breaks Argo CD**
>
> It cannot fix itself. `git revert` the commit, `git pull` on the VM and run `./scripts/02-argocd.sh` (break-glass).

## Do it

Open the UI: `http://argocd.<ip>.nip.io`, user `admin` (password: `./scripts/install.sh access`).

Commit `replicas: 3` in `deploy/components/smartlink-backend/values.yaml`: in about 3 minutes there are 3 pods, without a single `kubectl`.

## Break it

- Private repo: delete the deploy key in GitHub → `authentication required`. What is running **keeps running**: the cluster is frozen, not broken.
- [💥 GitOps drift](../break.md#3-gitops-drift)

## Key points

- Deploy = commit.
- Git is the only source of truth.

⬅️ [05 — Install scripts](05-scripts.md) · 📚 [All labs](../README.md#labs) · ➡️ [07 — Vault + VSO](07-vault.md)