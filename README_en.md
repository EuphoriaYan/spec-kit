# AI Team Spec Kit

[中文主文档](README.md)

AI Team Spec Kit is a team-oriented Spec-Driven Development distribution based
on Spec Kit `v0.12.5`. Its default profile installs six focused primary Team
Skills for Codex, Claude Code, Cursor, and Trae, plus optional advanced
extension entries, instead of the full native command set.

The goal is consistent collaboration across people and AI tools: requirements,
architecture boundaries, implementation scope, and verification evidence are
handed off through Issues and artifacts rather than hidden chat context.

## Six Team Skills

| Skill | Use | Output |
|---|---|---|
| `speckit.team.specify` | clarify a new Feature or project | complete User Stories and a publishable Feature Issue |
| `speckit.team.plan-and-task` | plan an accepted Feature Issue | CodeGraph-grounded HLD, module Tasks, self-tests, and deterministic check |
| `speckit.team.assess` | analyze a defect or Review finding | root-cause hypothesis, impact, fix boundary, and test strategy |
| `speckit.team.fix` | execute a ready or approved assessment | minimal fix, regression evidence, and automatic return to Review |
| `speckit.team.implement` | implement checked Feature Tasks | code, self-test evidence, and PR-ready result after the quality loop |
| `speckit.team.review` | review a PR or local diff | findings and `GO`, `GO-WITH-RISK`, or `NO-GO` recommendation |

## Advanced Extension Entries

Advanced entries do not participate in automatic Feature or Bugfix routing.
Invoke them only for an explicit maintenance request.

| Entry | Use | Output |
|---|---|---|
| `speckit.team.memory-consolidate` | preserve lessons or reuse an approved decision after delivery | advisory Memory or human-approved project Knowledge |

```text
Feature: plain demand -> Specify -> Issue acceptance -> Plan-and-Task
         -> Implement -> Review/Assess/Fix -> PR -> human merge decision

Bugfix: symptom -> Assess -> Fix -> Review/Assess/Fix
        -> optional PR -> human merge decision
```

## Install

Install Python 3.11+, Git, uv, and CodeGraph CLI 1.x, then run:

```bash
npm install -g @colbymchenry/codegraph@^1
uv tool install specify-cli --force \
  --from git+https://github.com/EuphoriaYan/spec-kit.git@v0.12.5+teamwork.2
specify init . --integration codex
```

Supported integrations are `codex`, `claude`, `cursor-agent`, and `trae`.
Use `--skill-profile full` only when the native Spec Kit skill set is also
required.

The current six-skill distribution is pinned to `v0.12.5+teamwork.2`. Do not
replace the shared Team version with the moving `main` branch.

Users can remain in chat and describe work naturally. See the
[installation guide](docs/installation_en.md),
[quick start](docs/quickstart_en.md),
[upgrade guide](docs/upgrade_en.md), and
[Team extension guide](extensions/team/README_en.md).

AI runtime contracts under `extensions/team/commands/`,
`extensions/team/references/`, and resources installed by `extension.yml`
remain in English with stable paths.
