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
        "speckit.team.implement": "commands/speckit.team.implement.md",
        "speckit.team.review": "commands/speckit.team.review.md",
    }

    raw = yaml.safe_load((EXTENSION_ROOT / "extension.yml").read_text(encoding="utf-8"))
    assert raw["requires"]["tools"] == [{"name": "gh", "required": False}]
    for command_file in commands.values():
        assert (EXTENSION_ROOT / command_file).is_file()


def test_implement_contract_uses_unified_root_and_lazy_pr_prompt():
    command = (EXTENSION_ROOT / "commands" / "speckit.team.implement.md").read_text(
        encoding="utf-8"
    )

    assert ".specify/specs/{feature-slug}" in command
    assert "only=T001-T010" in command
    assert "submit_pr=true" in command
    assert "Readiness blocked. Do not proceed with implementation." in command
    assert ".specify/extensions/team/commands/prompts/implement-pr.md" in command
    assert "phase: verified" in command


def test_pr_details_are_isolated_from_main_implementation_command():
    command = (EXTENSION_ROOT / "commands" / "speckit.team.implement.md").read_text(
        encoding="utf-8"
    )
    prompt = (
        EXTENSION_ROOT / "commands" / "prompts" / "implement-pr.md"
    ).read_text(encoding="utf-8")

    assert "gh pr create" not in command
    assert "gh pr create" in prompt
    assert "permission-envelope.yml" in prompt
    assert "implementation-report.md" in prompt
    assert "phase: pr-open" in prompt


def test_commands_forbid_legacy_feature_artifact_roots():
    for filename in ("speckit.team.implement.md", "speckit.team.review.md"):
        command = _normalized_markdown(EXTENSION_ROOT / "commands" / filename)
        assert "Never read or write" in command
        assert "repository-root `specs/`" in command
        assert "`.specify/ai-team/work/`" in command


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
