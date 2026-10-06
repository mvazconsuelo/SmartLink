🌐 [Leer en español](es/traefik.md) · 📖 [Docs index](README.md)

# 🚦 Traefik

**The only door into the cluster.** Every request from your browser, to the app or to a dashboard, goes through Traefik. It ships with K3s: we do not install it, we only give it routes.

## The path of a request

```text
browser ─► port 80 ─► entrypoint "web" ─► router (a rule) ─► Service ─► Pod
```

| Piece | What it is | In SmartLink |
| --- | --- | --- |
| **Entrypoint** | A port Traefik listens on | `web` (published as port 80 of the VM), `websecure` (443, unused: there is no TLS) and `traefik` (8080, internal, for its own dashboard) |
| **Router** | A rule, and where to send whatever matches it | One per route in the next table |
| **Service** | The Kubernetes Service that receives the request | `smartlink-api`, `smartlink-frontend`, `argocd-server`, `grafana`, `vault-ui` |
| **Middleware** | A step between the router and the service (login, redirects, limits) | None yet |
| **Provider** | Where Traefik reads its routes from | The Kubernetes API: `Ingress` and `IngressRoute` objects |

## Our routes

| URL | Rule | Object | Defined in |
| --- | --- | --- | --- |
| `http://<ip>/` (and `/docs`, `/health`, `/<code>`) | Any request, path prefix `/` | `Ingress` | `deploy/components/smartlink-backend/templates/ingress.yaml` |
| `http://<ip>/app` | Path prefix `/app` | `Ingress` | `deploy/components/smartlink-frontend/templates/ingress.yaml` |
| `http://argocd.<ip>.nip.io` | Host starts with `argocd.` | `IngressRoute` → `argocd-server:80` | `deploy/components/argocd/templates/ui-route.yaml` |
| `http://grafana.<ip>.nip.io` | Host starts with `grafana.` | `IngressRoute` → `grafana:80` | `deploy/components/grafana/templates/ui-route.yaml` |
| `http://vault.<ip>.nip.io` | Host starts with `vault.` | `IngressRoute` → `vault-ui:8200` | `deploy/components/vault/templates/ui-route.yaml` |
| `http://traefik.<ip>.nip.io` | Host starts with `traefik.` | `IngressRoute` → `api@internal` | `deploy/components/traefik/templates/ui-route.yaml` |

## Ingress or IngressRoute?

| | `Ingress` | `IngressRoute` |
| --- | --- | --- |
| What it is | The standard Kubernetes object, understood by any ingress controller | Traefik's own object |
| Used for | The app | The four dashboards |
| Why | Portable, and with no host it answers on any name (an IP or a domain) | It can match a host **by pattern** (`HostRegexp`), so the VM's IP is not written in Git, and it can point to Traefik's internal service `api@internal`, which an `Ingress` cannot |

## When two rules match

Traefik sorts the routers by the **length of their rule**: the longest is tried first ([rules and priority](https://doc.traefik.io/traefik/reference/routing-configuration/http/routing/rules-and-priority/)). That is what makes this work:

- `/app` (longer) wins over `/`, so the dashboard does not fall into the API.
- A request to `argocd.<ip>.nip.io` also matches the API's `/`, but the host rule is longer, so it reaches Argo CD.

Length is not specificity: a long, broad rule can hide a short, specific one. If a route "does not arrive", look at the competing rules first.

## The dashboard

`http://traefik.<ip>.nip.io` shows Traefik's own view of what is configured. It is read-only and has **no login** (more in [Lab 10](labs/10-dns-ingress.md#why-is-there-no-tls-yet)).

- *HTTP › Routers* has one row per router, with its rule, entrypoint, service and provider. The routes above appear with provider `kubernetes` (from an `Ingress`) or `kubernetescrd` (from an `IngressRoute`). The `@internal` ones are Traefik's own.
- On our VM it listed 10 routers and 0 middlewares: the six routes above, and Traefik's internal ones.
- A route that is missing means its object was not applied: `k get ingress,ingressroute -A`.

## What it answers when something is wrong

| You see | It means |
| --- | --- |
| `404 page not found` (plain text) | **No router matched**: wrong path or host, or the route does not exist. The app's own `404` is JSON |
| `https://…` answers `404` | The routes only listen on `web`; there is no TLS |
| `503` / `502` from Traefik | A router matched but the pods behind it are not ready, or failed. This is Traefik's general behavior and we did not reproduce it in the lab |

The [failure 7](break.md#7-dns--ingress) of Break the Platform makes the first one happen on purpose.

## Logs

```bash
k -n kube-system logs deploy/traefik
```

The access log (one line per request) is turned on, and Alloy ships it to Loki: in Grafana, `{app="traefik"}` ([Lab 11](labs/11-observability.md)).

## Configuration

Traefik itself is configured by K3s. What we control is one folder, `deploy/components/traefik/`: its minimal configuration (`values.yaml`) and the route to its dashboard. How to change it, and why there is no TLS yet, are in [Lab 10](labs/10-dns-ingress.md#where-is-traefik-configured).

## Sources

[Core concepts](https://doc.traefik.io/traefik/getting-started/configuration-overview/) · [Rules and priority](https://doc.traefik.io/traefik/reference/routing-configuration/http/routing/rules-and-priority/) · [Kubernetes Ingress provider](https://doc.traefik.io/traefik/reference/routing-configuration/kubernetes/ingress/) · [IngressRoute](https://doc.traefik.io/traefik/reference/routing-configuration/kubernetes/crd/http/ingressroute/) · [Dashboard](https://doc.traefik.io/traefik/operations/dashboard/)
