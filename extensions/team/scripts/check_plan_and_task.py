#!/usr/bin/env python3
"""Generate a deterministic readiness check for AI Team Plan and Tasks."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from work_item_paths import normalize_category, resolve_work_root


VALIDATOR = "ai-team-plan-and-task-check/v4"
SPEC_SCHEMA = "ai-team-feature-spec/v1"
PLAN_SCHEMA = "ai-team-plan-and-task/v4"
ACCEPTED_STATUSES = {"accept", "working"}
PLACEHOLDER = re.compile(r"(?i)\b(?:TBD|TODO|FIXME)\b|<[^>]+>|path/to/file")
ID_SPLIT = re.compile(r"\s*(?:,|;|<br\s*/?>)\s*", re.IGNORECASE)
HTTP_URL = re.compile(r"^https?://\S+$", re.IGNORECASE)
EMPTY_REFERENCES = {"", "-", "none", "n/a", "not-applicable"}


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


def _named_decider(value: object) -> bool:
    return str(value or "").strip().lower() not in {
        "",
        "yes",
        "approved",
        "pending",
        "tbd",
        "not-required",
    }


def evaluate(project_root: Path, work_type: str, work_id: str) -> tuple[str, str]:
    category = normalize_category(work_type)
    work_root = resolve_work_root(project_root, category, work_id)
    spec_path = work_root / "spec.md"
    plan_path = work_root / "plan-and-task.md"
    checks: list[Check] = []

    def record(check_id: str, ok: bool, detail: str, *, blocked: bool = False) -> None:
        checks.append(
            Check(check_id, "PASS" if ok else ("BLOCK" if blocked else "FAIL"), detail)
        )

    required_paths = [plan_path]
    if category == "feature":
        required_paths.insert(0, spec_path)
    missing = [path.name for path in required_paths if not path.is_file()]
    record(
        "ARTIFACTS",
        not missing,
        "required artifacts exist" if not missing else f"missing: {', '.join(missing)}",
        blocked=True,
    )

    spec_meta: dict[str, Any] = {}
    plan_meta: dict[str, Any] = {}
    spec_body = ""
    plan_body = ""
    parse_errors: list[str] = []
    if not missing:
        parse_targets = [(plan_path, "plan")]
        if category == "feature":
            parse_targets.insert(0, (spec_path, "spec"))
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
            spec_category = (
                normalize_category(str(spec_meta.get("work_type", "")))
                if category == "feature"
                else category
            )
        except ValueError:
            spec_category = plan_category = "invalid"
        issue_source = plan_meta.get("issue_source")
        issue_source = issue_source if isinstance(issue_source, dict) else {}
        source_ok = all(
            str(issue_source.get(key, "")).strip()
            for key in ("repository", "issue_number", "updated_at", "body_hash")
        )
        identity_ok = (
            plan_meta.get("schema") == PLAN_SCHEMA
            and str(plan_meta.get("work_id", "")) == work_id
            and spec_category == category
            and plan_category == category
            and _decision_evidence(plan_meta.get("primary_issue"))
            and source_ok
            and (
                category != "feature"
                or (
                    spec_meta.get("schema") == SPEC_SCHEMA
                    and str(spec_meta.get("work_id", "")) == work_id
                    and spec_meta.get("primary_issue") == plan_meta.get("primary_issue")
                )
            )
        )
        record(
            "IDENTITY", identity_ok, "schema, work ID, type, and primary Issue agree"
        )

        accepted = _status(plan_meta.get("issue_status")) in ACCEPTED_STATUSES
        record(
            "ISSUE_STATE",
            accepted,
            "Plan records status/accept or status/working"
            if accepted
            else "Issue must be status/accept or status/working",
            blocked=True,
        )
        approval = plan_meta.get("approval")
        approval = approval if isinstance(approval, dict) else {}
        approval_ok = (
            accepted
            and _named_decider(approval.get("decided_by"))
            and _decision_evidence(approval.get("evidence_url"))
        )
        record(
            "ISSUE_APPROVAL_EVIDENCE",
            approval_ok,
            "human decision reference is structurally recorded; remote authenticity is not asserted"
            if approval_ok
            else "accepted work requires a named decider and an http(s) decision URL",
            blocked=True,
        )

        if category == "feature":
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
            reproduction_ids: set[str] = set()
        else:
            story_ids = set()
            bug_rows = _table(plan_body, "Bugfix Verification")
            bug_columns = {"Verification ID", "Reproduction ID", "Expected result"}
            bug_shape = bool(bug_rows) and bug_columns.issubset(bug_rows[0])
            known_acceptance = (
                {row["Verification ID"] for row in bug_rows} if bug_shape else set()
            )
            reproduction_ids = (
                {row["Reproduction ID"] for row in bug_rows} if bug_shape else set()
            )
            bug_shape = (
                bug_shape
                and bool(known_acceptance)
                and all(re.fullmatch(r"VER-\d+", item) for item in known_acceptance)
                and all(re.fullmatch(r"BUG-OBS-\d+", item) for item in reproduction_ids)
                and all(
                    all(value.strip() for value in row.values())
                    and not PLACEHOLDER.search(" ".join(row.values()))
                    for row in bug_rows
                )
            )
            record(
                "BUGFIX_INPUT",
                bug_shape,
                "Bugfix reproduction and Verification IDs are parseable"
                if bug_shape
                else "Bugfix Verification requires VER-### and BUG-OBS-### mappings",
            )

        plan_common = {
            "Plan (HLD)",
            "Source And Code Graph Evidence",
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
        plan_specific = (
            {"Feature Delivery Plan", "User Story Delivery Mapping"}
            if category == "feature"
            else {
                "Bugfix Delivery Plan",
                "Accepted Bug Summary",
                "Bugfix Verification",
                "Root Cause Evidence",
                "Reproduction And Regression Mapping",
            }
        )
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
            "Architecture And Contract Impact",
            "Declared Change Scope",
            "Implementation Plan",
            "Parallel Development Strategy",
            "Development Chain",
            "Plan Review Decision",
            "Compatibility Migration And Rollback",
            "Risks And Deviations",
        } | (
            {"User Story Delivery Mapping"}
            if category == "feature"
            else {
                "Accepted Bug Summary",
                "Bugfix Verification",
                "Root Cause Evidence",
                "Reproduction And Regression Mapping",
            }
        )
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
            graph.get("kind") in {"code-graph", "source-fallback"}
            and _evidence_file(project_root, graph.get("evidence_path"))
            and _meaningful(source_revision)
            and str(graph.get("source_revision", "")).strip() == source_revision
        )
        record(
            "IMPACT_EVIDENCE",
            graph_ok,
            "versioned Code Graph or source-fallback evidence file exists"
            if graph_ok
            else "impact_analysis.code_graph requires kind, existing evidence_path, and matching source_revision",
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

            if category == "feature":
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
            else:
                delivery = _table(plan_body, "Reproduction And Regression Mapping")
                columns = {
                    "Reproduction ID",
                    "Root-cause evidence",
                    "Task IDs",
                    "Regression test IDs",
                }
                delivery_ok = bool(delivery) and columns.issubset(delivery[0])
                if delivery_ok:
                    mapped_tests = {
                        item
                        for row in delivery
                        for item in _ids(row["Regression test IDs"])
                    }
                    delivery_ok = (
                        {row["Reproduction ID"] for row in delivery} == reproduction_ids
                        and all(
                            _meaningful(row["Root-cause evidence"]) for row in delivery
                        )
                        and all(
                            set(_ids(row["Task IDs"])).issubset(task_ids)
                            for row in delivery
                        )
                        and all(
                            set(_ids(row["Regression test IDs"])).issubset(test_ids)
                            for row in delivery
                        )
                        and set(task_ids)
                        == {item for row in delivery for item in _ids(row["Task IDs"])}
                        and mapped_tests == set(test_ids)
                    )
            record(
                "DELIVERY_MAPPING",
                delivery_ok,
                "type-specific delivery mapping covers the declared work"
                if delivery_ok
                else "Feature User Stories or Bugfix reproductions are not fully mapped to Tasks and tests",
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
    args = parser.parse_args()

    try:
        root = args.project_root.resolve()
        result, rendered = evaluate(root, args.work_type, args.work_id)
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
