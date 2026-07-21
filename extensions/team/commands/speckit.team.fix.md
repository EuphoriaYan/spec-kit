---
description: "Fix a ready assessment, verify it, update PR progress, and re-enter review."
---

# Team Bug Fix

Apply a bug fix from a ready or risk-approved assessment, run verification,
write local `fix.md` and `test.md`, update review progress, and automatically
re-enter Review.

## User Input

```text
$ARGUMENTS
```

Accept any of:

- `assessment=.specify/bugfix/{bug-slug}/assessment.md`;
- `bug_slug=<bug-slug>`;
- a bare bug slug;
- optional `base=<branch>` for a pull request target;
- optional `issue=<issue-url-or-number>` or an Issue URL associated with the
  Bugfix.

## Assessment Resolution

Resolve `BUG_ROOT` and `ASSESSMENT` in this order:

1. Use explicit `assessment=<path>` when provided.
2. Use `.specify/bugfix/{bug-slug}/assessment.md` when `bug_slug=<bug-slug>` or a bare slug is provided.
3. If no bug is identified, list candidates under `.specify/bugfix/*/assessment.md` and ask the user to choose in interactive mode; stop in non-interactive mode.

Set:

```text
BUG_ROOT={repository root}/.specify/bugfix/{bug-slug}
ASSESSMENT={BUG_ROOT}/assessment.md
FIX_REPORT={BUG_ROOT}/fix.md
TEST_REPORT={BUG_ROOT}/test.md
WORK_CONTEXT={BUG_ROOT}/work-context.yml
CONTEXT_PACK={BUG_ROOT}/context-pack.md
```

All bugfix reports created by this command MUST stay under `BUG_ROOT`.

## Preconditions

Read `ASSESSMENT` in full before changing source code. Stop if it is missing.

Proceed only when `ASSESSMENT` has either:

```markdown
- **Status**: ready
```

or:

```markdown
- **Status**: approved
```

If the status is `approval-required` or `needs-info`, stop and return to
`speckit.team.assess`; only a named human can resolve a listed gate. If the
status field is absent, treat the assessment as `needs-info`.

Read `references/context.md`. Resume from `WORK_CONTEXT` when present; for an
older Bugfix directory, bootstrap a minimal package from `assessment.md`.
Reconcile identity or phase conflicts before changing source.

Read `references/memory-runtime.md` and retrieve guidance for role `fix`, work
type `bugfix`, and the assessment's affected modules. Binding Knowledge
constrains the fix. Advisory Memory may suggest a known pattern but cannot
replace the assessment or current source evidence.

Set `FLOW_KIND=feature-correction` only when the assessment contains both
`Parent Feature` and `User Stories`; otherwise set
`FLOW_KIND=standalone-bugfix`.

## Conditional Issue State Gate

Apply this section only for `FLOW_KIND=standalone-bugfix` when the user supplies
an Issue URL or Issue number. Without Issue input, skip this section and
continue from the ready or approved assessment.

For `FLOW_KIND=feature-correction`, the parent Feature Issue is intent context,
not a Bug Issue. Never apply the `type/bugfix` gate to `Parent Feature`, its
Issue URL, or the original Issue URL carried by the correction handoff.

Use an authenticated repository integration or host CLI to inspect the supplied
Issue before modifying source code. For GitCode, read
`references/gitcode-host-contract.md` and run its capability probe. Stop if
its repository or labels cannot be
verified. Require the Issue to belong to the coding repository and have
`type/bugfix`.

Proceed only when the Issue has label `status/working`.

If the issue does not have `status/working`, stop and explain that the issue is not in the correct state:

- If it has `status/new-issue`, tell the user the issue still needs review by the relevant people before fixing can start.
- If it has `status/accept`, remind the user to claim the issue and switch the label to `status/working` before running `speckit.team.fix` again.
- For any other status or missing status label, tell the user which labels were found and that `status/working` is required.

Stop when the Issue belongs to another repository or has a type other than
`type/bugfix`.

Do not change issue labels automatically. Label transitions require user or maintainer action outside this command.

## Implementation Rules

Use the assessment as the source of truth:

- implement the `Fix Strategy`;
- stay within `Permission Boundary -> Proposed Write Paths for Fix` unless the user explicitly approves expanding scope;
- add or update tests from `Test Strategy`;
- keep the change minimal and bug-focused;
- do not edit `assessment.md` during fix; record disagreements or discoveries in `fix.md`.

If the assessment appears wrong or insufficient after investigation, stop changing source code and write `FIX_REPORT` with `Status: blocked` and the reason.

For a Feature correction, preserve the assessment's Parent Feature, original
Issue URL, User Story IDs, and Verification clauses in `fix.md` and test
evidence. Do not reinterpret the Review finding from the current implementation.

## Verification Rules

Run the verification commands proposed in `assessment.md` when safe and available. Add or update regression tests when the assessment calls for them. Record every command you run, skip, or cannot run; never report a skipped or unavailable check as passing.

## Write fix.md

Write `FIX_REPORT` using this structure:

```markdown
# Bug Fix: <short title>

- **Bug Slug**: <bug-slug>
- **Primary Issue**: <supplied coding Issue URL or not-provided>
- **Assessment**: ./assessment.md
- **Fixed**: <ISO 8601 UTC>
- **Status**: applied | partial | blocked | not-applied

## Summary

<What changed and why.>

## Files Changed

| File | Change | Reason |
|---|---|---|
| `path/to/file.ext` | modified | <reason> |

## Permission Boundary Compliance

### Proposed Write Paths

- `path/to/file.ext`

### Actually Modified

- `path/to/file.ext`

### Deviations

<None, or user-approved scope expansions.>

## Implementation Notes

<Important details.>

## Follow-ups

- <follow-up>
```

