🌐 [Read in English](../README.md)

![SmartLink — DevOps / GitOps Platform Lab](../images/brand/hero.es.svg)

# 📖 Documentación de SmartLink

**SmartLink no es un acortador de URLs: es un laboratorio de plataforma que usa uno como excusa.** Lo construís, lo desplegás, lo observás, lo rompés y lo recuperás, llevando a la práctica la metodología DevOps: CI/CD, Kubernetes, GitOps y servicios desacoplados.

## Por dónde empezar

| | Página | Qué tenés |
| --- | --- | --- |
| 🚀 | [Instalación](install.md) | Un comando que te guía de cero a la app funcionando |
| 🧰 | [El stack](stack.md) | Qué es cada tecnología, qué hace acá y por qué la usamos |
| 🧩 | [El código](code.md) | Un mapa del backend, la API, la configuración, los datos y los tests |
| 🏗 | [Cómo funciona](architecture.md) | Qué hace cada pieza y dónde están las versiones |
| 🚦 | [Traefik](traefik.md) | La única puerta de entrada al cluster: cómo una request encuentra su pod, y cómo leer su panel |
| 💥 | [Break the Platform](break.md) | 11 fallas para provocar, diagnosticar y arreglar |
| 🔧 | [Troubleshooting](troubleshooting.md) | Dónde mirar primero, según el síntoma |
| 📚 | [Referencias](references.md) | De dónde sale cada decisión |

## Labs

| # | Lab | Aprendés |
| --- | --- | --- |
| 01 | [Aplicación](labs/01-application.md) | API stateless, fail-fast, 503 vs. 500 |
| 02 | [Cloudflare D1](labs/02-d1.md) | Migraciones versionadas y aditivas |
| 03 | [Docker](labs/03-docker.md) | Imágenes sin root, read-only, multi-arch |
| 04 | [K3s](labs/04-k3s.md) | get → describe → logs, reconciliación |
| 05 | [Scripts de instalación](labs/05-scripts.md) | Bootstrap vs. GitOps, idempotencia |
| 06 | [Argo CD](labs/06-argocd.md) | Desired vs. live, ApplicationSet |
| 07 | [Vault + VSO](labs/07-vault.md) | Kubernetes auth, policies, secretos fuera de Git |
| 08 | [GitHub Actions + GHCR](labs/08-github-actions.md) | SHA vs. semver, release sin rebuild |
| 09 | [GitOps](labs/09-gitops.md) | Drift y selfHeal |
| 10 | [DNS & Ingress](labs/10-dns-ingress.md) | Triage por capas |
| 11 | [Observabilidad](labs/11-observability.md) | LogQL, eventos de Kubernetes |
| 12 | [Rollback](labs/12-rollback.md) | `git revert` y migraciones |

## Los tres flujos

| Flujo | Cadena |
| --- | --- |
| **Entrega** | commit ─► CI (tests · imagen · migración) ─► commit en `deploy/` ─► Argo CD ─► K3s |
| **Secretos** | Vault ─► VSO ─► Secret ─► FastAPI |
| **Logs** | pods ─► Alloy ─► Loki ─► Grafana |
