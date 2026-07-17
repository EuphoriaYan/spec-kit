#!/usr/bin/env python3
"""Persist AI Team memory through a local file adapter or optional Mem0 mirror."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml


IGNORE_START = "# BEGIN AI TEAM PRIVATE MEMORY"
IGNORE_END = "# END AI TEAM PRIVATE MEMORY"
IGNORE_PATHS = (
    "/.specify/team/memory/staging/",
    "/.specify/team/memory/local/",
    "/.specify/team/memory/department/",
    "/.specify/team/releases/private/",
)
DEFAULT_TIER_PATHS = {
    "local": ".specify/team/memory/local",
    "department": ".specify/team/memory/department",
    "enterprise": "docs/ai-team/memory",
}
KNOWLEDGE_ROOT = Path("docs/ai-team/knowledge/rules")
VALID_MEMORY_TYPES = {
    "decision",
    "attempt",
    # Accepted legacy card names; new cards should use the two canonical types.
    "bugfix_lesson",
    "feature_decision",
}
VALID_AUTHORITIES = {"advisory", "approved-guidance"}
VALID_STATUSES = {"proposed", "active", "superseded"}
VALID_KNOWLEDGE_TYPES = {
    "architecture-rule",
    "coding-standard",
    "compatibility-rule",
    "operations-rule",
    "security-rule",
    "test-rule",
}


class MemoryAdapterError(RuntimeError):
    """Raised when memory cannot be persisted without violating its contract."""


def ensure_memory_gitignore(project_root: Path) -> Path:
    """Add the managed private-memory ignore block without touching other rules."""
    gitignore = project_root / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    block = "\n".join((IGNORE_START, *IGNORE_PATHS, IGNORE_END))

    if IGNORE_START in existing or IGNORE_END in existing:
        if IGNORE_START not in existing or IGNORE_END not in existing:
            raise MemoryAdapterError("incomplete AI Team memory block in .gitignore")
        pattern = re.compile(
            rf"{re.escape(IGNORE_START)}.*?{re.escape(IGNORE_END)}", re.DOTALL
        )
        updated = pattern.sub(block, existing)
    else:
        separator = "" if not existing or existing.endswith("\n") else "\n"
        updated = f"{existing}{separator}{block}\n"

    if updated != existing:
        gitignore.write_text(updated, encoding="utf-8")
    return gitignore


def _load_config(project_root: Path, config_path: Path | None) -> dict[str, Any]:
    if config_path is None:
        config_path = project_root / ".specify" / "team" / "ai-team-config.yml"
        legacy_path = (
            project_root
            / ".specify"
            / "extensions"
            / "ai-team"
            / "ai-team-config.yml"
        )
        if not config_path.exists() and legacy_path.exists():
            config_path = legacy_path
    if not config_path.exists():
        return {}
    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise MemoryAdapterError("AI Team config must be a YAML mapping")
    return loaded


def _frontmatter(card_text: str) -> dict[str, Any]:
    if not card_text.startswith("---\n"):
        raise MemoryAdapterError("memory card must start with YAML frontmatter")
    try:
        _, raw, _ = card_text.split("---", 2)
    except ValueError as exc:
        raise MemoryAdapterError("memory card frontmatter is not closed") from exc
    try:
        metadata = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise MemoryAdapterError("memory card frontmatter is invalid YAML") from exc
    if not isinstance(metadata, dict):
        raise MemoryAdapterError("memory card frontmatter must be a mapping")
    return metadata


def _body(card_text: str) -> str:
    _, _, body = card_text.split("---", 2)
    return body.lstrip("\r\n")


def _values(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value.strip()} if value.strip() else set()
    if isinstance(value, list):
        return {str(item).strip() for item in value if str(item).strip()}
    return set()


def _scope(metadata: dict[str, Any], key: str) -> set[str]:
    scope = metadata.get("scope", {})
    if not isinstance(scope, dict):
        return set()
    return _values(scope.get(key))


def _matches(metadata: dict[str, Any], filters: dict[str, set[str]]) -> bool:
    scope = metadata.get("scope")
    if not isinstance(scope, dict):
        return False
    if not any(_scope(metadata, key) for key in filters):
        return False
    for key, requested in filters.items():
        declared = _scope(metadata, key)
        if (
            requested
            and declared
            and "*" not in declared
            and not requested.intersection(declared)
        ):
            return False
    return True


def _safe_markdown_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    resolved_root = root.resolve()
    result: list[Path] = []
    for path in sorted(root.rglob("*.md")):
        try:
            path.resolve().relative_to(resolved_root)
        except ValueError:
            continue
        if path.is_file():
            result.append(path)
    return result


def _validate_memory_metadata(metadata: dict[str, Any], tier: str) -> None:
    memory_type = str(metadata.get("memory_type", "")).strip()
    if memory_type not in VALID_MEMORY_TYPES:
        raise MemoryAdapterError(
            "memory_type must be decision or attempt (legacy bugfix_lesson and feature_decision are also accepted)"
        )
    authority = str(metadata.get("authority", "advisory")).strip()
    if authority not in VALID_AUTHORITIES:
        raise MemoryAdapterError(
            "memory authority must be advisory or approved-guidance"
        )
    status = str(metadata.get("status", "active")).strip()
    if status not in VALID_STATUSES:
        raise MemoryAdapterError(
            "memory status must be proposed, active, or superseded"
        )
    if tier != "enterprise" and authority != "advisory":
        raise MemoryAdapterError(
            "local and department memory cannot claim approved guidance"
        )
    if tier == "enterprise" and metadata.get("privacy") == "private":
        raise MemoryAdapterError("private memory cannot be persisted as enterprise")
    if authority == "approved-guidance":
        required = {"approved_by", "approved_at", "evidence"}
        missing = sorted(key for key in required if not metadata.get(key))
        if missing:
            raise MemoryAdapterError(
                "approved guidance is missing: " + ", ".join(missing)
            )


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)


def _tier_path(config: dict[str, Any], tier: str) -> str:
    return str(
        config.get("memory", {})
        .get("tiers", {})
        .get(tier, {})
        .get("path", DEFAULT_TIER_PATHS[tier])
    )


def _update_index(destination: Path, record: dict[str, Any]) -> Path:
    index_path = destination.parent / "index.json"
    records: list[dict[str, Any]] = []
    if index_path.exists():
        loaded = json.loads(index_path.read_text(encoding="utf-8"))
        if isinstance(loaded, list):
            records = loaded
    records = [item for item in records if item.get("path") != record["path"]]
    records.append(record)
    _atomic_write(index_path, json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    return index_path


def _sync_mem0(
    card_text: str,
    metadata: dict[str, Any],
    config: dict[str, Any],
    tier: str,
) -> Any:
    service = config.get("memory", {}).get("service", {})
    tier_config = config.get("memory", {}).get("tiers", {}).get(tier, {})
    if tier == "local" or metadata.get("privacy") == "private":
        raise MemoryAdapterError("local or private memory cannot be synced to mem0")
    namespace = str(tier_config.get("namespace", "")).strip()
    if not namespace:
        raise MemoryAdapterError(f"mem0 sync requires memory.tiers.{tier}.namespace")
    api_key_env = str(service.get("mem0", {}).get("api_key_env", "MEM0_API_KEY"))
    api_key = os.environ.get(api_key_env, "").strip()
    if not api_key:
        raise MemoryAdapterError(f"mem0 sync requires environment variable {api_key_env}")
    try:
        mem0 = importlib.import_module("mem0")
    except ImportError as exc:
        raise MemoryAdapterError(
            "mem0 backend requires the optional 'mem0ai' package"
        ) from exc

    client = mem0.MemoryClient(api_key=api_key)
    remote_metadata = {
        key: value
        for key, value in metadata.items()
        if key not in {"raw_customer_demand", "credentials", "secrets"}
    }
    remote_metadata.update({"tier": tier, "namespace": namespace})
    return client.add(
        messages=[{"role": "user", "content": card_text}],
        user_id=namespace,
        metadata=remote_metadata,
    )


def persist_memory(
    *,
    project_root: Path,
    source: Path,
    tier: str,
    backend: str = "file",
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Persist one reviewed card locally and optionally mirror it to Mem0."""
    project_root = project_root.resolve()
    source = source.resolve()
    if tier not in DEFAULT_TIER_PATHS:
        raise MemoryAdapterError(f"unsupported memory tier: {tier}")
    if backend not in {"file", "mem0"}:
        raise MemoryAdapterError(f"unsupported memory backend: {backend}")
    if not _inside(source, project_root) or not source.is_file():
        raise MemoryAdapterError("memory source must be a file inside the project")

    ensure_memory_gitignore(project_root)
    config = _load_config(project_root, config_path)
    allowed_source_roots = [
        project_root / ".specify" / "team" / "memory" / "staging",
        project_root / DEFAULT_TIER_PATHS[tier],
    ]
    if not any(_inside(source, root) for root in allowed_source_roots):
        raise MemoryAdapterError(
            "memory source must be under the managed staging or canonical tier path"
        )
    card_text = source.read_text(encoding="utf-8")
    metadata = _frontmatter(card_text)
    if metadata.get("tier") != tier:
        raise MemoryAdapterError("memory card tier does not match requested tier")
    required = {"memory_type", "privacy", "owner"}
    missing = sorted(key for key in required if not metadata.get(key))
    if missing:
        raise MemoryAdapterError(f"memory card is missing: {', '.join(missing)}")
    _validate_memory_metadata(metadata, tier)

    relative_root = Path(_tier_path(config, tier))
    if relative_root.is_absolute() or ".." in relative_root.parts:
        raise MemoryAdapterError("memory tier path must stay inside the project")
    destination_root = (project_root / relative_root).resolve()
    if not _inside(destination_root, project_root):
        raise MemoryAdapterError("memory tier path escapes the project")
    destination = destination_root / source.name
    _atomic_write(destination, card_text)

    digest = hashlib.sha256(card_text.encode("utf-8")).hexdigest()
    record: dict[str, Any] = {
        "path": destination.relative_to(project_root).as_posix(),
        "sha256": digest,
        "tier": tier,
        "privacy": metadata["privacy"],
        "memory_type": metadata["memory_type"],
        "owner": metadata["owner"],
        "authority": metadata.get("authority", "advisory"),
        "status": metadata.get("status", "active"),
        "backend": backend,
    }
    if backend == "mem0":
        response = _sync_mem0(card_text, metadata, config, tier)
        record["remote"] = response
    index_path = _update_index(destination, record)
    record["index"] = index_path.relative_to(project_root).as_posix()
    return record


