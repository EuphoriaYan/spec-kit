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


def _spec(work_id: str, status: str = "accept") -> str:
    return f"""---
schema: ai-team-feature-spec/v1
work_id: "{work_id}"
work_type: feature
primary_issue: https://example.com/org/repo/issues/{work_id}
issue_status: status/{status}
issue_source:
  repository: example.com/org/repo
  issue_number: "{work_id}"
  updated_at: "2026-07-15T10:00:00Z"
  body_hash: sha256:accepted-body
approval:
  decided_by: technical-committee@example.com
  evidence_url: https://example.com/org/repo/issues/{work_id}#accepted
privacy_boundary: public-safe
---

# Feature Specification

## User Stories

### US-001 [P1] Export
As an operator, I want an export, so that I can reconcile results.

- Preconditions: selected rows exist.
- Main scenario: export returns all selected rows.
- Boundary or failure scenario: multi-page results remain complete.
- Verification (`VER-001`): every selected row is present.
"""


def _plan(
    work_id: str,
    work_type: str,
    *,
    stage: str = "ready-for-check",
    plan_decision: str = "continue-to-tasks",
    plan_decider: str = "architect@example.com",
    cross_module: bool = False,
    class_changes: bool = False,
    contract_change: str = "none",
    owner: str = "module-owner@example.com",
    owner_evidence: str = "https://example.com/org/repo/issues/approval",
    task_test: str = "TEST-001",
    task_dependency: str = "none",
    development_chain: str = "None. All Tasks are independent.",
    ownership_source: str = "src/export/README.md",
) -> str:
    common = f"""---
schema: ai-team-plan-and-task/v5
work_id: "{work_id}"
work_type: {work_type}
primary_issue: https://example.com/org/repo/issues/{work_id}
issue_status: status/accept
issue_source:
  repository: example.com/org/repo
  issue_number: "{work_id}"
  updated_at: "2026-07-15T10:00:00Z"
  body_hash: sha256:accepted-body
approval:
  decided_by: technical-committee@example.com
  evidence_url: https://example.com/org/repo/issues/{work_id}#accepted
planning_stage: {stage}
plan_review:
  decision: {plan_decision}
  decided_by: {plan_decider}
source_revision: abc123
declared_paths:
  - src/export.py
  - tests/test_export.py
affected_modules:
  - export
impact_analysis:
  code_graph:
    kind: codegraph
    evidence_path: .specify/{"feature" if work_type == "feature" else "bugfix"}/{work_id}/codegraph/summary.md
    source_revision: abc123
  cross_module: {str(cross_module).lower()}
  class_changes: {str(class_changes).lower()}
  public_contract_change: {contract_change}
  contract_authority:
    decided_by: {owner}
    evidence_url: {owner_evidence}
---

# Plan And Task

## Plan (HLD)

### Source And Code Graph Evidence
The export service and its test are the complete affected slice.

### Module Change Plan
| Module | Module path | Current responsibility | Planned change | Contract impact | Review route (optional) |
|---|---|---|---|---|---|
| export | {ownership_source} | export result production | preserve all result rows | none | none |

### Architecture And Contract Impact
The existing export path is reused and public behavior is compatible.

### Declared Change Scope
Implementation and regression test only.

### Implementation Plan
Adjust selection and verify the result.

### Parallel Development Strategy
T001 is independently assignable in parallel group P1.

### Development Chain
{development_chain}

### Plan Review Decision
The architect approved immediate Task decomposition.

## Tasks (LLD)

### Task Index
| Task ID | Status | Module | Requirement IDs | Planned paths | Depends on | Parallel group | Self-test IDs | LLD summary |
|---|---|---|---|---|---|---|---|---|
| T001 | [ ] | export | VER-001 | src/export.py | {task_dependency} | P1 | {task_test} | preserve every selected result row |

### Task Details
| Task ID | Goal and non-goals | Design and data flow | Inputs and contracts | Completion criteria |
|---|---|---|---|---|
| T001 | include all rows; no format change | advance the cursor after copying | existing export result contract | regression test passes |

### Minimum Self-Tests
| Test ID | Type | Scenario or fixture | Command or procedure | Expected evidence |
|---|---|---|---|---|
| TEST-001 | unit | multi-page export fixture | pytest tests/test_export.py | passing regression output |

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
| User Story ID | Verification IDs | Task IDs |
|---|---|---|
| US-001 | VER-001 | T001 |
"""
        )
    return (
        common
        + """

## Bugfix Delivery Plan

### Accepted Bug Summary
The export omits one row in a supported production profile.

### Bugfix Verification
| Verification ID | Reproduction ID | Expected result |
|---|---|---|
| VER-001 | BUG-OBS-001 | all rows are present |

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
    if work_type == "feature":
        (root / "spec.md").write_text(_spec(work_id), encoding="utf-8")
    (root / "plan-and-task.md").write_text(
        _plan(work_id, work_type, **plan_kwargs), encoding="utf-8"
    )
    return root


def _add_parallel_report_task(tmp_path: Path, root: Path) -> None:
    plan_path = root / "plan-and-task.md"
    plan = plan_path.read_text(encoding="utf-8")
    plan = plan.replace(
        "  - src/export.py\n  - tests/test_export.py\n",
        "  - src/export.py\n  - src/report.py\n  - tests/test_export.py\n",
    ).replace(
        "affected_modules:\n  - export\n",
        "affected_modules:\n  - export\n  - report\n",
    ).replace(
        "| export | src/export/README.md | export result production | preserve all result rows | none | none |",
        "| export | src/export/README.md | export result production | preserve all result rows | none | none |\n"
        "| report | src/report | report rendering | add export summary | none | none |",
    ).replace(
        "| T001 | [ ] | export | VER-001 | src/export.py | none | P1 | TEST-001 | preserve every selected result row |",
        "| T001 | [ ] | export | VER-001 | src/export.py | none | P1 | TEST-001 | preserve every selected result row |\n"
        "| T002 | [ ] | report | VER-001 | src/report.py | none | P1 | TEST-002 | render the export summary |",
    ).replace(
        "| T001 | include all rows; no format change | advance the cursor after copying | existing export result contract | regression test passes |",
        "| T001 | include all rows; no format change | advance the cursor after copying | existing export result contract | regression test passes |\n"
        "| T002 | render summary; no export mutation | consume export result | existing export result contract | report self-test passes |",
    ).replace(
        "| TEST-001 | unit | multi-page export fixture | pytest tests/test_export.py | passing regression output |",
        "| TEST-001 | unit | multi-page export fixture | pytest tests/test_export.py | passing regression output |\n"
        "| TEST-002 | unit | export result fixture | pytest tests/test_report.py | passing report output |",
    ).replace("| US-001 | VER-001 | T001 |", "| US-001 | VER-001 | T001, T002 |")
    plan_path.write_text(plan, encoding="utf-8")


def test_feature_and_bugfix_packages_can_be_ready(tmp_path: Path) -> None:
    module = _module()
    for work_id, work_type in (("101", "feature"), ("102", "bugfix")):
        _write_package(tmp_path, work_id, work_type)
        result, rendered = module.evaluate(tmp_path, work_type, work_id)
        assert result == "ready", rendered
        assert "| TRACEABILITY | PASS |" in rendered
        assert "| ISSUE_STATE | PASS |" in rendered


def test_independent_module_tasks_can_share_a_parallel_group(tmp_path: Path) -> None:
    module = _module()
    root = _write_package(tmp_path, "113", "feature")
    _add_parallel_report_task(tmp_path, root)

    result, rendered = module.evaluate(tmp_path, "feature", "113")

    assert result == "ready", rendered
    assert "| MODULE_SCOPE | PASS |" in rendered
    assert "| TASK_DEPENDENCIES | PASS |" in rendered
    assert "| PARALLEL_SCOPE | PASS |" in rendered


def test_parallel_tasks_cannot_claim_the_same_path(tmp_path: Path) -> None:
    module = _module()
    root = _write_package(tmp_path, "114", "feature")
    _add_parallel_report_task(tmp_path, root)
    plan_path = root / "plan-and-task.md"
    plan = plan_path.read_text(encoding="utf-8").replace(
        "| T002 | [ ] | report | VER-001 | src/report.py |",
        "| T002 | [ ] | report | VER-001 | src/export.py |",
    )
    plan_path.write_text(plan, encoding="utf-8")

    result, rendered = module.evaluate(tmp_path, "feature", "114")

    assert result == "revise"
    assert "| PARALLEL_SCOPE | FAIL |" in rendered


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
    plan = (root / "plan-and-task.md").read_text(encoding="utf-8")
    (root / "plan-and-task.md").write_text(
        plan.replace("issue_status: status/accept", "issue_status: status/new-issue"),
        encoding="utf-8",
    )
    result, rendered = module.evaluate(tmp_path, "feature", "104")
    assert result == "blocked"
    assert "| ISSUE_STATE | BLOCK |" in rendered


def test_public_contract_requires_human_authority(
    tmp_path: Path,
) -> None:
    module = _module()
    _write_package(
        tmp_path,
        "105",
        "feature",
        cross_module=True,
        class_changes=True,
        contract_change="spi",
        owner="pending",
        owner_evidence="pending",
    )
    result, rendered = module.evaluate(tmp_path, "feature", "105")
    assert result == "blocked"
    assert "| CONTRACT_AUTHORITY | BLOCK |" in rendered


def test_final_check_blocks_until_human_continues_to_tasks(tmp_path: Path) -> None:
    module = _module()
    _write_package(
        tmp_path,
        "115",
        "feature",
        stage="plan-review",
        plan_decision="pause-for-discussion",
    )

    result, rendered = module.evaluate(tmp_path, "feature", "115")

    assert result == "blocked"
    assert "| PLAN_TASK_HANDOFF | BLOCK |" in rendered


def test_acceptance_requires_human_decision_reference(tmp_path: Path) -> None:
    module = _module()
    root = _write_package(tmp_path, "107", "feature")
    plan = (root / "plan-and-task.md").read_text(encoding="utf-8")
    (root / "plan-and-task.md").write_text(
        plan.replace(
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


def test_source_fallback_is_not_valid_codegraph_evidence(tmp_path: Path) -> None:
    module = _module()
    root = _write_package(tmp_path, "118", "feature")
    plan_path = root / "plan-and-task.md"
    plan = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(
        plan.replace("kind: codegraph", "kind: source-fallback"),
        encoding="utf-8",
    )

    result, rendered = module.evaluate(tmp_path, "feature", "118")

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
    ).replace("| US-001 | VER-001 | T001 |", "| US-999 | VER-001 | T001 |")
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


def test_unsafe_module_path_blocks_planning(tmp_path: Path) -> None:
    module = _module()
    _write_package(
        tmp_path,
        "110",
        "feature",
        ownership_source="../outside",
    )

    result, rendered = module.evaluate(tmp_path, "feature", "110")

    assert result == "blocked"
    assert "| MODULE_SCOPE | BLOCK |" in rendered


def test_cyclic_task_dependency_requires_revision(tmp_path: Path) -> None:
    module = _module()
    _write_package(
        tmp_path,
        "111",
        "feature",
        task_dependency="T001",
        development_chain="T001 waits for T001.",
    )

    result, rendered = module.evaluate(tmp_path, "feature", "111")

    assert result == "revise"
    assert "| TASK_DEPENDENCIES | FAIL |" in rendered


def test_task_without_a_self_test_requires_revision(tmp_path: Path) -> None:
    module = _module()
    _write_package(tmp_path, "112", "feature", task_test="none")

    result, rendered = module.evaluate(tmp_path, "feature", "112")

    assert result == "revise"
    assert "| TRACEABILITY | FAIL |" in rendered
