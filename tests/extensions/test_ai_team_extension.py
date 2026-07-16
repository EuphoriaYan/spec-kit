import json
import importlib.util
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ROOT = REPO_ROOT / "extensions" / "team"
MEMORY_ADAPTER_PATH = EXTENSION_ROOT / "scripts" / "memory_adapter.py"
WORK_ITEM_PATHS = EXTENSION_ROOT / "scripts" / "work_item_paths.py"


def _load_memory_adapter():
    spec = importlib.util.spec_from_file_location("ai_team_memory_adapter", MEMORY_ADAPTER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_script(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _memory_card(tier: str, privacy: str = "department-internal") -> str:
    return f"""---
memory_type: bugfix_lesson
tier: {tier}
privacy: {privacy}
owner: module-maintainer
---

# Retry exhaustion

- Root cause: retry budget was shared across requests.
"""


def _staged_card(tmp_path: Path, name: str, content: str) -> Path:
    source = tmp_path / ".specify" / "team" / "memory" / "staging" / name
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(content, encoding="utf-8")
    return source


def test_feature_and_bugfix_share_one_directory_contract(tmp_path: Path):
    module = _load_script(WORK_ITEM_PATHS, "ai_team_work_item_paths")

    feature = module.resolve_work_root(tmp_path, "feature", "123")
    bugfix = module.resolve_work_root(tmp_path, "bugfix", "456")

    assert feature.relative_to(tmp_path).as_posix() == ".specify/feature/123"
    assert bugfix.relative_to(tmp_path).as_posix() == ".specify/bugfix/456"
    assert len(feature.relative_to(tmp_path).parts) == len(bugfix.relative_to(tmp_path).parts)
    assert module.resolve_work_root(tmp_path, "new-project", "REQ-7") == tmp_path / ".specify/feature/REQ-7"
    with pytest.raises(ValueError, match="safe stable identifier"):
        module.resolve_work_root(tmp_path, "feature", "../escape")


def test_ai_team_extension_manifest_and_catalog_are_in_sync():
    manifest = yaml.safe_load(
        (EXTENSION_ROOT / "extension.yml").read_text(encoding="utf-8")
    )
    catalog = json.loads(
        (REPO_ROOT / "extensions" / "catalog.json").read_text(encoding="utf-8")
    )

    assert manifest["extension"]["id"] == "team"
    assert "team" in catalog["extensions"]
    assert (
        catalog["extensions"]["team"]["version"]
        == manifest["extension"]["version"]
    )
    assert catalog["extensions"]["team"]["bundled"] is True


def test_ai_team_extension_command_files_exist():
    manifest = yaml.safe_load(
        (EXTENSION_ROOT / "extension.yml").read_text(encoding="utf-8")
    )

    assert "commands" not in manifest["requires"]
    assert "hooks" not in manifest

    command_names = {command["name"] for command in manifest["provides"]["commands"]}
    assert command_names == {
        "speckit.team.specify",
        "speckit.team.plan-and-task",
        "speckit.team.assess",
        "speckit.team.fix",
        "speckit.team.implement",
        "speckit.team.review",
    }

    for command in manifest["provides"]["commands"]:
        command_file = EXTENSION_ROOT / command["file"]
        assert command_file.exists(), command["file"]
        assert command_file.read_text(encoding="utf-8").startswith("---\n")

def test_ai_team_config_template_defines_repository_and_role_contracts():
    config = yaml.safe_load(
        (EXTENSION_ROOT / "config-template.yml").read_text(encoding="utf-8")
    )

    assert set(config["repositories"]) == {
        "enhancement_internal",
        "coding",
    }
    assert config["bootstrap"]["use_specify_init"] is True
    assert set(config["agent_tools"]["supported_integrations"]) == {
        "codex",
        "claude",
        "cursor-agent",
        "trae",
    }
    assert config["work_artifacts"]["root"] == ".specify"
    assert config["work_artifacts"]["categories"] == ["feature", "bugfix"]
    assert config["work_artifacts"]["path_template"] == ".specify/{category}/{work_id}"
    assert config["work_artifacts"]["plan_and_task_file"] == "plan-and-task.md"
    assert config["work_artifacts"]["plan_and_task_check_file"] == "plan-and-task-check.md"
    assert config["memory"]["service"]["default_backend"] == "file"
    assert config["memory"]["service"]["supported_backends"] == ["file", "mem0"]
    assert config["memory"]["service"]["mem0"]["optional_package"] == "mem0ai"
    assert config["memory"]["service"]["store_raw_transcripts_by_default"] is False
    assert config["memory"]["tiers"]["local"]["upload"] is False
    assert config["memory"]["tiers"]["local"]["docs"] is False
    assert config["memory"]["tiers"]["local"]["git_policy"] == "ignore-or-local-only"
    assert config["memory"]["tiers"]["department"]["upload"] is True
    assert config["memory"]["tiers"]["department"]["docs"] is False
    assert (
        config["memory"]["tiers"]["department"]["git_policy"]
        == "internal-only-or-service-sync"
    )
    assert config["memory"]["tiers"]["enterprise"]["upload"] is True
    assert config["memory"]["tiers"]["enterprise"]["docs"] is True
    assert config["memory"]["tiers"]["enterprise"]["git_policy"] == "commit-after-review"
    assert config["release_archive"]["private_root"] == ".specify/team/releases/private"
    assert config["release_archive"]["enterprise_root"] == "docs/ai-team/memory/releases"
    assert config["release_archive"]["default_privacy"] == "department-internal"
    assert config["release_archive"]["default_target_tier"] == "department"
    assert config["release_archive"]["delete_raw_evidence_by_default"] is False
    assert set(config["release_archive"]["enterprise_outputs"]) == {
        "release-summary.md",
        "shipped-work-index.md",
        "bugfix-lessons.md",
        "feature-decisions.md",
        "migration-playbook.md",
    }
    assert set(config["release_archive"]["private_outputs"]) == {
        "evidence-rollup.md",
        "archived-work.yml",
        "privacy-review.md",
    }
    assert "change_package_file" not in config["work_artifacts"]
    assert (
        config["work_artifacts"]["permission_envelope_file"]
        == "permission-envelope.yml"
    )
    assert config["permissions"]["default_enforcement_mode"] == "policy-only"
    assert set(config["permissions"]["supported_enforcement_modes"]) == {
        "policy-only",
        "agent-native",
        "wrapper-enforced",
    }
    assert config["permissions"]["require_envelope"] is True
    assert config["permissions"]["require_analysis_review"] is True
    assert config["permissions"]["require_implementation_review"] is True
    assert config["gates"]["require_work_item_anchor"] is True
    assert config["gates"]["allow_same_root_cause_issue_grouping"] is True
    assert config["planning"]["artifact"] == "plan-and-task.md"
    assert config["planning"]["stages"] == [
        "plan-review",
        "task-design",
        "ready-for-check",
    ]
    assert config["planning"]["require_human_plan_decision_before_tasks"] is True
    assert config["planning"]["plan_review_decisions"] == [
        "continue-to-tasks",
        "pause-for-discussion",
        "revise-plan",
    ]
    assert config["planning"]["final_check_after_task_design"] is True
    assert config["issue_publishing"]["default_adapter"] == "auto"
    assert config["issue_publishing"]["require_verified_issue_url"] is True
    assert config["issue_publishing"]["require_feature_readiness_pass"] is True
    assert config["code_graph"] == {
        "tool": "codegraph",
        "required_version": ">=1.0.0,<2.0.0",
        "local_index": ".codegraph/codegraph.db",
        "evidence_file": "codegraph/summary.md",
        "require_for_existing_project": True,
        "require_for": [
            "public interface change",
            "class add or delete",
            "cross-module semantic change",
            "dependency direction change",
            "resumed task with changed source snapshot",
        ],
    }
    assert (
        config["repositories"]["enhancement_internal"][
            "raw_demand_record_in_coding_repository"
        ]
        is False
    )
    assert (
        config["repositories"]["enhancement_internal"]["visibility"]
        == "internal-only"
    )
    assert config["repositories"]["enhancement_internal"]["customer_visible"] is False
    assert config["issue_lifecycle"]["type_labels"][
        "enhancement_internal_allowed"
    ] == ["type/feature"]
    assert set(config["issue_lifecycle"]["type_labels"]["coding_allowed"]) == {
        "type/feature",
        "type/bugfix",
    }
    assert set(config["issue_lifecycle"]["status_labels"]) == {
        "status/new-issue",
        "status/accept",
        "status/working",
        "status/close",
    }
    assert config["issue_lifecycle"]["enhancement_internal_allows_bugfix"] is False
    assert (
        config["repositories"]["coding"]["enhancement_handoff_submodule_path"] == ""
    )
    assert config["privacy"]["raw_customer_demand_public"] is False
    assert config["privacy"]["coding_repo_may_record_raw_internal_demand"] is False
    assert config["privacy"]["public_feature_may_start_from_coding_issue"] is True
    assert (
        config["privacy"]["internal_feature_requires_handoff_or_public_safe_summary"]
        is True
    )
    assert config["privacy"]["private_handoff_override_file"] == "spec.override.md"
    assert set(config["roles"]) == {"specify", "plan_and_task"}
    assert all(role["context_isolation"] is True for role in config["roles"].values())


def test_memory_adapter_generates_idempotent_git_ignore_rules(tmp_path):
    adapter = _load_memory_adapter()
    (tmp_path / ".gitignore").write_text("dist/\n", encoding="utf-8")

    adapter.ensure_memory_gitignore(tmp_path)
    adapter.ensure_memory_gitignore(tmp_path)

    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert text.startswith("dist/\n")
    assert text.count(adapter.IGNORE_START) == 1
    for ignored in adapter.IGNORE_PATHS:
        assert ignored in text


def test_memory_adapter_private_paths_are_ignored_by_git(tmp_path):
    adapter = _load_memory_adapter()
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    source = _staged_card(tmp_path, "candidate.md", _memory_card("local", "private"))

    result = adapter.persist_memory(
        project_root=tmp_path,
        source=source,
        tier="local",
    )

    destination = tmp_path / result["path"]
    assert destination.exists()
    ignored = subprocess.run(
        ["git", "-C", str(tmp_path), "check-ignore", "-q", str(destination)],
        check=False,
    )
    assert ignored.returncode == 0
    assert result["backend"] == "file"


def test_memory_adapter_writes_enterprise_memory_to_docs(tmp_path):
    adapter = _load_memory_adapter()
    source = _staged_card(
        tmp_path, "reviewed.md", _memory_card("enterprise", "public-safe")
    )

    result = adapter.persist_memory(
        project_root=tmp_path,
        source=source,
        tier="enterprise",
    )

    assert result["path"] == "docs/ai-team/memory/reviewed.md"
    assert (tmp_path / result["index"]).exists()


def test_memory_adapter_mem0_mirrors_sanitized_non_private_card(tmp_path, monkeypatch):
    adapter = _load_memory_adapter()
    source = _staged_card(tmp_path, "department.md", _memory_card("department"))
    config = tmp_path / "config.yml"
    config.write_text(
        """memory:
  service:
    mem0:
      api_key_env: TEST_MEM0_KEY
  tiers:
    department:
      path: .specify/team/memory/department
      namespace: ai-team/example/department
""",
        encoding="utf-8",
    )
    client = MagicMock()
    client.add.return_value = {"id": "memory-123"}
    client_type = MagicMock(return_value=client)
    monkeypatch.setenv("TEST_MEM0_KEY", "secret-not-written")
    monkeypatch.setattr(
        adapter.importlib,
        "import_module",
        lambda _name: SimpleNamespace(MemoryClient=client_type),
    )

    result = adapter.persist_memory(
        project_root=tmp_path,
        source=source,
        tier="department",
        backend="mem0",
        config_path=config,
    )

    client_type.assert_called_once_with(api_key="secret-not-written")
    client.add.assert_called_once()
    assert result["remote"] == {"id": "memory-123"}
    assert "secret-not-written" not in (tmp_path / result["index"]).read_text(
        encoding="utf-8"
    )


def test_memory_adapter_rejects_private_mem0_sync(tmp_path, monkeypatch):
    adapter = _load_memory_adapter()
    source = _staged_card(tmp_path, "private.md", _memory_card("local", "private"))

    with pytest.raises(adapter.MemoryAdapterError, match="cannot be synced"):
        adapter.persist_memory(
            project_root=tmp_path,
            source=source,
            tier="local",
            backend="mem0",
        )


def test_ai_team_support_model_document_exists():
    support_doc = EXTENSION_ROOT / "docs" / "skill-knowledge-memory.md"

    assert support_doc.exists()
    text = support_doc.read_text(encoding="utf-8")
    assert "Skill Layer" in text
    assert "Knowledge Layer" in text
    assert "Memory Layer" in text
    assert "Decision Memory" in text
    assert "Attempt Memory" in text
    assert "Memory Consolidation Flow" in text
    assert "local memory" in text
    assert "department memory" in text
    assert "enterprise memory" in text
    assert "mem0-style memory" in text
    assert "release-summary.md" in text
    assert "bugfix-lessons.md" in text
    assert "Third-party sources to review" in text
    assert "Precedence" in text


def test_ai_team_memory_tiers_document_exists():
    memory_doc = EXTENSION_ROOT / "docs" / "memory-tiers.md"

    assert memory_doc.exists()
    text = memory_doc.read_text(encoding="utf-8")
    assert "AI Team Memory Tiers" in text
    assert "local memory" in text
    assert "department memory" in text
    assert "enterprise memory" in text
    assert "mem0-style memory" in text


def test_ai_team_release_archive_document_exists():
    release_doc = EXTENSION_ROOT / "docs" / "release-archive.md"

    assert release_doc.exists()
    text = release_doc.read_text(encoding="utf-8")
    assert "Release Archive and Knowledge Consolidation" in text
    assert "bugfix-lessons.md" in text
    assert "migration-playbook.md" in text
    assert "not a mandatory pre-release gate" in text
    assert "public-safe" in text


def test_ai_team_repository_boundary_document_exists():
    boundary_doc = EXTENSION_ROOT / "docs" / "repository-boundary.md"

    assert boundary_doc.exists()
    text = boundary_doc.read_text(encoding="utf-8")
    assert "enhancement-internal" in text
    assert "coding issue URL" in text
    assert "Handoff requirement" in text
    assert "Do not use a local path" in text
    assert "type/feature" in text
    assert "type/bugfix" in text


def test_ai_team_issue_lifecycle_document_exists():
    issue_doc = EXTENSION_ROOT / "docs" / "issue-lifecycle.md"

    assert issue_doc.exists()
    text = issue_doc.read_text(encoding="utf-8")
    assert "enhancement repository" in text
    assert "`type/feature`" in text
    assert "`type/bugfix`" in text
    assert "status/new-issue" in text
    assert "status/accept" in text
    assert "status/close" in text


def test_ai_team_work_context_document_exists():
    context_doc = EXTENSION_ROOT / "docs" / "work-context-package.md"

    assert context_doc.exists()
    text = context_doc.read_text(encoding="utf-8")
    assert "Work Context Package" in text
    assert ".specify/<feature|bugfix>/<work_id>/" in text
    assert "work-context.yml" in text
    assert "change-package.yml" not in text
    assert "permission-envelope.yml" in text
    assert ".specify/workflows/runs/<run-id>/state.json" not in text
    assert "plan-and-task.md" in text
    assert "plan-and-task-check.md" in text
    assert "resume anchor" in text


def test_ai_team_reuses_native_sdd_artifacts_without_change_manifest():
    assert not (EXTENSION_ROOT / "docs" / "change-package.md").exists()
    readme = (EXTENSION_ROOT / "README.md").read_text(encoding="utf-8")
    assert "`spec.md`" in readme
    assert "human decision" in readme.lower()
    assert "change-package.yml" not in readme


def test_ai_team_readme_matches_current_role_contracts():
    readme = (EXTENSION_ROOT / "README.md").read_text(encoding="utf-8")

    assert "`draft`, `approved`, or `needs-info`" in readme
    assert ".specify/bugfix/<bug_slug>/" in readme
    assert "passing `plan-and-task-check.md`" in readme
    assert "Assess,\nFix, and Review install no role references or scripts" in readme
    assert "init_role_context.py` runs during project initialization" in readme
    assert "specify extension add extensions/team --dev" in readme
    assert "specify extension add team --dev extensions/team" not in readme


def test_ai_team_permission_envelope_document_exists():
    permission_doc = EXTENSION_ROOT / "docs" / "permission-envelope.md"

    assert permission_doc.exists()
    text = permission_doc.read_text(encoding="utf-8")
    assert "permission-envelope.yml" in text
    assert "policy-only" in text
    assert "agent-native" in text
    assert "wrapper-enforced" in text
    assert "status: pending-review" in text
    assert "approved_at" in text
    assert "do not sandbox shell commands" in text


def test_ai_team_code_graph_contract_is_reference_not_nested_command():
    contract = EXTENSION_ROOT / "docs" / "code-graph-contract.md"

    text = contract.read_text(encoding="utf-8")
    assert "## Evidence" in text
    assert "## Stop Conditions" in text
    assert "Do not create a separate generic impact artifact" in text
    assert "source-structure fallback" in text
    assert "$ARGUMENTS" not in text
    assert "## User Input" not in text


def test_ai_team_uses_one_plan_review_then_task_decomposition_flow():
    command = EXTENSION_ROOT / "commands" / "speckit.team.plan-and-task.md"
    text = command.read_text(encoding="utf-8")

    assert "continue to Tasks" in text
    assert "pause for discussion" in text
    assert "planning_stage: ready-for-check" in text
    assert not (EXTENSION_ROOT / "docs" / "compact-planning.md").exists()


def test_ai_team_work_field_spec_document_exists():
    field_doc = EXTENSION_ROOT / "docs" / "work-field-spec.md"

    assert field_doc.exists()
    text = field_doc.read_text(encoding="utf-8")
    assert "work_id" in text
    assert "work_type" in text
    assert ".specify/feature/<work_id>/" in text
    assert ".specify/bugfix/<work_id>/" in text
    assert "one root-cause change" in text


def test_core_templates_exclude_handoff_spec_override():
    """Core command templates must not embed AI Team handoff / override logic."""
    for rel in (
        "templates/commands/plan.md",
        "templates/commands/tasks.md",
        "templates/commands/checklist.md",
        "templates/commands/analyze.md",
        "templates/commands/implement.md",
        "templates/commands/converge.md",
        "templates/plan-template.md",
    ):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert "handoff_requirement_url" not in text, rel
        assert "spec.override.md" not in text, rel


def test_ai_team_uses_required_codegraph_without_adapter_fallbacks():
    assert not (EXTENSION_ROOT / "docs" / "code-graph-adapters.md").exists()

    graph_ref = EXTENSION_ROOT / "docs" / "code-graph-contract.md"
    text = graph_ref.read_text(encoding="utf-8")
    assert "codegraph version" in text
    assert "codegraph status" in text
    assert "codegraph explore" in text
    assert "not a replaceable adapter" in text
    assert "source-structure fallback" in text


def test_ai_team_user_journeys_document_exists():
    journeys_doc = EXTENSION_ROOT / "docs" / "user-journeys.md"

    assert journeys_doc.exists()
    text = journeys_doc.read_text(encoding="utf-8")
    assert "One-Sentence Feature" in text
    assert "Existing Public Feature Issue" in text
    assert "Confidential Enterprise Feature" in text
    assert "Bugfix" in text
    assert "New Project" in text
    assert "Plan Discussion And Task Decomposition" in text
    assert "Resume" in text
    for command in (
        "speckit.team.specify",
        "speckit.team.plan-and-task",
        "speckit.team.assess",
        "speckit.team.fix",
        "speckit.team.implement",
        "speckit.team.review",
    ):
        assert command in text


def test_ai_team_role_skills_do_not_register_workflows():
    catalog = json.loads(
        (REPO_ROOT / "workflows" / "catalog.json").read_text(encoding="utf-8")
    )
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    bundle_catalog = json.loads(
        (REPO_ROOT / "bundles" / "catalog.json").read_text(encoding="utf-8")
    )

    assert "ai-team-sdd" not in catalog["workflows"]
    assert "ai-team-bugfix" not in catalog["workflows"]
    assert "workflows/ai-team-sdd" not in pyproject
    assert "workflows/ai-team-bugfix" not in pyproject
    assert bundle_catalog["bundles"] == {}
