#!/usr/bin/env python3
"""Resolve the smallest ordered project-document slice for one Team role."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

import yaml


def _console(
    message: str, *, stream: Any = sys.stdout, end: str = "\n"
) -> None:
    logger = logging.getLogger(f"{__name__}.console.{id(stream)}")
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.terminator = end
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.info(message)


SCHEMA = "speckit-project-context/v1"
REQUIREMENTS = {"required", "suggested", "conditional"}
SAFE_SELECTOR = re.compile(r"^[A-Za-z0-9_.*/:-]+$")


class ContextResolutionError(RuntimeError):
    """Raised when the project-owned context manifest is unsafe or invalid."""


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContextResolutionError(f"{label} must be a mapping")
    return value


def _values(value: Any, label: str) -> list[str]:
    if value is None:
        return []
    raw = [value] if isinstance(value, str) else value
    if not isinstance(raw, list):
        raise ContextResolutionError(f"{label} must be a string or list")
    result = [str(item).strip() for item in raw if str(item).strip()]
    if any(not SAFE_SELECTOR.fullmatch(item) for item in result):
        raise ContextResolutionError(f"{label} contains an unsafe selector")
    return result


def _safe_path(project_root: Path, relative_text: str, label: str) -> Path:
    relative = Path(relative_text)
    if not relative_text.strip() or relative.is_absolute() or ".." in relative.parts:
        raise ContextResolutionError(f"{label} must stay repository-relative")
    root = project_root.resolve()
    candidate = project_root / relative
    try:
        candidate.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise ContextResolutionError(f"{label} escapes the repository") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ContextResolutionError(f"{label} must not traverse symbolic links")
    return candidate


def _load_yaml(path: Path, label: str) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ContextResolutionError(f"{label} is invalid YAML: {exc}") from exc
    return _mapping(loaded, label)


def _load_config(project_root: Path) -> dict[str, Any]:
    path = project_root / ".specify" / "team" / "ai-team-config.yml"
    return _load_yaml(path, "AI Team config") if path.is_file() else {}


def _matches(requested: str, declared: list[str]) -> bool:
    return not declared or "*" in declared or requested in declared


def _module_matches(requested: list[str], declared: list[str]) -> bool:
    if not declared or "*" in declared:
        return True
    if not requested:
        return False
    return bool(set(requested).intersection(declared))


def resolve_context(
    project_root: Path,
    *,
    role: str,
    phase: str,
    modules: list[str] | None = None,
) -> tuple[dict[str, Any], int]:
    project_root = project_root.resolve()
    config = _load_config(project_root)
    context_config = config.get("project_context") or {}
    context_config = _mapping(context_config, "project_context")
    manifest_text = str(
        context_config.get("manifest") or "docs/ai-team/context-map.yml"
    ).strip()
    manifest = _safe_path(project_root, manifest_text, "project_context.manifest")
    if not manifest.is_file():
        return (
            {
                "schema": SCHEMA,
                "status": "not-configured",
                "role": role,
                "phase": phase,
                "modules": modules or [],
                "manifest": manifest_text,
                "documents": [],
                "missing_required": [],
                "suggestions": [
                    f"Project context manifest is not present: {manifest_text}; continue with repository facts and consider adding one."
                ],
                "context_digest": "",
            },
            0,
        )

    data = _load_yaml(manifest, "project context manifest")
    if data.get("schema") != SCHEMA:
        raise ContextResolutionError(f"project context schema must be {SCHEMA}")
    raw_documents = data.get("documents") or []
    if not isinstance(raw_documents, list):
        raise ContextResolutionError("project context documents must be a list")

    selected: list[dict[str, Any]] = []
    missing_required: list[dict[str, str]] = []
    suggestions: list[str] = []
    seen_ids: set[str] = set()
    requested_modules = modules or []
    digest = hashlib.sha256(manifest.read_bytes())

    for index, raw in enumerate(raw_documents):
        item = _mapping(raw, f"documents[{index}]")
        document_id = str(item.get("id", "")).strip()
        if not document_id or not SAFE_SELECTOR.fullmatch(document_id):
            raise ContextResolutionError(f"documents[{index}].id is missing or unsafe")
        if document_id in seen_ids:
            raise ContextResolutionError(f"duplicate project context document id: {document_id}")
        seen_ids.add(document_id)
        requirement = str(item.get("requirement") or "suggested").strip()
        if requirement not in REQUIREMENTS:
            raise ContextResolutionError(
                f"{document_id}.requirement must be one of {sorted(REQUIREMENTS)}"
            )
        roles = _values(item.get("roles"), f"{document_id}.roles")
        phases = _values(item.get("phases"), f"{document_id}.phases")
        declared_modules = _values(item.get("modules"), f"{document_id}.modules")
        if not _matches(role, roles) or not _matches(phase, phases):
            continue
        if not _module_matches(requested_modules, declared_modules):
            continue
        relative_text = str(item.get("path", "")).strip()
        path = _safe_path(project_root, relative_text, f"{document_id}.path")
        entry = {
            "id": document_id,
            "path": relative_text.replace("\\", "/"),
            "requirement": requirement,
            "order": int(item.get("order", 100)),
            "description": str(item.get("description", "")).strip(),
            "exists": path.is_file(),
        }
        if path.is_file():
            digest.update(relative_text.encode("utf-8"))
            digest.update(path.read_bytes())
            selected.append(entry)
        elif requirement == "required":
            missing_required.append({"id": document_id, "path": entry["path"]})
        else:
            suggestions.append(
                f"Suggested project context is not present: {entry['path']} ({document_id})."
            )

    selected.sort(key=lambda item: (item["order"], item["id"]))
    missing_required.sort(key=lambda item: item["id"])
    status = "blocked" if missing_required else "ready"
    return (
        {
            "schema": SCHEMA,
            "status": status,
            "role": role,
            "phase": phase,
            "modules": requested_modules,
            "manifest": manifest_text,
            "documents": selected,
            "missing_required": missing_required,
            "suggestions": suggestions,
            "context_digest": digest.hexdigest(),
        },
        2 if missing_required else 0,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--role", required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--module", action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result, return_code = resolve_context(
            args.project_root,
            role=args.role,
            phase=args.phase,
            modules=args.module,
        )
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            output = _safe_path(
                args.project_root.resolve(),
                args.output.as_posix(),
                "output",
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
        _console(rendered, end="")
        return return_code
    except (ContextResolutionError, OSError, ValueError) as exc:
        _console(f"AI Team project context resolution failed: {exc}", stream=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
