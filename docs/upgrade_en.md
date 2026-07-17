# Version Upgrade and Project Refresh

[中文主文档](upgrade.md)

The AI Team distribution does not automatically follow upstream Spec Kit.
Treat the CLI version, Team Skills, and generated project files as separate
upgrade surfaces.

The upstream code baseline remains Spec Kit `v0.12.5`. The historical
`v0.12.5+teamwork.1` tag does not contain the current six-skill implementation,
so the current build is installed from this repository's `main` until a new
reviewed tag is published.

```bash
uv tool install specify-cli --force \
  --from git+https://github.com/EuphoriaYan/spec-kit.git@main
specify --version
```

To refresh an existing repository, first preserve local changes, then run:

```bash
specify init . --integration <codex|claude|cursor-agent|trae>
git diff
```

Review the six installed Skills, managed AI rule block, project-owned Team
configuration, `.gitignore`, and selected skill profile. A future reviewed tag
must publish migration, validation, and rollback evidence before replacing the
temporary `main` source.

