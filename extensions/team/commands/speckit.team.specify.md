---
description: "Specify an accepted repository Feature Record, with a legacy path for publishing a single Feature Issue."
---

# Spec Kit Team Specify

Own the Business/Product specification boundary for one Feature. The preferred
record-backed mode consumes `feature_id=<id>` and writes its formal `spec.md`.
The legacy mode still accepts a plain Feature/new-project demand and publishes
or prints one primary remote Issue. Never create architecture Plans, Tasks, or
Bugfix artifacts.

Do not load architecture or implementation chat history.

## Input

```text
$ARGUMENTS
```

The user may provide:

- `feature_id=<id>` for the repository Feature Record workflow;
- one sentence or an existing Feature Issue URL for the legacy Issue workflow;
- additional requirement context.

If the request is a defect, explain that it belongs to the Bugfix intake skill
and stop without inventing Feature artifacts.

## Preferred Record-Backed Mode

When `feature_id=<id>` is present:

1. Read `references/feature-lifecycle.md`.
2. Resolve the configured Feature Record and `.specify/<feature_id>/` work root
   with the installed `scripts/feature_records.py`; never hard-code the
   repository Feature directory.
3. Run:

   ```text
   scripts/check_feature_record.py --feature-id <id> --require-accepted
   ```

   Stop on a missing/unaccepted Feature, an unlocked Feature Record location,
   Catalog mismatch, or invalid identity.
4. Read the parent Requirement Issue and the accepted Feature Record. Do not
   require L0/L1 files. When present, use them only as project constraints;
   when absent, continue without creating placeholders.
5. Transition the Feature Record from `backlog` to `specifying` before
   specification work, validating the previous phase. Read
   `references/feature-spec.md` immediately before writing
   `.specify/<feature_id>/spec.md`. Specify complete User Stories, observable
   `VER-###` behavior, scope, non-goals, boundaries, compatibility constraints,
   parent Requirement traceability, and Feature Catalog traceability.
6. Create or update minimal `work-context.yml` and `context-pack.md`; after the
   Spec is complete, transition `specifying` to `planning` and set the next Skill to
   `speckit.team.plan-and-task feature_id=<id>`.
7. Rerun the Feature Record validator for each transition. Never
   accept the Feature or approve an architecture decision on behalf of a human.

In this mode do not create another remote Feature Issue. The Feature Record is
the repository delivery identity and the parent Requirement Issue is the remote
requirement authority.

Output:

```text
Team Specify Result:
- mode: feature-record
- Feature ID and Record:
- parent Requirement Issue:
- Feature acceptance:
- Spec: .specify/<feature_id>/spec.md
- optional architecture context:
- delivery transition:
- next Skill: speckit.team.plan-and-task feature_id=<id>
- result: specified / revise / blocked
```

The remaining sections apply only to legacy Issue mode.

## Legacy Issue Mode

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

If the repository or privacy boundary is unclear, read
`references/repository-boundary.md` before presenting the publication
decision. Do not preload it for an already unambiguous public coding-repository
request.

Show the exact title, body, repository, and labels, then ask the user to choose:

- **发布（`publish`）**: create the Issue. The user may simply say “发布”;
- **仅输出（`output only`）**: print the final Issue and create nothing. The
  user may say “只输出内容”;
- **修改（`revise`）**: continue the conversation and rerun the affected
  readiness pass. The user may say “修改需求” and describe the change;
- **停止（`stop`）**: create and persist nothing. The user may say “先停一下”.

Present the labels in the user's language, keep the stable internal value in
parentheses, and explicitly say that the user can reply with the natural phrase
instead of copying the internal value. Never require users to remember an
English workflow token.

For GitHub, use an available authenticated GitHub integration or `gh`. For
GitCode, read `references/gitcode-host-contract.md` and run its capability
probe before any remote operation. For other Git hosts, use an available
authenticated repository integration, API, CLI, or browser. If the host is
unsupported, authentication is unavailable, a
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
- current step: Issue publication decision
- next options: localized labels, stable internal values, and natural-language aliases
- recommended next step: one option plus a short reason; never choose it for the user
- result: published-new-issue / output-only / revise / blocked
```

Stop when the request is a Bugfix, privacy-safe publication cannot be
established, a required User Story remains unclear, or the user declines both
publication and output.
