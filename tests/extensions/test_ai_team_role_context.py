from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
AI_TEAM = REPO_ROOT / "extensions" / "team"
INIT_SCRIPT = AI_TEAM / "scripts" / "init_role_context.py"


def _load_init_module():
    spec = importlib.util.spec_from_file_location("ai_team_init_context", INIT_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _install_bootstrap(project: Path) -> None:
    target = project / ".specify/extensions/team/docs/context-bootstrap.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Installed bootstrap\n", encoding="utf-8")


def test_all_six_role_commands_are_registered() -> None:
    manifest = yaml.safe_load((AI_TEAM / "extension.yml").read_text(encoding="utf-8"))
    provided = {item["name"]: item for item in manifest["provides"]["commands"]}
    assert set(provided) == {
        "speckit.team.specify",
        "speckit.team.plan-and-task",
        "speckit.team.assess",
        "speckit.team.fix",
        "speckit.team.implement",
        "speckit.team.review",
    }
    assert {path.stem for path in (AI_TEAM / "commands").glob("*.md")} == set(provided)


def test_context_initializer_merges_supported_agent_files_idempotently(tmp_path: Path) -> None:
    _install_bootstrap(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Existing project rules\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("dist/\n", encoding="utf-8")
    specify = tmp_path / ".specify"
    specify.mkdir(exist_ok=True)
    (specify / "integration.json").write_text(
        json.dumps(
            {
                "active_integration": "codex",
                "installed_integrations": ["codex", "claude", "cursor-agent", "trae"],
            }
        ),
        encoding="utf-8",
    )

    module = _load_init_module()
    first = module.initialize(tmp_path)
    second = module.initialize(tmp_path)

    assert first == second == [
        "AGENTS.md",
        "CLAUDE.md",
        ".cursor/rules/specify-rules.mdc",
        ".trae/rules/project_rules.md",
    ]
    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "# Existing project rules" in agents
    assert agents.count(module.START) == 1
    assert module.BOOTSTRAP in agents
    claude = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude.count(module.START) == 1
    assert "@AGENTS.md" in claude
    assert module.BOOTSTRAP not in claude
    cursor = (tmp_path / ".cursor/rules/specify-rules.mdc").read_text(encoding="utf-8")
    assert "alwaysApply: true" in cursor
    assert cursor.count(module.START) == 1
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == "dist/\n"


def test_context_initializer_always_writes_agents_without_detected_tool(tmp_path: Path) -> None:
    _install_bootstrap(tmp_path)
    module = _load_init_module()

    assert module.initialize(tmp_path) == ["AGENTS.md"]
    assert module.BOOTSTRAP in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")


def test_context_initializer_writes_natural_language_skill_router(tmp_path: Path) -> None:
    _install_bootstrap(tmp_path)
    module = _load_init_module()

    module.initialize(tmp_path)

    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Users may describe work naturally" in agents
    assert "speckit.team.specify" in agents
    assert "speckit.team.plan-and-task" in agents
    assert "speckit.team.assess" in agents
    assert "speckit.team.fix" in agents
    assert "speckit.team.implement" in agents
    assert "speckit.team.review" in agents
    assert ".specify/<feature|bugfix>/<work_id>/" in agents


def test_router_only_includes_approved_role_skills(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_init_module()
    installed = tmp_path / "team"
    scripts = installed / "scripts"
    commands = installed / "commands"
    scripts.mkdir(parents=True)
    commands.mkdir()
    fake_script = scripts / "init_role_context.py"
    fake_script.write_text("# location marker\n", encoding="utf-8")
    for name, _, _ in module.ROUTES:
        (commands / f"{name}.md").write_text("# role\n", encoding="utf-8")
    monkeypatch.setattr(module, "__file__", str(fake_script))

    section = module._managed_section("AGENTS.md")

    for name, _, _ in module.ROUTES:
        assert name in section


def test_direct_team_setup_rolls_back_extension_when_rules_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from specify_cli import team_setup

    specify = tmp_path / ".specify"
    specify.mkdir()
    (specify / "init-options.json").write_text(
        json.dumps({"ai": "codex", "ai_skills": True}), encoding="utf-8"
    )
    (tmp_path / ".claude" / "skills").mkdir(parents=True)
    monkeypatch.setattr(team_setup, "_locate_bundled_extension", lambda _id: AI_TEAM)

    def fail_rules(_root: Path) -> list[str]:
        raise RuntimeError("rule failure")

    monkeypatch.setattr(team_setup, "_initialize_rules", fail_rules)

    with pytest.raises(RuntimeError, match="rule failure"):
        team_setup.install_bundled_team(tmp_path)

    assert not (specify / "extensions" / "team").exists()
    assert not (specify / "extensions" / ".backup" / "team").exists()
    assert not (tmp_path / ".agents" / "skills" / "speckit-team-specify").exists()
    assert not (tmp_path / ".claude" / "skills" / "speckit-team-specify").exists()


@pytest.mark.parametrize(
    ("integration", "skills_dir"),
    [
        ("codex", ".agents/skills"),
        ("claude", ".claude/skills"),
        ("cursor-agent", ".cursor/skills"),
        ("trae", ".trae/skills"),
    ],
)
def test_team_skills_install_with_local_references_and_scripts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    integration: str,
    skills_dir: str,
) -> None:
    from specify_cli import team_setup

    specify = tmp_path / ".specify"
    specify.mkdir()
    (specify / "init-options.json").write_text(
        json.dumps(
            {"ai": integration, "integration": integration, "ai_skills": True}
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(team_setup, "_locate_bundled_extension", lambda _id: AI_TEAM)

    team_setup.install_bundled_team(tmp_path)

    root = tmp_path / skills_dir
    specify_skill = root / "speckit-team-specify"
    plan_skill = root / "speckit-team-plan-and-task"
    assess_skill = root / "speckit-team-assess"
    fix_skill = root / "speckit-team-fix"
    implement_skill = root / "speckit-team-implement"
    review_skill = root / "speckit-team-review"
    assert (specify_skill / "SKILL.md").is_file()
    assert {
        path.name for path in (specify_skill / "references").glob("*.md")
    } == {"repository-boundary.md"}
    assert not (specify_skill / "scripts/init_role_context.py").exists()
    assert {
        path.name for path in (plan_skill / "references").glob("*.md")
    } == {
        "code-graph-adapters.md",
        "code-graph-contract.md",
        "context.md",
        "feature-spec.md",
        "handoff-spec-sync.md",
        "permission-envelope.md",
        "plan-and-task-format.md",
    }
    assert (plan_skill / "scripts/check_plan_and_task.py").is_file()
    assert (plan_skill / "scripts/check_permission_envelope.py").is_file()
    assert (plan_skill / "scripts/work_item_paths.py").is_file()
    for skill in (assess_skill, fix_skill, review_skill):
        assert (skill / "SKILL.md").is_file()
        assert not (skill / "references").exists()
        assert not (skill / "scripts").exists()
    assert {
        path.name for path in (implement_skill / "references").glob("*.md")
    } == {"implement-pr.md"}
    assert (implement_skill / "scripts/check_permission_envelope.py").is_file()
    assert (implement_skill / "scripts/work_item_paths.py").is_file()


def test_context_initializer_repairs_cursor_auto_load(tmp_path: Path) -> None:
    _install_bootstrap(tmp_path)
    cursor = tmp_path / ".cursor/rules/specify-rules.mdc"
    cursor.parent.mkdir(parents=True)
    cursor.write_text("---\nalwaysApply: false\n---\n\n# Existing\n", encoding="utf-8")
    specify = tmp_path / ".specify"
    (specify / "integration.json").write_text(
        json.dumps({"installed_integrations": ["cursor-agent"]}), encoding="utf-8"
    )

    module = _load_init_module()
    module.initialize(tmp_path)

    text = cursor.read_text(encoding="utf-8")
    assert "alwaysApply: true" in text
    assert "alwaysApply: false" not in text
    assert "# Existing" in text


def test_context_initializer_restores_all_rule_files_on_failure(tmp_path: Path) -> None:
    _install_bootstrap(tmp_path)
    agents = tmp_path / "AGENTS.md"
    claude = tmp_path / "CLAUDE.md"
    agents.write_text("# Existing agents\n", encoding="utf-8")
    claude.write_text("<!-- AI TEAM CONTEXT START -->\nbroken\n", encoding="utf-8")
    specify = tmp_path / ".specify"
    (specify / "integration.json").write_text(
        json.dumps({"installed_integrations": ["claude"]}), encoding="utf-8"
    )
    module = _load_init_module()

    with pytest.raises(ValueError, match="Unbalanced"):
        module.initialize(tmp_path)

    assert agents.read_text(encoding="utf-8") == "# Existing agents\n"
    assert claude.read_text(encoding="utf-8") == (
        "<!-- AI TEAM CONTEXT START -->\nbroken\n"
    )


def test_specify_role_contract_keeps_issue_and_user_story_model() -> None:
    text = (AI_TEAM / "commands/speckit.team.specify.md").read_text(
        encoding="utf-8"
    )

    assert "Publish or print one" in text or "publish or print one" in text
    assert "one Story at a time" in text
    assert "type/feature" in text
    assert "status/new-issue" in text
    assert "Do\nnot persist the checklist or an Issue draft" in text
    assert "Do not create local requirement drafts, `spec.md`" in text


def test_specify_converses_before_one_non_persistent_readiness_pass() -> None:
    text = (AI_TEAM / "commands/speckit.team.specify.md").read_text(
        encoding="utf-8"
    )

    assert "Conversation First" in text
    assert "After the demand is substantially understood" in text
    assert "For every User Story" in text
    assert "Do\nnot persist the checklist or an Issue draft" in text
    assert "output only" in text
    assert "fall back to `output only`" in text


def test_publication_approval_is_not_feature_acceptance() -> None:
    specify = (AI_TEAM / "commands/speckit.team.specify.md").read_text(
        encoding="utf-8"
    )
    for action in ("publish", "output only", "revise", "stop"):
        assert f"`{action}`" in specify
    assert "Publishing creates `status/new-issue`" in specify
    assert "Never assign\n`status/accept`" in specify

    internal_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (AI_TEAM / "references/internal").glob("*.md")
    )
    assert "the human Feature acceptance gate" not in internal_text


def test_plan_and_task_role_uses_core_artifact_scripts_without_prompt_chain() -> None:
    text = (AI_TEAM / "commands/speckit.team.plan-and-task.md").read_text(
        encoding="utf-8"
    )

    for removed_command in (
        "speckit.plan`",
        "speckit.tasks`",
        "speckit.analyze",
    ):
        assert removed_command not in text
    assert "minimum self-test" in text
    assert "LLD-level" in text
    assert "self-verification scenario" in text
    assert "plan-and-task-check.md" in text
    assert ".specify/<feature|bugfix>/<work_id>/plan-and-task.md" in text
    assert "Produce technical planning artifacts without" in text


def test_plan_and_task_has_structured_input_contract() -> None:
    text = (AI_TEAM / "commands/speckit.team.plan-and-task.md").read_text(
        encoding="utf-8"
    )

    assert "required user input is one primary Issue URL" in text
    assert "status/accept" in text
    assert "Issue Identity And Summary" in text
    assert "Read the current Issue body and all relevant discussion" in text
    assert "Code Graph slice tied to the exact source revision" in text
    assert "Design Tasks for parallel assignment" in text
    assert "Every Task belongs to one" in text
    assert "enhancement-<issue-id>" in text


def test_team_work_item_layout_and_templates_are_unified() -> None:
    layout = (AI_TEAM / "docs/work-item-layout.md").read_text(encoding="utf-8")
    assert ".specify/" in layout
    assert "feature/" in layout
    assert "bugfix/" in layout
    assert "<work_id>/" in layout

    expected = {"plan-and-task-template.md", "work-context-template.yml"}
    assert {path.name for path in (AI_TEAM / "templates").iterdir() if path.is_file()} == expected
    assert "plan-and-task.md" in layout
    assert "plan-and-task-check.md" in layout


def test_role_commands_require_repeatable_progressive_bootstrap() -> None:
    bootstrap = (AI_TEAM / "docs/context-bootstrap.md").read_text(encoding="utf-8")
    assert "after resume or context\ncompression" in bootstrap
    assert "Level 0: Always Load" in bootstrap
    assert "Level 1: Active Role Only" in bootstrap
    for role in (
        "Business / Product",
        "Architect",
        "Bug Assessor",
        "Bug Fixer",
        "Developer",
        "Reviewer",
    ):
        assert role in bootstrap
    for command in (AI_TEAM / "commands").glob("*.md"):
        text = command.read_text(encoding="utf-8")
        assert "scripts/init_role_context.py" not in text
        assert "context-bootstrap.md" not in text
        assert "## Bootstrap" not in text
        assert "relative to this installed `SKILL.md`" not in text
        assert "relative to the repository working directory" not in text

    manifest = (AI_TEAM / "extension.yml").read_text(encoding="utf-8")
    assert "target: references/context-bootstrap.md" not in manifest


def test_role_skills_load_references_only_at_the_phase_that_needs_them() -> None:
    specify = (AI_TEAM / "commands/speckit.team.specify.md").read_text(
        encoding="utf-8"
    )
    plan = (AI_TEAM / "commands/speckit.team.plan-and-task.md").read_text(
        encoding="utf-8"
    )
    implement = (AI_TEAM / "commands/speckit.team.implement.md").read_text(
        encoding="utf-8"
    )

    assert "If the repository or privacy boundary is unclear" in specify
    assert "Do not preload it" in specify
    assert "When resuming an existing work root" in plan
    assert "immediately before writing it" in plan
    assert "only when an adapter must be selected" in plan
    assert "approved_at" in plan
    assert "--require-approved" in plan
    assert "immediately before creating or\n   updating `plan-and-task.md`" in plan
    assert "Do not reproduce, guess, or preload" in implement


def test_team_manifest_has_minimal_per_skill_resource_sets() -> None:
    manifest = yaml.safe_load((AI_TEAM / "extension.yml").read_text(encoding="utf-8"))
    commands = {
        item["name"]: {
            resource["target"] for resource in item.get("resources", [])
        }
        for item in manifest["provides"]["commands"]
    }

    assert commands["speckit.team.specify"] == {
        "references/repository-boundary.md"
    }
    assert commands["speckit.team.assess"] == set()
    assert commands["speckit.team.fix"] == set()
    assert commands["speckit.team.review"] == set()
    assert commands["speckit.team.implement"] == {
        "references/implement-pr.md",
        "scripts/check_permission_envelope.py",
        "scripts/work_item_paths.py",
    }
    assert {
        "references/code-graph-contract.md",
        "references/permission-envelope.md",
        "scripts/check_permission_envelope.py",
    } <= commands["speckit.team.plan-and-task"]
