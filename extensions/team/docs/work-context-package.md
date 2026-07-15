# Work Context Package

Each durable task is one directory:

```text
.specify/<feature|bugfix>/<work_id>/
```

The directory is both the document package and the resume anchor. Do not keep a
second index under `.specify/ai-team/work`, native `specs/`, or a separate bug
tree.

## Files To Read On Resume

Read in this order and stop as soon as the current phase is clear:

1. `work-context.yml`: identity, phase, source snapshot, last action, next action.
2. `spec.md` or gitignored `spec.override.md`: intended behavior.
3. `plan-and-task.md`: Plan HLD, recorded human Plan decision, scope, Tasks, and
   self-tests. The same file survives a pause between Plan review and Task
   decomposition.
4. `plan-and-task-check.md`: readiness result and unresolved findings.
5. `context-pack.md`: short human-readable handoff when more explanation is needed.
6. `permission-envelope.yml`, `codegraph/`, or `evidence/` only when the active
   phase requires them.

## Minimal Context Index

```yaml
work_id: "123"
category: feature
primary_work_item: https://example.com/org/repo/issues/123
phase: specified | plan-review | plan-paused | task-design | tasks-ready | blocked | done
source_revision: <git-revision>
last_completed_skill: speckit.team.specify
next_skill: speckit.team.plan-and-task
artifacts:
  spec: .specify/feature/123/spec.md
  plan_and_task: .specify/feature/123/plan-and-task.md
  plan_and_task_check: .specify/feature/123/plan-and-task-check.md
unresolved: []
```

Do not duplicate full document contents in this YAML file. It is a small resume
index, not another specification or plan.

## Git Policy

Commit `spec.md`, `plan-and-task.md`, `plan-and-task-check.md`, and reviewed
team evidence. Ignore `spec.override.md`, private customer text, credentials,
and local memory. Repository privacy policy decides whether
`work-context.yml`, `context-pack.md`, and department-only evidence are committed.
