# Work Context Package

Plan-and-Task creates one resume anchor after an Issue reaches
`status/accept` or `status/working`:

```text
.specify/<feature|bugfix>/<work_id>/
```

Specify creates no Work Context Package.

## Resume Order

1. `work-context.yml`: Issue identity and revision, phase, last action, next action.
2. Feature only: `spec.override.md` when authorized, otherwise `spec.md`.
3. `plan-and-task.md`: HLD, human Plan decision, scope, Tasks, and self-tests.
4. `plan-and-task-check.md`: deterministic readiness and unresolved findings.
5. `context-pack.md`: concise human-readable handoff when needed.
6. `permission-envelope.yml`, Code Graph, or evidence files only for the active phase.

```yaml
work_id: "123"
category: feature
primary_issue: https://example.com/org/repo/issues/123
issue_status: status/accept
issue_updated_at: "2026-07-15T10:00:00Z"
issue_body_hash: "sha256:..."
phase: plan-review
source_revision: <git-revision>
last_completed_skill: speckit.team.plan-and-task
next_skill: speckit.team.plan-and-task
artifacts:
  spec: .specify/feature/123/spec.md
  plan_and_task: .specify/feature/123/plan-and-task.md
  plan_and_task_check: .specify/feature/123/plan-and-task-check.md
unresolved: []
```

Do not duplicate full Issue, Spec, or Plan content in this index.

## Git Policy

Commit Feature `spec.md`, `plan-and-task.md`, generated checks, and reviewed
team evidence. Ignore `spec.override.md`, private customer text, credentials,
and local memory. Repository policy decides whether the small context index and
department-only evidence are committed.
