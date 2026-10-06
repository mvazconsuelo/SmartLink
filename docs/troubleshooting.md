🌐 [Leer en español](es/troubleshooting.md) · 📖 [Docs index](README.md)

# 🔧 Troubleshooting

**Don't guess: walk a chain, from the outside in.**

| Chain | Links |
| --- | --- |
| 🌐 Traffic | DNS (nip.io) → Traefik → Ingress → Service → Pod → App → D1 |
| 🚚 Delivery | Git → CI → GHCR → Argo CD → K3s |
| 🔐 Secrets | Vault → VSO → Secret → Pod |

## By symptom

| Symptom | Look first at | Command |
| --- | --- | --- |
| Timeout | Network / VM | `curl http://<vm-ip>/health` · is the VM running? (`./scripts/install.sh ip`) |
| A dashboard (`argocd.<ip>.nip.io`) does not load | DNS / rule | `dig +short argocd.<ip>.nip.io` · `k get ingressroute -A` |
| `404 page not found` (plain text) | Ingress | `k get ingress,ingressroute -A` · Traefik dashboard: `http://traefik.<ip>.nip.io` › HTTP › Routers |
| `503` JSON | D1 | Loki: `{app="smartlink-api"} \|= "d1 request failed"` |
| `500` JSON | App / schema | `k -n smartlink-backend logs deploy/smartlink-api` (`no such table` → the migrations did not run: start CI) |
| `ImagePullBackOff` | GHCR / tag | `k describe pod <pod>` → Events |
| `https://…` answers `404` | No TLS | Use `http://`: the routes only listen on port 80 ([why](labs/10-dns-ingress.md#why-is-there-no-tls-yet)) |
| `CreateContainerConfigError` | Missing Secret | `k -n smartlink-backend get vaultstaticsecret,secret` |
| `CrashLoopBackOff` | Configuration | `k logs <pod> --previous` |
| Application `OutOfSync` | Drift or Git | Argo CD UI › *App Diff* |
| VSO `SYNCED False` | Vault | `v status` (sealed?) · events of the `VaultStaticSecret` |

## Inside a pod

```text
get ─► describe (events) ─► logs (--previous if it restarted) ─► Loki (what already happened)
```

To practice: [💥 Break the Platform](break.md).
