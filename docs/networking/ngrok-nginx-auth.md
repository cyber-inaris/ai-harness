# ngrok + nginx Access Pattern

## Goal

The first VPS may not have a domain or static IP. Use one ngrok tunnel as the public entrypoint, then let nginx route to internal services.

This keeps the setup compatible with a free ngrok account while still giving one public URL for Hermes, router/admin tools, benchmark dashboards, and webhooks.

## Planned Topology

```text
Internet
  |
  v
https://<ngrok-id>.ngrok-free.app
  |
  v
ngrok agent on VPS
  |
  v
nginx on 127.0.0.1:8080
  |
  ├─ /hermes/      -> Hermes service
  ├─ /router/      -> OmniRouter / cockpit tools / router API
  ├─ /benchmarks/  -> benchmark dashboard or API
  ├─ /webhooks/    -> Telegram or external webhooks
  └─ /cockpit/     -> Cockpit only if reverse proxy works cleanly
```

## Access Policy

For the initial setup, nginx will enforce Basic Auth at the edge.

```text
ngrok URL is public
nginx requires username/password
each internal service may still have its own auth
```

This is the minimum acceptable protection for exposing admin services through a public tunnel.

Do not expose these paths without nginx auth:

```text
/hermes/
/router/
/benchmarks/
/accounts/
/secrets/
/cockpit/
```

Public unauthenticated paths, if needed, should be explicit and narrow:

```text
/webhooks/telegram/
/healthz
```

## Basic Auth Setup

Install nginx and password helper:

```bash
sudo apt update
sudo apt install -y nginx apache2-utils
```

Create a Basic Auth user:

```bash
sudo htpasswd -c /etc/nginx/.htpasswd alex
```

For later password changes:

```bash
sudo htpasswd /etc/nginx/.htpasswd alex
```

## Example nginx Config

Example file:

```text
/etc/nginx/sites-available/ai-harness
```

Config:

```nginx
server {
  listen 127.0.0.1:8080;
  server_name _;

  auth_basic "AI Harness";
  auth_basic_user_file /etc/nginx/.htpasswd;

  location /hermes/ {
    proxy_pass http://127.0.0.1:3000/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location /router/ {
    proxy_pass http://127.0.0.1:4000/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location /benchmarks/ {
    proxy_pass http://127.0.0.1:5000/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location /webhooks/telegram/ {
    auth_basic off;
    proxy_pass http://127.0.0.1:7000/telegram/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

Enable it:

```bash
sudo ln -s /etc/nginx/sites-available/ai-harness /etc/nginx/sites-enabled/ai-harness
sudo nginx -t
sudo systemctl reload nginx
```

## Running ngrok

Run one public tunnel to nginx:

```bash
ngrok http 8080
```

The public URL will look like:

```text
https://<ngrok-id>.ngrok-free.app
```

Service URLs:

```text
https://<ngrok-id>.ngrok-free.app/hermes/
https://<ngrok-id>.ngrok-free.app/router/
https://<ngrok-id>.ngrok-free.app/benchmarks/
https://<ngrok-id>.ngrok-free.app/webhooks/telegram/
```

## Codex / Agent Config Pattern

Avoid storing Basic Auth passwords directly in URLs when possible.

Preferred:

```yaml
services:
  hermes:
    base_url: "https://<ngrok-id>.ngrok-free.app/hermes"
    auth:
      type: "basic"
      username_env: "AI_HARNESS_USER"
      password_env: "AI_HARNESS_PASSWORD"

  router:
    base_url: "https://<ngrok-id>.ngrok-free.app/router"
    auth:
      type: "basic"
      username_env: "AI_HARNESS_USER"
      password_env: "AI_HARNESS_PASSWORD"
```

Environment:

```env
AI_HARNESS_USER=alex
AI_HARNESS_PASSWORD=change-this-password
```

If a tool only supports a single URL and cannot send separate Basic Auth headers, use URL-embedded credentials only as a fallback:

```env
HERMES_URL=https://alex:change-this-password@<ngrok-id>.ngrok-free.app/hermes
```

This is less safe because credentials can appear in logs, shell history, screenshots, and config dumps.

## Router API With Two Auth Layers

If the router exposes an OpenAI-compatible API, use both layers:

```text
nginx Basic Auth = enter the private AI Harness network
router Bearer token = use the model/router API
```

Example request:

```bash
curl https://<ngrok-id>.ngrok-free.app/router/v1/models \
  -u "$AI_HARNESS_USER:$AI_HARNESS_PASSWORD" \
  -H "Authorization: Bearer $AI_HARNESS_ROUTER_KEY"
```

## Cockpit Note

Cockpit can be difficult to proxy under a path such as `/cockpit/` because of WebSockets and absolute paths.

Preferred access:

```bash
ssh -L 9090:localhost:9090 user@vps
```

Then open:

```text
https://localhost:9090
```

If Cockpit must go through ngrok/nginx, test it separately and document the exact working nginx config.

## Rules

1. One free ngrok tunnel is acceptable for the first setup.
2. nginx Basic Auth is required for admin paths.
3. Public unauthenticated paths must be explicit and narrow.
4. Secrets/account pages must not render full secrets in the browser.
5. Router APIs should still require their own API keys.
6. The ngrok URL should be treated as semi-public and rotated if leaked.
