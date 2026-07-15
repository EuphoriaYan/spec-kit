# AI Team Role Extension

The `team` extension adapts Spec Kit for enterprise collaboration without
changing native Spec Kit commands, templates, or prompts. This iteration
exposes exactly two agreed skills:

| Skill | Human/AI role | Input | Durable output |
|---|---|---|---|
| `speckit.team.specify` | Business / Product | one sentence, Issue URL, or confidential handoff URL | primary Issue plus `spec.md`, or Bug Issue plus reproduction |
| `speckit.team.plan-and-task` | Architect / Module Owner | accepted `spec.md` and source | Code Graph impact, `plan-and-task.md`, `plan-and-task-check.md`, minimum self-tests |

The skills are installed by the extension and appear as `speckit-team-*`
folders in skills-based AI tools. Command IDs use the Spec Kit canonical form
`speckit.team.*`.

Both skills use the same work directory:

```text
.specify/<feature|bugfix>/<work_id>/
|-- spec.md
|-- plan-and-task.md
`-- plan-and-task-check.md
```

## Four-Skill Target

The target model contains four large role skills. This iteration implements
`specify` and `plan-and-task`; `implement` and `review` are planned and are not
advertised until their command files are installed. Roles intentionally do not
share hidden chat context. They communicate
through an Issue and `spec.md`, then `plan-and-task.md`, its check, and the Work
Context Package.

The primary Issue is created during Specify. It is not deferred until Tasks.
Tasks are engineering decomposition and may contain LLD-level file, class,
function, data-flow, migration, and test details. Native
`speckit.taskstoissues` is never the source of the primary Feature Issue.

## Module Ownership And Parallel Tasks

The authoritative module card lives in each code module's `README.md`. Copy
[`templates/module-readme-template.md`](templates/module-readme-template.md)
into a module root and maintain the owner, review route, responsibility, public
contracts, dependency direction, and test entry points there. The project root
README may index module cards. `CODEOWNERS` is useful for review automation but
is not a substitute for module architecture documentation.

`speckit.team.plan-and-task` uses those cards to write an Issue-wide Plan (HLD)
and single-module Tasks (LLD). Tasks are parallel by default and can be assigned
to different contributors. When a Task must wait for another, the Plan records
the dependency, handoff artifact, serialization reason, and unblock evidence.

## Feature Flow

```text
plain-language demand
-> speckit.team.specify
-> user approves the exact Issue draft for publication
-> published state/draft Issue and spec.md
-> Technical Committee changes the Issue to state/accepted outside the skill
-> speckit.team.plan-and-task
-> deterministic plan-and-task-check.md
-> architecture/module-owner review
-> speckit.team.implement (planned)
-> speckit.team.review (planned)
```

There is no AI Team workflow runner. The human starts each role skill from chat,
and the skill performs its own checks before stopping at the next human decision
boundary. Standard and Compact planning use the same role skill; Compact only
shortens the Plan and Tasks after a human confirms low risk.

## Bugfix Flow

```text
observed defect
-> speckit.team.specify
-> user approves the exact Bug Issue draft for publication
-> reviewed Bug Issue and reproduction
-> speckit.team.plan-and-task
-> deterministic plan-and-task-check.md
-> reviewed root cause, scope, regression tests, and rollback
-> speckit.team.implement (planned)
-> speckit.team.review (planned)
```

Several same-root-cause Issues may map to one change
when each symptom has separate reproduction and verification evidence.

## Internal Capabilities

Only the two agreed skill files live under `commands/`. Supporting material lives
under `references/internal/`, `docs/`, and `scripts/`:

- context initialization and resume;
- privacy-aware Intake and repository boundary;
- confidential requirement URL synchronization;
- Permission Envelopes;
- Code Graph adapters and impact analysis;
- evidence finalization, review, retrospective, memory, and release archive.

A role loads these references progressively. They are not separately registered
as user skills, so users see two coherent entry points instead of a toolbox of
partial commands.

`speckit.team.plan-and-task` must run
`scripts/check_plan_and_task.py`. The script reads the Spec and Plan front
matter plus their structured tables, then generates the check file. A model may
revise source documents in response to findings but may not hand-write a
passing check.

## Context And Git

Repository rules contain only a short managed pointer to
`.specify/extensions/team/docs/context-bootstrap.md`. Every role reruns the
initializer after a new chat, resume, or context compression.

| Artifact | Git |
|---|---|
| Issue, `spec.md`, `plan-and-task.md`, `plan-and-task-check.md`, enterprise guidance | commit |
| approved architecture and Evidence Board required by team policy | commit |
| `spec.override.md`, private customer text, local memory | ignore |
| department memory | follow repository privacy policy |

## Installation

The recommended installation is the Team-minimal profile:

```bash
specify init . --integration codex
```

This keeps the full Spec Kit engine while registering only the skills declared
by this extension; the native Spec Kit workflow is also omitted. To expose the
native Spec Kit skills and workflow as well, use:

```bash
specify init . --integration codex --skill-profile full
```

Initialization installs `team` directly and atomically refreshes `AGENTS.md`,
`CLAUDE.md`, Cursor rules, or Trae rules for the detected integrations. The
generic bundle system remains available for unrelated multi-component stacks,
but AI Team no longer depends on a bundle, `bug`, or `agent-context`.

## Chat Entry

Users start from chat with a normal sentence:

```text
Please add CSV export to the current project. Keep the exported columns aligned
with the result list, and use Compact planning only if the architecture impact
is demonstrably low.
```

The AI tool should select `speckit.team.specify`, classify the work, and stop at
the appropriate human decision boundary. After acceptance, start
`speckit.team.plan-and-task` with the Issue URL or Work ID. The two roles share
documents and Issues, not hidden chat context.
