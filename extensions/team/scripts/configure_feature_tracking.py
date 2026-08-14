#!/usr/bin/env python3
"""Persist the one-time, human-confirmed Feature Record location."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def _console(message: str) -> None:
    logger = logging.getLogger(f"{__name__}.console.{id(sys.stdout)}")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.info(message)


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    return value


def _validate_root(project_root: Path, value: str) -> str:
    normalized = value.strip().replace("\\", "/").strip("/")
    relative = Path(normalized)
    if not normalized or relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Feature Record root must be a non-empty repository-relative path")
    if relative.parts[0].lower() in {".git", ".specify"}:
        raise ValueError("Feature Records must use a committed repository path")
    repository = project_root.resolve()
    candidate = project_root / relative
    try:
        candidate.resolve(strict=False).relative_to(repository)
    except ValueError as exc:
        raise ValueError("Feature Record root resolves outside the repository") from exc
    current = repository
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Feature Record root must not traverse symbolic links")
    if candidate.exists() and not candidate.is_dir():
        raise ValueError("Feature Record root must be a directory")
    return relative.as_posix()


def configure(
    project_root: Path,
    root: str,
    decided_by: str,
    *,
    decided_at: str | None = None,
) -> Path:
    actor = decided_by.strip()
    if not actor:
        raise ValueError("decided_by must name the human who confirmed the location")
    confirmed_root = _validate_root(project_root, root)
    config_path = project_root / ".specify" / "team" / "ai-team-config.yml"
    if config_path.is_file():
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        config = _mapping(loaded, "AI Team config")
    else:
        config = {}
    tracking = _mapping(config.get("feature_tracking"), "feature_tracking")
    location = _mapping(tracking.get("location"), "feature_tracking.location")
    existing_root = str(tracking.get("root", "")).strip().replace("\\", "/").strip("/")
    if location.get("locked") is True:
        if existing_root != confirmed_root:
            raise ValueError(
                "Feature Record location is already locked; use an explicit migration workflow"
            )
        return config_path
    tracking["root"] = confirmed_root
    tracking.setdefault("recommended_root", "docs/features")
    tracking["location"] = {
        **location,
        "status": "confirmed",
        "locked": True,
        "decided_by": actor,
        "decided_at": decided_at
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    config["feature_tracking"] = tracking
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return config_path


def snapshot(project_root: Path) -> dict[str, Any]:
    config_path = project_root / ".specify" / "team" / "ai-team-config.yml"
    if not config_path.is_file():
        raise ValueError(f"AI Team config is missing: {config_path}")
    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    config = _mapping(loaded, "AI Team config")
    tracking = _mapping(config.get("feature_tracking"), "feature_tracking")
    location = _mapping(tracking.get("location"), "feature_tracking.location")
    return {
        "config": str(config_path),
        "root": str(tracking.get("root", "")),
        "recommended_root": str(
            tracking.get("recommended_root", "docs/features")
        ),
        "catalog_file": str(
            tracking.get("catalog_file", "feature-catalog.yml")
        ),
        "record_path_template": str(
            tracking.get("record_path_template", "{feature_id}.md")
        ),
        "format": str(tracking.get("format", "markdown-frontmatter")),
        "location": {
            "status": str(location.get("status", "pending-confirmation")),
            "locked": location.get("locked") is True,
            "decided_by": str(location.get("decided_by", "")),
            "decided_at": str(location.get("decided_at", "")),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--root")
    parser.add_argument("--decided-by")
    parser.add_argument("--decided-at")
    args = parser.parse_args()
    try:
        project_root = args.project_root.resolve()
        if args.show:
            if args.root or args.decided_by or args.decided_at:
                raise ValueError("--show cannot be combined with write options")
            _console(json.dumps(snapshot(project_root), ensure_ascii=False, indent=2))
            return 0
        if not args.root or not args.decided_by:
            raise ValueError("--root and --decided-by are required unless --show is used")
        path = configure(
            project_root,
            args.root,
            args.decided_by,
            decided_at=args.decided_at,
        )
    except (OSError, ValueError, yaml.YAMLError) as exc:
        parser.exit(2, f"Feature tracking configuration blocked: {exc}\n")
    _console(f"Feature Record location confirmed and locked: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
