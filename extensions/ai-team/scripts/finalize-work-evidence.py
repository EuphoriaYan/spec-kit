#!/usr/bin/env python3
"""Require durable convergence evidence and finalize the Work Context index."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


def _set_scalar(text: str, key: str, value: str) -> str:
    pattern = rf"(?m)^({re.escape(key)}:)\s*.*$"
    if re.search(pattern, text):
        return re.sub(pattern, rf"\1 {value}", text, count=1)
    return text.rstrip() + f"\n{key}: {value}\n"


def _set_artifact(text: str, key: str, value: str) -> str:
    artifacts = re.search(r"(?m)^artifacts:\s*$", text)
    if not artifacts:
        return text.rstrip() + f"\nartifacts:\n  {key}: {value}\n"
    if re.search(rf"(?m)^  {re.escape(key)}:", text):
        return re.sub(rf"(?m)^(  {re.escape(key)}:)\s*.*$", rf"\1 {value}", text, count=1)
    insertion = artifacts.end()
    return text[:insertion] + f"\n  {key}: {value}" + text[insertion:]


def _atomic_text(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def finalize(project_root: Path, work_slug: str) -> dict:
    if not SAFE_NAME.fullmatch(work_slug):
        raise ValueError("work slug must be a safe directory name")
    work_root = project_root / ".specify" / "ai-team" / "work" / work_slug
    context_path = work_root / "work-context.yml"
    evidence_path = work_root / "evidence" / "evidence-board.md"
    tasks_path = project_root / "specs" / work_slug / "tasks.md"
    if not tasks_path.is_file():
        raise ValueError(f"tasks artifact is missing: {tasks_path}")
    if not evidence_path.is_file() or evidence_path.stat().st_size == 0:
        raise ValueError(f"durable Evidence Board is missing: {evidence_path}")
    evidence = evidence_path.read_text(encoding="utf-8")
    if "# Evidence Board" not in evidence:
        raise ValueError("evidence-board.md does not contain an Evidence Board heading")

    context = context_path.read_text(encoding="utf-8")
    now = datetime.now(timezone.utc).isoformat()
    context = _set_artifact(context, "tasks", f"specs/{work_slug}/tasks.md")
    context = _set_artifact(context, "evidence", f".specify/ai-team/work/{work_slug}/evidence/evidence-board.md")
    context = _set_scalar(context, "phase", "evidence")
    context = _set_scalar(context, "last_completed_command", "speckit.converge")
    context = _set_scalar(context, "next_command", "speckit.ai-team.pr")
    context = _set_scalar(context, "updated_at", now)
    _atomic_text(context_path, context)
    return {"status": "evidence-ready", "work_slug": work_slug, "evidence": str(evidence_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-slug", required=True)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        result = finalize(args.project_root.resolve(), args.work_slug)
    except (OSError, ValueError) as exc:
        print(f"AI Team evidence finalization failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
