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


VALIDATOR = "ai-team-plan-and-task-check/v1"
SPEC_SCHEMA = "ai-team-spec/v1"
PLAN_SCHEMA = "ai-team-plan-and-task/v1"
ACCEPTED_STATES = {"accepted", "working"}
PLACEHOLDER = re.compile(r"(?i)\b(?:TBD|TODO|FIXME)\b|<[^>]+>|path/to/file")
ID_SPLIT = re.compile(r"\s*(?:,|;|<br\s*/?>)\s*", re.IGNORECASE)


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
    match = re.search(
        rf"(?m)^(#{{2,4}})\s+{re.escape(heading)}\s*$", body
    )
    if not match:
        return ""
    rest = body[match.end() :]
    level = len(match.group(1))
    end = re.search(rf"(?m)^#{{2,{level}}}\s+", rest)
    return (rest[: end.start()] if end else rest).strip()


def _table(body: str, heading: str) -> list[dict[str, str]]:
    section = _section(body, heading)
    lines = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
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


def _state(value: object) -> str:
    return str(value or "").strip().lower().removeprefix("state/")


def _list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _meaningful(section: str) -> bool:
    content = re.sub(r"<!--.*?-->", "", section, flags=re.DOTALL).strip()
    return bool(content) and not PLACEHOLDER.search(content)


