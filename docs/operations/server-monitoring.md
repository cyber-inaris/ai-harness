# Server Monitoring

## Purpose

Use this runbook to add lightweight host monitoring for the `ai-harness`
server. The first priority is practical visibility into CPU, memory, disk,
network, Docker, and host temperature where the platform exposes sensors.

## Recommended Option: Netdata

Netdata is the best default option for fast server visibility and temperature
charts because it auto-discovers common Linux metrics and can read hardware
sensors through `lm-sensors`.

Temperature support:

| Host type | Temperature visibility | Notes |
|---|---:|---|
| Linux bare metal | Yes | Works when the kernel and `lm-sensors` can see CPU/mainboard sensors. |
| VPS | Often no | Virtualization usually hides physical temperature sensors. |
| Docker host | Sometimes | Works when Netdata runs with enough host access and the host exposes sensors. |

## Linux Temperature Setup

Install and detect sensors on Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y lm-sensors
sudo sensors-detect
sensors
```

Accept the safe defaults in `sensors-detect` unless the host has special
hardware requirements. If `sensors` shows CPU or board temperatures, Netdata
should usually be able to chart them after installation.

If `sensors` does not show temperatures, Netdata cannot invent them. On a VPS
this is expected. On bare metal, check BIOS/UEFI sensor settings, kernel
modules, and whether the hardware has supported monitoring chips.

## Netdata Installation

Use Netdata's official Linux installer on the host:

```bash
wget -O /tmp/netdata-kickstart.sh https://get.netdata.cloud/kickstart.sh
sudo sh /tmp/netdata-kickstart.sh --stable-channel
```

Verify the service:

```bash
systemctl status netdata --no-pager
curl -sS http://127.0.0.1:19999/api/v1/info | jq .
```

Netdata listens on port `19999` by default. Keep it private by default. Do not
expose it directly to the public internet; put it behind SSH tunneling,
Cloudflare Access, VPN/Tailscale, or another authenticated gateway.

Example SSH tunnel from an admin machine:

```bash
ssh -L 19999:127.0.0.1:19999 ai@SERVER_HOST
```

Then open:

```text
http://127.0.0.1:19999
```

## Operational Checks

After installation, check:

```bash
sensors
systemctl status netdata --no-pager
ss -lntp | grep 19999
curl -sS http://127.0.0.1:19999/api/v1/charts | jq 'keys[]' | grep -i sensor
```

Expected outcomes:

- Bare metal hosts should show CPU or board temperature charts when
  `lm-sensors` detects supported sensors.
- VPS hosts may show CPU, memory, disk, network, and Docker metrics but no
  physical temperature charts.
- Docker-based Netdata setups may need additional host mounts and privileges;
  prefer host installation for the primary `ai-harness` server unless container
  isolation is required.

## Heat Guard

The `ai-harness` host can run a lightweight heat guard timer:

```bash
sudo /opt/ai-harness/repo/scripts/install-heat-guard.sh
```

The timer runs every five minutes. Defaults:

```text
warning threshold: 80 C
critical threshold: 88 C
power mode: set power-saver at warning threshold
thermal daemon: start thermald at warning threshold
safe cleanup: apt cache, old temp files, disabled snap revisions, Docker prune,
              and old Firefox cache files
log: /var/log/ai-harness/heat-guard.log
```

The guard does not delete browser profiles, cookies, credentials, or session
state. It also does not close individual Firefox tabs because Firefox tab
control is not reliable without a dedicated remote debugging setup.

Critical-temperature Firefox restart is available, but disabled by default.
Enable it only if the interactive Firefox session is disposable:

```bash
sudoedit /etc/ai-harness/env/heat-guard.env
```

Set:

```text
AI_HARNESS_HEAT_RESTART_FIREFOX=1
```

On hosts where `thermald` exits with `Unsupported cpu model or platform`, keep
the heat guard active but disable repeated `thermald` starts:

```text
AI_HARNESS_HEAT_START_THERMALD=0
```

Then restart the timer/service:

```bash
sudo systemctl restart ai-harness-heat-guard.timer
sudo systemctl start ai-harness-heat-guard.service
```

Verification:

```bash
systemctl status ai-harness-heat-guard.timer --no-pager
sudo systemctl status ai-harness-heat-guard.service --no-pager
sudo tail -n 80 /var/log/ai-harness/heat-guard.log
powerprofilesctl get
systemctl is-active thermald
```

## References

- [Netdata Linux installation](https://learn.netdata.cloud/docs/netdata-agent/installation/linux/)
