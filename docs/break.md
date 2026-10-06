🌐 [Leer en español](es/break.md) · 📖 [Docs index](README.md)

# 💥 Break the Platform

**Break it on purpose, find the cause, bring it back.**

Every failure follows the same format: **trigger → what you see → where to look → fix**. Before you start, read the [triage map](troubleshooting.md).

Tip: keep a `curl .../health` loop running in another terminal. That way you see whether the **service** went down, not just which component broke.

| # | Failure | Chain | What you see |
| --- | --- | --- | --- |
| 1 | [ImagePullBackOff](#1-imagepullbackoff) | Delivery | The new pod cannot pull the image |
| 2 | [CrashLoopBackOff](#2-crashloopbackoff) | Secrets | The new pod starts and dies in a loop |
| 3 | [GitOps drift](#3-gitops-drift) | Delivery | `smartlink-backend` is `OutOfSync` |
| 4 | [D1 failure](#4-d1-failure) | Traffic | `503`, but `/health` is `200` |
| 5 | [Failed migration](#5-failed-migration) | Delivery | `migrate` fails and nothing is deployed |
| 6 | [Bad release](#6-bad-release) | Delivery | CI is green, the dashboard shows `HTTP 404` |
| 7 | [DNS / Ingress](#7-dns--ingress) | Traffic | `404 page not found` in plain text |
| 8 | [Sealed Vault](#8-sealed-vault) | Secrets | VSO does not sync, the app keeps running |
| 9 | [Wrong role](#9-wrong-role) | Secrets | VSO cannot log in |
| 10 | [Wrong policy](#10-wrong-policy) | Secrets | `403 permission denied` |
| 11 | [Missing secret](#11-missing-secret) | Secrets | Empty Secret and the new pod in a loop |

The `v kv ...` commands need a login with the root token: `printf '%s' "<root-token>" | v login -`.

---

## 1. ImagePullBackOff

**Trigger** · Commit `image.tag: "doesnotexist"` in `deploy/components/smartlink-backend/values.yaml`.

**What you see** · The new pod stays in `ImagePullBackOff`. The service keeps answering.

**Where to look** · In the events, not the logs, because the container never started:

**On the VM**

```bash
k -n smartlink-backend describe pod <new-pod> | sed -n '/Events/,$p'
```

Look for the `Failed to pull image` line:

- **`not found`**: the tag does not exist in GHCR.
- **`unauthorized`**: it exists, but the node has no access (private repo: `./scripts/install.sh ghcr`).

**Fix** · `git revert` the commit.

**Lesson** · It is a problem getting the image, not an app problem. Thanks to `maxUnavailable: 0`, the deploy gets stuck but the service stays up.

## 2. CrashLoopBackOff

**Trigger** · `v kv patch secret/smartlink/backend JWT_SECRET=short`

**What you see** · The new pod starts and dies in a loop. The old pods keep serving.

**Where to look** · In the logs of the **previous** container:

```bash
k -n smartlink-backend logs <new-pod> --previous | tail -2
# ConfigError: JWT_SECRET must be at least 32 characters
```

**Fix** · `v kv rollback -version=<previous> secret/smartlink/backend`. VSO restarts the backend with the good value.

**Lesson** · *CrashLoopBackOff* means it starts and dies. The cause is in `logs --previous`.

## 3. GitOps drift

**Trigger** · `k -n smartlink-backend scale deploy smartlink-api --replicas=5`

**What you see** · The `smartlink-backend` Application goes `OutOfSync`.

**Where to look** · In the Argo CD UI, *App Diff*: `replicas` is 2 in Git and 5 in the cluster.

**Fix** · *Sync* in Argo CD. Or turn on `selfHeal: true` with a commit so it fixes itself.

**Lesson** · Drift is a difference from Git. `selfHeal` decides whether Argo CD only shows it or fixes it.

## 4. D1 failure

**Trigger** · `v kv patch secret/smartlink/backend D1_API_TOKEN=invalid-token`

**What you see** · Requests return `503`, but `/health` stays `200`.

**Where to look** · In Loki: `{app="smartlink-api", level="ERROR"}` shows `d1 request failed reason=auth`.

**Fix** · `v kv rollback -version=<previous> secret/smartlink/backend`.

**Lesson** · A green `/health` means the process is alive, not that the system is healthy.

## 5. Failed migration

**Trigger** · Add `migrations/004_broken.sql` with `ALTER TABLE does_not_exist ADD COLUMN x TEXT;` and push to `main`.

**What you see** · In *Actions › ci*, `migrate` fails with `no such table` and `gitops` does not run.

**Fix** · Fix the file or revert the commit. If the migration had already been applied, the fix would go in a new migration (`005`).

**Lesson** · Since the migration runs before the deploy, a broken migration **blocks** the deploy but does not break the cluster.

## 6. Bad release

**Trigger** · In `frontend/app.py`, change `/stats` to `/statz` and push to `main`.

**What you see** · CI is green, but the dashboard shows `HTTP 404`.

**Where to look** · In Loki: `{app="smartlink-api"} |= "statz"`.

**Fix** · `git revert` the deploy commit ([rollback](labs/12-rollback.md)).

**Lesson** · A green pipeline only guarantees what the tests cover, and the frontend has none.

## 7. DNS / Ingress

**Trigger** · In `deploy/components/smartlink-backend/templates/ingress.yaml`, change `path: /` to `path: /api` and commit.

**What you see** · `/health` answers `404 page not found`, in plain text.

**Where to look** · That `404` comes from **Traefik**, not the app: `k -n smartlink-backend describe ingress smartlink-api`. Or open the Traefik dashboard (`http://traefik.<ip>.nip.io` › HTTP › Routers): there is no router for `/` any more.

**Fix** · `git revert` the commit.

**Lesson** · Who answers the error tells you the layer:

- timeout → network;
- `404` in plain text → Ingress;
- `404` in JSON → the app.

## 8. Sealed Vault

**Trigger** · `k -n vault delete pod vault-0`

**What you see** · `v status` shows `Sealed true`, and the `VaultStaticSecret` goes `SYNCED False`. **The app keeps running.**

**Fix** · `./scripts/install.sh unseal`

**Lesson** · The Kubernetes Secret works as a cache: with Vault down you cannot change anything, but the service stays up.

## 9. Wrong role

**Trigger** · `v write auth/kubernetes/role/smartlink-backend bound_service_account_namespaces=other`

**What you see** · VSO cannot log in and the Secret stops updating.

**Where to look** · The `VaultStaticSecret` events show a **login** error:

```bash
k -n smartlink-backend describe vaultstaticsecret smartlink-backend | sed -n '/Events/,$p'
```

**Fix** · `./scripts/install.sh configure`, which rewrites the roles and policies.

**Lesson** · It is an authentication problem: the role defines **who** can get in.

## 10. Wrong policy

**Trigger** · `printf 'path "secret/data/other" { capabilities = ["read"] }' | v policy write smartlink-backend -`

**What you see** · The login works, but reading the secret gives `403 permission denied`.

**Where to look** · In the `VaultStaticSecret` events and with `v policy read smartlink-backend`.

**Fix** · `./scripts/install.sh configure`.

**Lesson** · It is an authorization problem: the policy defines **what** can be read. Compare with failure 9.

## 11. Missing secret

**Trigger** · `v kv delete secret/smartlink/backend`

**What you see** · The Secret goes empty and the new pod enters `CrashLoopBackOff`. The old pods keep serving.

**Where to look** · `k -n smartlink-backend get secret smartlink-backend -o jsonpath='{.data}'` returns an empty Secret.

**Fix** · `v kv undelete -versions=<n> secret/smartlink/backend`. In KV v2 the delete is logical and can be undone.

**Lesson** · A green component can sync something empty. The service survives thanks to the app's fail-fast and `maxUnavailable: 0`.
