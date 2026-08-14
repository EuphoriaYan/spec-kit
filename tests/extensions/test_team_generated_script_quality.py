from __future__ import annotations

import ast
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "extensions" / "team" / "scripts"


def _trees() -> list[tuple[Path, ast.AST]]:
    return [(path, ast.parse(path.read_text(encoding="utf-8"))) for path in SCRIPTS.glob("*.py")]


def test_generated_scripts_do_not_use_print_or_sys_path_insertion() -> None:
    findings: list[str] = []
    for path, tree in _trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "print":
                    findings.append(f"{path.name}:{node.lineno}: print")
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            owner = node.func.value
            if not isinstance(owner, ast.Attribute):
                continue
            if (
                isinstance(owner.value, ast.Name)
                and owner.value.id == "sys"
                and owner.attr == "path"
                and node.func.attr == "insert"
            ):
                findings.append(f"{path.name}:{node.lineno}: sys.path.insert")
    assert findings == []


def test_generated_scripts_do_not_catch_value_error_with_its_children() -> None:
    child_names = {"UnicodeError", "JSONDecodeError"}
    findings: list[str] = []
    for path, tree in _trees():
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler) or not isinstance(node.type, ast.Tuple):
                continue
            names = {
                item.id
                if isinstance(item, ast.Name)
                else item.attr
                if isinstance(item, ast.Attribute)
                else ""
                for item in node.type.elts
            }
            duplicated = sorted(names & child_names) if "ValueError" in names else []
            if duplicated:
                findings.append(
                    f"{path.name}:{node.lineno}: ValueError with {', '.join(duplicated)}"
                )
    assert findings == []
