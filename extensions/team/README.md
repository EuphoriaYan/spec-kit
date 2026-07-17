# AI Team Role Extension

The `team` extension provides six role-oriented delivery skills and one
support skill without changing native Spec Kit commands:

| Skill | Role | Input | Durable output |
|---|---|---|---|
| `speckit.team.specify` | Business / Product | plain-language Feature or new-project demand | published Feature Issue, or Issue text in the current response |
| `speckit.team.plan-and-task` | Architect | accepted/working Feature Issue plus source | local Feature work package plus an Issue-ready Plan/Task handoff |
| `speckit.team.assess` | Bug Assessor | Issue URL, defect description, review finding, or `bug_slug` | local `assessment.md` with `ready`, `approval-required`, or `needs-info` status |
| `speckit.team.fix` | Bug Fixer | ready or risk-approved assessment and optional tracked Issue | source fix, local evidence, PR progress update, automatic re-review |
| `speckit.team.implement` | Developer | Feature `work_id`, checked Plan-and-Task, and permission envelope | source changes, implementation evidence, automatic quality loop, and submitted result |
| `speckit.team.review` | Reviewer | PR or local diff; optional Feature `work_id` or Bugfix `bug_slug` | findings, automatic correction routing, and merge recommendation |
| `speckit.team.memory-consolidate` | Contributor / Maintainer | completed work, evidence, or a reviewed decision | advisory Memory or human-approved task-scoped project Knowledge |

## Knowledge And Memory

Use `speckit.team.memory-consolidate` after completed work or when a durable
human decision should be reused. Local and department Memory remains advisory
and Git-ignored. Enterprise Memory is reviewed historical guidance. A coding
requirement becomes binding only through explicit promotion to
`docs/ai-team/knowledge/rules/`, with owner, approval, evidence, and scope.

Plan-and-Task, Assess, Fix, Implement, and Review retrieve only the matching
role, work-type, and module slice. Binding Knowledge constrains the active
role; Memory may suggest reuse or recurrent risks but cannot override source,
tests, the current Issue or Plan, or human decisions.

## Role Boundary

Roles do not share hidden chat context. Specify publishes complete User Stories
to the Issue. The Technical Committee or delegated authority discusses the
demand and applies `status/accept` outside the skill. Plan-and-Task reads the
accepted Issue and current source, while Implement and Review consume the
local planning/evidence artifacts and shared Issue/PR handoffs rather than prior role chat.

Bugfix uses the independent Assess -> Fix -> Review flow.

Plan-and-Task and Assess use the required local CodeGraph CLI for architecture
and impact evidence. Initialize an existing repository once with
`codegraph init`; the active Skill asks before creating a missing index, then
checks and synchronizes it before analysis. Source remains the implementation
truth, and `.codegraph/` remains local derived state.

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
sets `ready` automatically for clear same-repository, single-module work;
risky work requires a named human decision. Fix accepts `ready` or
risk-approved status, then writes `fix.md` and `test.md`. A coding Issue is optional; when one
is linked, Fix verifies `type/bugfix` and `status/working` without changing
labels automatically.

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
Plan-and-Task pauses at its HLD decision boundary before Task decomposition.
Implement stops when readiness, risk-triggered permissions, or verification
fails, then automatically enters Review. After the quality loop passes, it
submits the PR through available host automation or prints a paste-ready
fallback. Review never approves or merges a PR. Review can review any PR; Feature SDD
or Bugfix lifecycle alignment is assessed only when the corresponding work root
can be resolved.

## Bugfix Flow

```text
observed defect
-> speckit.team.assess
-> assessment with ready, approval-required, approved, or needs-info status
-> impact, proposed permission boundary, fix strategy, and test strategy
-> human approval only for a permanent gate
-> optionally create or verify a coding Issue with type/bugfix
-> when linked, a maintainer moves accepted and claimed work to status/working
-> speckit.team.fix
-> source fix, regression verification, fix.md and test.md
-> automatic speckit.team.review of assessment, fix, tests, diff, and any linked Issue
-> optional pull request after the quality loop
```

Several Bug Issues may map to one change only when they are symptoms of the
same root cause and each has separate reproduction and verification evidence.

## Planning And Delivery Rules

The Plan is Issue-wide HLD. Each Task is a small LLD unit scoped to one module
and designed for parallel assignment. When Tasks cannot run in parallel, the
Plan records the dependency, handoff artifact, serialization reason, and unblock
evidence.

Feature implementation requires a local `spec.md` (or an authorized override), a
passing `plan-and-task-check.md`, task-ready `plan-and-task.md`, and a permission
envelope. One envelope covers the selected Task batch; same-repository,
single-module work without a permanent gate is mechanically `ready`. It marks only completed Task Status checkboxes, records commands and
test results in `evidence/implementation-report.md`, and reaches
`phase: verified` before submission. After the automatic quality loop returns
`GO` or `GO-WITH-RISK`, PR submission runs through host automation or produces
a paste-ready fallback without another design approval.

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
|-- references/           # PR instructions loaded only after quality review
`-- scripts/              # Permission Envelope validation
```

Each Skill resolves declared resources relative to its own `SKILL.md`.
Specify installs its conditional repository-boundary reference. Plan-and-Task,
Assess, Fix, Implement, and Review install the shared Context Resume reference;
Plan-and-Task and Implement also install their phase-specific checks or PR
reference.
The extension implementation remains in the installed Specify CLI package and
is not copied into the project. Editable configuration and the stable context
bootstrap live under `.specify/team/`.
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
|-- test.md
|-- work-context.yml
|-- context-pack.md
`-- evidence/
```

The installer adds `/.specify/feature/` and `/.specify/bugfix/` to the target
coding repository's `.gitignore`. These directories are local runtime context,
not Team extension source and not PR payload. Share accepted User Stories,
Plan/Task summaries, verification, and risks through Issue/PR discussion;
promote only significant reviewed HLD or long-term knowledge to project docs.
Existing tracked work packages require a separate, deliberate index cleanup.

## Installation

The default Team-minimal profile installs only the self-contained Team role
skills plus `.specify/team/` state. It does not copy core scripts, the Team
extension implementation, native Spec Kit page templates, constitution,
skills, or workflow:

```bash
specify init . --integration codex
```

For extension development:

```bash
specify extension add extensions/team --dev
```

Use `--skill-profile full` only when native Spec Kit skills are also wanted.
Codex, Claude Code, Cursor Agent, and Trae receive the same role behavior and
their own installed Skill resources.

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
/speckit.team.implement work_id=123
/speckit.team.implement work_id=123 only=T001-T010
/speckit.team.review https://github.com/org/repo/pull/123
```

GitHub Issue/PR operations use authenticated automation when available. GitCode
or another host without a usable CLI/API still supports local review; the
skills print complete Issue/PR Markdown for the user to paste. Manual posting is
a platform transport step, not an extra technical approval.
