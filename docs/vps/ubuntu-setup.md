# Ubuntu Host Setup Runbook

## Purpose

This runbook prepares a Linux host for `ai-harness`.

The first host may be an always-on home laptop. Later, the same layout should work on a VPS. The target operating system is Ubuntu Server 24.04 LTS or a close Ubuntu/Debian equivalent.

The setup is intentionally minimal and practical:

- A dedicated `ai` user with sudo and Docker access.
- Host-level SSH, XFCE + xrdp, nginx, ngrok, Docker, and firewall.
- Docker-first application runtime where reasonable.
- Plain `.env` secrets on the host for MVP.
- A future `deploy.sh` script can automate the repeatable parts.

## Decisions

| Area | Decision |
|---|---|
| Development machine | macOS |
| Target runtime | Linux |
| First host | Always-on home laptop or VPS later |
| Runtime model | Mixed: system tools on host, apps in Docker |
| Admin desktop | XFCE + xrdp |
| Admin access | SSH + xrdp |
| Public ingress | ngrok -> nginx -> internal services |
| Private network | Not required for MVP |
| Secrets MVP | Plain `.env` files on host with `chmod 600` |
| Service user | Dedicated `ai` user, minimal restrictions, sudo allowed |

## Recommended Host Specs

Minimum for experiments:

```text
CPU: 2 vCPU
RAM: 4 GB
Disk: 40 GB
OS: Ubuntu Server 24.04 LTS
Network: stable outbound internet
```

Comfortable target:

```text
CPU: 4 vCPU
RAM: 8 GB
Disk: 80+ GB
OS: Ubuntu Server 24.04 LTS
Network: stable outbound internet
```

More RAM helps if the host runs a browser, XFCE, Docker services, benchmark workers, databases, and agent tooling at the same time.

## Directory Layout

Use the same layout on home Linux and VPS:

```text
/opt/ai-harness/
  repo/                  # git checkout
  config/                # non-secret YAML config
  secrets/               # local secret files, never committed
  docker/                # docker compose files and overrides
  logs/                  # local service logs when not managed elsewhere

/var/lib/ai-harness/
  benchmarks/            # benchmark outputs
  telemetry/             # production request observations
  scores/                # computed model/reseller scores
  router/                # router state if needed

/etc/ai-harness/
  env/                   # optional systemd env files
  nginx/                 # optional nginx snippets
```

## Access Model

MVP access model:

```text
SSH:
  primary technical access

XFCE + xrdp:
  manual desktop/admin setup

ngrok:
  public tunnel when there is no domain or static IP

nginx:
  local reverse proxy to internal services

app-level auth:
  required for anything exposed through ngrok
```

Expected request path:

```text
Internet
  -> ngrok URL
  -> nginx on host
  -> internal service
```

Do not expose raw secrets, router admin, Cockpit, or agent terminal endpoints without application-level auth.

## Always-On Laptop Policy

If the first host is a home laptop, disable system sleep separately from screen
blanking. A laptop can keep the display off while still suspending the whole OS
after an idle timeout, especially on battery. When the OS suspends, Wi-Fi,
Tailscale, SSH, Cloudflare Tunnel, Docker services, and agents all disconnect.

After cloning the repo on the host, run:

```bash
sudo /opt/ai-harness/repo/scripts/disable-laptop-sleep.sh
```

If the graphical desktop user is not `dima`, pass it explicitly:

```bash
sudo GUI_USER=alice /opt/ai-harness/repo/scripts/disable-laptop-sleep.sh
```

The script configures systemd-logind, masks sleep targets, disables GNOME idle
suspend for AC and battery, ignores lid-close suspend, and disables
NetworkManager Wi-Fi power save by override.

## Create The `ai` User

Create a dedicated user for this stack:

```bash
sudo adduser ai
sudo usermod -aG sudo ai
```

After Docker is installed, add the user to the Docker group:

```bash
sudo usermod -aG docker ai
```

This user is not a strict security sandbox in the MVP. It is an operational boundary for ownership, logs, cleanup, and future hardening.

## Base Packages

Install common host tools:

