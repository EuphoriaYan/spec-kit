# Compact Plan And Tasks Mode

Status: supported by `speckit.team.plan-and-task` when a human explicitly
selects Compact mode after impact analysis.

## Purpose

Small, low-risk changes should not pay the full coordination cost of separate
Plan and Tasks review cycles when the technical path is already clear. Compact
planning allows one user action and one combined human review while preserving
the two different meanings:

- Plan records technical decisions, boundaries, risks, and verification intent.
- Tasks record a single module's LLD, dependencies, file scope, and completion
  checks.

Compact planning is not permission to skip impact analysis, role isolation,
human accountability, implementation permissions, or evidence.

## Intended Flow

```text
work item -> context and impact analysis -> human selects compact mode
-> architect context writes Implementation Plan
-> the same isolated architecture role derives Execution Tasks
-> combined plan/task check and one human gate
-> implementation permission gate -> implement -> converge -> evidence
```

The Plan-and-Task role must not inherit hidden Business/Product chat context.
It reads the accepted Issue, Spec, impact evidence, and repository architecture
instead.

## Artifact Contract

Compact mode keeps native Spec Kit artifacts so core commands and resume remain
compatible:

```markdown
# plan-and-task.md

## Scope And Assumptions
## Expected Architecture Impact
## Technical Decisions
## Compatibility And Risks
## Verification Strategy

# Tasks (LLD, inside plan-and-task.md)

- T001: one module, declared paths, no dependency, one self-test
```

`plan-and-task.md` owns both technical decisions and execution Tasks. Compact
mode combines their authoring and review, not their meanings. Record
`planning_mode=compact`, the human selection, and the eligibility result in
`plan-and-task.md` and `plan-and-task-check.md`. No additional change manifest
is required.

## Eligibility

If the user starts with one sentence and no issue, run the Plain-Language
Intake first. Intake may recommend Compact from read-only impact evidence, but
formal Compact SDD starts only after the issue draft and mode are approved and
the issue URL exists. Feature acceptance remains a Technical Committee or
delegated human decision.

AI may recommend compact planning, but an accountable human must select it
after impact analysis. All of the following must be true:

- requirement and expected behavior are clear;
- implementation path has no unresolved technical alternatives;
- change radius is local or within one module;
- source or code graph evidence identifies the affected path and reuse point;
- failure cost is low and rollback is simple;
- no public API, SPI, schema, event, or compatibility promise changes;
- no database migration or state ownership change;
- no authentication, authorization, security, privacy, or sensitive-data rule
  changes;
- no new critical dependency or dependency-direction change;
- no cross-module coordination or parallel multi-agent implementation;
- no special deployment, gray release, migration, or operational rollback plan;
- the combined artifact can remain short, ordered, and independently verifiable.

File count is only a warning signal. A one-file SPI change can be high risk, and
a five-file local test refactor can still be compact.

## Mandatory Fallback

Use the standard `Feature Issue + Spec -> Acceptance -> Plan + Tasks -> Unified Review` path when
any eligibility condition is false or uncertain. In particular, do not select
compact mode solely because the request says "simple CRUD", "one config item",
"small project", or "only two files".

Zero-to-one projects use the Standard path. Compact mode is for changes to an
existing architecture whose boundary and runnable spine already exist.

If implementation discovers wider impact, stop, set the compact assessment to
invalidated, preserve completed evidence, and resume from the standard Plan
phase. Do not keep patching the compact task list around a changed design.

## Runtime And Chat Entry

Users do not need a command-line parameter. They can request Compact mode in
the same chat sentence:

```text
Use AI Team Compact planning for this accepted Issue: <issue URL>.
```

An Issue is optional in the first chat turn:

```text
Add CSV export whose columns match the visible result list. If impact analysis
shows that the change is local and low risk, recommend Compact planning.
```

The AI tool starts `speckit.team.specify` when no Issue exists. After the Issue
is accepted, the user starts `speckit.team.plan-and-task`; that skill performs
impact analysis and asks a human to confirm Compact eligibility. It presents one
combined Plan/Tasks review and falls back to Standard mode when Compact is
invalid.
