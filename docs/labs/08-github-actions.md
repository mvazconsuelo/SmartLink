🌐 [Leer en español](../es/labs/08-github-actions.md) · 📖 [Docs index](../README.md)

# Lab 08 — GitHub Actions + GHCR

**Goal:** Turn every commit into a deployable image and tell GitOps about it.

## Idea

CI tests, builds, publishes, migrates and **writes to Git**. Argo CD does the deploy. CI never touches the cluster.

## How it works

| Job | When | What it does |
| --- | --- | --- |
| `test` | Always | `ruff` + `pytest` |
| `build` | `main` | amd64 + arm64 images → `ghcr.io/<owner>/smartlink-*:<sha7>` |
| `migrate` | `main` | D1 migrations |
| `gitops` | `main` | Commit `deploy: smartlink <sha7>` in `deploy/components/smartlink-{backend,frontend}/values.yaml` |
| `release` | Tag `vX.Y.Z` | Adds the `X.Y.Z` tag to the image already built |

- **SHA to deploy, semver for humans.** Never `latest`.
- **A release does not rebuild:** it publishes exactly what was tested.
- **Each job depends on the previous one:** if `migrate` fails, there is no deploy.

## Do it

- *Actions › ci*: the 4 jobs green.
- *Packages*: the `<sha7>` tag, with two architectures.
- `main`: the deploy commit by `github-actions[bot]`.

Release: `git tag v1.0.0 && git push origin v1.0.0`. In GHCR, the image ends up with both tags and the same digest.

## Break it

Delete the `CLOUDFLARE_API_TOKEN` secret and run *ci*:
- `build` passes;
- `migrate` fails, saying which secret is missing;
- `gitops` does not run;
- the cluster keeps the previous version.

See also: [💥 Bad release](../break.md#6-bad-release).

## Key points

- A pipeline is a chain: the broken link stops what comes after it.
- CI produces artifacts and changes Git. Nothing else.

⬅️ [07 — Vault + VSO](07-vault.md) · 📚 [All labs](../README.md#labs) · ➡️ [09 — GitOps](09-gitops.md)