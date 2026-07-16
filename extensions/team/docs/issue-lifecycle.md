# Issue Lifecycle

Repository Issues are the human-visible demand ledger. Feature directories are
created when accepted work enters Plan-and-Task. Bugfix directories are created
by Assess and continue through Fix and Review without planning artifacts.

## Labels

Every Issue has exactly one type label:

- `type/feature` for Features and new projects;
- `type/bugfix` for defects.

Every Issue has exactly one status label:

| Status | Meaning | Allowed next status |
|---|---|---|
| `status/new-issue` | published for discussion; not accepted for planning | `status/accept`, `status/close` |
| `status/accept` | accepted by the Technical Committee or delegated authority | `status/working`, `status/close` |
| `status/working` | active planning or implementation | `status/close` |
| `status/close` | completed, declined, cancelled, or superseded; explain why in the Issue | terminal |

Publishing an Issue never grants `status/accept`. The governance body changes
that label outside the role skill.

## Repository Route

| Repository | Allowed work |
|---|---|
| coding repository | public or project-controlled Features and all Bugfixes |
| enhancement repository | confidential enterprise Features only |

The enhancement repository never receives `type/bugfix`.

## Feature Authority

Specify publishes complete User Stories directly in the Issue and creates no
local draft or `spec.md`. Discussion may refine the demand. Before applying
`status/accept`, maintainers should consolidate accepted changes into the Issue
body. A clearly identified decision comment may supplement the body.

Plan-and-Task reads the body and discussion, excludes rejected or unresolved
ideas, and creates the committed Feature `spec.md` snapshot. It records the
Issue update time and body hash so later changes can invalidate stale planning.

## Bugfix Authority

Bugfix does not use Specify or Plan-and-Task. Assess captures the observed
symptom, reproduction evidence, impact, likely code paths, permission boundary,
fix strategy, and test strategy in `assessment.md`. Fix consumes the approved
assessment and records implementation and verification in `fix.md` and
`test.md`. Review checks the resulting PR against those artifacts and any
linked Issue.

A Bugfix may enter Assess from a raw symptom and may proceed to Fix after human
approval of the assessment. A coding-repository Issue is optional. When one is
linked, Fix requires verified `type/bugfix` and `status/working` labels. Assess,
Fix, and Review do not grant acceptance or change labels on behalf of
maintainers.

## Work Identity

For Feature work, the absolute Issue URL is the global identity and its number
forms `work_id`; prefix enhancement work as `enhancement-<issue-id>`. For
Bugfix, `bug_slug` is the stable local artifact key. A supplied coding Issue
URL remains a repository-tracking reference and is recorded by Fix.

A PR may resolve several Bug Issues only when they are different symptoms of
the same root cause. Keep one primary Issue and map every additional Issue to
its own reproduction and verification evidence.
