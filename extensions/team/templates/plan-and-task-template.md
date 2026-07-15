---
schema: ai-team-plan-and-task/v1
work_id: ""
work_type: feature
planning_mode: standard
source_revision: ""
declared_paths: []
affected_modules: []
impact_analysis:
  code_graph_evidence: ""
  cross_module: false
  class_changes: false
  public_contract_change: none
  contract_owner_approval: not-required
compact_approved_by: not-applicable
---

# Plan And Task

## Common Engineering Plan

### Source And Code Graph Evidence

Record the Code Graph slice or explicit source-structure fallback and the
revision it describes.

### Affected Modules And Owners

### Architecture And Contract Impact

Describe the before/after architecture. Explicitly cover API, SPI, config,
schema, event, database ownership, dependency direction, and compatibility.

### Declared Change Scope

Explain why every `declared_paths` entry is needed. Paths used by Tasks must be
declared in the front matter.

### Implementation Plan

### Ordered Tasks

| Task ID | Requirement ID | Planned paths | Self-test IDs | Description |
|---|---|---|---|---|
| T001 | AC-001 | path/to/file | TEST-001 |  |

### Minimum Self-Tests

| Test ID | Type | Command or procedure | Expected evidence |
|---|---|---|---|
| TEST-001 | unit |  |  |

### Compatibility Migration And Rollback

State how existing behavior remains compatible. When compatibility changes,
link the responsible owner's approval and give migration and rollback steps.

### Risks And Deviations

Use `None` when no known deviation exists.

## Feature Delivery Plan

Complete for `work_type: feature`.

### User Story Delivery Mapping

| User Story ID | Acceptance IDs | Task IDs |
|---|---|---|
| US-001 | AC-001 | T001 |

## Bugfix Delivery Plan

Complete for `work_type: bugfix`.

### Root Cause Evidence

Separate observed evidence from the root-cause conclusion.

### Reproduction And Regression Mapping

| Reproduction ID | Root-cause evidence | Task IDs | Regression test IDs |
|---|---|---|---|
| BUG-OBS-001 |  | T001 | TEST-001 |
