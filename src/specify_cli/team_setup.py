"""Install the built-in AI Team extension and its managed agent rules."""

from __future__ import annotations

import runpy
import shutil
from dataclasses import dataclass
from pathlib import Path

from ._assets import _locate_bundled_extension, get_speckit_version


CODEGRAPH_INSTALL_ERROR = """CodeGraph CLI is required by the AI Team extension.
Install the MIT-licensed @colbymchenry/codegraph CLI, then run specify init again:
- Windows PowerShell: irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex
- macOS/Linux: curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh
- npm alternative: npm install -g @colbymchenry/codegraph
The installer does not execute remote third-party installation scripts automatically."""


@dataclass(frozen=True)
class TeamSetupResult:
    installed: bool
    rule_files: tuple[str, ...]


def _require_codegraph() -> str:
    executable = shutil.which("codegraph")
    if executable is None:
        raise RuntimeError(CODEGRAPH_INSTALL_ERROR)
    return executable


def _initialize_rules(project_root: Path) -> list[str]:
    script = (
        project_root
        / ".specify"
        / "extensions"
        / "team"
        / "scripts"
        / "init_role_context.py"
    )
    if not script.is_file():
        raise RuntimeError(f"AI Team context initializer is missing: {script}")
    try:
        initialize = runpy.run_path(str(script))["initialize"]
        return initialize(project_root)
    except (KeyError, OSError, UnicodeError, ValueError) as exc:
        raise RuntimeError(f"Could not initialize AI Team agent rules: {exc}") from exc


def install_bundled_team(project_root: Path) -> TeamSetupResult:
    """Install Team directly, then initialize rules as one bounded operation."""
    from .extensions import ExtensionManager

    _require_codegraph()

    source = _locate_bundled_extension("team")
    if source is None:
        raise RuntimeError(
            "The built-in AI Team extension is missing from this Spec Kit distribution."
        )

    manager = ExtensionManager(project_root)
    already_installed = manager.registry.is_installed("team")
    if not already_installed:
        manager.install_from_directory(source, get_speckit_version())

    try:
        rules = _initialize_rules(project_root)
    except Exception:
        if not already_installed:
            manager.remove("team")
            backup = project_root / ".specify" / "extensions" / ".backup" / "team"
            if backup.is_dir() and not backup.is_symlink():
                shutil.rmtree(backup)
            elif backup.exists() or backup.is_symlink():
                backup.unlink()
        raise

    return TeamSetupResult(
        installed=not already_installed,
        rule_files=tuple(rules),
    )
