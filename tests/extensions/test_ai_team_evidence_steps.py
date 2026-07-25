from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "extensions/team/scripts/check_evidence_steps.py"


def _module():
    spec = importlib.util.spec_from_file_location("ai_team_evidence_steps", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _manifest(result: str, missing_condition: str = "") -> str:
    return f"""schema: ai-team-evidence-steps/v1
revision: abc123
steps:
  - id: STEP-001
    title: Offline verification
    kind: deterministic
    prerequisites: [Packaged application]
    action: python verify.py
    expected: Exit code zero and exact result schema
    actual: Exit code zero and schema matched
    evidence: target/report.md
    result: {result}
    missing_condition: {missing_condition!r}
    recovery: Fix the named assertion and rerun
"""


def test_accepts_pass_and_blocked_with_recovery_evidence(tmp_path: Path) -> None:
    module = _module()
    passed = tmp_path / "pass.yml"
    passed.write_text(_manifest("PASS"), encoding="utf-8")
    blocked = tmp_path / "blocked.yml"
    blocked.write_text(
        _manifest("BLOCKED", "Approved provider contract is unavailable"),
        encoding="utf-8",
    )

    assert module.validate(passed) == []
    assert module.validate(blocked) == []


def test_rejects_subjective_or_unexplained_state(tmp_path: Path) -> None:
    module = _module()
    path = tmp_path / "bad.yml"
    path.write_text(
        _manifest("NOT_RUN").replace(
            "expected: Exit code zero and exact result schema", "expected: TODO"
        ),
        encoding="utf-8",
    )

    errors = module.validate(path)

    assert any("expected" in error for error in errors)
    assert any("missing_condition" in error for error in errors)
