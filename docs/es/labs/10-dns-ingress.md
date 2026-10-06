🌐 [Read in English](../../labs/10-dns-ingress.md) · 📖 [Índice](../README.md)

# Lab 10 — DNS & Ingress

**Objetivo:** Llevar una request del navegador al pod correcto y saber en qué capa se corta.

## Idea

Todo entra por **un solo puerto**, el 80 de la VM, donde escucha **Traefik**. Traefik decide a qué servicio va cada request según la **ruta** (`/app`) o el **nombre** (`argocd.…`). Los nombres los resuelve [nip.io](https://nip.io): un DNS público que responde con la IP que va dentro del nombre (`argocd.192.168.252.4.nip.io` → `192.168.252.4`). No hay que crear cuentas ni registrar dominios.

Traefik en sí, sus rutas y su panel tienen su propia página: [Traefik](../traefik.md).

## Cómo funciona

| URL | Regla de Traefik | Va a |
| --- | --- | --- |
| `http://<ip>/app` | Ingress, ruta `/app` | Streamlit |
| `http://<ip>/…` (`/docs`, `/health`, `/{code}`) | Ingress, ruta `/` | FastAPI |
| `http://argocd.<ip>.nip.io` | IngressRoute, host `argocd.*` | Argo CD |
| `http://grafana.<ip>.nip.io` | IngressRoute, host `grafana.*` | Grafana |
| `http://vault.<ip>.nip.io` | IngressRoute, host `vault.*` | Vault UI |
| `http://traefik.<ip>.nip.io` | IngressRoute, host `traefik.*` | El panel propio de Traefik (`api@internal`) |

- **Las reglas no tienen la IP.** Los Ingress de SmartLink no tienen host, y las IngressRoute de los paneles (`templates/ui-route.yaml` en las carpetas de `argocd`, `grafana` y `vault`) matchean el **prefijo** del nombre. La misma configuración de Git sirve en cualquier VM.
- **Argo CD, Grafana y Vault tienen su propio login; el panel de Traefik no** (es de solo lectura, pero lista todas las rutas). En una VM expuesta a Internet poné `uiRoutes.enabled: false` en `deploy/root/values.yaml` y entrá por `port-forward`.
- **Traefik viene incluido en K3s**, por eso su configuración propia no está en este repo. K3s habilita su panel pero no publica ninguna ruta hacia él: `deploy/components/traefik/` es esa ruta.

| Capa | Cómo se prueba |
| --- | --- |
| DNS (nip.io) | `dig +short argocd.<ip>.nip.io` → `<ip>` |
| Traefik | `curl -si http://<ip>/health` |
| Reglas | `k get ingress,ingressroute -A` |
| Service | `k -n smartlink-backend get endpoints` |
| Pod | `k get pods -A` |

## ¿Dónde se configura Traefik?

Traefik viene con K3s, que lo instala y lo actualiza. Lo que controlamos **nosotros** vive en una sola carpeta, `deploy/components/traefik/`:

| Archivo | Qué hace |
| --- | --- |
| `values.yaml` → `traefik:` | **Su configuración.** Mínima a propósito: solo el access log. Lo que agregues bajo esa clave va directo al chart de Traefik |
| `templates/helm-chart-config.yaml` | Se la pasa a K3s como [`HelmChartConfig`](https://docs.k3s.io/add-ons/helm), la forma propia de K3s para personalizar un chart empaquetado. K3s actualiza Traefik solo |
| `templates/ui-route.yaml` | La ruta al panel de Traefik. El chart trae `ingressRoute.dashboard.enabled: false`, así que K3s corre el panel pero no publica ninguna entrada |

Para agregar más, editá ese bloque `traefik:` y hacé push. Todo lo que acepta el chart está en su [values.yaml](https://github.com/traefik/traefik-helm-chart):

**`deploy/components/traefik/values.yaml`**

```yaml
traefik:
  accessLog:
    enabled: true
  log:
    level: DEBUG        # más detalle en el log propio de Traefik
  deployment:
    replicas: 2         # sin corte mientras Traefik se reinicia
```

> [!WARNING]
> **Cada cambio reinicia Traefik.** Con una réplica (el valor por defecto) hay unos segundos sin ingress en el puerto 80, para todas las UIs y para la app.

El access log pasa por Alloy hasta Loki, así que en Grafana: `{app="traefik"}`.

Las rutas hacia tus apps son aparte: el `Ingress` en `deploy/components/smartlink-*/templates/ingress.yaml` y la `IngressRoute` en el `templates/ui-route.yaml` de `argocd`, `grafana`, `vault` y `traefik`.

## ¿Por qué no hay TLS (todavía)?

Todo se sirve por **HTTP plano, en el puerto 80**. Es un límite deliberado del lab, no un olvido.

**Qué pasa hoy**

- Traefik también escucha en el 443, pero con su certificado autofirmado genérico (`TRAEFIK DEFAULT CERT`), y nuestras rutas solo escuchan en el puerto 80: `https://…` responde `404`.
- Los logins (Argo CD, Grafana, Vault y el JWT de la app) viajan **sin cifrar** por tu red.

**Por qué no lo agregamos**

| Obstáculo | Detalle |
| --- | --- |
| La VM tiene una IP privada | En Multipass es `192.168.x`. [Let's Encrypt](https://letsencrypt.org/docs/challenge-types/) comprueba que el nombre es tuyo entrando a tu host desde Internet (HTTP-01), y una IP privada no lo permite |
| nip.io no es nuestra zona DNS | La otra forma (DNS-01) necesita escribir un registro TXT en la zona. En nip.io no podemos, y además [no emite certificados comodín](https://nip.io/) |
| Una CA propia funciona, con una condición | cert-manager + una CA nuestra no necesita Internet, pero el navegador advierte hasta que confíes en esa CA, y suma un componente |
| Un certificado de confianza pide un dominio | DuckDNS o un dominio en Cloudflare lo resuelven (DNS-01), pero implican una cuenta más o pagar un dominio |

**Qué hacer mientras tanto**

- Usá el lab en una **red de confianza** y no expongas la VM a Internet tal como está.
- En una VM alcanzable, poné `uiRoutes.enabled: false` en `deploy/root/values.yaml`. Igual el login de la app seguiría en claro, así que **una VM pública necesita TLS primero**.

**Cómo se agregaría (no implementado, no probado)**

En una VM con **IP pública**, Traefik puede pedirle a Let's Encrypt **un certificado por cada URL**, solo, con HTTP-01 y nombres del estilo `argocd.<ip>.nip.io` ([su resolver de ACME](https://doc.traefik.io/traefik/v3.7/reference/install-configuration/tls/certificate-resolvers/acme/); nip.io cuenta que Let's Encrypt le subió el límite a 250.000 certificados). Haría falta:

1. una entrada `certificatesResolvers` en el bloque `traefik:` de `deploy/components/traefik/values.yaml`, con un volumen para guardar los certificados;
2. que las rutas escuchen en `websecure` con `tls.certResolver`;
3. la IP pública de la VM como valor de instalación: Traefik pide certificados para nombres exactos (`Host(...)`), no para la coincidencia por prefijo que usamos ahora.

Con una IP privada no hay opción de confianza con nip.io: ese es el caso de una CA propia o de DuckDNS/Cloudflare.

## Hacelo

```bash
dig +short argocd.<ip>.nip.io                     # la IP que va en el nombre
curl -si http://<ip>/health | head -1              # 200: la app
curl -si http://grafana.<ip>.nip.io | head -1      # 302 → /login: Grafana
curl -si http://<ip> -H 'Host: vault.x' | head -1  # 307 → /ui/: el nombre decide, no la IP
```

La última línea muestra que a Traefik solo le importa el header `Host`: nip.io es solo una forma cómoda de ponerlo desde el navegador.

Ahora abrí `http://traefik.<ip>.nip.io` → *HTTP › Routers*: ves todas las reglas de arriba, con el servicio al que apunta cada una. Cuando algo responde `404 page not found`, este es el primer lugar donde mirar.

## Rompelo

[💥 DNS / Ingress](../break.md#7-dns--ingress): con la ruta del backend en `/api`, `/health` devuelve `404 page not found` (texto de Traefik). La request llegó al cluster, pero no hay regla.

## Clave

- Un solo puerto, muchas apps: las separa el nombre o la ruta.
- Quién responde el error dice la capa: timeout = red; `404` de Traefik = falta una regla; `404` JSON = app.

⬅️ [09 — GitOps](09-gitops.md) · 📚 [Todos los labs](../README.md#labs) · ➡️ [11 — Observabilidad](11-observability.md)