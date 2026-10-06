🌐 [Leer en español](../es/labs/09-gitops.md) · 📖 [Docs index](../README.md)

# Lab 09 — GitOps

**Goal:** Follow a change end to end and spot what does not go through Git.

## Idea

`deploy/` is the desired state of the cluster. When CI changes `deploy/components/smartlink-*/values.yaml` it does not deploy: **it changes what is desired**, and Argo CD applies it.

## How it works

```yaml
# deploy/components/smartlink-backend/values.yaml — the only thing a deploy changes
# (same in smartlink-frontend/values.yaml)
image:
  repository: ghcr.io/<owner>/smartlink-api   # CI, from the repo owner
  tag: "abc1234"                              # CI, commit SHA
```

```text
push ─► CI ─► commit in deploy/ ─► Argo CD (every ~3 min) ─► K3s ─► pull from GHCR
```

## Do it

Change the title in `frontend/app.py` and push. Follow it:
1. *Actions*;
2. the deploy commit;
3. Argo CD `Synced` with that commit;
4. new pods;
5. the change in `/app`.

## Break it

[💥 GitOps drift](../break.md#3-gitops-drift): a `kubectl scale` leaves the app `OutOfSync`. The `smartlink-backend` and `smartlink-frontend` Applications have `selfHeal: false` on purpose, so the drift is visible. With `selfHeal: true`, Argo CD reverts it by itself.

## Key points

- A manual change is not faster: it is a change Git does not know about.
- `selfHeal` decides whether drift is shown or corrected.

⬅️ [08 — GitHub Actions + GHCR](08-github-actions.md) · 📚 [All labs](../README.md#labs) · ➡️ [10 — DNS & Ingress](10-dns-ingress.md)