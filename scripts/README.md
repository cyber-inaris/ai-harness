# Scripts

Helper scripts for VPS setup, provider checks, and benchmark runs.

Scripts should be safe to read before running and should not embed real secrets.

Current scripts:

```text
deploy-host.sh                 # base host setup
install-hermes.sh              # Hermes install/service setup
install-omniroute.sh           # OmniRoute install/service setup
install-langgraph-runtime.sh   # LangGraph task runtime setup
disable-laptop-sleep.sh        # prevent home laptop hosts from suspending
agent-task                     # stable wrapper Hermes should call
provider-bindings              # track provider Telegram binding state in SQLite
```

Useful `agent-task` commands:

```bash
./scripts/agent-task status
./scripts/agent-task mode-route --message "добавь в борду: протестировать tcdmx.com"
./scripts/agent-task command-route --message "/omni"
./scripts/agent-task command-run status
./scripts/agent-task command-run omni
./scripts/agent-task command-run hermes
./scripts/agent-task command-run deploy status
./scripts/agent-task notion-create-task --title "Test reseller tcdmx.com" --type provider --risk medium --agent benchmark
./scripts/agent-task brainstorm-start --topic "Agent modes"
```

Provider binding state:

```bash
./scripts/provider-bindings init
./scripts/provider-bindings exclude --provider freemodel
./scripts/provider-bindings record \
  --provider freemodel \
  --provider-account-ref "wgsr7b2t7@mozmail.com" \
  --start-link "https://t.me/FreeModelDevBot?start=<token>" \
  --ss-panel-response-json-file /tmp/sspanel-response.json \
  --executor codex-mac
./scripts/provider-bindings list --provider freemodel
```

The DB path defaults to `data/provider-bindings.sqlite` and can be overridden
with `AI_HARNESS_BINDINGS_DB`, for example
`/var/lib/ai-harness/provider-bindings.sqlite` on the Hermes server.
