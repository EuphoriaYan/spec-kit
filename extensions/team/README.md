# AI Team Role Extension

The `team` extension provides six role-oriented skills without changing native
Spec Kit commands:

| Skill | Role | Input | Durable output |
|---|---|---|---|
| `speckit.team.specify` | Business / Product | plain-language Feature or new-project demand | published Feature Issue, or Issue text in the current response |
| `speckit.team.plan-and-task` | Architect | primary Issue URL at `status/accept` or `status/working` | Feature spec when applicable, Code Graph impact, Plan, parallel Tasks, self-tests, generated check |
| `speckit.team.assess` | Bug Assessor | Issue URL, defect description, or `bug_slug` | `assessment.md` with `draft`, `approved`, or `needs-info` status |
| `speckit.team.fix` | Bug Fixer | approved assessment and optional tracked Issue | source fix, `fix.md`, `test.md`, optional PR |
| `speckit.team.implement` | Developer | Feature slug, checked Plan-and-Task, and permission envelope | source changes, completed Task status, implementation evidence, optional PR |
| `speckit.team.review` | Reviewer | PR URL or number; optional Feature slug | code findings, optional Feature SDD alignment/report, and merge recommendation |

## Role Boundary

Roles do not share hidden chat context. Specify publishes complete User Stories
to the Issue. The Technical Committee or delegated authority discusses the
demand and applies `status/accept` outside the skill. Plan-and-Task reads the
accepted Issue and current source, while Implement and Review consume the
durable planning and evidence artifacts rather than prior role chat.

An accepted Issue body is primary. Suggestions and rejected alternatives in
comments are not requirements. Before acceptance, maintainers should consolidate
accepted changes into the Issue body; an explicit decision comment may
supplement it.

## Labels And Identity

Use exactly one type and one status label:

```text
type/feature | type/bugfix
status/new-issue | status/accept | status/working | status/close
```

For Plan-and-Task, the Issue URL is the global identity. Coding-repository work
uses the numeric Issue ID as `work_id`; enhancement-repository work uses
`enhancement-<issue-id>` to avoid collisions.

Assess and Fix use a separate safe `bug_slug`. An explicit `bug_slug` wins; an
Issue URL otherwise produces a repository-and-number slug, and free-form input
produces a short kebab-case symptom slug. Do not assume this slug is the numeric
Issue ID.

Feature delivery uses `.specify/feature/<work_id>/`. Bugfix assessment and fix
delivery use `.specify/bugfix/<bug_slug>/`: Assess writes `assessment.md` and
sets `approved` only after explicit user approval; Fix requires that approved
status, then writes `fix.md` and `test.md`. For a tracked Issue, Fix also
requires `status/working` and never changes labels automatically.

## Feature Flow

```text
plain-language demand
-> speckit.team.specify
-> publish Issue and complete governance acceptance
-> speckit.team.plan-and-task
-> create .specify/feature/<work_id>/ artifacts
-> Code Graph, Plan HLD, parallel Tasks, self-tests, generated readiness check
-> speckit.team.implement
-> source changes and verification evidence
-> optional pull request
-> speckit.team.review
-> findings and merge recommendation
```

Specify writes no local checklist, Issue draft, Work Context, or `spec.md`.
Plan-and-Task pauses at its human decision boundary before Task decomposition.
Implement stops when readiness, permissions, or verification fails and creates
a PR only after explicit confirmation. Review never creates, approves, merges,
or resolves conversations on a PR. Review can review any PR; Feature SDD
alignment is assessed only when a Feature root can be resolved.

## Bugfix Flow

```text
observed defect
-> speckit.team.assess
-> assessment with draft, approved, or needs-info status
-> impact, proposed permission boundary, fix strategy, and test strategy
-> human approval
-> optionally create a type/bugfix Issue at status/new-issue
-> when an Issue is used, a maintainer moves claimed work to status/working
-> speckit.team.fix
-> source fix, regression verification, fix.md and test.md
-> optional pull request
-> speckit.team.review
```

Several Bug Issues may map to one change only when they are symptoms of the
same root cause and each has separate reproduction and verification evidence.

## Planning And Delivery Rules

The Plan is Issue-wide HLD. Each Task is a small LLD unit scoped to one module
and designed for parallel assignment. When Tasks cannot run in parallel, the
Plan records the dependency, handoff artifact, serialization reason, and unblock
evidence.

