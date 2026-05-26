#!/usr/bin/env bash
set -euo pipefail

AI_HARNESS_ROOT="${AI_HARNESS_ROOT:-/opt/ai-harness}"
AI_HARNESS_USER="${AI_HARNESS_USER:-ai}"
REPO_DIR="${REPO_DIR:-${AI_HARNESS_ROOT}/repo}"
VENV_DIR="${VENV_DIR:-${AI_HARNESS_ROOT}/venvs/langgraph-runtime}"
DATA_DIR="${DATA_DIR:-/var/lib/ai-harness/agent}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root or with sudo: sudo $0" >&2
  exit 1
fi

if ! id "${AI_HARNESS_USER}" >/dev/null 2>&1; then
  echo "User ${AI_HARNESS_USER} does not exist" >&2
  exit 1
fi

install -d -o "${AI_HARNESS_USER}" -g "${AI_HARNESS_USER}" "${AI_HARNESS_ROOT}/venvs" "${DATA_DIR}" "${DATA_DIR}/tasks"

sudo -u "${AI_HARNESS_USER}" python3 -m venv "${VENV_DIR}"
sudo -u "${AI_HARNESS_USER}" "${VENV_DIR}/bin/python" -m pip install --upgrade pip
sudo -u "${AI_HARNESS_USER}" "${VENV_DIR}/bin/python" -m pip install -e "${REPO_DIR}/packages/langgraph_runtime"

echo "LangGraph runtime installed."
echo "Verify:"
echo "  ${REPO_DIR}/scripts/agent-task status"

