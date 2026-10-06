🌐 [Leer en español](es/install.md) · 📖 [Docs index](README.md)

# 🚀 Install

**One command, and the script guides you.** It tells you what to do on each website (with the link), checks that it worked and waits. If you stop, run it again: it resumes where it left off.

## 1. Before you start

- [ ] **GitHub** and **Cloudflare** accounts, and a **password manager**.
- [ ] Where to run it: an **Ubuntu 24.04 VM** (2 vCPU, 4 GB, 30 GB, a user with `sudo`) or your **Mac**, which creates the VM by itself with Multipass. K3s needs Linux.
- [ ] Your own copy of the repo on GitHub:
  - **Public:** fork the repo.
  - **Private:** *New repository* → **Private**, empty, and copy the history (a fork cannot be private):

    ```bash
    git clone --bare https://github.com/<original-repo>/smartlink.git
    cd smartlink.git && git push --mirror git@github.com:<user>/<repo>.git && cd .. && rm -rf smartlink.git
    ```

## 2. Run the installer

### On an Ubuntu VM

```bash
ssh -A <user>@<vm-ip>        # -A: a private clone uses your SSH key, without copying it
git clone git@github.com:<user>/<repo>.git ~/smartlink && cd ~/smartlink   # public: https://...
./scripts/install.sh
```

### On a Mac

```bash
git clone git@github.com:<user>/<repo>.git && cd <repo>
./scripts/install.sh         # installs Multipass, creates the VM, copies the repo and continues inside
```

Afterwards: `./scripts/install.sh shell` to open a shell in the VM, `./scripts/install.sh ip` for its IP.

First it shows the repo it detected in the clone (`git remote origin`) and asks you to confirm it is **yours**: Argo CD will deploy from it and CI will run there. If you cloned the original instead of your fork, you fix it right there.

The walkthrough, in 7 stages, and **all your access details** at the end:

| # | Stage | What you do |
| --- | --- | --- |
| 1 | Cloudflare | Create a `D1 › Edit` token and paste it. It is validated on the spot |
| 2 | GitHub (optional) | Create a **1-day fine-grained token**, for your repo only, and paste it. With it, the script adds the deploy key, the variable and the secret, enables Actions and starts CI. Without it, it guides you with links |
| 3 | K3s and Argo CD | Without the token: add the **deploy key** it shows to GitHub |
| 4 | D1 database | Nothing (or the Account ID, if it cannot derive it from the token) |
| 5 | Vault | Nothing |
| 6 | First deploy | With the token: watch CI from the terminal. Without it: add the variable and the secret, and start CI on the web |
| 7 | Images and test | Private: create a **GitHub token** with only `read:packages`, so K3s can pull the private images from GHCR. Public: make the images public. Ends with the app answering |
| ✔ | Access details | Copy what it shows to your password manager: URLs, users, Argo CD and Grafana passwords, unseal key and root token. When you type `saved`, it deletes the keys from the VM |

> [!NOTE]
> **The stage 2 token**
>
> *Fine-grained*, it expires in 1 day and only works on your repo, with Actions, Administration, Secrets and Variables permissions. It **cannot** touch the code (*Contents*). It lives in memory while the installer runs: it is not stored on the VM or anywhere else.

![Token with D1 Edit](images/cloudflare/cloudflare-token-permissions.png)

![Read-only deploy key](images/github/github-deploy-key-add.png)

Non-secret values (repo, Account ID, D1 ID, IP) are saved by the installer in `scripts/config.env` **inside the VM** (`~/smartlink/scripts/config.env`). The file is not in the repo: Git ignores it, so it never reaches a fork. To see it: `./scripts/install.sh shell` and `cat ~/smartlink/scripts/config.env`. Tokens are not stored. What each script does inside: [Lab 05](labs/05-scripts.md).

## 3. Use SmartLink

Everything stays on your network. The end of the installer (and `./scripts/install.sh access`) shows:

| | URL | Login |
| --- | --- | --- |
| SmartLink | `http://<ip>/app` | Create your account |
| API docs | `http://<ip>/docs` (Swagger) · `http://<ip>/redoc` | Token from `/auth/login` in *Authorize* |
| Argo CD | `http://argocd.<ip>.nip.io` | `admin` + password from the final summary |
| Grafana | `http://grafana.<ip>.nip.io` | `admin` + password from the final summary |
| Vault | `http://vault.<ip>.nip.io` | *Token* method + root token |
| Traefik | `http://traefik.<ip>.nip.io` | None: read-only dashboard of the routes |