def promote_memory_to_knowledge(
    *,
    project_root: Path,
    source: Path,
    knowledge_type: str,
) -> dict[str, Any]:
    """Promote reviewed enterprise memory into binding project knowledge."""
    project_root = project_root.resolve()
    source = source.resolve()
    enterprise_root = (project_root / DEFAULT_TIER_PATHS["enterprise"]).resolve()
    if not _inside(source, enterprise_root) or not source.is_file():
        raise MemoryAdapterError(
            "only a persisted enterprise memory card can become project knowledge"
        )
    if knowledge_type not in VALID_KNOWLEDGE_TYPES:
        raise MemoryAdapterError(f"unsupported knowledge type: {knowledge_type}")

    card_text = source.read_text(encoding="utf-8")
    metadata = _frontmatter(card_text)
    _validate_memory_metadata(metadata, "enterprise")
    if metadata.get("tier") != "enterprise":
        raise MemoryAdapterError("knowledge promotion requires enterprise memory")
    if metadata.get("authority") != "approved-guidance":
        raise MemoryAdapterError(
            "knowledge promotion requires authority: approved-guidance"
        )
    if metadata.get("status", "active") != "active":
        raise MemoryAdapterError("knowledge promotion requires status: active")
    if not _matches(
        metadata,
        {"roles": set(), "work_types": set(), "modules": set()},
    ):
        raise MemoryAdapterError("knowledge promotion requires an explicit scope")

    knowledge_metadata = dict(metadata)
    knowledge_metadata.update(
        {
            "knowledge_type": knowledge_type,
            "authority": "binding",
            "source_memory": source.relative_to(project_root).as_posix(),
        }
    )
    rendered = (
        "---\n"
        + yaml.safe_dump(
            knowledge_metadata, sort_keys=False, allow_unicode=True
        )
        + "---\n\n"
        + _body(card_text)
    )
    destination = (project_root / KNOWLEDGE_ROOT / source.name).resolve()
    if not _inside(destination, project_root / KNOWLEDGE_ROOT):
        raise MemoryAdapterError("knowledge destination escapes the project")
    _atomic_write(destination, rendered)
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    record = {
        "path": destination.relative_to(project_root).as_posix(),
        "sha256": digest,
        "authority": "binding",
        "knowledge_type": knowledge_type,
        "owner": metadata["owner"],
        "source_memory": knowledge_metadata["source_memory"],
    }
    index_path = _update_index(destination, record)
    record["index"] = index_path.relative_to(project_root).as_posix()
    return record


