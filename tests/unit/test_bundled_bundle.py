"""Tests for init-time installation from the distribution bundle catalog."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specify_cli.bundler import BundlerError


def _write_bundle(catalog_dir: Path, bundle_id: str) -> None:
    bundle_dir = catalog_dir / bundle_id
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "bundle.yml").write_text(
        f"""
schema_version: "1.0"
bundle:
  id: {bundle_id}
  name: Test Bundle
  version: "1.0.0"
  role: test
  description: Test bundle
  author: Test
  license: MIT
requires:
  speckit_version: ">=0.12.4"
  tools: []
  mcp: []
provides: {{}}
""".lstrip(),
        encoding="utf-8",
    )


def test_load_bundled_manifests_resolves_every_relative_download_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from specify_cli.bundler.services import bundled_install

    _write_bundle(tmp_path, "alpha")
    _write_bundle(tmp_path, "beta")
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "bundles": {
                    "beta": {
                        "id": "beta",
                        "version": "1.0.0",
                        "download_url": "beta/bundle.yml",
                    },
                    "alpha": {
                        "id": "alpha",
                        "version": "1.0.0",
                        "download_url": "alpha/bundle.yml",
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        bundled_install, "_bundled_catalog_path", lambda: catalog_path
    )

    manifests = bundled_install.load_bundled_manifests()

    assert [manifest.bundle.id for manifest in manifests] == ["alpha", "beta"]


def test_load_bundled_manifests_rejects_path_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from specify_cli.bundler.services import bundled_install

    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "bundles": {
                    "escape": {
                        "id": "escape",
                        "version": "1.0.0",
                        "download_url": "../bundle.yml",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        bundled_install, "_bundled_catalog_path", lambda: catalog_path
    )

    with pytest.raises(BundlerError, match="outside the bundled catalog"):
        bundled_install.load_bundled_manifests()


def test_load_bundled_manifests_uses_packaged_core_without_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from specify_cli.bundler.services import bundled_install

    core = tmp_path / "core_pack"
    catalog_dir = core / "bundles"
    _write_bundle(catalog_dir, "packaged")
    (catalog_dir / "catalog.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "bundles": {
                    "packaged": {
                        "id": "packaged",
                        "version": "1.0.0",
                        "download_url": "packaged/bundle.yml",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(bundled_install, "_locate_core_pack", lambda: core)
    monkeypatch.setattr(
        bundled_install,
        "_repo_root",
        lambda: pytest.fail("source-checkout fallback was used"),
    )

    manifests = bundled_install.load_bundled_manifests()

    assert [manifest.bundle.id for manifest in manifests] == ["packaged"]


def test_init_installs_only_team_extension_and_managed_rules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from typer.testing import CliRunner

    from specify_cli import app
    from specify_cli import team_setup

    monkeypatch.setattr(team_setup, "_require_codegraph", lambda: "codegraph")
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "init",
            "--here",
            "--force",
            "--integration",
            "codex",
            "--ignore-agent-tools",
            "--script",
            "sh",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (tmp_path / ".specify" / "extensions" / "team").is_dir()
    assert not (tmp_path / ".specify" / "extensions" / "bug").exists()
    assert not (tmp_path / ".specify" / "extensions" / "agent-context").exists()
    assert not (
        tmp_path / ".specify" / "presets" / "ai-team-sdd-governance"
    ).exists()
    assert not (tmp_path / ".specify" / "workflows" / "ai-team-intake").exists()
    assert not (tmp_path / ".specify" / "workflows" / "ai-team-sdd").exists()
    assert not (tmp_path / ".specify" / "workflows" / "ai-team-bugfix").exists()
    assert not (tmp_path / ".specify" / "workflows" / "speckit").exists()
    assert "AI TEAM CONTEXT START" in (tmp_path / "AGENTS.md").read_text(
        encoding="utf-8"
    )
    assert not (tmp_path / ".specify" / "bundles" / "installed.json").exists()
    skills = {path.name for path in (tmp_path / ".agents" / "skills").iterdir()}
    assert skills == {
        "speckit-team-assess",
        "speckit-team-fix",
        "speckit-team-implement",
        "speckit-team-plan-and-task",
        "speckit-team-review",
        "speckit-team-specify",
    }


def test_init_fails_closed_when_team_setup_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from typer.testing import CliRunner

    from specify_cli import app
    from specify_cli import team_setup

    monkeypatch.chdir(tmp_path)

    def fail_install(*args, **kwargs):
        raise RuntimeError("team setup exploded")

    monkeypatch.setattr(
        team_setup,
        "install_bundled_team",
        fail_install,
    )

    result = CliRunner().invoke(
        app,
        [
            "init",
            "--here",
            "--force",
            "--integration",
            "generic",
            "--integration-options",
            "--commands-dir .agent/commands/",
            "--script",
            "sh",
        ],
    )

    assert result.exit_code == 1
    assert "Initialization failed: team setup exploded" in result.stdout
    assert "Project ready." not in result.stdout


def test_team_profile_hides_native_skills_and_full_profile_keeps_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from typer.testing import CliRunner

    from specify_cli import app
    from specify_cli import team_setup

    monkeypatch.setattr(team_setup, "_require_codegraph", lambda: "codegraph")

    runner = CliRunner()
    team_root = tmp_path / "team"
    full_root = tmp_path / "full"

    team_result = runner.invoke(
        app,
        [
            "init",
            str(team_root),
            "--ignore-agent-tools",
            "--integration",
            "codex",
            "--script",
            "sh",
        ],
    )
    full_result = runner.invoke(
        app,
        [
            "init",
            str(full_root),
            "--ignore-agent-tools",
            "--integration",
            "codex",
            "--script",
            "sh",
            "--skill-profile",
            "full",
        ],
    )

    assert team_result.exit_code == 0, team_result.stdout
    assert full_result.exit_code == 0, full_result.stdout
    team_skills = {path.name for path in (team_root / ".agents" / "skills").iterdir()}
    full_skills = {path.name for path in (full_root / ".agents" / "skills").iterdir()}
    assert team_skills == {
        "speckit-team-assess",
        "speckit-team-fix",
        "speckit-team-implement",
        "speckit-team-plan-and-task",
        "speckit-team-review",
        "speckit-team-specify",
    }
    assert team_skills < full_skills
    assert "speckit-plan" in full_skills
    assert "speckit-implement" in full_skills
    assert (full_root / ".specify" / "workflows" / "speckit" / "workflow.yml").is_file()
