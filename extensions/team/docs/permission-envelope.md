# AI Team Permission Envelope

The Permission Envelope records what one AI Team task may read, write, execute,
and access over the network. It is task-scoped and lives beside the Change
Package.

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
status: pending-review
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
approval_required:
  - expand-write-paths
  - public-contract-change
  - cross-module-change
  - dependency-install
  - external-network-write
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

- `pending-review`: structurally ready for a human decision;
- `approved`: approved by the named human in `approved_by` at `approved_at`;
- `blocked`: unsafe or incomplete; record concrete `blockers`;
- `expired`: approval no longer matches the work, source revision, or scope.

An approved envelope must have non-empty `approved_by`, `approved_at`, and
`updated_at`. Both timestamps use ISO 8601 UTC, and `updated_at` cannot be
earlier than `approved_at`.

Changing `mode`, allowed operations, or scope invalidates prior approval. Set
`status` to `pending-review` or `blocked`, clear `approved_by` and
`approved_at`, and refresh `updated_at`.

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

1. At intake, create an analysis envelope with read-only paths and commands and
   set it to `pending-review`.
2. Before code graph or source analysis, a human reviews sensitive reads and
   network access.
3. After plan and task review, revise the envelope for the smallest write paths,
   commands, and dependency operations needed for implementation.
4. Before implementation, a human approves the revised envelope and records
   `approved_by` and `approved_at`; refresh `updated_at` for that approved
   revision.
5. Evidence records the effective enforcement mode and any operations that
   required approval.
6. Expanding the envelope requires another human decision; AI agents cannot
   self-authorize.

## Stop Conditions

Stop when:

- the work slug, repository role, or target module is unknown;
- a required read, write, command, or network action is outside the envelope;
- private data may leave its approved repository or service boundary;
- hard runtime confinement is required but only `policy-only` is available;
- an AI tool requests broader access without a named human approval;
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
