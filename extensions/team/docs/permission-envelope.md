# AI Team Permission Envelope

The Permission Envelope records what one AI Team work item may read, write,
execute, and access over the network. One envelope covers the selected Task
batch; do not create or approve one envelope per Task.

It does not claim that every AI coding tool has a sandbox. The envelope must
state how its restrictions are enforced.

## Storage And Shape

```text
.specify/feature/<work_id>/permission-envelope.yml
```

This file is the Feature implementation envelope. Bugfix records its proposed
and actual write boundary in `assessment.md` and `fix.md`.

```yaml
schema_version: "1.0"
work_id: 003-search-export
mode: analysis
status: ready
enforcement_mode: policy-only
integration: codex
allow:
  read_paths:
    - AGENTS.md
    - .specify/feature/003-search-export
    - src/upload
    - tests/upload
  write_paths: []
  commands:
    - rg
    - git diff
  network:
    - none
deny:
  read_paths:
    - .env
    - credentials
  write_paths:
    - .git
    - other-module-internals
  commands:
    - destructive-history-rewrite
    - unreviewed-package-install
  network:
    - upload-source-or-private-data
approval_required: []
runtime:
  adapter: ""
  verified: false
  gaps:
    - policy is not a runtime sandbox
approved_by: ""
approved_at: ""
updated_at: "2026-07-16T10:00:00Z"
```

Paths must be repository-relative and as narrow as practical. Do not use broad
wildcards when the affected module is known.

`status` must be one of:

- `ready`: mechanically valid and authorized without a human decision because
  the current operation has no human-gate trigger;
- `pending-review`: structurally ready for a human decision;
- `approved`: approved by the named human in `approved_by` at `approved_at`;
- `blocked`: unsafe or incomplete; record concrete `blockers`;
- `expired`: approval no longer matches the work, source revision, or scope.

`approval_required` lists triggers detected in the current work, not every
trigger that might occur in the future. Use only these human-gate triggers:
cross-repository or cross-module change, public-contract change, new dependency,
security or license decision, incompatible change, or expansion beyond the
approved Plan.

A `ready` envelope must have empty `approval_required`, `approved_by`, and
`approved_at`. An approved envelope must have non-empty `approved_by`, `approved_at`, and
`updated_at`. Both timestamps use ISO 8601 UTC, and `updated_at` cannot be
earlier than `approved_at`.

Changing `mode`, allowed operations, or scope invalidates prior approval. Set
`status` to `ready` when the revised work has no human-gate trigger, otherwise
use `pending-review` or `blocked`; clear `approved_by` and `approved_at`, and
refresh `updated_at`.

## Enforcement Modes

| Mode | Meaning | Allowed claim |
|---|---|---|
| `policy-only` | prompts, repository rules, and human gates describe the boundary | "boundary recorded" |
| `agent-native` | the selected AI tool's native sandbox or approval controls are configured and verified | "native controls verified" |
| `wrapper-enforced` | file, command, and network operations pass through a team-owned enforcement adapter | "wrapper controls verified" |

Default to `policy-only`. Never upgrade the mode because a tool usually has a
sandbox; record the concrete adapter or configuration and verification result.

Human approvals and skill checks do not sandbox shell commands. A skill runs
with the current user's privileges unless an external agent or wrapper
constrains it.

## Lifecycle

1. At planning, create an analysis envelope with narrow read-only paths and
   commands. Use `ready` for clear repository-local analysis; use
   `pending-review` only for cross-repository/private reads or sensitive
   network access.
2. After Plan and Task review, revise the same envelope for the smallest write paths,
   commands, and dependency operations needed for implementation.
3. Use `ready` when the complete Task batch stays in one repository and one
   module and has no human-gate trigger. Otherwise use `pending-review` and
   record the detected triggers.
4. A human approves the complete risky batch once and records `approved_by`
   and `approved_at`; never ask for Task-by-Task approval.
5. Evidence records the effective enforcement mode and any operations that
   required approval.
6. Expanding beyond the Plan requires another human decision; AI agents cannot
   self-authorize.

## Stop Conditions

Stop when:

- the work slug, repository role, or target module is unknown;
- a required read, write, command, or network action is outside the envelope;
- private data may leave its approved repository or service boundary;
- hard runtime confinement is required but only `policy-only` is available;
- an AI tool requests access beyond the Plan or across a human-gated boundary
  without a named approval;
- the envelope and Work Context Package identify different work units.

## Tool Adapters

Tool-specific enforcement belongs behind an adapter. An adapter should report:

- supported controls: read, write, command, network, approval prompts;
- applied configuration and scope;
- verification evidence;
- unsupported controls and fallback stop conditions.

Codex, Claude Code, Cursor Agent, and Trae may expose different controls. The
shared envelope remains stable while adapters translate it into tool-specific
settings when available.
