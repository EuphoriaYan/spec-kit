# AI Team Lifecycle Quick Start

[中文主文档](quickstart.md)

After installation, daily work starts from chat. Team Skills are
routed by delivery phase. Users may name a Skill, but they can also describe
the current situation naturally.

## Skill Contracts

| Skill | Minimum input | Output |
|---|---|---|
| Requirement | project-level or existing-project requirement | one reviewed Requirement Issue |
| Feature Split | accepted Requirement Issue | reviewed architecture context, Feature Catalog, and repository Feature Records |
| Specify | accepted `feature_id` | clarified User Stories and local Feature Spec |
| Plan-and-Task | accepted `feature_id` | L2 design, module Tasks, minimum self-tests, deterministic check |
| Assess | symptom, Issue, Review finding, or `bug_slug` | assessment, impact, fix boundary, and test strategy |
| Fix | ready or approved assessment | minimal fix, regression evidence, progress update, and Review handoff |
| Implement | `feature_id` | code, tests, architecture synchronization, evidence, and automatic quality loop |
| Review | PR URL or local diff | findings, correction routing, and merge recommendation |

## Advanced Extension Entry

`speckit.team.memory-consolidate` is outside the Feature/Bugfix delivery flow.
Invoke it explicitly after delivery to preserve a lesson, record a decision, or
promote approved guidance into project Knowledge.

## Feature Journey

```text
project-level or existing-project requirement
-> Requirement clarifies and publishes one Requirement Issue
-> governance accepts the requirement
-> Feature Split loads or creates the required architecture context
-> ask once where committed Feature Records belong, then lock the location
-> review the Feature Catalog and accept each Feature
-> Specify writes one accepted Feature's User Stories
-> Plan-and-Task reads the Feature Record, source, and CodeGraph
-> human reviews the HLD, then Tasks are decomposed
-> Implement verifies and enters Review automatically
-> repairable blocker/major findings use Assess -> Fix -> Re-review
-> submit PR -> human merge decision
```

Start with:

```text
Add CSV export with the same fields as the result list. Help me clarify the
requirement before changing code.
```

## Bugfix Journey

```text
symptom or Review finding
-> Assess preserves intent and finds source-grounded impact
-> clear single-repository, single-module work becomes ready
-> Fix applies the smallest change and verifies regression coverage
-> Review -> optional automatic Assess/Fix rounds
-> optional PR -> human merge decision
```

A standalone Bugfix does not require an Issue. When an Issue is supplied, Fix
checks `type/bugfix` and `status/working`.

## Resume

Resume with a Requirement Issue URL, `feature_id`, legacy `work_id`,
`bug_slug`, or PR URL. Repository Feature Records remain committed at the
user-confirmed location. Local work packages under `.specify/<feature_id>/`,
legacy `.specify/feature/`, and `.specify/bugfix/` are ignored by Git;
another machine reconstructs context from the Issue/PR handoff, current source,
tests, and approved artifacts rather than remembered chat.

Only requirement acceptance; HLD, cross-module and public-interface design;
dependency, security, license and incompatibility decisions; Plan expansion;
and final merge remain permanent human decisions.
