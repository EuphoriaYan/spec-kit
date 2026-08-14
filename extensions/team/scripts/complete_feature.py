#!/usr/bin/env python3
"""Close one Feature from verified merge and release facts."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from feature_records import complete_feature_record


def _console(message: str, *, stream: object = sys.stdout) -> None:
    logger = logging.getLogger(f"{__name__}.console.{id(stream)}")
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.info(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-id", required=True)
    parser.add_argument("--merged-commit", required=True)
    parser.add_argument("--delivered-in", required=True)
    parser.add_argument("--release-evidence", required=True)
    parser.add_argument("--completed-by", required=True)
    parser.add_argument("--completed-at")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        path, record = complete_feature_record(
            args.project_root.resolve(),
            args.feature_id,
            merged_commit=args.merged_commit,
            delivered_in=args.delivered_in,
            release_evidence=args.release_evidence,
            completed_by=args.completed_by,
            completed_at=args.completed_at,
        )
    except (OSError, ValueError) as exc:
        _console(json.dumps({"status": "blocked", "errors": [str(exc)]}, indent=2))
        _console(f"Feature completion failed: {exc}", stream=sys.stderr)
        return 2
    _console(
        json.dumps(
            {
                "status": "done",
                "feature_id": args.feature_id,
                "feature_record": str(path),
                "merged_commit": record["delivery"]["merged_commit"],
                "delivered_in": record["release"]["delivered_in"],
                "release_evidence": record["release"]["evidence"],
                "completed_by": record["completion"]["completed_by"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
