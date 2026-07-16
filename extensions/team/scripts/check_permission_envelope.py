#!/usr/bin/env python3
"""Validate an AI Team Permission Envelope without granting permission."""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import yaml

from work_item_paths import resolve_work_root


VALID_STATUSES = {"pending-review", "approved", "blocked", "expired"}
VALID_MODES = {"analysis", "implementation", "verification", "submission"}
VALID_ENFORCEMENT = {"policy-only", "agent-native", "wrapper-enforced"}
CAPABILITY_KEYS = {"read_paths", "write_paths", "commands", "network"}


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


def validate_envelope(
    path: Path,
    *,
    work_id: str,
    mode: str,
    require_approved: bool = False,
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
        errors.append("status must be pending-review, approved, blocked, or expired")
    if require_approved and status != "approved":
        errors.append("status must be approved")
    if status == "approved":
        if not str(root.get("approved_by", "")).strip():
            errors.append("approved envelopes require approved_by")
        if not str(root.get("approved_at", "")).strip():
            errors.append("approved envelopes require approved_at")
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

    for section_name in ("allow", "deny"):
        section = _mapping(root.get(section_name), section_name, errors)
        for key in CAPABILITY_KEYS:
            values = _string_list(section.get(key), f"{section_name}.{key}", errors)
            if key.endswith("paths"):
                for value in values:
                    if not _safe_relative_path(value):
                        errors.append(
                            f"{section_name}.{key} contains unsafe path: {value}"
                        )

    _string_list(root.get("approval_required"), "approval_required", errors)
    runtime = _mapping(root.get("runtime"), "runtime", errors)
    if not isinstance(runtime.get("verified"), bool):
        errors.append("runtime.verified must be true or false")
    _string_list(runtime.get("gaps"), "runtime.gaps", errors)
    if root.get("enforcement_mode") == "policy-only" and runtime.get("verified") is True:
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
    args = parser.parse_args()

    root = resolve_work_root(
        Path(args.project_root).resolve(), args.work_type, args.work_id
    )
    envelope = root / "permission-envelope.yml"
    errors = validate_envelope(
        envelope,
        work_id=args.work_id,
        mode=args.mode,
        require_approved=args.require_approved,
    )
    if errors:
        print("Permission Envelope Check: blocked")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Permission Envelope Check: ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
