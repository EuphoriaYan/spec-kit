import re
from pathlib import Path

import yaml

from specify_cli.extensions import ExtensionManifest


REPO_ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ROOT = REPO_ROOT / "extensions" / "team"


def _normalized_markdown(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_team_manifest_is_valid_and_declares_execution_commands():
    manifest = ExtensionManifest(EXTENSION_ROOT / "extension.yml")

    assert manifest.id == "team"
    assert manifest.requires_speckit_version == ">=0.12.4"
    commands = {command["name"]: command["file"] for command in manifest.commands}
    assert commands == {
        "speckit.team.specify": "commands/speckit.team.specify.md",
        "speckit.team.plan-and-task": "commands/speckit.team.plan-and-task.md",
        "speckit.team.assess": "commands/speckit.team.assess.md",
        "speckit.team.fix": "commands/speckit.team.fix.md",
        "speckit.team.implement": "commands/speckit.team.implement.md",
        "speckit.team.review": "commands/speckit.team.review.md",
    }

    raw = yaml.safe_load((EXTENSION_ROOT / "extension.yml").read_text(encoding="utf-8"))
    assert raw["requires"]["tools"] == [{"name": "gh", "required": False}]
    for command_file in commands.values():
        assert (EXTENSION_ROOT / command_file).is_file()


def test_assess_contract_uses_bugfix_root_and_merges_analysis():
    command = _normalized_markdown(
        EXTENSION_ROOT / "commands" / "speckit.team.assess.md"
    )

    assert ".specify/bugfix/{bug-slug}" in command
    assert "assessment.md" in command
    assert "Code Graph / Relevant Code Paths" in command
    assert "Impact Analysis" in command
    assert "Permission Boundary" in command
    assert "Review and Revision Loop" in command
    assert "Status**: draft | approved | needs-info" in command
    assert "Do not include a separate `## Assessment Review` section" in command
    assert "Issue Creation" in command
    assert "status/new-issue" in command
    assert "type/bugfix" in command
    assert "workflow_run_id" not in command


def test_fix_contract_writes_reports_and_asks_before_pr():
    command = _normalized_markdown(
        EXTENSION_ROOT / "commands" / "speckit.team.fix.md"
    )

    assert ".specify/bugfix/{bug-slug}" in command
    assert "assessment.md" in command
    assert "fix.md" in command
    assert "test.md" in command
    assert "Status**: approved" in command
    assert "ask the user whether to create a pull request" in command
    assert "gh pr create" in command
    assert "Do not create a pull request without asking the user first" in command
    assert "Issue State Gate" in command
    assert "status/working" in command
    assert "status/new-issue" in command
    assert "status/accept" in command
    assert "Do not change issue labels automatically" in command


def test_bugfix_commands_use_canonical_bugfix_root():
    for filename in ("speckit.team.assess.md", "speckit.team.fix.md"):
        command = _normalized_markdown(EXTENSION_ROOT / "commands" / filename)
        assert ".specify/bugfix/" in command
        assert ".specify/bugs/" not in command


def test_implement_contract_uses_unified_root_and_lazy_pr_prompt():
    command = (EXTENSION_ROOT / "commands" / "speckit.team.implement.md").read_text(
        encoding="utf-8"
    )

    assert ".specify/feature/{feature-slug}" in command
    assert "only=T001-T010" in command
    assert "submit_pr=true" in command
    assert "Readiness blocked. Do not proceed with implementation." in command
    assert "references/implement-pr.md" in command
    assert "phase: verified" in command
    assert "`plan-and-task.md`" in command
    assert "`plan-and-task-check.md`" in command
    assert "`plan.md`" not in command
    assert "`tasks.md`" not in command


def test_pr_details_are_isolated_from_main_implementation_command():
    command = (EXTENSION_ROOT / "commands" / "speckit.team.implement.md").read_text(
        encoding="utf-8"
    )
    prompt = (
        EXTENSION_ROOT / "references" / "internal" / "implement-pr.md"
    ).read_text(encoding="utf-8")

    assert "gh pr create" not in command
    assert "gh pr create" in prompt
    assert "permission-envelope.yml" in prompt
    assert "implementation-report.md" in prompt
    assert "phase: pr-open" in prompt


def test_commands_do_not_describe_unrelated_spec_kit_storage():
    forbidden = (
        "repository-root `specs/`",
        ".specify/ai-team",
        ".specify/team",
        ".specify/extensions/team",
    )
    for path in (EXTENSION_ROOT / "commands").glob("speckit.team.*.md"):
        command = path.read_text(encoding="utf-8")
        assert all(value not in command for value in forbidden), path.name


def test_review_contract_treats_pr_as_primary_input():
    command = _normalized_markdown(
        EXTENSION_ROOT / "commands" / "speckit.team.review.md"
    )

    assert "Require a PR URL or `pr=<number>`" in command
    assert "gh pr view" in command
    assert "gh pr diff" in command
    assert "## Review Findings" in command
    assert "## Merge Recommendation" in command
    assert "evidence/review-report.md" in command
    assert "`plan-and-task.md`" in command
    assert "`plan-and-task-check.md`" in command
    assert "`plan.md`" not in command
    assert "`tasks.md`" not in command


def test_internal_references_are_installed_or_explicitly_reserved():
    manifest = yaml.safe_load(
        (EXTENSION_ROOT / "extension.yml").read_text(encoding="utf-8")
    )
    commands = {item["name"]: item for item in manifest["provides"]["commands"]}

    active: dict[str, tuple[str, str]] = {}
    for command_name, command in commands.items():
        for resource in command.get("resources", []):
            prefix = "references/internal/"
            if resource["source"].startswith(prefix):
                active[Path(resource["source"]).name] = (
                    command_name,
                    resource["target"],
                )

    lifecycle = (
        EXTENSION_ROOT / "references" / "internal" / "README.md"
    ).read_text(encoding="utf-8")
    active_section, reserved_section = lifecycle.split(
        "## Reserved Capability Sources", maxsplit=1
    )
    reserved_section = reserved_section.split("## Migrated Sources", maxsplit=1)[0]
    listed_active = set(re.findall(r"\| `([^`]+\.md)` \|", active_section))
    listed_reserved = set(re.findall(r"\| `([^`]+\.md)` \|", reserved_section))

    files = {
        path.name
        for path in (EXTENSION_ROOT / "references" / "internal").glob("*.md")
        if path.name != "README.md"
    }
    assert listed_active == set(active)
    assert files == listed_active | listed_reserved
    assert listed_active.isdisjoint(listed_reserved)
    assert "init-context.md" not in files

    for source_name, (command_name, target) in active.items():
        command_file = EXTENSION_ROOT / commands[command_name]["file"]
        command_text = command_file.read_text(encoding="utf-8")
        assert target in command_text, (
            f"{source_name} is installed as {target} but {command_name} "
            "does not explicitly load it"
        )
