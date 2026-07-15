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


def test_init_installs_every_bundle_from_distribution_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from typer.testing import CliRunner

    from specify_cli import app
    from specify_cli.bundler.models.records import load_records

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
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

    assert result.exit_code == 0, result.stdout
    assert (tmp_path / ".specify" / "extensions" / "team").is_dir()
    assert (tmp_path / ".specify" / "extensions" / "bug").is_dir()
    assert (tmp_path / ".specify" / "extensions" / "agent-context").is_dir()
    assert not (tmp_path / ".specify" / "extensions" / "ai-team").exists()
    assert not (
        tmp_path / ".specify" / "presets" / "ai-team-sdd-governance"
    ).exists()
    assert not (tmp_path / ".specify" / "workflows" / "ai-team-intake").exists()
    assert not (tmp_path / ".specify" / "workflows" / "ai-team-sdd").exists()
    assert not (tmp_path / ".specify" / "workflows" / "ai-team-bugfix").exists()
    assert "AI TEAM CONTEXT START" in (tmp_path / "AGENTS.md").read_text(
        encoding="utf-8"
    )
    assert [record.bundle_id for record in load_records(tmp_path)] == ["ai-team"]


def test_init_fails_closed_when_distribution_bundle_install_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from typer.testing import CliRunner

    from specify_cli import app
    from specify_cli.bundler.services import bundled_install

    monkeypatch.chdir(tmp_path)

    def fail_install(*args, **kwargs):
        raise BundlerError("distribution bundle exploded")

    monkeypatch.setattr(
        bundled_install,
        "install_bundled_catalog",
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
    assert "Initialization failed: distribution bundle exploded" in result.stdout
    assert "Project ready." not in result.stdout
