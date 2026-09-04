from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "extensions" / "team" / "scripts" / "import_quality_findings.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("import_quality_findings", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_inline_xlsx(path: Path, rows: list[list[object]]) -> None:
    def cell(row: int, column: int, value: object) -> str:
        letters = ""
        index = column
        while index:
            index, remainder = divmod(index - 1, 26)
            letters = chr(ord("A") + remainder) + letters
        reference = f"{letters}{row}"
        if isinstance(value, int):
            return f'<c r="{reference}"><v>{value}</v></c>'
        escaped = (
            str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        return f'<c r="{reference}" t="inlineStr"><is><t>{escaped}</t></is></c>'

    sheet_rows = "".join(
        f'<row r="{row_number}">'
        + "".join(
            cell(row_number, column, value)
            for column, value in enumerate(values, start=1)
        )
        + "</row>"
        for row_number, values in enumerate(rows, start=1)
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""",
        )
        archive.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
        )
        archive.writestr(
            "xl/workbook.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="问题清单" sheetId="1" r:id="rId1"/></sheets>
</workbook>""",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>""",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>{sheet_rows}</sheetData>
</worksheet>""",
        )


def test_imports_cvgs_xlsx_and_preserves_review_audit(tmp_path: Path) -> None:
    module = _load_module()
    report = tmp_path / "cvgs.xlsx"
    _write_inline_xlsx(
        report,
        [
            [
                "文件名称",
                "行号",
                "编码规则",
                "问题描述",
                "问题级别 (0:致命 1:严重 2：一般 3:建议)",
                "问题状态 (0:未解决 1:已解决 2：已忽略)",
                "代码示例",
                "审核人账号",
                "审核日期",
                "申请理由",
                "审核结果",
            ],
            [
                "tests/demo.py",
                12,
                "G.TES.01 production assert",
                "assert found",
                2,
                0,
                "assert token != secret",
                "--",
                "--",
                "--",
                "--",
            ],
            [
                "src/demo.py",
                8,
                "G.CTL.04 enumerate",
                "range and len",
                3,
                2,
                "for i in range(len(items))",
                "maintainer",
                "2026-09-04",
                "not applicable",
                "approved",
            ],
        ],
    )

    result = module.import_report(
        report,
        source_revision="abc123",
        generated_at="2026-09-04T12:00:00+00:00",
    )

    assert result["summary"] == {
        "total": 2,
        "open": 1,
        "resolved": 0,
        "ignored": 1,
        "new": 0,
        "matched": 0,
        "unknown": 2,
    }
    assert result["findings"][0]["severity"] == "minor"
    assert result["findings"][0]["rule_id"] == "G.TES.01"
    assert "snippet" not in result["findings"][0]
    assert result["findings"][1]["review"]["reviewer"] == "maintainer"
    assert result["source"]["source_revision"] == "abc123"
    assert len(result["source"]["report_sha256"]) == 64

    local_result = module.import_report(
        report,
        source_revision="abc123",
        generated_at="2026-09-04T12:00:00+00:00",
        include_snippets=True,
    )
    assert local_result["findings"][0]["snippet"] == "assert token != secret"


def test_best_effort_baseline_match_ignores_line_movement(tmp_path: Path) -> None:
    module = _load_module()
    common = {
        "tool": "cvgs",
        "source_format": "json",
        "report_name": "report.json",
        "report_sha256": "a" * 64,
        "generated_at": "2026-09-04T12:00:00+00:00",
        "source_revision": "abc123",
    }
    first = module.normalize(
        [
            {
                "file": "src/demo.py",
                "line": 10,
                "rule": "G.CTL.04",
                "description": "use enumerate",
                "severity": "minor",
                "status": "open",
            }
        ],
        **common,
    )
    baseline = tmp_path / "baseline.yml"
    baseline.write_text(yaml.safe_dump(first), encoding="utf-8")
    second = module.normalize(
        [
            {
                "file": "src/demo.py",
                "line": 25,
                "rule": "G.CTL.04",
                "description": "use enumerate",
                "severity": "minor",
                "status": "open",
            }
        ],
        baseline_counts=module._load_baseline(baseline),
        **common,
    )

    assert first["findings"][0]["baseline_state"] == "unknown"
    assert second["findings"][0]["baseline_state"] == "matched"
    assert "fingerprint" not in second["findings"][0]


def test_rejects_finding_path_outside_repository() -> None:
    module = _load_module()

    with pytest.raises(module.FindingsImportError, match="repository-relative"):
        module.normalize(
            [
                {
                    "file": "../outside.py",
                    "line": 1,
                    "rule": "RULE-1",
                    "description": "bad",
                    "severity": "major",
                    "status": "open",
                }
            ],
            tool="scanner",
            source_format="json",
            report_name="report.json",
            report_sha256="a" * 64,
            generated_at="2026-09-04T12:00:00+00:00",
            source_revision="abc123",
        )
