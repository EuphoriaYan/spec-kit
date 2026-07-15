# Team Work Item Layout

All Team Feature and Bugfix documents use one directory contract:

```text
.specify/
|-- feature/
|   `-- <work_id>/
|       |-- spec.md
|       |-- plan-and-task.md
|       |-- plan-and-task-check.md
|       |-- work-context.yml
|       |-- context-pack.md
|       |-- permission-envelope.yml
|       |-- codegraph/
|       `-- evidence/
`-- bugfix/
    `-- <work_id>/
        `-- same file contract
```

`work_id` is the stable unique identifier from the primary Issue or approved
requirement. It must match `[A-Za-z0-9][A-Za-z0-9._-]{0,127}`. Prefer an Issue
number or durable requirement ID. Never derive it from a mutable title.

Feature, confidential Feature, and new-project work use `feature`. Defect work
uses `bugfix`. The category and ID together form the canonical identity and
must not change between skills, sessions, branches, or AI tools.

The Team extension does not store its work artifacts under native `specs/` or
under a separate bug directory. Native Spec Kit commands may continue to use
their original layout; Team skills do not modify that behavior.

## Core Files

- `spec.md`: observable problem or desired behavior, User Stories or Bugfix
  reproduction, scope, non-goals, and acceptance points.
- `plan-and-task.md`: Issue-wide HLD and module change plan, followed by
  single-module LLD Tasks, their parallel/dependency model, minimum self-tests,
  compatibility, migration, and rollback.
- `plan-and-task-check.md`: generated `ready`, `revise`, or `blocked` result
  covering cross-file consistency, scope, Code Graph, ownership, and self-test
  findings. Generate it with `scripts/check_plan_and_task.py`; do not hand-edit
  a passing result.

`spec.override.md` may sit beside `spec.md` for an authorized confidential
handoff, but it must be ignored by Git. When present, planning reads it before
`spec.md` without copying private source text into committed files.
