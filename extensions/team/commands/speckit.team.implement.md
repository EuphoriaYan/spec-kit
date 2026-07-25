---
description: "Implement task-ready feature work, verify it, run the quality loop, and submit the result."
---

# Team Implement

Implement the selected tasks and produce local verification evidence. After
Phase 5, automatically hand the diff to the isolated Review -> Assess -> Fix
quality loop before offering pull-request submission.

## User Input

```text
$ARGUMENTS
```

Accept:

- `work_id=<id>` identifying `.specify/feature/<work_id>/`, or the accepted
  Feature Issue URL from which the work ID can be derived;
- optional `only=T001-T010` (also accept a comma-separated list of task IDs).

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
   When the local work root is absent because another contributor performed
   planning, fetch the authoritative Issue and its accepted Plan/Task handoff,
   reconstruct only the public-safe local artifacts, create a fresh Context
   Package and implementation Permission Envelope, and rerun the installed
   deterministic checks. Stop if the Issue lacks an unambiguous accepted HLD,
   Task scope, self-tests, permission status, or decision evidence. Never treat
   remembered chat as the handoff.
3. Read `references/context.md` when resuming, then read, when present,
   `work-context.yml`, `context-pack.md`,
   `permission-envelope.yml`, `handoffs/`, and `codegraph/`.
   Read `references/memory-runtime.md` and retrieve guidance for role
   `implement`, work type `feature`, and the selected Tasks' modules. Apply
   binding Knowledge before editing. Advisory Memory may inform reuse and risk
   checks but cannot expand the Plan or Permission Envelope.
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

If a selected Task delivers a tutorial, runbook, deployment guide, or
walkthrough, require its evidence file and `scripts/check_evidence_steps.py`
command in the Task completion criteria.

## Phase 3: Permission

Require `permission-envelope.yml`. Run the installed
`scripts/check_permission_envelope.py` by its resolved path with
`--work-type feature --work-id <work_id> --mode implementation
--require-authorized`. A `ready` envelope is authorized without a human
approval only when it has no current `approval_required` trigger. An
`approved` envelope records the one human decision for the complete selected
Task batch. Stop if the deterministic check is blocked; do not
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
5. For tutorial-like deliverables, run the installed
   `scripts/check_evidence_steps.py` against the completed evidence file. Keep
   missing prerequisites as `BLOCKED` or `NOT_RUN`; never rewrite them as
   success to make the report green.
6. Update the Verification section of `context-pack.md`.

Output `## Verification Report`. Verification passes only when every selected
task is checked, required checks pass, and the diff stays in scope. On success,
update `work-context.yml` to `phase: verified`,
   `last_completed_skill: speckit.team.implement`, and
   `next_skill: speckit.team.review`, preserving all other fields. On failure, do not set `verified`;
report the repair needed and stop without entering the PR phase.

## Phase 6: Automatic Quality Loop

After verification passes, invoke `speckit.team.review` in local-diff mode with
`work_id=<work_id> auto_fix=true`. Do not ask the user to approve this routine
transition. The Reviewer must reconstruct intent from the Issue, effective
Feature spec, accepted Plan, and User Story mappings rather than from hidden
implementation chat.

When Review finds a repairable blocker or major finding within the authorized
repository, module, Plan, and dependency boundary, it automatically hands the
finding and original User Story IDs to `speckit.team.assess`, then
`speckit.team.fix`, and repeats Review. Stop after three correction rounds, on
a repeated root cause, or whenever a human-gate trigger appears. Minor findings
may finish as `GO-WITH-RISK` with the risk listed for the final merge decision.

If the integration cannot chain installed Skills, print the exact next Skill
invocation and mark the quality loop `continuation-required`; this is a tooling
limitation, not a request for design approval.

## Phase 7: Pull Request

After the quality loop reports `GO` or `GO-WITH-RISK`:

- read and execute the installed `references/implement-pr.md` immediately;
- create or update the PR automatically when the host integration is usable;
- for GitCode or another host without a usable API/CLI, output the complete
  title, body, file list, and `## Paste Into PR Description` block;
- treat manual posting as transport, not another design approval.

Do not reproduce, guess, or preload the PR reference before Phase 7.

Do not ask whether to submit a PR. Stop only when submission prerequisites are
unresolved, and report the exact prerequisite without invalidating verified
implementation. Final merge remains a human decision.

## Output Order

Use these sections, omitting later sections after a stop condition:

```text
## Context Summary
## Readiness Report
## Permission Check
## Implementation Progress
## Verification Report
## Automated Quality Loop
## Pull Request
```
