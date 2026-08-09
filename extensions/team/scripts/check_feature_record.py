#!/usr/bin/env python3
"""Deterministically validate a repository Team lifecycle record."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from feature_records import (
    accept_feature_record,
    accept_local_requirement_record,
    resolve_feature_work_root,
    validate_feature_record,
    validate_local_requirement_record,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    identity = parser.add_mutually_exclusive_group(required=True)
    identity.add_argument("--feature-id")
    identity.add_argument("--requirement-record")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--require-accepted", action="store_true")
    parser.add_argument(
        "--record-verbal-acceptance-by",
        help="Persist an explicit current-conversation human approval before checking",
    )
    parser.add_argument(
        "--decided-at",
        help="Optional ISO-8601 UTC decision time (defaults to now)",
    )
    parser.add_argument("--previous-phase")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    try:
        acceptance_recorded = False
        if args.decided_at and not args.record_verbal_acceptance_by:
            raise ValueError(
                "--decided-at requires --record-verbal-acceptance-by"
            )
        if args.record_verbal_acceptance_by and args.previous_phase:
            raise ValueError(
                "verbal acceptance cannot be combined with --previous-phase"
            )
        if args.record_verbal_acceptance_by:
            if args.requirement_record:
                accept_local_requirement_record(
                    project_root,
                    args.requirement_record,
                    args.record_verbal_acceptance_by,
                    decided_at=args.decided_at,
                )
            else:
                accept_feature_record(
                    project_root,
                    args.feature_id,
                    args.record_verbal_acceptance_by,
                    decided_at=args.decided_at,
                )
            acceptance_recorded = True
        if args.requirement_record:
            if args.previous_phase:
                raise ValueError(
                    "--previous-phase applies only to Feature Records"
                )
            path, record, errors = validate_local_requirement_record(
                project_root,
                args.requirement_record,
                require_accepted=args.require_accepted,
            )
            work_root = Path()
        else:
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
        acceptance_recorded = False

    result = {
        "record_type": "requirement" if args.requirement_record else "feature",
        "feature_id": args.feature_id,
        "requirement_id": record.get("requirement_id"),
        "status": "ready" if not errors else "blocked",
        "record": str(path),
        "feature_record": str(path) if args.feature_id else "",
        "requirement_record": str(path) if args.requirement_record else "",
        "work_root": str(work_root),
        "acceptance": (record.get("acceptance") or {}).get("status"),
        "acceptance_recorded": acceptance_recorded,
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
