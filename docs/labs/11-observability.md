🌐 [Leer en español](../es/labs/11-observability.md) · 📖 [Docs index](../README.md)

# Lab 11 — Observability

**Goal:** Find an error without going into each pod.

## Idea

Alloy collects the logs of every pod and the Kubernetes events. It stores them in Loki, and you query them in Grafana. Do not confuse this with business analytics (clicks, in D1): this is for **operating** the system.

## How it works

```text
pods + events ─► Alloy ─► Loki (7 days) ─► Grafana
```

Labels: `namespace`, `pod`, `container`, `app` and `level`. Few on purpose: variable data (`code`, `user_id`) is searched in the text.

| Question | LogQL |
| --- | --- |
| API errors | `{namespace="smartlink-backend", level="ERROR"}` |
| 500 responses | `{app="smartlink-api"} \|= "status=500"` |
| D1 failures | `{app="smartlink-api"} \|= "d1 request failed"` |
| Slow requests | `{app="smartlink-api"} \| logfmt \| duration_ms > 1000` |
| Pod problems | `{job=~"loki.source.kubernetes_events.*"} \|= "BackOff"` |

## Do it

Open `http://grafana.<ip>.nip.io` (user `admin`; password: `./scripts/install.sh access`) and generate errors:

```bash
for i in $(seq 20); do curl -s -o /dev/null http://<vm-ip>/does-not-exist-$i; done
```

In *Explore › Loki*: `{app="smartlink-api"} |= "redirect not_found"` → 20 lines.

## Break it

[💥 D1 failure](../break.md#4-d1-failure): the business dashboard tells you *that* it fails; Loki tells you *why* (`reason=auth`).

## Key points

- `key=value` logs = queryable text.
- Kubernetes events explain the pods that never got to log anything.

⬅️ [10 — DNS & Ingress](10-dns-ingress.md) · 📚 [All labs](../README.md#labs) · ➡️ [12 — Rollback](12-rollback.md)