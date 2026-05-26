# Docker

Docker and Docker Compose layout notes for routers, workers, databases, and supporting tools.

## Current Layout

Use host-installed Docker with compose files stored in:

```text
/opt/ai-harness/docker/
```

The repo includes an initial skeleton:

```text
docker/compose.yml
```

It intentionally uses disabled placeholder services until the exact Hermes/router/benchmark images are selected.

## Runtime Ports

The nginx gateway expects services on local-only ports:

```text
Hermes:     127.0.0.1:3000
Router:     127.0.0.1:4000
Benchmarks: 127.0.0.1:5000
Webhooks:   127.0.0.1:7000
Cockpit:    127.0.0.1:9090
```

Do not bind admin services to `0.0.0.0` unless there is a deliberate reason.
