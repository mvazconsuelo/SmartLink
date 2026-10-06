🌐 [Read in English](../stack.md) · 📖 [Índice](README.md)

# 🧰 El stack

**Qué es cada tecnología, qué hace en SmartLink y por qué la usamos.** Si un nombre de los labs no te suena, empezá por acá.

## La app

| Tecnología | Qué es | Qué hace acá | Por qué |
| --- | --- | --- | --- |
| **FastAPI** | Un framework web de Python | La API: cuentas, links cortos, redirecciones, estadísticas. Sirve su propia documentación en `/docs` | Es chico, tipado, y la documentación interactiva sale gratis. La app no es el punto del lab, así que se mantiene simple |
| **Streamlit** | Una librería de Python para interfaces web | El dashboard, bajo `/app` | Una interfaz sin cadena de herramientas de JavaScript, como servicio aparte para poder desplegar cada uno por separado |
| **Cloudflare D1** | Una base de datos SQL administrada (SQLite) | Guarda usuarios, links y clicks, **fuera** del cluster | Los pods quedan sin estado y reemplazables, no hay una base que operar, y el schema cambia con migraciones versionadas |
| **Wrangler** | La herramienta de línea de comandos de Cloudflare | Aplica las migraciones de D1 desde CI | Es la forma oficial de correr migraciones de D1 |

## Construir y entregar

| Tecnología | Qué es | Qué hace acá | Por qué |
| --- | --- | --- | --- |
| **Docker** | Empaqueta una app y sus dependencias como imagen | Construye las dos imágenes: sin root, sistema de archivos de solo lectura, amd64 y arm64 | El mismo artefacto corre en cualquier nodo, y no lleva configuración ni secretos |
| **GitHub Actions** | CI/CD que vive en el repo | Corre los tests, construye las imágenes, aplica las migraciones y escribe el tag nuevo en Git | Está junto al código, y nunca necesita acceso al cluster |
| **GHCR** | El registry de contenedores de GitHub | Guarda las imágenes, con el SHA del commit como tag | Es gratis, está junto al repo, y CI entra con el token que GitHub ya da |
| **Helm** | Un gestor de paquetes para Kubernetes: plantillas más values | Empaqueta nuestras dos apps; los charts oficiales (Vault, Loki…) también se instalan con él | Las herramientas que instalamos ya vienen como charts de Helm, y `values.yaml` es donde se configura cada una |
| **Argo CD** | Un controlador GitOps | Mantiene el cluster igual a lo que dice Git; un ApplicationSet crea una Application por carpeta de `deploy/components/` | Desplegar es un commit, volver atrás es un `git revert`, y un cambio manual se ve como drift |

## La plataforma

| Tecnología | Qué es | Qué hace acá | Por qué |
| --- | --- | --- | --- |
| **K3s** | Kubernetes en un solo binario liviano | Corre todo | Es Kubernetes de verdad, entra en una VM de 2 CPU y 4 GB, y ya incluye Traefik y almacenamiento |
| **Traefik** | Un ingress controller (un reverse proxy) | La única entrada: manda cada request del puerto 80 al Service correcto ([más](traefik.md)) | Viene con K3s, así que no hay nada que instalar |
| **nip.io** | Un DNS público que responde con la IP escrita en el nombre | `argocd.<ip>.nip.io` resuelve a `<ip>` | Los paneles tienen nombre sin configurar ningún DNS |
| **Multipass** | Máquinas virtuales Ubuntu en tu computadora | En una Mac, aloja la VM donde corre K3s | K3s necesita Linux, y esto crea una con un solo comando |

## Secretos

| Tecnología | Qué es | Qué hace acá | Por qué |
| --- | --- | --- | --- |
| **Vault** | Un almacén de secretos | Guarda el token de Cloudflare, `JWT_SECRET` y el password de Grafana, con una policy de solo lectura por app | Los valores nunca pasan por Git, y cada app solo puede leer su propia ruta |
| **Vault Secrets Operator (VSO)** | Un operador de Kubernetes | Copia los valores de Vault a un Secret normal de Kubernetes y reinicia la app cuando cambian | La app no sabe que Vault existe: solo lee variables de entorno |

## Observabilidad

| Tecnología | Qué es | Qué hace acá | Por qué |
| --- | --- | --- | --- |
| **Grafana Alloy** | El colector de telemetría de Grafana | Junta los logs de cada pod y los eventos de Kubernetes | Lee por la API de Kubernetes, así que no monta nada del nodo |
| **Loki** | Una base de logs que indexa etiquetas, no texto | Guarda los logs por 7 días | Es barata de operar, y alcanza para un nodo |
| **Grafana** | Una interfaz para consultar y graficar datos | Donde buscás en los logs (LogQL) | Es la interfaz estándar de Loki |

## Dónde ver cada una funcionando

Sus URLs y logins aparecen al final del instalador, y `./scripts/install.sh access` los muestra de nuevo ([Instalación](install.md#3-usar-smartlink)). Los labs profundizan, uno por tema: [índice](README.md#labs). Las razones detrás de cada decisión, con sus fuentes, están en [Referencias](references.md).
