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
        "speckit.team.memory-consolidate": "commands/speckit.team.memory-consolidate.md",
    }

    raw = yaml.safe_load((EXTENSION_ROOT / "extension.yml").read_text(encoding="utf-8"))
    assert raw["requires"]["tools"] == [
        {"name": "gh", "required": False},
        {
            "name": "codegraph",
            "version": ">=1.0.0,<2.0.0",
            "required": False,
        },
    ]
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
    assert "Risk Routing" in command
    assert "Status**: ready | approval-required | approved | needs-info" in command
    assert "`draft` is not a valid assessment status" in command
    assert "Only when Assess is invoked for a Feature correction" in command
    assert "Omit both fields for a standalone Bugfix" in command
    assert "or not-applicable" not in command
    assert "repository-local analysis does not need human approval" in command
    assert "Issue Creation" in command
    assert "status/new-issue" in command
    assert "type/bugfix" in command
    assert "Primary Issue" not in command
    assert "Issue Status" not in command
    assert "references/context.md" in command
    assert "work-context.yml" in command
    assert "context-pack.md" in command
    assert "workflow_run_id" not in command


def test_fix_contract_writes_reports_and_asks_before_pr():
    command = _normalized_markdown(
        EXTENSION_ROOT / "commands" / "speckit.team.fix.md"
    )

    assert ".specify/bugfix/{bug-slug}" in command
    assert "assessment.md" in command
    assert "fix.md" in command
    assert "test.md" in command
    assert "Status**: ready" in command
    assert "Status**: approved" in command
    assert "ask the user whether to create a pull request" in command
    assert "gh pr create" in command
    assert "Do not create a pull request without asking the user first" in command
    assert "Conditional Issue State Gate" in command
    assert "status/working" in command
    assert "status/new-issue" in command
    assert "status/accept" in command
    assert "Do not change issue labels automatically" in command
    assert "Apply this section only for `FLOW_KIND=standalone-bugfix`" in command
    assert "Never apply the `type/bugfix` gate to `Parent Feature`" in command
    assert "Proceed only when the Issue has label `status/working`" in command
    assert "Primary Issue**: <supplied coding Issue URL or not-provided>" in command
    assert "references/context.md" in command
    assert "This section creates a PR only for a standalone Bugfix" in command
    assert "never create a separate Bugfix PR" in command
    assert "Use the exact labels `Bug Slug:` and `Bug Root:`" in command
    assert "`assessment.md`, including its status" in command
    assert "`Parent Work ID:`" in command
    assert "omit `Bug Root:`" in command
    assert "stop if the current branch is the default branch" in command
    assert "Exclude local prompts, scratch files, private demand" in command
    assert "symptoms of the same root cause" in command


def test_bugfix_issue_is_created_by_assess_and_gated_only_when_fix_receives_it():
    commands = EXTENSION_ROOT / "commands"
    assess = _normalized_markdown(commands / "speckit.team.assess.md")
    fix = _normalized_markdown(commands / "speckit.team.fix.md")
    review = _normalized_markdown(commands / "speckit.team.review.md")

    assert "ask whether the user wants to create or update a tracking Issue" in assess
    assert "Primary Issue" not in assess
    assert "Without Issue input, skip this section" in fix
    assert "an absent Issue is not a Bugfix blocker" in review
    assert "Require the Issue to belong to the coding repository" in fix


def test_bugfix_commands_use_canonical_bugfix_root():
    for filename in ("speckit.team.assess.md", "speckit.team.fix.md"):
        command = _normalized_markdown(EXTENSION_ROOT / "commands" / filename)
        assert ".specify/bugfix/" in command
        assert ".specify/bugs/" not in command


def test_bugfix_flow_has_its_own_resume_context():
    layout = _normalized_markdown(EXTENSION_ROOT / "docs" / "work-item-layout.md")
    lifecycle = _normalized_markdown(EXTENSION_ROOT / "docs" / "issue-lifecycle.md")

    context = _normalized_markdown(
        EXTENSION_ROOT / "docs" / "work-context-package.md"
    )

    assert "work-context.yml" in layout
    assert "context-pack.md" in layout
    assert ".specify/bugfix/<bug_slug>/" in context
    assert "last_completed_skill: speckit.team.assess" in context
    assert "next_skill: speckit.team.fix" in context
    assert "Bugfix does not use Specify or Plan-and-Task" in lifecycle
    assert "type/bugfix" in lifecycle
    assert "status/new-issue" in lifecycle


