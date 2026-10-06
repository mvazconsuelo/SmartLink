🌐 [Read in English](../../labs/05-scripts.md) · 📖 [Índice](../README.md)

# Lab 05 — Scripts de instalación

**Objetivo:** Levantar la base de la plataforma con scripts repetibles y entregarle el control a GitOps.

## Idea

Los scripts de `scripts/` instalan **solo lo que GitOps no puede instalarse a sí mismo**: el cluster, Argo CD y la base de datos. Lo demás (Vault, VSO, SmartLink, observabilidad) lo despliega Argo CD desde Git.

## Cómo funciona

| Script | Qué hace | Por qué no es GitOps |
| --- | --- | --- |
| `01-k3s.sh` | Paquetes, Helm y K3s (versiones fijas, Secrets cifrados) | Sin cluster no hay Argo CD |
| `02-argocd.sh` | Argo CD (desde `deploy/components/argocd/`), credencial del repo, Application raíz | Argo CD no puede instalarse a sí mismo. Después se administra solo |
| `03-d1.sh` | Crea la base D1 en Cloudflare | Está fuera del cluster |
| `04-vault.sh` | Init, unseal, policies, roles y secretos | Las llaves de Vault no pueden estar en Git |
| `05-ghcr-auth.sh` | Credencial de GHCR en el nodo (solo repo privado) | Es configuración del nodo, no del cluster |

`install.sh` es el punto de entrada: sin argumentos es la **instalación guiada** (7 etapas: corre del 01 al 05 y te guía en Cloudflare y GitHub). `unseal`, `secrets`, `configure`, `ghcr` y `access` son los atajos del día a día (`./scripts/install.sh help`).

En **macOS**, `install.sh` crea una VM Ubuntu con Multipass y se ejecuta adentro (`shell` e `ip` la manejan). `uninstall.sh` desinstala, también según el sistema. Los scripts `01`–`05` se niegan a correr fuera de Linux.

No hay nada que configurar a mano: detectan el repo desde el clon (y te piden confirmarlo), preguntan lo que falta y lo guardan en **`scripts/config.env`** (valores no secretos, fuera de Git). Los tokens se piden al correr, sin mostrarlos; cada pregunta dice adónde va ese secreto (Vault, GitHub, o solo memoria). Comparten `scripts/lib.sh`, que da el formato de salida y las funciones comunes.

Todos son **idempotentes**: revisan el estado antes de actuar, así que correrlos de nuevo no rompe nada.

## Hacelo

Mirá la salida de cualquier script: cada paso dice qué hizo (`✔`) o por qué se frenó (`✖ ...`). La salida de los scripts está en inglés, como el código y la documentación por defecto.

**Upgrades:**
- **Argo CD** ya no se actualiza con un script: su versión vive en Git (`deploy/components/argocd/Chart.yaml`) y cambia con un commit ([Lab 06](06-argocd.md)). `02-argocd.sh` queda como *break-glass*.
- **K3s y Helm** se fijan en `deploy/root/values.yaml` (bloque `bootstrap`). Hoy `01-k3s.sh` no actualiza un K3s ya instalado.

## Rompelo

Corré `./scripts/03-d1.sh` dos veces: la segunda dice `already exists` y muestra el mismo ID. Si un script no fuera idempotente, crearía una segunda base o fallaría.

## Clave

- Los scripts son el **bootstrap**; después, todo pasa por Git.
- Versiones fijas: cada chart en el `Chart.yaml` de su carpeta; K3s y Helm en `deploy/root/values.yaml`.

⬅️ [04 — K3s](04-k3s.md) · 📚 [Todos los labs](../README.md#labs) · ➡️ [06 — Argo CD](06-argocd.md)