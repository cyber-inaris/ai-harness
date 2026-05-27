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
mcp-ai-harness-fs              # filesystem MCP wrapper for Hermes
agent-task                     # stable wrapper Hermes should call
```

Useful `agent-task` commands:

```bash
./scripts/agent-task status
./scripts/agent-task mode-route --message "добавь в борду: протестировать tcdmx.com"
./scripts/agent-task notion-create-task --title "Test reseller tcdmx.com" --type provider --risk medium --agent benchmark
./scripts/agent-task brainstorm-start --topic "Agent modes"
```
