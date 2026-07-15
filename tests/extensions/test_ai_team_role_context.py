from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

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


def test_exactly_two_role_commands_are_registered() -> None:
    manifest = yaml.safe_load((AI_TEAM / "extension.yml").read_text(encoding="utf-8"))
    provided = {item["name"]: item for item in manifest["provides"]["commands"]}
    assert set(provided) == {
        "speckit.team.specify",
        "speckit.team.plan-and-task",
    }
    assert {path.stem for path in (AI_TEAM / "commands").glob("*.md")} == set(provided)


def test_context_initializer_merges_supported_agent_files_idempotently(tmp_path: Path) -> None:
    _install_bootstrap(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Existing project rules\n", encoding="utf-8")
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


def test_context_initializer_always_writes_agents_without_detected_tool(tmp_path: Path) -> None:
    _install_bootstrap(tmp_path)
    module = _load_init_module()

    assert module.initialize(tmp_path) == ["AGENTS.md"]
    assert module.BOOTSTRAP in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")


def test_ai_team_bundle_initializes_rules_before_first_skill(
    tmp_path: Path, monkeypatch
) -> None:
    from specify_cli import _assets
    from specify_cli.commands.bundle import _initialize_bundled_ai_team_context

    _install_bootstrap(tmp_path)
    specify = tmp_path / ".specify"
    (specify / "integration.json").write_text(
        json.dumps({"installed_integrations": ["codex", "claude"]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(_assets, "_locate_bundled_extension", lambda _id: AI_TEAM)
    manifest = SimpleNamespace(bundle=SimpleNamespace(id="ai-team"))
    context_module = _load_init_module()

    targets = _initialize_bundled_ai_team_context(tmp_path, manifest)

    assert targets == ["AGENTS.md", "CLAUDE.md"]
    assert context_module.BOOTSTRAP in (tmp_path / "AGENTS.md").read_text(
        encoding="utf-8"
    )
    assert "@AGENTS.md" in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")


def test_non_ai_team_bundle_does_not_write_agent_rules(tmp_path: Path) -> None:
    from specify_cli.commands.bundle import _initialize_bundled_ai_team_context

    manifest = SimpleNamespace(bundle=SimpleNamespace(id="other"))
    assert _initialize_bundled_ai_team_context(tmp_path, manifest) == []
    assert not (tmp_path / "AGENTS.md").exists()


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


def test_specify_role_contract_keeps_issue_and_user_story_model() -> None:
    text = (AI_TEAM / "commands/speckit.team.specify.md").read_text(
        encoding="utf-8"
    )

    assert "Produce the primary collaboration Issue before" in text
    assert "prioritized, independently testable User" in text
    assert "type/feature" in text
    assert "exactly one lifecycle state label" in text
    assert "speckit.taskstoissues" in text
    assert "Never wait for `plan-and-task.md` to create the primary Issue" in text
    assert ".specify/<category>/<work_id>/spec.md" in text


def test_publication_approval_is_not_feature_acceptance() -> None:
    specify = (AI_TEAM / "commands/speckit.team.specify.md").read_text(
        encoding="utf-8"
    )
    assert "`approve publication`, `revise`, or `reject`" in specify
    assert "Publication approval must\n   not add `state/accepted`" in specify
    assert "decision is outside this skill" in specify

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
    assert "test/evidence ID" in text
    assert "plan-and-task-check.md" in text
    assert ".specify/<feature|bugfix>/<work_id>/plan-and-task.md" in text
    assert "Produce the technical Plan and executable Tasks without" in text


def test_team_work_item_layout_and_templates_are_unified() -> None:
    layout = (AI_TEAM / "docs/work-item-layout.md").read_text(encoding="utf-8")
    assert ".specify/" in layout
    assert "feature/" in layout
    assert "bugfix/" in layout
    assert "<work_id>/" in layout

    expected = {
        "spec-template.md",
        "plan-and-task-template.md",
        "plan-and-task-check-template.md",
        "work-context-template.yml",
    }
    assert {path.name for path in (AI_TEAM / "templates").iterdir() if path.is_file()} == expected
    assert "plan-and-task.md" in layout
    assert "plan-and-task-check.md" in layout


def test_role_commands_require_repeatable_progressive_bootstrap() -> None:
    bootstrap = (AI_TEAM / "docs/context-bootstrap.md").read_text(encoding="utf-8")
    assert "after every resume or\ncontext compression" in bootstrap
    assert "Level 0: Always Load" in bootstrap
    assert "Level 1: Load Only For The Active Role" in bootstrap
    for role in ("Business / Product", "Architect / Module Owner"):
        assert role in bootstrap
    for command in (AI_TEAM / "commands").glob("*.md"):
        text = command.read_text(encoding="utf-8")
        assert "scripts/init_role_context.py" in text
        assert "context-bootstrap.md" in text