```bash
sudo apt update
sudo apt install -y \
  apache2-utils \
  ca-certificates \
  curl \
  git \
  gnupg \
  htop \
  jq \
  nano \
  nginx \
  openssh-server \
  python3-venv \
  sqlite3 \
  ufw \
  unzip
```

Package groups used by the current stack:

| Group | Packages | Why |
|---|---|---|
| Base OS/admin | `ca-certificates`, `curl`, `git`, `gnupg`, `htop`, `jq`, `nano`, `unzip` | Shell work, Git checkout, API/debug commands, downloading installers |
| SSH | `openssh-server` | Primary technical access |
| Firewall | `ufw` | Basic host firewall |
| Web gateway | `nginx`, `apache2-utils` | Local reverse proxy; `apache2-utils` provides `htpasswd` for optional Basic Auth |
| Agent runtime | `python3-venv`, `sqlite3` | LangGraph virtualenv and manual inspection of task SQLite databases |
| Docker runtime | `docker.io`, `docker-compose-v2` | Router/apps in Docker Compose |
| Optional desktop | `xfce4`, `xfce4-goodies`, `xrdp` | GUI access for account setup and browser-based admin work |

The `scripts/deploy-host.sh` installer currently installs the full MVP set:

```bash
sudo /opt/ai-harness/repo/scripts/deploy-host.sh
```

Manual minimal install can omit the optional desktop packages if xrdp is not needed.

## SSH Setup

Make sure SSH is enabled:

```bash
sudo systemctl enable --now ssh
sudo systemctl status ssh --no-pager
```

Recommended SSH hardening for the MVP:

```text
Use SSH keys.
Disable password login after key access is confirmed.
Disable root SSH login after normal sudo access is confirmed.
```

Edit SSH config:

```bash
sudo nano /etc/ssh/sshd_config
```

Recommended settings:

```text
PasswordAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
```

Restart SSH:

```bash
sudo systemctl restart ssh
```

Before closing the current session, open a second terminal and verify key-based SSH still works.

## Firewall

Enable a basic firewall:

```bash
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw status verbose
```

For MVP, do not open xrdp, Cockpit, router admin, or benchmark/admin UIs publicly unless there is a deliberate reason.

If xrdp must be reachable directly on a private LAN, allow only the local network range:

```bash
sudo ufw allow from 192.168.0.0/16 to any port 3389 proto tcp
```

If using ngrok for public ingress, nginx can listen locally and does not require opening public HTTP/HTTPS ports.

## Docker And Docker Compose

Install Docker from Docker's official repository or Ubuntu packages. The future `deploy.sh` should use one clear method and verify installation.

Ubuntu package method used by the current MVP script:

```bash
sudo apt install -y docker.io docker-compose-v2
```

Validation commands:

```bash
docker --version
docker compose version
docker run --rm hello-world
```

After adding `ai` to the Docker group, log out and back in, then verify:

```bash
su - ai
docker ps
```

## XFCE + xrdp

Install optional desktop access:

```bash
sudo apt install -y xfce4 xfce4-goodies xrdp
sudo systemctl enable --now xrdp
echo "startxfce4" > ~/.xsession
sudo adduser xrdp ssl-cert
sudo systemctl restart xrdp
```

Recommended access:

```text
Use xrdp from LAN, SSH tunnel, or a controlled tunnel.
Do not expose RDP directly to the internet unless deliberately hardened.
```

SSH tunnel example:

```bash
ssh -L 3389:localhost:3389 ai@HOST
```

Then connect an RDP client to:

```text
localhost:3389
```

## nginx

nginx is the local reverse proxy.

MVP target:

```text
ngrok public URL
  -> nginx
  -> app services on localhost or Docker network
```

Example future routes:

```text
/agent       -> Hermes or agent UI
/router      -> router admin/API
/benchmarks  -> benchmark dashboard/API
/webhooks    -> public webhook endpoints
```

Every service exposed through ngrok must have its own auth or be explicitly safe for public access.

If Basic Auth is used at the nginx layer, install:

```bash
sudo apt install -y apache2-utils
```

Then create/update the password file with `htpasswd`.

## ngrok

ngrok is the first public ingress option when there is no domain or static IP.