[nip.io](https://nip.io) resolves `argocd.<ip>.nip.io` to `<ip>`: no DNS to configure ([Lab 10](labs/10-dns-ingress.md)).

> [!NOTE]
> **HTTP only, on your local network.** There is no TLS, so do not expose this VM to the Internet as it is. Why, and how it would be added: [Lab 10](labs/10-dns-ingress.md#why-is-there-no-tls-yet).

1. Open `http://<ip>/app` and create an account.
2. Paste a long URL, optionally with an alias, and click **Shorten**.
3. Open the short link: it redirects and adds a click to the dashboard.

## 4. Run commands on the cluster

`kubectl` lives **inside the VM**, so there is no kubeconfig to copy or merge: your own `kubectl` and its contexts are never touched. Two shortcuts exist in the VM, and the installer sets them up in every new shell:

| Shortcut | Runs | Example |
| --- | --- | --- |
| `k` | `kubectl` against SmartLink's K3s | `k get pods -A` |
| `v` | the `vault` CLI inside the Vault pod | `v status` |

**From your Mac, one command at a time** (nothing to install, nothing to configure):

```bash
./scripts/install.sh k get pods -A
./scripts/install.sh k -n smartlink-backend logs deploy/smartlink-api --tail=20
./scripts/install.sh v status
```

**Or open a shell in the VM** and work there, with `k` and `v` ready:

```bash
./scripts/install.sh shell
k get nodes
```

**On a Linux VM or server**, connect with `ssh <user>@<vm-ip>` and use `k` and `v` directly (or `./scripts/install.sh k ...` from the cloned repo).

`v` needs a login for anything that reads or writes secrets (`v status` does not):

```bash
printf '%s' "<root-token>" | v login -
```

The labs and the failure scenarios use `k` and `v` exactly like this.

---

## Day to day

All of these work the same from your Mac or from inside the VM.

**After restarting the VM**

```bash
./scripts/install.sh unseal
```

Vault starts sealed after every restart. The app keeps running in the meantime, with the last Secret.

**See URLs, users and passwords**

```bash
./scripts/install.sh access
```

Asks for the Vault root token (it is in your password manager).

**Change a secret (e.g. the Cloudflare token)**

```bash
./scripts/install.sh secrets
```

**Deploy a change**

```bash
git pull && git push
```

CI also commits to `main` (the deploy commits), so pull first.

**Roll back the last deploy**

```bash
git log --oneline -- deploy/components | head -3
git revert --no-edit <hash> && git push
```

Find the `deploy: smartlink <sha>` commit you want to undo. More in the [rollback lab](labs/12-rollback.md).

**Upgrade a component — `deploy/components/<component>/Chart.yaml`**

```yaml
dependencies:
  - name: vault
    version: 0.34.1
```

Change it, commit and push: Argo CD upgrades it. For Vault, also run `k -n vault delete pod vault-0` and unseal.

**Uninstall**

```bash
./scripts/uninstall.sh
```

Asks you to type `delete`. On macOS it deletes the whole VM. Cloudflare and GitHub stay: the script lists what to delete by hand.

Something is broken? → [Troubleshooting](troubleshooting.md)

---

## Reference

### Public or private

| | Public | Private |
| --- | --- | --- |
| Copy of the repo | Fork | New repo + `git push --mirror` (a fork cannot be private) |
| URL used by Argo CD | HTTPS | SSH + deploy key (generated by `02-argocd.sh`) |
| GHCR images | Public packages | Private + `install.sh ghcr` |

### Forking this lab

**What a fork inherits.** Only the image lines CI writes in `deploy/components/smartlink-backend/values.yaml` and `smartlink-frontend/values.yaml` (`repository` and `tag`). The installer notices that image is not yours (`ghcr.io/<you>/…`) and starts CI, which replaces it with yours on its first run. Nothing else is tied to the author: `scripts/config.env` is ignored by Git, there are no secrets in the repo or its history, and the repo URL, the D1 ID and the IPs are decided at install time.

**If you publish your own copy as a template**, put those lines back to the placeholder first, so nobody starts from your image:

```bash
sed -i.bak -e 's|^  repository: .*|  repository: ghcr.io/set-by-ci/smartlink-api|' -e 's|^  tag: .*|  tag: "0000000"|' deploy/components/smartlink-backend/values.yaml
sed -i.bak -e 's|^  repository: .*|  repository: ghcr.io/set-by-ci/smartlink-frontend|' -e 's|^  tag: .*|  tag: "0000000"|' deploy/components/smartlink-frontend/values.yaml
rm deploy/components/smartlink-*/values.yaml.bak
```

**Before you make a repo public**, close what GitHub leaves open by default. All of it is in the repo's *Settings*:

| Where | What to set |
| --- | --- |
| *Actions › General* | **Public template:** *Disable Actions* (it does not run CI; whoever uses it runs their own). **The repo where you run the lab:** keep them on, allowing only GitHub-owned actions and `docker/*`. In both: fork pull request workflows → *Require approval for all external contributors*; workflow permissions → *Read*; untick *Allow GitHub Actions to create and approve pull requests* |
| *General › Features* | Turn off Wikis, Projects and Discussions if you will not use them |
| *Code security* | Turn on Dependabot alerts and security updates, **Secret scanning**, **Push protection** and private vulnerability reporting |
| *Rules › Rulesets* | Protect the default branch against force-push and deletion. Do **not** require pull requests: CI commits straight to `main` |
| *Secrets and variables*, *Deploy keys*, *Pages*, *Collaborators* | A public template should have none of them: remove the Cloudflare secret and variable, the `argocd` deploy key and anyone you do not need |

> [!NOTE]
> **Keep your running lab and your published template apart.** CI commits the new image tag to whichever repo is running the lab, so the repo you install from will always carry *your* tag. Install from a private copy and publish a clean one.

### Where each credential lives

| Credential | Lives in | Used by |
| --- | --- | --- |
| Cloudflare token (`D1 › Edit`) | GitHub secret `CLOUDFLARE_API_TOKEN` and Vault, `secret/smartlink/backend` | CI (migrations) and the backend. To separate them, create two tokens and load one on each side |
| Grafana password | Vault, `secret/grafana` | Grafana |
| Deploy key (private) | Secret `repo-smartlink` in `argocd` | Argo CD |
| GHCR token (private) | `/etc/rancher/k3s/registries.yaml` | K3s |
| Unseal key + root token | Your password manager | You |
