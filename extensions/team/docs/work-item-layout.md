# Team Work Item Layout

Plan-and-Task creates a Feature work directory after a primary Issue is visible
at `status/accept` or `status/working`. Assess creates a separate Bugfix work
directory; Bugfix does not use planning artifacts.

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
    `-- <bug_slug>/
        |-- assessment.md
        |-- fix.md
        |-- test.md
        |-- work-context.yml
        |-- context-pack.md
        `-- evidence/
```

Bugfix uses `assessment.md` as the human-approved handoff into Fix. Fix records
the actual change and verification in `fix.md` and `test.md`; Review may add
review evidence. Bugfix does not use `spec.md`, `plan-and-task.md`, or
`plan-and-task-check.md`.

## Identity

- Feature in a coding repository: `<work_id>` is its numeric Issue ID;
- Feature in an enhancement repository: `<work_id>` is
  `enhancement-<issue-id>`;
- Bugfix: `<bug_slug>` is the stable local artifact key created by Assess
  before or after Issue publication;
- when a Bugfix Issue is linked, its absolute URL is the repository-tracking
  identity and is recorded in the ready or risk-approved assessment before Fix.

Never silently select the newest work directory. A generated Bug Slug may be
derived from the initial symptom, but it must remain stable after assessment
approval even when the Issue title changes.

## Core Files

- Feature `spec.md`: reviewed snapshot of accepted User Stories and their
  Verification behavior, generated from the Issue by Plan-and-Task.
- Feature `plan-and-task.md`: Issue-wide HLD followed by single-module LLD Tasks,
  parallel/dependency design, minimum self-tests, compatibility, and rollback.
- Feature `plan-and-task-check.md`: generated readiness result; never hand-edit a
  passing result.
- Bugfix `assessment.md`: observed evidence, impact, permission boundary, fix
  strategy, test strategy, and risk-routing state.
- Bugfix `fix.md` and `test.md`: actual change scope and verification evidence.
- `work-context.yml` and `context-pack.md`: small resume indexes for both
  Feature and Bugfix; they point to native artifacts without duplicating them.

`spec.override.md` may sit beside a Feature `spec.md` for an authorized
confidential handoff, but it must be ignored by Git and read first. It is not
used to copy private demand into committed files.

## Persistence Boundary

Everything under `.specify/feature/<work_id>/` and
`.specify/bugfix/<bug_slug>/` is local runtime context and is ignored by Git.
It may be deleted after its useful resume window. Durable collaboration lives
in the Issue, PR, source, tests, and explicitly promoted HLD or long-term
knowledge. The Team extension source remains in the external Spec Kit
distribution; installation copies only the skills, bootstrap/configuration,
agent-rule pointers, and managed ignore rules needed by the target repository.
