🌐 [Leer en español](../es/labs/03-docker.md) · 📖 [Docs index](../README.md)

# Lab 03 — Docker

**Goal:** Package the app as an immutable, secure artifact.

## Idea

The image is built **once**, in CI, and runs the same on any node. It carries code and dependencies, **never** configuration or secrets: those arrive at runtime from Vault. K3s does not build images, it pulls them from GHCR.

## How it works

| Decision | Why |
| --- | --- |
| `python:3.12-slim`, dependencies before the code | Small image; layer cache |
| User `10001` | Does not run as root |
| Read-only filesystem (API) | Nothing can be written inside the container |
| `amd64` + `arm64` | The VM can be x86 or ARM |

## Do it

```bash
k -n smartlink-backend exec deploy/smartlink-api -- id           # uid=10001(smartlink)
k -n smartlink-backend exec deploy/smartlink-api -- touch /test  # Read-only file system
```

## Break it

Run the image without configuration:

```bash
k -n smartlink-backend run probe --rm -it --restart=Never \
  --image="$(k -n smartlink-backend get deploy smartlink-api -o jsonpath='{.spec.template.spec.containers[0].image}')"
# ConfigError: missing required environment variable JWT_SECRET
```

Inside a Deployment, that shows up as [💥 CrashLoopBackOff](../break.md#2-crashloopbackoff).

## Key points

- Image = code + dependencies. Configuration stays outside.
- Security is verified in the cluster, not only in the Dockerfile.

⬅️ [02 — Cloudflare D1 and migrations](02-d1.md) · 📚 [All labs](../README.md#labs) · ➡️ [04 — K3s](04-k3s.md)