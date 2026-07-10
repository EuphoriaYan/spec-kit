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

Resolve:

- `work_slug`;
- requested `mode=analysis|implementation|verification|submission`;
- repository role and target module;
- active AI integration;
- required read paths, write paths, commands, dependency operations, and
  network destinations;
- requested enforcement mode, if any.

Load:

- `.specify/ai-team/work/<work_slug>/work-context.yml`;
- existing `permission-envelope.yml`;
- repository and AI integration rules.

## Workflow

1. Derive the narrowest access required for the requested mode.
2. Separate read, write, command, dependency, and network capabilities.
3. Deny credential files, private demand leakage, `.git` internals, unrelated
   modules, destructive history changes, and unapproved external writes.
4. Detect only verifiable enforcement:
   - use `agent-native` when native controls are configured and checked;
   - use `wrapper-enforced` when all relevant operations use a verified wrapper;
   - otherwise use `policy-only` and list the enforcement gaps.
5. Write or update
   `.specify/ai-team/work/<work_slug>/permission-envelope.yml`.
6. Update the permission summary in `work-context.yml` and `context-pack.md`.
7. Return the envelope diff and required human approvals. Do not begin the next
   protected phase.

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

- the Work Context Package is missing or identifies another work unit;
- paths are absolute, ambiguous, or broader than the approved module without a
  human decision;
- implementation requests writes before plan/task review;
- public-contract, cross-module, dependency, or network expansion lacks the
  relevant owner approval;
- hard runtime confinement is required but no verified native or wrapper
  enforcement exists;
- the AI agent would have to claim a sandbox it cannot verify.
