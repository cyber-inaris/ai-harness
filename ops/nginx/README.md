# nginx

Reverse proxy templates and notes. Admin services should be private by default and reached through SSH tunnels, Tailscale, or app-level auth unless explicitly hardened.

## Files

- `ai-harness.conf` - MVP gateway config for local nginx.

## MVP Routing

The host exposes one nginx gateway on ports `80` and `8080`.

```text
/healthz      -> nginx health check
/hermes/      -> 127.0.0.1:3000
/router/      -> 127.0.0.1:4000
/benchmarks/  -> 127.0.0.1:5000
/cockpit/     -> 127.0.0.1:9090
/webhooks/    -> 127.0.0.1:7000
```

Cloudflare Tunnel or ngrok should point at `http://localhost:8080`.
