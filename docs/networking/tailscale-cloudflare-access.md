# Tailscale + Cloudflare Access Notes

## Current Decision

Use Tailscale for operator SSH and use Cloudflare Tunnel only for web ingress.

This is the practical MVP split:

```text
SSH/admin:
  Mac -> Tailscale -> ai@host

Web:
  Internet -> Cloudflare Tunnel -> nginx on host -> local services

RDP/XFCE:
  RDP client -> Tailscale IP:3389
```

## Why Cloudflare SSH Was Not Used For MVP

Cloudflare Tunnel with an SSH hostname is not the same as exposing raw port 22.

When `ssh.ss-promotion.com` is protected by Cloudflare Access, a direct SSH command does not work:

```bash
ssh ai@ssh.ss-promotion.com
```

The client must use `cloudflared access ssh` as a `ProxyCommand`:

```sshconfig
Host ai-harness-cloudflare
  HostName ssh.ss-promotion.com
  User ai
  IdentityFile ~/.ssh/ai_harness_ssh
  IdentitiesOnly yes
  ProxyCommand cloudflared access ssh --hostname %h
```

During setup, the tunnel showed three different failure modes:

| Symptom | Root cause |
|---|---|
| `connect: connection refused` in cloudflared logs | `sshd` was not running or not reachable on localhost:22 |
| Browser/HTTP showed Cloudflare Access redirect | hostname was protected by Access and required auth |
| SSH timed out during banner exchange | client did not receive a real SSH stream through Access |

Because Tailscale SSH worked immediately and does not require browser auth during every agent connection, it is the default admin path.

## Working SSH Config

```sshconfig
Host ai-harness-ts
  HostName 100.105.206.54
  User ai
  IdentityFile ~/.ssh/ai_harness_ssh
  IdentitiesOnly yes
```

Connect:

```bash
ssh ai-harness-ts
```

## Cloudflare Web Hostname

Use one web hostname that points to nginx:

```text
apps.ss-promotion.com -> http://localhost:8080
```

nginx then owns path routing:

```text
/healthz      -> local health check
/hermes/      -> localhost:3000
/router/      -> localhost:4000
/benchmarks/  -> localhost:5000
/cockpit/     -> localhost:9090
/webhooks/    -> localhost:7000
```

## Security Baseline

For the MVP, do not expose raw secrets or terminal controls through the public web hostname.

Acceptable public paths:

```text
/healthz
/webhooks/*
```

Admin paths should have their own app login at minimum:

```text
/hermes/
/router/
/benchmarks/
/cockpit/
```

Later hardening options:

- Cloudflare Access policies for admin paths.
- Tailscale-only admin services.
- nginx Basic Auth as an additional outer layer.
- Separate public and private hostnames.
