from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "extensions" / "team" / "scripts" / "resolve_project_context.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("resolve_project_context", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_manifest(project: Path, documents: list[dict[str, object]]) -> None:
    path = project / "docs" / "ai-team" / "context-map.yml"
    path.parent.mkdir(parents=True)
    path.write_text(
        yaml.safe_dump(
            {"schema": "speckit-project-context/v1", "documents": documents},
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_missing_manifest_is_non_blocking_suggestion(tmp_path: Path) -> None:
    module = _load_module()

    result, return_code = module.resolve_context(
        tmp_path, role="developer", phase="implementing"
    )

    assert return_code == 0
    assert result["status"] == "not-configured"
    assert result["missing_required"] == []
    assert result["suggestions"]


def test_missing_suggested_document_does_not_warn_or_block(tmp_path: Path) -> None:
    module = _load_module()
    _write_manifest(
        tmp_path,
        [
            {
                "id": "system-context",
                "path": "docs/architecture/L0.md",
                "requirement": "suggested",
                "roles": ["developer"],
                "phases": ["implementing"],
            }
        ],
    )

    result, return_code = module.resolve_context(
        tmp_path, role="developer", phase="implementing"
    )

    assert return_code == 0
    assert result["status"] == "ready"
    assert result["missing_required"] == []
    assert result["suggestions"] == [
        "Suggested project context is not present: docs/architecture/L0.md (system-context)."
    ]


def test_explicit_required_document_blocks_only_matching_stage(tmp_path: Path) -> None:
    module = _load_module()
    _write_manifest(
        tmp_path,
        [
            {
                "id": "release-policy",
                "path": "docs/release.md",
                "requirement": "required",
                "roles": ["reviewer"],
                "phases": ["reviewing"],
            }
        ],
    )

    blocked, blocked_code = module.resolve_context(
        tmp_path, role="reviewer", phase="reviewing"
    )
    unaffected, unaffected_code = module.resolve_context(
        tmp_path, role="developer", phase="implementing"
    )

    assert blocked_code == 2
    assert blocked["status"] == "blocked"
    assert blocked["missing_required"] == [
        {"id": "release-policy", "path": "docs/release.md"}
    ]
    assert unaffected_code == 0
    assert unaffected["status"] == "ready"


def test_role_phase_module_filter_and_order_are_deterministic(tmp_path: Path) -> None:
    module = _load_module()
    architecture = tmp_path / "docs" / "architecture"
    architecture.mkdir(parents=True)
    (architecture / "L0.md").write_text("system", encoding="utf-8")
    (architecture / "query.md").write_text("query", encoding="utf-8")
    _write_manifest(
        tmp_path,
        [
            {
                "id": "query-module",
                "path": "docs/architecture/query.md",
                "requirement": "conditional",
                "roles": ["developer"],
                "phases": ["implementing"],
                "modules": ["product-query"],
                "order": 20,
            },
            {
                "id": "system-context",
                "path": "docs/architecture/L0.md",
                "requirement": "suggested",
                "roles": ["architect", "developer", "reviewer"],
                "phases": ["implementing"],
                "modules": ["*"],
                "order": 10,
            },
        ],
    )

    result, return_code = module.resolve_context(
        tmp_path,
        role="developer",
        phase="implementing",
        modules=["product-query"],
    )

    assert return_code == 0
    assert [item["id"] for item in result["documents"]] == [
        "system-context",
        "query-module",
    ]
    assert len(result["context_digest"]) == 64


@pytest.mark.parametrize(
    "documents, message",
    [
        (
            [
                {
                    "id": "escape",
                    "path": "../outside.md",
                    "requirement": "suggested",
                }
            ],
            "must stay repository-relative",
        ),
        (
            [
                {"id": "duplicate", "path": "one.md"},
                {"id": "duplicate", "path": "two.md"},
            ],
            "duplicate project context document id",
        ),
    ],
)
def test_invalid_manifest_is_rejected(
    tmp_path: Path, documents: list[dict[str, object]], message: str
) -> None:
    module = _load_module()
    _write_manifest(tmp_path, documents)

    with pytest.raises(module.ContextResolutionError, match=message):
        module.resolve_context(tmp_path, role="developer", phase="implementing")
