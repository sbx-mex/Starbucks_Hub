"""Regression checks for CMS changes that previously passed unnoticed."""

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_cms import source_link_errors  # noqa: E402
from build_cms import build, normalize_tools  # noqa: E402


def links_workbook(path: Path, links: list[tuple[str, str]]) -> None:
    rows = [("ID", "Nombre", "URL", "Notas"), *[(str(i), name, url, "") for i, (name, url) in enumerate(links, 1)]]
    xml_rows = []
    for row_number, values in enumerate(rows, 1):
        cells = "".join(
            f'<c r="{chr(65 + column)}{row_number}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
            for column, value in enumerate(values)
        )
        xml_rows.append(f'<row r="{row_number}">{cells}</row>')
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Links" r:id="rId1"/></sheets></workbook>')
        archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        archive.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + "".join(xml_rows) + '</sheetData></worksheet>')


class StabilityTests(unittest.TestCase):
    def test_invalid_order_keeps_visual_excel_order(self):
        for invalid in (1.5, "nan", "inf", "", 0, 1):
            with self.subTest(invalid=invalid):
                records = [{"Nombre": "Primera", "Orden": 1}, {"Nombre": "Segunda", "Orden": invalid}]
                self.assertEqual([row["Nombre"] for row in normalize_tools(records)], ["Primera", "Segunda"])
                self.assertEqual([row["Orden"] for row in records], [1, 2])

    def test_audit_detects_links_before_generator_discards_them(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "links.xlsx"
            links_workbook(source, [("Válido", "https://example.com"), ("Sin URL", ""), ("Duplicado", "https://example.com"), ("Mal formado", "https://"), ("IPv6 inválida", "https://[abc")])
            errors = source_link_errors(source)
            self.assertEqual(len(errors), 4, errors)
            self.assertTrue(any("faltan Nombre o URL" in error for error in errors))
            self.assertTrue(any("URL duplicada" in error for error in errors))
            self.assertTrue(any("URL inválida" in error for error in errors))

    def test_failed_replace_preserves_last_good_cms(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "cms.json"
            output.write_text("última versión válida", encoding="utf-8")
            with patch("build_cms.os.replace", side_effect=OSError("fallo simulado")):
                with self.assertRaises(OSError):
                    build(ROOT / "Starbucks_Hub_CMS.xlsx", output)
            self.assertEqual(output.read_text(encoding="utf-8"), "última versión válida")
            self.assertEqual(list(Path(directory).iterdir()), [output])


if __name__ == "__main__":
    unittest.main()
