🌐 [Leer en español](../es/labs/12-rollback.md) · 📖 [Docs index](../README.md)

# Lab 12 — Rollback

**Goal:** Roll back fast, without leaving Git and the cluster disagreeing.

## Idea

What runs is what Git says. Rolling back = `git revert`. A `kubectl rollout undo` only lasts until Argo CD applies Git again.

## How it works

| Revert | What happens |
| --- | --- |
| A deploy commit (`deploy: smartlink <sha>`) | No CI: Argo CD deploys the previous image, which already exists. **The fastest** |
| A code commit | CI builds a new image without the bug. Slower |

> [!WARNING]
> **The database does not roll back**
>
> Reverting the app does not revert the migrations. It works because they are additive: the previous version ignores the new columns.

## Do it

1. **Deploy a bug:** in `frontend/app.py`, change `/stats` to `/statz`. CI passes, because the frontend has no tests, and the dashboard shows `HTTP 404`.
2. **Revert the deploy** (in a clone of your repo):

```bash
git log --oneline -- deploy/components | head -3   # deploy: smartlink <bad-sha>
git revert --no-edit <hash> && git push
```

In about 3 minutes the dashboard is back.

## Break it

With the bad version, try `k -n smartlink-frontend rollout undo deploy/smartlink-frontend`. Argo CD marks it `OutOfSync`. Here `selfHeal` is off (on purpose, see [Lab 09](09-gitops.md)), so it stays that way until you press *Sync*, which brings the bad version back. With `selfHeal: true` it would go back by itself.

## Key points

- A rollback in GitOps is a commit: traceable and reversible.
- Additive migrations make the app rollback safe.

⬅️ [11 — Observability](11-observability.md) · 📚 [All labs](../README.md#labs) · ➡️ [💥 Break the Platform](../break.md)