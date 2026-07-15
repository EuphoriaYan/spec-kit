---
description: "Architect/Module Owner role for producing one source-grounded Plan-and-Task artifact plus its readiness check."
---

# Spec Kit Team Plan And Task

Own the Architect/Module Owner role. Consume accepted documents, not hidden
Business/Product chat. Produce the technical Plan and executable Tasks without
editing product source.

## Bootstrap

1. Run `python .specify/extensions/team/scripts/init_role_context.py`.
2. Read the invariant and Architect/Module Owner sections of
   `.specify/extensions/team/docs/context-bootstrap.md`.
3. Load the accepted Issue and Spec or Bug artifact.
4. Progressively load only the needed internal references:
   - `docs/work-item-layout.md` for the canonical directory and files;
   - `references/internal/context.md` and `permissions.md`;
   - `handoff-spec-sync.md` for confidential URL input;
   - `codegraph.md`, `docs/code-graph-adapters.md`, and `impact.md`.
   Resolve them under `.specify/extensions/team/`. They are internal
   capabilities, not separate user skills.

## Input

```text
$ARGUMENTS
```

## Flow

1. Resolve the canonical category and `work_id` from the arguments, primary
   Issue, or existing `spec.md` path. Stop when the result is missing or
   ambiguous. Never pick the newest directory as a fallback. Open or resume
   that Work Context Package.
2. Fetch an authorized confidential handoff and prefer gitignored
   `spec.override.md` when present.
3. Create the analysis Permission Envelope.
4. Generate or attach a Code Graph slice. Fall back to explicit source
   structure evidence when the adapter is unavailable.
5. Record affected modules, owners, reuse candidates, callers/callees,
   contracts, dependencies, tests, and declared file scope.
6. Read `.specify/<category>/<work_id>/spec.md`. Verify its Issue is already
   `state/accepted` or `state/working`; this decision must exist before the
   skill starts and cannot be granted inside the skill. Create or update
   `plan-and-task.md` in that same directory. It combines architecture Plan,
   change scope, ordered Tasks, minimum self-tests, compatibility, and rollback.
7. For Bugfix work, include root-cause evidence and regression Tasks. For
   Feature/new-project work, map each Task to a User Story and acceptance point.
8. Tasks may include LLD-level files, classes, functions, data flow, migration,
   and tests, but may not invent decisions absent from the Plan.
9. Map every Task to a minimum self-test/evidence ID and acceptance point.
10. Run `python .specify/extensions/team/scripts/check_plan_and_task.py
    --work-type <feature|bugfix> --work-id <work_id>`. The script owns
    `plan-and-task-check.md`; never hand-write a passing result. Revise the Plan
    and Tasks until the deterministic check returns `ready` or a human records
    why a blocking finding remains.

Compact mode may shorten Plan and Tasks but may not omit scope, compatibility,
rollback, or self-test evidence. Escalate to Standard when impact expands.

## Output

```text
Team Plan And Task:
- work item:
- work ID and category:
- planning mode:
- code graph or fallback:
- affected modules and owners:
- declared files:
- architecture and public-contract deltas:
- plan and task: .specify/<feature|bugfix>/<work_id>/plan-and-task.md
- check: .specify/<feature|bugfix>/<work_id>/plan-and-task-check.md
- minimum self-test mapping:
- compatibility and rollback:
- unresolved findings:
- human decision required:
- next step: later role skill / revise / blocked
- result: ready / revise / blocked
```

Stop when Feature acceptance is missing, Bug scope is unconfirmed, ownership or
public-contract authority is unclear, scope exceeds the approved boundary, or
Spec, Plan-and-Task, check, and self-test mappings disagree.
