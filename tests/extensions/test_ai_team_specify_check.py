from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "extensions/team/scripts/check_specify_intake.py"


def _module():
    spec = importlib.util.spec_from_file_location("ai_team_specify_check", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_intake(tmp_path: Path, slug: str, *, acceptance: str = "ready") -> None:
    root = tmp_path / ".specify/ai-team/intake" / slug
    root.mkdir(parents=True)
    common = []
    for number in range(1, 10):
        check_id = f"CL-{number:03d}"
        status = acceptance if check_id == "CL-006" else "ready"
        common.append(f"| {check_id} | requirement | {status} | confirmed answer |")
    checklist = f"""---
schema: ai-team-specify-checklist/v1
intake_slug: "{slug}"
work_type: feature
last_updated: "2026-07-15"
---

# Specify Checklist

## Common Readiness
| Check ID | Requirement | Status | Evidence or answer |
|---|---|---|---|
{chr(10).join(common)}

## Feature Or New Project Readiness
| Check ID | Requirement | Status | Evidence or answer |
|---|---|---|---|
| CL-F01 | story | ready | user capability and value |
| CL-F02 | main | ready | main scenario |
| CL-F03 | failure | ready | failure scenario |

## Bugfix Readiness
| Check ID | Requirement | Status | Evidence or answer |
|---|---|---|---|
| CL-B01 | behavior | not-applicable | feature work |
| CL-B02 | reproduction | not-applicable | feature work |
| CL-B03 | impact | not-applicable | feature work |
"""
    (root / "specify-checklist.md").write_text(checklist, encoding="utf-8")
    (root / "issue-draft.md").write_text(
        f"""---
schema: ai-team-issue-draft/v1
intake_slug: "{slug}"
work_type: feature
target_repository: org/project
privacy_boundary: public-safe
publication_status: not-published
proposed_labels: [type/feature, state/draft]
---

# Export selected records

## User And Problem
An operator needs a complete export.

## Goal And Value
Exporting selected records avoids manual transcription.

## User Stories Or Bug Observation
As an operator, I want CSV export, so that I can reuse selected records.

## Scenarios
The operator selects records and receives a CSV file.

## Scope
Export selected visible records.

## Non-Goals
Importing and scheduled exports are excluded.

## Acceptance
AC-001: Given selected records, when export runs, then every record is present.

## Known Unknowns
None.

## Publication
Publish to org/project with type/feature and state/draft.
""",
        encoding="utf-8",
    )


def test_ready_checklist_and_issue_draft_can_be_published(tmp_path: Path) -> None:
    module = _module()
    _write_intake(tmp_path, "csv-export")

    result = module.evaluate(tmp_path, "csv-export")

    assert result == {"result": "ready", "pending": [], "next": None}


def test_checker_returns_the_next_blocking_question(tmp_path: Path) -> None:
    module = _module()
    _write_intake(tmp_path, "csv-export", acceptance="pending")

    result = module.evaluate(tmp_path, "csv-export")

    assert result["result"] == "revise"
    assert result["next"] == "CL-006"
