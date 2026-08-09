from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "extensions" / "team" / "scripts"


def _load_module(filename: str, name: str):
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(SCRIPTS))


def _record(
    feature_id: str = "FEAT-001",
    *,
    phase: str = "backlog",
    accepted: bool = True,
) -> dict:
    return {
        "schema": "speckit-feature-record/v1",
        "feature_id": feature_id,
        "title": "Feature lifecycle",
        "parent_requirement": "https://example.test/issues/25",
        "acceptance": {
            "status": "accepted" if accepted else "proposed",
            "decided_by": "architecture-group" if accepted else "",
            "decided_at": "2026-07-25T00:00:00Z" if accepted else "",
        },
        "behavior_acceptance": {
            "status": "accepted" if phase != "backlog" else "proposed",
            "decided_by": "product-owner" if phase != "backlog" else "",
            "decided_at": "2026-07-25T01:00:00Z" if phase != "backlog" else "",
            "decision_source": "conversation" if phase != "backlog" else "",
        },
        "delivery": {
            "phase": phase,
            "pull_request": "",
            "review_target": {
                "type": "",
                "url": "",
                "revision": "",
            },
            "merged_commit": "",
        },
        "architecture_impact": {
            "level": "none",
            "update_required": False,
            "reason": "No architecture boundary changes.",
            "affected_files": [],
        },
        "definition_of_done": {
            "code_complete": False,
            "tests_complete": False,
            "evidence_complete": False,
            "architecture_synchronized": False,
            "review_passed": False,
        },
    }


def _write_tracking_config(project_root: Path, **overrides):
    config = {
        "root": "docs/features",
        "recommended_root": "docs/features",
        "location": {
            "status": "confirmed",
            "locked": True,
            "decided_by": "repository-owner",
            "decided_at": "2026-07-25T00:00:00Z",
        },
        "catalog_file": "feature-catalog.yml",
        "record_path_template": "{feature_id}.md",
        "format": "markdown-frontmatter",
        "id_pattern": "^FEAT-[0-9]{3,}$",
    }
    config.update(overrides)
    path = project_root / ".specify/team/ai-team-config.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"feature_tracking": config}, sort_keys=False),
        encoding="utf-8",
    )


