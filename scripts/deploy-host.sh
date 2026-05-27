#!/usr/bin/env bash
set -euo pipefail

AI_HARNESS_USER="${AI_HARNESS_USER:-ai}"
AI_HARNESS_ROOT="${AI_HARNESS_ROOT:-/opt/ai-harness}"
AI_HARNESS_STATE="${AI_HARNESS_STATE:-/var/lib/ai-harness}"
AI_HARNESS_ETC="${AI_HARNESS_ETC:-/etc/ai-harness}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root or with sudo: sudo $0" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y \
  apache2-utils \
  ca-certificates \
  curl \
  docker-compose-v2 \
  docker.io \
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
  unzip \
  xfce4 \
  xfce4-goodies \
  xrdp

systemctl enable --now ssh nginx docker xrdp

if id "${AI_HARNESS_USER}" >/dev/null 2>&1; then
  usermod -aG sudo,docker "${AI_HARNESS_USER}"
  mkdir -p "/home/${AI_HARNESS_USER}"
  chown "${AI_HARNESS_USER}:${AI_HARNESS_USER}" "/home/${AI_HARNESS_USER}"
  printf "startxfce4\n" > "/home/${AI_HARNESS_USER}/.xsession"
  chown "${AI_HARNESS_USER}:${AI_HARNESS_USER}" "/home/${AI_HARNESS_USER}/.xsession"
fi

adduser xrdp ssl-cert >/dev/null 2>&1 || true

mkdir -p \
  "${AI_HARNESS_ROOT}/repo" \
  "${AI_HARNESS_ROOT}/config" \
  "${AI_HARNESS_ROOT}/docker" \
  "${AI_HARNESS_ROOT}/logs" \
  "${AI_HARNESS_ROOT}/secrets" \
  "${AI_HARNESS_STATE}/benchmarks" \
  "${AI_HARNESS_STATE}/telemetry" \
  "${AI_HARNESS_STATE}/scores" \
  "${AI_HARNESS_STATE}/router" \
  "${AI_HARNESS_STATE}/agent" \
  "${AI_HARNESS_ETC}/env" \
  "${AI_HARNESS_ETC}/nginx"

if id "${AI_HARNESS_USER}" >/dev/null 2>&1; then
  chown -R "${AI_HARNESS_USER}:${AI_HARNESS_USER}" "${AI_HARNESS_ROOT}" "${AI_HARNESS_STATE}" "${AI_HARNESS_ETC}"
fi

chmod 700 "${AI_HARNESS_ROOT}/secrets"
for file in providers.env accounts.env router.env hermes.env ngrok.env cloudflare.env; do
  touch "${AI_HARNESS_ROOT}/secrets/${file}"
done
chmod 600 "${AI_HARNESS_ROOT}"/secrets/*.env

install -m 0644 "${REPO_ROOT}/ops/nginx/ai-harness.conf" /etc/nginx/sites-available/ai-harness
ln -sfn /etc/nginx/sites-available/ai-harness /etc/nginx/sites-enabled/ai-harness
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

ufw allow OpenSSH >/dev/null || true

systemctl restart xrdp nginx

echo "AI Harness host deployment complete."
echo "Verify:"
echo "  systemctl is-active ssh nginx docker xrdp"
echo "  curl -I http://localhost:8080/healthz"
