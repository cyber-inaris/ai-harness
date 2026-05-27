# Brainstorming

Use this skill when the user asks Hermes to brainstorm, design, invent a feature, choose architecture, or modify behavior creatively.

## Hard Gate

Do not implement, edit files, deploy, install, or change runtime behavior until a design has been presented and approved by the user.

## Workflow

1. Explore current project context first.
2. Ask one clarifying question at a time.
3. Propose 2-3 approaches with trade-offs.
4. Recommend one approach and explain why.
5. Present the design in small sections.
6. Ask for approval.
7. Write the approved spec to `/opt/ai-harness/repo/docs/superpowers/specs/`.
8. Self-review the spec for placeholders, contradictions, scope creep, and ambiguity.
9. Ask the user to review the spec before implementation planning.

## Routing

Use this stable command to create a local brainstorming task record:

```bash
/opt/ai-harness/repo/scripts/agent-task brainstorm-start --topic "..."
```

If the user only asks to add the idea to Notion/tasks, use Notion mode instead:

```bash
/opt/ai-harness/repo/scripts/agent-task notion-create-task --title "..." --type research --risk low --agent planner
```

## Rules

- Keep questions short.
- Ask one question per turn.
- Do not turn every discussion into a Notion task.
- Create Notion tasks only when the user asks for Notion/board/backlog/planning, or when the design is approved and needs implementation tracking.
