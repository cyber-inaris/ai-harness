# CrewAI MVP Setup

## Purpose

This runbook describes the first practical CrewAI setup for `ai-harness`.

The MVP goal is intentionally small:

```text
Hermes receives a Telegram request.
Hermes calls a local CrewAI command.
CrewAI runs a docs-agent task.
docs-agent creates or updates a markdown report.
reviewer-agent checks the output.
Hermes returns a short summary to Telegram.
```

This proves the controller/worker pattern before connecting risky tools such as secrets, router changes, Notion writes, or provider accounts.

## References

CrewAI docs to check before installing:

| Resource | Link |
|---|---|
| CrewAI installation | https://docs.crewai.com/en/installation |
| CrewAI concepts | https://docs.crewai.com/en/concepts/agents |
| CrewAI tasks | https://docs.crewai.com/en/concepts/tasks |
| CrewAI hierarchical process | https://docs.crewai.com/en/learn/hierarchical-process |

CrewAI changes quickly. Treat this document as the local harness runbook, but verify install commands against the official docs before production use.

## Install CrewAI

CrewAI currently recommends installing the CLI through `uv`.

Install `uv` if missing:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart the shell or load `uv` into PATH, then install CrewAI:

```bash
uv tool install crewai
```

Upgrade later:

```bash
uv tool install crewai --upgrade
```

Verify:

```bash
crewai --version
crewai --help
```

## MVP Location

Put CrewAI project files under:

```text
/opt/ai-harness/repo/crews/ai_harness_ops/
```

Repository layout:

```text
ai-harness/
  crews/
    ai_harness_ops/
      .env.example
      pyproject.toml
      src/
        ai_harness_ops/
          __init__.py
          crew.py
          main.py
          config/
            agents.yaml
            tasks.yaml
          tools/
            __init__.py
            markdown_report_tool.py
```

Generated CrewAI projects may use a similar structure. If `crewai create crew ai_harness_ops` produces a different layout, keep the generated structure and adapt the paths in this runbook.

## Create Project

From the repo root:

```bash
mkdir -p crews
cd crews
crewai create crew ai_harness_ops
cd ai_harness_ops
crewai install
```

Do not commit real `.env` files. Commit only `.env.example`.

## Environment

The MVP should use a trusted model, not an unverified reseller.

Example `.env.example`:

```env
# Trusted model for manager/reviewer work.
OPENAI_API_KEY=
OPENAI_MODEL_NAME=gpt-4o

# Harness paths.
AI_HARNESS_REPO=/opt/ai-harness/repo
AI_HARNESS_DATA=/var/lib/ai-harness
AI_HARNESS_BENCHMARKS=/var/lib/ai-harness/benchmarks
```

On the VPS, real values should come from:

```text
/opt/ai-harness/secrets/hermes.env
/opt/ai-harness/secrets/providers.env
```

Do not store them inside the CrewAI project directory unless the file is local-only and ignored by git.

## Agents

Initial MVP agents:

```text
manager-agent
docs-agent
reviewer-agent
```

Later agents:

```text
ops-agent
benchmark-agent
pricing-agent
router-agent
notion-agent
github-agent
```

Example `agents.yaml` concept:

```yaml
docs_agent:
  role: "AI Harness Documentation Agent"
  goal: "Create and update clear operational markdown docs for ai-harness"
  backstory: >
    You maintain practical runbooks for a VPS-based AI-agent harness.
    You write concise markdown, avoid secrets, and prefer explicit commands.

reviewer_agent:
  role: "AI Harness Reviewer"
  goal: "Review task outputs for correctness, safety, missing steps, and secret leaks"
  backstory: >
    You are a strict reviewer for infrastructure and AI-agent operations docs.
    You check whether outputs are actionable and safe.
```

If using CrewAI hierarchical process, the manager can be configured through `manager_llm` or a custom manager agent.

## Tasks

First task: update a markdown report.

Example `tasks.yaml` concept:

```yaml
update_markdown_report:
  description: >
    Create or update a markdown report for the requested ai-harness topic.
    The report must include purpose, context, concrete steps, risks, and next actions.
    Do not include secrets, API keys, passwords, tokens, cookies, or private account data.
  expected_output: >
    A markdown report saved under the requested path, plus a short summary of changes.
  agent: docs_agent

review_markdown_report:
  description: >
    Review the markdown report created by docs_agent.
    Check for correctness, missing operational steps, unsafe instructions, and secret leaks.
  expected_output: >
    A review verdict: pass, pass-with-notes, or fail, with concise findings.
  agent: reviewer_agent
```

