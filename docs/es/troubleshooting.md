🌐 [Read in English](../troubleshooting.md) · 📖 [Índice](README.md)

# 🔧 Troubleshooting

**No se adivina: se recorre una cadena, de afuera hacia adentro.**

| Cadena | Eslabones |
| --- | --- |
| 🌐 Tráfico | DNS (nip.io) → Traefik → Ingress → Service → Pod → App → D1 |
| 🚚 Entrega | Git → CI → GHCR → Argo CD → K3s |
| 🔐 Secretos | Vault → VSO → Secret → Pod |

## Por síntoma

| Síntoma | Mirá primero | Comando |
| --- | --- | --- |
| Timeout | Red / VM | `curl http://<ip-vm>/health` · ¿la VM está prendida? (`./scripts/install.sh ip`) |
| Un panel (`argocd.<ip>.nip.io`) no carga | DNS / regla | `dig +short argocd.<ip>.nip.io` · `k get ingressroute -A` |
| `404 page not found` (texto) | Ingress | `k get ingress,ingressroute -A` · Panel de Traefik: `http://traefik.<ip>.nip.io` › HTTP › Routers |
| `503` JSON | D1 | Loki: `{app="smartlink-api"} \|= "d1 request failed"` |
| `500` JSON | App / schema | `k -n smartlink-backend logs deploy/smartlink-api` (`no such table` → no corrieron las migraciones: lanzá CI) |
| `ImagePullBackOff` | GHCR / tag | `k describe pod <pod>` → Events |
| `https://…` responde `404` | No hay TLS | Usá `http://`: las rutas solo escuchan en el puerto 80 ([por qué](labs/10-dns-ingress.md#por-qué-no-hay-tls-todavía)) |
| `CreateContainerConfigError` | Secret faltante | `k -n smartlink-backend get vaultstaticsecret,secret` |
| `CrashLoopBackOff` | Configuración | `k logs <pod> --previous` |
| Application `OutOfSync` | Drift o Git | UI de Argo CD › *App Diff* |
| VSO `SYNCED False` | Vault | `v status` (¿sellado?) · eventos del `VaultStaticSecret` |

## Dentro de un pod

```text
get ─► describe (eventos) ─► logs (--previous si se reinició) ─► Loki (lo que ya pasó)
```

Para practicar: [💥 Break the Platform](break.md).
