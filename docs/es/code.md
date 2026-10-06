🌐 [Read in English](../code.md) · 📖 [Índice](README.md)

# 🧩 El código

**Un mapa del código de la aplicación.** Es chico a propósito: el lab trata de la plataforma que lo rodea. Todo lo que figura acá es real y está verificado contra el código fuente.

Convención: cada función y clase pública tiene un docstring de una línea que dice **qué** hace; los comentarios dicen **por qué**.

## Dónde está cada cosa

```text
backend/
├── app/            la API (FastAPI)
├── tests/          sus tests
├── Dockerfile · requirements.txt · requirements-dev.txt
frontend/
├── app.py          el dashboard (Streamlit), en un solo archivo
└── Dockerfile · requirements.txt
migrations/         el schema de D1, un archivo SQL numerado por cada cambio
scripts/            el instalador (ver el Lab 05)
deploy/             lo que despliega Argo CD (ver el Lab 06)
.github/workflows/  ci.yaml (ver el Lab 08)
```

## El backend

Una request baja por tres capas. Solo la última habla con D1.

```text
HTTP        main.py         rutas, códigos de estado, logs
  │
Lógica      auth.py  shortener.py  analytics.py  qr.py
  │
Datos       database.py     el único código que corre SQL contra D1
```

| Módulo | Responsabilidad |
| --- | --- |
| `main.py` | `create_app()` arma la API: las rutas, el log de requests y cómo los errores se vuelven respuestas HTTP |
| `auth.py` | Passwords (PBKDF2) y tokens (JWT). `get_current_user` es la dependencia que protege una ruta |
| `shortener.py` | Crear y resolver links: códigos, alias, palabras reservadas, expiración |
| `analytics.py` | Registrar un click y los números del dashboard |
| `database.py` | La interfaz `Database` y `D1Database`, que habla con la API REST de D1 |
| `config.py` | Lee el entorno. Un valor faltante o inseguro frena la app al arrancar |
| `schemas.py` | Los modelos de request y de respuesta |
| `qr.py` | Dibuja un código QR. No se guarda nada |

Reglas que sigue el código, y por qué:

- **Solo `database.py` corre SQL contra D1.** El resto depende de la interfaz `Database`, así que los tests cambian D1 por un doble en memoria.
- **Que D1 falle no es un bug.** D1 inalcanzable → `DatabaseUnavailable` → `503`. D1 rechaza el SQL → `QueryError` → `500`.
- **Registrar un click puede fallar sin romper la redirección.** El visitante igual llega a donde iba; el click perdido queda en el log.
- **`/health` no consulta D1.** Reiniciar pods no arreglaría una dependencia externa.
- **La redirección es `302`**, nunca `301`: el navegador cachea un `301` y los clicks siguientes no llegarían.
- **`/{code}` se registra al final**, porque coincide con cualquier segmento de path.

## La API

| Método y ruta | Pide token | Responde |
| --- | --- | --- |
| `GET /health` | No | `200` `{"status": "ok"}` |
| `POST /auth/register` | No | `201` un token · `409` el usuario existe · `403` el registro está deshabilitado |
| `POST /auth/login` | No | `200` un token · `401` credenciales incorrectas |
| `POST /shorten` | Sí | `201` el link · `409` alias en uso · `422` alias, URL o expiración inválidos |
| `GET /urls` | Sí | `200` tus links |
| `GET /urls/{code}` | Sí | `200` el link con sus estadísticas · `404` no existe o no es tuyo |
| `GET /urls/{code}/qr` | Sí | `200` un PNG |
| `GET /stats` | Sí | `200` tus totales, clicks por día, links más usados y últimos clicks |
| `GET /{code}` | No | `302` al destino · `404` desconocido · `410` expirado |

Cualquier ruta también puede responder `401` (sin token o inválido), `503` (D1 inalcanzable) o `500`. La versión interactiva, con cada campo, es `http://<ip>/docs`.

## Configuración

`config.py` las lee una sola vez al arrancar. En el cluster llegan todas desde el Secret `smartlink-backend`, que VSO arma a partir de Vault ([Lab 07](labs/07-vault.md)).

