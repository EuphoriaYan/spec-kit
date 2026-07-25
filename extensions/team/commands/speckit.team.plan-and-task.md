---
description: "Architect role for turning an accepted Issue into a source-grounded Plan, parallel module Tasks, self-tests, and a deterministic readiness check."
---

# Spec Kit Team Plan And Task

Own the Architect role. Prefer an accepted repository Feature Record and its
formal Spec; retain the accepted remote Feature Issue path for compatibility.
Consume durable artifacts, not hidden Business/Product chat. Produce technical
planning artifacts without editing product source.

## Input Contract

Preferred input is `feature_id=<id>`. Legacy input is one primary accepted
Feature Issue URL. Optional input may name User Stories, suspected modules,
architecture documents, Code Graph evidence, constraints, or a request to
pause after the Plan.

```text
$ARGUMENTS
```

In record-backed mode, run
`scripts/check_feature_record.py --feature-id <id> --require-accepted`, resolve
the configured Feature Record and `.specify/<feature_id>/` work root, and read
its parent Requirement Issue plus `spec.md`. Do not require L0/L1 documents:
apply them when present and record `not-present` when absent.

In legacy mode, use an authenticated repository integration or CLI to read the Issue. GitHub
may use a GitHub integration or `gh`; other hosts may use their API, CLI, or an
authenticated browser. For GitCode, read
`references/gitcode-host-contract.md` and run its capability probe. If the
preferred tool is unavailable or fails, try an
available read-only method for that host. Stop when the Issue body, comments,
labels, and stable URL cannot be verified. Do not plan from a title or copied
excerpt alone.

The legacy Issue must have type label `type/feature` and exactly one status
label. Planning may start only at `status/accept` or resume at
`status/working`. In record-backed mode, the parent Requirement Issue must be
readable and the Feature Record must be accepted. If the input is
`type/bugfix`, stop and direct the user to the Bugfix path.

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

1. Resolve the Feature ID/work ID, then create or resume the configuration-
   aware work root (default `.specify/<feature_id>/`, with legacy
   `.specify/feature/<work_id>/` fallback). When resuming an existing work root,
   read `references/context.md`; do not load it for a new work root. For new
   work, create `work-context.yml` and `context-pack.md` as small resume indexes
   after resolving the Issue identity and source revision. Do not copy the full
   Issue, Spec, Plan, or chat history into either file.
2. In record-backed mode, validate and consume the existing `spec.md`; do not
   silently rewrite accepted behavior while planning. In legacy mode, summarize
   the accepted Issue and accepted discussion into `spec.md`. Read
   `references/feature-spec.md` immediately before writing it.
3. When an authorized confidential handoff is in scope, read and execute
   `references/handoff-spec-sync.md`. Otherwise do not load it. Never copy
   private source text into committed public artifacts.
4. Read `references/permission-envelope.md`, then create or update one
   work-item Permission Envelope. Analysis with clear repository-local read
   scope does not require human approval: use `status: ready`, keep
   `approval_required`, `approved_by`, and `approved_at` empty. Run the
   installed `scripts/check_permission_envelope.py` by its resolved path with
   `--work-type feature --work-id <work_id> --mode analysis
   --require-authorized`. Use `pending-review` only when analysis itself would
   cross a repository/privacy boundary or require sensitive network access.
   Stop when the check is blocked; the script validates but never grants a
   risky operation.
5. Read `references/code-graph-contract.md`, then use the required CodeGraph
   CLI or MCP tool and write the smallest graph and impact evidence summary tied
   to the exact source revision. For an existing project, stop when CodeGraph
   is unavailable, uninitialized, incomplete, or stale; do not silently replace
   it with source search.
6. Classify every accepted User Story as `business-software`, `framework`, or
   `external-prerequisite`
   before designing the solution. Record the classification and PR delivery
   boundary in the Plan. Business and framework changes default to linked PRs.
   They may share one PR only when they are in the same repository, form one
   atomic outcome, share release and rollback, remain backward compatible,
   have separate Tasks/tests, and carry named framework-owner decision
   evidence. Cross-repository delivery always uses linked PRs. Missing external
   or framework capability remains `BLOCKED`; never create a scenario-private
   substitute to manufacture completeness.
7. Identify affected and adjacent modules from source layout, build metadata,
   architecture guidance, and the Code Graph. Record module paths,
   responsibilities, contracts, dependencies, existing tests, reuse candidates,
   and likely change paths. Record an owner or review route when the repository
   declares one, but do not block Task decomposition merely because none exists.
   Then read `references/memory-runtime.md` and run its installed retrieval for
   role `plan-and-task`, work type `feature`, and the affected modules. Apply
   binding Knowledge to the HLD and cite advisory Memory only when current
   source and Issue evidence still support it.
8. Read `references/plan-and-task-format.md` immediately before creating or
   updating `plan-and-task.md`. The Plan is Issue-wide HLD: architecture
   before/after, contract impact, declared scope, per-module change,
   sequencing, compatibility, risk, and rollback. Set `planning_stage:
   plan-review` without inventing Tasks.
9. Present the Plan and ask the user to choose one localized option:
   - **继续拆任务（`continue-to-tasks`）**: accept the HLD and enter Task
     decomposition. At this gate, “下一步”, “继续”, or “继续拆 Task” maps to
     this option;
   - **暂停讨论（`pause-for-discussion`）**: preserve the Plan and stop for
     discussion. “先暂停” maps to this option;
   - **修改方案（`revise-plan`）**: stay in planning and revise the named HLD
     part. “修改方案：……” maps to this option.
   Show labels in the user's language, retain each stable internal value in
   parentheses, explain the effect in one sentence, and state that a natural
   phrase is sufficient. The second option means “pause for discussion”; this
   English explanation is not another value the user must type. “下一步” is
   only an alias while this exact gate is
   active; never infer it across an ambiguous phase boundary. Before asking,
   update `work-context.yml` to
   `phase: plan-review`, with this Skill as both the last completed and next
   Skill, and summarize unresolved decisions in `context-pack.md`. Record the
   decision and named human. For pause or revision, set `phase: plan-paused`
   and preserve the next action so another session can resume. A material Plan
   revision invalidates Tasks and returns to this decision.
