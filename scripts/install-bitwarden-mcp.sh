#!/usr/bin/env bash
set -euo pipefail

BITWARDEN_NPM_PREFIX="${BITWARDEN_NPM_PREFIX:-$HOME/.local/npm-global}"
BITWARDEN_CLI_VERSION="${BITWARDEN_CLI_VERSION:-2026.4.2}"
BITWARDEN_MCP_VERSION="${BITWARDEN_MCP_VERSION:-2026.5.1}"

if ! command -v node >/dev/null 2>&1; then
  echo "node is required. Install Node.js 22+ first." >&2
  exit 1
fi

node_major="$(node --version | sed -E 's/^v([0-9]+).*/\1/')"
if [[ "${node_major}" -lt 22 ]]; then
  echo "Node.js 22+ is required. Current: $(node --version)" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required." >&2
  exit 1
fi

mkdir -p "${BITWARDEN_NPM_PREFIX}"
npm config set prefix "${BITWARDEN_NPM_PREFIX}"

export PATH="${BITWARDEN_NPM_PREFIX}/bin:${PATH}"

npm install -g \
  "@bitwarden/cli@${BITWARDEN_CLI_VERSION}" \
  "@bitwarden/mcp-server@${BITWARDEN_MCP_VERSION}"

echo "Installed:"
bw --version
npm list -g --depth=0 | grep -E '@bitwarden/(cli|mcp-server)' || true

cat <<EOF

Add this to the runtime user's shell profile if it is not already present:

  export PATH="${BITWARDEN_NPM_PREFIX}/bin:\$PATH"

Next:

  bw login
  bw unlock --raw

Store the returned BW_SESSION only in a local secret file, not in git.
EOF