def test_feature_and_bugfix_delivery_chains_are_distinct_with_review_bridge():
    commands = EXTENSION_ROOT / "commands"
    specify = _normalized_markdown(commands / "speckit.team.specify.md")
    plan = _normalized_markdown(commands / "speckit.team.plan-and-task.md")
    implement = _normalized_markdown(commands / "speckit.team.implement.md")
    assess = _normalized_markdown(commands / "speckit.team.assess.md")
    fix = _normalized_markdown(commands / "speckit.team.fix.md")
    review = _normalized_markdown(commands / "speckit.team.review.md")

    assert ".specify/bugfix/" not in plan
    assert "assessment.md" not in plan
    assert ".specify/bugfix/" not in implement
    assert "assessment.md" not in implement
    assert "parent Feature root" in assess
    assert "User Story Verification clauses" in assess
    assert ".specify/feature/" not in fix
    assert "plan-and-task.md" not in fix
    assert "belongs to the Bugfix intake skill" in specify
    assert "Automated Quality Loop" in implement
    assert "Assess -> Fix -> Re-review" in review

    assert "never both" in review
    assert ".specify/feature/{work_id}" in review
    assert ".specify/bugfix/{bug-slug}" in review
    assert "For Feature" in review
    assert "For Bugfix" in review


def test_implement_contract_uses_unified_root_and_automatic_pr_transport():
    command = (EXTENSION_ROOT / "commands" / "speckit.team.implement.md").read_text(
        encoding="utf-8"
    )

    assert ".specify/feature/{work_id}" in command
    assert "`work_id=<id>`" in command
    assert "accepted Plan/Task handoff" in command
    assert "feature_slug" not in command
    assert "only=T001-T010" in command
    assert "Do not ask whether to submit a PR" in command
    assert "create or update the PR automatically" in command
    assert "Final merge remains a human decision" in command
    assert "submit_pr=true" not in command
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


def test_review_contract_supports_pr_and_local_quality_loop():
    command = _normalized_markdown(
        EXTENSION_ROOT / "commands" / "speckit.team.review.md"
    )

    assert "Accept a PR URL, `pr=<number>`, or `local=true`" in command
    assert "gh pr view" in command
    assert "gh pr diff" in command
    assert "## Review Findings" in command
    assert "## Final Conclusion" in command
    assert "GO | GO-WITH-RISK | NO-GO" in command
    assert "## Required Next Action" in command
    assert "## Durable Follow-up" in command
    assert "test, mechanical gate, role Skill correction" in command
    assert "evidence/review-report.md" in command
    assert "`bug_slug=<slug>`" in command
    assert "require `assessment.md`, `fix.md`, and `test.md`" in command
    assert "same root cause" in command
    assert "`GO`" in command
    assert "`GO-WITH-RISK`" in command
    assert "`NO-GO`" in command
    assert "Do not merge" in command
    assert "Paste Into PR Discussion" in command
    assert "`plan-and-task.md`" in command
    assert "`plan-and-task-check.md`" in command
    assert "`plan.md`" not in command
    assert "`tasks.md`" not in command
    assert not (
        EXTENSION_ROOT / "references" / "internal" / "review.md"
    ).exists()


def test_every_internal_reference_is_installed_and_read_by_its_skill():
    manifest = yaml.safe_load(
        (EXTENSION_ROOT / "extension.yml").read_text(encoding="utf-8")
    )
    commands = {item["name"]: item for item in manifest["provides"]["commands"]}

    active: dict[str, list[tuple[str, str]]] = {}
    for command_name, command in commands.items():
        for resource in command.get("resources", []):
            prefix = "references/internal/"
            if resource["source"].startswith(prefix):
                active.setdefault(Path(resource["source"]).name, []).append(
                    (command_name, resource["target"])
                )

    lifecycle = (
        EXTENSION_ROOT / "references" / "internal" / "README.md"
    ).read_text(encoding="utf-8")
    listed_active = set(re.findall(r"\| `([^`]+\.md)` \|", lifecycle))

    files = {
        path.name
        for path in (EXTENSION_ROOT / "references" / "internal").glob("*.md")
        if path.name != "README.md"
    }
    assert listed_active == set(active)
    assert files == listed_active
    assert files == set(active)
    assert "init-context.md" not in files
    assert "Reserved Capability Sources" not in lifecycle

    for source_name, bindings in active.items():
        for command_name, target in bindings:
            command_file = EXTENSION_ROOT / commands[command_name]["file"]
            command_text = command_file.read_text(encoding="utf-8")
            assert target in command_text, (
                f"{source_name} is installed as {target} but {command_name} "
                "does not explicitly load it"
            )
