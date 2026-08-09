# Project Context Routing

Project documentation is optional by default. Team Skills must not crawl every
Markdown file or assume that a mature documentation set exists. A repository
may opt into deterministic, ordered discovery with
`docs/ai-team/context-map.yml` using schema `speckit-project-context/v1`.

Each entry declares a stable ID, repository-relative path, applicable roles and
phases, optional module selectors, order, and one requirement level:

- `required`: block only the matching role/phase when the project explicitly
  declares that this document is indispensable;
- `suggested`: include it when present and otherwise return a non-blocking
  suggestion;
- `conditional`: include it only when the requested role, phase, and module
  selectors match; absence remains a suggestion.

The installed `scripts/resolve_project_context.py` returns a small JSON result
with ordered existing documents, missing explicit requirements, suggestions,
and a content digest. A missing manifest is `not-configured`, not an error.

Typical usage:

```text
python scripts/resolve_project_context.py \
  --project-root <repo> --role developer --phase implementing \
  --module product-query
```

Read returned paths in order. Do not substitute similarly named files, preload
unselected documents, or infer missing project facts from remembered chat.
Current source, tests, accepted work artifacts, and human decisions still have
the precedence defined by the Team context bootstrap.
