from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "extensions" / "team" / "scripts" / "run_quality_gates.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_quality_gates", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _configure(project: Path, mode: str = "required") -> None:
    path = project / ".specify" / "team" / "ai-team-config.yml"
    path.parent.mkdir(parents=True)
    path.write_text(
        yaml.safe_dump(
            {
                "quality_gates": {
                    "mode": mode,
                    "manifest": "docs/ai-team/quality/rules.yml",
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _rules(project: Path, rules: list[dict[str, object]]) -> None:
    path = project / "docs" / "ai-team" / "quality" / "rules.yml"
    path.parent.mkdir(parents=True)
    path.write_text(
        yaml.safe_dump(
            {
                "schema": "speckit-quality-rules/v1",
                "pack": {"id": "test-pack", "version": "1.0.0"},
                "rules": rules,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _record_file(
    project: Path, name: str, schema: str, key: str, values: list[dict[str, str]]
) -> Path:
    path = project / ".specify" / "work" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"schema": schema, key: values}, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _model_rule(enforcement: str = "required") -> dict[str, object]:
    return {
        "id": "ARCH-001",
        "title": "Architecture boundary",
        "engine": "model-as-judge",
        "enforcement": enforcement,
        "phases": ["reviewing"],
        "roles": ["reviewer"],
        "model": {"instruction": "Inspect boundaries."},
    }


def _external_rule(
    enforcement: str = "required", **external: object
) -> dict[str, object]:
    return {
        "id": "CVGS-001",
        "title": "External quality findings",
        "engine": "external",
        "enforcement": enforcement,
        "phases": ["reviewing"],
        "roles": ["reviewer"],
        "external": {"tool": "cvgs", **external},
    }


def _external_report(project: Path, findings: list[dict[str, object]]) -> Path:
    path = project / ".specify" / "work" / "external.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "schema": "speckit-external-quality-findings/v1",
                "source": {
                    "tool": "cvgs",
                    "report": "cvgs.xlsx",
                    "report_sha256": "a" * 64,
                    "generated_at": "2026-09-04T12:00:00+00:00",
                    "source_revision": "abc123",
                },
                "findings": findings,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def test_existing_project_is_disabled_by_default(tmp_path: Path) -> None:
    module = _load_module()

    result, return_code = module.evaluate(tmp_path, phase="reviewing", role="reviewer")

    assert return_code == 0
    assert result["status"] == "disabled"
    assert result["verdict"] == "GO"


def test_missing_required_manifest_fails_closed(tmp_path: Path) -> None:
    module = _load_module()
    _configure(tmp_path)

    result, return_code = module.evaluate(tmp_path, phase="reviewing", role="reviewer")

    assert return_code == 2
    assert result["status"] == "not-configured"
    assert result["verdict"] == "NO-GO"
    assert result["suggestions"]


def test_static_failure_is_required_no_go(tmp_path: Path) -> None:
    module = _load_module()
    _configure(tmp_path)
    source = tmp_path / "src" / "Demo.java"
    source.parent.mkdir()
    source.write_text('String password = "secret";', encoding="utf-8")
    _rules(
        tmp_path,
        [
            {
                "id": "SEC-001",
                "title": "No password literal",
                "engine": "static",
                "enforcement": "required",
                "static": {
                    "check": "forbidden-regex",
                    "pattern": "password\\s*=",
                    "include": ["*.java", "**/*.java"],
                },
            }
        ],
    )

    result, return_code = module.evaluate(
        tmp_path,
        phase="implementing",
        role="developer",
        files=["src/Demo.java"],
    )

    assert return_code == 2
    assert result["verdict"] == "NO-GO"
    assert result["results"][0]["evidence"] == ["src/Demo.java:1"]
    assert len(result["manifest_sha256"]) == 64


@pytest.mark.parametrize(
    "exit_code, expected",
    [(0, "GO"), (3, "NO-GO")],
)
def test_command_rules_use_argv_and_capture_exit(
    tmp_path: Path, exit_code: int, expected: str
) -> None:
    module = _load_module()
    _configure(tmp_path)
    argv = [sys.executable, "-c", f"raise SystemExit({exit_code})"]
    _rules(
        tmp_path,
        [
            {
                "id": "BUILD-001",
                "title": "Build",
                "engine": "command",
                "enforcement": "required",
                "command": {"argv": argv, "windows_argv": argv},
            }
        ],
    )

    result, return_code = module.evaluate(
        tmp_path, phase="implementing", role="developer", files=[]
    )

    assert result["verdict"] == expected
    assert return_code == (0 if exit_code == 0 else 2)


def test_missing_model_result_fails_closed(tmp_path: Path) -> None:
    module = _load_module()
    _configure(tmp_path)
    _rules(tmp_path, [_model_rule()])

    result, return_code = module.evaluate(
        tmp_path, phase="reviewing", role="reviewer", files=[]
    )

    assert return_code == 2
    assert result["verdict"] == "NO-GO"
    assert result["results"][0]["status"] == "not-assessed"


def test_named_human_can_reduce_model_failure_to_go_with_risk(
    tmp_path: Path,
) -> None:
    module = _load_module()
    _configure(tmp_path)
    _rules(tmp_path, [_model_rule()])
    judge = _record_file(
        tmp_path,
        "judge.yml",
        "speckit-model-judge-results/v1",
        "results",
        [
            {
                "rule_id": "ARCH-001",
                "status": "fail",
                "rationale": "Possible duplicate boundary.",
            }
        ],
    )
    overrides = _record_file(
        tmp_path,
        "overrides.yml",
        "speckit-quality-overrides/v1",
        "overrides",
        [
            {
                "rule_id": "ARCH-001",
                "outcome": "go-with-risk",
                "decided_by": "Maintainer Name",
                "decided_at": "2026-08-09T12:00:00+08:00",
                "reason": "The adapter is an approved compatibility boundary.",
            }
        ],
    )

    result, return_code = module.evaluate(
        tmp_path,
        phase="reviewing",
        role="reviewer",
        files=[],
        judge_path=judge,
        override_path=overrides,
    )

    assert return_code == 0
    assert result["verdict"] == "GO-WITH-RISK"
    assert result["results"][0]["human_override"]["decided_by"] == ("Maintainer Name")
    assert result["merge_responsibility"] == "human"


def test_unquoted_yaml_timestamp_is_json_serializable(tmp_path: Path) -> None:
    module = _load_module()
    _configure(tmp_path)
    _rules(tmp_path, [_model_rule()])
    judge = _record_file(
        tmp_path,
        "judge.yml",
        "speckit-model-judge-results/v1",
        "results",
        [{"rule_id": "ARCH-001", "status": "fail", "rationale": "Risk."}],
    )
    overrides = tmp_path / ".specify" / "work" / "overrides.yml"
    overrides.write_text(
        """schema: speckit-quality-overrides/v1
overrides:
  - rule_id: ARCH-001
    outcome: go-with-risk
    decided_by: Maintainer
    decided_at: 2026-08-09T12:00:00+08:00
    reason: Approved exception.
""",
        encoding="utf-8",
    )

    result, return_code = module.evaluate(
        tmp_path,
        phase="reviewing",
        role="reviewer",
        judge_path=judge,
        override_path=overrides,
    )

    assert return_code == 0
    assert result["results"][0]["human_override"]["decided_at"] == (
        "2026-08-09 12:00:00+08:00"
    )
    json.dumps(result)


def test_static_failure_cannot_be_human_overridden(tmp_path: Path) -> None:
    module = _load_module()
    _configure(tmp_path)
    source = tmp_path / "bad.txt"
    source.write_text("forbidden", encoding="utf-8")
    _rules(
        tmp_path,
        [
            {
                "id": "STATIC-001",
                "engine": "static",
                "enforcement": "required",
                "static": {
                    "check": "forbidden-regex",
                    "pattern": "forbidden",
                },
            }
        ],
    )
    overrides = _record_file(
        tmp_path,
        "overrides.yml",
        "speckit-quality-overrides/v1",
        "overrides",
        [
            {
                "rule_id": "STATIC-001",
                "outcome": "go-with-risk",
                "decided_by": "Maintainer",
                "decided_at": "2026-08-09T12:00:00+08:00",
                "reason": "Attempted bypass.",
            }
        ],
    )

    with pytest.raises(module.QualityGateError, match="only model-as-judge"):
        module.evaluate(
            tmp_path,
            phase="reviewing",
            role="reviewer",
            files=["bad.txt"],
            override_path=overrides,
        )


def test_advisory_model_failure_is_go_with_risk(tmp_path: Path) -> None:
    module = _load_module()
    _configure(tmp_path, mode="required")
    _rules(tmp_path, [_model_rule(enforcement="advisory")])

    result, return_code = module.evaluate(
        tmp_path, phase="reviewing", role="reviewer", files=[]
    )

    assert return_code == 0
    assert result["verdict"] == "GO-WITH-RISK"


def test_unassessed_model_rule_cannot_be_overridden(tmp_path: Path) -> None:
    module = _load_module()
    _configure(tmp_path)
    _rules(tmp_path, [_model_rule()])
    overrides = _record_file(
        tmp_path,
        "overrides.yml",
        "speckit-quality-overrides/v1",
        "overrides",
        [
            {
                "rule_id": "ARCH-001",
                "outcome": "go-with-risk",
                "decided_by": "Maintainer",
                "decided_at": "2026-08-09T12:00:00+08:00",
                "reason": "Judge was never run.",
            }
        ],
    )

    with pytest.raises(module.QualityGateError, match="assessed model-as-judge"):
        module.evaluate(
            tmp_path,
            phase="reviewing",
            role="reviewer",
            files=[],
            override_path=overrides,
        )


def test_engine_phase_and_role_filters_limit_evaluation(tmp_path: Path) -> None:
    module = _load_module()
    _configure(tmp_path)
    _rules(tmp_path, [_model_rule()])

    result, return_code = module.evaluate(
        tmp_path,
        phase="implementing",
        role="developer",
        engines={"command", "static"},
        files=[],
    )

    assert return_code == 0
    assert result["verdict"] == "GO"
    assert result["results"] == []


def test_required_external_rule_fails_closed_without_report(tmp_path: Path) -> None:
    module = _load_module()
    _configure(tmp_path)
    _rules(tmp_path, [_external_rule()])

    result, return_code = module.evaluate(
        tmp_path, phase="reviewing", role="reviewer", files=["src/demo.py"]
    )

    assert return_code == 2
    assert result["verdict"] == "NO-GO"
    assert result["results"][0]["status"] == "not-assessed"


def test_advisory_external_rule_does_not_block_without_report(tmp_path: Path) -> None:
    module = _load_module()
    _configure(tmp_path)
    _rules(tmp_path, [_external_rule(enforcement="advisory")])

    result, return_code = module.evaluate(
        tmp_path, phase="reviewing", role="reviewer", files=["src/demo.py"]
    )

    assert return_code == 0
    assert result["verdict"] == "GO-WITH-RISK"
    assert result["results"][0]["status"] == "not-assessed"


def test_external_rule_filters_matched_and_unchanged_findings(tmp_path: Path) -> None:
    module = _load_module()
    _configure(tmp_path)
    _rules(tmp_path, [_external_rule(severities=["major", "minor"])])
    report = _external_report(
        tmp_path,
        [
            {
                "baseline_state": "matched",
                "rule_id": "G.TES.01",
                "path": "src/demo.py",
                "line": 10,
                "severity": "minor",
                "status": "open",
                "message": "baseline",
            },
            {
                "baseline_state": "new",
                "rule_id": "G.TES.01",
                "path": "src/other.py",
                "line": 11,
                "severity": "major",
                "status": "open",
                "message": "outside diff",
            },
            {
                "baseline_state": "new",
                "rule_id": "G.TES.01",
                "path": "src/demo.py",
                "line": 12,
                "severity": "minor",
                "status": "open",
                "message": "new finding",
            },
        ],
    )

    result, return_code = module.evaluate(
        tmp_path,
        phase="reviewing",
        role="reviewer",
        files=["src/demo.py"],
        external_paths=[report],
    )

    assert return_code == 2
    assert result["verdict"] == "NO-GO"
    assert result["results"][0]["evidence"] == ["src/demo.py:12 [G.TES.01] new finding"]
    assert result["results"][0]["external_report"]["source_revision"] == "abc123"


@pytest.mark.parametrize("reviewed, expected", [(False, "NO-GO"), (True, "GO")])
def test_ignored_external_finding_requires_audit(
    tmp_path: Path, reviewed: bool, expected: str
) -> None:
    module = _load_module()
    _configure(tmp_path)
    _rules(tmp_path, [_external_rule()])
    finding: dict[str, object] = {
        "baseline_state": "new",
        "rule_id": "G.TES.01",
        "path": "tests/demo.py",
        "line": 12,
        "severity": "minor",
        "status": "ignored",
        "message": "pytest assertion",
    }
    if reviewed:
        finding["review"] = {
            "reviewer": "Maintainer",
            "reviewed_at": "2026-09-04T12:00:00+00:00",
            "reason": "Rule excludes tests.",
            "outcome": "false-positive",
        }
    report = _external_report(tmp_path, [finding])

    result, return_code = module.evaluate(
        tmp_path,
        phase="reviewing",
        role="reviewer",
        files=["tests/demo.py"],
        external_paths=[report],
    )

    assert result["verdict"] == expected
    assert return_code == (0 if reviewed else 2)


def test_external_report_revision_must_match_current_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    _configure(tmp_path)
    _rules(tmp_path, [_external_rule(require_source_revision=True)])
    report = _external_report(tmp_path, [])
    monkeypatch.setattr(module, "_git_revision", lambda _root: "different")

    result, return_code = module.evaluate(
        tmp_path,
        phase="reviewing",
        role="reviewer",
        files=[],
        external_paths=[report],
    )

    assert return_code == 2
    assert result["verdict"] == "NO-GO"
    assert "does not match" in result["results"][0]["rationale"]