| Variable | Obligatoria | Por defecto | Notas |
| --- | --- | --- | --- |
| `JWT_SECRET` | Sí | | Al menos 32 caracteres; la genera el instalador |
| `PUBLIC_BASE_URL` | Sí | | La base de los links cortos y los QR |
| `D1_ACCOUNT_ID`, `D1_DATABASE_ID`, `D1_API_TOKEN` | Sí | | Cómo llegar a D1 |
| `D1_TIMEOUT_SECONDS` | No | `5` | |
| `JWT_TTL_MINUTES` | No | `60` | Cuánto vive un token |
| `ALLOW_REGISTRATION` | No | `true` | `false` cierra el registro |
| `LOG_LEVEL` | No | `INFO` | |

El dashboard tiene una: `API_URL`, la dirección de la API (en el cluster, el Service del backend).

## Los datos

Tres tablas, creadas por las migraciones de `migrations/` ([Lab 02](labs/02-d1.md)). Las fechas son texto UTC, `YYYY-MM-DD HH:MM:SS`.

| Tabla | Columnas |
| --- | --- |
| `users` | `id`, `username` (único), `password_hash`, `created_at` |
| `short_urls` | `id`, `user_id`, `code` (único), `original_url`, `created_at`, `expires_at` (migración 002), `is_active`, `click_count` |
| `click_events` | `id`, `short_url_id`, `clicked_at`, `referrer` (solo el sitio), `user_agent` (cortado a 200 caracteres) |

`is_active` lo lee el estado (`active`, `expired`, `inactive`), pero nada en la API lo pone en `0` todavía.

## Los logs

Una línea por evento, `key=value`, a stdout: `level=INFO logger=smartlink.api msg=…`. Los que usan los labs:

| Mensaje | Cuándo |
| --- | --- |
| `request method=… path=… status=… duration_ms=…` | Cada request (`/health` solo en nivel debug, salvo que falle) |
| `redirect not_found code=…` · `redirect expired code=…` | Una redirección que no se hizo |
| `click not recorded code=…` | La redirección funcionó, el análisis no |
| `d1 request failed reason=auth\|timeout\|connection\|upstream\|invalid_json` | No se pudo llegar a D1 ([falla 4](break.md#4-falla-de-d1)). El token nunca se loguea |
| `d1 query rejected … error=…` | D1 rechazó el SQL |

Cómo consultarlos: [Lab 11](labs/11-observability.md).

## El dashboard

`frontend/app.py` es un solo archivo. `api()` es el único lugar que hace llamadas HTTP: agrega el token, convierte los errores en `ApiError` y te manda al login cuando el token expira. El token vive en la sesión del navegador (`st.session_state`). Nunca habla con D1.

## Los tests

33 tests, sin red y sin Cloudflare. `FakeD1` es un SQLite en memoria que carga los archivos reales de `migrations/`, así que los tests corren el SQL real de la aplicación sobre el schema real. `BrokenD1` simula una caída.

| Archivo | Qué comprueba |
| --- | --- |
| `test_api.py` | La API de punta a punta: cuentas, links, alias, expiración, redirecciones, propiedad, QR, dashboard, `503` y `500` |
| `test_d1_client.py` | `D1Database` contra un transporte HTTP falso: qué envía, timeouts, errores, y que el token nunca se loguea |

Para correrlos, junto con los chequeos que corre CI:

```bash
cd backend && pip install -r requirements-dev.txt && pytest -q
cd .. && ruff check backend frontend && ruff format --check backend frontend
```

## Cómo cambiarlo

- **Un endpoint nuevo.** La lógica en `shortener.py` o `analytics.py`, los modelos en `schemas.py` y la ruta en `main.py`, **arriba** de `/{code}`. Su docstring pasa a ser su texto en `/docs`. Sumá un test en `test_api.py`.
- **Una columna o tabla nueva.** Un archivo numerado nuevo en `migrations/`, siempre aditivo ([Lab 02](labs/02-d1.md)).
- **Una configuración nueva.** Leela en `config.py`; para darle valor en el cluster, agregala a los valores del Secret en Vault (`./scripts/install.sh secrets`, o `v kv patch secret/smartlink/backend NOMBRE=valor`).
