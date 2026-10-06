🌐 [Read in English](../break.md) · 📖 [Índice](README.md)

# 💥 Break the Platform

**Rompela a propósito, encontrá la causa, recuperala.**

Cada falla sigue el mismo formato: **provocar → qué ves → dónde mirar → arreglo**. Antes de empezar, leé el [mapa de triage](troubleshooting.md).

Tip: dejá corriendo un `curl .../health` en loop en otra terminal. Así ves si se cortó el **servicio**, además de qué componente se rompió.

| # | Falla | Cadena | Qué ves |
| --- | --- | --- | --- |
| 1 | [ImagePullBackOff](#1-imagepullbackoff) | Entrega | El pod nuevo no descarga la imagen |
| 2 | [CrashLoopBackOff](#2-crashloopbackoff) | Secretos | El pod nuevo arranca y muere en bucle |
| 3 | [GitOps drift](#3-gitops-drift) | Entrega | `smartlink-backend` en `OutOfSync` |
| 4 | [Falla de D1](#4-falla-de-d1) | Tráfico | `503`, pero `/health` en `200` |
| 5 | [Migración fallida](#5-migración-fallida) | Entrega | `migrate` falla y no se despliega nada |
| 6 | [Bad release](#6-bad-release) | Entrega | CI en verde, dashboard con `HTTP 404` |
| 7 | [DNS / Ingress](#7-dns--ingress) | Tráfico | `404 page not found` en texto plano |
| 8 | [Vault sellado](#8-vault-sellado) | Secretos | VSO no sincroniza, la app sigue andando |
| 9 | [Role incorrecto](#9-role-incorrecto) | Secretos | VSO no puede hacer login |
| 10 | [Policy incorrecta](#10-policy-incorrecta) | Secretos | `403 permission denied` |
| 11 | [Secret faltante](#11-secret-faltante) | Secretos | Secret vacío y pod nuevo en bucle |

Los comandos `v kv ...` necesitan login con el root token: `printf '%s' "<root-token>" | v login -`.

---

## 1. ImagePullBackOff

**Provocar** · Hacé un commit en `deploy/components/smartlink-backend/values.yaml` con `image.tag: "noexiste"`.

**Qué ves** · El pod nuevo queda en `ImagePullBackOff`. El servicio sigue respondiendo.

**Dónde mirar** · En los eventos, no en los logs, porque el contenedor nunca arrancó:

**En la VM**

```bash
k -n smartlink-backend describe pod <pod-nuevo> | sed -n '/Events/,$p'
```

Buscá la línea `Failed to pull image`:

- **`not found`**: el tag no existe en GHCR.
- **`unauthorized`**: existe, pero el nodo no tiene acceso (repo privado: `./scripts/install.sh ghcr`).

**Arreglo** · `git revert` del commit.

**Lección** · Es un problema para obtener la imagen, no de la app. Gracias a `maxUnavailable: 0`, el deploy queda trabado pero el servicio no se cae.

## 2. CrashLoopBackOff

**Provocar** · `v kv patch secret/smartlink/backend JWT_SECRET=corto`

**Qué ves** · El pod nuevo arranca y muere en bucle. Los pods viejos siguen sirviendo.

**Dónde mirar** · En los logs del contenedor **anterior**:

```bash
k -n smartlink-backend logs <pod-nuevo> --previous | tail -2
# ConfigError: JWT_SECRET must be at least 32 characters
```

**Arreglo** · `v kv rollback -version=<anterior> secret/smartlink/backend`. VSO reinicia el backend con el valor bueno.

**Lección** · *CrashLoopBackOff* significa que arranca y muere. La causa está en `logs --previous`.

## 3. GitOps drift

**Provocar** · `k -n smartlink-backend scale deploy smartlink-api --replicas=5`

**Qué ves** · La Application `smartlink-backend` queda en `OutOfSync`.

**Dónde mirar** · En la UI de Argo CD, *App Diff*: `replicas` vale 2 en Git y 5 en el cluster.

**Arreglo** · Hacé *Sync* en Argo CD. Otra opción: activá `selfHeal: true` por commit para que se corrija solo.

**Lección** · El drift es una diferencia con Git. `selfHeal` decide si Argo CD solo la muestra o la corrige.

## 4. Falla de D1

**Provocar** · `v kv patch secret/smartlink/backend D1_API_TOKEN=token-invalido`

**Qué ves** · Las requests devuelven `503`, pero `/health` sigue en `200`.

**Dónde mirar** · En Loki: `{app="smartlink-api", level="ERROR"}` muestra `d1 request failed reason=auth`.

**Arreglo** · `v kv rollback -version=<anterior> secret/smartlink/backend`.

**Lección** · `/health` en verde significa proceso vivo, no sistema sano.

## 5. Migración fallida

**Provocar** · Agregá `migrations/004_broken.sql` con `ALTER TABLE no_existe ADD COLUMN x TEXT;` y hacé push a `main`.

**Qué ves** · En *Actions › ci*, `migrate` falla con `no such table` y `gitops` no corre.

**Arreglo** · Corregí el archivo o revertí el commit. Si la migración ya se hubiera aplicado, la corrección iría en una migración nueva (`005`).

**Lección** · Como la migración corre antes del deploy, una migración rota **bloquea** el deploy, pero no rompe el cluster.

## 6. Bad release

**Provocar** · En `frontend/app.py`, cambiá `/stats` por `/statz` y hacé push a `main`.

**Qué ves** · CI en verde, pero el dashboard muestra `HTTP 404`.

**Dónde mirar** · En Loki: `{app="smartlink-api"} |= "statz"`.

**Arreglo** · `git revert` del commit de deploy ([rollback](labs/12-rollback.md)).

**Lección** · Un pipeline verde solo garantiza lo que cubren los tests, y el frontend no tiene.

## 7. DNS / Ingress

**Provocar** · En `deploy/components/smartlink-backend/templates/ingress.yaml`, cambiá `path: /` por `path: /api` y hacé commit.

**Qué ves** · `/health` responde `404 page not found`, en texto plano.

**Dónde mirar** · Ese `404` lo devuelve **Traefik**, no la app: `k -n smartlink-backend describe ingress smartlink-api`. O abrí el panel de Traefik (`http://traefik.<ip>.nip.io` › HTTP › Routers): ya no hay un router para `/`.

**Arreglo** · `git revert` del commit.

**Lección** · Quién responde el error te dice la capa:

- timeout → red;
- `404` en texto → Ingress;
- `404` en JSON → la app.

## 8. Vault sellado

**Provocar** · `k -n vault delete pod vault-0`

**Qué ves** · `v status` muestra `Sealed true`, y el `VaultStaticSecret` queda en `SYNCED False`. **La app sigue funcionando.**

**Arreglo** · `./scripts/install.sh unseal`

**Lección** · El Secret de Kubernetes funciona como caché: con Vault caído no se pueden hacer cambios, pero el servicio sigue.

## 9. Role incorrecto

**Provocar** · `v write auth/kubernetes/role/smartlink-backend bound_service_account_namespaces=otro`

**Qué ves** · VSO no puede hacer login y el Secret deja de actualizarse.

**Dónde mirar** · En los eventos del `VaultStaticSecret` aparece un error de **login**:

```bash
k -n smartlink-backend describe vaultstaticsecret smartlink-backend | sed -n '/Events/,$p'
```

**Arreglo** · `./scripts/install.sh configure`, que reescribe los roles y las policies.

**Lección** · Es un problema de autenticación: el role define **quién** puede entrar.

## 10. Policy incorrecta

**Provocar** · `printf 'path "secret/data/otra" { capabilities = ["read"] }' | v policy write smartlink-backend -`

**Qué ves** · El login funciona, pero leer el secreto da `403 permission denied`.

**Dónde mirar** · En los eventos del `VaultStaticSecret` y con `v policy read smartlink-backend`.

**Arreglo** · `./scripts/install.sh configure`.

**Lección** · Es un problema de autorización: la policy define **qué** se puede leer. Compará con la falla 9.

## 11. Secret faltante

**Provocar** · `v kv delete secret/smartlink/backend`

**Qué ves** · El Secret queda vacío y el pod nuevo entra en `CrashLoopBackOff`. Los pods viejos siguen sirviendo.

**Dónde mirar** · `k -n smartlink-backend get secret smartlink-backend -o jsonpath='{.data}'` devuelve un Secret vacío.

**Arreglo** · `v kv undelete -versions=<n> secret/smartlink/backend`. En KV v2, el delete es lógico y se puede recuperar.

**Lección** · Un componente en verde puede sincronizar algo vacío. El servicio se salva gracias al fail-fast de la app y a `maxUnavailable: 0`.
