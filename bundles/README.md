# Bundle catalogs (AI Team distribution)

This directory defines the **distribution bundle catalog** consumed
automatically by `specify init`. The catalog and manifests are packaged under
`specify_cli/core_pack/bundles/`, so initialization is fully offline.

## Layout

| Path | Purpose |
|------|---------|
| [`catalog.json`](catalog.json) | Bundle catalog entries (`ai-team`, …) |
| [`ai-team/bundle.yml`](ai-team/bundle.yml) | Manifest: pinned extensions, preset, workflows |
| [`ai-team/README.md`](ai-team/README.md) | Bundle-specific usage |

## Consumer flow

Users install the CLI from this fork, then initialize each coding repository:

```bash
specify init . --integration cursor-agent
```

`specify init` reads `catalog.json`, resolves each entry's package-relative
`download_url`, and installs every listed bundle. Users do not register a
catalog or run `specify bundle install` separately.

## Maintainer notes

- Add every distribution bundle to `catalog.json`; init installs all entries.
- Keep each `download_url` relative to this directory, for example
  `ai-team/bundle.yml`.
- Keep catalog and manifest versions aligned.
- Set `verified: true` only after the packaged CLI and clean-project init
  install test pass for that catalog revision.
- Authoring: `specify bundle validate --path bundles/ai-team` and
  `specify bundle build --path bundles/ai-team --output dist/`.
