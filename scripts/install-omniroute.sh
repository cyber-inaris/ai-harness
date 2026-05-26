#!/usr/bin/env bash
set -euo pipefail

AI_HARNESS_USER="${AI_HARNESS_USER:-ai}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_SRC="${REPO_ROOT}/docker/omniroute.compose.yml"
COMPOSE_DST="/opt/ai-harness/docker/omniroute.compose.yml"
ENV_DST="/opt/ai-harness/secrets/omniroute.env"
DATA_DIR="/var/lib/ai-harness/router/omniroute"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root or with sudo: sudo $0" >&2
  exit 1
fi

if [[ ! -f "${COMPOSE_SRC}" ]]; then
  echo "Missing ${COMPOSE_SRC}" >&2
  exit 1
fi

mkdir -p /opt/ai-harness/docker /opt/ai-harness/secrets "${DATA_DIR}"
install -m 0644 "${COMPOSE_SRC}" "${COMPOSE_DST}"

if [[ ! -f "${ENV_DST}" ]]; then
  install -m 0600 "${REPO_ROOT}/configs/examples/omniroute.env.example" "${ENV_DST}"
else
  chmod 600 "${ENV_DST}"
fi

if id "${AI_HARNESS_USER}" >/dev/null 2>&1; then
  chown -R "${AI_HARNESS_USER}:${AI_HARNESS_USER}" /opt/ai-harness/docker "${DATA_DIR}"
  chown "${AI_HARNESS_USER}:${AI_HARNESS_USER}" "${ENV_DST}"
fi

docker compose -f "${COMPOSE_DST}" pull
docker compose -f "${COMPOSE_DST}" up -d

install -m 0644 "${REPO_ROOT}/ops/nginx/ai-harness.conf" /etc/nginx/sites-available/ai-harness
nginx -t
systemctl reload nginx

echo "Waiting for OmniRoute on http://127.0.0.1:20128 ..."
for _ in $(seq 1 60); do
  if curl -fsS --max-time 2 http://127.0.0.1:20128/ >/dev/null 2>&1; then
    echo "OmniRoute is responding."
    exit 0
  fi
  sleep 2
done

echo "OmniRoute did not respond within timeout." >&2
docker compose -f "${COMPOSE_DST}" ps >&2 || true
docker logs --tail 100 ai-harness-omniroute >&2 || true
exit 1