## Write test.md

Write `TEST_REPORT` using this structure:

```markdown
# Bug Fix Verification: <short title>

- **Bug Slug**: <bug-slug>
- **Primary Issue**: <supplied coding Issue URL or not-provided>
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Tested**: <ISO 8601 UTC>
- **Result**: verified | partial | failed | not-run

## Test Strategy from Assessment

<Summary of intended verification.>

## Tests Added or Updated

- `path/to/test.ext` — <what it covers>

## Commands Run

| Command | Result | Notes |
|---|---|---|
| `<command>` | pass / fail / skipped / not-run | <notes> |

## Output Excerpts

<Short relevant excerpts only.>

## Residual Risks

- <risk>
```

## Progress Update And Re-review

After verification, use the `FLOW_KIND` resolved from the assessment.

For a Feature correction, update the existing parent Feature PR discussion.
Include the parent work ID and Issue, Review finding identity, affected User
Story IDs and Verification clauses, addressed root cause, changed files, tests
and results, residual risk, correction round, and `ready for re-review` status.
Do not include the temporary Bug Root or local Bugfix artifact paths.

For a standalone Bugfix with an existing PR, include `Bug Slug`, `Bug Root`,
the `assessment.md` path and status, root-cause/fix summary, changed files,
tests and results, residual risk, and `ready for re-review` status. The paths
identify the complete local Bugfix package; do not stage its runtime files.

- For a supplied GitHub PR and authenticated `gh`, post the comment
  automatically.
- For GitCode or any host without a usable CLI/API, output the complete comment
  under `## Paste Into PR Discussion`. Tell the user where to paste it; this is
  a transport step, not a design approval.
- With no PR, keep the same content in the final response.

Then invoke `speckit.team.review` automatically in local-diff mode, using the
parent Feature `work_id` for Feature corrections or this `bug_slug` for a
standalone Bugfix. Stop after three correction rounds, a repeated finding, or
a human-gate trigger.

## Pull Request

This section creates a PR only for a standalone Bugfix. A Feature correction
already belongs to the parent Feature PR: never create a separate Bugfix PR,
update that PR using `Progress Update And Re-review`, and return directly to
Review.

For a standalone Bugfix, after writing `fix.md` and `test.md`, ask the user
whether to create a pull request. Do not create a PR without explicit user
confirmation in the current interaction.

Before automated submission:

1. Run `git status --short --branch`, determine the default branch without
   switching branches, and stop if the current branch is the default branch.
2. Inspect staged, unstaged, and untracked files. Include only the approved
   Bugfix source and tests, plus only explicitly promoted durable HLD or
   knowledge. `assessment.md`, `fix.md`, `test.md`, context, and evidence under
   `.specify/bugfix/` are local runtime artifacts and must not be staged.
   Exclude local prompts, scratch files, private demand, and
   `spec.override.md`.
3. Confirm the repository is the coding repository and every submitted file
   fits the assessment Permission Boundary. Stop on an unapproved deviation.
4. Require regression evidence in `test.md`, including skipped checks and
   residual risks. Never turn a skipped check into a passing claim.
5. When the change resolves additional Bug Issues, include only symptoms of
   the same root cause and map each Issue to its reproduction and verification
   evidence.
6. Do not stage or overwrite unrelated user changes.

If the user approves and `gh` is available, run `gh pr create` with a concise title and a body that links or references:

- `Bug Slug` and `.specify/bugfix/{bug-slug}/` as the `Bug Root`;
- `assessment.md`, including its status and a public-safe root-cause summary;
- the primary coding Issue, when linked;
- `fix.md` and `test.md`;
- changed files;
- verification commands and results;
- residual risks.

Use the exact labels `Bug Slug:` and `Bug Root:` in a standalone Bugfix PR body
so Review can resolve the complete local package when it is available. These
paths are traceability references, not files to stage or publish. Add `Primary
Issue:` when an Issue is linked.

For a Feature correction, use the existing Feature PR comment instead. Include
the exact labels `Parent Work ID:`, `Review Finding:`, `User Stories:`, and
`Correction Round:`; omit `Bug Root:` and the temporary assessment/fix/test
paths.

If the user declines, `gh` is unavailable, or PR creation fails, provide manual PR instructions instead. Do not treat a missing PR as a failed fix.

## Resume Context

After writing `fix.md` and `test.md`, minimally update `WORK_CONTEXT` and
`CONTEXT_PACK` with the actual files changed, verification result, skipped
checks, residual risks, current phase, last completed Skill, and next Skill.
Use `phase: fix-verified` only when required verification passes; otherwise
record `fix-partial` or `fix-blocked`. Do not duplicate full reports.

## Final Response

Report:

- bug slug;
- supplied Issue URL or `not-provided`;
- `fix.md` path;
- `test.md` path;
- verification result;
- PR URL if one was created, or manual PR guidance if not.

## Guardrails

- Do not proceed without a `ready` assessment or one approved for its listed human-gate triggers.
- When an Issue is linked, do not proceed without verified `type/bugfix` and
  `status/working` labels.
- Do not edit `assessment.md`.
- Do not write bugfix reports outside `.specify/bugfix/{bug-slug}/`.
- Do not create a pull request without asking the user first.
- Do not invent test results.
