# Issue Lifecycle

Repository Issues are the human-visible demand ledger. Team work directories
are technical snapshots created only when accepted or active work enters
planning.

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

## Work Identity

The absolute Issue URL is the global identity. Use the numeric Issue ID as
`work_id` for coding-repository work. Prefix enhancement-repository work as
`enhancement-<issue-id>` so equal numbers from different repositories do not
collide.

A PR may resolve several Bug Issues only when they are different symptoms of
the same root cause. Keep one primary Issue and map every additional Issue to
its own reproduction and verification evidence.
