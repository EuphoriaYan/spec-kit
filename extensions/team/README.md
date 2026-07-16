# Team Bugfix, Implement & Review

The `team` extension provides a small execution layer for bug fixes and task-ready Spec Kit features. Bugfix commands keep their assessment, fix, and verification reports under `.specify/bugfix/<bug-slug>/` and do not depend on `ai-team` artifacts.

## Commands

| Command | Purpose |
|---|---|
| `speckit.team.assess` | Assess an issue URL or bug description, merge context/impact/permission analysis, and write `.specify/bugfix/<bug-slug>/assessment.md`. |
| `speckit.team.fix` | Fix an approved assessment, verify it, write `fix.md` and `test.md`, and ask before creating a pull request. |
| `speckit.team.implement` | Load a feature, check readiness and permissions, implement its tasks, verify the result, and optionally open a pull request. |
| `speckit.team.review` | Review an existing pull request for code quality and alignment with the feature artifacts. |

Feature implementation commands use one artifact root:

```text
.specify/feature/<feature-slug>/
```

The implementation command requires `spec.md`, `plan.md`, and `tasks.md` in that directory. A `permission-envelope.yml` must authorize implementation writes. `work-context.yml`, `context-pack.md`, handoffs, and code graph data are loaded when present.

Bugfix commands use `.specify/bugfix/<bug-slug>/`. `speckit.team.assess` writes `assessment.md` and folds context, code path, impact, permission-boundary, and human revision work into that file. `speckit.team.fix` requires an approved assessment, writes `fix.md` and `test.md`, and asks before opening a pull request.

## Usage

Install the extension from a source checkout while it is under development:

```bash
specify extension add team --dev extensions/team
```

Then run it through the command syntax supported by the active integration:

```text
/speckit.team.assess https://github.com/org/repo/issues/123
/speckit.team.assess "Login returns 500 after session expiry" bug_slug=login-session-expiry
/speckit.team.fix bug_slug=login-session-expiry
/speckit.team.fix assessment=.specify/bugfix/login-session-expiry/assessment.md
/speckit.team.implement feature_slug=003-search-export
/speckit.team.implement feature_slug=003-search-export only=T001-T010
/speckit.team.implement feature_slug=003-search-export submit_pr=true
/speckit.team.review https://github.com/org/repo/pull/123
/speckit.team.review pr=123 feature_slug=003-search-export
```

Implementation is complete after the selected tasks are implemented and the
verification phase passes. Opening a pull request is optional and happens only
after explicit confirmation or `submit_pr=true`. Pull request operations and
review require GitHub CLI access; without `gh`, implementation can still finish
and the commands provide manual guidance for the GitHub-specific steps.

The commands deliberately never read or write the legacy repository-root `specs/` path. Bugfix commands also never read from or write to `.specify/ai-team/`, and they do not read `.specify/extensions/team` as project context.
