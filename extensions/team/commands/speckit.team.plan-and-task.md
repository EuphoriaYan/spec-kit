---
description: "Architect role for turning an accepted Issue into a source-grounded Plan, parallel module Tasks, self-tests, and a deterministic readiness check."
---

# Spec Kit Team Plan And Task

Own the Architect role. Consume the accepted Issue and its discussion, not
hidden Business/Product chat. Produce technical planning artifacts without
editing product source.

## Input Contract

The required user input is one primary Issue URL. Optional input may name User
Stories, suspected modules, architecture documents, Code Graph evidence,
constraints, or a request to pause after the Plan.

```text
$ARGUMENTS
```

Use an authenticated repository integration or CLI to read the Issue. GitHub
may use a GitHub integration or `gh`; other hosts may use their API, CLI, or an
authenticated browser. If the preferred tool is unavailable or fails, try an
available read-only method for that host. Stop when the Issue body, comments,
labels, and stable URL cannot be verified. Do not plan from a title or copied
excerpt alone.

The Issue must have exactly one type label, `type/feature` or `type/bugfix`, and
exactly one status label. Planning may start only at `status/accept` or resume
at `status/working`.

## Issue Identity And Summary

1. Treat the absolute Issue URL as the global identity.
2. For an Issue in the coding repository, use its numeric Issue ID as
   `work_id`. For an Issue in the configured enhancement repository, use
   `enhancement-<issue-id>` to avoid cross-repository collisions.
3. Read the current Issue body and all relevant discussion. The accepted Issue
   body is primary. Merge a change from comments only when a human decision
   comment clearly accepts it. Exclude rejected alternatives, suggestions, and
   unresolved discussion.
4. Record the Issue repository, number, remote update time, and a normalized
   body hash so later runs can detect stale planning input.
5. Record the named human or governance body and exact Issue/comment URL that
   supports `status/accept`. The skill cannot grant acceptance.

## Flow

1. Resolve category and work ID, then create or resume
   `.specify/<feature|bugfix>/<work_id>/`. When resuming an existing work root,
   read `references/context.md`; do not load it for a new work root.
2. For Feature work, summarize the accepted Issue and accepted discussion into
   `spec.md`. Read `references/feature-spec.md` immediately before writing it.
   For Bugfix work, do not load that reference or create `spec.md`; consume the
   Bugfix intake artifact supplied by its preceding skill when available and
   preserve the Issue observations in the Bugfix section of
   `plan-and-task.md`.
3. When an authorized confidential handoff is in scope, read and execute
   `references/handoff-spec-sync.md`. Otherwise do not load it. Never copy
   private source text into committed public artifacts.
4. Read `references/permission-envelope.md`, then create or update the analysis
   Permission Envelope with `status: pending-review` and empty `approved_by`
   and `approved_at`. Never self-approve it. After a named human approves the
   exact envelope, record `status: approved`, `approved_by`, and `approved_at`.
   Any change to `mode`, `allow`, `deny`, or scope invalidates that approval;
   return to `pending-review` or `blocked` and clear both approval fields. Run
   the installed
   `scripts/check_permission_envelope.py` by its resolved path with
   `--work-type <feature|bugfix> --work-id <work_id> --mode analysis
   --require-approved`. Stop before source or Code Graph analysis when it is
   blocked; the script validates but never grants approval.
5. Read `references/code-graph-contract.md`, then generate or attach the
   smallest Code Graph slice tied to the exact source revision. Read
   `references/code-graph-adapters.md` only when an adapter must be selected or
   its license, installation, or network behavior must be evaluated. Use an
   explicit source-structure fallback when no adapter is available.
6. Identify affected and adjacent modules from source layout, build metadata,
   architecture guidance, and the Code Graph. Record module paths,
   responsibilities, contracts, dependencies, existing tests, reuse candidates,
   and likely change paths. Record an owner or review route when the repository
   declares one, but do not block Task decomposition merely because none exists.
7. Read `references/plan-and-task-format.md` immediately before creating or
   updating `plan-and-task.md`. The Plan is Issue-wide HLD: architecture
   before/after, contract impact, declared scope, per-module change,
   sequencing, compatibility, risk, and rollback. Set `planning_stage:
   plan-review` without inventing Tasks.
8. Present the Plan and ask the user to continue to Tasks, pause for discussion,
   or revise the Plan. Record the decision and named human. A material Plan
   revision invalidates Tasks and returns to this decision.
9. After `continue-to-tasks`, derive LLD-level Tasks. Every Task belongs to one
   module, declares exact paths and completion criteria, and has at least one
   concrete self-verification scenario. Design Tasks for parallel assignment by
   default. When serialization is necessary, describe the dependency, handoff
   artifact, reason, and unblock evidence in the Plan. Reject cycles.
10. For Feature work, map every Task to User Stories and their Verification
    behavior. For Bugfix work, map reproduction and root-cause evidence to
    regression Tasks and self-tests.
11. Set `planning_stage: ready-for-check`, then run the installed
    `scripts/check_plan_and_task.py` by its resolved path with
    `--work-type <feature|bugfix> --work-id <work_id>`. The script owns
    `plan-and-task-check.md`; never hand-write a passing result. Revise until it
    reports `ready` or preserve the blocking findings.

## Output

```text
Team Plan And Task:
- Issue URL, repository, ID, status, and source revision:
- work ID and category:
- accepted Issue summary:
- code graph or fallback:
- affected modules and paths:
- optional owners or review routes:
- architecture and public-contract deltas:
- plan and task: .specify/<feature|bugfix>/<work_id>/plan-and-task.md
- feature spec: .specify/feature/<work_id>/spec.md or not-applicable
- check: .specify/<feature|bugfix>/<work_id>/plan-and-task-check.md
- minimum self-test mapping:
- parallel groups and development chain:
- compatibility and rollback:
- unresolved findings and human decisions:
- result: plan-awaiting-decision / plan-paused / ready / revise / blocked
```

Stop when the Issue cannot be read, labels are invalid, status is not accepted
or working, accepted discussion cannot be distinguished from unresolved
discussion, public-contract authority is missing, scope exceeds the accepted
Issue, or the deterministic check remains blocked.
