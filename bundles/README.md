# Bundle catalogs

This directory keeps the generic Spec Kit bundle catalog format available for
teams that need to compose several independent extensions, presets, or
workflows. AI Team itself no longer needs a bundle: `specify init` installs the
single built-in `team` extension directly.

## Layout

| Path | Purpose |
|---|---|
| [`catalog.json`](catalog.json) | Optional distribution bundle entries |

## Maintainer Notes

- Add a bundle only when one product installation genuinely composes multiple
  independently useful components.
- Keep each `download_url` relative to this directory.
- Keep catalog and manifest versions aligned.
- Set `verified: true` only after packaged CLI and clean-project installation
  tests pass for that catalog revision.
