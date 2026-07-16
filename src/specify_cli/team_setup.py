"""Install the built-in AI Team extension and its managed agent rules."""

from __future__ import annotations

import runpy
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from packaging.version import InvalidVersion, Version

from ._assets import _locate_bundled_extension, get_speckit_version


CODEGRAPH_MIN_VERSION = Version("1.0.0")
CODEGRAPH_MAX_VERSION = Version("2.0.0")
CODEGRAPH_VERSION = re.compile(r"(?<![0-9])([0-9]+\.[0-9]+\.[0-9]+)(?![0-9])")
CODEGRAPH_INSTALL_ERROR = """CodeGraph CLI 1.x is required by AI Team.
Install it, open a new terminal, then run specify init again:
- Windows PowerShell: irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex
- macOS/Linux: curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh
- npm: npm install -g @colbymchenry/codegraph@^1
Specify does not execute third-party installation scripts automatically."""


@dataclass(frozen=True)
class TeamSetupResult:
    installed: bool
    rule_files: tuple[str, ...]


def _require_codegraph() -> tuple[str, str]:
    executable = shutil.which("codegraph")
    if executable is None:
        raise RuntimeError(CODEGRAPH_INSTALL_ERROR)
    try:
        result = subprocess.run(
            [executable, "version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"Could not run CodeGraph version check: {exc}") from exc

    output = f"{result.stdout}\n{result.stderr}".strip()
    match = CODEGRAPH_VERSION.search(output)
    if match is None:
        raise RuntimeError(f"Could not parse CodeGraph version from: {output!r}")
    try:
        version = Version(match.group(1))
    except InvalidVersion as exc:
        raise RuntimeError(
            f"CodeGraph returned an invalid version: {match.group(1)}"
        ) from exc
    if not CODEGRAPH_MIN_VERSION <= version < CODEGRAPH_MAX_VERSION:
        raise RuntimeError(
            f"CodeGraph {version} is unsupported; AI Team requires >=1.0.0,<2.0.0."
        )
    return executable, str(version)


def _initialize_rules(project_root: Path, source: Path) -> list[str]:
    script = source / "scripts" / "init_role_context.py"
    if not script.is_file():
        raise RuntimeError(f"AI Team context initializer is missing: {script}")
    try:
        initialize = runpy.run_path(str(script))["initialize"]
        return initialize(project_root)
    except (KeyError, OSError, UnicodeError, ValueError) as exc:
        raise RuntimeError(f"Could not initialize AI Team agent rules: {exc}") from exc


def install_bundled_team(project_root: Path) -> TeamSetupResult:
    """Register packaged Team skills, then initialize project-owned state."""
    from .extensions import ExtensionManager

    _require_codegraph()

    source = _locate_bundled_extension("team")
    if source is None:
        raise RuntimeError(
            "The built-in AI Team extension is missing from this Spec Kit distribution."
        )

    manager = ExtensionManager(project_root)
    already_installed = manager.registry.is_installed("team")
    created_state: list[Path] = []
    if not already_installed:
        manager.install_bundled_from_directory(source, get_speckit_version())

    try:
        state_dir = project_root / ".specify" / "team"
        state_dir.mkdir(parents=True, exist_ok=True)
        for source_file, name in (
            (source / "docs" / "context-bootstrap.md", "context-bootstrap.md"),
            (source / "config-template.yml", "ai-team-config.yml"),
        ):
            target = state_dir / name
            if not target.exists():
                shutil.copy2(source_file, target)
                created_state.append(target)

        if not already_installed:
            manager.registry.update(
                "team",
                {
                    "state_files": [
                        ".specify/team/context-bootstrap.md",
                        ".specify/team/ai-team-config.yml",
                    ]
                },
            )
        rules = _initialize_rules(project_root, source)
    except Exception:
        if not already_installed:
            manager.remove("team")
            backup = project_root / ".specify" / "extensions" / ".backup" / "team"
            if backup.is_dir() and not backup.is_symlink():
                shutil.rmtree(backup)
            elif backup.exists() or backup.is_symlink():
                backup.unlink()
        for path in created_state:
            if path.exists() or path.is_symlink():
                path.unlink()
        raise

    return TeamSetupResult(
        installed=not already_installed,
        rule_files=tuple(rules),
    )
