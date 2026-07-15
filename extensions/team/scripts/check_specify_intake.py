#!/usr/bin/env python3
"""Check progressive Specify readiness without inventing user answers."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
PLACEHOLDER = re.compile(r"(?i)\b(?:pending|TBD|TODO|FIXME)\b|<[^>]+>")
COMMON = {f"CL-{number:03d}" for number in range(1, 10)}
FEATURE = {"CL-F01", "CL-F02", "CL-F03"}
BUGFIX = {"CL-B01", "CL-B02", "CL-B03"}
ISSUE_SECTIONS = {
    "User And Problem",
    "Goal And Value",
    "User Stories Or Bug Observation",
    "Scenarios",
    "Scope",
    "Non-Goals",
    "Acceptance",
    "Known Unknowns",
    "Publication",
}


def _frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.name} must start with YAML front matter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError(f"{path.name} has unclosed YAML front matter")
    value = yaml.safe_load(text[4:end]) or {}
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} front matter must be a mapping")
    return value, text[end + 5 :]


def _section(body: str, heading: str) -> str:
    match = re.search(rf"(?m)^(#{{2,4}})\s+{re.escape(heading)}\s*$", body)
    if not match:
        return ""
    rest = body[match.end() :]
    level = len(match.group(1))
    end = re.search(rf"(?m)^#{{2,{level}}}\s+", rest)
    return (rest[: end.start()] if end else rest).strip()


def _table(body: str, heading: str) -> dict[str, dict[str, str]]:
    lines = [
        line.strip()
        for line in _section(body, heading).splitlines()
        if line.strip().startswith("|")
    ]
    if len(lines) < 2:
        return {}

    def cells(line: str) -> list[str]:
        return [cell.strip().strip("`") for cell in line.strip("|").split("|")]

    headers = cells(lines[0])
    rows: dict[str, dict[str, str]] = {}
    for line in lines[2:]:
        values = cells(line)
        if len(values) == len(headers):
            row = dict(zip(headers, values))
            check_id = row.get("Check ID", "")
            if check_id:
                rows[check_id] = row
    return rows


def evaluate(project_root: Path, intake_slug: str) -> dict[str, object]:
    if not SLUG.fullmatch(intake_slug):
        raise ValueError("intake slug must be lower-kebab and at most 80 characters")
    intake_root = (project_root / ".specify/ai-team/intake" / intake_slug).resolve()
    intake_root.relative_to(project_root.resolve())
    checklist = intake_root / "specify-checklist.md"
    issue_draft = intake_root / "issue-draft.md"
    missing = [path.name for path in (checklist, issue_draft) if not path.is_file()]
    if missing:
        return {"result": "revise", "pending": missing, "next": missing[0]}

    metadata, body = _frontmatter(checklist)
    work_type = str(metadata.get("work_type", "")).strip().lower()
    if (
        metadata.get("schema") != "ai-team-specify-checklist/v1"
        or str(metadata.get("intake_slug", "")).strip() != intake_slug
        or work_type not in {"feature", "new-project", "bugfix"}
    ):
        return {"result": "revise", "pending": ["CL-007"], "next": "CL-007"}

    rows = {}
    for heading in (
        "Common Readiness",
        "Feature Or New Project Readiness",
        "Bugfix Readiness",
    ):
        rows.update(_table(body, heading))
    required = COMMON | (BUGFIX if work_type == "bugfix" else FEATURE)
    pending = []
    for check_id in sorted(required):
        row = rows.get(check_id, {})
        status = row.get("Status", "").strip().lower()
        evidence = row.get("Evidence or answer", "").strip()
        if status != "ready" or not evidence or PLACEHOLDER.search(evidence):
            pending.append(check_id)

    draft_meta, draft_body = _frontmatter(issue_draft)
    sections_ready = all(
        (content := _section(draft_body, heading))
        and not PLACEHOLDER.search(content)
        for heading in ISSUE_SECTIONS
    )
    labels = draft_meta.get("proposed_labels")
    labels = labels if isinstance(labels, list) else []
    expected_type = "type/bug" if work_type == "bugfix" else "type/feature"
    draft_ready = (
        draft_meta.get("schema") == "ai-team-issue-draft/v1"
        and str(draft_meta.get("intake_slug", "")).strip() == intake_slug
        and str(draft_meta.get("work_type", "")).strip().lower() == work_type
        and expected_type in labels
        and "state/draft" in labels
        and len(labels) == 2
        and str(draft_meta.get("target_repository", "")).strip()
        and str(draft_meta.get("privacy_boundary", "")).strip()
        in {"public-safe", "confidential"}
        and str(draft_meta.get("publication_status", "")).strip().lower()
        == "not-published"
        and sections_ready
    )
    if not draft_ready:
        pending.append("issue-draft.md")
    return {
        "result": "ready" if not pending else "revise",
        "pending": pending,
        "next": pending[0] if pending else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--intake-slug", required=True)
    args = parser.parse_args()
    result = evaluate(Path(args.project_root).resolve(), args.intake_slug)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["result"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
