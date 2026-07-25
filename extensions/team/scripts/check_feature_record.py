#!/usr/bin/env python3
"""Deterministically validate a repository Feature Record and lifecycle state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from feature_records import (
    resolve_feature_work_root,
    validate_feature_record,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-id", required=True)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--require-accepted", action="store_true")
    parser.add_argument("--previous-phase")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    try:
        path, record, errors = validate_feature_record(
            project_root,
            args.feature_id,
            require_accepted=args.require_accepted,
            previous_phase=args.previous_phase,
        )
        work_root = resolve_feature_work_root(project_root, args.feature_id)
    except (OSError, UnicodeError, ValueError) as exc:
        errors = [str(exc)]
        path = Path()
        work_root = Path()
        record = {}

    result = {
        "feature_id": args.feature_id,
        "status": "ready" if not errors else "blocked",
        "feature_record": str(path),
        "work_root": str(work_root),
        "acceptance": (record.get("acceptance") or {}).get("status"),
        "delivery_phase": (record.get("delivery") or {}).get("phase"),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        for error in errors:
            print(f"Feature Record check failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
