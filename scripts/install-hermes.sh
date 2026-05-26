#!/usr/bin/env bash
set -euo pipefail

AI_HARNESS_USER="${AI_HARNESS_USER:-ai}"
INSTALL_FLAGS="${INSTALL_FLAGS:---skip-browser}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root or with sudo: sudo $0" >&2
  exit 1
fi

if ! id "${AI_HARNESS_USER}" >/dev/null 2>&1; then
  echo "User ${AI_HARNESS_USER} does not exist" >&2
  exit 1
fi

sudo -u "${AI_HARNESS_USER}" bash -lc "curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash -s -- ${INSTALL_FLAGS}"

install -m 0644 "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/ops/systemd/hermes-dashboard.service" /etc/systemd/system/hermes-dashboard.service
systemctl daemon-reload
systemctl enable --now hermes-dashboard.service

echo "Hermes installed."
echo "Next interactive step:"
echo "  sudo -iu ${AI_HARNESS_USER}"
echo "  hermes setup"
echo "Verify dashboard:"
echo "  curl -I http://127.0.0.1:9119/"
