# Six-Skill Quick Start

[中文主文档](quickstart.md)

After installation, daily work starts from chat. The six primary Skills are
routed by delivery phase. Users may name a Skill, but they can also describe
the current situation naturally.

## Skill Contracts

| Skill | Minimum input | Output |
|---|---|---|
| Specify | plain Feature or new-project demand | clarified User Stories and a published or paste-ready Feature Issue |
| Plan-and-Task | accepted Feature Issue URL | Issue-level HLD, module Tasks, minimum self-tests, deterministic check |
| Assess | symptom, Issue, Review finding, or `bug_slug` | assessment, impact, fix boundary, and test strategy |
| Fix | ready or approved assessment | minimal fix, regression evidence, progress update, and Review handoff |
| Implement | `work_id` or Feature Issue URL | implementation, evidence, and automatic quality loop |
| Review | PR URL or local diff | findings, correction routing, and merge recommendation |

## Advanced Extension Entry

`speckit.team.memory-consolidate` is outside the Feature/Bugfix delivery flow.
Invoke it explicitly after delivery to preserve a lesson, record a decision, or
promote approved guidance into project Knowledge.

## Feature Journey

```text
plain-language demand
-> Specify clarifies User Stories
-> publish type/feature + status/new-issue
-> Technical Committee accepts the demand
-> Plan-and-Task reads the Issue, source, and CodeGraph
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

Resume with a Feature Issue URL, `work_id`, `bug_slug`, or PR URL. Local work
packages under `.specify/feature/` and `.specify/bugfix/` are ignored by Git;
another machine reconstructs context from the Issue/PR handoff, current source,
tests, and approved artifacts rather than remembered chat.

Only requirement acceptance; HLD, cross-module and public-interface design;
dependency, security, license and incompatibility decisions; Plan expansion;
and final merge remain permanent human decisions.
