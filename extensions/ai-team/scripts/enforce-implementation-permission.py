#!/usr/bin/env python3
"""Enforce the implementation envelope after the human permission gate."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
READY_STATUSES = {"pending-review", "ready", "approved"}


def _scalar(text: str, key: str, *, indent: int = 0) -> str:
    match = re.search(rf"(?m)^{' ' * indent}{re.escape(key)}:\s*[\"']?([^\n\"']*)", text)
    return match.group(1).strip() if match else ""


def _section(text: str, key: str, *, indent: int = 0) -> str:
    start = re.search(rf"(?m)^{' ' * indent}{re.escape(key)}:\s*$", text)
    if not start:
        return ""
    rest = text[start.end():]
    # PyYAML commonly emits an "indentless" sequence whose dash has the same
    # indentation as its parent key. A dash therefore remains part of the
    # section; only a non-list token at this indentation closes it.
    end = re.search(rf"(?m)^ {{0,{indent}}}(?!-\s)\S", rest)
    return rest[:end.start()] if end else rest


def _list(text: str, key: str, *, indent: int) -> list[str]:
    body = _section(text, key, indent=indent)
    return [item.strip().strip("\"'") for item in re.findall(r"(?m)^\s+-\s+(.+?)\s*$", body)]


def _set_scalar(text: str, key: str, value: str, *, indent: int = 0) -> str:
    pattern = rf"(?m)^({' ' * indent}{re.escape(key)}:)\s*.*$"
    replacement = rf"\1 {value}"
    if re.search(pattern, text):
        return re.sub(pattern, replacement, text, count=1)
    return text.rstrip() + f"\n{' ' * indent}{key}: {value}\n"


def _set_artifact(text: str, key: str, value: str) -> str:
    artifacts = re.search(r"(?m)^artifacts:\s*$", text)
    if not artifacts:
        return text.rstrip() + f"\nartifacts:\n  {key}: {value}\n"
    body = _section(text, "artifacts")
    if re.search(rf"(?m)^  {re.escape(key)}:", body):
        return re.sub(rf"(?m)^(  {re.escape(key)}:)\s*.*$", rf"\1 {value}", text, count=1)
    insertion = artifacts.end()
    return text[:insertion] + f"\n  {key}: {value}" + text[insertion:]


def _atomic_text(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def enforce(project_root: Path, run_id: str, work_slug: str) -> dict:
    if not SAFE_NAME.fullmatch(run_id) or not SAFE_NAME.fullmatch(work_slug):
        raise ValueError("run id and work slug must be safe directory names")

    run_state_path = project_root / ".specify" / "workflows" / "runs" / run_id / "state.json"
    work_root = project_root / ".specify" / "ai-team" / "work" / work_slug
    envelope_path = work_root / "permission-envelope.yml"
    context_path = work_root / "work-context.yml"
    state = json.loads(run_state_path.read_text(encoding="utf-8"))
    envelope = envelope_path.read_text(encoding="utf-8")
    context = context_path.read_text(encoding="utf-8")

    gate = state.get("step_results", {}).get("review-permissions", {})
    choice = gate.get("output", {}).get("choice")
    if choice != "approve":
        raise ValueError("review-permissions gate is not approved")
    if _scalar(envelope, "mode") != "implementation":
        raise ValueError("permission envelope mode must be implementation")
    status = _scalar(envelope, "status")
    if status not in READY_STATUSES:
        raise ValueError(
            f"implementation permission status is {status or '<missing>'}; "
            f"expected one of {sorted(READY_STATUSES)}"
        )

    tasks_path = project_root / "specs" / work_slug / "tasks.md"
    if not tasks_path.is_file():
        raise ValueError(f"approved implementation requires tasks: {tasks_path}")

    requested = _section(envelope, "requested_implementation_access")
    intended = set(_list(requested, "intended_write_paths", indent=2))
    allowed = set(_list(_section(envelope, "allow"), "write_paths", indent=2))
    missing = sorted(intended - allowed)
    if not intended:
        raise ValueError("requested_implementation_access.intended_write_paths is empty")
    if missing:
        raise ValueError(f"intended write paths are not allowed: {', '.join(missing)}")

    now = datetime.now(timezone.utc).isoformat()
    envelope = _set_scalar(envelope, "status", "approved")
    envelope = _set_scalar(envelope, "approved_by", gate.get("output", {}).get("decided_by") or "workflow-gate")
    envelope = _set_scalar(envelope, "approved_at", gate.get("output", {}).get("decided_at") or now)
    envelope = _set_scalar(envelope, "updated_at", now)
    context = _set_artifact(context, "tasks", f"specs/{work_slug}/tasks.md")
    context = _set_scalar(context, "phase", "implementing")
    context = _set_scalar(context, "last_completed_command", "speckit.ai-team.permissions")
    context = _set_scalar(context, "next_command", "speckit.implement")
    context = _set_scalar(context, "updated_at", now)
    _atomic_text(envelope_path, envelope)
    _atomic_text(context_path, context)
    return {"status": "approved", "work_slug": work_slug, "write_paths": sorted(intended)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--work-slug", required=True)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        result = enforce(args.project_root.resolve(), args.run_id, args.work_slug)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"AI Team implementation permission failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
