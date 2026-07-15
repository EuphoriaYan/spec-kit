# AI Team Role Extension

The `team` extension adds two role-isolated skills without changing native Spec Kit commands:

| Skill | Role | Input | Durable output |
|---|---|---|---|
| `speckit.team.specify` | Business / Product | plain-language Feature or new-project demand | published Feature Issue, or Issue text in the current response |
| `speckit.team.plan-and-task` | Architect | Issue URL at `status/accept` or `status/working` plus source | Feature `spec.md` when applicable, Code Graph impact, Plan, parallel Tasks, self-tests, generated check |

Bugfix intake is owned by a separate preceding skill. Plan-and-Task accepts its reviewed `type/bugfix` Issue but does not require a Bugfix `spec.md`.

## Role Boundary

Roles do not share hidden chat context. Specify publishes complete User Stories to the Issue. The Technical Committee or delegated authority discusses the demand and applies `status/accept` outside the skill. Plan-and-Task then reads the Issue body, accepted discussion, labels, decision evidence, and current source.

An accepted Issue body is primary. Suggestions and rejected alternatives in comments are not requirements. Before acceptance, maintainers should consolidate accepted changes into the Issue body; an explicit decision comment may supplement it.

## Labels And Identity

Use exactly one type and one status label:

```text
type/feature | type/bugfix
status/new-issue | status/accept | status/working | status/close
```

The Issue URL is the global identity. Coding-repository work uses the numeric Issue ID as `work_id`; enhancement-repository work uses `enhancement-<issue-id>` to avoid collisions.

## Feature Flow

```text
plain-language demand
-> speckit.team.specify
-> natural clarification
-> one completeness pass per Issue and User Story
-> publish Issue or print final Issue text
-> status/new-issue discussion
-> Technical Committee sets status/accept
-> speckit.team.plan-and-task reads Issue and comments
-> create feature/<work_id>/spec.md
-> Code Graph and impact
-> Plan HLD
-> human continue / pause / revise
-> parallel single-module Tasks and minimum self-tests
-> generated plan-and-task-check.md
```

Specify writes no local checklist, Issue draft, Work Context, or `spec.md`.

## Bugfix Flow Boundary

```text
observed defect
-> separate Bugfix intake skill
-> reviewed type/bugfix Issue
-> status/accept or status/working
-> speckit.team.plan-and-task
-> Bugfix summary in plan-and-task.md, without spec.md
-> Code Graph, root-cause evidence, regression Tasks, self-tests, check
```

Several Bug Issues may map to one change only when they are symptoms of the same root cause and each has separate reproduction and verification evidence.

## Planning Rules

The Plan is Issue-wide HLD. Each Task is a small LLD unit scoped to one module and designed for parallel assignment. The module must have a clear repository path and responsibility; a named Module Owner is optional. When Tasks cannot run in parallel, the Plan records the dependency, handoff artifact, serialization reason, and unblock evidence.

Public API, SPI, configuration, protocol, schema, database ownership, or cross-module semantics still require the appropriate human architecture or contract authority.

## Installed Skill Layout

Each supported skills-based integration receives a self-contained directory:

```text
speckit-team-<role>/
|-- SKILL.md
|-- references/
`-- scripts/
```

The Skill resolves these resources relative to its own `SKILL.md`. The complete extension remains under `.specify/extensions/team/` for registration, upgrade, shared configuration, and repository context pointers. References are loaded progressively; they are not separately exposed as user skills.

Plan-and-Task must run its installed `scripts/check_plan_and_task.py`. The script generates `plan-and-task-check.md`; a model may fix source artifacts but may not hand-write a passing result. Human decisions remain in the Issue and Plan review record.

## Work Directories

```text
.specify/feature/<work_id>/   # includes spec.md
.specify/bugfix/<work_id>/    # no spec.md
```

Commit Feature Specs, Plans, generated checks, and reviewed evidence. Ignore `spec.override.md`, private customer text, credentials, and local memory.

## Installation

The default Team-minimal profile keeps the Spec Kit engine but installs only the Team role skills:

```bash
specify init . --integration codex
```

Use `--skill-profile full` only when native Spec Kit skills are also wanted. Codex, Claude Code, Cursor Agent, and Trae receive the same role behavior and their own installed Skill resources.

## Chat Entry

Users do not need to name a skill:

```text
Please add CSV export to the current project. Export the same fields shown in the result list, and help me turn this into a reviewable requirement.
```

The AI routes a new Feature to Specify. After governance acceptance, a user can start planning with:

```text
Please plan the accepted work at <Issue URL>. Pause after the HLD so we can discuss it before decomposing Tasks.
```
