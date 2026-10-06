🌐 [Leer en español](es/references.md) · 📖 [Docs index](README.md)

# 📚 References

**Where every decision in the project comes from.** First, the decision log: what was done, why, and which source it is based on. Then, the glossary of sources by topic.

## Decision log

### GitOps and Argo CD

| Decision | Why | Source |
| --- | --- | --- |
| One folder per component in `deploy/components/`, with `Chart.yaml` + `values.yaml` (+ `templates/`) | Everything about a component in one place: version, configuration, routes | [Phalanx](https://phalanx.lsst.io/v/DM-35703/arch/repository.html) |
| One **ApplicationSet** with the *Git directory generator*: folder = Application = namespace | Adding a component means adding a folder; no hand-written Applications | [Git generator](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Generators-Git/) |
| Per-component differences with `templatePatch` (prune and selfHeal) | Exceptions are explicit and in one place | [ApplicationSet Template](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Template/) · [Go templates](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/GoTemplate/) |
| Official charts as a **dependency** in our own `Chart.yaml`, with a pinned version | The version sits next to its configuration; Renovate/Dependabot understand it | [Helm: dependencies](https://helm.sh/docs/topics/charts/#chart-dependencies) · [Argo CD: immutable manifests](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/) |
| Root Application created by a script, with the repo URL as a value | No file contains your URL; the repo works for any fork | [Cluster bootstrapping](https://argo-cd.readthedocs.io/en/stable/operator-manual/cluster-bootstrapping/) |
| **AppProject `smartlink`** instead of `default` | Restricts source repos and destination namespaces | [Projects](https://argo-cd.readthedocs.io/en/stable/user-guide/projects/) · [Declarative setup](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/) |
| Argo CD manages itself, with `ServerSideApply=true` and `prune: false` | Upgrade with a commit; it never deletes itself | [Declarative setup](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/) · [Sync options](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/) |
| `ignoreDifferences` on VSO's `restartedAt` annotation | The restart VSO performs is not drift | [Diffing](https://argo-cd.readthedocs.io/en/stable/user-guide/diffing/) |
| `SkipDryRunOnMissingResource` + `retry` | VSO's CRDs come from another component | [Sync options](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/) |
| `selfHeal: false` on `smartlink-*` | Manual drift shows up as `OutOfSync` (lab 09) | [Automated sync](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/) |
| Read-only deploy key for the private repo | Argo CD can only read this repo | [Private repositories](https://argo-cd.readthedocs.io/en/stable/user-guide/private-repositories/) · [GitHub deploy keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys) |
| Same repo for code and configuration (not a separate repo) | A single fork for the lab. Cost: CI commits to `main`, so you `git pull` before pushing | [Best practices: separate repos](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/) |

### CI/CD

| Decision | Why | Source |
| --- | --- | --- |
| CI writes to Git, never to the cluster | The K3s API is not exposed; Argo CD pulls from the repo | [Best practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/) |
| Image tag = SHA; a release retags without rebuilding | Traceable; what was tested is what gets published | [buildx imagetools create](https://docs.docker.com/reference/cli/docker/buildx/imagetools/create/) |
| amd64 + arm64 images | The VM can be x86 or ARM (Multipass on a Mac) | [Docker multi-platform](https://docs.docker.com/build/building/multi-platform/) |
| `paths-ignore` (`deploy/`, `scripts/`, `docs/`) and manual *Run workflow* | Configuration changes do not trigger builds; first deploy on demand | [Workflow syntax](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions) |
| D1 migrations before the deploy, additive | A new app never runs against an old schema | [D1 migrations](https://developers.cloudflare.com/d1/reference/migrations/) |
| Credential check at the start of the `migrate` job | A clear error if the secret is empty or the token is invalid | [Cloudflare: API tokens](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/) |

### Secrets and security

| Decision | Why | Source |
| --- | --- | --- |
| Vault with KV v2 + Kubernetes auth, one read-only policy per consumer | Each app reads only its own path | [Kubernetes auth](https://developer.hashicorp.com/vault/docs/auth/kubernetes) · [KV v2](https://developer.hashicorp.com/vault/docs/secrets/kv/kv-v2) |
| Vault with Raft on a volume, no PDB | Persistent data; a PDB with 1 replica would block drains | [Raft storage](https://developer.hashicorp.com/vault/docs/configuration/storage/raft) · [Vault Helm](https://developer.hashicorp.com/vault/docs/platform/k8s/helm) |
| Manual init and unseal; unseal key only in the password manager | Vault does not store its key: next to the data, the encryption would be useless | [Seal/unseal](https://developer.hashicorp.com/vault/docs/concepts/seal) |
| Vault Secrets Operator: `VaultStaticSecret`, `excludeRaw`, `rolloutRestartTargets` | The app only sees a Secret; it restarts by itself when it changes | [VSO](https://developer.hashicorp.com/vault/docs/platform/k8s/vso) · [API reference](https://developer.hashicorp.com/vault/docs/platform/k8s/vso/api-reference) |
| K3s with `--secrets-encryption` | Secrets are encrypted on disk | [K3s secrets encryption](https://docs.k3s.io/security/secrets-encryption) |
| `read:packages` GHCR token in the node's `registries.yaml` | K3s pulls private images without Secrets in the cluster | [K3s private registry](https://docs.k3s.io/installation/private-registry) · [GHCR](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) |
| *Fine-grained* token for 1 day, this repo only, no *Contents* (optional) | Automates GitHub without leaving write access behind; the repo cannot be prefilled in the link | [Fine-grained PATs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) · [gh CLI](https://cli.github.com/manual/) |
| Repo settings closed by hand before going public: Actions off in the template, read-only token, approval for fork PRs, secret scanning + push protection, `main` without force-push | A public repo is read by everyone and forked by anyone; the defaults are too open | [GitHub REST: Actions permissions](https://docs.github.com/en/rest/actions/permissions) · [GitHub REST: rulesets](https://docs.github.com/en/rest/repos/rules) · [About push protection](https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection) |
| `sudo -v` with our own prompt | `sudo` reads the password, never the script | [sudo](https://www.sudo.ws/docs/man/sudo.man/) |
| Non-root containers, read-only filesystem, no ServiceAccount token | Smaller blast radius if a pod is compromised | [Security context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/) |

### Network and access

| Decision | Why | Source |
| --- | --- | --- |
| nip.io for the dashboards (`argocd.<ip>.nip.io`) instead of DuckDNS | Everything local, no accounts and no DNS of our own | [nip.io](https://nip.io) |
| Traefik `IngressRoute` with a prefix `HostRegexp` | The IP does not live in Git | [Traefik routers](https://doc.traefik.io/traefik/routing/routers/) · [K3s networking](https://docs.k3s.io/networking/networking-services) |
| No TLS for now: HTTP on the local network | A private IP (Multipass, `192.168.x`) cannot pass Let's Encrypt's HTTP-01; nip.io is not our DNS zone (no DNS-01) and does not issue wildcard certificates. On a public VM, Traefik's own ACME resolver would issue one certificate per URL | [nip.io](https://nip.io/) · [Traefik ACME resolver](https://doc.traefik.io/traefik/v3.7/reference/install-configuration/tls/certificate-resolvers/acme/) · [Let's Encrypt challenge types](https://letsencrypt.org/docs/challenge-types/) |
| App Ingress without a host | Answers on any name (IP or DNS) | [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/) |
| Traefik is the one that ships with K3s; we only configure it, with a minimal `HelmChartConfig` in Git | K3s installs and upgrades it; the configuration is versioned and easy to extend (`deploy/components/traefik/values.yaml`) | [K3s networking services](https://docs.k3s.io/networking/networking-services) · [K3s: Helm and HelmChartConfig](https://docs.k3s.io/add-ons/helm) |
| Traefik dashboard published by our own `IngressRoute` to `api@internal` (host `traefik.*`) | K3s enables the dashboard, but the chart ships its route off (`ingressRoute.dashboard.enabled: false`); this keeps the route in Git, with the same switch as the other UIs | [Traefik dashboard](https://doc.traefik.io/traefik/operations/dashboard/) · [IngressRoute](https://doc.traefik.io/traefik/reference/routing-configuration/kubernetes/crd/http/ingressroute/) · [traefik-helm-chart](https://github.com/traefik/traefik-helm-chart) |

### App, data and observability

| Decision | Why | Source |
| --- | --- | --- |
| Stateless API; configuration through environment variables | Replaceable pods; the image carries no config | [12-factor: config](https://12factor.net/config) |
| `302` redirect, not `301` | The browser caches a 301 and later clicks would never arrive | [MDN 302](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/302) |
| Rolling update with `maxUnavailable: 0` | A broken deploy gets stuck, not down | [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-update-deployment) |
| Loki *single binary* on the filesystem, 7 days | Enough for one node | [Loki deployment modes](https://grafana.com/docs/loki/latest/get-started/deployment-modes/) |
| Alloy reads logs through the Kubernetes API, plus the events | No node disk mounts; events explain pods that never logged | [loki.source.kubernetes](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.kubernetes/) · [kubernetes_events](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.kubernetes_events/) |

### Installation and docs

| Decision | Why | Source |
| --- | --- | --- |
| Idempotent bash scripts instead of Terraform | They install only what GitOps cannot; fewer moving parts | [Cluster bootstrapping](https://argo-cd.readthedocs.io/en/stable/operator-manual/cluster-bootstrapping/) |
| On macOS, an Ubuntu VM with Multipass; the repo is copied, not mounted | K3s needs Linux; macOS blocks Multipass from reading *Documents* | [Multipass](https://canonical.com/multipass/docs) |
| Uninstall with K3s's official script | Cleans services, data and networking | [K3s uninstall](https://docs.k3s.io/installation/uninstall) |
| Docs in GitHub Markdown: English in `docs/`, Spanish in `docs/es/`, a language link at the top of each page | They are read in the repo, so they must render on github.com; English matches the code and the scripts' output | [GitHub: writing and formatting](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax) |

## Glossary of sources

| Topic | Documentation |
| --- | --- |
| **Argo CD** | [Docs](https://argo-cd.readthedocs.io/en/stable/) · [Best practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/) · [Cluster bootstrapping](https://argo-cd.readthedocs.io/en/stable/operator-manual/cluster-bootstrapping/) · [Declarative setup](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/) · [ApplicationSet](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/) · [Helm](https://argo-cd.readthedocs.io/en/stable/user-guide/helm/) |
| **Helm** | [Charts](https://helm.sh/docs/topics/charts/) · [helm dependency](https://helm.sh/docs/helm/helm_dependency/) |
| **K3s** | [Docs](https://docs.k3s.io/) |
| **Vault and VSO** | [Vault](https://developer.hashicorp.com/vault/docs) · [VSO](https://developer.hashicorp.com/vault/docs/platform/k8s/vso) |
| **Cloudflare D1** | [D1](https://developers.cloudflare.com/d1/) · [Migrations](https://developers.cloudflare.com/d1/reference/migrations/) |
| **GitHub** | [Actions](https://docs.github.com/en/actions) · [GHCR](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) · [Template repositories](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository) · [Actions billing](https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions) |
| **Observability** | [Loki](https://grafana.com/docs/loki/latest/) · [Alloy](https://grafana.com/docs/alloy/latest/) · [Grafana](https://grafana.com/docs/grafana/latest/) |
| **Traefik** | [Docs](https://doc.traefik.io/traefik/) · [Core concepts](https://doc.traefik.io/traefik/getting-started/configuration-overview/) · [Rules and priority](https://doc.traefik.io/traefik/reference/routing-configuration/http/routing/rules-and-priority/) · [Traefik dashboard](https://doc.traefik.io/traefik/operations/dashboard/) · [traefik-helm-chart](https://github.com/traefik/traefik-helm-chart) |
| **Kubernetes** | [Docs](https://kubernetes.io/docs/) |
| **Reference project** | [Phalanx (Vera Rubin Observatory)](https://phalanx.lsst.io/) |
| **These docs** | [GitHub Markdown](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax) · [Alerts (`> [!NOTE]`)](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts) |