## Minimal Tool

The first custom tool should only write markdown to an allowed directory.

Allowed write paths:

```text
/opt/ai-harness/repo/docs/
/var/lib/ai-harness/benchmarks/
```

Tool rules:

```text
reject paths outside allowed roots
create parent directories if needed
refuse to write content containing obvious secret markers
return absolute path and byte count
```

Suggested tool file:

```text
crews/ai_harness_ops/src/ai_harness_ops/tools/markdown_report_tool.py
```

This tool can be implemented later. The MVP document only defines its contract.

## Crew Process

For the first runnable version, use sequential process:

```text
docs-agent writes report
reviewer-agent reviews report
result returns to Hermes
```

After the sequential MVP works, enable hierarchical process:

```text
manager-agent plans/delegates
docs-agent writes
reviewer-agent validates
manager-agent returns final summary
```

CrewAI hierarchical process requires a manager LLM or custom manager agent.

Conceptual Python structure:

```python
from crewai import Crew, Process

crew = Crew(
    agents=[docs_agent, reviewer_agent],
    tasks=[update_markdown_report, review_markdown_report],
    process=Process.sequential,
)

result = crew.kickoff(inputs={
    "topic": "ngrok nginx auth",
    "target_path": "/opt/ai-harness/repo/docs/networking/ngrok-nginx-auth.md",
})
```

Later hierarchical version:

```python
crew = Crew(
    agents=[docs_agent, reviewer_agent],
    tasks=[update_markdown_report, review_markdown_report],
    process=Process.hierarchical,
    manager_llm="trusted-admin-model",
    planning=True,
)
```

## Hermes Integration

MVP integration can be a local CLI command.

Hermes receives:

```text
"Update the docs about ngrok nginx auth"
```

Hermes runs:

```bash
cd /opt/ai-harness/repo/crews/ai_harness_ops
crewai run --inputs '{"topic":"ngrok nginx auth","target_path":"/opt/ai-harness/repo/docs/networking/ngrok-nginx-auth.md"}'
```

If CrewAI CLI input format differs in the installed version, create a wrapper script:

```text
scripts/run-crewai-task
```

Wrapper contract:

```bash
scripts/run-crewai-task docs-report \
  --topic "ngrok nginx auth" \
  --target /opt/ai-harness/repo/docs/networking/ngrok-nginx-auth.md
```

Hermes should call the wrapper, not raw internal Python, so the interface stays stable.

## First Smoke Scenario

Scenario:

```text
Hermes asks CrewAI docs-agent to create a markdown report.
Reviewer-agent checks it.
Hermes returns the summary.
```

Test prompt:

```text
Create a short markdown note at /opt/ai-harness/repo/docs/agents/crew-smoke-result.md.
Topic: CrewAI smoke test.
Include: purpose, what ran, output path, and next step.
Do not include secrets.
```

Expected result:

```text
file exists
file is markdown
file contains no secrets
reviewer verdict is pass or pass-with-notes
Hermes reports the path in Telegram
```

Verification:

```bash
test -f /opt/ai-harness/repo/docs/agents/crew-smoke-result.md
sed -n '1,120p' /opt/ai-harness/repo/docs/agents/crew-smoke-result.md
```

## Safety Gates

The first CrewAI MVP must not:

```text
write secrets
edit nginx
restart services
change router policy
call reseller APIs
write to Notion
commit or push to GitHub
```

Allowed:

```text
read docs
write docs under allowed paths
write benchmark notes under allowed paths
return summaries
```

## Promotion Checklist

Before adding more powerful agents, confirm:

```text
CrewAI can run from the VPS
Hermes can call the CrewAI wrapper
docs-agent writes only to allowed paths
reviewer-agent catches unsafe output
secrets are not printed in logs
task output path is reported back to Telegram
failures are understandable
```

Then add agents in this order:

1. `benchmark-agent`
2. `pricing-agent`
3. `github-agent`
4. `notion-agent`
5. `router-agent`
6. `ops-agent`

This order starts with low-risk documentation and benchmark work before granting infrastructure or account-changing power.
