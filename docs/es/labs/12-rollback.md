🌐 [Read in English](../../labs/12-rollback.md) · 📖 [Índice](../README.md)

# Lab 12 — Rollback

**Objetivo:** Volver atrás rápido, sin dejar Git y el cluster en desacuerdo.

## Idea

Lo que corre es lo que dice Git. Volver atrás = `git revert`. Un `kubectl rollout undo` dura hasta que Argo CD vuelve a aplicar Git.

## Cómo funciona

| Revertir | Qué pasa |
| --- | --- |
| Commit de deploy (`deploy: smartlink <sha>`) | Sin CI: Argo CD despliega la imagen anterior, que ya existe. **El más rápido** |
| Commit de código | CI construye una imagen nueva sin el bug. Más lento |

> [!WARNING]
> **La base no vuelve atrás**
>
> Revertir la app no revierte las migraciones. Funciona porque son aditivas: la versión anterior ignora las columnas nuevas.

## Hacelo

1. **Desplegá un bug:** en `frontend/app.py`, cambiá `/stats` por `/statz`. CI pasa, porque el frontend no tiene tests, y el dashboard muestra `HTTP 404`.
2. **Revertí el deploy** (en un clon de tu repo):

```bash
git log --oneline -- deploy/components | head -3   # deploy: smartlink <sha-malo>
git revert --no-edit <hash> && git push
```

En unos 3 minutos el dashboard vuelve.

## Rompelo

Con la versión mala, probá `k -n smartlink-frontend rollout undo deploy/smartlink-frontend`. Argo CD marca `OutOfSync`. Acá `selfHeal` está apagado (a propósito, ver el [Lab 09](09-gitops.md)), así que queda así hasta que toques *Sync*, que trae de vuelta la versión mala. Con `selfHeal: true` volvería sola.

## Clave

- Un rollback en GitOps es un commit: rastreable y reversible.
- Las migraciones aditivas hacen seguro el rollback de la app.

⬅️ [11 — Observabilidad](11-observability.md) · 📚 [Todos los labs](../README.md#labs) · ➡️ [💥 Break the Platform](../break.md)