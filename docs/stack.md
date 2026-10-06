🌐 [Leer en español](es/stack.md) · 📖 [Docs index](README.md)

# 🧰 The stack

**What each technology is, what it does in SmartLink, and why we use it.** If a name in the labs does not ring a bell, start here.

## The app

| Technology | What it is | What it does here | Why |
| --- | --- | --- | --- |
| **FastAPI** | A Python web framework | The API: accounts, short links, redirects, stats. Serves its own docs at `/docs` | Small, typed, and the interactive docs come for free. The app is not the point of the lab, so it stays simple |
| **Streamlit** | A Python library for web UIs | The dashboard under `/app` | A UI without a JavaScript toolchain, kept as its own service so the two can be deployed separately |
| **Cloudflare D1** | A managed SQL database (SQLite) | Stores users, links and clicks, **outside** the cluster | The pods stay stateless and replaceable, there is no database to operate, and the schema changes through versioned migrations |
| **Wrangler** | Cloudflare's command line tool | Applies the D1 migrations from CI | It is the official way to run D1 migrations |

## Build and delivery

| Technology | What it is | What it does here | Why |
| --- | --- | --- | --- |
| **Docker** | Packages an app and its dependencies as an image | Builds the two images: non-root, read-only filesystem, amd64 and arm64 | The same artifact runs on any node, and it carries no configuration or secrets |
| **GitHub Actions** | CI/CD that lives in the repo | Tests, builds the images, runs the migrations and writes the new image tag to Git | It is next to the code, and it never needs access to the cluster |
| **GHCR** | GitHub's container registry | Stores the images, tagged with the commit SHA | Free, next to the repo, and CI logs in with the token GitHub already provides |
| **Helm** | A package manager for Kubernetes: templates plus values | Packages our two apps; the official charts (Vault, Loki…) are installed with it too | The tools we install already ship as Helm charts, and `values.yaml` is where each one is configured |
| **Argo CD** | A GitOps controller | Keeps the cluster equal to what Git says; an ApplicationSet creates one Application per folder in `deploy/components/` | Deploying is a commit, a rollback is a `git revert`, and a manual change shows up as drift |

## The platform

| Technology | What it is | What it does here | Why |
| --- | --- | --- | --- |
| **K3s** | Kubernetes in a single lightweight binary | Runs everything | It is real Kubernetes that fits a 2 CPU, 4 GB VM, and it already includes Traefik and storage |
| **Traefik** | An ingress controller (a reverse proxy) | The only way in: sends each request on port 80 to the right Service ([more](traefik.md)) | It ships with K3s, so there is nothing to install |
| **nip.io** | A public DNS that answers with the IP written in the name | `argocd.<ip>.nip.io` resolves to `<ip>` | The dashboards get names without configuring any DNS |
| **Multipass** | Ubuntu virtual machines on your computer | On a Mac, hosts the VM that runs K3s | K3s needs Linux, and this creates one with a single command |

## Secrets

| Technology | What it is | What it does here | Why |
| --- | --- | --- | --- |
| **Vault** | A secret store | Holds the Cloudflare token, `JWT_SECRET` and the Grafana password, with one read-only policy per app | The values never go through Git, and each app can read only its own path |
| **Vault Secrets Operator (VSO)** | A Kubernetes operator | Copies the values from Vault into a normal Kubernetes Secret and restarts the app when they change | The app does not know Vault exists: it just reads environment variables |

## Observability

| Technology | What it is | What it does here | Why |
| --- | --- | --- | --- |
| **Grafana Alloy** | Grafana's telemetry collector | Collects the logs of every pod and the Kubernetes events | It reads through the Kubernetes API, so it mounts nothing from the node |
| **Loki** | A log database that indexes labels, not text | Stores the logs for 7 days | Cheap to run, and enough for one node |
| **Grafana** | A UI to query and chart data | Where you search the logs (LogQL) | It is the standard front end for Loki |

## Where to see each one running

Their URLs and logins are at the end of the installer, and `./scripts/install.sh access` shows them again ([Install](install.md#3-use-smartlink)). The labs go deeper, one per topic: [index](README.md#labs). The reasons behind each decision, with their sources, are in [References](references.md).
