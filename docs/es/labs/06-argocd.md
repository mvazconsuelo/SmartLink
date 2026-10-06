🌐 [Read in English](../../labs/06-argocd.md) · 📖 [Índice](../README.md)

# Lab 06 — Argo CD

**Objetivo:** Que el cluster siga a Git, sin que CI lo toque.

## Idea

Argo CD corre **dentro** del cluster, lee Git y hace que el cluster coincida con lo que dice Git. CI solo escribe en Git: nunca necesita credenciales del cluster.

## Cómo funciona

```text
scripts/02-argocd.sh ─► smartlink-root ─► argocd · smartlink-backend · smartlink-frontend · vault · vault-secrets-operator · loki · alloy · grafana
```

| Término | Significado |
| --- | --- |
| Desired / live state | Lo que dice Git / lo que hay en el cluster |
| OutOfSync | Son distintos |
| Sync | Aplicar Git al cluster |
| Self-heal | Revertir cambios manuales solo |

La raíz (`smartlink-root`) la crea `scripts/02-argocd.sh` y apunta a `deploy/root/`, con la URL del repo y la rama como values: ningún archivo contiene tu URL. Ahí hay un **ApplicationSet** que crea **una Application por carpeta** de `deploy/components/` (nombre de carpeta = Application = namespace). Agregar un componente es agregar una carpeta. El acceso al repo depende del modo: público por HTTPS, sin credencial; privado por SSH, con una deploy key de solo lectura.

**Un AppProject propio.** Las Applications usan el proyecto `smartlink` (`deploy/root/templates/project.yaml`), no `default`: solo este repo y los repos de charts oficiales, y solo los namespaces de SmartLink. La raíz queda en `default` porque es la que crea el proyecto.

**Argo CD se administra a sí mismo.** La Application `argocd` usa la carpeta `deploy/components/argocd/` (chart oficial `argo-cd` como dependencia + sus values); el script instaló exactamente lo mismo. Upgrade = cambiar la versión en su `Chart.yaml` y hacer commit. Usa `prune: false`: nunca se borra a sí mismo.

> [!WARNING]
> **Si un upgrade rompe Argo CD**
>
> No puede arreglarse solo. `git revert` del commit, `git pull` en la VM y `./scripts/02-argocd.sh` (break-glass).

## Hacelo

Entrá a la UI: `http://argocd.<ip>.nip.io`, usuario `admin` (password: `./scripts/install.sh access`).

Commit con `replicas: 3` en `deploy/components/smartlink-backend/values.yaml`: en unos 3 minutos hay 3 pods, sin ningún `kubectl`.

## Rompelo

- Repo privado: borrá la deploy key en GitHub → `authentication required`. Lo que corre **sigue corriendo**: el cluster queda congelado, no roto.
- [💥 GitOps drift](../break.md#3-gitops-drift)

## Clave

- Deploy = commit.
- La única fuente de verdad es Git.

⬅️ [05 — Scripts de instalación](05-scripts.md) · 📚 [Todos los labs](../README.md#labs) · ➡️ [07 — Vault + VSO](07-vault.md)