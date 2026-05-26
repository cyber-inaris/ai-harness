# Architecture

`ai-harness` separates operational concerns into documents, configs, benchmark definitions, scripts, and future code packages.

```text
VPS
  ├─ Admin access
  │   ├─ SSH
  │   ├─ Cockpit through SSH tunnel
  │   └─ Optional XFCE + xrdp through SSH tunnel or VPN
  │
  ├─ Router layer
  │   ├─ OmniRouter or compatible router
  │   ├─ Provider metadata
  │   └─ Routing policy
  │
  ├─ Agent layer
  │   ├─ Hermes
  │   ├─ Codex workflows
  │   └─ Future task agents
  │
  ├─ Benchmark layer
  │   ├─ Smoke tests
  │   ├─ Identity tests
  │   ├─ Coding tests
  │   └─ Long-context tests
  │
  └─ Data/secrets
      ├─ Local or encrypted secrets
      ├─ Benchmark results
      ├─ Telemetry
      └─ Score history
```

The repo does not expose admin surfaces publicly by default. The expected access pattern is SSH key auth plus tunnels or a private VPN.

## Design Principle

Prefer existing infrastructure tools first. Add custom code only when there is a concrete gap, such as scoring aggregation, benchmark execution, or router integration glue.

