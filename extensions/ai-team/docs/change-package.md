# AI Team Change Package

The Change Package is the single index for one AI Team work unit. It lets a
human or AI agent find the work item, SDD artifacts, handoffs, code graph,
evidence, permission envelope, and PR without searching several directories.

The package is an index, not another copy of the requirement or plan. Source
artifacts remain authoritative at their existing locations.

## Storage

```text
.specify/ai-team/work/<work_slug>/
|-- change-package.yml       # stable artifact and authority index
|-- work-context.yml         # current phase and next command
|-- context-pack.md          # human-readable resume summary
|-- permission-envelope.yml  # task-scoped access contract
|-- handoffs/
|-- codegraph/
`-- evidence/
```

Spec Kit artifacts stay under `specs/<work_slug>/`. Bug artifacts stay under
`.specify/bugs/<bug_slug>/`. The Change Package points to them; it does not move
or duplicate them.

## Required Shape

```yaml
schema_version: "1.0"
work_slug: 003-search-export
work_type: feature
repository_role: coding
work_item:
  coding_issue_url: https://example.com/org/project/issues/456
  handoff_requirement_url: ""
  bug_slug: ""
artifacts:
  specification:
    path: specs/003-search-export/spec.md
    authority: requirement
    status: current
    visibility: project
  plan:
    path: specs/003-search-export/plan.md
    authority: architecture
    status: draft
    visibility: project
  tasks:
    path: specs/003-search-export/tasks.md
    authority: implementation-plan
    status: missing
    visibility: project
  handoffs:
    path: .specify/ai-team/work/003-search-export/handoffs
    status: current
    visibility: project
  code_graph:
    path: .specify/ai-team/work/003-search-export/codegraph
    status: current
    visibility: project
  evidence:
    path: .specify/ai-team/work/003-search-export/evidence
    status: draft
    visibility: project
  permission_envelope:
    path: .specify/ai-team/work/003-search-export/permission-envelope.yml
    status: current
    visibility: project
  pull_request:
    url: ""
    status: missing
owners:
  requirement: ""
  architecture: ""
  module: ""
  review: ""
source_snapshot: ""
updated_at: ""
```

Allowed artifact status values are `missing`, `draft`, `approved`, `current`,
`superseded`, and `complete`. Visibility is `local`, `internal`, `project`, or
`public`.

## Authority Rules

- the issue or allowed handoff URL explains why the work exists;
- `spec.md` owns accepted behavior for this work unit;
- `plan.md` owns the approved technical approach;
- `tasks.md` owns implementation sequencing;
- handoff documents transfer approved context between isolated roles;
- source code remains the first truth for current implementation behavior;
- evidence records what was actually verified;
- the permission envelope limits this task's access, not system behavior;
- owner decisions override AI summaries and historical memory.

The Change Package must not silently promote task discoveries into team rules,
architecture policy, public interfaces, or long-term enterprise guidance. Such
changes require the existing human review path.

## Update Protocol

1. `speckit.ai-team.context` creates or reconstructs the package at intake.
2. Each phase updates only its artifact entry, status, source snapshot, and
   owner reference.
3. Resume loads `change-package.yml` first, then `work-context.yml`, then only
   the artifacts needed for the current phase.
4. PR preparation verifies that indexed paths and URLs match the actual diff.
5. A missing required artifact is reported as missing; the AI must not invent a
   path or mark it complete.

## Privacy

The package stores references, not raw confidential demand. A public coding
repository must not contain private enhancement draft paths, raw customer text,
commercial context, or credentials. Use a public-safe summary or an allowed
handoff reference according to repository policy.

## Relationship To OpenSpec

This package borrows the useful idea of one change-level index without adopting
automatic living-spec mutation. AI Team governance and architecture rules are
stable project controls and change only through their explicit owner review.