def retrieve_context(
    *,
    project_root: Path,
    role: str,
    work_type: str,
    modules: list[str] | None = None,
    include_department: bool = False,
) -> str:
    """Return a small, precedence-ordered guidance slice for one task."""
    project_root = project_root.resolve()
    if include_department:
        config = _load_config(project_root, None)
        namespace = (
            config.get("memory", {})
            .get("tiers", {})
            .get("department", {})
            .get("namespace", "")
        )
        if not str(namespace).strip():
            raise MemoryAdapterError(
                "department memory retrieval requires an approved namespace"
            )
    filters = {
        "roles": {role},
        "work_types": {work_type},
        "modules": set(modules or []),
    }
    sources: list[tuple[str, Path]] = [
        ("binding knowledge", project_root / KNOWLEDGE_ROOT),
        ("enterprise memory (advisory)", project_root / DEFAULT_TIER_PATHS["enterprise"]),
    ]
    if include_department:
        sources.append(
            (
                "department memory (advisory)",
                project_root / DEFAULT_TIER_PATHS["department"],
            )
        )

    promoted_sources: set[str] = set()
    for path in _safe_markdown_files(project_root / KNOWLEDGE_ROOT):
        try:
            source_memory = _frontmatter(
                path.read_text(encoding="utf-8")
            ).get("source_memory")
        except MemoryAdapterError:
            continue
        if isinstance(source_memory, str) and source_memory.strip():
            promoted_sources.add(source_memory.strip())

    sections: list[str] = []
    seen: set[Path] = set()
    for heading, root in sources:
        entries: list[str] = []
        for path in _safe_markdown_files(root):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            text = path.read_text(encoding="utf-8")
            try:
                metadata = _frontmatter(text)
            except MemoryAdapterError:
                continue
            if metadata.get("status", "active") != "active":
                continue
            if not _matches(metadata, filters):
                continue
            if heading == "binding knowledge":
                if metadata.get("authority") != "binding":
                    continue
            elif metadata.get("authority", "advisory") == "binding":
                continue
            relative = path.relative_to(project_root).as_posix()
            if heading != "binding knowledge" and relative in promoted_sources:
                continue
            entries.append(f"### {relative}\n\n{_body(text).rstrip()}")
        if entries:
            sections.append(f"## {heading.title()}\n\n" + "\n\n".join(entries))

    if not sections:
        return "No matching approved Knowledge or advisory Memory was found.\n"
    preamble = (
        "# Task Guidance Slice\n\n"
        "Binding Knowledge is project policy. Memory is advisory and must not "
        "override current source, tests, Issue, Plan, or human decisions.\n\n"
    )
    return preamble + "\n\n".join(sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", nargs="?", choices=("persist", "promote", "retrieve"), default="persist"
    )
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--ensure-ignore", action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--tier", choices=sorted(DEFAULT_TIER_PATHS))
    parser.add_argument("--backend", choices=("file", "mem0"), default="file")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--knowledge-type", choices=sorted(VALID_KNOWLEDGE_TYPES))
    parser.add_argument("--role")
    parser.add_argument("--work-type")
    parser.add_argument("--module", action="append", default=[])
    parser.add_argument("--include-department", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        if args.ensure_ignore:
            path = ensure_memory_gitignore(args.project_root.resolve())
            print(json.dumps({"gitignore": str(path)}, ensure_ascii=False))
            return 0
        if args.action == "retrieve":
            if not args.role or not args.work_type:
                parser.error("retrieve requires --role and --work-type")
            rendered = retrieve_context(
                project_root=args.project_root,
                role=args.role,
                work_type=args.work_type,
                modules=args.module,
                include_department=args.include_department,
            )
            if args.output:
                output = args.output.resolve()
                project_root = args.project_root.resolve()
                if not _inside(output, project_root):
                    raise MemoryAdapterError("retrieval output must stay inside the project")
                _atomic_write(output, rendered)
            else:
                print(rendered, end="")
            return 0
        if args.source is None:
            parser.error(f"{args.action} requires --source")
        if args.action == "promote":
            if not args.knowledge_type:
                parser.error("promote requires --knowledge-type")
            result = promote_memory_to_knowledge(
                project_root=args.project_root,
                source=args.source,
                knowledge_type=args.knowledge_type,
            )
        else:
            if args.tier is None:
                parser.error("persist requires --tier")
            result = persist_memory(
                project_root=args.project_root,
                source=args.source,
                tier=args.tier,
                backend=args.backend,
                config_path=args.config,
            )
    except (MemoryAdapterError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"AI Team memory adapter failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
