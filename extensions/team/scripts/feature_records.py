"""Resolve and validate repository-versioned Team lifecycle records."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from architecture_terms import normalize_architecture_level


SUPPORTED_FORMATS = {"markdown-frontmatter", "yaml", "json"}
HTTP_URL = re.compile(r"^https?://\S+$", re.IGNORECASE)
LOCAL_REVIEW_REVISION = re.compile(
    r"^(?:[0-9a-f]{7,64}|sha256:[0-9a-f]{64})$", re.IGNORECASE
)
ACCEPTANCE_STATES = {"proposed", "accepted", "deferred", "rejected"}
BEHAVIOR_ACCEPTANCE_STATES = {"proposed", "accepted"}
BEHAVIOR_CONFIRMATION_MODES = {"required", "advisory", "disabled"}
COMPLETION_VALIDATION_MODES = {"required", "legacy-compatible"}
COMPLETION_GIT_VERIFICATION_MODES = {"best-effort", "strict"}
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
    behavior_confirmation_mode: str
    completion_validation_mode: str
    completion_git_verification_mode: str


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
    behavior_confirmation = configured.get("behavior_confirmation")
    if behavior_confirmation is None:
        # Compatibility default for repositories created before this policy
        # existed. Newly installed configs explicitly select `required`.
        behavior_confirmation_mode = "advisory"
    else:
        behavior_confirmation = _mapping(
            behavior_confirmation,
            "feature_tracking.behavior_confirmation",
        )
        behavior_confirmation_mode = str(
            behavior_confirmation.get("mode", "")
        ).strip()
        if behavior_confirmation_mode not in BEHAVIOR_CONFIRMATION_MODES:
            raise ValueError(
                "feature_tracking.behavior_confirmation.mode must be one of "
                f"{sorted(BEHAVIOR_CONFIRMATION_MODES)}"
            )
    completion = configured.get("completion")
    if completion is None:
        # Compatibility default for repositories that already contain `done`
        # records created before release/completion evidence was introduced.
        completion_validation_mode = "legacy-compatible"
        completion_git_verification_mode = "best-effort"
    else:
        completion = _mapping(completion, "feature_tracking.completion")
        completion_validation_mode = str(
            completion.get("validation", "required")
        ).strip()
        completion_git_verification_mode = str(
            completion.get("git_verification", "best-effort")
        ).strip()
        if completion_validation_mode not in COMPLETION_VALIDATION_MODES:
            raise ValueError(
                "feature_tracking.completion.validation must be one of "
                f"{sorted(COMPLETION_VALIDATION_MODES)}"
            )
        if (
            completion_git_verification_mode
            not in COMPLETION_GIT_VERIFICATION_MODES
        ):
            raise ValueError(
                "feature_tracking.completion.git_verification must be one of "
                f"{sorted(COMPLETION_GIT_VERIFICATION_MODES)}"
            )
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
    format_name = str(values.get("format", "")).strip()
    if format_name not in SUPPORTED_FORMATS:
        raise ValueError(
            f"unsupported Feature Record format {format_name!r}; "
            f"expected one of {sorted(SUPPORTED_FORMATS)}"
        )
    root = _safe_relative(
        project_root, root_value, label="feature_tracking.root"
    )
    catalog_name = str(values.get("catalog_file", ""))
    if Path(catalog_name).is_absolute() or ".." in Path(catalog_name).parts:
        raise ValueError("feature_tracking.catalog_file must stay under its root")
    catalog = _safe_relative(
        project_root,
        str(Path(root_value) / catalog_name),
        label="Feature Catalog path",
    )
    try:
        id_pattern = re.compile(str(values.get("id_pattern", "")))
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
        record_template=str(values.get("record_path_template", "")),
        format=format_name,
        id_pattern=id_pattern,
        work_root_template=work_root_template,
        require_committed_records=bool(values.get("require_committed_records", False)),
        behavior_confirmation_mode=behavior_confirmation_mode,
        completion_validation_mode=completion_validation_mode,
        completion_git_verification_mode=completion_git_verification_mode,
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


def _markdown_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("markdown Feature Record must start with YAML frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("markdown Feature Record has unterminated frontmatter")
    return text[end + 4 :]


def _markdown_section_has_content(body: str, heading: str) -> bool:
    match = re.search(
        rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        body,
    )
    if not match:
        return False
    content = match.group(1).strip()
    return bool(content and content not in {"-", "TBD", "TODO"})


def _feature_behavior_errors(
    path: Path, record: dict[str, Any], format_name: str
) -> list[str]:
    if format_name == "markdown-frontmatter":
        body = _markdown_body(path)
        errors = []
        if not _markdown_section_has_content(body, "User Stories"):
            errors.append("Feature Record User Stories must be written back by Specify")
        if not _markdown_section_has_content(body, "Verification"):
            errors.append("Feature Record Verification must be written back by Specify")
        return errors
    errors = []
    user_stories = record.get("user_stories") or []
    verification = record.get("verification") or []
    if not isinstance(user_stories, list) or not any(
        isinstance(item, str) and item.strip() for item in user_stories
    ):
        errors.append("Feature Record user_stories must be written back by Specify")
    if not isinstance(verification, list) or not any(
        isinstance(item, str) and item.strip() for item in verification
    ):
        errors.append("Feature Record verification must be written back by Specify")
    return errors


def _write_markdown_frontmatter(path: Path, record: dict[str, Any]) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path} must start with YAML frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError(f"{path} has unterminated frontmatter")
    body = text[end + 4 :]
    rendered = yaml.safe_dump(
        record,
        sort_keys=False,
        allow_unicode=True,
    )
    path.write_text(f"---\n{rendered}---{body}", encoding="utf-8")


def _write_record(path: Path, record: dict[str, Any], format_name: str) -> None:
    if format_name == "markdown-frontmatter":
        _write_markdown_frontmatter(path, record)
    elif format_name == "yaml":
        path.write_text(
            yaml.safe_dump(record, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    elif format_name == "json":
        path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    else:
        raise ValueError(f"unsupported record format {format_name!r}")


def _decision_time(value: str | None) -> str:
    if value:
        if not _is_utc_timestamp(value):
            raise ValueError("decided_at must be an ISO-8601 UTC timestamp")
        return value.strip()
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _record_human_acceptance(
    path: Path,
    record: dict[str, Any],
    decided_by: str,
    *,
    decided_at: str | None = None,
    format_name: str = "markdown-frontmatter",
) -> dict[str, Any]:
    actor = decided_by.strip()
    if not actor:
        raise ValueError("decided_by must name the human who approved the record")
    acceptance = record.get("acceptance") or {}
    acceptance = _mapping(acceptance, "acceptance")
    current = str(acceptance.get("status", "")).strip()
    if current == "accepted":
        if str(acceptance.get("decided_by", "")).strip() != actor:
            raise ValueError(
                "record is already accepted by another decision authority"
            )
        return record
    if current != "proposed":
        raise ValueError(
            f"only a proposed record can be verbally accepted (current: {current or 'missing'})"
        )
    record["acceptance"] = {
        **acceptance,
        "status": "accepted",
        "decided_by": actor,
        "decided_at": _decision_time(decided_at),
        "decision_source": "conversation",
    }
    _write_record(path, record, format_name)
    return record


def accept_local_requirement_record(
    project_root: Path,
    relative_path: str,
    decided_by: str,
    *,
    decided_at: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Persist an explicit human conversation decision on a local Requirement."""
    path, record, errors = validate_local_requirement_record(
        project_root,
        relative_path,
    )
    if errors:
        raise ValueError("; ".join(errors))
    updated = _record_human_acceptance(
        path,
        record,
        decided_by,
        decided_at=decided_at,
    )
    return path, updated


