🌐 [Read in English](../../labs/07-vault.md) · 📖 [Índice](../README.md)

# Lab 07 — Vault + VSO

**Objetivo:** Llevar secretos de Vault al pod sin que pasen por Git.

## Idea

Los valores (tokens, `JWT_SECRET`, IDs) viven en **Vault**. **VSO** los copia a un Secret de Kubernetes, y el backend los lee como variables de entorno. Git solo dice *quién* puede leer *qué*; nunca contiene valores.

## Cómo funciona

```text
Vault KV ─► VSO (con la identidad del backend) ─► Secret smartlink-backend ─► FastAPI
```

| Qué | Quién |
| --- | --- |
| Instalar Vault y VSO | Argo CD (charts oficiales) |
| Init, unseal, policies, roles, valores | Una persona, una vez (`scripts/04-vault.sh`) |
| Copiar a Kubernetes y reiniciar el backend si cambia algo | VSO |

**Identidad:** VSO se autentica como la ServiceAccount `smartlink-backend`, con un token de audience `vault`. El role solo acepta esa SA en ese namespace, y la policy solo permite **leer** `secret/data/smartlink/backend`. Grafana usa el mismo patrón con `secret/grafana`.

**Por qué el init es manual:** genera las llaves que abren Vault. Si una máquina las guardara, quedarían junto a lo que protegen.

## Hacelo

Cambiá un valor y mirá cómo se propaga:

```bash
v kv patch secret/smartlink/backend LOG_LEVEL=DEBUG
k -n smartlink-backend get pods -w   # en ≤60 s, VSO actualiza el Secret y reinicia el backend
```

Un pod que ya corre **no** ve variables nuevas: necesita reiniciarse, y VSO lo hace.

> [!WARNING]
> **Después de cada reinicio, Vault arranca sellado**
>
> `./scripts/install.sh unseal`. Mientras tanto la app sigue funcionando con el último Secret.

## Rompelo

| Escenario | Qué enseña |
| --- | --- |
| [💥 Vault sellado](../break.md#8-vault-sellado) | El Secret funciona como caché |
| [💥 Role incorrecto](../break.md#9-role-incorrecto) | Autenticación: *quién* entra |
| [💥 Policy incorrecta](../break.md#10-policy-incorrecta) | Autorización: *qué* lee |
| [💥 Secret faltante](../break.md#11-secret-faltante) | Un componente en verde puede sincronizar algo vacío |

## Clave

- Git declara relaciones; Vault guarda valores.
- Vault caído corta los **cambios**, no el servicio.
- Datos en un PVC `local-path`: si se pierde el disco, se pierden los secretos.

⬅️ [06 — Argo CD](06-argocd.md) · 📚 [Todos los labs](../README.md#labs) · ➡️ [08 — GitHub Actions + GHCR](08-github-actions.md)