10. After `continue-to-tasks`, derive LLD-level Tasks. Every Task belongs to one
   module, declares exact paths and completion criteria, and has at least one
   concrete self-verification scenario. Design Tasks for parallel assignment by
   default. When serialization is necessary, describe the dependency, handoff
   artifact, reason, and unblock evidence in the Plan. Reject cycles.
   The Task set must include concrete code, test-case, verification-evidence,
   and architecture-description work. When architecture impact is `none`,
   include a checked no-impact rationale; when an update is required, name the
   exact architecture files and completion criteria. Architecture synchronization
   is part of implementation Definition of Done, not a later documentation pass.
   Declare and assign the standard
   `.specify/<feature_id>/evidence/implementation-report.md` verification
   artifact required by Implement, in addition to any feature-specific
   evidence file. Include every runnable package or module entrypoint needed by
   the self-test commands in the exact declared paths and owning Task.
   In the localized gate, this means “continue to Tasks”; it is an explanation,
   not another value the user must type.
11. Map every Task to User Stories and their Verification behavior.
12. When the accepted Feature delivers a tutorial, runbook, deployment guide,
    or walkthrough, add a Task that instantiates
    `references/evidence-steps-template.yml` and requires the
    installed `scripts/check_evidence_steps.py` to pass. Every tutorial step
    must be deterministic or evaluable and must record exactly one of `PASS`,
    `FAIL`, `BLOCKED`, or `NOT_RUN`; a missing prerequisite is never `PASS`.
    Ordinary code-only Features do not need this additional artifact.
13. Revise the same Permission Envelope to `mode: implementation` for the
    complete Task batch. Use `status: ready` when work stays in one repository
    and one module, follows the approved Plan, preserves public contracts and
    compatibility, and adds no dependency, security, or license decision. Put
    the detected reasons in `approval_required` and use `status:
    pending-review` when work is cross-repository, cross-module, changes a
    public contract, adds a dependency/security/license decision, is
    incompatible, or exceeds the approved Plan. One named human may approve
    the complete batch; never request approval Task by Task.
    In record-backed mode, `allow.write_paths` must include the exact resolved
    repository-relative Feature Record path because Implement must update its
    delivery phase and evidence-backed Definition of Done. Do not authorize
    the whole Feature Record directory, Catalog, or other Feature Records, and
    do not place a parent of the authorized record in `deny.write_paths`.
14. Set `planning_stage: ready-for-check`, update the Context Package to
    `phase: planning-check`, and then run the installed
    `scripts/check_plan_and_task.py` by its resolved path with
    `--work-type feature --work-id <work_id>`. The script owns
    `plan-and-task-check.md`; never hand-write a passing result. Revise until it
    reports `ready` or preserve the blocking findings. Also run
    `scripts/check_permission_envelope.py --work-type feature --work-id
    <work_id> --mode implementation --require-authorized`. On `ready`, update
    `work-context.yml` to `phase: tasks-ready`, set `next_skill` to
    `speckit.team.implement`, and summarize the checked Task groups in
    `context-pack.md`. On failure, set `phase: planning-blocked`, keep
    `next_skill` as `speckit.team.plan-and-task`, and record the unresolved
    check findings.
    In record-backed mode also run
    `scripts/check_feature_record.py --feature-id <id> --require-accepted`
    and update the Feature delivery phase to `tasks-ready` only after both
    checks pass.
15. On `ready`, publish a public-safe Plan/Task handoff to the primary Issue.
    Include the Issue-wide HLD summary, affected modules, public-contract and
    compatibility impact, Task IDs and module/path scope, dependency/parallel
    groups, minimum self-tests, permission status, and unresolved risks. For
    GitHub with authenticated automation, post the comment. For GitCode, use
    the verified-write procedure in `references/gitcode-host-contract.md`; if
    the probe or read-back fails, output the complete Markdown under
    `## Paste Into Issue Discussion`. Never publish private override content.
    This Issue handoff, not the local `.specify/feature/` directory, enables a
    different contributor to reconstruct the accepted work package.

## Output

```text
Team Plan And Task:
- Issue URL, repository, ID, status, and source revision:
- work ID and category (`feature`):
- accepted Issue summary:
- CodeGraph evidence:
- affected modules and paths:
- requirement responsibilities and PR strategy:
- optional owners or review routes:
- architecture and public-contract deltas:
- current step: Plan review
- next options: localized label + stable value + natural-language alias
- recommended next step: one option plus a short reason; never choose it for the user
- Feature Record and parent Requirement Issue:
- plan and task: <resolved-work-root>/plan-and-task.md
- feature spec: <resolved-work-root>/spec.md
- check: <resolved-work-root>/plan-and-task-check.md
- resume index: <resolved-work-root>/work-context.yml
- handoff summary: <resolved-work-root>/context-pack.md
- minimum self-test mapping:
- parallel groups and development chain:
- compatibility and rollback:
- unresolved findings and human decisions:
- Issue handoff: posted / paste-required / blocked
- result: plan-awaiting-decision / plan-paused / ready / revise / blocked
```

Stop when the Issue cannot be read, labels are invalid, status is not accepted
or working, accepted discussion cannot be distinguished from unresolved
discussion, public-contract authority is missing, scope exceeds the accepted
Issue, or the deterministic check remains blocked.
