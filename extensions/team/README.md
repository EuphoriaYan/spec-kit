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

## Why Only Two Are Implemented Here

The target model contains four large role skills. This iteration implements only
the two whose contracts and names have been agreed. Roles intentionally do not
share hidden chat context. They communicate
through an Issue and `spec.md`, then `plan-and-task.md`, its check, and the Work
Context Package. Later decision, implementation, test, and review skills remain
uncommitted until their ownership and names are agreed.

The primary Issue is created during Specify. It is not deferred until Tasks.
Tasks are engineering decomposition and may contain LLD-level file, class,
function, data-flow, migration, and test details. Native
`speckit.taskstoissues` is never the source of the primary Feature Issue.

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
-> later role skill (outside this extension iteration)
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
-> later role skill (outside this extension iteration)
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

The recommended installation is the bundle:

```bash
specify init . --integration codex --integration-options="--skills"
specify bundle catalog add https://raw.githubusercontent.com/EuphoriaYan/spec-kit/main/bundles/catalog.json --id ai-team --policy install-allowed
specify bundle install ai-team
```

Manual installation:

```bash
specify extension add team
specify extension add bug
specify extension add agent-context
```

The recommended bundle initializes AI rule files during installation. A manual
extension-only install must run the idempotent initializer once before the first
chat:

```bash
python .specify/extensions/team/scripts/init_role_context.py
```

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
