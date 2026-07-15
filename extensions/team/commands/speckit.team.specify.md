---
description: "Business/Product role for turning a plain-language Feature or new-project demand into a complete, reviewable Issue."
---

# Spec Kit Team Specify

Own the Business/Product role for Feature and new-project demand. Start from a
natural conversation, clarify complete User Stories, and publish or print one
primary Issue. Do not create local requirement drafts, `spec.md`, architecture
plans, Tasks, or Bugfix artifacts.

Resolve `references/` and `scripts/` relative to this installed `SKILL.md`, not
relative to the repository working directory.

## Bootstrap

1. Run the installed `scripts/init_role_context.py` by its resolved path.
2. Read the invariant and Business/Product sections of
   `references/context-bootstrap.md`.
3. Load only when needed:
   - `references/issue-lifecycle.md` for labels and governance state;
   - `references/repository-boundary.md` for public or confidential placement.

Do not load architecture or implementation chat history.

## Input

```text
$ARGUMENTS
```

The user may provide one sentence, an existing Feature Issue URL, or additional
context. If the request is a defect, explain that it belongs to the Bugfix
intake skill and stop without inventing a Feature Issue.

## Conversation First

1. Let the user explain the demand in their own words. Establish the affected
   user, desired capability, important context, and broad boundary before
   applying a structured checklist.
2. Split a large demand into independently understandable User Stories. Work
   through one Story at a time so later Stories can reuse established context.
3. Ask one focused question only when the answer materially changes a Story,
   scope, publication safety, or target repository. Do not turn the opening
   conversation into a form interview.

## Readiness Pass

After the demand is substantially understood, perform one explicit
completeness pass. Fill known answers first, then ask only for missing blocking
information.

For the whole Issue, check:

- Feature versus new project is understood;
- target repository and privacy boundary are known;
- scope and important non-goals are not contradictory;
- unresolved questions do not prevent review.

For every User Story, check:

- a concrete user or affected party;
- the capability they need;
- the value or outcome;
- preconditions or triggering context;
- a main scenario;
- an important boundary or failure scenario when relevant;
- observable `Verification` behavior with a stable `VER-###` ID.

Repeat only the affected Story's readiness pass after a material revision. Do
not persist the checklist or an Issue draft to disk.

## Issue Format

Present one complete Issue using this shape. `Background / Goal`, `Scope`,
`Non-Goals`, and `Open Questions` are optional when they add useful context.

```markdown
# <Feature title>

## User Stories

### US-001: <Story title>

As a <user>, I want <capability>, so that <value>.

- Preconditions:
- Main scenario:
- Boundary or failure scenario:
- Verification (`VER-001`):

## Background / Goal

## Scope

## Non-Goals

## Open Questions
```

`Verification` is the observable result that future planning, self-tests, and
review can trace. It is not Issue acceptance; governance acceptance is
represented only by `status/accept`.

The proposed labels must be exactly:

- `type/feature`;
- `status/new-issue`.

New-project demand also uses `type/feature`.

## Publication Decision

Show the exact title, body, repository, and labels, then ask the user to choose:

- `publish`: create the Issue;
- `output only`: print the final Issue in the current response and create
  nothing;
- `revise`: continue the conversation and rerun the affected readiness pass;
- `stop`: create and persist nothing.

For GitHub, use an available authenticated GitHub integration or `gh`. For
other Git hosts, use an available authenticated repository integration, API,
CLI, or browser. If the host is unsupported, authentication is unavailable, a
tool is missing, or publication fails, fall back to `output only`. Report the
failure honestly and never claim that an Issue was created.

Publishing creates `status/new-issue`; it does not accept the Feature. The
Technical Committee or delegated authority changes the Issue to
`status/accept` outside this skill after discussion. Never assign
`status/accept` or continue into architecture planning.

## Output

```text
Team Specify Result:
- work type: feature / new-project
- target repository:
- Issue URL: <url or not-created>
- labels: type/feature, status/new-issue
- User Stories:
- privacy boundary:
- unresolved non-blocking questions:
- publication decision: published / output-only / revise / stopped
- next step: Issue discussion / Technical Committee decision / revise / stop
- result: published-new-issue / output-only / revise / blocked
```

Stop when the request is a Bugfix, privacy-safe publication cannot be
established, a required User Story remains unclear, or the user declines both
publication and output.
