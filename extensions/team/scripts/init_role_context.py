#!/usr/bin/env python3
"""Install a small AI Team bootstrap pointer into supported agent rule files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


START = "<!-- AI TEAM CONTEXT START -->"
END = "<!-- AI TEAM CONTEXT END -->"
BOOTSTRAP = ".specify/extensions/team/docs/context-bootstrap.md"
AGENT_FILES = {
    "codex": "AGENTS.md",
    "claude": "CLAUDE.md",
    "cursor-agent": ".cursor/rules/specify-rules.mdc",
    "cursor": ".cursor/rules/specify-rules.mdc",
    "trae": ".trae/rules/project_rules.md",
}


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _integrations(root: Path) -> list[str]:
    state = _read_json(root / ".specify" / "integration.json")
    values: list[str] = []
    for key in ("active_integration", "default_integration", "integration"):
        value = state.get(key)
        if isinstance(value, str):
            values.append(value)
    installed = state.get("installed_integrations")
    if isinstance(installed, list):
        values.extend(value for value in installed if isinstance(value, str))

    options = _read_json(root / ".specify" / "init-options.json")
    for key in ("integration", "ai"):
        value = options.get(key)
        if isinstance(value, str):
            values.append(value)

    result: list[str] = []
    for value in values:
        normalized = value.strip().lower()
        if normalized in AGENT_FILES and normalized not in result:
            result.append(normalized)
    return result


def _managed_section(target: str) -> str:
    if target == "CLAUDE.md":
        return f"{START}\n@AGENTS.md\n{END}\n"
    return (
        f"{START}\n"
        "Before any AI Team role work, read and follow "
        f"`{BOOTSTRAP}`. Re-run its bootstrap after resume or context "
        "compression and before each phase artifact or gate. Repository files "
        "and approved artifacts override remembered chat context.\n"
        f"{END}\n"
    )


def _with_mdc_frontmatter(content: str) -> str:
    match = re.match(r"^(\s*---\n)(.*?)(\n---(?:\n|$))", content, re.DOTALL)
    if not match:
        return "---\nalwaysApply: true\n---\n\n" + content
    frontmatter = match.group(2)
    if re.search(r"(?m)^\s*alwaysApply\s*:", frontmatter):
        frontmatter = re.sub(
            r"(?m)^(\s*)alwaysApply\s*:.*$",
            r"\1alwaysApply: true",
            frontmatter,
            count=1,
        )
    else:
        frontmatter = frontmatter.rstrip() + "\nalwaysApply: true"
    return match.group(1) + frontmatter + match.group(3) + content[match.end() :]


def _safe_target(root: Path, relative: str) -> Path:
    path = root / relative
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"AI agent rule path escapes the project root: {relative}") from exc
    return path


def _merge(path: Path, target: str) -> None:
    content = path.read_text(encoding="utf-8-sig") if path.exists() else ""
    section = _managed_section(target)
    start = content.find(START)
    end = content.find(END, start + len(START)) if start >= 0 else -1
    if (start >= 0) != (end >= 0):
        raise ValueError(f"Unbalanced AI Team context markers in {target}")
    if start >= 0 and end >= 0:
        end += len(END)
        merged = content[:start] + section.rstrip("\n") + content[end:]
    else:
        separator = "" if not content or content.endswith("\n\n") else "\n\n"
        merged = content + separator + section
    if path.suffix == ".mdc":
        merged = _with_mdc_frontmatter(merged)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(merged.replace("\r\n", "\n"), encoding="utf-8")


def initialize(root: Path) -> list[str]:
    root = root.resolve()
    bootstrap = (root / BOOTSTRAP).resolve()
    try:
        bootstrap.relative_to(root)
    except ValueError as exc:
        raise ValueError("AI Team bootstrap path escapes the project root") from exc
    if not bootstrap.is_file():
        raise FileNotFoundError(
            f"AI Team bootstrap is not installed: {bootstrap}. Install the ai-team bundle first."
        )

    targets = ["AGENTS.md"]
    for integration in _integrations(root):
        target = AGENT_FILES[integration]
        if target not in targets:
            targets.append(target)
    for target in targets:
        _merge(_safe_target(root, target), target)
    return targets


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    targets = initialize(Path(args.project_root))
    print("AI Team context initialized: " + ", ".join(targets))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
