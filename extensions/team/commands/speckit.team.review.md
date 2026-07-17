---
description: "Review a pull request or local implementation diff for correctness, evidence, permissions, and SDD alignment."
---

# Team Pull Request Review

Review an existing pull request or a verified local implementation diff. Help
a human make the final merge decision, and optionally route repairable findings
through the automatic Assess -> Fix -> Re-review loop. This command never
approves or merges a pull request.

## User Input

```text
$ARGUMENTS
```

Accept a PR URL, `pr=<number>`, or `local=true`. Accept optional `work_id=<id>` for Feature
or `bug_slug=<slug>` for Bugfix, but never both. Reject unsafe identifiers
containing path separators, `..`, or anything other than letters, numbers,
dots, underscores, and hyphens.

Accept optional `auto_fix=true` and `iteration=<1..3>`. Auto-fix is allowed
only for blocker/major findings that stay inside the accepted Plan and current
permission boundary and trigger none of the permanent human decisions.

## Phase 1: Load Review Target

1. For a GitHub PR, use an available authenticated integration or `gh`. Fetch PR metadata, body,
   commits, changed files, checks, and the complete diff with read-only `gh pr
   view`, `gh pr checks`, and `gh pr diff` operations.
2. For `local=true`, inspect the current branch, merge base, committed and
   uncommitted diff, changed files, and local verification evidence. Do not
   require a PR or remote CLI.
3. For a non-GitHub PR such as GitCode, use an authenticated host integration
   when available. Otherwise review the matching local branch/diff plus
   user-supplied PR metadata. Clearly mark remote checks or comments that could
   not be fetched; do not block source review solely because `gh` is absent.
4. Confirm the PR belongs to the current repository. Do not check out the PR or
   modify the working tree merely to review it.
5. Resolve at most one work association in this order:
   - explicit `work_id` or `bug_slug`;
   - `Work ID:`, `Bug Slug:`, or `Bug Root:` in the PR
     body;
   - a Feature `work-context.yml` whose `pr_url` matches the PR;
   - an unambiguous Feature work ID or Bugfix slug in the PR branch name.
6. Set `WORK_TYPE` and `WORK_ROOT` to either
   `.specify/feature/{work_id}` or `.specify/bugfix/{bug-slug}`. Reject an
   ambiguous match. All artifact reads and optional evidence writes MUST stay
   under `WORK_ROOT`.

When `WORK_ROOT` is resolved, read `references/context.md` and reconcile its
identity and phase with the PR before lifecycle review.

If remote content cannot be fetched and no matching local diff or pasted patch
is available, stop and report the exact prerequisite. A missing work
association does not prevent code review, but it makes lifecycle alignment
`not assessed` and must affect the verdict.

## Phase 2: Code Review

Read `references/memory-runtime.md` and retrieve guidance for role `review`, the
resolved work type, and changed modules. Review binding Knowledge as project
policy. Use advisory Memory only to look for recurrent failure patterns; never
raise a finding solely because a past attempt differed.

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

For Feature, read the authoritative Issue and effective spec
(`spec.override.md` before `spec.md`),
`plan-and-task.md`, `plan-and-task-check.md`, `permission-envelope.yml`,
`work-context.yml`, `evidence/implementation-report.md`, and relevant handoff
or Code Graph artifacts. Never quote or copy private override content into the
review output.

For Bugfix, require `assessment.md`, `fix.md`, and `test.md`. When the Bugfix
was created from a Feature review finding, first load the parent Feature Issue,
effective spec, and referenced User Story IDs so the finding cannot redefine
the expected behavior. Read any `Primary
Issue` from `fix.md` or the PR body and confirm that it belongs to the coding
repository with `type/bugfix`; an absent Issue is not a Bugfix blocker. Check that the
assessment was `ready` or human-approved when a gate was triggered, the fix stayed inside its proposed write paths
or records approved deviations, and `test.md` contains regression evidence for
the observed symptom. When one PR resolves additional Bug Issues, require each
to represent another symptom of the same root cause and map each Issue to
reproduction and verification.

Check that:

- delivered behavior satisfies the Feature spec and Tasks or the ready/risk-approved
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

## Phase 4: Verdict And Correction Routing

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

## Final Conclusion
GO | GO-WITH-RISK | NO-GO
Reason: ...
Residual risks: none / ...

## Required Next Action
none | automatic correction | revise | split | architecture review | human decision
Reason: ...

## Durable Follow-up
- none / test / gate / skill / Code Graph knowledge / human decision
- reason and owning repository: ...
```

List findings in descending severity. If there are no findings, explicitly say
so and mention any unassessed or residual risk. Use exactly one final conclusion:

- `GO`: required evidence passes, scope and architecture match the accepted
  design, no blocker/major/minor finding remains, and no human gate is open.
- `GO-WITH-RISK`: no blocker or major finding remains and required behavior is
  verified, but bounded minor findings, explicitly skipped external checks, or
  other understood residual risks remain. List every risk; a human decides
  whether to merge.
- `NO-GO`: any blocker or major finding, missing or stale required evidence,
  unverified required behavior, permission/scope mismatch, unresolved human
  gate, repeated blocker/major finding, or exhausted correction loop remains.
  Do not merge.

Keep routing separate from the conclusion. Use `revise` for ordinary unresolved
findings, `split` for unrelated independently reviewable changes,
`architecture review` for public-contract, cross-module, privacy, or high-risk
design decisions, `automatic correction` when the bounded repair loop may
continue, and `human decision` for a permanent gate or final merge choice.

When `auto_fix=true`, blocker/major findings are repairable, and iteration is
below three, create a correction handoff containing the finding identity,
original Issue URL, User Story IDs and Verification clauses, accepted Plan
scope, allowed paths, and current diff revision. Invoke `speckit.team.assess`
with that handoff, then `speckit.team.fix`, then repeat this Review with the
incremented iteration. Never use implementation behavior as the source of the
expected result.

Stop automatic correction for a repeated finding/root cause, iteration three,
unclear intent, or any requirement-acceptance, HLD/cross-module/public-interface,
dependency/security/license/incompatibility, Plan-expansion, or merge decision.
Minor-only results may be `GO-WITH-RISK`; list every residual risk for the
human merge decision.

Use `Durable Follow-up` only when a review finding or failure pattern is likely
to recur. Recommend the smallest durable control: a regression test, mechanical
gate, role Skill correction, Code Graph or project-knowledge update, or an
explicit human decision. Do not modify Skills, promote memory, or change
governance records as part of Review.

Optionally, when `WORK_ROOT` is unambiguous, write the same report to the local
`evidence/review-report.md`. This work root is Git-ignored. For
either work type, minimally update `work-context.yml` to `phase: review`,
`last_completed_skill: speckit.team.review`, and an ISO 8601 UTC `updated_at`.
Preserve unknown fields. Do not write evidence when doing so would modify an
unrelated or dirty working tree without the user's permission.

## Host Output

For GitHub with authenticated automation, post the review or progress comment
when the user requested remote review. For GitCode or another host without a
usable CLI/API, output a complete `## Paste Into PR Discussion` Markdown block
containing findings, evidence, current correction round, residual risk, and
final conclusion. State that manual posting is a transport step, not a
technical approval gate.
