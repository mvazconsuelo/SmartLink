🌐 [Leer en español](../es/labs/10-dns-ingress.md) · 📖 [Docs index](../README.md)

# Lab 10 — DNS & Ingress

**Goal:** Take a request from the browser to the right pod, and know at which layer it breaks.

## Idea

Everything comes in through **a single port**, the VM's port 80, where **Traefik** listens. Traefik decides which service each request goes to by its **path** (`/app`) or its **name** (`argocd.…`). Names are resolved by [nip.io](https://nip.io): a public DNS that answers with the IP embedded in the name (`argocd.192.168.252.4.nip.io` → `192.168.252.4`). No accounts, no domains to register.

Traefik itself, its routes and its dashboard have their own page: [Traefik](../traefik.md).

## How it works

| URL | Traefik rule | Goes to |
| --- | --- | --- |
| `http://<ip>/app` | Ingress, path `/app` | Streamlit |
| `http://<ip>/…` (`/docs`, `/health`, `/{code}`) | Ingress, path `/` | FastAPI |
| `http://argocd.<ip>.nip.io` | IngressRoute, host `argocd.*` | Argo CD |
| `http://grafana.<ip>.nip.io` | IngressRoute, host `grafana.*` | Grafana |
| `http://vault.<ip>.nip.io` | IngressRoute, host `vault.*` | Vault UI |
| `http://traefik.<ip>.nip.io` | IngressRoute, host `traefik.*` | Traefik's own dashboard (`api@internal`) |

- **The rules do not contain the IP.** SmartLink's Ingresses have no host, and the dashboards' IngressRoutes (`templates/ui-route.yaml` in the `argocd`, `grafana` and `vault` folders) match the **prefix** of the name. The same Git config works on any VM.
- **Argo CD, Grafana and Vault have their own login; Traefik's dashboard has none** (it is read-only, but it lists every route). On a VM exposed to the Internet set `uiRoutes.enabled: false` in `deploy/root/values.yaml` and use `port-forward`.
- **Traefik is built into K3s**, so its own configuration is not in this repo. K3s enables its dashboard but publishes no route to it: `deploy/components/traefik/` is that route.

| Layer | How to test it |
| --- | --- |
| DNS (nip.io) | `dig +short argocd.<ip>.nip.io` → `<ip>` |
| Traefik | `curl -si http://<ip>/health` |
| Rules | `k get ingress,ingressroute -A` |
| Service | `k -n smartlink-backend get endpoints` |
| Pod | `k get pods -A` |

## Where is Traefik configured?

Traefik ships with K3s, which installs and upgrades it. What **we** control lives in one folder, `deploy/components/traefik/`:

| File | What it does |
| --- | --- |
| `values.yaml` → `traefik:` | **Its configuration.** Minimal on purpose: only the access log. Whatever you add under that key goes straight to Traefik's chart |
| `templates/helm-chart-config.yaml` | Passes it to K3s as a [`HelmChartConfig`](https://docs.k3s.io/add-ons/helm), K3s's own way to customize a packaged chart. K3s upgrades Traefik by itself |
| `templates/ui-route.yaml` | The route to Traefik's dashboard. The chart ships `ingressRoute.dashboard.enabled: false`, so K3s runs the dashboard but publishes no way in |

To add more, edit that `traefik:` block and push. Everything the chart accepts is in its [values.yaml](https://github.com/traefik/traefik-helm-chart):

**`deploy/components/traefik/values.yaml`**

```yaml
traefik:
  accessLog:
    enabled: true
  log:
    level: DEBUG        # more detail in Traefik's own log
  deployment:
    replicas: 2         # no gap while Traefik restarts
```

> [!WARNING]
> **Every change rolls Traefik.** With one replica (the default) there are a few seconds without ingress on port 80, for every UI and for the app.

The access log goes through Alloy to Loki, so in Grafana: `{app="traefik"}`.

The routes to your apps are separate: the `Ingress` in `deploy/components/smartlink-*/templates/ingress.yaml` and the `IngressRoute` in the `templates/ui-route.yaml` of `argocd`, `grafana`, `vault` and `traefik`.

## Why is there no TLS (yet)?

Everything is served over **plain HTTP, on port 80**. This is a deliberate limit of the lab, not an oversight.

**What happens today**

- Traefik also listens on 443, but with its generic self-signed certificate (`TRAEFIK DEFAULT CERT`), and our routes only listen on port 80: `https://…` answers `404`.
- The logins (Argo CD, Grafana, Vault and the app's own JWT) cross your network **unencrypted**.

**Why we did not add it**

| Obstacle | Detail |
| --- | --- |
| The VM has a private IP | In the Multipass setup it is `192.168.x`. [Let's Encrypt](https://letsencrypt.org/docs/challenge-types/) proves you own a name by reaching your host from the Internet (HTTP-01), which a private IP cannot do |
| nip.io is not our DNS zone | The other way (DNS-01) needs to write a TXT record in the zone. We cannot do that in nip.io, which also [does not issue wildcard certificates](https://nip.io/) |
| A local CA works, with a catch | cert-manager + our own CA needs no Internet, but the browser warns until you trust that CA, and it adds a component |
| A trusted certificate needs a domain | DuckDNS or a domain on Cloudflare would do it (DNS-01), but it means one more account, or paying for a domain |

**What to do about it**

- Use the lab on a **trusted network** and do not expose the VM to the Internet as it is.
- On a VM that is reachable, set `uiRoutes.enabled: false` in `deploy/root/values.yaml`. That still leaves the app's login in clear, so **a public VM needs TLS first**.

**How it would be added (not implemented, not tested)**

On a VM with a **public IP**, Traefik can ask Let's Encrypt for **one certificate per URL** by itself, over HTTP-01, with `argocd.<ip>.nip.io`-style names ([its ACME resolver](https://doc.traefik.io/traefik/v3.7/reference/install-configuration/tls/certificate-resolvers/acme/); nip.io says Let's Encrypt raised its rate limit to 250,000 certificates). It would take:

1. a `certificatesResolvers` entry in the `traefik:` block of `deploy/components/traefik/values.yaml`, with a volume to keep the certificates;
2. the routes listening on `websecure` with `tls.certResolver`;
3. the VM's public IP as an install value: Traefik requests certificates for exact names (`Host(...)`), not for the prefix match we use now.

On a private IP there is no trusted option with nip.io: that is the case for a local CA or for DuckDNS/Cloudflare.

## Do it

```bash
dig +short argocd.<ip>.nip.io                     # the IP inside the name
curl -si http://<ip>/health | head -1              # 200: the app
curl -si http://grafana.<ip>.nip.io | head -1      # 302 → /login: Grafana
curl -si http://<ip> -H 'Host: vault.x' | head -1  # 307 → /ui/: the name decides, not the IP
```

The last line shows that Traefik only cares about the `Host` header: nip.io is just a convenient way to set it from the browser.

Now open `http://traefik.<ip>.nip.io` → *HTTP › Routers*: you see every rule above, with the service each one points to. When something answers `404 page not found`, this is the first place to look.

## Break it

[💥 DNS / Ingress](../break.md#7-dns--ingress): with the backend path set to `/api`, `/health` returns `404 page not found` (Traefik's text). The request reached the cluster, but no rule matched.

## Key points

- One port, many apps: the name or the path separates them.
- Who answers the error tells you the layer: timeout = network; Traefik `404` = a rule is missing; JSON `404` = the app.

⬅️ [09 — GitOps](09-gitops.md) · 📚 [All labs](../README.md#labs) · ➡️ [11 — Observability](11-observability.md)