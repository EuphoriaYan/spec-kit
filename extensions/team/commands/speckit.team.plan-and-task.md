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

## Input Contract

Users may invoke this skill with a natural-language sentence. `$ARGUMENTS` is
the transport for that sentence, not the complete input model.

```text
$ARGUMENTS
```

### Required To Locate The Work

Provide the primary Issue URL. As a resume convenience, a canonical `work_id`
or `spec.md` path is also accepted only when it resolves to exactly one primary
Issue URL recorded in `spec.md`. The effective input must contain all of:

- one primary Issue URL for the Feature or Bugfix;
- one canonical `.specify/<feature|bugfix>/<work_id>/spec.md`;
- Issue state `accepted` or `working`, with named human decision maker and the
  exact acceptance Issue/comment URL;
- one coding repository, current branch, and source revision.

Stop when the Issue URL is absent, two locators disagree, the Spec is not
accepted, or the selected repository/revision is ambiguous. Do not choose the
newest Issue or work directory as a fallback.

### Required Before Planning Can Finish

The following evidence is mandatory, but the user does not have to supply it
in the opening sentence. Discover or generate it during this skill:

- Feature User Stories and acceptance IDs from the accepted `spec.md`, or
  Bugfix observations, reproduction IDs, and fix acceptance IDs;
- relevant project architecture guidance and module descriptions from source,
  module `README.md` files, architecture docs, ownership files, and build
  metadata;
- a Code Graph slice tied to the exact source revision, or an explicit
  source-structure fallback when no adapter is available;
- affected and adjacent modules, owners, reuse candidates, callers/callees,
  public contracts, dependencies, existing tests, and likely change paths.

The Code Graph and module context are inputs to the final Plan even when this
skill creates them as intermediate evidence.

### Optional User Guidance

The opening request may additionally provide:

- a subset or priority order of User Story, acceptance, or reproduction IDs
  already present in `spec.md`;
- suspected modules, relevant architecture/module-document paths, or an
  existing Code Graph artifact path;
- planning constraints, non-goals, compatibility concerns, or required test
  environments;
- a request to evaluate Compact planning.

Optional guidance never overrides the accepted Spec, source evidence, module
owners, or public contracts. A new or materially changed User Story is not a
planning hint: return to `speckit.team.specify`, revise the Spec and Issue, and
obtain the required acceptance before planning it.

Example minimal request:

```text
Plan the accepted work at https://github.com/acme/project/issues/123.
```

Example request with optional guidance:

```text
Plan https://github.com/acme/project/issues/123 for US-002 first. Inspect the
export and storage modules, reuse .specify/feature/123/codegraph/summary.md if
its source revision still matches, and evaluate whether Compact mode is safe.
```

## Flow

1. Resolve the canonical category and `work_id` from the primary Issue URL. A
   supplied `work_id` or `spec.md` path is only a locator for that same Issue;
   compare every supplied locator and stop on mismatch. Never pick the newest
   directory as a fallback. Open or resume that Work Context Package.
2. Fetch an authorized confidential handoff and prefer gitignored
   `spec.override.md` when present.
3. Create the analysis Permission Envelope.
4. Generate or attach a Code Graph slice. Fall back to explicit source
   structure evidence when the adapter is unavailable. Persist the evidence
   file and record its kind, project-relative path, and exact source revision.
5. Record affected modules, owners, reuse candidates, callers/callees,
   contracts, dependencies, tests, and declared file scope.
6. Read `.specify/<category>/<work_id>/spec.md`. Verify its Issue is already
   `state/accepted` or `state/working`; this decision must exist before the
   skill starts and cannot be granted inside the skill. Require a named human
   decision maker and the exact Issue/comment URL; the local checker validates
   that reference shape but does not claim remote authenticity. Create or update
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
