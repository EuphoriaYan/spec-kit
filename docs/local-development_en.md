# Local Development and Validation

[中文主文档](local-development.md)

This guide is for contributors maintaining AI Team Spec Kit itself.

```bash
git clone git@github.com:EuphoriaYan/spec-kit.git
cd spec-kit
git checkout -b <your-branch>
uv venv
uv pip install -e .
specify --help
```

Run directly from the current source when needed:

```bash
PYTHONPATH=src python -m specify_cli --help
```

Validate installation in a separate temporary product repository. Confirm that
the six primary Team Skills and declared advanced extension entries are
installed, resources stay self-contained, managed AI rules are idempotent,
local work roots are ignored, and project-owned rules are preserved.

```bash
PYTHONPATH=src python -m pytest -q tests/extensions
PYTHONPATH=src python -m pytest -q tests/unit/test_bundled_bundle.py
python -m ruff check src extensions tests
```

Human-facing AI Team documentation uses Chinese primary files and `_en` English
backups. AI Skills, references, scripts, and agent rules retain stable English
contracts. Keep one authoritative location for each fact and link to it from
other pages.
