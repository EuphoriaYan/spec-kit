# Team Extension Maintainer Guide

[中文主文档](README.md)

The `team` extension provides six primary delivery Skills without modifying
native Spec Kit commands. End users should start with the
[Six-Skill Quick Start](../../docs/quickstart_en.md).

| Skill | Role | Durable result |
|---|---|---|
| `speckit.team.specify` | Business / Product | published or paste-ready Feature Issue |
| `speckit.team.plan-and-task` | Architect | local Spec, Issue-level HLD, module Tasks, self-tests, and check |
| `speckit.team.assess` | Bug Assessor | assessment and risk routing |
| `speckit.team.fix` | Bug Fixer | minimal fix, test evidence, and Review handoff |
| `speckit.team.implement` | Developer | implementation evidence and automatic quality loop |
| `speckit.team.review` | Reviewer | findings and merge recommendation |

## Advanced Extension Entries

Advanced entries are installed but are not delivery roles and do not
participate in automatic Feature or Bugfix routing.

| Entry | User | Durable result |
|---|---|---|
| `speckit.team.memory-consolidate` | Contributor / Maintainer | advisory Memory or human-approved project Knowledge |

Invoke this entry only for an explicit post-delivery maintenance request.

The default `team` profile installs self-contained Skill directories. Each
Skill receives only its declared references and deterministic scripts. The
extension source is not copied into the product repository. Stable Team
configuration and bootstrap live under `.specify/team/`; managed agent rules
are merged without replacing project-owned instructions.

Feature work packages under `.specify/feature/<work_id>/` and Bugfix packages
under `.specify/bugfix/<bug_slug>/` are local and Git-ignored. Cross-person
facts move through Issues, PRs, source, tests, and explicitly promoted HLD or
project knowledge.

Plan-and-Task requires CodeGraph and a generated deterministic check. A
Permission Envelope records risk boundaries but is not a runtime sandbox.
Implement enters Review automatically, and repairable blocker/major findings
may use up to three Assess/Fix/Re-review rounds. Review never approves or
merges a PR.

`extension.yml` is the installation manifest. Every command dependency must be
declared as that command's resource and resolve relative to its installed
Skill directory.

```bash
specify extension add extensions/team --dev
PYTHONPATH=src python -m pytest -q tests/extensions
PYTHONPATH=src python -m pytest -q tests/unit/test_bundled_bundle.py
```

Human-facing docs use Chinese primary files and `_en` English backups. Skills,
references, bootstrap, templates, and script contracts remain English.
