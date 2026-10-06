<div align="center">

<img src="docs/images/brand/hero.svg" alt="SmartLink — DevOps / GitOps Platform Lab: code, build, ship, deploy, observe, break, diagnose, recover, learn" width="100%">

<br>

[![CI](https://img.shields.io/badge/ci-GitHub_Actions-0B0F14?logo=githubactions&logoColor=22D3EE&labelColor=0B0F14)](../../actions/workflows/ci.yaml)
![Images](https://img.shields.io/badge/images-amd64_·_arm64-0B0F14?logo=docker&logoColor=22D3EE&labelColor=0B0F14)
![Kubernetes](https://img.shields.io/badge/kubernetes-K3s_1.37-0B0F14?logo=kubernetes&logoColor=22D3EE&labelColor=0B0F14)
![GitOps](https://img.shields.io/badge/gitops-Argo_CD_3.5-0B0F14?logo=argo&logoColor=22D3EE&labelColor=0B0F14)
![Observability](https://img.shields.io/badge/observability-Alloy_·_Loki_·_Grafana-0B0F14?logo=grafana&logoColor=22D3EE&labelColor=0B0F14)
![Security](https://img.shields.io/badge/secrets-Vault_+_VSO-0B0F14?logo=vault&logoColor=22D3EE&labelColor=0B0F14)

**[Install](docs/install.md)** · **[Labs](#-labs)** · **[Break the Platform](docs/break.md)** · **[The stack](docs/stack.md)** · **[How it works](docs/architecture.md)** · **[References](docs/references.md)** · **[All docs](docs/README.md)**

**English** · [Español](README.es.md)

</div>

## ⚡ The idea

**SmartLink is not a URL shortener: it is a platform lab that uses one as an excuse.** You build it, deploy it, observe it, break it and bring it back, putting DevOps practices to work: CI/CD, Kubernetes, GitOps and decoupled services.

> [!NOTE]
> Installed and tested end to end on a local VM (Multipass on macOS).

## 🧱 Stack

**Application**<br>
<img alt="Python" src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">&nbsp;<img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">&nbsp;<img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white">&nbsp;<img alt="Cloudflare D1" src="https://img.shields.io/badge/Cloudflare_D1-F38020?style=for-the-badge&logo=cloudflare&logoColor=white">

**Platform**<br>
<img alt="Docker" src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white">&nbsp;<img alt="GHCR" src="https://img.shields.io/badge/GHCR-181717?style=for-the-badge&logo=github&logoColor=white">&nbsp;<img alt="K3s" src="https://img.shields.io/badge/K3s-FFC61C?style=for-the-badge&logo=k3s&logoColor=black">&nbsp;<img alt="Helm" src="https://img.shields.io/badge/Helm-0F1689?style=for-the-badge&logo=helm&logoColor=white">&nbsp;<img alt="Argo CD" src="https://img.shields.io/badge/Argo_CD-EF7B4D?style=for-the-badge&logo=argo&logoColor=white">&nbsp;<img alt="Traefik" src="https://img.shields.io/badge/Traefik-24A1C1?style=for-the-badge&logo=traefikproxy&logoColor=white">

**Bootstrap**<br>
<img alt="Bash" src="https://img.shields.io/badge/Bash-4EAA25?style=for-the-badge&logo=gnubash&logoColor=white">&nbsp;<img alt="GitHub Actions" src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white">&nbsp;<img alt="Multipass" src="https://img.shields.io/badge/Multipass-E95420?style=for-the-badge&logo=ubuntu&logoColor=white">&nbsp;<img alt="nip.io" src="https://img.shields.io/badge/nip.io-555555?style=for-the-badge">

**Observability**<br>
<img alt="Alloy" src="https://img.shields.io/badge/Alloy-F46800?style=for-the-badge&logo=grafana&logoColor=white">&nbsp;<img alt="Loki" src="https://img.shields.io/badge/Loki-F46800?style=for-the-badge&logo=grafana&logoColor=white">&nbsp;<img alt="Grafana" src="https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white">

**Security**<br>
<img alt="Vault" src="https://img.shields.io/badge/Vault-FFEC6E?style=for-the-badge&logo=vault&logoColor=black">&nbsp;<img alt="Vault Secrets Operator" src="https://img.shields.io/badge/Vault_Secrets_Operator-FFEC6E?style=for-the-badge&logo=vault&logoColor=black">

## 🏗 Architecture

![SmartLink architecture: developer, GitHub Actions, GHCR, Cloudflare D1, and the K3s cluster with Argo CD, Vault, the app and observability](docs/images/architecture.svg)

GitHub Actions **never** touches the cluster: it changes Git, and Argo CD, from inside, does the rest.

## 🧪 Labs

| # | Lab | You learn |
| --- | --- | --- |
| 01 | [Application](docs/labs/01-application.md) | Stateless API, fail-fast, 503 vs. 500 |
| 02 | [Cloudflare D1](docs/labs/02-d1.md) | Versioned, additive migrations |
| 03 | [Docker](docs/labs/03-docker.md) | Non-root, read-only, multi-arch images |
| 04 | [K3s](docs/labs/04-k3s.md) | get → describe → logs, reconciliation |
| 05 | [Install scripts](docs/labs/05-scripts.md) | Bootstrap vs. GitOps, idempotency |
| 06 | [Argo CD](docs/labs/06-argocd.md) | Desired vs. live, ApplicationSet |
| 07 | [Vault + VSO](docs/labs/07-vault.md) | Kubernetes auth, policies, secrets outside Git |
| 08 | [GitHub Actions + GHCR](docs/labs/08-github-actions.md) | SHA vs. semver, release without rebuild |
| 09 | [GitOps](docs/labs/09-gitops.md) | Drift and selfHeal |
| 10 | [DNS & Ingress](docs/labs/10-dns-ingress.md) | Layer-by-layer triage |
| 11 | [Observability](docs/labs/11-observability.md) | LogQL, Kubernetes events |
| 12 | [Rollback](docs/labs/12-rollback.md) | `git revert` and migrations |

## 💥 Break the Platform

11 real failures, triggered on purpose: **trigger → what you see → where to look → fix → lesson.**

`ImagePullBackOff` · `CrashLoopBackOff` · GitOps drift · D1 failure · failed migration · bad release · DNS/Ingress · sealed Vault · wrong role · wrong policy · missing secret → [scenarios](docs/break.md)

## 🚀 Get started

**You need:** a Linux VM (or your Mac), a GitHub account and a Cloudflare account.

```bash
git clone git@github.com:<you>/<your-repo>.git && cd <your-repo>
./scripts/install.sh    # guides you step by step: on a Mac it creates the VM first
```

<a href="docs/install.md"><img src="https://img.shields.io/badge/Install_guide-→-22D3EE?style=for-the-badge&labelColor=0B0F14&logo=gnubash&logoColor=22D3EE" alt="Install guide"></a>
<a href="docs/README.md"><img src="https://img.shields.io/badge/All_docs-→-1F2A37?style=for-the-badge&labelColor=0B0F14&logo=readthedocs&logoColor=22D3EE" alt="All docs"></a>

<details>
<summary><b>Repository layout</b></summary>

```text
backend/  frontend/   App (FastAPI + Streamlit) with their Dockerfiles
migrations/           D1 schema, versioned
scripts/              Bootstrap: install.sh (guided) · uninstall.sh
deploy/root/          ApplicationSet + AppProject: one Application per folder in components/
deploy/components/    One folder per component: Chart.yaml (version) · values.yaml · templates/
.github/workflows/    ci.yaml
docs/                 Documentation: English (docs/) and Spanish (docs/es/)
```

</details>
