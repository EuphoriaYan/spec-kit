from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "extensions" / "team" / "scripts" / "check_plan_and_task.py"


def _module():
    spec = importlib.util.spec_from_file_location("ai_team_plan_check", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _spec(work_id: str, work_type: str, state: str = "accepted") -> str:
    common = f"""---
schema: ai-team-spec/v1
work_id: "{work_id}"
work_type: {work_type}
primary_issue: https://example.com/org/repo/issues/{work_id}
issue_state: {state}
approval:
  decided_by: technical-committee@example.com
  evidence_url: https://example.com/org/repo/issues/{work_id}#accepted
privacy_boundary: public-safe
---

# Specification

## Common Specification

### Problem And Goal
Deliver the requested behavior.

### Acceptance Summary
- AC-001: behavior is observable.

### Scope
One module.

### Non-Goals
No API change.

### Open Questions
None.
"""
    if work_type == "feature":
        return (
            common
            + """

## Feature Specification

### User Stories

#### US-001 [P1] Export
As an operator, I want an export, so that I can reconcile results.

### Feature Acceptance
| Acceptance ID | Given | When | Then |
|---|---|---|---|
| AC-001 | filtered rows | export runs | matching rows are returned |
"""
        )
    return (
        common
        + """

## Bugfix Specification

### Observed Behavior
The export omits one row.

### Expected Behavior
All matching rows are present.

### Reproduction
BUG-OBS-001 reproduces with a two-page result.

### Environment
Supported production profile.

### Impact
One export is incomplete.

### Fix Acceptance
| Acceptance ID | Reproduction ID | Expected result after fix |
|---|---|---|
| AC-001 | BUG-OBS-001 | all rows are present |
"""
    )


def _plan(
    work_id: str,
    work_type: str,
    *,
    mode: str = "standard",
    cross_module: bool = False,
    class_changes: bool = False,
    contract_change: str = "none",
    owner: str = "module-owner@example.com",
    owner_evidence: str = "https://example.com/org/repo/issues/approval",
    compact_owner: str = "not-applicable",
    task_test: str = "TEST-001",
) -> str:
    common = f"""---
schema: ai-team-plan-and-task/v1
work_id: "{work_id}"
work_type: {work_type}
planning_mode: {mode}
source_revision: abc123
declared_paths:
  - src/export.py
  - tests/test_export.py
affected_modules:
  - export
impact_analysis:
  code_graph:
    kind: code-graph
    evidence_path: .specify/{"feature" if work_type == "feature" else "bugfix"}/{work_id}/codegraph/summary.md
    source_revision: abc123
  cross_module: {str(cross_module).lower()}
  class_changes: {str(class_changes).lower()}
  public_contract_change: {contract_change}
  contract_owner_approval:
    decided_by: {owner}
    evidence_url: {owner_evidence}
compact_approved_by: {compact_owner}
---

# Plan And Task

## Common Engineering Plan

### Source And Code Graph Evidence
The export service and its test are the complete affected slice.

### Affected Modules And Owners
The export module owner reviews this change.

### Architecture And Contract Impact
The existing export path is reused and public behavior is compatible.

### Declared Change Scope
Implementation and regression test only.

### Implementation Plan
Adjust selection and verify the result.

### Ordered Tasks
| Task ID | Requirement ID | Planned paths | Self-test IDs | Description |
|---|---|---|---|---|
| T001 | AC-001 | src/export.py | {task_test} | implement the accepted behavior |

### Minimum Self-Tests
| Test ID | Type | Command or procedure | Expected evidence |
|---|---|---|---|
| TEST-001 | unit | pytest tests/test_export.py | passing regression output |

### Compatibility Migration And Rollback
Existing callers remain compatible. Revert src/export.py to roll back.

### Risks And Deviations
None.
"""
    if work_type == "feature":
        return (
            common
            + """

## Feature Delivery Plan

### User Story Delivery Mapping
| User Story ID | Acceptance IDs | Task IDs |
|---|---|---|
| US-001 | AC-001 | T001 |
"""
        )
    return (
        common
        + """

## Bugfix Delivery Plan

### Root Cause Evidence
The page cursor is advanced before the last row is copied.

### Reproduction And Regression Mapping
| Reproduction ID | Root-cause evidence | Task IDs | Regression test IDs |
|---|---|---|---|
| BUG-OBS-001 | cursor trace | T001 | TEST-001 |
"""
    )


def _write_package(tmp_path: Path, work_id: str, work_type: str, **plan_kwargs) -> Path:
    category = "feature" if work_type == "feature" else "bugfix"
    root = tmp_path / ".specify" / category / work_id
    root.mkdir(parents=True)
    graph = root / "codegraph" / "summary.md"
    graph.parent.mkdir()
    graph.write_text("source revision abc123 impact slice\n", encoding="utf-8")
    (root / "spec.md").write_text(_spec(work_id, work_type), encoding="utf-8")
    (root / "plan-and-task.md").write_text(
        _plan(work_id, work_type, **plan_kwargs), encoding="utf-8"
    )
    return root


def test_feature_and_bugfix_packages_can_be_ready(tmp_path: Path) -> None:
    module = _module()
    for work_id, work_type in (("101", "feature"), ("102", "bugfix")):
        _write_package(tmp_path, work_id, work_type)
        result, rendered = module.evaluate(tmp_path, work_type, work_id)
        assert result == "ready", rendered
        assert "| TRACEABILITY | PASS |" in rendered
        assert "| ISSUE_STATE | PASS |" in rendered


def test_check_is_deterministic_and_cli_detects_stale_output(tmp_path: Path) -> None:
    module = _module()
    root = _write_package(tmp_path, "103", "feature")
    first = module.evaluate(tmp_path, "feature", "103")
    second = module.evaluate(tmp_path, "feature", "103")
    assert first == second

    output = root / "plan-and-task-check.md"
    output.write_text(first[1], encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--project-root",
            str(tmp_path),
            "--work-type",
            "feature",
            "--work-id",
            "103",
            "--check",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr

    output.write_text("stale\n", encoding="utf-8")
    stale = subprocess.run(completed.args, capture_output=True, text=True, check=False)
    assert stale.returncode == 2
    assert "stale" in stale.stderr


def test_draft_issue_blocks_planning(tmp_path: Path) -> None:
    module = _module()
    root = _write_package(tmp_path, "104", "feature")
    (root / "spec.md").write_text(
        _spec("104", "feature", state="draft"), encoding="utf-8"
    )
    result, rendered = module.evaluate(tmp_path, "feature", "104")
    assert result == "blocked"
    assert "| ISSUE_STATE | BLOCK |" in rendered


def test_public_contract_and_unsafe_compact_require_human_authority(
    tmp_path: Path,
) -> None:
    module = _module()
    _write_package(
        tmp_path,
        "105",
        "feature",
        mode="compact",
        cross_module=True,
        class_changes=True,
        contract_change="spi",
        owner="pending",
        owner_evidence="pending",
        compact_owner="maintainer@example.com",
    )
    result, rendered = module.evaluate(tmp_path, "feature", "105")
    assert result == "blocked"
    assert "| CONTRACT_AUTHORITY | BLOCK |" in rendered
    assert "| PLANNING_MODE | BLOCK |" in rendered


def test_acceptance_requires_human_decision_reference(tmp_path: Path) -> None:
    module = _module()
    root = _write_package(tmp_path, "107", "feature")
    spec = (root / "spec.md").read_text(encoding="utf-8")
    (root / "spec.md").write_text(
        spec.replace(
            "technical-committee@example.com\n  evidence_url: https://example.com/org/repo/issues/107#accepted",
            "approved\n  evidence_url: pending",
        ),
        encoding="utf-8",
    )

    result, rendered = module.evaluate(tmp_path, "feature", "107")

    assert result == "blocked"
    assert "| ISSUE_APPROVAL_EVIDENCE | BLOCK |" in rendered


def test_code_graph_evidence_must_exist_and_match_revision(tmp_path: Path) -> None:
    module = _module()
    root = _write_package(tmp_path, "108", "bugfix")
    (root / "codegraph" / "summary.md").unlink()

    result, rendered = module.evaluate(tmp_path, "bugfix", "108")

    assert result == "blocked"
    assert "| IMPACT_EVIDENCE | BLOCK |" in rendered


def test_empty_sections_and_incomplete_delivery_mapping_require_revision(
    tmp_path: Path,
) -> None:
    module = _module()
    root = _write_package(tmp_path, "109", "feature")
    plan = (root / "plan-and-task.md").read_text(encoding="utf-8")
    plan = plan.replace(
        "### Implementation Plan\nAdjust selection and verify the result.",
        "### Implementation Plan\n",
    ).replace("| US-001 | AC-001 | T001 |", "| US-999 | AC-001 | T001 |")
    (root / "plan-and-task.md").write_text(plan, encoding="utf-8")

    result, rendered = module.evaluate(tmp_path, "feature", "109")

    assert result == "revise"
    assert "| PLAN_CONTENT | FAIL |" in rendered
    assert "| DELIVERY_MAPPING | FAIL |" in rendered


def test_missing_self_test_mapping_requires_revision(tmp_path: Path) -> None:
    module = _module()
    _write_package(tmp_path, "106", "bugfix", task_test="TEST-404")
    result, rendered = module.evaluate(tmp_path, "bugfix", "106")
    assert result == "revise"
    assert "| TRACEABILITY | FAIL |" in rendered
