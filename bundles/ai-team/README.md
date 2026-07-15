# AI Team Bundle

The `ai-team` bundle installs an enterprise collaboration layer without
overwriting native Spec Kit commands.

AI Team targets four large role skills. This bundle currently exposes the first
two agreed skills; later role skills remain unregistered until their contracts
and names are decided.

## Installed Components

| Component | Installed item |
|---|---|
| Role extension | `team`, exposing exactly two `speckit.team.*` skills |
| Bug artifacts | native `bug` extension, reused without modification |
| Agent context | native `agent-context` extension |

No preset overlays native `speckit.specify`, `speckit.plan`,
`speckit.tasks`, `speckit.implement`, or `speckit.converge`.

## Install

```bash
specify init . --integration codex --integration-options="--skills"
specify bundle catalog add https://raw.githubusercontent.com/EuphoriaYan/spec-kit/main/bundles/catalog.json --id ai-team --policy install-allowed
specify bundle install ai-team
```

Bundle installation immediately creates or refreshes the short AI Team pointer
in the active tools' rule files, including `AGENTS.md`. It uses only the trusted
initializer shipped with this Spec Kit distribution; third-party extension
installers are not executed.

After installation, start in chat with a normal requirement or defect. The
active AI tool starts with `speckit.team.specify`; after the required human
acceptance, the user starts `speckit.team.plan-and-task` with the Issue or Work
ID. Each role skill performs its own checks and stops at its human decision
boundary; no AI Team workflow command is installed.
