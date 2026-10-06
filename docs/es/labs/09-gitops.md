🌐 [Read in English](../../labs/09-gitops.md) · 📖 [Índice](../README.md)

# Lab 09 — GitOps

**Objetivo:** Seguir un cambio de punta a punta y detectar lo que no pasa por Git.

## Idea

`deploy/` es el estado deseado del cluster. Cuando CI cambia `deploy/components/smartlink-*/values.yaml` no despliega: **cambia lo deseado**, y Argo CD lo aplica.

## Cómo funciona

```yaml
# deploy/components/smartlink-backend/values.yaml — lo único que cambia en un deploy
# (lo mismo en smartlink-frontend/values.yaml)
image:
  repository: ghcr.io/<dueño>/smartlink-api   # CI, desde el dueño del repo
  tag: "abc1234"                              # CI, SHA del commit
```

```text
push ─► CI ─► commit en deploy/ ─► Argo CD (cada ~3 min) ─► K3s ─► pull de GHCR
```

## Hacelo

Cambiá el título en `frontend/app.py` y pusheá. Seguilo:
1. *Actions*;
2. commit de deploy;
3. Argo CD `Synced` con ese commit;
4. pods nuevos;
5. el cambio en `/app`.

## Rompelo

[💥 GitOps drift](../break.md#3-gitops-drift): un `kubectl scale` deja la app `OutOfSync`. Las Applications `smartlink-backend` y `smartlink-frontend` tienen `selfHeal: false` a propósito, para que el drift se vea. Con `selfHeal: true`, Argo CD lo revierte solo.

## Clave

- Un cambio manual no es más rápido: es un cambio que Git no conoce.
- `selfHeal` decide si el drift se muestra o se corrige.

⬅️ [08 — GitHub Actions + GHCR](08-github-actions.md) · 📚 [Todos los labs](../README.md#labs) · ➡️ [10 — DNS & Ingress](10-dns-ingress.md)