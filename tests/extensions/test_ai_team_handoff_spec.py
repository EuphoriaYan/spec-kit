"""Tests for internal Team handoff spec synchronization."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from tests.conftest import requires_bash

REPO_ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ROOT = REPO_ROOT / "extensions" / "team"
SYNC_SH = EXTENSION_ROOT / "scripts" / "bash" / "sync-handoff-spec.sh"


def _install_handoff_repo(repo: Path, category: str = "feature", work_id: str = "001-test") -> Path:
    repo.mkdir(parents=True, exist_ok=True)
    ext_scripts = repo / ".specify" / "extensions" / "team" / "scripts" / "bash"
    ext_scripts.mkdir(parents=True, exist_ok=True)
    for name in (
        "handoff-spec-common.sh",
        "sync-handoff-spec.sh",
    ):
        shutil.copy(EXTENSION_ROOT / "scripts" / "bash" / name, ext_scripts / name)
    feat = repo / ".specify" / category / work_id
    feat.mkdir(parents=True, exist_ok=True)
    return feat


def _run_sync(repo: Path, env: dict, *args: str) -> subprocess.CompletedProcess[str]:
    sync_sh = repo / ".specify" / "extensions" / "team" / "scripts" / "bash" / "sync-handoff-spec.sh"
    clean = {k: v for k, v in os.environ.items() if not k.startswith("SPECIFY_")}
    clean.update(env)
    command_args = list(args) or ["work_type=feature", "work_id=001-test"]
    return subprocess.run(
        ["bash", str(sync_sh), "--json", *command_args],
        cwd=repo,
        env=clean,
        capture_output=True,
        text=True,
        check=False,
    )


def test_team_plan_skill_loads_internal_handoff_capability():
    manifest = yaml.safe_load(
        (EXTENSION_ROOT / "extension.yml").read_text(encoding="utf-8")
    )
    assert "hooks" not in manifest
    plan_task = (
        EXTENSION_ROOT / "commands" / "speckit.team.plan-and-task.md"
    ).read_text(encoding="utf-8")
    assert "handoff-spec-sync.md" in plan_task
    assert "confidential handoff" in plan_task
    plan_command = next(
        item
        for item in manifest["provides"]["commands"]
        if item["name"] == "speckit.team.plan-and-task"
    )
    assert any(
        item["target"] == "references/handoff-spec-sync.md"
        for item in plan_command["resources"]
    )


@requires_bash
def test_sync_skipped_without_url(tmp_path: Path):
    repo = tmp_path / "proj"
    _install_handoff_repo(repo)
    result = _run_sync(repo, {})
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["SKIPPED"] is True


@requires_bash
def test_sync_bootstraps_spec_and_writes_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = tmp_path / "proj"
    feat = _install_handoff_repo(repo)
    fetched = "# Remote Requirement\n\nUser story P1: bootstrap from URL\n"
    fetch_src = tmp_path / "remote.md"
    fetch_src.write_text(fetched, encoding="utf-8")

    fake_curl = tmp_path / "curl"
    fake_curl.write_text(
        "#!/usr/bin/env bash\n"
        'cp "$MOCK_FETCH_SOURCE" "${!#}"\n',
        encoding="utf-8",
    )
    fake_curl.chmod(0o755)

    env = {
        "PATH": f"{tmp_path}:{os.environ.get('PATH', '')}",
        "HANDOFF_REQUIREMENT_URL": "https://example.com/requirements/remote.md",
        "MOCK_FETCH_SOURCE": str(fetch_src),
    }
    result = _run_sync(repo, env)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["SKIPPED"] is False
    assert data["SPEC_BOOTSTRAPPED"] is True
    assert (feat / "spec.md").exists()
    assert "handoff_requirement_url:" in (feat / "spec.md").read_text(encoding="utf-8")
    override = feat / "spec.override.md"
    assert override.exists()
    override_text = override.read_text(encoding="utf-8")
    assert "Remote Requirement" in override_text
    assert "https://example.com/requirements/remote.md" in override_text
    assert data["WORK_DIR"].endswith(".specify/feature/001-test")
    assert data["SPEC"].endswith(".specify/feature/001-test/spec.md")
    assert data["EFFECTIVE_SPEC"].endswith("spec.override.md")
    gitignore = (repo / ".gitignore").read_text(encoding="utf-8")
    assert "**/spec.override.md" in gitignore


@requires_bash
def test_sync_merges_existing_spec_baseline(tmp_path: Path):
    repo = tmp_path / "proj"
    feat = _install_handoff_repo(repo)
    (feat / "spec.md").write_text("# Public baseline\n\nP1 local spec\n", encoding="utf-8")
    fetched = "# Remote Requirement\n\nP1 remote spec\n"
    fetch_src = tmp_path / "remote.md"
    fetch_src.write_text(fetched, encoding="utf-8")

    fake_curl = tmp_path / "curl"
    fake_curl.write_text(
        "#!/usr/bin/env bash\n"
        'cp "$MOCK_FETCH_SOURCE" "${!#}"\n',
        encoding="utf-8",
    )
    fake_curl.chmod(0o755)

    env = {
        "PATH": f"{tmp_path}:{os.environ.get('PATH', '')}",
        "HANDOFF_REQUIREMENT_URL": "https://example.com/requirements/remote.md",
        "MOCK_FETCH_SOURCE": str(fetch_src),
    }
    result = _run_sync(repo, env)
    assert result.returncode == 0, result.stderr
    baseline = (feat / "spec.md").read_text(encoding="utf-8")
    assert baseline.startswith("# Public baseline")
    override_text = (feat / "spec.override.md").read_text(encoding="utf-8")
    assert "Public baseline (from spec.md)" in override_text
    assert "Handoff requirement (fetched)" in override_text
