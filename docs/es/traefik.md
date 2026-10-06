🌐 [Read in English](../traefik.md) · 📖 [Índice](README.md)

# 🚦 Traefik

**La única puerta de entrada al cluster.** Toda request de tu navegador, a la app o a un panel, pasa por Traefik. Viene incluido en K3s: no lo instalamos, solo le damos rutas.

## El camino de una request

```text
navegador ─► puerto 80 ─► entrypoint "web" ─► router (una regla) ─► Service ─► Pod
```

| Pieza | Qué es | En SmartLink |
| --- | --- | --- |
| **Entrypoint** | Un puerto en el que Traefik escucha | `web` (publicado como el puerto 80 de la VM), `websecure` (443, sin uso: no hay TLS) y `traefik` (8080, interno, para su propio panel) |
| **Router** | Una regla, y adónde mandar lo que la cumple | Uno por cada ruta de la tabla siguiente |
| **Service** | El Service de Kubernetes que recibe la request | `smartlink-api`, `smartlink-frontend`, `argocd-server`, `grafana`, `vault-ui` |
| **Middleware** | Un paso entre el router y el service (login, redirecciones, límites) | Ninguno por ahora |
| **Provider** | De dónde lee Traefik sus rutas | La API de Kubernetes: objetos `Ingress` e `IngressRoute` |

## Nuestras rutas

| URL | Regla | Objeto | Definida en |
| --- | --- | --- | --- |
| `http://<ip>/` (y `/docs`, `/health`, `/<código>`) | Cualquier request, prefijo de path `/` | `Ingress` | `deploy/components/smartlink-backend/templates/ingress.yaml` |
| `http://<ip>/app` | Prefijo de path `/app` | `Ingress` | `deploy/components/smartlink-frontend/templates/ingress.yaml` |
| `http://argocd.<ip>.nip.io` | El host empieza con `argocd.` | `IngressRoute` → `argocd-server:80` | `deploy/components/argocd/templates/ui-route.yaml` |
| `http://grafana.<ip>.nip.io` | El host empieza con `grafana.` | `IngressRoute` → `grafana:80` | `deploy/components/grafana/templates/ui-route.yaml` |
| `http://vault.<ip>.nip.io` | El host empieza con `vault.` | `IngressRoute` → `vault-ui:8200` | `deploy/components/vault/templates/ui-route.yaml` |
| `http://traefik.<ip>.nip.io` | El host empieza con `traefik.` | `IngressRoute` → `api@internal` | `deploy/components/traefik/templates/ui-route.yaml` |

## ¿Ingress o IngressRoute?

| | `Ingress` | `IngressRoute` |
| --- | --- | --- |
| Qué es | El objeto estándar de Kubernetes, que entiende cualquier ingress controller | El objeto propio de Traefik |
| Se usa para | La app | Los cuatro paneles |
| Por qué | Es portable, y sin host responde en cualquier nombre (una IP o un dominio) | Puede comparar el host **por patrón** (`HostRegexp`), así que la IP de la VM no queda escrita en Git, y puede apuntar al servicio interno de Traefik `api@internal`, cosa que un `Ingress` no puede |

## Cuando dos reglas coinciden

Traefik ordena los routers por el **largo de su regla**: se prueba primero la más larga ([reglas y prioridad](https://doc.traefik.io/traefik/reference/routing-configuration/http/routing/rules-and-priority/)). Eso es lo que hace que esto funcione:

- `/app` (más larga) le gana a `/`, así que el dashboard no cae en la API.
- Una request a `argocd.<ip>.nip.io` también cumple el `/` de la API, pero la regla del host es más larga, así que llega a Argo CD.

Largo no es lo mismo que especificidad: una regla larga y amplia puede tapar a una corta y específica. Si una ruta "no llega", mirá primero las reglas que compiten.

## El panel

`http://traefik.<ip>.nip.io` muestra la vista propia de Traefik de lo que está configurado. Es de solo lectura y **no tiene login** (más en el [Lab 10](labs/10-dns-ingress.md#por-qué-no-hay-tls-todavía)).

- *HTTP › Routers* tiene una fila por router, con su regla, entrypoint, servicio y provider. Las rutas de arriba aparecen con provider `kubernetes` (si vienen de un `Ingress`) o `kubernetescrd` (si vienen de una `IngressRoute`). Los `@internal` son los propios de Traefik.
- En nuestra VM listaba 10 routers y 0 middlewares: las seis rutas de arriba y los internos de Traefik.
- Si falta una ruta, es que su objeto no se aplicó: `k get ingress,ingressroute -A`.

## Qué responde cuando algo anda mal

| Ves | Significa |
| --- | --- |
| `404 page not found` (texto plano) | **Ningún router coincidió**: path o host equivocado, o la ruta no existe. El `404` de la app, en cambio, es JSON |
| `https://…` responde `404` | Las rutas solo escuchan en `web`; no hay TLS |
| `503` / `502` de Traefik | Un router coincidió, pero los pods de atrás no están listos o fallaron. Es el comportamiento general de Traefik y no lo reprodujimos en el lab |

La [falla 7](break.md#7-dns--ingress) de Break the Platform provoca la primera a propósito.

## Logs

```bash
k -n kube-system logs deploy/traefik
```

El access log (una línea por request) está prendido, y Alloy lo manda a Loki: en Grafana, `{app="traefik"}` ([Lab 11](labs/11-observability.md)).

## Configuración

Traefik en sí lo configura K3s. Lo que controlamos nosotros es una carpeta, `deploy/components/traefik/`: su configuración mínima (`values.yaml`) y la ruta a su panel. Cómo cambiarla, y por qué todavía no hay TLS, está en el [Lab 10](labs/10-dns-ingress.md#dónde-se-configura-traefik).

## Fuentes

[Conceptos básicos](https://doc.traefik.io/traefik/getting-started/configuration-overview/) · [Reglas y prioridad](https://doc.traefik.io/traefik/reference/routing-configuration/http/routing/rules-and-priority/) · [Provider Kubernetes Ingress](https://doc.traefik.io/traefik/reference/routing-configuration/kubernetes/ingress/) · [IngressRoute](https://doc.traefik.io/traefik/reference/routing-configuration/kubernetes/crd/http/ingressroute/) · [Dashboard](https://doc.traefik.io/traefik/operations/dashboard/)
