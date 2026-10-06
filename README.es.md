<div align="center">

<img src="docs/images/brand/hero.es.svg" alt="SmartLink — DevOps / GitOps Platform Lab: code, build, ship, deploy, observe, break, diagnose, recover, learn" width="100%">

<br>

[![CI](https://img.shields.io/badge/ci-GitHub_Actions-0B0F14?logo=githubactions&logoColor=22D3EE&labelColor=0B0F14)](../../actions/workflows/ci.yaml)
![Images](https://img.shields.io/badge/images-amd64_·_arm64-0B0F14?logo=docker&logoColor=22D3EE&labelColor=0B0F14)
![Kubernetes](https://img.shields.io/badge/kubernetes-K3s_1.37-0B0F14?logo=kubernetes&logoColor=22D3EE&labelColor=0B0F14)
![GitOps](https://img.shields.io/badge/gitops-Argo_CD_3.5-0B0F14?logo=argo&logoColor=22D3EE&labelColor=0B0F14)
![Observability](https://img.shields.io/badge/observability-Alloy_·_Loki_·_Grafana-0B0F14?logo=grafana&logoColor=22D3EE&labelColor=0B0F14)
![Security](https://img.shields.io/badge/secrets-Vault_+_VSO-0B0F14?logo=vault&logoColor=22D3EE&labelColor=0B0F14)

**[Instalación](docs/es/install.md)** · **[Labs](#-labs)** · **[Break the Platform](docs/es/break.md)** · **[El stack](docs/es/stack.md)** · **[Arquitectura](docs/es/architecture.md)** · **[Referencias](docs/es/references.md)** · **[Toda la documentación](docs/es/README.md)**

[English](README.md) · **Español**

</div>

## ⚡ La idea

**SmartLink no es un acortador de URLs: es un laboratorio de plataforma que usa uno como excusa.** Lo construís, lo desplegás, lo observás, lo rompés y lo recuperás, llevando a la práctica la metodología DevOps: CI/CD, Kubernetes, GitOps y servicios desacoplados.

> [!NOTE]
> Instalado y probado de punta a punta en una VM local (Multipass en macOS).

## 🧱 Stack

**Aplicación**<br>
<img alt="Python" src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">&nbsp;<img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">&nbsp;<img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white">&nbsp;<img alt="Cloudflare D1" src="https://img.shields.io/badge/Cloudflare_D1-F38020?style=for-the-badge&logo=cloudflare&logoColor=white">

**Plataforma**<br>
<img alt="Docker" src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white">&nbsp;<img alt="GHCR" src="https://img.shields.io/badge/GHCR-181717?style=for-the-badge&logo=github&logoColor=white">&nbsp;<img alt="K3s" src="https://img.shields.io/badge/K3s-FFC61C?style=for-the-badge&logo=k3s&logoColor=black">&nbsp;<img alt="Helm" src="https://img.shields.io/badge/Helm-0F1689?style=for-the-badge&logo=helm&logoColor=white">&nbsp;<img alt="Argo CD" src="https://img.shields.io/badge/Argo_CD-EF7B4D?style=for-the-badge&logo=argo&logoColor=white">&nbsp;<img alt="Traefik" src="https://img.shields.io/badge/Traefik-24A1C1?style=for-the-badge&logo=traefikproxy&logoColor=white">

**Bootstrap**<br>
<img alt="Bash" src="https://img.shields.io/badge/Bash-4EAA25?style=for-the-badge&logo=gnubash&logoColor=white">&nbsp;<img alt="GitHub Actions" src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white">&nbsp;<img alt="Multipass" src="https://img.shields.io/badge/Multipass-E95420?style=for-the-badge&logo=ubuntu&logoColor=white">&nbsp;<img alt="nip.io" src="https://img.shields.io/badge/nip.io-555555?style=for-the-badge">

**Observabilidad**<br>
<img alt="Alloy" src="https://img.shields.io/badge/Alloy-F46800?style=for-the-badge&logo=grafana&logoColor=white">&nbsp;<img alt="Loki" src="https://img.shields.io/badge/Loki-F46800?style=for-the-badge&logo=grafana&logoColor=white">&nbsp;<img alt="Grafana" src="https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white">

**Seguridad**<br>
<img alt="Vault" src="https://img.shields.io/badge/Vault-FFEC6E?style=for-the-badge&logo=vault&logoColor=black">&nbsp;<img alt="Vault Secrets Operator" src="https://img.shields.io/badge/Vault_Secrets_Operator-FFEC6E?style=for-the-badge&logo=vault&logoColor=black">

## 🏗 Arquitectura

![Arquitectura de SmartLink: developer, GitHub Actions, GHCR, Cloudflare D1 y el cluster K3s con Argo CD, Vault, la app y la observabilidad](docs/images/architecture.es.svg)

GitHub Actions **nunca** toca el cluster: cambia Git, y Argo CD, desde adentro, hace el resto.

## 🧪 Labs

| # | Lab | Aprendés |
| --- | --- | --- |
| 01 | [Aplicación](docs/es/labs/01-application.md) | API stateless, fail-fast, 503 vs. 500 |
| 02 | [Cloudflare D1](docs/es/labs/02-d1.md) | Migraciones versionadas y aditivas |
| 03 | [Docker](docs/es/labs/03-docker.md) | Imágenes sin root, read-only, multi-arch |
| 04 | [K3s](docs/es/labs/04-k3s.md) | get → describe → logs, reconciliación |
| 05 | [Scripts de instalación](docs/es/labs/05-scripts.md) | Bootstrap vs. GitOps, idempotencia |
| 06 | [Argo CD](docs/es/labs/06-argocd.md) | Desired vs. live, ApplicationSet |
| 07 | [Vault + VSO](docs/es/labs/07-vault.md) | Kubernetes auth, policies, secretos fuera de Git |
| 08 | [GitHub Actions + GHCR](docs/es/labs/08-github-actions.md) | SHA vs. semver, release sin rebuild |
| 09 | [GitOps](docs/es/labs/09-gitops.md) | Drift y selfHeal |
| 10 | [DNS & Ingress](docs/es/labs/10-dns-ingress.md) | Triage por capas |
| 11 | [Observabilidad](docs/es/labs/11-observability.md) | LogQL, eventos de Kubernetes |
| 12 | [Rollback](docs/es/labs/12-rollback.md) | `git revert` y migraciones |

## 💥 Break the Platform

11 fallas reales, provocadas a propósito: **provocar → qué ves → dónde mirar → causa → arreglo → lección.**

`ImagePullBackOff` · `CrashLoopBackOff` · GitOps drift · falla de D1 · migración fallida · bad release · DNS/Ingress · Vault sellado · role incorrecto · policy incorrecta · secret faltante → [escenarios](docs/es/break.md)

## 🚀 Empezar

**Necesitás:** una VM Linux (o tu Mac), una cuenta de GitHub y una de Cloudflare.

```bash
git clone git@github.com:<vos>/<tu-repo>.git && cd <tu-repo>
./scripts/install.sh    # te guía paso a paso: en una Mac primero crea la VM
```

<a href="docs/es/install.md"><img src="https://img.shields.io/badge/Guía_de_instalación-→-22D3EE?style=for-the-badge&labelColor=0B0F14&logo=gnubash&logoColor=22D3EE" alt="Guía de instalación"></a>
<a href="docs/es/README.md"><img src="https://img.shields.io/badge/Toda_la_documentación-→-1F2A37?style=for-the-badge&labelColor=0B0F14&logo=readthedocs&logoColor=22D3EE" alt="Toda la documentación"></a>

<details>
<summary><b>Estructura del repositorio</b></summary>

```text
backend/  frontend/   App (FastAPI + Streamlit) con sus Dockerfiles
migrations/           Schema de D1, versionado
scripts/              Bootstrap: install.sh (guiada) · uninstall.sh
deploy/root/          ApplicationSet + AppProject: una Application por carpeta de components/
deploy/components/    Una carpeta por componente: Chart.yaml (versión) · values.yaml · templates/
.github/workflows/    ci.yaml
docs/                 Documentación: inglés (docs/) y español (docs/es/)
```

</details>
