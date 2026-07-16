---
description: "Fix a bug from assessment.md, verify it, write fix.md/test.md, and ask before creating a PR"
---

# Team Bug Fix

Apply a bug fix from an approved assessment, run verification, write `fix.md` and `test.md`, and ask the user before creating a pull request.

Resolve `references/` and `scripts/` relative to this installed `SKILL.md`, not
relative to the repository working directory.

## Bootstrap

1. Read the invariant and Bug Fixer sections of
   `references/context-bootstrap.md`.
2. Load `references/issue-lifecycle.md`, `references/work-item-layout.md`, and
   `references/permissions.md` before assessing state and write authorization.

## User Input

```text
$ARGUMENTS
```

Accept any of:

- `assessment=.specify/bugfix/{bug-slug}/assessment.md`;
- `bug_slug=<bug-slug>`;
- a bare bug slug;
- optional `base=<branch>` for a pull request target;
- optional `issue=<issue-url-or-number>` or an issue URL associated with the bugfix.

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
```

All bugfix reports created by this command MUST stay under `BUG_ROOT`.

## Preconditions

Read `ASSESSMENT` in full before changing source code. Stop if it is missing.

Proceed only when `ASSESSMENT` has:

```markdown
- **Status**: approved
```

If the status is `draft` or `needs-info`, stop and ask the user to finish or revise `speckit.team.assess` first. If the status field is absent, treat the assessment as draft.

## Issue State Gate

When the user provides an issue URL or issue number, inspect the issue labels before modifying source code. If `gh` is unavailable or labels cannot be read, stop and ask the user to provide the issue labels or verify the state manually.

Proceed only when the issue has label `status/working`.

If the issue does not have `status/working`, stop and explain that the issue is not in the correct state:

- If it has `status/new-issue`, tell the user the issue still needs review by the relevant people before fixing can start.
- If it has `status/accept`, remind the user to claim the issue and switch the label to `status/working` before running `speckit.team.fix` again.
- For any other status or missing status label, tell the user which labels were found and that `status/working` is required.

Do not change issue labels automatically. Label transitions require user or maintainer action outside this command.

## Implementation Rules

Use the assessment as the source of truth:

- implement the `Fix Strategy`;
- stay within `Permission Boundary -> Proposed Write Paths for Fix` unless the user explicitly approves expanding scope;
- add or update tests from `Test Strategy`;
- keep the change minimal and bug-focused;
- do not edit `assessment.md` during fix; record disagreements or discoveries in `fix.md`.

If the assessment appears wrong or insufficient after investigation, stop changing source code and write `FIX_REPORT` with `Status: blocked` and the reason.

## Verification Rules

Run the verification commands proposed in `assessment.md` when safe and available. Add or update regression tests when the assessment calls for them. Record every command you run, skip, or cannot run; never report a skipped or unavailable check as passing.

## Write fix.md

Write `FIX_REPORT` using this structure:

```markdown
# Bug Fix: <short title>

- **Bug Slug**: <bug-slug>
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

## Pull Request

After writing `fix.md` and `test.md`, ask the user whether to create a pull request. Do not create a PR without explicit user confirmation in the current interaction.

If the user approves and `gh` is available, run `gh pr create` with a concise title and a body that links or references:

- `assessment.md`;
- `fix.md`;
- `test.md`;
- changed files;
- verification commands and results;
- residual risks.

If the user declines, `gh` is unavailable, or PR creation fails, provide manual PR instructions instead. Do not treat a missing PR as a failed fix.

## Final Response

Report:

- bug slug;
- `fix.md` path;
- `test.md` path;
- verification result;
- PR URL if one was created, or manual PR guidance if not.

## Guardrails

- Do not proceed without an approved `assessment.md`.
- Do not edit `assessment.md`.
- Do not write bugfix reports outside `.specify/bugfix/{bug-slug}/`.
- Do not read from or write to `.specify/ai-team/`.
- Do not read `.specify/extensions/team` as project context.
- Do not create a pull request without asking the user first.
- Do not invent test results.
