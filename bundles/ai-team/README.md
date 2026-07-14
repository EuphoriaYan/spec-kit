# AI Team SDD bundle

One-step bootstrap for enterprise AI Team Spec-Driven Development in a coding
repository.

## What it installs

| Kind | ID | Purpose |
|------|-----|---------|
| Extension | `ai-team` | Enterprise SDD commands, hooks, and work context |
| Extension | `bug` | Bug assess/fix/test stages for bugfix workflow |
| Extension | `agent-context` | Managed Spec Kit section in agent context files |
| Preset | `ai-team-sdd-governance` | Work-item traceability, handoff reading, checks, evidence |
| Workflow | `ai-team-intake` | Plain-language intake → issue → formal handoff |
| Workflow | `ai-team-sdd` | Feature / new-project SDD cycle |
| Workflow | `ai-team-bugfix` | Bug fix lifecycle with evidence |

This bundle is **integration-agnostic** but AI Team workflows require one of:
`codex`, `claude`, `cursor-agent`, or `trae`. Pass `--integration` on init.

## Usage

Install this distribution and initialize the project:

```bash
specify init . --integration cursor-agent
```

Initialization reads the packaged distribution catalog and installs this bundle
automatically. No catalog registration or separate bundle command is required.
The catalog entry remains `verified: false` until clean-project init install
tests pass for a packaged CLI build.

### Validate the manifest

Maintainers can validate changes locally:

```bash
specify bundle validate --path bundles/ai-team --offline
```

## After install

1. Run `speckit.ai-team.workspace` to record repository boundaries.
2. Optionally run `speckit.agent-context.update` when using the agent-context extension.
3. Start work with `speckit.ai-team.start` or `specify workflow run ai-team-intake`.
