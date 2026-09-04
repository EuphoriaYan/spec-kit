#!/usr/bin/env python3
"""Normalize external quality reports into auditable AI Team evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import re
import sys
import zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from xml.etree import ElementTree

import yaml


SCHEMA = "speckit-external-quality-findings/v1"
SEVERITY_MAP = {0: "blocker", 1: "major", 2: "minor", 3: "advisory"}
STATUS_MAP = {0: "open", 1: "resolved", 2: "ignored"}
_COLUMN_ALIASES = {
    "path": ("文件名称", "file", "filename", "path"),
    "line": ("行号", "line", "line_number"),
    "rule": ("编码规则", "rule", "rule_id"),
    "description": ("问题描述", "description", "message"),
    "severity": ("问题级别", "severity", "level"),
    "status": ("问题状态", "status"),
    "snippet": ("代码示例", "snippet", "code"),
    "reviewer": ("审核人账号", "reviewer"),
    "reviewed_at": ("审核日期", "reviewed_at"),
    "reason": ("申请理由", "reason"),
    "outcome": ("审核结果", "outcome"),
    "comment": ("审核意见", "comment"),
}
_NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_REL_NS = {
    "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
    "doc": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


class FindingsImportError(RuntimeError):
    """Raised when an external findings report cannot be normalized safely."""


def _console(message: str, *, stream: Any = sys.stdout) -> None:
    logger = logging.getLogger(f"{__name__}.console.{id(stream)}")
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.info(message)


def _cell_text(cell: ElementTree.Element, shared: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//main:t", _NS))
    value = cell.find("main:v", _NS)
    if value is None or value.text is None:
        return ""
    if cell_type == "s":
        try:
            return shared[int(value.text)]
        except (IndexError, ValueError) as exc:
            raise FindingsImportError("XLSX contains an invalid shared string") from exc
    return value.text


def _column_index(reference: str) -> int:
    letters = re.match(r"[A-Za-z]+", reference)
    if letters is None:
        raise FindingsImportError(f"invalid XLSX cell reference: {reference}")
    result = 0
    for character in letters.group(0).upper():
        result = result * 26 + ord(character) - ord("A") + 1
    return result - 1


def _xlsx_rows(path: Path, sheet_name: str | None = None) -> list[dict[str, Any]]:
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise FindingsImportError(f"invalid XLSX report: {path.name}") from exc
    with archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = [
                "".join(node.text or "" for node in item.findall(".//main:t", _NS))
                for item in root.findall("main:si", _NS)
            ]
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        relationships = ElementTree.fromstring(
            archive.read("xl/_rels/workbook.xml.rels")
        )
        targets = {
            item.attrib["Id"]: item.attrib["Target"]
            for item in relationships.findall("pkg:Relationship", _REL_NS)
        }
        sheets = workbook.findall("main:sheets/main:sheet", _NS)
        selected = next(
            (item for item in sheets if item.attrib.get("name") == sheet_name),
            sheets[0] if sheets and sheet_name is None else None,
        )
        if selected is None:
            raise FindingsImportError(f"XLSX sheet was not found: {sheet_name}")
        relation_id = selected.attrib.get(f"{{{_REL_NS['doc']}}}id")
        target = targets.get(str(relation_id), "")
        target = target.lstrip("/")
        if not target.startswith("xl/"):
            target = f"xl/{target}"
        sheet = ElementTree.fromstring(archive.read(target))
        matrix: list[list[str]] = []
        for row in sheet.findall(".//main:sheetData/main:row", _NS):
            values: dict[int, str] = {}
            for cell in row.findall("main:c", _NS):
                index = _column_index(cell.attrib.get("r", ""))
                values[index] = _cell_text(cell, shared)
            if values:
                matrix.append(
                    [values.get(index, "") for index in range(max(values) + 1)]
                )
        if not matrix:
            return []
        headers = [str(value).strip() for value in matrix[0]]
        return [
            {
                header: row[index] if index < len(row) else ""
                for index, header in enumerate(headers)
                if header
            }
            for row in matrix[1:]
            if any(str(value).strip() for value in row)
        ]


def _csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _json_rows(path: Path) -> list[dict[str, Any]]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(loaded, dict):
        loaded = loaded.get("findings")
    if not isinstance(loaded, list) or not all(
        isinstance(item, dict) for item in loaded
    ):
        raise FindingsImportError("JSON report must be a list or contain findings: []")
    return [dict(item) for item in loaded]


def _find_column(row: dict[str, Any], logical_name: str) -> Any:
    aliases = _COLUMN_ALIASES[logical_name]
    for header, value in row.items():
        normalized = str(header).strip().lower()
        if any(
            normalized == alias or normalized.startswith(alias) for alias in aliases
        ):
            return value
    return None


def _integer(value: Any, label: str) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError) as exc:
        raise FindingsImportError(f"{label} must be an integer: {value!r}") from exc


def _path(value: Any) -> str:
    normalized = str(value or "").strip().replace("\\", "/")
    candidate = PurePosixPath(normalized)
    if not normalized or candidate.is_absolute() or ".." in candidate.parts:
        raise FindingsImportError(
            f"finding path must be repository-relative: {value!r}"
        )
    return candidate.as_posix()


def _rule_id(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise FindingsImportError("finding rule is required")
    return text.split(maxsplit=1)[0]


def _enum_value(value: Any, mapping: dict[int, str], label: str) -> str:
    text = str(value or "").strip().lower()
    if text in mapping.values():
        return text
    number = _integer(value, label)
    try:
        return mapping[number]
    except KeyError as exc:
        raise FindingsImportError(f"unsupported {label}: {value!r}") from exc


def _meaningful(value: Any) -> str:
    text = str(value or "").strip()
    return "" if text in {"", "--", "nan", "None"} else text


def _match_key(tool: str, finding: dict[str, Any]) -> tuple[str, str, str, str]:
    """Return a best-effort comparison key, not a persistent finding identity."""
    return (
        tool.strip().lower(),
        str(finding.get("rule_id") or "").strip(),
        str(finding.get("path") or "").strip().replace("\\", "/"),
        " ".join(str(finding.get("message") or "").split()),
    )


def _load_baseline(path: Path | None) -> Counter[tuple[str, str, str, str]] | None:
    if path is None:
        return None
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict) or loaded.get("schema") != SCHEMA:
        raise FindingsImportError(f"baseline schema must be {SCHEMA}")
    source = loaded.get("source") or {}
    if not isinstance(source, dict):
        raise FindingsImportError("baseline source must be a mapping")
    baseline_tool = str(source.get("tool") or "").strip()
    if not baseline_tool:
        raise FindingsImportError("baseline source.tool is required")
    findings = loaded.get("findings") or []
    if not isinstance(findings, list):
        raise FindingsImportError("baseline findings must be a list")
    return Counter(
        _match_key(baseline_tool, item)
        for item in findings
        if isinstance(item, dict)
    )


def normalize(
    rows: Iterable[dict[str, Any]],
    *,
    tool: str,
    source_format: str,
    report_name: str,
    report_sha256: str,
    generated_at: str,
    source_revision: str,
    baseline_counts: Counter[tuple[str, str, str, str]] | None = None,
    include_snippets: bool = False,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    remaining_baseline = baseline_counts.copy() if baseline_counts is not None else None
    for row in rows:
        path = _path(_find_column(row, "path"))
        line = _integer(_find_column(row, "line"), "line")
        rule = _rule_id(_find_column(row, "rule"))
        description = _meaningful(_find_column(row, "description"))
        finding = {
            "rule_id": rule,
            "path": path,
            "line": line,
            "severity": _enum_value(
                _find_column(row, "severity"), SEVERITY_MAP, "severity"
            ),
            "status": _enum_value(_find_column(row, "status"), STATUS_MAP, "status"),
            "message": description,
        }
        if remaining_baseline is None:
            finding["baseline_state"] = "unknown"
        else:
            key = _match_key(tool, finding)
            if remaining_baseline[key] > 0:
                finding["baseline_state"] = "matched"
                remaining_baseline[key] -= 1
            else:
                finding["baseline_state"] = "new"
        snippet = _meaningful(_find_column(row, "snippet"))
        if include_snippets and snippet:
            finding["snippet"] = snippet
        review = {
            key: _meaningful(_find_column(row, key))
            for key in ("reviewer", "reviewed_at", "reason", "outcome", "comment")
        }
        review = {key: value for key, value in review.items() if value}
        if review:
            finding["review"] = review
        findings.append(finding)
    counts = Counter(item["status"] for item in findings)
    baseline_states = Counter(item["baseline_state"] for item in findings)
    return {
        "schema": SCHEMA,
        "source": {
            "tool": tool,
            "format": source_format,
            "report": report_name,
            "report_sha256": report_sha256,
            "generated_at": generated_at,
            "source_revision": source_revision,
        },
        "summary": {
            "total": len(findings),
            "open": counts["open"],
            "resolved": counts["resolved"],
            "ignored": counts["ignored"],
            "new": baseline_states["new"],
            "matched": baseline_states["matched"],
            "unknown": baseline_states["unknown"],
        },
        "findings": findings,
    }


def import_report(
    path: Path,
    *,
    source_format: str = "auto",
    sheet_name: str | None = None,
    tool: str = "cvgs",
    tool_version: str = "",
    source_revision: str = "",
    generated_at: str = "",
    baseline_path: Path | None = None,
    include_snippets: bool = False,
) -> dict[str, Any]:
    if not path.is_file():
        raise FindingsImportError(f"report does not exist: {path}")
    resolved_format = source_format
    if resolved_format == "auto":
        resolved_format = {".xlsx": "cvgs-xlsx", ".csv": "csv", ".json": "json"}.get(
            path.suffix.lower(), ""
        )
    if resolved_format == "cvgs-xlsx":
        rows = _xlsx_rows(path, sheet_name)
    elif resolved_format == "csv":
        rows = _csv_rows(path)
    elif resolved_format == "json":
        rows = _json_rows(path)
    else:
        raise FindingsImportError(
            f"unsupported report format: {resolved_format or path.suffix}"
        )
    if not rows:
        raise FindingsImportError("external report contains no findings")
    timestamp = (
        generated_at or datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()
    )
    payload = normalize(
        rows,
        tool=tool,
        source_format=resolved_format,
        report_name=path.name,
        report_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        generated_at=timestamp,
        source_revision=source_revision,
        baseline_counts=_load_baseline(baseline_path),
        include_snippets=include_snippets,
    )
    if tool_version:
        payload["source"]["tool_version"] = tool_version
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--format", choices=("auto", "cvgs-xlsx", "csv", "json"), default="auto"
    )
    parser.add_argument("--sheet")
    parser.add_argument("--tool", default="cvgs")
    parser.add_argument("--tool-version", default="")
    parser.add_argument("--source-revision", default="")
    parser.add_argument("--generated-at", default="")
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--include-snippets", action="store_true")
    args = parser.parse_args()
    try:
        payload = import_report(
            args.input,
            source_format=args.format,
            sheet_name=args.sheet,
            tool=args.tool,
            tool_version=args.tool_version,
            source_revision=args.source_revision,
            generated_at=args.generated_at,
            baseline_path=args.baseline,
            include_snippets=args.include_snippets,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        rendered = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
        args.output.write_text(rendered, encoding="utf-8")
        _console(json.dumps(payload["summary"], ensure_ascii=False))
        return 0
    except (FindingsImportError, OSError, ValueError, yaml.YAMLError) as exc:
        _console(f"AI Team findings import failed: {exc}", stream=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
