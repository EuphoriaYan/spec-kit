# Team Implement: Phase 7 Pull Request

Load this file only after `speckit.team.implement` verification has passed and
Review returned `GO` or `GO-WITH-RISK`. PR submission is a transport step, not
an additional design approval.

PR failure does not invalidate the verified implementation. On any stop or
failure below, leave `work-context.yml` at `phase: verified`, do not write a
`pr_url`, and provide a manual checklist.

## Pre-submit Checks

1. Run `git status --short --branch`; determine the repository default branch
   without changing branches. Stop if the current branch is the default branch.
2. Inspect staged, unstaged, and untracked changes. Include only intended
   source, tests, and explicitly promoted durable HLD or knowledge. Exclude
   `.specify/feature/`, `.specify/bugfix/`, `.ai-local/`, scratch files,
   private drafts, and `spec.override.md`.
3. Read `FEATURE_ROOT/work-context.yml`. Require at least one work-item link in
   `coding_issue_url` or `handoff_requirement_url`. Never expose a private URL or
   private requirement detail in a public repository; use only an approved
   public-safe summary where applicable.
4. Confirm every file to be submitted is allowed by
   `FEATURE_ROOT/permission-envelope.yml`. Stop if authorization is missing or
   actual operations exceeded it.
5. Read the local `FEATURE_ROOT/evidence/implementation-report.md` and confirm it
   records passing required tests and any skipped checks.
6. Do not overwrite unrelated user changes. Do not stage or commit them.
7. Use authenticated GitHub automation when available. For GitCode or another
   host without a usable CLI/API, give the user a complete title, body, file
   list, and `## Paste Into PR Description` block. Manual posting is a transport
   step, not another approval gate.

## Pull Request Description

Prepare a concise title and a body containing:

```markdown
## Summary
- ...

## Feature
- Work ID: ...
- Work item: ...

## Tasks completed
- T001 ...

## Verification
- `command` — pass/fail
- Skipped checks and reason: ...

## Permissions and risk
- Enforcement mode: ...
- Scope deviations: none / ...
- Residual risks: ...
```

Do not include local Feature/Bugfix root paths, private requirement text, secrets, or claims
not supported by the diff and implementation report.

## Submit

1. Reuse an existing non-default feature branch. If a new branch is necessary,
   follow the repository's branch convention and obtain user confirmation
   before creating it.
2. Stage only the reviewed files. Show the exact staged set before committing.
3. Create a focused commit only when submission requires one. Follow repository
   authorship/disclosure rules, including required agent-assistance trailers.
4. Push the feature branch, then use `gh pr create` with the prepared title and
   body. Never force-push.
5. Read the created PR URL from `gh`; do not infer it.
6. Only after successful creation, minimally update the local `work-context.yml` with
   `pr_url`, `phase: pr-open`,
   `last_completed_skill: speckit.team.implement`,
   `next_skill: speckit.team.review`, and an ISO 8601 UTC `updated_at`.

## Pull Request Output

Output `## Pull Request` with the URL, title, linked work item, submitted files,
verification summary, and this next step:

```text
/speckit.team.review {pr_url} work_id={work_id}
```

Stop before submission when the branch, repository route, work-item link,
privacy boundary, permission coverage, evidence, staged file set, authentication,
or required agent disclosure is unresolved.