Feature implementation requires `spec.md` (or an authorized override), a
passing `plan-and-task-check.md`, task-ready `plan-and-task.md`, and a permission
envelope. It marks only completed Task Status checkboxes, records commands and
test results in `evidence/implementation-report.md`, and reaches
`phase: verified` without requiring a PR. PR submission details are loaded
progressively only after verification and user confirmation.

Public API, SPI, configuration, protocol, schema, database ownership, or
cross-module semantics still require the appropriate human architecture or
contract authority.

## Installed Skill Layout

Each supported skills-based integration receives self-contained directories.
Every role has `SKILL.md`; references and scripts are installed only when that
role loads or executes them:

```text
speckit-team-<role>/
`-- SKILL.md

speckit-team-plan-and-task/
|-- SKILL.md
|-- references/
`-- scripts/              # deterministic checks and handoff helpers

speckit-team-implement/
|-- SKILL.md
|-- references/           # loaded only after PR confirmation
`-- scripts/              # Permission Envelope validation
```

Each Skill resolves declared resources relative to its own `SKILL.md`.
Specify installs only its conditional repository-boundary reference. Assess,
Fix, and Review install no role references or scripts.
`init_role_context.py` runs during project initialization and is not copied
into individual Skills.

Plan-and-Task must run its installed `scripts/check_plan_and_task.py`. The
script generates `plan-and-task-check.md`; a model may fix source artifacts but
may not hand-write a passing result. Human decisions remain in the Issue and
Plan review record.

## Work Directories

```text
.specify/feature/<work_id>/
|-- spec.md
|-- plan-and-task.md
|-- plan-and-task-check.md
|-- work-context.yml
|-- context-pack.md
|-- permission-envelope.yml
|-- codegraph/
`-- evidence/
    |-- implementation-report.md
    `-- review-report.md          # optional

.specify/bugfix/<bug_slug>/
|-- assessment.md
|-- fix.md
`-- test.md
```

Plan-and-Task may also use `.specify/bugfix/<work_id>/` for an accepted Bugfix
Issue's formal planning package; Bugfix planning does not create `spec.md`.

Commit Feature Specs, Plans, generated checks, and reviewed evidence according
to repository policy. Ignore `spec.override.md`, private customer text,
credentials, and local memory.

## Installation

CodeGraph is a required Team dependency. Install it once, then initialize the
coding repository's local graph before impact-sensitive work:

```bash
npm install -g @colbymchenry/codegraph
codegraph init .
```

The default Team-minimal profile checks that `codegraph` is on PATH, keeps the
Spec Kit engine, and installs the Team role skills:

```bash
specify init . --integration codex
```

For extension development:

```bash
specify extension add extensions/team --dev
```

Use `--skill-profile full` only when native Spec Kit skills are also wanted.
Codex, Claude Code, Cursor Agent, and Trae receive the same role behavior and
their own installed Skill resources. CodeGraph can configure MCP directly for
Codex, Claude Code, and Cursor; every role can use its CLI, including in Trae.

## Chat Entry

Users do not need to name a skill. New Feature and Bugfix work can start
naturally:

```text
Please add CSV export to the current project. Export the same fields shown in
the result list, and help me turn this into a reviewable requirement.

Login returns 500 after session expiry. Assess the defect before changing code.
```

After governance acceptance, continue with the Issue URL. Once planning is
task-ready, delivery can be invoked directly:

```text
/speckit.team.specify Please add CSV export with the same fields as the result list
/speckit.team.plan-and-task https://github.com/org/repo/issues/123
/speckit.team.assess https://github.com/org/repo/issues/123
/speckit.team.assess "Login returns 500 after session expiry" bug_slug=login-session-expiry
/speckit.team.fix bug_slug=login-session-expiry
/speckit.team.implement feature_slug=123
/speckit.team.implement feature_slug=123 only=T001-T010
/speckit.team.implement feature_slug=123 submit_pr=true
/speckit.team.review https://github.com/org/repo/pull/123
```

GitHub Issue/PR operations and Review require authenticated GitHub access;
Review specifically requires `gh`. Without PR access, Implement and Fix can
still finish verification and provide manual submission guidance.
