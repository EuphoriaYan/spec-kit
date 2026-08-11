# Version Upgrade and Project Refresh

[中文主文档](upgrade.md)

The AI Team distribution does not automatically follow upstream Spec Kit.
Treat the CLI version, Team Skills, and generated project files as separate
upgrade surfaces.

The upstream code baseline remains Spec Kit `v0.12.5`. The current Team lifecycle
distribution is pinned to `v0.12.5+teamwork.6`; historical `teamwork.1`
through `teamwork.4` tags remain available only for traceability.

```bash
uv tool install specify-cli --force \
  --from git+https://github.com/EuphoriaYan/spec-kit.git@v0.12.5+teamwork.6
specify --version
```

To refresh an existing repository, first preserve local changes, then run:

```bash
specify init . --integration <codex|claude|cursor-agent|trae>
git diff
```

Review the installed lifecycle Skills, managed AI rule block, project-owned Team
configuration, `.gitignore`, and selected skill profile. Each future reviewed
tag must publish migration, validation, and rollback evidence before replacing
the shared Team version.

For `teamwork.6`, merge the release PR first, create
`v0.12.5+teamwork.6` on that merge commit, and then smoke-test the command above
with all four integrations. Do not announce the command as available before the
tag exists.
