# Bitwarden MCP

Bitwarden MCP is the preferred future path for storing operational credentials
that agents may need to retrieve. It should stay local to the host and must not
be exposed over the network.

## Installed Components

Install or refresh the server-side tools:

```bash
/opt/ai-harness/repo/scripts/install-bitwarden-mcp.sh
```

The script installs these packages under the runtime user's local npm prefix:

```text
@bitwarden/cli
@bitwarden/mcp-server
```

The host needs Node.js 22+.

## Login

Log in manually as the runtime user:

```bash
ssh ai-harness-ts
export PATH="$HOME/.local/npm-global/bin:$PATH"
bw login
```

Unlock the vault and get a session token:

```bash
bw unlock --raw
```

Store the returned token in a local secret file only:

```bash
install -m 700 -d /opt/ai-harness/secrets
umask 077
cat > /opt/ai-harness/secrets/bitwarden-mcp.env <<'EOF'
BW_SESSION=<paste-unlocked-session-token>
EOF
```

Do not commit `BW_SESSION`. Rotate it by locking/unlocking the vault again.

## MCP Configuration

For an MCP client running on the same host, configure a local stdio server:

```json
{
  "mcpServers": {
    "bitwarden": {
      "command": "npx",
      "args": ["-y", "@bitwarden/mcp-server"],
      "env": {
        "BW_SESSION": "<load-from-/opt/ai-harness/secrets/bitwarden-mcp.env>"
      }
    }
  }
}
```

Prefer client-specific secret loading if available. If the client cannot load
env files directly, use a wrapper script outside git that sources
`/opt/ai-harness/secrets/bitwarden-mcp.env` and then starts
`mcp-server-bitwarden`.

## Verification

Check CLI installation:

```bash
export PATH="$HOME/.local/npm-global/bin:$PATH"
bw --version
bw status
```

Expected before login:

```json
{"status":"unauthenticated"}
```

Expected after login and unlock:

```json
{"status":"unlocked"}
```

Check MCP startup:

```bash
timeout 3 npx -y @bitwarden/mcp-server
```

Expected output:

```text
Bitwarden MCP Server running on stdio
```

## Security Rules

- Run Bitwarden MCP only as a local stdio MCP server.
- Never expose it through nginx, Cloudflare Tunnel, Tailscale HTTP, or Docker
  published ports.
- Do not store `BW_SESSION`, master passwords, API keys, or vault exports in git.
- Give agents narrow tasks when asking them to retrieve secrets.
- Prefer separate Bitwarden items for Proton Bridge, reseller accounts, and
  provider API keys so access can be audited and rotated cleanly.
