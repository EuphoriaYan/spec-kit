#!/usr/bin/env python3
"""Validate an AI Team Permission Envelope without granting permission."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import yaml

from feature_records import resolve_feature_record
from work_item_paths import resolve_work_root


VALID_STATUSES = {"ready", "pending-review", "approved", "blocked", "expired"}
VALID_MODES = {"analysis", "implementation", "verification", "submission"}
VALID_ENFORCEMENT = {"policy-only", "agent-native", "wrapper-enforced"}
CAPABILITY_KEYS = {"read_paths", "write_paths", "commands", "network"}


def _console(message: str) -> None:
    logger = logging.getLogger(f"{__name__}.console.{id(sys.stdout)}")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.info(message)


def _mapping(value: Any, field: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{field} must be a mapping")
        return {}
    return value


def _string_list(value: Any, field: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        errors.append(f"{field} must be a list of non-empty strings")
        return []
    return value


def _safe_relative_path(value: str) -> bool:
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    return (
        bool(normalized)
        and not path.is_absolute()
        and not PureWindowsPath(value).is_absolute()
        and ".." not in path.parts
        and not normalized.startswith("~")
        and not any(character in normalized for character in "*?[]")
    )


def _utc_timestamp(value: Any, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty ISO 8601 UTC timestamp")
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} must be a valid ISO 8601 UTC timestamp")
        return None
    if parsed.utcoffset() != timedelta(0):
        errors.append(f"{field} must use UTC")
        return None
    return parsed


def validate_envelope(
    path: Path,
    *,
    work_id: str,
    mode: str,
    require_approved: bool = False,
    require_authorized: bool = False,
    required_write_paths: list[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"missing Permission Envelope: {path}"]
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [f"cannot read Permission Envelope: {exc}"]

    root = _mapping(document, "document", errors)
    if root.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    if str(root.get("work_id", "")) != work_id:
        errors.append(f"work_id must equal {work_id}")
    if root.get("mode") != mode:
        errors.append(f"mode must equal {mode}")

    status = root.get("status")
    if status not in VALID_STATUSES:
        errors.append(
            "status must be ready, pending-review, approved, blocked, or expired"
        )
    if require_approved and status != "approved":
        errors.append("status must be approved")
    approval_required = _string_list(
        root.get("approval_required"), "approval_required", errors
    )
    if require_authorized and status not in {"ready", "approved"}:
        errors.append("status must be ready or approved for this operation")
    if status == "ready" and approval_required:
        errors.append("ready envelopes cannot contain approval_required triggers")
    if status == "pending-review" and not approval_required:
        errors.append("pending-review envelopes require approval_required triggers")
    updated_at = _utc_timestamp(root.get("updated_at"), "updated_at", errors)
    if status == "approved":
        if not str(root.get("approved_by", "")).strip():
            errors.append("approved envelopes require approved_by")
        approved_at = _utc_timestamp(
            root.get("approved_at"), "approved_at", errors
        )
        if (
            approved_at is not None
            and updated_at is not None
            and updated_at < approved_at
        ):
            errors.append("updated_at cannot be earlier than approved_at")
    elif str(root.get("approved_by", "")).strip() or str(
        root.get("approved_at", "")
    ).strip():
        errors.append("non-approved envelopes must clear approved_by and approved_at")
    if status == "blocked":
        blockers = _string_list(root.get("blockers"), "blockers", errors)
        if not blockers:
            errors.append("blocked envelopes require at least one blocker")

    if root.get("enforcement_mode") not in VALID_ENFORCEMENT:
        errors.append(
            "enforcement_mode must be policy-only, agent-native, or wrapper-enforced"
        )
    if not str(root.get("integration", "")).strip():
        errors.append("integration must be a non-empty string")

    capabilities: dict[str, dict[str, list[str]]] = {}
    for section_name in ("allow", "deny"):
        section = _mapping(root.get(section_name), section_name, errors)
        capabilities[section_name] = {}
        for key in CAPABILITY_KEYS:
            values = _string_list(section.get(key), f"{section_name}.{key}", errors)
            capabilities[section_name][key] = values
            if key.endswith("paths"):
                for value in values:
                    if not _safe_relative_path(value):
                        errors.append(
                            f"{section_name}.{key} contains unsafe path: {value}"
                        )

    def covers(container: str, required: str) -> bool:
        container_path = PurePosixPath(container.replace("\\", "/"))
        required_path = PurePosixPath(required.replace("\\", "/"))
        return (
            container_path == required_path
            or container_path in required_path.parents
        )

    for required_path in required_write_paths or []:
        allowed = capabilities.get("allow", {}).get("write_paths", [])
        denied = capabilities.get("deny", {}).get("write_paths", [])
        if not any(covers(value, required_path) for value in allowed):
            errors.append(
                "allow.write_paths must authorize required lifecycle path: "
                f"{required_path}"
            )
        if any(covers(value, required_path) for value in denied):
            errors.append(
                "deny.write_paths blocks required lifecycle path: "
                f"{required_path}"
            )

    runtime = _mapping(root.get("runtime"), "runtime", errors)
    if not isinstance(runtime.get("verified"), bool):
        errors.append("runtime.verified must be true or false")
    _string_list(runtime.get("gaps"), "runtime.gaps", errors)
    if (
        root.get("enforcement_mode") == "policy-only"
        and runtime.get("verified") is True
    ):
        errors.append("policy-only enforcement cannot claim runtime verification")
    if root.get("enforcement_mode") in {"agent-native", "wrapper-enforced"}:
        if not str(runtime.get("adapter", "")).strip():
            errors.append("enforced modes require runtime.adapter")
        if runtime.get("verified") is not True:
            errors.append("enforced modes require runtime.verified: true")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--work-type", required=True)
    parser.add_argument("--work-id", required=True)
    parser.add_argument("--mode", required=True, choices=sorted(VALID_MODES))
    parser.add_argument("--require-approved", action="store_true")
    parser.add_argument("--require-authorized", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    root = resolve_work_root(project_root, args.work_type, args.work_id)
    required_write_paths: list[str] = []
    if args.work_type == "feature" and args.mode in {"implementation", "verification"}:
        try:
            feature_record = resolve_feature_record(project_root, args.work_id)
        except ValueError:
            feature_record = None
        if feature_record is not None and feature_record.is_file():
            required_write_paths.append(
                feature_record.relative_to(project_root).as_posix()
            )
    envelope = root / "permission-envelope.yml"
    errors = validate_envelope(
        envelope,
        work_id=args.work_id,
        mode=args.mode,
        require_approved=args.require_approved,
        require_authorized=args.require_authorized,
        required_write_paths=required_write_paths,
    )
    if errors:
        _console("Permission Envelope Check: blocked")
        for error in errors:
            _console(f"- {error}")
        return 1
    _console("Permission Envelope Check: ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
