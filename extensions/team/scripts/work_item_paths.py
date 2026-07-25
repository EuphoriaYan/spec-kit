"""Canonical, configuration-aware paths for Team work artifacts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


SAFE_WORK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
RESERVED_SPECIFY_NAMES = {
    "bugfix",
    "extensions",
    "memory",
    "scripts",
    "team",
    "templates",
    "workflows",
}
CATEGORY_ALIASES = {
    "feature": "feature",
    "new-project": "feature",
    "template": "feature",
    "bug": "bugfix",
    "bugfix": "bugfix",
}
DEFAULT_FEATURE_TEMPLATE = ".specify/{work_id}"
LEGACY_FEATURE_TEMPLATE = ".specify/feature/{work_id}"
DEFAULT_BUGFIX_TEMPLATE = ".specify/bugfix/{bug_slug}"


def normalize_category(work_type: str) -> str:
    category = CATEGORY_ALIASES.get(work_type.strip().lower())
    if category is None:
        raise ValueError("work type must resolve to feature or bugfix")
    return category


def _load_team_config(project_root: Path) -> dict[str, Any]:
    config_path = project_root / ".specify" / "team" / "ai-team-config.yml"
    if not config_path.is_file():
        return {}
    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError("AI Team config must contain a YAML mapping")
    return loaded


def _template_for(project_root: Path, category: str) -> tuple[str, str]:
    config = _load_team_config(project_root)
    artifacts = config.get("work_artifacts") or {}
    if not isinstance(artifacts, dict):
        raise ValueError("work_artifacts must be a mapping")
    if category == "feature":
        return (
            str(artifacts.get("feature_path_template") or DEFAULT_FEATURE_TEMPLATE),
            "work_id",
        )
    return (
        str(artifacts.get("bugfix_path_template") or DEFAULT_BUGFIX_TEMPLATE),
        "bug_slug",
    )


def _render_safe_path(
    project_root: Path, template: str, placeholder: str, value: str
) -> Path:
    expected = "{" + placeholder + "}"
    if template.count(expected) != 1:
        raise ValueError(f"path template must contain exactly one {expected}")
    rendered = template.replace(expected, value)
    relative = Path(rendered)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("work root template must remain repository-relative")

    root = project_root.resolve()
    candidate = project_root / relative
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("work root resolves outside the repository") from exc

    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("work root must not traverse symbolic links")
    return candidate


def resolve_work_root(
    project_root: Path,
    work_type: str,
    work_id: str,
    *,
    prefer_legacy_existing: bool = True,
) -> Path:
    if not SAFE_WORK_ID.fullmatch(work_id):
        raise ValueError("work ID must be a safe stable identifier")
    category = normalize_category(work_type)
    if category == "feature" and work_id.lower() in RESERVED_SPECIFY_NAMES:
        raise ValueError("feature ID collides with a reserved .specify directory")

    template, placeholder = _template_for(project_root, category)
    target = _render_safe_path(project_root, template, placeholder, work_id)

    if category == "feature" and prefer_legacy_existing and not target.exists():
        legacy = _render_safe_path(
            project_root, LEGACY_FEATURE_TEMPLATE, "work_id", work_id
        )
        if legacy.exists():
            return legacy
    return target
