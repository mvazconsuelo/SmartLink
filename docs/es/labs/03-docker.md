🌐 [Read in English](../../labs/03-docker.md) · 📖 [Índice](../README.md)

# Lab 03 — Docker

**Objetivo:** Empaquetar la app como un artefacto inmutable y seguro.

## Idea

La imagen se construye **una vez**, en CI, y corre igual en cualquier nodo. Lleva código y dependencias, **nunca** configuración ni secretos: esos llegan en runtime desde Vault. K3s no construye imágenes, las descarga de GHCR.

## Cómo funciona

| Decisión | Por qué |
| --- | --- |
| `python:3.12-slim`, dependencias antes que el código | Imagen chica; cache de capas |
| Usuario `10001` | No corre como root |
| Filesystem de solo lectura (API) | Nada puede escribirse en el contenedor |
| `amd64` + `arm64` | La VM puede ser x86 o ARM |

## Hacelo

```bash
k -n smartlink-backend exec deploy/smartlink-api -- id           # uid=10001(smartlink)
k -n smartlink-backend exec deploy/smartlink-api -- touch /test  # Read-only file system
```

## Rompelo

Corré la imagen sin configuración:

```bash
k -n smartlink-backend run probe --rm -it --restart=Never \
  --image="$(k -n smartlink-backend get deploy smartlink-api -o jsonpath='{.spec.template.spec.containers[0].image}')"
# ConfigError: missing required environment variable JWT_SECRET
```

Dentro de un Deployment, eso se ve como [💥 CrashLoopBackOff](../break.md#2-crashloopbackoff).

## Clave

- Imagen = código + dependencias. La configuración, afuera.
- La seguridad se verifica en el cluster, no solo en el Dockerfile.

⬅️ [02 — Cloudflare D1 y migraciones](02-d1.md) · 📚 [Todos los labs](../README.md#labs) · ➡️ [04 — K3s](04-k3s.md)