---
description: "Create or verify the task-scoped Permission Envelope and report its real enforcement level."
---

# AI Team Permissions

Create, revise, or verify the Permission Envelope for one AI Team work unit.
This command does not grant permissions and does not replace human approval.

## User Input

```text
$ARGUMENTS
```

## Required Inputs

Resolve either a formal work scope or an Intake scope:

- formal `work_id`, or `intake_mode=true` plus `intake_slug`;
- requested `mode=analysis|implementation|verification|submission`;
- repository role and target module;
- active AI integration;
- required read paths, write paths, commands, dependency operations, and
  network destinations;
- requested enforcement mode, if any.

Load exactly one context root:

- formal: `.specify/<category>/<work_id>/work-context.yml` and its
  `permission-envelope.yml`;
- Intake: `.specify/ai-team/intake/<intake_slug>/intake.yml` and its
  `permission-envelope.yml`;
- repository and AI integration rules.

For `mode=implementation`, also resolve and read the authoritative
`.specify/<category>/<work_id>/plan-and-task.md` and
`plan-and-task-check.md`. Do not trust a stale context cache when the current
artifact exists. A recorded human approval of the Plan and Tasks is review
evidence; it does not grant broader runtime access.

## Procedure

1. Derive the narrowest access required for the requested mode.
2. Separate read, write, command, dependency, and network capabilities.
3. Deny credential files, private demand leakage, `.git` internals, unrelated
   modules, destructive history changes, and unapproved external writes.
4. Detect only verifiable enforcement:
   - use `agent-native` when native controls are configured and checked;
   - use `wrapper-enforced` when all relevant operations use a verified wrapper;
   - otherwise use `policy-only` and list the enforcement gaps.
5. Write or update the envelope under the selected formal or Intake root.
6. For formal work, update `work-context.yml` and `context-pack.md`. For Intake,
   update only `intake.yml`; do not create formal context files.
7. Return the envelope diff and required human approvals. Do not begin the next
   protected phase.

For implementation mode, write this machine-readable contract:

- `status: pending-review` only when native `plan-and-task.md` exists, required earlier
  plan/task gates are approved, and every intended write path is present in
  `allow.write_paths`;
- `status: blocked` otherwise, with concrete `blockers`;
- `requested_implementation_access.intended_write_paths` must be non-empty;
- update `work-context.yml` so `artifacts.tasks` points to the native file when
  it exists, but do not mark the work implementing before permission approval.

After human approval, the later role skill or its configured enforcement adapter
may change `pending-review` to `approved`. Never infer approval from chat alone.

## Output Shape

```text
AI Team Permission Check:
- work slug:
- requested mode:
- enforcement mode:
- allowed reads:
- allowed writes:
- allowed commands:
- allowed network:
- denied or unrequested capabilities:
- approval required:
- runtime adapter:
- verification evidence:
- enforcement gaps:
- recommendation: approve / revise / block
```

## Stop Conditions

Stop and recommend `block` when:

- the selected formal Work Context or Intake artifact is missing or identifies
  another unit;
- paths are absolute, ambiguous, or broader than the approved module without a
  human decision;
- implementation requests writes before plan/task review;
- public-contract, cross-module, dependency, or network expansion lacks the
  relevant owner approval;
- hard runtime confinement is required but no verified native or wrapper
  enforcement exists;
- the AI agent would have to claim a sandbox it cannot verify.
