# Git Sync Setup

Step-by-step guide for configuring the bi-directional Git sync between the server and your Mac.

## Architecture

```
Mac (vault-personal, human SoT)
        │
        │  SSH git push/pull over Tailscale
        │
Server /opt/vaults/vault-personal  ←→  Git remote "mac"
Server /opt/vaults/vault-agents    →   Git remote "origin" (Mac pulls only)
```

---

## 1. Server: Configure SSH for Git

The `ai` user on the server needs an SSH key pair for Git operations.

```bash
# On server, as user ai
ssh-keygen -t ed25519 -C "vault-sync@server" -f ~/.ssh/vault_sync -N ""
cat ~/.ssh/vault_sync.pub
```

Add this public key to:
- GitHub (if using GitHub as central remote)
- Or the `~/.ssh/authorized_keys` on a dedicated Git server

---

## 2. Mac: Add the server as a remote

### Option A — Direct SSH over Tailscale (recommended)

The server's Tailscale hostname is typically `<machine-name>` or accessible via its Tailscale IP.

```bash
# On Mac
cd ~/path/to/vault-personal  # your local Obsidian vault folder

git init  # if not already a git repo
git remote add server ssh://ai@<tailscale-ip-or-hostname>/opt/vaults/vault-personal
```

Test connectivity:
```bash
ssh ai@<tailscale-ip> "echo ok"
```

### Option B — Via GitHub (centralised)

```bash
# On server, inside vault-personal
git remote add origin git@github.com:yourorg/vault-personal.git
git push -u origin main

# On Mac
git clone git@github.com:yourorg/vault-personal.git ~/Documents/vault-personal
```

---

## 3. Server: Configure vault-personal remote

```bash
# On server, as user ai
cd /opt/vaults/vault-personal
git remote add mac ssh://your-mac-user@<mac-tailscale-ip>/Users/your-user/Documents/vault-personal
```

Or if using GitHub:
```bash
git remote add origin git@github.com:yourorg/vault-personal.git
git push -u origin main
```

Update `vault-sync.sh` environment if using a non-default remote name:
```bash
# In /etc/systemd/system/vault-sync.service
Environment=VAULT_PERSONAL_REMOTE=origin
```

---

## 4. Server: Configure vault-agents remote

`vault-agents` is server SoT. Mac only pulls from it.

```bash
# On server, as user ai
cd /opt/vaults/vault-agents
git remote add origin git@github.com:yourorg/vault-agents.git
git push -u origin main
```

On Mac (read-only mirror):
```bash
cd ~/Documents/vault-agents
git clone git@github.com:yourorg/vault-agents.git .
# Set up a cron/launchd that runs: git pull origin main
```

---

## 5. Mac: Obsidian setup

1. Download and install [Obsidian](https://obsidian.md)
2. Open Obsidian → **Open folder as vault**
3. Select `~/Documents/vault-personal` (your local git clone)
4. Go to **Settings → Community plugins → Browse**
5. Search for **Dataview** and install it
6. Enable Dataview in the installed plugins list

**Optional read-only vault-agents view:**
- In Obsidian → **Open another vault**
- Select `~/Documents/vault-agents`
- This gives you read-only visibility into agent activity

---

## 6. Mac: Automated sync (LaunchAgent)

Create a LaunchAgent to pull vault-personal from the server every 5 minutes:

```xml
<!-- ~/Library/LaunchAgents/com.vault.sync.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.vault.sync</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-c</string>
    <string>cd ~/Documents/vault-personal && git pull --rebase origin main 2>&1 >> ~/Library/Logs/vault-sync.log</string>
  </array>
  <key>StartInterval</key>
  <integer>300</integer>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.vault.sync.plist
```

---

## 7. Conflict resolution summary

| Vault | Mac action | Server action | Conflict winner |
|---|---|---|---|
| vault-personal | push new notes | pull + rebase | Newer file (timestamp) |
| vault-agents | git pull only | commit + push | Server always wins |

---

## 8. Troubleshooting

### Permission denied (publickey)
```bash
ssh -vT ai@<tailscale-ip>  # check SSH key negotiation
```

### Rebase conflicts
```bash
# On server
cd /opt/vaults/vault-personal
git rebase --abort
git status
# vault-sync.sh handles this automatically with timestamp fallback
```

### Vault sync timer not running
```bash
systemctl status vault-sync.timer
systemctl status vault-sync.service
journalctl -u vault-sync.service -n 50
```