def evaluate(project_root: Path, work_type: str, work_id: str) -> tuple[str, str]:
    category = normalize_category(work_type)
    work_root = resolve_work_root(project_root, category, work_id)
    spec_path = work_root / "spec.md"
    plan_path = work_root / "plan-and-task.md"
    checks: list[Check] = []

    def record(check_id: str, ok: bool, detail: str, *, blocked: bool = False) -> None:
        checks.append(Check(check_id, "PASS" if ok else ("BLOCK" if blocked else "FAIL"), detail))

    missing = [path.name for path in (spec_path, plan_path) if not path.is_file()]
    record("ARTIFACTS", not missing, "required artifacts exist" if not missing else f"missing: {', '.join(missing)}", blocked=True)

    spec_meta: dict[str, Any] = {}
    plan_meta: dict[str, Any] = {}
    spec_body = ""
    plan_body = ""
    parse_errors: list[str] = []
    if not missing:
        for path, target in ((spec_path, "spec"), (plan_path, "plan")):
            try:
                metadata, body = _frontmatter(path)
                if target == "spec":
                    spec_meta, spec_body = metadata, body
                else:
                    plan_meta, plan_body = metadata, body
            except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
                parse_errors.append(str(exc))
    record("FRONTMATTER", not parse_errors and not missing, "front matter parsed" if not parse_errors else "; ".join(parse_errors))

    if not missing and not parse_errors:
        try:
            spec_category = normalize_category(str(spec_meta.get("work_type", "")))
            plan_category = normalize_category(str(plan_meta.get("work_type", "")))
        except ValueError:
            spec_category = plan_category = "invalid"
        identity_ok = (
            spec_meta.get("schema") == SPEC_SCHEMA
            and plan_meta.get("schema") == PLAN_SCHEMA
            and str(spec_meta.get("work_id", "")) == work_id
            and str(plan_meta.get("work_id", "")) == work_id
            and spec_category == category
            and plan_category == category
            and bool(str(spec_meta.get("primary_issue", "")).strip())
        )
        record("IDENTITY", identity_ok, "schema, work ID, type, and primary Issue agree")

        accepted = _state(spec_meta.get("issue_state")) in ACCEPTED_STATES
        record("ISSUE_STATE", accepted, "Issue is accepted for planning" if accepted else "Issue must be state/accepted or state/working", blocked=True)

        spec_common = {
            "Common Specification",
            "Problem And Goal",
            "Acceptance Summary",
            "Scope",
            "Non-Goals",
            "Open Questions",
        }
        spec_specific = (
            {"Feature Specification", "User Stories", "Feature Acceptance"}
            if category == "feature"
            else {
                "Bugfix Specification",
                "Observed Behavior",
                "Expected Behavior",
                "Reproduction",
                "Environment",
                "Impact",
                "Fix Acceptance",
            }
        )
        missing_spec = sorted((spec_common | spec_specific) - _headings(spec_body))
        record("SPEC_STRUCTURE", not missing_spec, "required common and type-specific Spec sections exist" if not missing_spec else f"missing headings: {', '.join(missing_spec)}")

        plan_common = {
            "Common Engineering Plan",
            "Source And Code Graph Evidence",
            "Affected Modules And Owners",
            "Architecture And Contract Impact",
            "Declared Change Scope",
            "Implementation Plan",
            "Ordered Tasks",
            "Minimum Self-Tests",
            "Compatibility Migration And Rollback",
            "Risks And Deviations",
        }
        plan_specific = (
            {"Feature Delivery Plan", "User Story Delivery Mapping"}
            if category == "feature"
            else {"Bugfix Delivery Plan", "Root Cause Evidence", "Reproduction And Regression Mapping"}
        )
        missing_plan = sorted((plan_common | plan_specific) - _headings(plan_body))
        record("PLAN_STRUCTURE", not missing_plan, "required common and type-specific Plan sections exist" if not missing_plan else f"missing headings: {', '.join(missing_plan)}")

        declared_paths = _list(plan_meta.get("declared_paths"))
        modules = _list(plan_meta.get("affected_modules"))
        safe_paths = bool(declared_paths) and all(
            not Path(path).is_absolute() and ".." not in Path(path).parts
            for path in declared_paths
        )
        record("DECLARED_SCOPE", safe_paths and bool(modules), "declared paths and affected modules are non-empty and project-relative")

        impact = plan_meta.get("impact_analysis")
        impact = impact if isinstance(impact, dict) else {}
        graph = str(impact.get("code_graph_evidence", "")).strip()
        cross_module = impact.get("cross_module") is True
        class_changes = impact.get("class_changes") is True
        contract_change = str(impact.get("public_contract_change", "")).strip().lower()
        owner_approval = str(impact.get("contract_owner_approval", "")).strip()
        graph_ok = bool(graph) and not PLACEHOLDER.search(graph)
        record("IMPACT_EVIDENCE", graph_ok, "Code Graph or source fallback is recorded" if graph_ok else "impact_analysis.code_graph_evidence is required")
        contract_ok = contract_change == "none" or owner_approval.lower() not in {
            "", "not-required", "pending", "tbd"
        }
        record("CONTRACT_AUTHORITY", contract_ok, "public-contract authority is satisfied" if contract_ok else "public contract change requires recorded owner approval", blocked=True)

        mode = str(plan_meta.get("planning_mode", "")).strip().lower()
        compact_owner = str(plan_meta.get("compact_approved_by", "")).strip().lower()
        compact_ok = mode in {"standard", "compact"}
        if mode == "compact":
            compact_ok = (
                compact_owner not in {"", "not-applicable", "pending", "tbd"}
                and not cross_module
                and not class_changes
                and contract_change == "none"
            )
        record("PLANNING_MODE", compact_ok, "planning mode and human Compact selection are valid" if compact_ok else "Compact requires a named human and no cross-module, class, or public-contract change", blocked=True)

        tasks = _table(plan_body, "Ordered Tasks")
        tests = _table(plan_body, "Minimum Self-Tests")
        task_columns = {"Task ID", "Requirement ID", "Planned paths", "Self-test IDs", "Description"}
        test_columns = {"Test ID", "Type", "Command or procedure", "Expected evidence"}
        task_shape = bool(tasks) and task_columns.issubset(tasks[0])
        test_shape = bool(tests) and test_columns.issubset(tests[0])
        record("TASK_TABLE", task_shape, "ordered Task table is parseable" if task_shape else "Ordered Tasks must use the Team table columns")
        record("SELF_TEST_TABLE", test_shape, "minimum self-test table is parseable" if test_shape else "Minimum Self-Tests must use the Team table columns")

        if task_shape and test_shape:
            task_ids = [row["Task ID"] for row in tasks]
            test_ids = [row["Test ID"] for row in tests]
            known_acceptance = set(re.findall(r"\bAC-\d+\b", spec_body))
            mappings_ok = (
                len(task_ids) == len(set(task_ids))
                and len(test_ids) == len(set(test_ids))
                and all(row["Requirement ID"] in known_acceptance for row in tasks)
                and all(set(_ids(row["Self-test IDs"])).issubset(test_ids) for row in tasks)
                and all(set(_ids(row["Planned paths"])).issubset(declared_paths) for row in tasks)
                and all(
                    not PLACEHOLDER.search(" ".join(row.values()))
                    and all(value.strip() for value in row.values())
                    for row in tasks + tests
                )
            )
            record("TRACEABILITY", mappings_ok, "Tasks map to acceptance IDs, declared paths, and defined self-tests" if mappings_ok else "Task/test IDs, acceptance mapping, declared paths, or required values are inconsistent")

        compatibility_ok = _meaningful(
            _section(plan_body, "Compatibility Migration And Rollback")
        )
        record("COMPATIBILITY_ROLLBACK", compatibility_ok, "compatibility and rollback are explicitly documented" if compatibility_ok else "compatibility and rollback section is missing or contains placeholders")

    result = "blocked" if any(item.result == "BLOCK" for item in checks) else (
        "revise" if any(item.result == "FAIL" for item in checks) else "ready"
    )
    mode = str(plan_meta.get("planning_mode", "unknown"))
    lines = [
        "# Plan And Task Check",
        "",
        "This file is generated. Do not hand-edit it.",
        "",
        f"- Result: {result}",
        f"- Work ID: {work_id}",
        f"- Work type: {category}",
        f"- Planning mode: {mode}",
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
    lines.extend(
        [f"- {item.check_id}: {item.detail}" for item in findings] or ["None"]
    )
    return result, "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--work-type", required=True)
    parser.add_argument("--work-id", required=True)
    parser.add_argument("--check", action="store_true", help="fail when the generated check file is stale")
    args = parser.parse_args()

    try:
        root = args.project_root.resolve()
        result, rendered = evaluate(root, args.work_type, args.work_id)
        output = resolve_work_root(root, args.work_type, args.work_id) / "plan-and-task-check.md"
        if args.check:
            if not output.is_file() or output.read_text(encoding="utf-8").replace("\r\n", "\n") != rendered:
                print(f"AI Team Plan-and-Task check is stale: {output}", file=sys.stderr)
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
