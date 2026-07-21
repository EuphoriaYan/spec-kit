# Installation and Environment Diagnostics

[中文主文档](installation.md)

This guide installs AI Team Skills into a real coding repository. After setup,
users work from their AI coding tool's chat instead of manually orchestrating a
CLI workflow.

## Prerequisites

- Python 3.11+, Git, and uv;
- CodeGraph CLI `>=1.0.0,<2.0.0` before the first Plan or Assess run;
- one supported integration: `codex`, `claude`, `cursor-agent`, or `trae`.

```bash
npm install -g @colbymchenry/codegraph@^1
codegraph --version
```

Codex and Claude Code integrations require their CLI executable on `PATH`.
Cursor and Trae support IDE-only Skills; Cursor CLI is needed only for optional
headless dispatch.

## Install and Initialize

Install the reviewed six-skill build from its fixed tag:

```bash
uv tool install specify-cli --force \
  --from git+https://github.com/EuphoriaYan/spec-kit.git@v0.12.5+teamwork.3
specify --version

cd <coding-repository>
specify init . --integration codex
```

Replace `codex` with `claude`, `cursor-agent`, or `trae` as needed. The default
`team` profile installs the six primary Team Skills, advanced extension entries,
and their required resources.
Use `--skill-profile full` only when native Spec Kit Skills are also required.

## Installed Result

Initialization:

1. installs six self-contained primary Team Skills and advanced extension entries;
2. creates `.specify/team/` context and configuration;
3. adds a managed natural-language router to `AGENTS.md` and tool-specific rules;
4. ignores Feature/Bugfix work packages, the `.codegraph/` index, and only the
   generated `speckit-team-*` Skill directories; it does not blanket-ignore
   `.agents/` or `.specify/`;
5. defers the CodeGraph version and index check until Plan or Assess, without
   running remote installers.

| Tool | Skills | Rule entry |
|---|---|---|
| Codex | `.agents/skills/` | `AGENTS.md` |
| Claude Code | `.claude/skills/` | `CLAUDE.md` imports `AGENTS.md` |
| Cursor | `.cursor/skills/` | `.cursor/rules/specify-rules.mdc` |
| Trae | `.trae/skills/` | `.trae/rules/project_rules.md` |

The Team extension source is not copied into the product repository.

For an existing project, initialize and verify CodeGraph before planning or
assessment:

```bash
codegraph init
codegraph status
```

Continue with the [Quick Start](quickstart_en.md).
