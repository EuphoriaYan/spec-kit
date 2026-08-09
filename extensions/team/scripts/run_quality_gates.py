#!/usr/bin/env python3
"""Evaluate repository-owned command, static, and model quality rules."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


RULES_SCHEMA = "speckit-quality-rules/v1"
JUDGE_SCHEMA = "speckit-model-judge-results/v1"
OVERRIDE_SCHEMA = "speckit-quality-overrides/v1"
RESULT_SCHEMA = "speckit-quality-gate-result/v1"
ENGINES = {"command", "static", "model-as-judge"}
STATIC_CHECKS = {"forbidden-regex", "required-regex", "forbidden-path"}


class QualityGateError(RuntimeError):
    """Raised when quality configuration is invalid or unsafe."""


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise QualityGateError(f"{label} must be a mapping")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise QualityGateError(f"{label} must be a list")
    return value


def _load_yaml(path: Path, label: str) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise QualityGateError(f"{label} is invalid YAML: {exc}") from exc
    return _mapping(loaded, label)


def _safe_path(root: Path, value: str, label: str, *, require_file: bool = False) -> Path:
    relative = Path(value)
    if not value.strip() or relative.is_absolute() or ".." in relative.parts:
        raise QualityGateError(f"{label} must stay repository-relative")
    root = root.resolve()
    candidate = root / relative
    try:
        candidate.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise QualityGateError(f"{label} escapes the repository") from exc
    if require_file and not candidate.is_file():
        raise QualityGateError(f"{label} does not exist: {value}")
    return candidate


def _read_config(root: Path) -> tuple[str, str]:
    path = root / ".specify" / "team" / "ai-team-config.yml"
    if not path.is_file():
        return "disabled", "docs/ai-team/quality/rules.yml"
    config = _load_yaml(path, "AI Team config")
    quality = _mapping(config.get("quality_gates") or {}, "quality_gates")
    mode = str(quality.get("mode") or "disabled")
    if mode not in {"disabled", "advisory", "required"}:
        raise QualityGateError(
            "quality_gates.mode must be disabled, advisory, or required"
        )
    manifest = str(quality.get("manifest") or "docs/ai-team/quality/rules.yml")
    return mode, manifest


def _git_names(root: Path, args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False
    )
    if result.returncode:
        return []
    return [
        line.strip().replace("\\", "/")
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def _changed_files(root: Path, explicit: list[str], base: str | None) -> list[str]:
    names = list(explicit)
    if not names and base:
        names = _git_names(
            root,
            ["diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD"],
        )
    if not names:
        names = _git_names(root, ["diff", "--name-only", "--diff-filter=ACMR"])
        names += _git_names(
            root, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"]
        )
    if not names:
        names = _git_names(
            root, ["diff", "--name-only", "--diff-filter=ACMR", "HEAD^", "HEAD"]
        )
    normalized: list[str] = []
    for name in dict.fromkeys(names):
        _safe_path(root, name, "changed file")
        normalized.append(name.replace("\\", "/"))
    return sorted(normalized)


def _selected(path: str, include: list[str], exclude: list[str]) -> bool:
    included = any(fnmatch.fnmatch(path, item) for item in (include or ["*"]))
    excluded = any(fnmatch.fnmatch(path, item) for item in exclude)
    return included and not excluded


def _static_result(
    root: Path, rule: dict[str, Any], files: list[str]
) -> tuple[str, str, list[str]]:
    rule_id = rule["id"]
    config = _mapping(rule.get("static") or {}, f"{rule_id}.static")
    check = str(config.get("check") or "")
    if check not in STATIC_CHECKS:
        raise QualityGateError(f"{rule_id}.static.check is invalid")
    pattern = str(config.get("pattern") or "")
    if not pattern:
        raise QualityGateError(f"{rule_id}.static.pattern is required")
    include = [
        str(item) for item in _list(config.get("include"), f"{rule_id}.include")
    ]
    exclude = [
        str(item) for item in _list(config.get("exclude"), f"{rule_id}.exclude")
    ]
    selected = [name for name in files if _selected(name, include, exclude)]
    evidence: list[str] = []
    if check == "forbidden-path":
        evidence = [name for name in selected if fnmatch.fnmatch(name, pattern)]
    else:
        try:
            compiled = re.compile(pattern, re.MULTILINE)
        except re.error as exc:
            raise QualityGateError(
                f"{rule_id}.static.pattern is invalid: {exc}"
            ) from exc
        for name in selected:
            path = root / name
            if not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            matches = list(compiled.finditer(content))
            if check == "forbidden-regex" and matches:
                line = content.count("\n", 0, matches[0].start()) + 1
                evidence.append(f"{name}:{line}")
            elif check == "required-regex" and not matches:
                evidence.append(name)
    status = "fail" if evidence else "pass"
    default = "Static rule matched." if evidence else "Static rule passed."
    return status, str(config.get("message") or default), evidence


def _command_result(
    root: Path, rule: dict[str, Any]
) -> tuple[str, str, list[str]]:
    rule_id = rule["id"]
    config = _mapping(rule.get("command") or {}, f"{rule_id}.command")
    key = "windows_argv" if os.name == "nt" and config.get("windows_argv") else "argv"
    argv = [
        str(item) for item in _list(config.get(key), f"{rule_id}.command.{key}")
    ]
    if not argv:
        raise QualityGateError(f"{rule_id}.command.{key} is required")
    timeout = int(config.get("timeout_seconds") or 300)
    try:
        result = subprocess.run(
            argv,
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
            shell=False,
        )
        output = (result.stdout + "\n" + result.stderr).strip()[-4000:]
        return (
            "pass" if result.returncode == 0 else "fail",
            f"Command exited with {result.returncode}.",
            [output] if output else [],
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "fail", f"Command could not complete: {exc}", []


def _index_records(
    path: Path | None, schema: str, key: str
) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    data = _load_yaml(path, path.name)
    if data.get("schema") != schema:
        raise QualityGateError(f"{path.name} schema must be {schema}")
    records: dict[str, dict[str, Any]] = {}
    for raw in _list(data.get(key), key):
        item = _mapping(raw, key)
        rule_id = str(item.get("rule_id") or "")
        if not rule_id or rule_id in records:
            raise QualityGateError(f"{key} contains a missing or duplicate rule_id")
        records[rule_id] = item
    return records


def _apply_override(
    rule_id: str,
    engine: str,
    status: str,
    overrides: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    decision = overrides.get(rule_id)
    if decision is None or status == "pass":
        return None
    if status != "fail":
        raise QualityGateError(
            f"only an assessed model-as-judge failure may be overridden: {rule_id}"
        )
    if engine != "model-as-judge":
        raise QualityGateError(
            f"only model-as-judge failures may be overridden: {rule_id}"
        )
    required = ("decided_by", "decided_at", "reason")
    valid = decision.get("outcome") == "go-with-risk" and all(
        str(decision.get(key) or "").strip() for key in required
    )
    if not valid:
        raise QualityGateError(
            f"override for {rule_id} must be a named, timed, reasoned "
            "go-with-risk decision"
        )
    normalized = dict(decision)
    # PyYAML resolves an unquoted ISO-8601 value to datetime. Quality gate
    # results are JSON evidence, so normalize the value at the boundary while
    # preserving the human-readable timestamp.
    normalized["decided_at"] = str(decision["decided_at"])
    return normalized


def evaluate(
    root: Path,
    *,
    phase: str,
    role: str,
    engines: set[str] | None = None,
    files: list[str] | None = None,
    base: str | None = None,
    judge_path: Path | None = None,
    override_path: Path | None = None,
) -> tuple[dict[str, Any], int]:
    root = root.resolve()
    mode, manifest_text = _read_config(root)
    if mode == "disabled":
        return {
            "schema": RESULT_SCHEMA,
            "status": "disabled",
            "verdict": "GO",
            "results": [],
        }, 0
    manifest = _safe_path(root, manifest_text, "quality_gates.manifest")
    if not manifest.is_file():
        verdict = "NO-GO" if mode == "required" else "GO-WITH-RISK"
        return {
            "schema": RESULT_SCHEMA,
            "status": "not-configured",
            "verdict": verdict,
            "suggestions": [
                f"Quality rules manifest is not present: {manifest_text}."
            ],
            "results": [],
        }, 2 if mode == "required" else 0
    data = _load_yaml(manifest, "quality rules manifest")
    if data.get("schema") != RULES_SCHEMA:
        raise QualityGateError(f"quality rules schema must be {RULES_SCHEMA}")
    pack = _mapping(data.get("pack") or {}, "pack")
    if not str(pack.get("id") or "") or not str(pack.get("version") or ""):
        raise QualityGateError("quality rule pack requires id and version")
    changed = _changed_files(root, files or [], base)
    judge = _index_records(judge_path, JUDGE_SCHEMA, "results")
    overrides = _index_records(override_path, OVERRIDE_SCHEMA, "overrides")
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in _list(data.get("rules"), "rules"):
        rule = _mapping(raw, "rule")
        rule_id = str(rule.get("id") or "")
        if not rule_id or rule_id in seen:
            raise QualityGateError("rules contain a missing or duplicate id")
        seen.add(rule_id)
        rule["id"] = rule_id
        if rule.get("enabled", True) is False:
            continue
        engine = str(rule.get("engine") or "")
        if engine not in ENGINES:
            raise QualityGateError(f"{rule_id}.engine is invalid")
        if engines and engine not in engines:
            continue
        phases = [
            str(item) for item in _list(rule.get("phases"), f"{rule_id}.phases")
        ]
        roles = [
            str(item) for item in _list(rule.get("roles"), f"{rule_id}.roles")
        ]
        if (phases and phase not in phases) or (roles and role not in roles):
            continue
        enforcement = str(rule.get("enforcement") or "required")
        if enforcement not in {"required", "advisory"}:
            raise QualityGateError(f"{rule_id}.enforcement is invalid")
        if engine == "static":
            status, rationale, evidence = _static_result(root, rule, changed)
        elif engine == "command":
            status, rationale, evidence = _command_result(root, rule)
        else:
            model = _mapping(rule.get("model") or {}, f"{rule_id}.model")
            if not str(model.get("instruction") or "").strip():
                raise QualityGateError(f"{rule_id}.model.instruction is required")
            item = judge.get(rule_id) or {}
            status = str(item.get("status") or "not-assessed")
            if status not in {"pass", "fail", "not-assessed"}:
                raise QualityGateError(
                    f"judge result for {rule_id} has invalid status"
                )
            rationale = str(
                item.get("rationale") or "Model-as-Judge result was not provided."
            )
            evidence = [
                str(value)
                for value in _list(item.get("evidence"), f"{rule_id}.evidence")
            ]
        human_override = _apply_override(rule_id, engine, status, overrides)
        results.append(
            {
                "rule_id": rule_id,
                "title": str(rule.get("title") or rule_id),
                "category": str(rule.get("category") or "general"),
                "severity": str(rule.get("severity") or "major"),
                "engine": engine,
                "enforcement": enforcement,
                "status": status,
                "rationale": rationale,
                "evidence": evidence,
                "human_override": human_override,
            }
        )
    failures = [item for item in results if item["status"] != "pass"]
    required_failures = [
        item
        for item in failures
        if item["enforcement"] == "required" and not item["human_override"]
    ]
    verdict = "NO-GO" if required_failures else "GO-WITH-RISK" if failures else "GO"
    payload = {
        "schema": RESULT_SCHEMA,
        "status": "evaluated",
        "mode": mode,
        "pack": {"id": str(pack["id"]), "version": str(pack["version"])},
        "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "phase": phase,
        "role": role,
        "changed_files": changed,
        "verdict": verdict,
        "results": results,
        "merge_responsibility": "human",
    }
    return payload, 2 if mode == "required" and verdict == "NO-GO" else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--phase", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--engine", action="append", choices=sorted(ENGINES))
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--base")
    parser.add_argument("--judge-results", type=Path)
    parser.add_argument("--overrides", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        root = args.project_root.resolve()
        judge = (
            _safe_path(
                root,
                args.judge_results.as_posix(),
                "judge results",
                require_file=True,
            )
            if args.judge_results
            else None
        )
        overrides = (
            _safe_path(
                root, args.overrides.as_posix(), "overrides", require_file=True
            )
            if args.overrides
            else None
        )
        payload, return_code = evaluate(
            root,
            phase=args.phase,
            role=args.role,
            engines=set(args.engine) if args.engine else None,
            files=args.file,
            base=args.base,
            judge_path=judge,
            override_path=overrides,
        )
        rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            output = _safe_path(root, args.output.as_posix(), "output")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return return_code
    except (QualityGateError, OSError, UnicodeError, ValueError) as exc:
        print(f"AI Team quality gate failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
