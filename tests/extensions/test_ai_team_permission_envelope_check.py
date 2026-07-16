import subprocess
import sys
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "extensions" / "team" / "scripts" / "check_permission_envelope.py"


def _write_envelope(
    project: Path,
    *,
    status: str = "approved",
    mode: str = "implementation",
    work_id: str = "123",
) -> Path:
    root = project / ".specify" / "feature" / "123"
    root.mkdir(parents=True)
    document = {
        "schema_version": "1.0",
        "work_id": work_id,
        "mode": mode,
        "status": status,
        "enforcement_mode": "policy-only",
        "integration": "codex",
        "allow": {
            "read_paths": ["src", "tests"],
            "write_paths": ["src/feature.py", "tests/test_feature.py"],
            "commands": ["pytest"],
            "network": ["none"],
        },
        "deny": {
            "read_paths": [".env"],
            "write_paths": [".git"],
            "commands": ["git reset --hard"],
            "network": ["upload-source"],
        },
        "approval_required": ["expand-write-paths"],
        "runtime": {
            "adapter": "",
            "verified": False,
            "gaps": ["policy is not a runtime sandbox"],
        },
        "approved_by": "maintainer" if status == "approved" else "",
        "approved_at": "2026-07-16T10:00:00Z" if status == "approved" else "",
        "updated_at": "2026-07-16T10:00:00Z",
    }
    path = root / "permission-envelope.yml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def _run(project: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--project-root",
            str(project),
            "--work-type",
            "feature",
            "--work-id",
            "123",
            "--mode",
            "implementation",
            *extra,
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_permission_envelope_check_accepts_approved_matching_envelope(
    tmp_path: Path,
) -> None:
    _write_envelope(tmp_path)

    result = _run(tmp_path, "--require-approved")

    assert result.returncode == 0
    assert "Permission Envelope Check: ready" in result.stdout


def test_permission_envelope_check_does_not_treat_pending_as_approved(
    tmp_path: Path,
) -> None:
    _write_envelope(tmp_path, status="pending-review")

    result = _run(tmp_path, "--require-approved")

    assert result.returncode == 1
    assert "status must be approved" in result.stdout


def test_permission_envelope_check_requires_approved_at(tmp_path: Path) -> None:
    path = _write_envelope(tmp_path)
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    document["approved_at"] = ""
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    result = _run(tmp_path, "--require-approved")

    assert result.returncode == 1
    assert "approved_at must be a non-empty ISO 8601 UTC timestamp" in result.stdout


def test_permission_envelope_check_rejects_approval_after_update(
    tmp_path: Path,
) -> None:
    path = _write_envelope(tmp_path)
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    document["approved_at"] = "2026-07-16T11:00:00Z"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    result = _run(tmp_path, "--require-approved")

    assert result.returncode == 1
    assert "updated_at cannot be earlier than approved_at" in result.stdout


def test_permission_envelope_check_requires_utc_approval_time(
    tmp_path: Path,
) -> None:
    path = _write_envelope(tmp_path)
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    document["approved_at"] = "2026-07-16T18:00:00+08:00"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    result = _run(tmp_path, "--require-approved")

    assert result.returncode == 1
    assert "approved_at must use UTC" in result.stdout


@pytest.mark.parametrize("unsafe_path", ["../outside.py", "C:/outside.py", "src/**"])
def test_permission_envelope_check_rejects_unsafe_paths(
    tmp_path: Path, unsafe_path: str
) -> None:
    path = _write_envelope(tmp_path)
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    document["allow"]["write_paths"] = [unsafe_path]
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    result = _run(tmp_path, "--require-approved")

    assert result.returncode == 1
    assert "contains unsafe path" in result.stdout
