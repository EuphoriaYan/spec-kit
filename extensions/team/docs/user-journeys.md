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
4. `speckit.team.plan-and-task` loads source and Code Graph evidence and writes
   the Issue-wide HLD into `plan-and-task.md`.
5. A human chooses to continue to Task decomposition, pause for discussion, or
   revise the Plan. The same file is reused after resume.
6. After continuation, Plan-and-Task writes single-module LLD Tasks, minimum
   self-tests, and the generated `plan-and-task-check.md`.
7. An architect/module owner approves or revises the checked Plan and Tasks.
8. A later development role skill changes code, runs tests, compares
   actual scope with the Plan, and writes the Evidence Board.
9. Named humans review and merge.

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

New-project work uses the Feature journey. Plan-and-Task must define
architecture boundaries, the runnable spine, module ownership,
interfaces, dependency minimum, deployment, rollback, and first end-to-end
verification before implementation.

## Plan Discussion And Task Decomposition

Every change uses the same path. Plan-and-Task first produces the Plan HLD and
stops for a human decision. Small local changes naturally have a short Plan and
one Task; larger changes have a wider HLD and multiple parallel single-module
Tasks. A paused Plan can be discussed in a PR, Issue, or team review and resumed
later from the same `plan-and-task.md`. The final check runs only after Task
decomposition is complete.

## Resume

- New chat/tool/session: invoke the role owning the current phase with the
  `work_id` or Issue URL.
- Every role reruns context initialization and reconstructs from artifacts.
- If source, Issue, or scope changed, stop and reconcile before continuing.

## Post-Delivery Knowledge

When requested after completed work, a later role skill loads retrospective,
memory, or release archive references progressively.