Secrets:

```text
/opt/ai-harness/secrets/ngrok.env
```

Example variables:

```text
NGROK_AUTHTOKEN=
NGROK_DOMAIN=
```

If no reserved domain is available, use the generated ngrok URL and update webhook configs as needed.

## Secrets

MVP secrets are plain host files with restrictive permissions.

Create directories:

```bash
sudo mkdir -p /opt/ai-harness/{config,secrets,docker,logs,repo}
sudo mkdir -p /var/lib/ai-harness/{benchmarks,telemetry,scores,router}
sudo mkdir -p /etc/ai-harness/env
sudo chown -R ai:ai /opt/ai-harness /var/lib/ai-harness /etc/ai-harness
sudo chmod 700 /opt/ai-harness/secrets
```

Create secret files:

```bash
sudo -u ai touch /opt/ai-harness/secrets/providers.env
sudo -u ai touch /opt/ai-harness/secrets/accounts.env
sudo -u ai touch /opt/ai-harness/secrets/ngrok.env
sudo chmod 600 /opt/ai-harness/secrets/*.env
```

Rules:

```text
Do not commit secrets to git.
Do not expose secrets through nginx/ngrok.
Do not store browser cookies unless there is no API alternative.
Prefer API tokens with narrow scopes.
```

Future upgrade:

```text
sops + age
or Vault / Infisical / Doppler / 1Password Connect
```

## Clone The Repository

As `ai`:

```bash
sudo -iu ai
cd /opt/ai-harness
git clone https://github.com/cyber-inaris/ai-harness.git repo
```

If the repo is already present:

```bash
cd /opt/ai-harness/repo
git pull
```

## Docker-First Application Runtime

Run application services in Docker where practical:

```text
Router
Benchmark runner
Telemetry/scoring database
Optional admin tools
```

Keep host-level services for:

```text
SSH
XFCE + xrdp
nginx
ngrok
Docker
firewall
systemd
```

## LangGraph Runtime Dependencies

The LangGraph agent runtime is installed into a host virtualenv:

```text
/opt/ai-harness/venvs/langgraph-runtime
```

Required apt packages:

```bash
sudo apt install -y python3-venv sqlite3
```

Why:

```text
python3-venv  -> create the runtime virtualenv
sqlite3       -> inspect /var/lib/ai-harness/agent/tasks.sqlite from shell
```

The Python package dependencies are managed by:

```bash
sudo /opt/ai-harness/repo/scripts/install-langgraph-runtime.sh
```

That script installs the local package from:

```text
/opt/ai-harness/repo/packages/langgraph_runtime
```

## Future `deploy.sh`

A future script can automate the repeatable parts:

```text
scripts/deploy.sh
```

Suggested phases:

1. Check OS and privileges.
2. Install base packages.
3. Create `ai` user.
4. Install Docker.
5. Install optional XFCE + xrdp.
6. Install and configure nginx.
7. Create `/opt`, `/var/lib`, and `/etc` directory layout.
8. Create empty secret files with safe permissions.
9. Print next manual steps for secrets and ngrok auth.

The script should be idempotent: running it twice should not destroy existing config or secrets.

## Verification Checklist

After setup, verify:

```bash
id ai
sudo -iu ai pwd
ssh -V
sudo systemctl status ssh --no-pager
sudo ufw status verbose
docker --version
docker compose version
sudo systemctl status nginx --no-pager
sudo systemctl status xrdp --no-pager
ls -la /opt/ai-harness
ls -la /opt/ai-harness/secrets
```

Expected:

```text
ai user exists.
SSH is active.
Firewall is active.
Docker works.
nginx is active.
xrdp is active if installed.
/opt/ai-harness/secrets is mode 700.
secret .env files are mode 600.
```

## Agent Instructions

When an AI agent executes this runbook:

1. Confirm the host OS and whether it is home Linux or VPS.
2. Do not overwrite existing secrets.
3. Do not disable SSH until a second SSH login has been verified.
4. Do not expose xrdp, Cockpit, router admin, or secret UIs publicly without explicit approval.
5. Print every generated path and service status at the end.
6. If a command fails, stop and report the exact command and output.
