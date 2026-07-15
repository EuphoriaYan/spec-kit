"""Trusted AI Team rule initialization shared by init and bundle commands."""

from __future__ import annotations

import runpy
from pathlib import Path

from ..._assets import _locate_bundled_extension
from .. import BundlerError


def initialize_bundled_team_context(project_root: Path, manifest) -> list[str]:
    """Initialize rule pointers only for the built-in AI Team bundle."""
    if manifest.bundle.id != "ai-team":
        return []

    bundled = _locate_bundled_extension("team")
    script = bundled / "scripts" / "init_role_context.py" if bundled else None
    if script is None or not script.is_file():
        raise BundlerError(
            "The built-in AI Team context initializer is missing from this "
            "Spec Kit distribution."
        )
    try:
        initialize = runpy.run_path(str(script))["initialize"]
        return initialize(project_root)
    except (KeyError, OSError, UnicodeError, ValueError) as exc:
        raise BundlerError(f"Could not initialize AI Team agent rules: {exc}") from exc