def accept_feature_record(
    project_root: Path,
    feature_id: str,
    decided_by: str,
    *,
    decided_at: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Persist an explicit human conversation decision on a Feature Record."""
    path, record, errors = validate_feature_record(project_root, feature_id)
    if errors:
        raise ValueError("; ".join(errors))
    tracking = load_tracking(project_root)
    updated = _record_human_acceptance(
        path,
        record,
        decided_by,
        decided_at=decided_at,
        format_name=tracking.format,
    )
    return path, updated


def accept_feature_behavior(
    project_root: Path,
    feature_id: str,
    decided_by: str,
    *,
    decided_at: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Persist human confirmation of Specify's detailed Feature behavior."""
    path, record, errors = validate_feature_record(
        project_root, feature_id, require_accepted=True
    )
    tracking = load_tracking(project_root)
    if tracking.behavior_confirmation_mode == "disabled":
        raise ValueError("detailed behavior confirmation is disabled by policy")
    errors = [
        error
        for error in errors
        if not error.startswith("detailed behavior must be accepted")
    ]
    errors.extend(_feature_behavior_errors(path, record, tracking.format))
    phase = str((record.get("delivery") or {}).get("phase", ""))
    if phase != "specifying":
        errors.append(
            "detailed behavior can only be accepted while delivery.phase is specifying"
        )
    if errors:
        raise ValueError("; ".join(dict.fromkeys(errors)))
    actor = decided_by.strip()
    if not actor:
        raise ValueError("decided_by must name the human who confirmed the behavior")
    acceptance = record.get("behavior_acceptance") or {"status": "proposed"}
    acceptance = _mapping(acceptance, "behavior_acceptance")
    current = str(acceptance.get("status", "")).strip()
    if current == "accepted":
        if str(acceptance.get("decided_by", "")).strip() != actor:
            raise ValueError(
                "detailed behavior is already accepted by another decision authority"
            )
        return path, record
    if current != "proposed":
        raise ValueError(
            "only proposed detailed behavior can be accepted "
            f"(current: {current or 'missing'})"
        )
    record["behavior_acceptance"] = {
        **acceptance,
        "status": "accepted",
        "decided_by": actor,
        "decided_at": _decision_time(decided_at),
        "decision_source": "conversation",
    }
    _write_record(path, record, tracking.format)
    return path, record


def _verified_repository_commit(
    project_root: Path, revision: str, *, mode: str
) -> tuple[str, bool]:
    candidate = revision.strip()
    if not LOCAL_REVIEW_REVISION.fullmatch(candidate) or candidate.startswith("sha256:"):
        raise ValueError("merged_commit must be a Git commit revision")
    resolved = subprocess.run(
        ["git", "rev-parse", "--verify", f"{candidate}^{{commit}}"],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if resolved.returncode != 0:
        if mode == "strict":
            raise ValueError("merged_commit does not resolve in the current repository")
        if len(candidate) not in {40, 64}:
            raise ValueError(
                "an unresolved merged_commit must be a full 40- or 64-character hash"
            )
        return candidate.lower(), False
    full_revision = resolved.stdout.strip()
    # A post-release backfill may run from a maintenance branch or detached
    # checkout. Resolving the immutable commit is useful evidence; ancestry to
    # the operator's current HEAD is not a release invariant.
    return full_revision, True


def _verified_repository_ref(
    project_root: Path, ref_name: str, *, mode: str
) -> tuple[str, bool]:
    ref = ref_name.strip()
    if (
        not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", ref)
        or ".." in ref
        or ref.endswith("/")
    ):
        raise ValueError("release tag is not a safe Git ref name")
    resolved = subprocess.run(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if resolved.returncode != 0:
        if mode == "strict":
            raise ValueError("release tag does not resolve in the current repository")
        return ref, False
    full_revision = resolved.stdout.strip()
    return full_revision, True


def complete_feature_record(
    project_root: Path,
    feature_id: str,
    *,
    merged_commit: str,
    delivered_in: str,
    release_evidence: str,
    completed_by: str,
    completed_at: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Close a reviewed Feature from already-existing merge/release facts."""
    actor = completed_by.strip()
    release_name = delivered_in.strip()
    evidence = release_evidence.strip()
    if not actor:
        raise ValueError("completed_by must name the human closing the Feature")
    if not release_name:
        raise ValueError("delivered_in must name the delivered release")
    if not (HTTP_URL.fullmatch(evidence) or evidence.startswith("git-tag:")):
        raise ValueError("release_evidence must be an HTTP(S) URL or git-tag:<tag>")
    tracking = load_tracking(project_root)
    git_mode = tracking.completion_git_verification_mode
    full_revision, commit_is_local = _verified_repository_commit(
        project_root, merged_commit, mode=git_mode
    )
    if evidence.startswith("git-tag:"):
        tag = evidence.removeprefix("git-tag:").strip()
        if not tag:
            raise ValueError("git-tag release evidence is missing its tag")
        tag_commit, tag_is_local = _verified_repository_ref(
            project_root, tag, mode=git_mode
        )
        if commit_is_local and tag_is_local:
            contains = subprocess.run(
                ["git", "merge-base", "--is-ancestor", full_revision, tag_commit],
                cwd=project_root,
                text=True,
                capture_output=True,
                check=False,
            )
            if contains.returncode != 0:
                raise ValueError("release tag does not contain merged_commit")

    path, record, errors = validate_feature_record(
        project_root, feature_id, require_accepted=True
    )
    phase = str((record.get("delivery") or {}).get("phase", ""))
    if phase != "ready-to-merge":
        errors.append("Feature must be ready-to-merge before completion")
    if errors:
        raise ValueError("; ".join(dict.fromkeys(errors)))

    original = path.read_bytes()
    delivery = _mapping(record.get("delivery") or {}, "delivery")
    release = _mapping(record.get("release") or {}, "release")
    record["delivery"] = {
        **delivery,
        "phase": "done",
        "merged_commit": full_revision,
    }
    record["release"] = {
        **release,
        "delivered_in": release_name,
        "evidence": evidence,
    }
    record["completion"] = {
        "completed_by": actor,
        "completed_at": _decision_time(completed_at),
        "evidence_source": "post-merge-release-backfill",
    }
    try:
        _write_record(path, record, tracking.format)
        _, checked, completion_errors = validate_feature_record(
            project_root,
            feature_id,
            require_accepted=True,
            previous_phase="ready-to-merge",
        )
        if completion_errors:
            raise ValueError("; ".join(completion_errors))
    except Exception:
        path.write_bytes(original)
        raise
    return path, checked


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
    except (OSError, ValueError, yaml.YAMLError) as exc:
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
            errors.append(
                "new-project local Requirement requires accepted top-level design (L0)"
            )
        if not str(architecture.get("l0_path", "")).strip():
            errors.append(
                "new-project local Requirement requires a top-level design (L0) path"
            )
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
    except (OSError, ValueError, yaml.YAMLError) as exc:
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

    behavior_acceptance = record.get("behavior_acceptance")
    if behavior_acceptance is None:
        # Existing backlog/specifying records migrate as unconfirmed behavior.
        behavior_acceptance = {"status": "proposed"}
    elif not isinstance(behavior_acceptance, dict):
        errors.append("behavior_acceptance must be a mapping")
        behavior_acceptance = {}
    behavior_status = str(behavior_acceptance.get("status", ""))
    if behavior_status not in BEHAVIOR_ACCEPTANCE_STATES:
        errors.append("behavior_acceptance.status is not recognized")
    if behavior_status == "accepted":
        if not str(behavior_acceptance.get("decided_by", "")).strip():
            errors.append(
                "accepted detailed behavior is missing behavior_acceptance.decided_by"
            )
        if not _is_utc_timestamp(behavior_acceptance.get("decided_at")):
            errors.append(
                "accepted detailed behavior requires a valid UTC "
                "behavior_acceptance.decided_at"
            )
        errors.extend(_feature_behavior_errors(path, record, tracking.format))
    if (
        tracking.behavior_confirmation_mode == "required"
        and phase
        in DELIVERY_PHASES - {"backlog", "specifying", "blocked", "cancelled"}
    ):
        if behavior_status != "accepted":
            errors.append(
                "detailed behavior must be accepted before leaving specifying"
            )

    ownership = record.get("ownership") or {}
    if not isinstance(ownership, dict):
        errors.append("ownership must be a mapping when present")
    else:
        collaborators = ownership.get("collaborators") or []
        if not isinstance(collaborators, list) or not all(
            isinstance(item, str) and item.strip() for item in collaborators
        ):
            errors.append("ownership.collaborators must be a list of names")

    shared_contracts = record.get("shared_contracts") or []
    if not isinstance(shared_contracts, list) or not all(
        isinstance(item, str) and item.strip() for item in shared_contracts
    ):
        errors.append("shared_contracts must be a list of repository-relative paths")
        shared_contracts = []
    for contract_path in shared_contracts:
        try:
            resolved_contract = _safe_relative(
                project_root, contract_path, label="shared contract path"
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if phase in DELIVERY_PHASES - {"backlog", "specifying", "blocked", "cancelled"}:
            if not resolved_contract.is_file():
                errors.append(f"shared contract is missing: {contract_path}")

    architecture = record.get("architecture_impact") or {}
    if not isinstance(architecture, dict):
        errors.append("architecture_impact must be a mapping")
        architecture = {}
    level = normalize_architecture_level(architecture.get("level", ""))
    if level is None:
        errors.append(
            "architecture_impact.level is not recognized; use none, pending, "
            "top-level design (L0), module design (L1), or interface and data "
            "structure design (L2)"
        )
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
        completion = record.get("completion") or {}
        if not isinstance(release, dict):
            errors.append("release must be a mapping")
            release = {}
        if not isinstance(completion, dict):
            errors.append("completion must be a mapping")
            completion = {}
        delivered_in = str(release.get("delivered_in", "")).strip()
        merged_commit = str(delivery.get("merged_commit", "")).strip()
        if not delivered_in:
            errors.append("done Feature is missing release.delivered_in")
        if not merged_commit:
            errors.append("done Feature is missing delivery.merged_commit")
        new_completion_values = (
            str(release.get("evidence", "")).strip(),
            str(completion.get("completed_by", "")).strip(),
            str(completion.get("completed_at", "")).strip(),
        )
        legacy_done = (
            tracking.completion_validation_mode == "legacy-compatible"
            and not any(new_completion_values)
        )
        if not legacy_done:
            if not new_completion_values[0]:
                errors.append("done Feature is missing release.evidence")
            if not new_completion_values[1]:
                errors.append("done Feature is missing completion.completed_by")
            if not _is_utc_timestamp(completion.get("completed_at")):
                errors.append(
                    "done Feature requires a valid UTC completion.completed_at"
                )

    return path, record, errors
