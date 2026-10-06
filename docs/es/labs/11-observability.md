🌐 [Read in English](../../labs/11-observability.md) · 📖 [Índice](../README.md)

# Lab 11 — Observabilidad

**Objetivo:** Encontrar un error sin entrar a cada pod.

## Idea

Alloy junta los logs de todos los pods y los eventos de Kubernetes. Los guarda en Loki, y se consultan en Grafana. No hay que confundirlo con las analytics de negocio (clicks, en D1): esto es para **operar**.

## Cómo funciona

```text
pods + eventos ─► Alloy ─► Loki (7 días) ─► Grafana
```

Labels: `namespace`, `pod`, `container`, `app` y `level`. Pocos a propósito: los datos variables (`code`, `user_id`) se buscan en el texto.

| Pregunta | LogQL |
| --- | --- |
| Errores de la API | `{namespace="smartlink-backend", level="ERROR"}` |
| Respuestas 500 | `{app="smartlink-api"} \|= "status=500"` |
| Fallas de D1 | `{app="smartlink-api"} \|= "d1 request failed"` |
| Requests lentas | `{app="smartlink-api"} \| logfmt \| duration_ms > 1000` |
| Problemas de pods | `{job=~"loki.source.kubernetes_events.*"} \|= "BackOff"` |

## Hacelo

Abrí `http://grafana.<ip>.nip.io` (usuario `admin`; password: `./scripts/install.sh access`) y generá errores:

```bash
for i in $(seq 20); do curl -s -o /dev/null http://<ip-vm>/no-existe-$i; done
```

En *Explore › Loki*: `{app="smartlink-api"} |= "redirect not_found"` → 20 líneas.

## Rompelo

[💥 Falla de D1](../break.md#4-falla-de-d1): el dashboard de negocio dice *que* falla; Loki dice *por qué* (`reason=auth`).

## Clave

- Logs `key=value` = texto consultable.
- Los eventos de Kubernetes explican los pods que nunca llegaron a loguear.

⬅️ [10 — DNS & Ingress](10-dns-ingress.md) · 📚 [Todos los labs](../README.md#labs) · ➡️ [12 — Rollback](12-rollback.md)