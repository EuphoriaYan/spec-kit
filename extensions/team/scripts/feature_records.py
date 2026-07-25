"""Resolve and validate repository-versioned Team lifecycle records."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml


SUPPORTED_FORMATS = {"markdown-frontmatter", "yaml", "json"}
HTTP_URL = re.compile(r"^https?://\S+$", re.IGNORECASE)
LOCAL_REVIEW_REVISION = re.compile(
    r"^(?:[0-9a-f]{7,64}|sha256:[0-9a-f]{64})$", re.IGNORECASE
)
ACCEPTANCE_STATES = {"proposed", "accepted", "deferred", "rejected"}
REQUIREMENT_ACCEPTANCE_STATES = {"proposed", "accepted", "working", "rejected"}
DELIVERY_PHASES = {
    "backlog",
    "specifying",
    "planning",
    "tasks-ready",
    "implementing",
    "reviewing",
    "ready-to-merge",
    "done",
    "blocked",
    "cancelled",
}
LEGAL_TRANSITIONS = {
    "backlog": {"specifying", "blocked", "cancelled"},
    "specifying": {"planning", "blocked", "cancelled"},
    "planning": {"tasks-ready", "blocked", "cancelled"},
    "tasks-ready": {"implementing", "planning", "blocked", "cancelled"},
    "implementing": {"reviewing", "blocked", "cancelled"},
    "reviewing": {"implementing", "ready-to-merge", "blocked", "cancelled"},
    "ready-to-merge": {"reviewing", "done", "blocked", "cancelled"},
    "done": set(),
    "blocked": {
        "backlog",
        "specifying",
        "planning",
        "tasks-ready",
        "implementing",
        "reviewing",
        "ready-to-merge",
        "cancelled",
    },
    "cancelled": set(),
}
DEFAULTS = {
    "enabled": True,
    "root": "",
    "recommended_root": "docs/features",
    "location": {
        "status": "pending-confirmation",
        "locked": False,
        "decided_by": "",
        "decided_at": "",
    },
    "catalog_file": "feature-catalog.yml",
    "record_path_template": "{feature_id}.md",
    "format": "markdown-frontmatter",
    "id_pattern": r"^FEAT-[0-9]{3,}$",
    "require_committed_records": True,
}


@dataclass(frozen=True)
class FeatureTracking:
    root: Path
    catalog: Path
    record_template: str
    format: str
    id_pattern: re.Pattern[str]
    work_root_template: str
    require_committed_records: bool


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    return value


def _is_utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.utcoffset() == timedelta(0)


def _load_config(project_root: Path) -> dict[str, Any]:
    path = project_root / ".specify" / "team" / "ai-team-config.yml"
    if not path.is_file():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return _mapping(loaded, "AI Team config")


def _safe_relative(
    project_root: Path, relative_text: str, *, label: str
) -> Path:
    relative = Path(relative_text)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{label} must remain repository-relative")
    root = project_root.resolve()
    candidate = project_root / relative
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} resolves outside the repository") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{label} must not traverse symbolic links")
    return candidate


def load_tracking(project_root: Path) -> FeatureTracking:
    config = _load_config(project_root)
    configured = config.get("feature_tracking") or {}
    configured = _mapping(configured, "feature_tracking")
    values = {**DEFAULTS, **configured}
    work_artifacts = config.get("work_artifacts") or {}
    work_artifacts = _mapping(work_artifacts, "work_artifacts")
    if values.get("enabled") is False:
        raise ValueError("Feature tracking is disabled")
    location = values.get("location") or {}
    location = _mapping(location, "feature_tracking.location")
    root_value = str(values.get("root", "")).strip()
    if (
        not root_value
        or location.get("status") != "confirmed"
        or location.get("locked") is not True
    ):
        recommendation = str(values.get("recommended_root") or "docs/features")
        raise ValueError(
            "Feature Record location has not been confirmed and locked; "
            f"ask the user once (recommended: {recommendation}) and persist the "
            "decision in feature_tracking.root and feature_tracking.location"
        )
    format_name = str(values["format"]).strip()
    if format_name not in SUPPORTED_FORMATS:
        raise ValueError(
            f"unsupported Feature Record format {format_name!r}; "
            f"expected one of {sorted(SUPPORTED_FORMATS)}"
        )
    root = _safe_relative(
        project_root, root_value, label="feature_tracking.root"
    )
    catalog_name = str(values["catalog_file"])
    if Path(catalog_name).is_absolute() or ".." in Path(catalog_name).parts:
        raise ValueError("feature_tracking.catalog_file must stay under its root")
    catalog = _safe_relative(
        project_root,
        str(Path(root_value) / catalog_name),
        label="Feature Catalog path",
    )
    try:
        id_pattern = re.compile(str(values["id_pattern"]))
    except re.error as exc:
        raise ValueError(f"invalid Feature ID pattern: {exc}") from exc
    work_root_template = str(
        work_artifacts.get("feature_path_template") or ".specify/{work_id}"
    )
    if work_root_template.count("{work_id}") != 1:
        raise ValueError(
            "work_artifacts.feature_path_template must contain exactly one {work_id}"
        )
    work_root_template = work_root_template.replace("{work_id}", "{feature_id}")
    return FeatureTracking(
        root=root,
        catalog=catalog,
        record_template=str(values["record_path_template"]),
        format=format_name,
        id_pattern=id_pattern,
        work_root_template=work_root_template,
        require_committed_records=bool(values["require_committed_records"]),
    )


def _render_template(template: str, feature_id: str, *, label: str) -> str:
    if template.count("{feature_id}") != 1:
        raise ValueError(f"{label} must contain exactly one {{feature_id}}")
    return template.replace("{feature_id}", feature_id)


def validate_feature_id(tracking: FeatureTracking, feature_id: str) -> None:
    if not tracking.id_pattern.fullmatch(feature_id):
        raise ValueError(
            f"Feature ID {feature_id!r} does not match "
            f"{tracking.id_pattern.pattern!r}"
        )


def resolve_feature_record(project_root: Path, feature_id: str) -> Path:
    tracking = load_tracking(project_root)
    validate_feature_id(tracking, feature_id)
    rendered = _render_template(
        tracking.record_template, feature_id, label="record_path_template"
    )
    relative = Path(rendered)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Feature Record path must stay under its configured root")
    candidate = _safe_relative(
        project_root,
        str(tracking.root.relative_to(project_root) / relative),
        label="Feature Record path",
    )
    try:
        candidate.resolve(strict=False).relative_to(tracking.root.resolve(strict=False))
    except ValueError as exc:
        raise ValueError("Feature Record path escapes its configured root") from exc
    return candidate


def resolve_feature_work_root(project_root: Path, feature_id: str) -> Path:
    tracking = load_tracking(project_root)
    validate_feature_id(tracking, feature_id)
    rendered = _render_template(
        tracking.work_root_template, feature_id, label="work_root_template"
    )
    target = _safe_relative(project_root, rendered, label="Feature work root")
    specify_root = (project_root / ".specify").resolve(strict=False)
    try:
        target.resolve(strict=False).relative_to(specify_root)
    except ValueError as exc:
        raise ValueError("Feature work root must stay under .specify") from exc
    reserved = {
        "bugfix",
        "extensions",
        "memory",
        "scripts",
        "team",
        "templates",
        "workflows",
    }
    relative = target.resolve(strict=False).relative_to(specify_root)
    if relative.parts and relative.parts[0].lower() in reserved:
        raise ValueError("Feature work root collides with a reserved .specify directory")
    if not target.exists():
        legacy = project_root / ".specify" / "feature" / feature_id
        if legacy.exists():
            return legacy
    return target


def _load_markdown_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("markdown Feature Record must start with YAML frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("markdown Feature Record has unterminated frontmatter")
    loaded = yaml.safe_load(text[4:end]) or {}
    return _mapping(loaded, "record frontmatter")


def validate_local_requirement_record(
    project_root: Path,
    relative_path: str,
    *,
    require_accepted: bool = False,
) -> tuple[Path, dict[str, Any], list[str]]:
    config = _load_config(project_root)
    publishing = config.get("issue_publishing") or {}
    publishing = _mapping(publishing, "issue_publishing")
    fallback = publishing.get("local_requirement_fallback") or {}
    fallback = _mapping(
        fallback, "issue_publishing.local_requirement_fallback"
    )
    if fallback.get("enabled", True) is not True:
        raise ValueError("local Requirement fallback is disabled")
    configured_root = str(fallback.get("root") or "docs/requirements")
    id_pattern_text = str(fallback.get("id_pattern") or r"^REQ-[0-9]{3,}$")
    try:
        id_pattern = re.compile(id_pattern_text)
    except re.error as exc:
        raise ValueError(f"invalid Requirement ID pattern: {exc}") from exc

    path = _safe_relative(
        project_root, relative_path, label="local Requirement Record path"
    )
    fallback_root = _safe_relative(
        project_root, configured_root, label="local Requirement Record root"
    )
    try:
        path.resolve(strict=False).relative_to(fallback_root.resolve(strict=False))
    except ValueError as exc:
        raise ValueError(
            "local Requirement Record must stay under its configured root"
        ) from exc
    if not path.is_file():
        return path, {}, [f"local Requirement Record is missing: {path}"]

    errors: list[str] = []
    try:
        record = _load_markdown_frontmatter(path)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
        return path, {}, [str(exc)]
    if record.get("schema") != "speckit-requirement-record/v1":
        errors.append(
            "local Requirement Record schema must be speckit-requirement-record/v1"
        )
    requirement_id = str(record.get("requirement_id", "")).strip()
    if not id_pattern.fullmatch(requirement_id):
        errors.append("local Requirement Record requirement_id is invalid")
    if path.stem != requirement_id:
        errors.append("local Requirement Record filename must match requirement_id")
    if not str(record.get("title", "")).strip():
        errors.append("local Requirement Record is missing title")
    mode = str(record.get("mode", "")).strip()
    if mode not in {"new-project", "existing-project"}:
        errors.append(
            "local Requirement Record mode must be new-project or existing-project"
        )

    source = record.get("source") or {}
    if not isinstance(source, dict):
        errors.append("local Requirement Record source must be a mapping")
        source = {}
    if source.get("type") != "local-record":
        errors.append("local Requirement Record source.type must be local-record")
    if source.get("publication_attempted") is not True:
        errors.append("local fallback requires a recorded online publication attempt")
    if not str(source.get("fallback_reason", "")).strip():
        errors.append("local fallback requires a concrete publication failure reason")
    if not str(source.get("fallback_selected_by", "")).strip():
        errors.append("local fallback requires the named human who selected it")
    if not _is_utc_timestamp(source.get("fallback_selected_at")):
        errors.append("local fallback requires a valid UTC selection timestamp")
    if str(source.get("issue_url", "")).strip():
        errors.append(
            "local fallback source.issue_url must stay empty until replaced by a verified online authority"
        )

    acceptance = record.get("acceptance") or {}
    if not isinstance(acceptance, dict):
        errors.append("local Requirement Record acceptance must be a mapping")
        acceptance = {}
    status = str(acceptance.get("status", "")).strip()
    if status not in REQUIREMENT_ACCEPTANCE_STATES:
        errors.append("local Requirement Record acceptance.status is not recognized")
    if status in {"accepted", "working"}:
        if not str(acceptance.get("decided_by", "")).strip():
            errors.append("accepted local Requirement is missing acceptance.decided_by")
        if not _is_utc_timestamp(acceptance.get("decided_at")):
            errors.append(
                "accepted local Requirement requires a valid UTC acceptance.decided_at"
            )
    if require_accepted and status not in {"accepted", "working"}:
        errors.append("local Requirement must be accepted before Feature Split")

    architecture = record.get("architecture") or {}
    if not isinstance(architecture, dict):
        errors.append("local Requirement Record architecture must be a mapping")
        architecture = {}
    if mode == "new-project":
        if architecture.get("l0_status") != "accepted":
            errors.append("new-project local Requirement requires accepted L0")
        if not str(architecture.get("l0_path", "")).strip():
            errors.append("new-project local Requirement requires an L0 path")
    return path, record, errors


def load_feature_record(path: Path, format_name: str) -> dict[str, Any]:
    if format_name == "markdown-frontmatter":
        return _load_markdown_frontmatter(path)
    if format_name == "yaml":
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return _mapping(loaded, "Feature Record")
    if format_name == "json":
        loaded = json.loads(path.read_text(encoding="utf-8"))
        return _mapping(loaded, "Feature Record")
    raise ValueError(f"unsupported Feature Record format {format_name!r}")


def _catalog_entries(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    root = _mapping(loaded, "Feature Catalog")
    entries = root.get("features") or []
    if not isinstance(entries, list):
        raise ValueError("Feature Catalog features must be a list")
    return [_mapping(entry, "Feature Catalog entry") for entry in entries]


def validate_transition(previous: str, current: str) -> list[str]:
    if previous == current:
        return []
    if previous not in DELIVERY_PHASES or current not in DELIVERY_PHASES:
        return ["delivery phase is not recognized"]
    if current not in LEGAL_TRANSITIONS[previous]:
        return [f"illegal delivery transition: {previous} -> {current}"]
    return []


def validate_feature_record(
    project_root: Path,
    feature_id: str,
    *,
    require_accepted: bool = False,
    previous_phase: str | None = None,
) -> tuple[Path, dict[str, Any], list[str]]:
    tracking = load_tracking(project_root)
    path = resolve_feature_record(project_root, feature_id)
    errors: list[str] = []
    if not path.is_file():
        return path, {}, [f"Feature Record is missing: {path}"]
    try:
        record = load_feature_record(path, tracking.format)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        return path, {}, [str(exc)]

    if record.get("feature_id") != feature_id:
        errors.append("Feature Record feature_id does not match requested Feature ID")
    for field in ("title", "parent_requirement"):
        if not str(record.get(field, "")).strip():
            errors.append(f"Feature Record is missing {field}")

    acceptance = record.get("acceptance") or {}
    if not isinstance(acceptance, dict):
        errors.append("acceptance must be a mapping")
        acceptance = {}
    acceptance_status = str(acceptance.get("status", ""))
    if acceptance_status not in ACCEPTANCE_STATES:
        errors.append("acceptance.status is not recognized")
    if acceptance_status == "accepted":
        if not str(acceptance.get("decided_by", "")).strip():
            errors.append("accepted Feature is missing acceptance.decided_by")
        if not str(acceptance.get("decided_at", "")).strip():
            errors.append("accepted Feature is missing acceptance.decided_at")
    if require_accepted and acceptance_status != "accepted":
        errors.append("Feature must be accepted before entering SDD")

    delivery = record.get("delivery") or {}
    if not isinstance(delivery, dict):
        errors.append("delivery must be a mapping")
        delivery = {}
    phase = str(delivery.get("phase", ""))
    if phase not in DELIVERY_PHASES:
        errors.append("delivery.phase is not recognized")
    if previous_phase is not None:
        errors.extend(validate_transition(previous_phase, phase))

    architecture = record.get("architecture_impact") or {}
    if not isinstance(architecture, dict):
        errors.append("architecture_impact must be a mapping")
        architecture = {}
    level = str(architecture.get("level", ""))
    if level not in {"none", "L0", "L1", "L2", "pending"}:
        errors.append("architecture_impact.level is not recognized")
    update_required = architecture.get("update_required")
    if not isinstance(update_required, bool):
        errors.append("architecture_impact.update_required must be boolean")
    affected_files = architecture.get("affected_files") or []
    if not isinstance(affected_files, list) or not all(
        isinstance(item, str) and item.strip() for item in affected_files
    ):
        errors.append("architecture_impact.affected_files must be a list of paths")
        affected_files = []
    unsafe_architecture_paths = [
        item
        for item in affected_files
        if Path(item).is_absolute() or ".." in Path(item).parts
    ]
    if unsafe_architecture_paths:
        errors.append("architecture_impact.affected_files must stay repository-relative")
    if update_required and not affected_files:
        errors.append("architecture update requires affected_files")
    if update_required is False:
        if affected_files:
            errors.append("no architecture update must not list affected_files")
        if not str(architecture.get("reason", "")).strip():
            errors.append("no architecture update requires an explicit reason")
    if phase in {
        "tasks-ready",
        "implementing",
        "reviewing",
        "ready-to-merge",
        "done",
    } and level == "pending":
        errors.append("architecture impact must be resolved before implementation")

    entries = _catalog_entries(tracking.catalog)
    matches = [entry for entry in entries if entry.get("id") == feature_id]
    if len(matches) != 1:
        errors.append("Feature Catalog must contain exactly one matching Feature ID")
    elif str(matches[0].get("record", "")).replace("\\", "/") != str(
        path.relative_to(project_root)
    ).replace("\\", "/"):
        errors.append("Feature Catalog record path does not match configured Feature Record")

    if phase in {"ready-to-merge", "done"}:
        dod = record.get("definition_of_done") or {}
        if not isinstance(dod, dict):
            errors.append("definition_of_done must be a mapping")
            dod = {}
        for key in (
            "code_complete",
            "tests_complete",
            "evidence_complete",
            "architecture_synchronized",
            "review_passed",
        ):
            if dod.get(key) is not True:
                errors.append(f"Definition of Done is incomplete: {key}")
        pull_request = str(delivery.get("pull_request", "")).strip()
        review_target = delivery.get("review_target") or {}
        if not isinstance(review_target, dict):
            errors.append("delivery.review_target must be a mapping")
            review_target = {}
        target_type = str(review_target.get("type", "")).strip()
        target_url = str(review_target.get("url", "")).strip()
        target_revision = str(review_target.get("revision", "")).strip()
        if pull_request:
            if not HTTP_URL.fullmatch(pull_request):
                errors.append("delivery.pull_request must be a verified HTTP(S) URL")
            if target_type and target_type != "pull-request":
                errors.append(
                    "an online pull request requires delivery.review_target.type pull-request"
                )
            if target_url and target_url != pull_request:
                errors.append(
                    "delivery.review_target.url must match delivery.pull_request"
                )
        else:
            if target_type != "local-diff":
                errors.append(
                    f"{phase} Feature without an online pull request requires "
                    "delivery.review_target.type local-diff"
                )
            if target_url:
                errors.append("a local-diff review target must not contain a URL")
            if not LOCAL_REVIEW_REVISION.fullmatch(target_revision):
                errors.append(
                    "a local-diff review target requires an immutable Git or sha256 revision"
                )
    if phase == "done":
        release = record.get("release") or {}
        if not isinstance(release, dict) or not str(
            release.get("delivered_in", "")
        ).strip():
            errors.append("done Feature is missing release.delivered_in")
        if not str(delivery.get("merged_commit", "")).strip():
            errors.append("done Feature is missing delivery.merged_commit")

    return path, record, errors
