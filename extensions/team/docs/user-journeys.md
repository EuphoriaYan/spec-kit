# AI Team User Journeys

The target model has four role skills. This iteration exposes only Specify and
Plan-and-Task; later role skills remain unnamed. Internal capability documents
and scripts are loaded by the active role and are not separate user commands.

## One-Sentence Feature

```text
Please add CSV export. Keep exported columns aligned with the result list.
```

1. `speckit.team.specify` classifies the request, checks privacy, creates the
   primary Feature Issue, and writes `spec.md` with testable User Stories.
2. The requester approves publication of the exact Issue draft inside Specify;
   the new Issue starts at `state/draft`.
3. Outside any skill, the Technical Committee decides whether to accept the
   Feature and records scope, release/wave, owner, and `state/accepted`.
4. `speckit.team.plan-and-task` loads source and Code Graph evidence, then
   writes one LLD-capable `plan-and-task.md`, minimum self-tests, and
   `plan-and-task-check.md`.
5. An architect/module owner approves or revises the Plan and Tasks.
6. A later development role skill changes code, runs tests, compares
   actual scope with the Plan, and writes the Evidence Board.
7. Named humans review and merge.

## Existing Public Feature Issue

Provide the Issue URL in the same chat request. Specify reuses the Issue instead
of creating another one and checks that its User Stories and labels are valid.

## Confidential Enterprise Feature

Provide only the authorized internal requirement or handoff URL. Specify keeps
raw customer text out of the public coding repository. Plan-and-Task fetches
the URL within its Permission Envelope, combines allowed content with
`spec.md`, writes gitignored `spec.override.md`, and uses the override first.

## Bugfix

1. `speckit.team.specify` creates or validates the coding Bug Issue and
   captures observation, expected behavior, reproduction, and acceptance.
2. Bugfix skips Technical Committee Feature acceptance, but a maintainer still
   triages it and records `state/accepted` or `state/working` before planning.
3. `speckit.team.plan-and-task` produces root-cause evidence, architecture
   impact, fix scope, regression Tasks, self-tests, and rollback.
4. A later development role skill applies the fix and records
   regression tests, actual scope, Evidence Board, and residual risk.

Several Issues may share one change only when they are different symptoms of
one root cause. Map every Issue to separate reproduction and verification.

## New Project

New-project work uses the Feature journey and Standard planning. Plan-and-Task
must define architecture boundaries, the runnable spine, module ownership,
interfaces, dependency minimum, deployment, rollback, and first end-to-end
verification before implementation.

## Compact Planning

Users may ask for Compact in ordinary language. Plan-and-Task recommends it only
after impact evidence proves the work is low risk. A human confirms the mode.
Compact still creates `plan-and-task.md` and the generated
`plan-and-task-check.md`.

## Resume

- New chat/tool/session: invoke the role owning the current phase with the
  `work_id` or Issue URL.
- Every role reruns context initialization and reconstructs from artifacts.
- If source, Issue, or scope changed, stop and reconcile before continuing.

## Post-Delivery Knowledge

When requested after completed work, a later role skill loads retrospective,
memory, or release archive references progressively.
