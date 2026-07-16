---
description: "Review a pull request for correctness, evidence, permissions, and SDD alignment."
---

# Team Pull Request Review

Review an existing pull request and help a human reviewer decide whether it is
merge-ready. This command never creates, edits, approves, merges, or resolves
conversations on a pull request.

## User Input

```text
$ARGUMENTS
```

Require a PR URL or `pr=<number>`. Accept optional `work_id=<id>` for Feature
or `bug_slug=<slug>` for Bugfix, but never both. Reject unsafe identifiers
containing path separators, `..`, or anything other than letters, numbers,
dots, underscores, and hyphens.

## Phase 1: Fetch PR

1. Require an available, authenticated `gh` CLI. Fetch PR metadata, body,
   commits, changed files, checks, and the complete diff with read-only `gh pr
   view`, `gh pr checks`, and `gh pr diff` operations.
2. Confirm the PR belongs to the current repository. Do not check out the PR or
   modify the working tree merely to review it.
3. Resolve at most one work association in this order:
   - explicit `work_id` or `bug_slug`;
   - `Work ID:`, `Feature root:`, `Bug Slug:`, or `Bug Root:` in the PR
     body;
   - a Feature `work-context.yml` whose `pr_url` matches the PR;
   - an unambiguous Feature work ID or Bugfix slug in the PR branch name.
4. Set `WORK_TYPE` and `WORK_ROOT` to either
   `.specify/feature/{work_id}` or `.specify/bugfix/{bug-slug}`. Reject an
   ambiguous match. All artifact reads and optional evidence writes MUST stay
   under `WORK_ROOT`.

When `WORK_ROOT` is resolved, read `references/context.md` and reconcile its
identity and phase with the PR before lifecycle review.

If `gh` is unavailable, authentication fails, the PR cannot be fetched, or its
repository is ambiguous, stop and report the exact manual prerequisite. A
missing work association does not prevent code review, but it makes lifecycle
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

## Phase 3: Lifecycle Alignment

For Feature, read the effective spec (`spec.override.md` before `spec.md`),
`plan-and-task.md`, `plan-and-task-check.md`, `permission-envelope.yml`,
`work-context.yml`, `evidence/implementation-report.md`, and relevant handoff
or Code Graph artifacts. Never quote or copy private override content into the
review output.

For Bugfix, require `assessment.md`, `fix.md`, and `test.md`. Read any `Primary
Issue` from `fix.md` or the PR body and confirm that it belongs to the coding
repository with `type/bugfix`; an absent Issue is not a Bugfix blocker. Check that the
assessment was human-approved, the fix stayed inside its proposed write paths
or records approved deviations, and `test.md` contains regression evidence for
the observed symptom. When one PR resolves additional Bug Issues, require each
to represent another symptom of the same root cause and map each Issue to
reproduction and verification.

Check that:

- delivered behavior satisfies the Feature spec and Tasks or the approved
  Bugfix assessment;
- the implementation follows the Plan or Fix Strategy and records justified
  deviations;
- changed files and operations fit the Feature Permission Envelope or Bugfix
  Permission Boundary;
- implementation or Bugfix test evidence supports the PR's claims;
- Feature Task state or Bugfix reports, PR body, diff, and any linked primary
  Issue agree;
- coding changes are in the coding repository and private demand or internal
  enhancement drafts are absent;
- the as-built dependency direction, state ownership, Code Graph impact, and
  public contracts match the approved design;
- touched files stay inside the approved module or Bugfix write boundary and do
  not edit another module's internals to bypass a public interface;
- API, SPI, config defaults, wire/data shapes, examples, golden files, and
  snapshots remain forward-compatible, or the responsible human approval and
  migration path are recorded;
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
- work type and identity (`work_id` or `bug_slug`): ...
- linked primary Issue and additional Bug Issues, if any: ...
- Feature or Bugfix artifacts: ...
- permission envelope or boundary: ...
- implementation or Bugfix reports: ...
- Commands/tests: ...

## Merge Recommendation
approve | request changes | split | architecture review
Reason: ...

## Durable Follow-up
- none / test / gate / skill / Code Graph knowledge / human decision
- reason and owning repository: ...
```

List findings in descending severity. If there are no findings, explicitly say
so and mention any unassessed or residual risk. Recommend `request changes` for
an absent required Feature Issue, private-demand
leakage, missing required artifacts, unresolved blocker/major findings, or
missing behavior/evidence;
`split` for unrelated changes with independently reviewable scope; and
`architecture review` for unapproved public-contract, cross-module, privacy, or
high-risk design changes. Human approval remains required.

Use `Durable Follow-up` only when a review finding or failure pattern is likely
to recur. Recommend the smallest durable control: a regression test, mechanical
gate, role Skill correction, Code Graph or project-knowledge update, or an
explicit human decision. Do not modify Skills, promote memory, or change
governance records as part of Review.

Optionally, when `WORK_ROOT` is unambiguous and repository policy permits
tracked evidence, write the same report to `evidence/review-report.md`. For
either work type, minimally update `work-context.yml` to `phase: review`,
`last_completed_skill: speckit.team.review`, and an ISO 8601 UTC `updated_at`.
Preserve unknown fields. Do not write evidence when doing so would modify an
unrelated or dirty working tree without the user's permission.
