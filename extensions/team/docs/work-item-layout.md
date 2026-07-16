# Team Work Item Layout

Plan-and-Task creates the formal work directory after a primary Issue is
visible at `status/accept` or `status/working`.

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
        |-- plan-and-task.md
        |-- plan-and-task-check.md
        |-- work-context.yml
        |-- context-pack.md
        |-- permission-envelope.yml
        |-- codegraph/
        `-- evidence/
```

Bugfix intake may create `assessment.md` under a slug-based Bugfix intake root
before formal planning. The assessment is intake evidence; it does not by
itself establish an accepted Issue identity. Bugfix work does not use
`spec.md`.

## Identity

- coding-repository Issue: `<work_id>` is its numeric Issue ID;
- enhancement-repository Issue: `<work_id>` is `enhancement-<issue-id>`;
- absolute Issue URL remains the global authority.

Never derive identity from a mutable title or silently select the newest work
directory.

## Core Files

- Feature `spec.md`: reviewed snapshot of accepted User Stories and their
  Verification behavior, generated from the Issue by Plan-and-Task.
- `plan-and-task.md`: Issue-wide HLD followed by single-module LLD Tasks,
  parallel/dependency design, minimum self-tests, compatibility, and rollback.
- `plan-and-task-check.md`: generated readiness result; never hand-edit a
  passing result.

`spec.override.md` may sit beside a Feature `spec.md` for an authorized
confidential handoff, but it must be ignored by Git and read first. It is not
used to copy private demand into committed files.
