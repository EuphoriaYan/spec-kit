from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
TEAM = REPO_ROOT / "extensions" / "team"


def _run(script: str, project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(TEAM / "scripts" / script),
            "--project-root",
            str(project),
            *args,
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def test_first_confirmation_to_accepted_feature_sdd_entry(tmp_path: Path) -> None:
    config = tmp_path / ".specify" / "team" / "ai-team-config.yml"
    config.parent.mkdir(parents=True)
    shutil.copyfile(TEAM / "config-template.yml", config)

    blocked = _run(
        "check_feature_record.py",
        tmp_path,
        "--feature-id",
        "FEAT-001",
        "--require-accepted",
    )
    assert blocked.returncode == 2
    assert "ask the user once" in blocked.stdout

    confirmed = _run(
        "configure_feature_tracking.py",
        tmp_path,
        "--root",
        "docs/features",
        "--decided-by",
        "repository-owner",
        "--decided-at",
        "2026-07-25T00:00:00Z",
    )
    assert confirmed.returncode == 0, confirmed.stderr

    feature_root = tmp_path / "docs" / "features"
    feature_root.mkdir(parents=True)
    record_path = feature_root / "FEAT-001.md"
    record = {
        "schema": "speckit-feature-record/v1",
        "feature_id": "FEAT-001",
        "title": "Repository Feature lifecycle",
        "parent_requirement": "https://example.test/issues/25",
        "acceptance": {
            "status": "accepted",
            "decided_by": "architecture-group",
            "decided_at": "2026-07-25T00:10:00Z",
        },
        "delivery": {
            "phase": "backlog",
            "pull_request": "",
            "merged_commit": "",
        },
        "architecture_impact": {
            "level": "none",
            "update_required": False,
            "reason": "No established L0/L1 files exist and no boundary changes are proposed.",
            "affected_files": [],
        },
        "definition_of_done": {
            "code_complete": False,
            "tests_complete": False,
            "evidence_complete": False,
            "architecture_synchronized": False,
            "review_passed": False,
        },
    }
    record_path.write_text(
        f"---\n{yaml.safe_dump(record, sort_keys=False)}---\n\n# Feature\n",
        encoding="utf-8",
    )
    (feature_root / "feature-catalog.yml").write_text(
        yaml.safe_dump(
            {
                "schema": "speckit-feature-catalog/v1",
                "parent_requirement": "https://example.test/issues/25",
                "features": [
                    {
                        "id": "FEAT-001",
                        "title": record["title"],
                        "record": "docs/features/FEAT-001.md",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    ready = _run(
        "check_feature_record.py",
        tmp_path,
        "--feature-id",
        "FEAT-001",
        "--require-accepted",
    )
    assert ready.returncode == 0, ready.stdout
    payload = json.loads(ready.stdout)
    assert payload["status"] == "ready"
    assert payload["feature_record"].endswith("docs/features/FEAT-001.md")
    assert payload["work_root"].endswith(".specify/FEAT-001")

