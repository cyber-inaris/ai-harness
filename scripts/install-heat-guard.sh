#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root or with sudo: sudo $0" >&2
  exit 1
fi

apt-get update
apt-get install -y lm-sensors power-profiles-daemon thermald

install -m 0755 "${REPO_ROOT}/scripts/heat-guard.sh" /usr/local/sbin/ai-harness-heat-guard
install -m 0644 "${REPO_ROOT}/ops/systemd/ai-harness-heat-guard.service" /etc/systemd/system/ai-harness-heat-guard.service
install -m 0644 "${REPO_ROOT}/ops/systemd/ai-harness-heat-guard.timer" /etc/systemd/system/ai-harness-heat-guard.timer

install -d -m 0755 /etc/ai-harness/env /var/log/ai-harness
if [[ ! -f /etc/ai-harness/env/heat-guard.env ]]; then
  install -m 0644 "${REPO_ROOT}/configs/examples/heat-guard.env.example" /etc/ai-harness/env/heat-guard.env
fi

systemctl daemon-reload
systemctl enable --now thermald.service
systemctl enable --now ai-harness-heat-guard.timer
systemctl start ai-harness-heat-guard.service

echo "AI Harness heat guard installed."
echo "Verify:"
echo "  systemctl status ai-harness-heat-guard.timer --no-pager"
echo "  tail -n 50 /var/log/ai-harness/heat-guard.log"