def _write_catalog(root: Path, record_path: str, feature_id: str = "FEAT-001"):
    feature_root = root / "docs" / "features"
    feature_root.mkdir(parents=True, exist_ok=True)
    (feature_root / "feature-catalog.yml").write_text(
        yaml.safe_dump(
            {
                "schema": "speckit-feature-catalog/v1",
                "parent_requirement": "https://example.test/issues/25",
                "features": [
                    {
                        "id": feature_id,
                        "title": "Feature lifecycle",
                        "record": record_path,
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_markdown_record(root: Path, data: dict):
    path = root / "docs" / "features" / f"{data['feature_id']}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\n{yaml.safe_dump(data, sort_keys=False)}---\n\n# Feature\n\n"
        "## User Stories\n\n- US-001: User can complete the behavior.\n\n"
        "## Verification\n\n- VER-001: The observable result is produced.\n",
        encoding="utf-8",
    )
    _write_catalog(
        root, path.relative_to(root).as_posix(), feature_id=data["feature_id"]
    )
    return path


def _write_requirement_record(root: Path, data: dict) -> Path:
    path = root / "docs/requirements" / f"{data['requirement_id']}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\n{yaml.safe_dump(data, sort_keys=False)}---\n\n# Requirement\n",
        encoding="utf-8",
    )
    return path


def test_default_markdown_record_and_direct_work_root(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_records_default")
    _write_tracking_config(tmp_path)
    _write_markdown_record(tmp_path, _record())

    path, record, errors = module.validate_feature_record(
        tmp_path, "FEAT-001", require_accepted=True
    )

    assert path == tmp_path / "docs/features/FEAT-001.md"
    assert record["feature_id"] == "FEAT-001"
    assert errors == []
    assert module.resolve_feature_work_root(
        tmp_path, "FEAT-001"
    ) == tmp_path / ".specify/FEAT-001"


@pytest.mark.parametrize(
    ("format_name", "record_name"),
    [("yaml", "FEAT-001.yml"), ("json", "FEAT-001.json")],
)
def test_configurable_yaml_and_json_records(
    tmp_path: Path, format_name: str, record_name: str
):
    module = _load_module(
        "feature_records.py", f"team_feature_records_{format_name}"
    )
    _write_tracking_config(
        tmp_path,
        root="product/features",
        catalog_file="catalog.yml",
        record_path_template=(
            "{feature_id}.yml"
            if format_name == "yaml"
            else "{feature_id}.json"
        ),
        format=format_name,
        id_pattern="^FEAT-[0-9]{3}$",
    )
    feature_root = tmp_path / "product/features"
    feature_root.mkdir(parents=True)
    data = _record(accepted=False)
    record_path = feature_root / record_name
    if format_name == "yaml":
        record_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    else:
        record_path.write_text(json.dumps(data), encoding="utf-8")
    (feature_root / "catalog.yml").write_text(
        yaml.safe_dump(
            {
                "features": [
                    {
                        "id": "FEAT-001",
                        "record": record_path.relative_to(tmp_path).as_posix(),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    _, _, blocked = module.validate_feature_record(
        tmp_path, "FEAT-001", require_accepted=True
    )
    assert "Feature must be accepted before entering SDD" in blocked

    module.accept_feature_record(
        tmp_path,
        "FEAT-001",
        "architecture-group",
        decided_at="2026-07-27T00:00:00Z",
    )
    path, accepted, errors = module.validate_feature_record(
        tmp_path, "FEAT-001", require_accepted=True
    )
    assert path == record_path
    assert accepted["acceptance"] == {
        "status": "accepted",
        "decided_by": "architecture-group",
        "decided_at": "2026-07-27T00:00:00Z",
        "decision_source": "conversation",
    }
    assert errors == []


def test_missing_l0_l1_does_not_block_feature_record(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_records_no_arch")
    _write_tracking_config(tmp_path)
    _write_markdown_record(tmp_path, _record())

    _, _, errors = module.validate_feature_record(
        tmp_path, "FEAT-001", require_accepted=True
    )

    assert not (tmp_path / "docs/architecture").exists()
    assert errors == []


def test_local_requirement_fallback_requires_named_acceptance(tmp_path: Path):
    module = _load_module("feature_records.py", "team_requirement_record")
    _write_tracking_config(tmp_path)
    record = {
        "schema": "speckit-requirement-record/v1",
        "requirement_id": "REQ-001",
        "title": "Offline collaboration fallback",
        "mode": "existing-project",
        "source": {
            "type": "local-record",
            "issue_url": "",
            "publication_attempted": True,
            "fallback_reason": "Git host was unavailable.",
            "fallback_selected_by": "repository-owner",
            "fallback_selected_at": "2026-07-25T00:00:00Z",
        },
        "acceptance": {
            "status": "proposed",
            "decided_by": "",
            "decided_at": "",
        },
        "architecture": {
            "l0_status": "not-present",
            "l0_path": "",
            "l1_status": "not-present",
            "l1_path": "",
        },
    }
    path = _write_requirement_record(tmp_path, record)

    _, _, errors = module.validate_local_requirement_record(
        tmp_path,
        path.relative_to(tmp_path).as_posix(),
        require_accepted=True,
    )
    assert "local Requirement must be accepted before Feature Split" in errors

    record["acceptance"] = {
        "status": "accepted",
        "decided_by": "repository-owner",
        "decided_at": "2026-07-25T00:00:00Z",
    }
    _write_requirement_record(tmp_path, record)
    _, _, errors = module.validate_local_requirement_record(
        tmp_path,
        "docs/requirements/REQ-001.md",
        require_accepted=True,
    )
    assert errors == []


def test_new_project_local_requirement_requires_accepted_l0(tmp_path: Path):
    module = _load_module("feature_records.py", "team_requirement_record_l0")
    _write_tracking_config(tmp_path)
    path = _write_requirement_record(
        tmp_path,
        {
            "schema": "speckit-requirement-record/v1",
            "requirement_id": "REQ-002",
            "title": "New project",
            "mode": "new-project",
            "source": {
                "type": "local-record",
                "issue_url": "",
                "publication_attempted": True,
                "fallback_reason": "Git host was unavailable.",
                "fallback_selected_by": "repository-owner",
                "fallback_selected_at": "2026-07-25T00:00:00Z",
            },
            "acceptance": {
                "status": "accepted",
                "decided_by": "repository-owner",
                "decided_at": "2026-07-25T00:00:00Z",
            },
            "architecture": {
                "l0_status": "not-present",
                "l0_path": "",
                "l1_status": "not-present",
                "l1_path": "",
            },
        },
    )

    _, _, errors = module.validate_local_requirement_record(
        tmp_path, path.relative_to(tmp_path).as_posix(), require_accepted=True
    )

    assert "new-project local Requirement requires accepted L0" in errors


def test_unaccepted_feature_is_blocked_from_sdd(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_records_acceptance")
    _write_tracking_config(tmp_path)
    _write_markdown_record(tmp_path, _record(accepted=False))

    _, _, errors = module.validate_feature_record(
        tmp_path, "FEAT-001", require_accepted=True
    )

    assert "Feature must be accepted before entering SDD" in errors


def test_specifying_feature_requires_written_behavior_before_confirmation(
    tmp_path: Path,
):
    module = _load_module("feature_records.py", "team_feature_behavior_missing")
    _write_tracking_config(tmp_path)
    data = _record(phase="specifying")
    data["behavior_acceptance"] = {
        "status": "proposed",
        "decided_by": "",
        "decided_at": "",
        "decision_source": "",
    }
    path = _write_markdown_record(tmp_path, data)
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "- VER-001: The observable result is produced.", ""
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Verification must be written back"):
        module.accept_feature_behavior(tmp_path, "FEAT-001", "product-owner")


def test_human_can_confirm_written_behavior_and_unlock_planning(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_behavior_accept")
    _write_tracking_config(tmp_path)
    data = _record(phase="specifying")
    data["behavior_acceptance"] = {
        "status": "proposed",
        "decided_by": "",
        "decided_at": "",
        "decision_source": "",
    }
    _write_markdown_record(tmp_path, data)

    _, updated = module.accept_feature_behavior(
        tmp_path,
        "FEAT-001",
        "product-owner",
        decided_at="2026-07-27T02:00:00Z",
    )
    assert updated["behavior_acceptance"] == {
        "status": "accepted",
        "decided_by": "product-owner",
        "decided_at": "2026-07-27T02:00:00Z",
        "decision_source": "conversation",
    }

    path = tmp_path / "docs/features/FEAT-001.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("phase: specifying", "phase: planning")
    path.write_text(text, encoding="utf-8")
    _, _, errors = module.validate_feature_record(
        tmp_path, "FEAT-001", previous_phase="specifying"
    )
    assert errors == []


def test_planning_is_blocked_without_detailed_behavior_confirmation(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_behavior_gate")
    _write_tracking_config(
        tmp_path, behavior_confirmation={"mode": "required"}
    )
    data = _record(phase="planning")
    data["behavior_acceptance"] = {
        "status": "proposed",
        "decided_by": "",
        "decided_at": "",
        "decision_source": "",
    }
    _write_markdown_record(tmp_path, data)

    _, _, errors = module.validate_feature_record(tmp_path, "FEAT-001")

    assert "detailed behavior must be accepted before leaving specifying" in errors


def test_legacy_config_keeps_unconfirmed_planning_record_advisory(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_behavior_legacy")
    _write_tracking_config(tmp_path)
    data = _record(phase="planning")
    data.pop("behavior_acceptance")
    _write_markdown_record(tmp_path, data)

    _, _, errors = module.validate_feature_record(tmp_path, "FEAT-001")

    assert "detailed behavior must be accepted before leaving specifying" not in errors
    assert module.load_tracking(tmp_path).behavior_confirmation_mode == "advisory"


def test_explicit_advisory_mode_does_not_block_planning(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_behavior_advisory")
    _write_tracking_config(
        tmp_path, behavior_confirmation={"mode": "advisory"}
    )
    data = _record(phase="planning")
    data["behavior_acceptance"] = {"status": "proposed"}

    _write_markdown_record(tmp_path, data)

    _, _, errors = module.validate_feature_record(tmp_path, "FEAT-001")

    assert "detailed behavior must be accepted before leaving specifying" not in errors


def test_disabled_mode_rejects_local_behavior_decision(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_behavior_disabled")
    _write_tracking_config(
        tmp_path, behavior_confirmation={"mode": "disabled"}
    )
    _write_markdown_record(tmp_path, _record(phase="specifying"))

    with pytest.raises(ValueError, match="disabled by policy"):
        module.accept_feature_behavior(tmp_path, "FEAT-001", "product-owner")


def test_invalid_behavior_confirmation_mode_is_rejected(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_behavior_invalid")
    _write_tracking_config(
        tmp_path, behavior_confirmation={"mode": "sometimes"}
    )

    with pytest.raises(ValueError, match="behavior_confirmation.mode"):
        module.load_tracking(tmp_path)


def test_planning_validates_referenced_shared_contract(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_shared_contract")
    _write_tracking_config(tmp_path)
    data = _record(phase="planning")
    data["shared_contracts"] = ["docs/architecture/contracts/query.md"]
    _write_markdown_record(tmp_path, data)

    _, _, missing_errors = module.validate_feature_record(tmp_path, "FEAT-001")
    assert "shared contract is missing: docs/architecture/contracts/query.md" in missing_errors

    contract = tmp_path / "docs/architecture/contracts/query.md"
    contract.parent.mkdir(parents=True)
    contract.write_text("# Query contract\n", encoding="utf-8")
    _, _, errors = module.validate_feature_record(tmp_path, "FEAT-001")
    assert errors == []


def test_shared_contract_path_cannot_escape_repository(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_shared_contract_path")
    _write_tracking_config(tmp_path)
    data = _record(phase="planning")
    data["shared_contracts"] = ["../outside.md"]
    _write_markdown_record(tmp_path, data)

    _, _, errors = module.validate_feature_record(tmp_path, "FEAT-001")

    assert "shared contract path must remain repository-relative" in errors


def test_ready_to_merge_requires_complete_dod(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_records_dod")
    _write_tracking_config(tmp_path)
    _write_markdown_record(tmp_path, _record(phase="ready-to-merge"))

    _, _, errors = module.validate_feature_record(tmp_path, "FEAT-001")

    assert "Definition of Done is incomplete: code_complete" in errors
    assert (
        "ready-to-merge Feature without an online pull request requires "
        "delivery.review_target.type local-diff"
    ) in errors


def test_ready_to_merge_prefers_url_but_accepts_immutable_local_diff(
    tmp_path: Path,
):
    module = _load_module("feature_records.py", "team_feature_records_review_target")
    _write_tracking_config(tmp_path)
    data = _record(phase="ready-to-merge")
    data["definition_of_done"] = {
        "code_complete": True,
        "tests_complete": True,
        "evidence_complete": True,
        "architecture_synchronized": True,
        "review_passed": True,
    }
    data["delivery"]["review_target"] = {
        "type": "local-diff",
        "url": "",
        "revision": "sha256:" + ("a" * 64),
    }
    _write_markdown_record(tmp_path, data)

    _, _, errors = module.validate_feature_record(tmp_path, "FEAT-001")

    assert errors == []


def test_ready_to_merge_rejects_local_sentinel_as_pull_request(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_records_fake_pr")
    _write_tracking_config(tmp_path)
    data = _record(phase="ready-to-merge")
    data["definition_of_done"] = {
        "code_complete": True,
        "tests_complete": True,
        "evidence_complete": True,
        "architecture_synchronized": True,
        "review_passed": True,
    }
    data["delivery"]["pull_request"] = "local=true"
    _write_markdown_record(tmp_path, data)

    _, _, errors = module.validate_feature_record(tmp_path, "FEAT-001")

    assert "delivery.pull_request must be a verified HTTP(S) URL" in errors


def test_implementation_requires_resolved_safe_architecture_impact(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_records_architecture")
    _write_tracking_config(tmp_path)
    data = _record(phase="tasks-ready")
    data["architecture_impact"] = {
        "level": "pending",
        "update_required": True,
        "reason": "",
        "affected_files": ["../outside.md"],
    }
    _write_markdown_record(tmp_path, data)

    _, _, errors = module.validate_feature_record(tmp_path, "FEAT-001")

    assert "architecture_impact.affected_files must stay repository-relative" in errors
    assert "architecture impact must be resolved before implementation" in errors


def test_legal_and_illegal_delivery_transitions():
    module = _load_module("feature_records.py", "team_feature_records_transition")

    assert module.validate_transition("planning", "tasks-ready") == []
    assert module.validate_transition("planning", "done") == [
        "illegal delivery transition: planning -> done"
    ]


def test_feature_record_rejects_path_traversal(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_records_traversal")
    _write_tracking_config(
        tmp_path, record_path_template="../../{feature_id}.md"
    )

    with pytest.raises(ValueError, match="must stay under"):
        module.resolve_feature_record(tmp_path, "FEAT-001")


def test_legacy_feature_work_root_is_reused(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_records_legacy")
    _write_tracking_config(tmp_path)
    legacy = tmp_path / ".specify/feature/FEAT-001"
    legacy.mkdir(parents=True)

    assert module.resolve_feature_work_root(tmp_path, "FEAT-001") == legacy


def test_feature_location_must_be_confirmed_once(tmp_path: Path):
    module = _load_module("feature_records.py", "team_feature_records_location")
    config = tmp_path / ".specify/team/ai-team-config.yml"
    config.parent.mkdir(parents=True)
    config.write_text(
        yaml.safe_dump(
            {
                "feature_tracking": {
                    "root": "",
                    "recommended_root": "docs/features",
                    "location": {
                        "status": "pending-confirmation",
                        "locked": False,
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="ask the user once"):
        module.load_tracking(tmp_path)


def test_confirmed_feature_location_is_persisted_and_locked(tmp_path: Path):
    module = _load_module(
        "configure_feature_tracking.py", "team_configure_feature_tracking"
    )

    path = module.configure(
        tmp_path,
        "product/features",
        "repository-owner",
        decided_at="2026-07-25T00:00:00Z",
    )
    config = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert config["feature_tracking"]["root"] == "product/features"
    assert config["feature_tracking"]["location"] == {
        "status": "confirmed",
        "locked": True,
        "decided_by": "repository-owner",
        "decided_at": "2026-07-25T00:00:00Z",
    }
    module.configure(tmp_path, "product/features", "another-user")
    unchanged = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert unchanged["feature_tracking"]["location"]["decided_by"] == "repository-owner"
    with pytest.raises(ValueError, match="already locked"):
        module.configure(tmp_path, "docs/features", "repository-owner")

    compact = module.snapshot(tmp_path)
    assert compact["root"] == "product/features"
    assert compact["location"]["locked"] is True
    assert "issue_publishing" not in compact
