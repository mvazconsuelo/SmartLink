🌐 [Leer en español](../es/labs/01-application.md) · 📖 [Docs index](../README.md)

# Lab 01 — The application

**Goal:** Understand what gets deployed and how it behaves when something is missing.

## Idea

A URL shortener: `http://<host>/promo` redirects and counts the click. **FastAPI** has all the logic and is the only one that talks to **D1**. **Streamlit** is just the UI. The API stores nothing locally, so it can run 2 replicas and restart without losing data.

## How it works

```text
browser ─► /app ─► Streamlit ─► FastAPI ─► D1 (Cloudflare REST API)
browser ─► /{code} ──────────► FastAPI ─► 302 to the target
```

| Route | What it does |
| --- | --- |
| `POST /auth/register`, `/auth/login` | Return a JWT |
| `POST /shorten` | Creates a link (optional alias and expiration) |
| `GET /urls`, `/urls/{code}`, `/stats` | The user's links and stats |
| `GET /{code}` | `302`; `404` if it does not exist; `410` if it expired |
| `GET /health` | Process alive; does not query D1 |

| Decision | Why |
| --- | --- |
| `302`, not `301` | The browser caches a 301 and later clicks would never reach the API |
| D1 not answering → `503`; SQL rejected → `500` | Separates "the dependency is down" from "there is a bug" |
| Missing configuration → it does not start | A clear error beats a misconfigured app |

The tests run on every PR, with an in-memory database that applies the real migrations.

## Do it

```bash
H=http://<vm-ip>
TOKEN=$(curl -s -X POST $H/auth/register -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo-password"}' | jq -r .access_token)
curl -s -X POST $H/shorten -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"original_url":"https://example.com","custom_alias":"promo"}'
curl -si $H/promo | head -1      # HTTP/1.1 302 Found
```

## Break it

In a PR, change the redirect to `301` in `backend/app/main.py`. The `test` job fails and no image is built.

For a failure in the cluster: [💥 CrashLoopBackOff](../break.md#2-crashloopbackoff).

## Key points

- The app fails loudly at startup and degrades gracefully at runtime.
- Tests are the first barrier.

⬅️ [All labs](../README.md#labs) · ➡️ [02 — Cloudflare D1](02-d1.md)