🌐 [Read in English](../../labs/01-application.md) · 📖 [Índice](../README.md)

# Lab 01 — La aplicación

**Objetivo:** Entender qué se despliega y cómo se comporta cuando le falta algo.

## Idea

Un acortador de URLs: `http://<host>/promo` redirige y cuenta el click. **FastAPI** tiene toda la lógica y es el único que habla con **D1**. **Streamlit** es solo la interfaz. La API no guarda nada local, por eso puede tener 2 réplicas y reiniciarse sin perder datos.

## Cómo funciona

```text
navegador ─► /app ─► Streamlit ─► FastAPI ─► D1 (REST API de Cloudflare)
navegador ─► /{code} ──────────► FastAPI ─► 302 al destino
```

| Ruta | Qué hace |
| --- | --- |
| `POST /auth/register`, `/auth/login` | Devuelven un JWT |
| `POST /shorten` | Crea un link (alias y expiración opcionales) |
| `GET /urls`, `/urls/{code}`, `/stats` | Links y estadísticas del usuario |
| `GET /{code}` | `302`; `404` si no existe; `410` si expiró |
| `GET /health` | Proceso vivo; no consulta D1 |

| Decisión | Por qué |
| --- | --- |
| `302`, no `301` | El navegador cachea el 301 y los clicks siguientes no llegarían |
| D1 no responde → `503`; SQL rechazado → `500` | Separa "la dependencia no está" de "hay un bug" |
| Falta configuración → no arranca | Mejor un error claro que una app mal configurada |

Los tests corren en cada PR, con una base en memoria que aplica las migraciones reales.

## Hacelo

```bash
H=http://<ip-vm>
TOKEN=$(curl -s -X POST $H/auth/register -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo-password"}' | jq -r .access_token)
curl -s -X POST $H/shorten -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"original_url":"https://example.com","custom_alias":"promo"}'
curl -si $H/promo | head -1      # HTTP/1.1 302 Found
```

## Rompelo

En un PR, cambiá el redirect a `301` en `backend/app/main.py`. El job `test` falla y no se construye ninguna imagen.

Para una falla en el cluster: [💥 CrashLoopBackOff](../break.md#2-crashloopbackoff).

## Clave

- La app falla fuerte al arrancar y se degrada con elegancia en runtime.
- Los tests son la primera barrera.

⬅️ [Todos los labs](../README.md#labs) · ➡️ [02 — Cloudflare D1](02-d1.md)