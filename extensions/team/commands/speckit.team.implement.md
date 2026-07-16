---
description: "Implement task-ready feature work, verify it, and optionally submit a pull request."
---

# Team Implement

Implement the selected tasks and produce durable verification evidence. A pull
request is optional; implementation is complete when Phase 5 passes.

## User Input

```text
$ARGUMENTS
```

Accept:

- required `work_id=<id>` identifying `.specify/feature/<work_id>/`;
- optional `only=T001-T010` (also accept a comma-separated list of task IDs);
- optional `submit_pr=true`.

Reject an unsafe work ID containing path separators, `..`, or anything other than
letters, numbers, dots, underscores, and hyphens. Set:

```text
FEATURE_ROOT={repository root}/.specify/feature/{work_id}
```

All feature artifact reads and writes MUST stay under `FEATURE_ROOT`. Do not
modify workflow files.

## Phase 1: Context

1. Resolve the repository root and `FEATURE_ROOT` as absolute paths.
2. Require regular files `spec.md` (or `spec.override.md`),
   `plan-and-task.md`, and `plan-and-task-check.md`. Prefer `spec.override.md`
   over `spec.md` when both exist, but do not copy override content into
   tracked source or reports.
3. Read `references/context.md` when resuming, then read, when present,
   `work-context.yml`, `context-pack.md`,
   `permission-envelope.yml`, `handoffs/`, and `codegraph/`.
4. Create or minimally update `work-context.yml` with `work_id`, the
   relative `feature_root`, artifact names, `phase: implementing`, and an ISO
   8601 UTC `updated_at`. Preserve unrelated and unknown fields.
5. Output `## Context Summary`, including the resolved work ID and selected
   task range.

If required artifacts are missing, report them and stop without changing
source code.

## Phase 2: Readiness

Perform a read-only consistency review before implementation:

- the Plan section identifies the technology, architecture, affected files or modules,
  test approach, and important risks;
- every selected task has an ID, an actionable outcome, sufficient file or
  module context, and an order compatible with its dependencies;
- the effective spec and the Plan and Tasks sections describe the same behavior and scope;
- `plan-and-task-check.md` reports a current passing readiness result;
- selected tasks are not already complete and `only=` names existing tasks;
- no unresolved placeholder, contradiction, or missing decision prevents safe
  implementation.

Output exactly one `## Readiness Report` with work ID/root, `PASS` or
`BLOCKED`, and categorized Plan issues, Tasks issues, and Cross-artifact gaps.
Use `[blocker]`, `[major]`, or `[minor]` severity.

If any blocker exists, immediately stop. Do not perform Phases 3-6 and do not
ask whether implementation should continue. End with:

```text
Readiness blocked. Do not proceed with implementation.
Revise artifacts with:
  /speckit.team.plan-and-task work_id={work_id}

Then re-run:
  /speckit.team.implement work_id={work_id}
```

For a passing review, update only the Readiness section of `context-pack.md`;
do not edit the specification or the Plan section.

## Phase 3: Permission

Require `permission-envelope.yml`. Run the installed
`scripts/check_permission_envelope.py` by its resolved path with
`--work-type feature --work-id <work_id> --mode implementation
--require-approved`. Stop if the deterministic check is blocked; do not
hand-wave or replace its result. The check verifies the approval identity and
timestamps as well as the envelope structure.

Then compare the selected Tasks and intended operations with the validated
envelope and confirm that it:

- authorizes implementation rather than analysis-only work;
- is ready/approved rather than blocked, expired, or pending review;
- covers every intended source, test, artifact, command, dependency, and
  network operation;
- identifies the enforcement mode and any gaps.

Output `## Permission Check` with status, enforcement mode, allowed operations,
and gaps. Stop before source changes when the envelope is missing, ambiguous,
stale, blocked, or does not cover the intended work. Never widen or self-approve
the envelope. Metadata such as the check timestamp may be refreshed, but its
authorization fields must not be changed.

## Phase 4: Execute

Read the complete task list, then implement only the selected incomplete tasks:

1. Respect task order, dependencies, test-first instructions, and repository
   conventions.
2. Make the smallest coherent code and test changes allowed by the envelope.
3. Never edit `spec.md`, `spec.override.md`, or the Plan section of
   `plan-and-task.md`.
4. In the Task Index of `plan-and-task.md`, change only the selected task
   Status checkboxes from `[ ]` to `[x]`, and only after that task is actually
   complete. Preserve all other content.
5. Stop on a failed sequential task. Independent tasks may continue only when
   doing so cannot hide or compound the failure.

Output `## Implementation Progress` mapping each selected task ID to its result
and changed files.

## Phase 5: Verify

1. Inspect the repository diff and confirm it matches the selected Tasks, Plan
   scope, and permission envelope.
2. Run the most relevant targeted tests, then the build, lint, type, integration,
   or broader test commands required by the plan and repository guidance.
3. Treat skipped checks as explicit residual risk. Do not report a skipped or
   failing required check as success.
4. Write `evidence/implementation-report.md` with scope, completed task IDs,
   changed files, commands and exit results, skipped checks, failures, and
   residual risks.
5. Update the Verification section of `context-pack.md`.

Output `## Verification Report`. Verification passes only when every selected
task is checked, required checks pass, and the diff stays in scope. On success,
update `work-context.yml` to `phase: verified`,
`last_completed_skill: speckit.team.implement`, and an appropriate
`next_skill`, preserving all other fields. On failure, do not set `verified`;
report the repair needed and stop without entering the PR phase.

## Optional Phase 6

After verification passes:

- when `submit_pr=true`, continue immediately;
- otherwise ask only:

  ```text
  Implementation and verification complete.

  Submit a pull request for this feature? (yes/no)
  ```

- continue only after an explicit yes. A no or absent confirmation ends with
  `phase: verified`.

When continuing, read and execute the installed
`references/implement-pr.md`. Do not reproduce, guess, or preload its
instructions before confirmation.

## Output Order

Use these sections, omitting later sections after a stop condition and omitting
Pull Request unless Phase 6 runs:

```text
## Context Summary
## Readiness Report
## Permission Check
## Implementation Progress
## Verification Report
## Pull Request
```
