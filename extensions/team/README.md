# AI Team Role Extension

The `team` extension provides six role-oriented skills without changing native
Spec Kit commands:

| Skill | Role | Input | Durable output |
|---|---|---|---|
| `speckit.team.specify` | Business / Product | plain-language Feature or new-project demand | published Feature Issue, or Issue text in the current response |
| `speckit.team.plan-and-task` | Architect | accepted/working Issue plus source | Feature spec when applicable, Code Graph impact, Plan, parallel Tasks, self-tests, generated check |
| `speckit.team.assess` | Bug Assessor | Issue URL or defect description | approved `assessment.md` with impact, permissions, fix, and test strategy |
| `speckit.team.fix` | Bug Fixer | approved assessment and optional tracked Issue | source fix, `fix.md`, `test.md`, optional PR |
| `speckit.team.implement` | Developer | task-ready Feature artifacts and permission envelope | source changes, completed Tasks, verification evidence, optional PR |
| `speckit.team.review` | Reviewer | PR URL or number | prioritized findings and merge recommendation |

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

The Issue URL is the global identity. Coding-repository work uses the numeric
Issue ID as `work_id`; enhancement-repository work uses
`enhancement-<issue-id>` to avoid collisions.

Feature delivery uses `.specify/feature/<work_id>/`. Bugfix delivery uses
`.specify/bugfix/<work_id>/`: Assess writes `assessment.md`; Fix requires its
human-approved status, then writes `fix.md` and `test.md`. For a tracked Issue,
Fix also requires `status/working` and never changes labels automatically.

## Feature Flow

```text
plain-language demand
-> speckit.team.specify
-> publish Issue and complete governance acceptance
-> speckit.team.plan-and-task
-> create .specify/feature/<work_id>/ artifacts
-> Code Graph, Plan HLD, parallel Tasks, self-tests, generated check
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
or resolves conversations on a PR.

## Bugfix Flow

```text
observed defect
-> speckit.team.assess
-> assessment, impact, permission boundary, fix and test strategy
-> human approval and optional type/bugfix Issue at status/new-issue
-> maintainer moves claimed work to status/working
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

Implementation requires task-ready artifacts and a permission envelope. It
marks only completed Task checkboxes, records commands and test results in
`evidence/implementation-report.md`, and reaches `phase: verified` without
requiring a PR. PR submission details are loaded progressively only after
verification and user confirmation.

Public API, SPI, configuration, protocol, schema, database ownership, or
cross-module semantics still require the appropriate human architecture or
contract authority.

## Installed Skill Layout

Each supported skills-based integration receives a self-contained directory:

```text
speckit-team-<role>/
|-- SKILL.md
|-- references/
`-- scripts/
```

The Skill resolves declared resources relative to its own `SKILL.md`. The
complete extension remains under `.specify/extensions/team/` for registration,
upgrade, shared configuration, and progressively loaded delivery prompts.

Plan-and-Task must run its installed `scripts/check_plan_and_task.py`. The
script generates `plan-and-task-check.md`; a model may fix source artifacts but
may not hand-write a passing result. Human decisions remain in the Issue and
Plan review record.

## Work Directories

```text
.specify/feature/<work_id>/   # includes spec.md
.specify/bugfix/<work_id>/    # no spec.md
```

Commit Feature Specs, Plans, generated checks, and reviewed evidence according
to repository policy. Ignore `spec.override.md`, private customer text,
credentials, and local memory. Delivery commands never fall back to legacy
repository-root `specs/` or `.specify/ai-team/work/` paths.

## Installation

The default Team-minimal profile keeps the Spec Kit engine and installs the
Team role skills:

```bash
specify init . --integration codex
```

For extension development:

```bash
specify extension add team --dev extensions/team
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
/speckit.team.assess https://github.com/org/repo/issues/123
/speckit.team.assess "Login returns 500 after session expiry" bug_slug=login-session-expiry
/speckit.team.fix bug_slug=login-session-expiry
/speckit.team.implement feature_slug=123
/speckit.team.implement feature_slug=123 only=T001-T010
/speckit.team.implement feature_slug=123 submit_pr=true
/speckit.team.review https://github.com/org/repo/pull/123
```

Pull request operations and Review require GitHub CLI access. Without `gh`,
Implement and Fix can still finish and provide a manual PR checklist. Delivery
commands never use the legacy repository-root `specs/` or
`.specify/ai-team/work/` paths. Bugfix commands do not use `.specify/ai-team/`
and never treat `.specify/extensions/team` as application evidence.
