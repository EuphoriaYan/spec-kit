#!/usr/bin/env python3
"""Generate a deterministic readiness check for AI Team Plan and Tasks."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_permission_envelope import validate_envelope
from work_item_paths import normalize_category, resolve_work_root


VALIDATOR = "ai-team-plan-and-task-check/v6"
SPEC_SCHEMA = "ai-team-feature-spec/v1"
PLAN_SCHEMA = "ai-team-plan-and-task/v5"
ACCEPTED_STATUSES = {"accept", "accepted", "working"}
PLACEHOLDER = re.compile(r"(?i)\b(?:TBD|TODO|FIXME)\b|<[^>]+>|path/to/file")
ID_SPLIT = re.compile(r"\s*(?:,|;|<br\s*/?>)\s*", re.IGNORECASE)
HTTP_URL = re.compile(r"^https?://\S+$", re.IGNORECASE)
EMPTY_REFERENCES = {"", "-", "none", "n/a", "not-applicable"}
RESPONSIBILITIES = {"business-software", "framework", "external-prerequisite"}
PR_STRATEGIES = {"business-only", "framework-only", "single-pr", "linked-prs"}
ARCHITECTURE_LEVELS = {"none", "l0", "l1", "l2"}


@dataclass(frozen=True)
class Check:
    check_id: str
    result: str
    detail: str


def _frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.name} must start with YAML front matter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError(f"{path.name} has unclosed YAML front matter")
    data = yaml.safe_load(text[4:end]) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} front matter must be a mapping")
    return data, text[end + 5 :]


def _headings(body: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in re.finditer(r"(?m)^#{2,4}\s+(.+?)\s*$", body)
    }


def _section(body: str, heading: str) -> str:
    match = re.search(rf"(?m)^(#{{2,4}})\s+{re.escape(heading)}\s*$", body)
    if not match:
        return ""
    rest = body[match.end() :]
    level = len(match.group(1))
    end = re.search(rf"(?m)^#{{2,{level}}}\s+", rest)
    return (rest[: end.start()] if end else rest).strip()


def _table(body: str, heading: str) -> list[dict[str, str]]:
    section = _section(body, heading)
    lines = [
        line.strip() for line in section.splitlines() if line.strip().startswith("|")
    ]
    if len(lines) < 2:
        return []

    def cells(line: str) -> list[str]:
        return [cell.strip().strip("`") for cell in line.strip("|").split("|")]

    headers = cells(lines[0])
    if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells(lines[1])):
        return []
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        values = cells(line)
        if len(values) == len(headers):
            rows.append(dict(zip(headers, values)))
    return rows


def _ids(value: str) -> list[str]:
    return [part.strip() for part in ID_SPLIT.split(value) if part.strip()]


def _references(value: str) -> list[str]:
    return [item for item in _ids(value) if item.lower() not in EMPTY_REFERENCES]


def _acyclic(task_ids: list[str], dependencies: dict[str, list[str]]) -> bool:
    pending = {task_id: set(dependencies.get(task_id, [])) for task_id in task_ids}
    while pending:
        ready = {task_id for task_id, required in pending.items() if not required}
        if not ready:
            return False
        pending = {
            task_id: required - ready
            for task_id, required in pending.items()
            if task_id not in ready
        }
    return True


def _status(value: object) -> str:
    return str(value or "").strip().lower().removeprefix("status/")


def _list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _meaningful(section: str) -> bool:
    content = re.sub(r"<!--.*?-->", "", section, flags=re.DOTALL).strip()
    return bool(content) and not PLACEHOLDER.search(content)


def _meaningful_value(value: object) -> bool:
    text = str(value or "").strip()
    return (
        text.lower() not in EMPTY_REFERENCES
        and not PLACEHOLDER.search(text)
    )


def _evidence_file(project_root: Path, value: object) -> bool:
    raw = str(value or "").strip()
    path = Path(raw)
    if not raw or path.is_absolute() or ".." in path.parts:
        return False
    resolved = (project_root / path).resolve(strict=False)
    try:
        resolved.relative_to(project_root)
    except ValueError:
        return False
    return resolved.is_file()


def _decision_evidence(value: object) -> bool:
    return bool(HTTP_URL.fullmatch(str(value or "").strip()))


def _utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.utcoffset() == timedelta(0)


def _recorded_acceptance(
    project_root: Path, value: object
) -> tuple[bool, str]:
    raw = str(value or "").strip()
    if not _evidence_file(project_root, raw):
        return False, ""
    path = project_root / raw
    try:
        if path.suffix.lower() == ".json":
            record = json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix.lower() in {".yml", ".yaml"}:
            record = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        else:
            record, _ = _frontmatter(path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError, yaml.YAMLError):
        return False, ""
    if not isinstance(record, dict):
        return False, ""
    acceptance = record.get("acceptance") or {}
    if not isinstance(acceptance, dict):
        return False, ""
    actor = str(acceptance.get("decided_by", "")).strip()
    valid = (
        _status(acceptance.get("status")) in {"accepted", "working"}
        and _named_decider(actor)
        and _utc_timestamp(acceptance.get("decided_at"))
    )
    return valid, actor


def _named_decider(value: object) -> bool:
    return str(value or "").strip().lower() not in {
        "",
        "yes",
        "approved",
        "pending",
        "tbd",
        "not-required",
    }


def _git_changed_paths(
    project_root: Path, source_revision: str
) -> tuple[list[str], str | None]:
    if not source_revision:
        return [], "implementation scope requires plan source_revision"
    commands = (
        ["git", "diff", "--name-only", "--no-renames", source_revision, "--"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    paths: set[str] = set()
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            return [], f"{' '.join(command[:2])} failed: {detail}"
        paths.update(
            line.strip().replace("\\", "/")
            for line in completed.stdout.splitlines()
            if line.strip()
        )
    return sorted(paths), None


def _path_is_declared(project_root: Path, changed: str, declared: str) -> bool:
    changed_path = changed.strip().replace("\\", "/").strip("/")
    declared_path = declared.strip().replace("\\", "/").strip("/")
    if not changed_path or not declared_path:
        return False
    if changed_path == declared_path:
        return True
    candidate = project_root / declared_path
    return (
        (declared.endswith(("/", "\\")) or candidate.is_dir())
        and changed_path.startswith(declared_path + "/")
    )


def evaluate(
    project_root: Path,
    work_type: str,
    work_id: str,
    *,
    implementation_scope: bool = False,
) -> tuple[str, str]:
    category = normalize_category(work_type)
    if category != "feature":
        raise ValueError(
            "Plan-and-Task supports Feature work only; use Assess -> Fix -> Review for Bugfix"
        )
    work_root = resolve_work_root(project_root, category, work_id)
    spec_path = work_root / "spec.md"
    plan_path = work_root / "plan-and-task.md"
    checks: list[Check] = []

    def record(check_id: str, ok: bool, detail: str, *, blocked: bool = False) -> None:
        checks.append(
            Check(check_id, "PASS" if ok else ("BLOCK" if blocked else "FAIL"), detail)
        )

    required_paths = [spec_path, plan_path]
    missing = [path.name for path in required_paths if not path.is_file()]
    record(
        "ARTIFACTS",
        not missing,
        "required artifacts exist" if not missing else f"missing: {', '.join(missing)}",
        blocked=True,
    )

    spec_meta: dict[str, Any] = {}
    plan_meta: dict[str, Any] = {}
    declared_paths: list[str] = []
    spec_body = ""
    plan_body = ""
    parse_errors: list[str] = []
    if not missing:
        parse_targets = [(spec_path, "spec"), (plan_path, "plan")]
        for path, target in parse_targets:
            try:
                metadata, body = _frontmatter(path)
                if target == "spec":
                    spec_meta, spec_body = metadata, body
                else:
                    plan_meta, plan_body = metadata, body
            except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
                parse_errors.append(str(exc))
    record(
        "FRONTMATTER",
        not parse_errors and not missing,
        "front matter parsed" if not parse_errors else "; ".join(parse_errors),
    )

    if not missing and not parse_errors:
        try:
            plan_category = normalize_category(str(plan_meta.get("work_type", "")))
            spec_category = normalize_category(str(spec_meta.get("work_type", "")))
        except ValueError:
            spec_category = plan_category = "invalid"
        issue_source = plan_meta.get("issue_source")
        issue_source = issue_source if isinstance(issue_source, dict) else {}
        primary_authority = str(plan_meta.get("primary_issue", "")).strip()
        feature_record = str(plan_meta.get("feature_record", "")).strip()
        record_backed = bool(feature_record)
        online_authority = _decision_evidence(primary_authority)
        local_authority = _evidence_file(project_root, primary_authority)
        online_source_ok = all(
            str(issue_source.get(key, "")).strip()
            for key in ("repository", "issue_number", "updated_at", "body_hash")
        )
        source_ok = (
            online_source_ok
            if online_authority
            else (
                local_authority
                and str(issue_source.get("kind", "")).strip().lower()
                == "local-record"
            )
        )
        record_acceptance_ok, record_decider = _recorded_acceptance(
            project_root, feature_record
        )
        identity_ok = (
            plan_meta.get("schema") == PLAN_SCHEMA
            and str(plan_meta.get("work_id", "")) == work_id
            and spec_category == category
            and plan_category == category
            and (online_authority or local_authority)
            and source_ok
            and (
                not record_backed
                or (
                    _evidence_file(project_root, feature_record)
                    and spec_meta.get("feature_record") == feature_record
                )
            )
            and spec_meta.get("schema") == SPEC_SCHEMA
            and str(spec_meta.get("work_id", "")) == work_id
            and spec_meta.get("primary_issue") == plan_meta.get("primary_issue")
        )
        record(
            "IDENTITY", identity_ok, "schema, work ID, type, and primary Issue agree"
        )

        online_state_ok = (
            _status(plan_meta.get("issue_status")) in ACCEPTED_STATUSES
        )
        accepted = (
            record_acceptance_ok
            and (online_state_ok if online_authority else local_authority)
            if record_backed
            else online_state_ok
        )
        if record_backed and online_authority:
            state_detail = (
                "online parent Requirement is accepted and the Feature Record "
                "contains a named, timestamped human acceptance"
                if accepted
                else (
                    "online parent Requirement must be status/accept or "
                    "status/working, and the Feature Record must contain human "
                    "acceptance"
                )
            )
        elif record_backed:
            state_detail = (
                "local Requirement and Feature Record contain persisted human acceptance"
                if accepted
                else (
                    "local Requirement and Feature Record must contain "
                    "persisted human acceptance"
                )
            )
        else:
            state_detail = (
                "Plan records status/accept or status/working"
                if accepted
                else "Issue must be status/accept or status/working"
            )
        record(
            "ISSUE_STATE",
            accepted,
            state_detail,
            blocked=True,
        )
        approval = plan_meta.get("approval")
        approval = approval if isinstance(approval, dict) else {}
        approval_decider = str(approval.get("decided_by", "")).strip()
        approval_ok = accepted and _named_decider(approval_decider) and (
            (
                record_backed
                and str(approval.get("decision_source", "")).strip().lower()
                in {"conversation", "local-record"}
                and str(approval.get("evidence_record", "")).strip()
                == feature_record
                and approval_decider == record_decider
            )
            or (
                not record_backed
                and _decision_evidence(approval.get("evidence_url"))
            )
        )
        record(
            "ISSUE_APPROVAL_EVIDENCE",
            approval_ok,
            (
                "named human acceptance is recorded in the local Feature Record"
                if record_backed
                else "human decision reference is structurally recorded; remote authenticity is not asserted"
            )
            if approval_ok
            else (
                "record-backed work requires a matching named decider, local evidence record, and conversation/local-record source"
                if record_backed
                else "accepted online work requires a named decider and an http(s) decision URL"
            ),
            blocked=True,
        )

        story_ids = set(re.findall(r"(?m)^#{3,4}\s+(US-\d+)\b", spec_body))
        known_acceptance = set(re.findall(r"\bVER-\d+\b", spec_body))
        missing_spec = sorted({"User Stories"} - _headings(spec_body))
        spec_ok = (
            not missing_spec
            and _meaningful(_section(spec_body, "User Stories"))
            and bool(story_ids)
            and bool(known_acceptance)
        )
        record(
            "SPEC_STRUCTURE",
            spec_ok,
            "Feature Spec contains User Stories and Verification IDs"
            if spec_ok
            else "Feature Spec requires User Stories and VER-### Verification IDs",
        )

        plan_common = {
            "Plan (HLD)",
            "Source And Code Graph Evidence",
            "Requirement Responsibility And PR Strategy",
            "Module Change Plan",
            "Architecture And Contract Impact",
            "Declared Change Scope",
            "Implementation Plan",
            "Parallel Development Strategy",
            "Development Chain",
            "Plan Review Decision",
            "Tasks (LLD)",
            "Task Index",
            "Task Details",
            "Minimum Self-Tests",
            "Compatibility Migration And Rollback",
            "Risks And Deviations",
        }
        plan_specific = {"Feature Delivery Plan", "User Story Delivery Mapping"}
        missing_plan = sorted((plan_common | plan_specific) - _headings(plan_body))
        record(
            "PLAN_STRUCTURE",
            not missing_plan,
            "required common and type-specific Plan sections exist"
            if not missing_plan
            else f"missing headings: {', '.join(missing_plan)}",
        )
        plan_leaf_sections = {
            "Source And Code Graph Evidence",
            "Requirement Responsibility And PR Strategy",
            "Architecture And Contract Impact",
            "Declared Change Scope",
            "Implementation Plan",
            "Parallel Development Strategy",
            "Development Chain",
            "Plan Review Decision",
            "Compatibility Migration And Rollback",
            "Risks And Deviations",
        } | {"User Story Delivery Mapping"}
        empty_plan = sorted(
            heading
            for heading in plan_leaf_sections
            if heading in _headings(plan_body)
            and not _meaningful(_section(plan_body, heading))
        )
        record(
            "PLAN_CONTENT",
            not empty_plan,
            "required Plan sections contain non-placeholder content"
            if not empty_plan
            else f"empty or placeholder sections: {', '.join(empty_plan)}",
        )

        declared_paths = _list(plan_meta.get("declared_paths"))
        modules = _list(plan_meta.get("affected_modules"))
        safe_paths = bool(declared_paths) and all(
            not Path(path).is_absolute() and ".." not in Path(path).parts
            for path in declared_paths
        )
        record(
            "DECLARED_SCOPE",
            safe_paths and bool(modules),
            "declared paths and affected modules are non-empty and project-relative",
        )

        architecture = plan_meta.get("architecture_impact")
        architecture = architecture if isinstance(architecture, dict) else {}
        architecture_level = str(architecture.get("level", "")).strip().lower()
        architecture_update = architecture.get("update_required")
        architecture_files = _list(architecture.get("affected_files"))
        safe_architecture_files = all(
            not Path(path).is_absolute() and ".." not in Path(path).parts
            for path in architecture_files
        )
        architecture_shape_ok = (
            architecture_level in ARCHITECTURE_LEVELS
            and isinstance(architecture_update, bool)
            and safe_architecture_files
        )
        if architecture_shape_ok and architecture_update:
            architecture_shape_ok = (
                architecture_level != "none"
                and bool(architecture_files)
                and set(architecture_files).issubset(declared_paths)
            )
        elif architecture_shape_ok:
            architecture_shape_ok = (
                not architecture_files
                and _meaningful_value(architecture.get("reason"))
            )
        record(
            "ARCHITECTURE_DOD",
            architecture_shape_ok,
            "architecture impact has an explicit level and synchronized-file plan"
            if architecture_shape_ok
            else "architecture_impact requires none/L0/L1/L2, a boolean update_required, safe declared affected_files when updating, or a meaningful no-update reason",
            blocked=True,
        )

        impact = plan_meta.get("impact_analysis")
        impact = impact if isinstance(impact, dict) else {}
        graph = impact.get("code_graph")
        graph = graph if isinstance(graph, dict) else {}
        impact_flags_ok = isinstance(impact.get("cross_module"), bool) and isinstance(
            impact.get("class_changes"), bool
        )
        record(
            "IMPACT_FLAGS",
            impact_flags_ok,
            "cross-module and class-change impact are explicitly declared"
            if impact_flags_ok
            else "impact_analysis must declare boolean cross_module and class_changes flags",
        )
        contract_change = str(impact.get("public_contract_change", "")).strip().lower()
        source_revision = str(plan_meta.get("source_revision", "")).strip()
        graph_ok = (
            graph.get("kind") == "codegraph"
            and _evidence_file(project_root, graph.get("evidence_path"))
            and _meaningful(source_revision)
            and str(graph.get("source_revision", "")).strip() == source_revision
        )
        record(
            "IMPACT_EVIDENCE",
            graph_ok,
            "versioned CodeGraph evidence file exists"
            if graph_ok
            else "impact_analysis.code_graph requires codegraph evidence, an existing evidence_path, and matching source_revision",
            blocked=True,
        )
        contract_authority = impact.get("contract_authority")
        contract_authority = (
            contract_authority if isinstance(contract_authority, dict) else {}
        )
        contract_ok = bool(contract_change)
        if contract_change != "none":
            contract_ok = (
                contract_ok
                and _named_decider(contract_authority.get("decided_by"))
                and _decision_evidence(contract_authority.get("evidence_url"))
            )
        record(
            "CONTRACT_AUTHORITY",
            contract_ok,
            "contract impact and required owner decision reference are recorded"
            if contract_ok
            else "public contract change requires a named architecture or contract authority and an http(s) decision URL",
            blocked=True,
        )

        responsibility = _table(
            plan_body, "Requirement Responsibility And PR Strategy"
        )
        responsibility_columns = {
            "User Story ID",
            "Responsibility",
            "Target repository",
            "Delivery unit",
            "Dependency",
            "Review route",
        }
        responsibility_shape = bool(responsibility) and responsibility_columns.issubset(
            responsibility[0]
        )
        strategy = plan_meta.get("delivery_strategy")
        strategy = strategy if isinstance(strategy, dict) else {}
        strategy_name = str(strategy.get("pr_strategy", "")).strip()
        repositories = set(_list(strategy.get("repositories")))
        domains = {
            row["Responsibility"].strip() for row in responsibility
        } if responsibility_shape else set()
        target_repositories = {
            row["Target repository"].strip() for row in responsibility
        } if responsibility_shape else set()
        delivery_units = {
            row["Delivery unit"].strip() for row in responsibility
        } if responsibility_shape else set()
        base_responsibility_ok = (
            responsibility_shape
            and {row["User Story ID"].strip() for row in responsibility} == story_ids
            and len(responsibility) == len(story_ids)
            and bool(domains)
            and domains.issubset(RESPONSIBILITIES)
            and strategy_name in PR_STRATEGIES
            and repositories == target_repositories
            and all(
                _meaningful_value(row["Target repository"])
                and _meaningful_value(row["Delivery unit"])
                and _meaningful_value(row["Review route"])
                for row in responsibility
            )
        )
        strategy_ok = base_responsibility_ok
        strategy_detail = "requirements are classified and the PR boundary is coherent"
        if base_responsibility_ok and "external-prerequisite" in domains:
            strategy_ok = False
            strategy_detail = (
                "external prerequisites must be resolved or remain BLOCKED before a ready implementation plan"
            )
        elif base_responsibility_ok and domains == {"business-software"}:
            strategy_ok = strategy_name == "business-only"
        elif base_responsibility_ok and domains == {"framework"}:
            strategy_ok = strategy_name == "framework-only"
        elif base_responsibility_ok and {"business-software", "framework"}.issubset(domains):
            if strategy_name == "single-pr":
                framework_review = strategy.get("framework_review")
                framework_review = (
                    framework_review if isinstance(framework_review, dict) else {}
                )
                strategy_ok = (
                    len(repositories) == 1
                    and len(delivery_units) == 1
                    and impact.get("cross_module") is True
                    and strategy.get("shared_release_and_rollback") is True
                    and _meaningful_value(strategy.get("atomic_reason"))
                    and _named_decider(framework_review.get("decided_by"))
                    and _decision_evidence(framework_review.get("evidence_url"))
                )
                strategy_detail = (
                    "combined business/framework PR has one repository, one atomic delivery unit, shared rollback, and owner evidence"
                )
            elif strategy_name == "linked-prs":
                strategy_ok = len(delivery_units) >= 2 and any(
                    _references(row["Dependency"]) for row in responsibility
                )
                strategy_detail = (
                    "business/framework work uses linked delivery units with explicit dependency order"
                )
            else:
                strategy_ok = False
        record(
            "RESPONSIBILITY_BOUNDARY",
            strategy_ok,
            strategy_detail
            if strategy_ok
            else "classify every User Story and use a valid business-only, framework-only, atomic single-pr, or linked-prs boundary",
            blocked=not base_responsibility_ok or "external-prerequisite" in domains,
        )

        stage = str(plan_meta.get("planning_stage", "")).strip().lower()
        plan_review = plan_meta.get("plan_review")
        plan_review = plan_review if isinstance(plan_review, dict) else {}
        handoff_ok = (
            stage == "ready-for-check"
            and plan_review.get("decision") == "continue-to-tasks"
            and _named_decider(plan_review.get("decided_by"))
        )
        record(
            "PLAN_TASK_HANDOFF",
            handoff_ok,
            "a named human approved Task decomposition and the artifact is ready for check"
            if handoff_ok
            else "final check requires ready-for-check plus a named continue-to-tasks decision",
            blocked=True,
        )

        module_plan = _table(plan_body, "Module Change Plan")
        tasks = _table(plan_body, "Task Index")
        task_details = _table(plan_body, "Task Details")
        tests = _table(plan_body, "Minimum Self-Tests")
        module_columns = {
            "Module",
            "Module path",
            "Current responsibility",
            "Planned change",
            "Contract impact",
            "Review route (optional)",
        }
        task_columns = {
            "Task ID",
            "Status",
            "Module",
            "Requirement IDs",
            "Planned paths",
            "Depends on",
            "Parallel group",
            "Self-test IDs",
            "LLD summary",
        }
        detail_columns = {
            "Task ID",
            "Goal and non-goals",
            "Design and data flow",
            "Inputs and contracts",
            "Completion criteria",
        }
        test_columns = {
            "Test ID",
            "Type",
            "Scenario or fixture",
            "Command or procedure",
            "Expected evidence",
        }
        module_shape = bool(module_plan) and module_columns.issubset(module_plan[0])
        task_shape = bool(tasks) and task_columns.issubset(tasks[0])
        detail_shape = bool(task_details) and detail_columns.issubset(task_details[0])
        test_shape = bool(tests) and test_columns.issubset(tests[0])
        record(
            "MODULE_PLAN",
            module_shape,
            "per-module HLD table is parseable"
            if module_shape
            else "Module Change Plan must use the Team table columns",
        )
        record(
            "TASK_TABLE",
            task_shape,
            "single-module Task index is parseable"
            if task_shape
            else "Task Index must use the Team table columns",
        )
        task_status_ok = task_shape and all(
            re.fullmatch(r"\[(?: |x|X)\]", row["Status"].strip()) for row in tasks
        )
        record(
            "TASK_STATUS",
            task_status_ok,
            "every Task has an unchecked or completed Status checkbox"
            if task_status_ok
            else "Task Status must be [ ] or [x]",
        )
        record(
            "TASK_DETAILS",
            detail_shape,
            "Task LLD detail table is parseable"
            if detail_shape
            else "Task Details must use the Team table columns",
        )
        record(
            "SELF_TEST_TABLE",
            test_shape,
            "minimum self-test table is parseable"
            if test_shape
            else "Minimum Self-Tests must use the Team table columns",
        )

        if module_shape and task_shape and detail_shape and test_shape:
            task_ids = [row["Task ID"] for row in tasks]
            test_ids = [row["Test ID"] for row in tests]
            module_ids = [row["Module"] for row in module_plan]
            detail_ids = [row["Task ID"] for row in task_details]
            task_modules = {row["Task ID"]: row["Module"] for row in tasks}
            dependencies = {
                row["Task ID"]: _references(row["Depends on"]) for row in tasks
            }

            module_plan_ok = (
                len(module_ids) == len(set(module_ids))
                and set(module_ids) == set(modules)
                and all(
                    bool(row["Module path"].strip())
                    and not Path(row["Module path"]).is_absolute()
                    and ".." not in Path(row["Module path"]).parts
                    for row in module_plan
                )
                and all(
                    not PLACEHOLDER.search(" ".join(row.values()))
                    and all(value.strip() for value in row.values())
                    for row in module_plan
                )
                and set(task_modules.values()) == set(modules)
            )
            record(
                "MODULE_SCOPE",
                module_plan_ok,
                "affected modules map to bounded module paths and Tasks"
                if module_plan_ok
                else "each affected module needs one safe module path and at least one Task",
                blocked=True,
            )

            mappings_ok = (
                len(task_ids) == len(set(task_ids))
                and len(test_ids) == len(set(test_ids))
                and len(detail_ids) == len(set(detail_ids))
                and set(detail_ids) == set(task_ids)
                and all(
                    bool(_references(row["Requirement IDs"]))
                    and set(_references(row["Requirement IDs"])).issubset(known_acceptance)
                    for row in tasks
                )
                and all(
                    bool(_references(row["Self-test IDs"]))
                    and set(_references(row["Self-test IDs"])).issubset(test_ids)
                    for row in tasks
                )
                and all(
                    bool(_references(row["Planned paths"]))
                    and set(_references(row["Planned paths"])).issubset(declared_paths)
                    for row in tasks
                )
                and all(row["Module"] in modules for row in tasks)
                and all(
                    not PLACEHOLDER.search(" ".join(row.values()))
                    and all(value.strip() for value in row.values())
                    for row in tasks + task_details + tests
                )
            )
            record(
                "TRACEABILITY",
                mappings_ok,
                "Tasks map to Verification IDs, declared paths, and defined self-tests"
                if mappings_ok
                else "Task/test IDs, Verification mapping, declared paths, or required values are inconsistent",
            )

            planned_task_paths = {
                path for row in tasks for path in _references(row["Planned paths"])
            }
            architecture_task_ok = (
                architecture_shape_ok
                and (
                    not architecture_update
                    or set(architecture_files).issubset(planned_task_paths)
                )
            )
            record(
                "ARCHITECTURE_TASKS",
                architecture_task_ok,
                "every architecture-description update is assigned to a verified Task"
                if architecture_task_ok
                else "every architecture_impact.affected_files path must be declared and assigned to a Task",
                blocked=True,
            )

            dependency_refs_ok = all(
                task_id not in required and set(required).issubset(task_ids)
                for task_id, required in dependencies.items()
            )
            dependency_graph_ok = dependency_refs_ok and _acyclic(task_ids, dependencies)
            chain = _section(plan_body, "Development Chain")
            dependency_ids = {
                item
                for task_id, required in dependencies.items()
                for item in [task_id, *required]
                if required
            }
            chain_ok = not dependency_ids or all(item in chain for item in dependency_ids)
            record(
                "TASK_DEPENDENCIES",
                dependency_graph_ok and chain_ok,
                "Task dependency graph is acyclic and its serial chain is explained"
                if dependency_graph_ok and chain_ok
                else "dependencies must reference Tasks, remain acyclic, and be explained in Development Chain",
            )

            parallel_paths: dict[tuple[str, str], str] = {}
            parallel_conflict = False
            for row in tasks:
                for path in _references(row["Planned paths"]):
                    key = (row["Parallel group"], path)
                    if key in parallel_paths:
                        parallel_conflict = True
                    parallel_paths[key] = row["Task ID"]
            record(
                "PARALLEL_SCOPE",
                not parallel_conflict,
                "Tasks in the same parallel group do not claim the same path"
                if not parallel_conflict
                else "Tasks in one parallel group must not edit the same declared path",
            )

            delivery = _table(plan_body, "User Story Delivery Mapping")
            columns = {"User Story ID", "Verification IDs", "Task IDs"}
            delivery_ok = bool(delivery) and columns.issubset(delivery[0])
            if delivery_ok:
                mapped_acceptance = {
                    item
                    for row in delivery
                    for item in _ids(row["Verification IDs"])
                }
                delivery_ok = (
                    {row["User Story ID"] for row in delivery} == story_ids
                    and mapped_acceptance == known_acceptance
                    and all(
                        set(_ids(row["Task IDs"])).issubset(task_ids)
                        for row in delivery
                    )
                    and set(task_ids)
                    == {item for row in delivery for item in _ids(row["Task IDs"])}
                )
            record(
                "DELIVERY_MAPPING",
                delivery_ok,
                "Feature delivery mapping covers the declared work"
                if delivery_ok
                else "Feature User Stories are not fully mapped to Tasks and tests",
            )

        compatibility_ok = _meaningful(
            _section(plan_body, "Compatibility Migration And Rollback")
        )
        record(
            "COMPATIBILITY_ROLLBACK",
            compatibility_ok,
            "compatibility and rollback are explicitly documented"
            if compatibility_ok
            else "compatibility and rollback section is missing or contains placeholders",
        )

    if implementation_scope:
        source_revision = str(plan_meta.get("source_revision", "")).strip()
        changed_paths, diff_error = _git_changed_paths(project_root, source_revision)
        undeclared = [
            path
            for path in changed_paths
            if not any(
                _path_is_declared(project_root, path, declared)
                for declared in declared_paths
            )
        ]
        permission_errors = (
            validate_envelope(
                work_root / "permission-envelope.yml",
                work_id=work_id,
                mode="implementation",
                require_authorized=True,
                required_write_paths=changed_paths,
            )
            if not diff_error
            else []
        )
        scope_ok = (
            bool(changed_paths)
            and not diff_error
            and not undeclared
            and not permission_errors
        )
        if diff_error:
            scope_detail = diff_error
        elif not changed_paths:
            scope_detail = "no implementation changes found from plan source_revision"
        elif undeclared:
            scope_detail = "changed paths outside declared scope: " + ", ".join(
                undeclared
            )
        elif permission_errors:
            scope_detail = "Permission Envelope rejects changed paths: " + "; ".join(
                permission_errors
            )
        else:
            scope_detail = (
                f"{len(changed_paths)} changed path(s) fit plan declared_paths "
                "and the implementation Permission Envelope"
            )
        record(
            "IMPLEMENTATION_DIFF_SCOPE",
            scope_ok,
            scope_detail,
            blocked=True,
        )

    result = (
        "blocked"
        if any(item.result == "BLOCK" for item in checks)
        else ("revise" if any(item.result == "FAIL" for item in checks) else "ready")
    )
    stage = str(plan_meta.get("planning_stage", "unknown"))
    lines = [
        "# Plan And Task Check",
        "",
        "This file is generated. Do not hand-edit it.",
        "",
        f"- Result: {result}",
        f"- Work ID: {work_id}",
        f"- Work type: {category}",
        f"- Planning stage: {stage}",
        f"- Validator: {VALIDATOR}",
        "",
        "## Deterministic Checks",
        "",
        "| Check ID | Result | Detail |",
        "|---|---|---|",
    ]
    lines.extend(
        f"| {item.check_id} | {item.result} | {item.detail.replace('|', '/')} |"
        for item in checks
    )
    findings = [item for item in checks if item.result != "PASS"]
    lines.extend(["", "## Required Revisions", ""])
    lines.extend([f"- {item.check_id}: {item.detail}" for item in findings] or ["None"])
    return result, "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--work-type", required=True)
    parser.add_argument("--work-id", required=True)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the generated check file is stale",
    )
    parser.add_argument(
        "--implementation-scope",
        action="store_true",
        help=(
            "compare tracked, staged, unstaged, and untracked implementation "
            "paths with plan declared_paths and the implementation Permission "
            "Envelope from source_revision"
        ),
    )
    args = parser.parse_args()

    try:
        root = args.project_root.resolve()
        result, rendered = evaluate(
            root,
            args.work_type,
            args.work_id,
            implementation_scope=args.implementation_scope,
        )
        output = (
            resolve_work_root(root, args.work_type, args.work_id)
            / "plan-and-task-check.md"
        )
        if args.check:
            if (
                not output.is_file()
                or output.read_text(encoding="utf-8").replace("\r\n", "\n") != rendered
            ):
                print(
                    f"AI Team Plan-and-Task check is stale: {output}", file=sys.stderr
                )
                return 2
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
        print(f"AI Team Plan-and-Task check: {result} ({output})")
        return 0 if result == "ready" else 2
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
        print(f"AI Team Plan-and-Task check failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
