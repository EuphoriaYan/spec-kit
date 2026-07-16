---
description: "Review a pull request for correctness, evidence, permissions, and SDD alignment."
---

# Team Pull Request Review

Review an existing pull request and help a human reviewer decide whether it is
merge-ready. This command never creates, edits, approves, merges, or resolves
conversations on a pull request.

Resolve `references/` and `scripts/` relative to this installed `SKILL.md`, not
relative to the repository working directory.

## Bootstrap

1. Read the invariant and Reviewer sections of
   `references/context-bootstrap.md`.
2. Load `references/work-item-layout.md` and `references/permissions.md` before
   resolving feature artifacts or assessing authorization.

## User Input

```text
$ARGUMENTS
```

Require a PR URL or `pr=<number>`. Accept optional
`feature_slug=<slug>`. Reject unsafe slugs containing path separators, `..`, or
anything other than letters, numbers, dots, underscores, and hyphens.

## Phase 1: Fetch PR

1. Require an available, authenticated `gh` CLI. Fetch PR metadata, body,
   commits, changed files, checks, and the complete diff with read-only `gh pr
   view`, `gh pr checks`, and `gh pr diff` operations.
2. Confirm the PR belongs to the current repository. Do not check out the PR or
   modify the working tree merely to review it.
3. Resolve `feature_slug` in this order:
   - explicit user input;
   - a `work-context.yml` whose `pr_url` matches the PR;
   - `Feature slug:` or `Feature root:` in the PR body;
   - an unambiguous feature slug in the PR branch name.
4. When a slug is resolved, set
   `FEATURE_ROOT={repository root}/.specify/feature/{feature-slug}`. All feature
   artifact reads and writes MUST stay under it.

If `gh` is unavailable, authentication fails, the PR cannot be fetched, or its
repository is ambiguous, stop and report the exact manual prerequisite. A
missing feature association does not prevent code review, but it makes SDD
alignment `not assessed` and must affect the verdict.

## Phase 2: Code Review

Review the diff, not just the PR description. Prioritize findings that affect:

- functional correctness, edge cases, error handling, concurrency, and data
  integrity;
- security, privacy, secrets, permission boundaries, and unsafe input handling;
- backward compatibility and public API, schema, configuration, or wire-format
  changes;
- tests that fail to exercise changed behavior or would pass despite a defect;
- unnecessary scope, generated/local files, and unrelated cleanup.

For every finding, cite the narrowest file and line range available and state
the concrete impact and required action. Do not inflate style preferences into
findings.

## Phase 3: SDD Alignment

When `FEATURE_ROOT` is available, read the effective spec (`spec.override.md`
before `spec.md`), `plan-and-task.md`, `plan-and-task-check.md`,
`permission-envelope.yml`, `work-context.yml`,
`evidence/implementation-report.md`, and relevant handoff or codegraph
artifacts when present. Never quote or copy private override content into the
review output.

Check that:

- delivered behavior satisfies the spec and selected tasks;
- the implementation follows the plan or records justified deviations;
- changed files and operations fit the permission envelope;
- implementation evidence supports the PR's test claims;
- task checkboxes, PR body, diff, and work context agree;
- the PR remains minimal and preserves module and dependency boundaries.

Treat missing required artifacts, unapproved deviations, stale evidence, or
permission mismatches as findings rather than silently guessing.

## Phase 4: Verdict

Output:

```text
## Review Findings
- [blocker/major/minor] path:line
  Issue: ...
  Impact: ...
  Required action: ...

## Open Questions
- ...

## Evidence Checked
- PR metadata and checks: ...
- Feature artifacts: ...
- Permission envelope: ...
- Implementation report: ...
- Commands/tests: ...

## Merge Recommendation
approve | request changes | split | architecture review
Reason: ...
```

List findings in descending severity. If there are no findings, explicitly say
so and mention any unassessed or residual risk. Recommend `request changes` for
unresolved blocker/major findings or missing required behavior/evidence;
`split` for unrelated changes with independently reviewable scope; and
`architecture review` for unapproved public-contract, cross-module, privacy, or
high-risk design changes. Human approval remains required.

Optionally, when `FEATURE_ROOT` is unambiguous and repository policy permits
tracked evidence, write the same report to `evidence/review-report.md` and
minimally update `work-context.yml` to `phase: review`,
`last_completed_command: speckit.team.review`, and an ISO 8601 UTC `updated_at`.
Preserve unknown fields. Do not write these artifacts when doing so would modify
an unrelated or dirty working tree without the user's permission.
