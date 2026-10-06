🌐 [Read in English](../references.md) · 📖 [Índice](README.md)

# 📚 Referencias

**De dónde sale cada decisión del proyecto.** Primero, el registro de ajustes: qué se hizo, por qué y en qué fuente se basa. Después, el glosario de fuentes por tema.

## Registro de decisiones

### GitOps y Argo CD

| Decisión | Por qué | Fuente |
| --- | --- | --- |
| Una carpeta por componente en `deploy/components/`, con `Chart.yaml` + `values.yaml` (+ `templates/`) | Todo lo de un componente en un lugar: versión, configuración, rutas | [Phalanx](https://phalanx.lsst.io/v/DM-35703/arch/repository.html) |
| Un **ApplicationSet** con *Git directory generator*: carpeta = Application = namespace | Agregar un componente es agregar una carpeta; sin Applications escritas a mano | [Git generator](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Generators-Git/) |
| Diferencias por componente con `templatePatch` (prune y selfHeal) | Las excepciones quedan explícitas y en un solo lugar | [ApplicationSet Template](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Template/) · [Go templates](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/GoTemplate/) |
| Charts oficiales como **dependencia** en un `Chart.yaml` propio, con versión fija | Versión al lado de su configuración; Renovate/Dependabot la entienden | [Helm: dependencias](https://helm.sh/docs/topics/charts/#chart-dependencies) · [Argo CD: manifests inmutables](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/) |
| Application raíz creada por script, con la URL del repo como value | Ningún archivo contiene tu URL; el repo sirve para cualquier fork | [Cluster bootstrapping](https://argo-cd.readthedocs.io/en/stable/operator-manual/cluster-bootstrapping/) |
| **AppProject `smartlink`** en vez de `default` | Limita repos de origen y namespaces de destino | [Projects](https://argo-cd.readthedocs.io/en/stable/user-guide/projects/) · [Declarative setup](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/) |
| Argo CD se administra a sí mismo, con `ServerSideApply=true` y `prune: false` | Upgrade con un commit; nunca se borra a sí mismo | [Declarative setup](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/) · [Sync options](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/) |
| `ignoreDifferences` en la anotación `restartedAt` de VSO | El reinicio que hace VSO no es drift | [Diffing](https://argo-cd.readthedocs.io/en/stable/user-guide/diffing/) |
| `SkipDryRunOnMissingResource` + `retry` | Los CRDs de VSO llegan desde otro componente | [Sync options](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/) |
| `selfHeal: false` en `smartlink-*` | El drift manual se ve como `OutOfSync` (lab 09) | [Automated sync](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/) |
| Deploy key de solo lectura para el repo privado | Argo CD solo puede leer este repo | [Private repositories](https://argo-cd.readthedocs.io/en/stable/user-guide/private-repositories/) · [GitHub deploy keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys) |
| Mismo repo para código y configuración (no un repo aparte) | Un solo fork para el lab. Costo: CI hace commits en `main`, hay que hacer `git pull` antes del push | [Best practices: repos separados](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/) |

### CI/CD

| Decisión | Por qué | Fuente |
| --- | --- | --- |
| CI escribe en Git, nunca en el cluster | La API de K3s no se expone; Argo CD tira del repo | [Best practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/) |
| Imagen con tag = SHA; release que reetiqueta sin reconstruir | Trazable; se publica exactamente lo que se probó | [buildx imagetools create](https://docs.docker.com/reference/cli/docker/buildx/imagetools/create/) |
| Imágenes amd64 + arm64 | La VM puede ser x86 o ARM (Multipass en Mac) | [Docker multi-platform](https://docs.docker.com/build/building/multi-platform/) |
| `paths-ignore` (`deploy/`, `scripts/`, `docs/`) y *Run workflow* manual | Cambios de configuración no disparan builds; primer deploy a demanda | [Workflow syntax](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions) |
| Migraciones D1 antes del deploy, aditivas | App nueva nunca contra schema viejo | [D1 migrations](https://developers.cloudflare.com/d1/reference/migrations/) |
| Chequeo de credenciales al inicio del job `migrate` | Error claro si el secret está vacío o el token es inválido | [Cloudflare: API tokens](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/) |

### Secretos y seguridad

| Decisión | Por qué | Fuente |
| --- | --- | --- |
| Vault con KV v2 + auth de Kubernetes, una policy de solo lectura por consumidor | Cada app lee solo su ruta | [Kubernetes auth](https://developer.hashicorp.com/vault/docs/auth/kubernetes) · [KV v2](https://developer.hashicorp.com/vault/docs/secrets/kv/kv-v2) |
| Vault con Raft en un volumen, sin PDB | Datos persistentes; el PDB con 1 réplica bloquearía los drains | [Raft storage](https://developer.hashicorp.com/vault/docs/configuration/storage/raft) · [Vault Helm](https://developer.hashicorp.com/vault/docs/platform/k8s/helm) |
| Init y unseal manuales; unseal key solo en el gestor | Vault no guarda su llave: si quedara junto a los datos, el cifrado no serviría | [Seal/unseal](https://developer.hashicorp.com/vault/docs/concepts/seal) |
| Vault Secrets Operator: `VaultStaticSecret`, `excludeRaw`, `rolloutRestartTargets` | La app solo ve un Secret; se reinicia sola cuando cambia | [VSO](https://developer.hashicorp.com/vault/docs/platform/k8s/vso) · [API reference](https://developer.hashicorp.com/vault/docs/platform/k8s/vso/api-reference) |
| K3s con `--secrets-encryption` | Los Secrets se cifran en disco | [K3s secrets encryption](https://docs.k3s.io/security/secrets-encryption) |
| Token GHCR `read:packages` en `registries.yaml` del nodo | K3s baja imágenes privadas sin Secrets en el cluster | [K3s private registry](https://docs.k3s.io/installation/private-registry) · [GHCR](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) |
| Token *fine-grained* de 1 día, solo este repo, sin *Contents* (opcional) | Automatiza GitHub sin dejar permisos de escritura; el repo no se puede precargar en el link | [Fine-grained PATs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) · [gh CLI](https://cli.github.com/manual/) |
| Ajustes del repo cerrados a mano antes de hacerlo público: Actions apagadas en la plantilla, token de solo lectura, aprobación para PRs de forks, secret scanning + push protection, `main` sin force-push | Un repo público lo lee cualquiera y lo forkea cualquiera; los valores por defecto están demasiado abiertos | [GitHub REST: Actions permissions](https://docs.github.com/en/rest/actions/permissions) · [GitHub REST: rulesets](https://docs.github.com/en/rest/repos/rules) · [About push protection](https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection) |
| `sudo -v` con mensaje propio | La clave la lee `sudo`, nunca el script | [sudo](https://www.sudo.ws/docs/man/sudo.man/) |
| Contenedores sin root, filesystem de solo lectura, sin token de ServiceAccount | Menos superficie si un pod se compromete | [Security context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/) |

### Red y acceso

| Decisión | Por qué | Fuente |
| --- | --- | --- |
| nip.io para los paneles (`argocd.<ip>.nip.io`) en vez de DuckDNS | Todo local, sin cuentas ni DNS propio | [nip.io](https://nip.io) |
| `IngressRoute` de Traefik con `HostRegexp` por prefijo | La IP no vive en Git | [Traefik routers](https://doc.traefik.io/traefik/routing/routers/) · [K3s networking](https://docs.k3s.io/networking/networking-services) |
| Sin TLS por ahora: HTTP en la red local | Una IP privada (Multipass, `192.168.x`) no puede pasar el HTTP-01 de Let's Encrypt; nip.io no es nuestra zona DNS (no hay DNS-01) y no emite certificados comodín. En una VM pública, el resolver ACME de Traefik emitiría un certificado por URL | [nip.io](https://nip.io/) · [Resolver ACME de Traefik](https://doc.traefik.io/traefik/v3.7/reference/install-configuration/tls/certificate-resolvers/acme/) · [Tipos de desafío de Let's Encrypt](https://letsencrypt.org/docs/challenge-types/) |
| Ingress de la app sin host | Responde en cualquier nombre (IP o DNS) | [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/) |
| Traefik es el que trae K3s; solo lo configuramos, con un `HelmChartConfig` mínimo en Git | K3s lo instala y lo actualiza; la configuración queda versionada y es fácil de ampliar (`deploy/components/traefik/values.yaml`) | [K3s: servicios de red](https://docs.k3s.io/networking/networking-services) · [K3s: Helm y HelmChartConfig](https://docs.k3s.io/add-ons/helm) |
| Panel de Traefik publicado con una `IngressRoute` propia hacia `api@internal` (host `traefik.*`) | K3s habilita el panel, pero el chart trae su ruta apagada (`ingressRoute.dashboard.enabled: false`); así la ruta queda en Git, con el mismo interruptor que las otras UIs | [Panel de Traefik](https://doc.traefik.io/traefik/operations/dashboard/) · [IngressRoute](https://doc.traefik.io/traefik/reference/routing-configuration/kubernetes/crd/http/ingressroute/) · [traefik-helm-chart](https://github.com/traefik/traefik-helm-chart) |

### App, datos y observabilidad

| Decisión | Por qué | Fuente |
| --- | --- | --- |
| API stateless; configuración por variables de entorno | Pods reemplazables; la imagen no lleva config | [12-factor: config](https://12factor.net/config) |
| Redirect `302`, no `301` | El navegador cachea el 301 y los clicks siguientes no llegarían | [MDN 302](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/302) |
| Rolling update con `maxUnavailable: 0` | Un deploy roto queda trabado, no caído | [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-update-deployment) |
| Loki *single binary* en filesystem, 7 días | Suficiente para un nodo | [Loki deployment modes](https://grafana.com/docs/loki/latest/get-started/deployment-modes/) |
| Alloy lee logs por la API de Kubernetes y también los eventos | Sin montar el disco del nodo; los eventos explican pods que nunca logearon | [loki.source.kubernetes](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.kubernetes/) · [kubernetes_events](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.kubernetes_events/) |

### Instalación y documentación

| Decisión | Por qué | Fuente |
| --- | --- | --- |
| Scripts bash idempotentes en vez de Terraform | Solo instalan lo que GitOps no puede; menos piezas | [Cluster bootstrapping](https://argo-cd.readthedocs.io/en/stable/operator-manual/cluster-bootstrapping/) |
| En macOS, una VM Ubuntu con Multipass; el repo se copia, no se monta | K3s necesita Linux; macOS bloquea el acceso de Multipass a *Documentos* | [Multipass](https://canonical.com/multipass/docs) |
| Desinstalar con el script oficial de K3s | Limpia servicios, datos y red | [K3s uninstall](https://docs.k3s.io/installation/uninstall) |
| Documentación en Markdown de GitHub: inglés en `docs/`, español en `docs/es/`, link de idioma arriba de cada página | Se lee en el repo, así que tiene que verse bien en github.com; el inglés coincide con el código y la salida de los scripts | [GitHub: escribir y dar formato](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax) |

## Glosario de fuentes

| Tema | Documentación |
| --- | --- |
| **Argo CD** | [Docs](https://argo-cd.readthedocs.io/en/stable/) · [Best practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/) · [Cluster bootstrapping](https://argo-cd.readthedocs.io/en/stable/operator-manual/cluster-bootstrapping/) · [Declarative setup](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/) · [ApplicationSet](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/) · [Helm](https://argo-cd.readthedocs.io/en/stable/user-guide/helm/) |
| **Helm** | [Charts](https://helm.sh/docs/topics/charts/) · [helm dependency](https://helm.sh/docs/helm/helm_dependency/) |
| **K3s** | [Docs](https://docs.k3s.io/) |
| **Vault y VSO** | [Vault](https://developer.hashicorp.com/vault/docs) · [VSO](https://developer.hashicorp.com/vault/docs/platform/k8s/vso) |
| **Cloudflare D1** | [D1](https://developers.cloudflare.com/d1/) · [Migraciones](https://developers.cloudflare.com/d1/reference/migrations/) |
| **GitHub** | [Actions](https://docs.github.com/en/actions) · [GHCR](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) · [Template repositories](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository) · [Facturación de Actions](https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions) |
| **Observabilidad** | [Loki](https://grafana.com/docs/loki/latest/) · [Alloy](https://grafana.com/docs/alloy/latest/) · [Grafana](https://grafana.com/docs/grafana/latest/) |
| **Traefik** | [Docs](https://doc.traefik.io/traefik/) · [Conceptos básicos](https://doc.traefik.io/traefik/getting-started/configuration-overview/) · [Reglas y prioridad](https://doc.traefik.io/traefik/reference/routing-configuration/http/routing/rules-and-priority/) · [Panel](https://doc.traefik.io/traefik/operations/dashboard/) · [traefik-helm-chart](https://github.com/traefik/traefik-helm-chart) |
| **Kubernetes** | [Docs](https://kubernetes.io/docs/) |
| **Proyecto de referencia** | [Phalanx (Vera Rubin Observatory)](https://phalanx.lsst.io/) |
| **Esta documentación** | [Markdown de GitHub](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax) · [Alertas (`> [!NOTE]`)](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts) |
