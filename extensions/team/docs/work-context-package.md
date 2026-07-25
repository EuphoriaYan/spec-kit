# Work Context Package

The Work Context Package is a small resume index. It does not replace the
native Feature or Bugfix artifacts and must not copy full Issues, Specs,
assessments, logs, or reports.

## Feature

Plan-and-Task creates or resumes:

```text
.specify/feature/<work_id>/
|-- work-context.yml
`-- context-pack.md
```

Read in this order:

1. `work-context.yml`: Issue identity and revision, phase, last Skill, next Skill.
2. `spec.override.md` when authorized, otherwise `spec.md`.
3. `plan-and-task.md` and `plan-and-task-check.md`.
4. `context-pack.md`: concise handoff and unresolved items.
5. `permission-envelope.yml`, Code Graph, and evidence required by the active
   phase.

```yaml
work_id: "123"
category: feature
primary_issue: https://example.com/org/repo/issues/123
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

## Bugfix

Assess creates and later Bugfix Skills resume:

```text
.specify/bugfix/<bug_slug>/
|-- work-context.yml
`-- context-pack.md
```

Read in this order:

1. `work-context.yml`: Bug Slug, source summary, phase, last Skill, next Skill.
2. `assessment.md`: observation, impact, permission boundary, and approval.
3. `fix.md` and `test.md` when the phase has reached Fix or Review.
4. `context-pack.md`: concise current findings, unresolved items, and next action.
5. Code Graph and evidence required by the active phase.

```yaml
bug_slug: "upload-timeout"
category: bugfix
source: "upload timeout reported during development"
phase: assessment-ready
source_revision: <git-revision>
last_completed_skill: speckit.team.assess
next_skill: speckit.team.fix
artifacts:
  assessment: .specify/bugfix/upload-timeout/assessment.md
  fix: .specify/bugfix/upload-timeout/fix.md
  test: .specify/bugfix/upload-timeout/test.md
unresolved: []
```

Assess updates the package after risk routing and any required human decision. Fix updates it
after implementation and verification. Review reads it to resolve the same Bug
Root and may update only review phase metadata when repository policy allows.
This gives Bugfix work an explicit cross-session resume path without introducing
Feature Spec, Plan, or Task fields.

## Git Policy

Feature and Bugfix work packages are runtime context owned by the installed
Team extension. The installer adds `/.specify/feature/` and
`/.specify/bugfix/` to the target coding repository's `.gitignore`; do not
commit them. It also ignores the local `/.codegraph/` index and only the
generated `speckit-team-*` Skill directories for supported integrations.
Do not ignore all of `.agents/` or `.specify/`: those roots may contain
project-owned Skills and shared `.specify/team/` configuration. Stable Team
configuration remains separately governed and is not covered by these ignore
rules.

Cross-person handoff uses the authoritative Issue and PR discussion. Publish a
public-safe User Story, accepted Plan/Task summary, verification result, and
remaining risk there. A significant HLD may be promoted to project `docs/`
after human review. Never publish private customer text, credentials, local
memory, raw logs, or `spec.override.md`.

If older work-package files are already tracked, adding `.gitignore` does not
remove them from the Git index. Migrate them in a focused repository PR after
confirming that required Issue, PR, test, and HLD facts remain available.
