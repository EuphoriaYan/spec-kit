#!/usr/bin/env python3
"""Validate deterministic/evaluable tutorial steps and four-state evidence."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml


SCHEMA = "ai-team-evidence-steps/v1"
STEP_ID = re.compile(r"STEP-\d{3}")
KINDS = {"deterministic", "evaluable"}
RESULTS = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}
PLACEHOLDER = re.compile(r"(?i)\b(?:TBD|TODO|FIXME)\b|<[^>]+>")


def _text(value: object) -> str:
    return str(value or "").strip()


def _meaningful(value: object) -> bool:
    text = _text(value)
    return bool(text) and not PLACEHOLDER.search(text)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def validate(path: Path) -> list[str]:
    data: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return ["root must be a mapping"]
    errors: list[str] = []
    if data.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    if not _meaningful(data.get("revision")):
        errors.append("revision must identify the tested source state")
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        return [*errors, "steps must be a non-empty list"]

    seen: set[str] = set()
    for index, raw in enumerate(steps, start=1):
        prefix = f"steps[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        step_id = _text(raw.get("id"))
        if not STEP_ID.fullmatch(step_id):
            errors.append(f"{prefix}.id must match STEP-###")
        elif step_id in seen:
            errors.append(f"{prefix}.id is duplicated: {step_id}")
        seen.add(step_id)
        if raw.get("kind") not in KINDS:
            errors.append(f"{prefix}.kind must be deterministic or evaluable")
        for field in ("title", "action", "expected", "actual", "evidence", "recovery"):
            if not _meaningful(raw.get(field)):
                errors.append(f"{prefix}.{field} must be objective and non-empty")
        if not _string_list(raw.get("prerequisites")):
            errors.append(f"{prefix}.prerequisites must be a non-empty string list")
        result = _text(raw.get("result")).upper()
        if result not in RESULTS:
            errors.append(f"{prefix}.result must be PASS, FAIL, BLOCKED, or NOT_RUN")
        missing = raw.get("missing_condition")
        if result in {"BLOCKED", "NOT_RUN"} and not _meaningful(missing):
            errors.append(f"{prefix}.missing_condition is required for {result}")
        if result in {"PASS", "FAIL"} and _meaningful(missing):
            errors.append(f"{prefix}.missing_condition must be empty for {result}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        errors = validate(args.manifest.resolve())
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        print(f"Evidence step check failed: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 2
    print(f"Evidence step check: PASS ({args.manifest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
