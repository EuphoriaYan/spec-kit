# Version Upgrade and Project Refresh

[中文主文档](upgrade.md)

The AI Team distribution does not automatically follow upstream Spec Kit.
Treat the CLI version, Team Skills, and generated project files as separate
upgrade surfaces.

The upstream code baseline remains Spec Kit `v0.12.5`. The current six-skill
distribution is pinned to `v0.12.5+teamwork.3`; the historical
`v0.12.5+teamwork.1` and `v0.12.5+teamwork.2` tags remain available only for
traceability.

```bash
uv tool install specify-cli --force \
  --from git+https://github.com/EuphoriaYan/spec-kit.git@v0.12.5+teamwork.3
specify --version
```

To refresh an existing repository, first preserve local changes, then run:

```bash
specify init . --integration <codex|claude|cursor-agent|trae>
git diff
```

Review the six installed Skills, managed AI rule block, project-owned Team
configuration, `.gitignore`, and selected skill profile. Each future reviewed
tag must publish migration, validation, and rollback evidence before replacing
the shared Team version.

For `teamwork.3`, merge the implementation PR first, create
`v0.12.5+teamwork.3` on that merge commit, and then smoke-test the command above
with all four integrations. Do not announce the command as available before the
tag exists.
