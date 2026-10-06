🌐 [Read in English](../../labs/08-github-actions.md) · 📖 [Índice](../README.md)

# Lab 08 — GitHub Actions + GHCR

**Objetivo:** Convertir cada commit en una imagen desplegable y avisarle a GitOps.

## Idea

CI prueba, construye, publica, migra y **escribe en Git**. El deploy lo hace Argo CD. CI nunca toca el cluster.

## Cómo funciona

| Job | Cuándo | Qué hace |
| --- | --- | --- |
| `test` | Siempre | `ruff` + `pytest` |
| `build` | `main` | Imágenes amd64 + arm64 → `ghcr.io/<dueño>/smartlink-*:<sha7>` |
| `migrate` | `main` | Migraciones D1 |
| `gitops` | `main` | Commit `deploy: smartlink <sha7>` en `deploy/components/smartlink-{backend,frontend}/values.yaml` |
| `release` | Tag `vX.Y.Z` | Agrega el tag `X.Y.Z` a la imagen ya construida |

- **SHA para desplegar, semver para personas.** Nunca `latest`.
- **El release no reconstruye:** publica exactamente lo que se probó.
- **Cada job depende del anterior:** si `migrate` falla, no hay deploy.

## Hacelo

- *Actions › ci*: los 4 jobs en verde.
- *Packages*: el tag `<sha7>`, con dos arquitecturas.
- `main`: el commit de deploy de `github-actions[bot]`.

Release: `git tag v1.0.0 && git push origin v1.0.0`. En GHCR, la imagen queda con los dos tags y el mismo digest.

## Rompelo

Borrá el secret `CLOUDFLARE_API_TOKEN` y corré *ci*:
- `build` pasa;
- `migrate` falla, diciendo qué secret falta;
- `gitops` no corre;
- el cluster sigue con la versión anterior.

Ver también: [💥 Bad release](../break.md#6-bad-release).

## Clave

- Un pipeline es una cadena: el eslabón roto frena lo que sigue.
- CI produce artefactos y cambia Git. Nada más.

⬅️ [07 — Vault + VSO](07-vault.md) · 📚 [Todos los labs](../README.md#labs) · ➡️ [09 — GitOps](09-gitops.md)