# Team Implement & Review

The `team` extension provides a small execution layer for task-ready Spec Kit
features. It is independent of the existing `ai-team` workflows and does not
replace their collaboration infrastructure.

## Commands

| Command | Purpose |
|---|---|
| `speckit.team.implement` | Load a feature, check readiness and permissions, implement its tasks, verify the result, and optionally open a pull request. |
| `speckit.team.review` | Review an existing pull request for code quality and alignment with the feature artifacts. |

Both commands use one artifact root:

```text
.specify/specs/<feature-slug>/
```

The implementation command requires `spec.md`, `plan.md`, and `tasks.md` in
that directory. A `permission-envelope.yml` must authorize implementation
writes. `work-context.yml`, `context-pack.md`, handoffs, and code graph data are
loaded when present.

## Usage

Install the extension from a source checkout while it is under development:

```bash
specify extension add team --dev extensions/team
```

Then run it through the command syntax supported by the active integration:

```text
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

The commands deliberately never read or write the legacy repository-root
`specs/` or `.specify/ai-team/work/` paths.
