# Compact Plan And Tasks Extension

Status: planned extension. The bundled workflows still use separate Plan and
Tasks phases until this contract is implemented and tested.

## Purpose

Small, low-risk changes should not pay the full coordination cost of separate
Plan and Tasks review cycles when the technical path is already clear. Compact
planning allows one user action and one combined human review while preserving
the two different meanings:

- Plan records technical decisions, boundaries, risks, and verification intent.
- Tasks record execution order, dependencies, file scope, and completion checks.

Compact planning is not permission to skip impact analysis, role isolation,
human accountability, implementation permissions, or evidence.

## Intended Flow

```text
work item -> context and impact analysis -> human selects compact mode
-> architect context writes Implementation Plan
-> isolated developer context derives Execution Tasks
-> combined plan/task check and one human gate
-> implementation permission gate -> implement -> converge -> evidence
```

The architect and developer phases must not share hidden chat context. They
exchange the approved specification, impact evidence, and the compact artifact.

## Artifact Contract

`plan.md` is the canonical reviewed artifact:

```markdown
# Compact Implementation Plan

## Scope And Assumptions
## Technical Decisions
## Compatibility And Risks
## Verification Strategy

# Execution Tasks

- [ ] T001 ...
- [ ] T002 ...
```

Spec Kit core currently requires `tasks.md` for `speckit.implement` and
`speckit.converge`. A future compact workflow may generate `tasks.md` as a
compatibility projection of `plan.md#execution-tasks`. That projection must be
marked generated, must not be edited independently, and must be regenerated
when it differs from the canonical section.

The Change Package should record:

```yaml
planning_mode: compact
artifacts:
  plan:
    path: specs/<work_slug>/plan.md
    authority: architecture-and-execution
  tasks:
    path: specs/<work_slug>/tasks.md
    authority: generated-projection
    source: specs/<work_slug>/plan.md#execution-tasks
```

## Eligibility

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

Use the standard `Spec -> Plan -> Plan Review -> Tasks -> Tasks Review` path when
any eligibility condition is false or uncertain. In particular, do not select
compact mode solely because the request says "simple CRUD", "one config item",
"small project", or "only two files".

Zero-to-one projects use the standard path by default. A small project may use
compact planning only after its product boundary, architecture skeleton,
dependency policy, ownership, and runnable spine already exist.

If implementation discovers wider impact, stop, set the compact assessment to
invalidated, preserve completed evidence, and resume from the standard Plan
phase. Do not keep patching the compact task list around a changed design.

## Planned Runtime Contract

The future implementation should provide an explicit workflow alias such as
`ai-team-sdd compact path`, not silently infer the shortcut. It should record:

- human selector and selection reason;
- eligibility evidence and source snapshot;
- combined review result;
- canonical artifact and generated projection hash;
- fallback reason when compact mode is invalidated.

Until that workflow exists, users should continue to run the standard AI Team
SDD workflow and may generate Plan and Tasks close together, but must keep the
separate artifacts and review gates.
