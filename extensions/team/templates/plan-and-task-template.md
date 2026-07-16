---
schema: ai-team-plan-and-task/v5
work_id: ""
work_type: feature
primary_issue: ""
issue_status: status/accept
issue_source:
  repository: ""
  issue_number: ""
  updated_at: ""
  body_hash: ""
approval:
  decided_by: ""
  evidence_url: ""
planning_stage: plan-review
plan_review:
  decision: pending
  decided_by: ""
source_revision: ""
declared_paths: []
affected_modules: []
impact_analysis:
  code_graph:
    kind: code-graph
    evidence_path: ""
    source_revision: ""
  cross_module: false
  class_changes: false
  public_contract_change: none
  contract_authority:
    decided_by: not-required
    evidence_url: not-required
---

# Plan And Task

## Plan (HLD)

### Source And Code Graph Evidence

Record the Code Graph slice or explicit source-structure fallback and the
revision it describes.

### Module Change Plan

Identify modules from the repository's actual source layout, build metadata,
architecture guidance, and Code Graph. A named owner or review route is useful
when the repository declares one, but it is not required for Task decomposition.

| Module | Module path | Current responsibility | Planned change | Contract impact | Review route (optional) |
|---|---|---|---|---|---|
| module-name | path/to/module |  |  | none | none |

### Architecture And Contract Impact

Describe the before/after architecture. Explicitly cover API, SPI, config,
schema, event, database ownership, dependency direction, and compatibility.

### Declared Change Scope

Explain why every `declared_paths` entry is needed. Paths used by Tasks must be
declared in the front matter.

### Implementation Plan

Describe the issue-wide solution and how the module changes fit together. This
is the HLD; do not duplicate per-file implementation detail from Tasks.

### Parallel Development Strategy

Tasks are parallel by default. Identify independent work groups, shared
prerequisites, integration points, and how contributors avoid editing the same
files or public contracts concurrently.

### Development Chain

At Plan review, describe module-level sequencing constraints without inventing
Task IDs. After Task decomposition, update this section with the concrete Task
dependency, handoff artifact, serialization reason, and unblock evidence. Use
`None. All Tasks are independent.` when no dependency exists.

### Plan Review Decision

Stop here before Task decomposition. Present the HLD for human discussion and
record one decision in front matter: `continue-to-tasks`,
`pause-for-discussion`, or `revise-plan`. Record the named human in
`plan_review.decided_by`. Any material Plan change returns to this gate.

## Tasks (LLD)

Each Task is one small, independently assignable delivery unit owned by exactly
one module. Do not combine unrelated modules in one Task. Cross-module
integration may be a dedicated Task, but it still needs one coordinating module
and explicit dependencies.

### Task Index

Use `none` in `Depends on` only when the Task has no prerequisite. Tasks in the
same parallel group are intended to be assigned concurrently.

| Task ID | Status | Module | Requirement IDs | Planned paths | Depends on | Parallel group | Self-test IDs | LLD summary |
|---|---|---|---|---|---|---|---|---|
| T001 | [ ] | module-name | VER-001 | path/to/file | none | P1 | TEST-001 |  |

### Task Details

| Task ID | Goal and non-goals | Design and data flow | Inputs and contracts | Completion criteria |
|---|---|---|---|---|
| T001 |  |  |  |  |

### Minimum Self-Tests

| Test ID | Type | Scenario or fixture | Command or procedure | Expected evidence |
|---|---|---|---|---|
| TEST-001 | unit |  |  |  |

### Compatibility Migration And Rollback

State how existing behavior remains compatible. When compatibility changes,
link the responsible architecture or contract authority's approval and give
migration and rollback steps.

### Risks And Deviations

Use `None` when no known deviation exists.

## Feature Delivery Plan

Complete for `work_type: feature`.

### User Story Delivery Mapping

| User Story ID | Verification IDs | Task IDs |
|---|---|---|
| US-001 | VER-001 | T001 |

## Bugfix Delivery Plan

Complete for `work_type: bugfix`.

### Accepted Bug Summary

Summarize observed behavior, expected behavior, environment, impact, and the
accepted Issue discussion without inventing a root cause.

### Bugfix Verification

| Verification ID | Reproduction ID | Expected result |
|---|---|---|
| VER-001 | BUG-OBS-001 |  |

### Root Cause Evidence

Separate observed evidence from the root-cause conclusion.

### Reproduction And Regression Mapping

| Reproduction ID | Root-cause evidence | Task IDs | Regression test IDs |
|---|---|---|---|
| BUG-OBS-001 |  | T001 | TEST-001 |
