🌐 [Leer en español](es/README.md)

![SmartLink — DevOps / GitOps Platform Lab](images/brand/hero.svg)

# 📖 SmartLink documentation

**SmartLink is not a URL shortener: it is a platform lab that uses one as an excuse.** You build it, deploy it, observe it, break it and bring it back, putting DevOps practices to work: CI/CD, Kubernetes, GitOps and decoupled services.

## Start here

| | Page | What you get |
| --- | --- | --- |
| 🚀 | [Install](install.md) | One command that guides you from zero to a running app |
| 🧰 | [The stack](stack.md) | What each technology is, what it does here and why we use it |
| 🧩 | [The code](code.md) | A map of the backend, the API, the configuration, the data and the tests |
| 🏗 | [How it works](architecture.md) | What each piece does and where the versions live |
| 🚦 | [Traefik](traefik.md) | The only door into the cluster: how a request finds its pod, and how to read its dashboard |
| 💥 | [Break the Platform](break.md) | 11 failures to trigger, diagnose and fix |
| 🔧 | [Troubleshooting](troubleshooting.md) | Where to look first, by symptom |
| 📚 | [References](references.md) | Where every decision comes from |

## Labs

| # | Lab | You learn |
| --- | --- | --- |
| 01 | [Application](labs/01-application.md) | Stateless API, fail-fast, 503 vs. 500 |
| 02 | [Cloudflare D1](labs/02-d1.md) | Versioned, additive migrations |
| 03 | [Docker](labs/03-docker.md) | Non-root, read-only, multi-arch images |
| 04 | [K3s](labs/04-k3s.md) | get → describe → logs, reconciliation |
| 05 | [Install scripts](labs/05-scripts.md) | Bootstrap vs. GitOps, idempotency |
| 06 | [Argo CD](labs/06-argocd.md) | Desired vs. live, ApplicationSet |
| 07 | [Vault + VSO](labs/07-vault.md) | Kubernetes auth, policies, secrets outside Git |
| 08 | [GitHub Actions + GHCR](labs/08-github-actions.md) | SHA vs. semver, release without rebuild |
| 09 | [GitOps](labs/09-gitops.md) | Drift and selfHeal |
| 10 | [DNS & Ingress](labs/10-dns-ingress.md) | Layer-by-layer triage |
| 11 | [Observability](labs/11-observability.md) | LogQL, Kubernetes events |
| 12 | [Rollback](labs/12-rollback.md) | `git revert` and migrations |

## The three flows

| Flow | Chain |
| --- | --- |
| **Delivery** | commit ─► CI (tests · image · migration) ─► commit in `deploy/` ─► Argo CD ─► K3s |
| **Secrets** | Vault ─► VSO ─► Secret ─► FastAPI |
| **Logs** | pods ─► Alloy ─► Loki ─► Grafana |
