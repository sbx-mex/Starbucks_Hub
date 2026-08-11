#!/usr/bin/env python3
"""Convierte Starbucks_Hub_CMS.xlsx a data/cms.json sin dependencias externas."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
SHEET_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
DATE_HEADERS = {"Fecha", "Fecha Inicio", "Fecha Fin", "Vigencia Inicio", "Vigencia Fin"}
REQUIRED_SHEETS = {
    "Informativo",
    "WFM",
    "Herramientas",
    "Links",
    "Eventos",
    "Actividades_Semanales",
    "Actividades_Diaria",
    "Duty_Roster",
    "Identidad",
}
REMOVED_TOOLS = {"Evidencia Antes / Después"}
REQUIRED_TOOLS = [
    {
        "Categoria": "Operación", "Grupo": "App", "Vista": "CN", "Icono": "📍",
        "Nombre": "CN Connect", "Tipo": "Web", "URL": "https://sbx-mx.github.io/CentroNorteConnect/",
        "Notas": "Centraliza información, comunicación y recursos del Centro Norte.", "Favorito": "No", "Orden": 17,
    },
    {
        "Categoria": "Operación", "Grupo": "App", "Vista": "General", "Icono": "🚀",
        "Nombre": "Esfuerzo Operativo", "Tipo": "Web", "URL": "https://sbx-mx.github.io/Esfuerzo_Operativo/",
        "Notas": "Consulta el avance diario, la tendencia semanal y las prioridades por región, DM y tienda.", "Favorito": "Si", "Orden": 18,
    },
]


def normalize_tools(records: list[dict]) -> list[dict]:
    """Aplica la navegación oficial de Herramientas sin mezclarla con Links."""
    current = [record for record in records if record.get("Nombre") not in REMOVED_TOOLS]
    by_name = {record.get("Nombre"): record for record in current}
    for required in REQUIRED_TOOLS:
        if required["Nombre"] in by_name:
            by_name[required["Nombre"]].update(required)
        else:
            current.append(dict(required))
    return sorted(current, key=lambda record: (float(record.get("Orden") or 999), str(record.get("Nombre") or "")))


def normalize_quick_links(records: list[dict]) -> list[dict]:
    """Publica únicamente links marcados para conservar y con URL web válida."""
    result = []
    for index, record in enumerate(records, start=1):
        decision = str(record.get("Decisión") or record.get("Decision") or "Dejar").strip().lower()
        if decision not in {"dejar", "si", "sí", "true", "1"}:
            continue
        url = str(record.get("URL") or "").strip()
        if not re.match(r"^https?://", url, flags=re.IGNORECASE):
            continue
        clean = dict(record)
        clean["URL"] = url
        clean["Orden"] = index
        result.append(clean)
    return result


def column_index(reference: str) -> int:
    match = re.match(r"([A-Z]+)", reference)
    if not match:
        return 0
    value = 0
    for character in match.group(1):
        value = value * 26 + ord(character) - 64
    return value - 1


def excel_date(value: float) -> str:
    return (datetime(1899, 12, 30) + timedelta(days=float(value))).date().isoformat()


def shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    values = []
    for item in root.findall("m:si", NS):
        values.append("".join(node.text or "" for node in item.iterfind(".//m:t", NS)))
    return values


def workbook_sheets(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        rel.attrib["Id"]: rel.attrib["Target"].lstrip("/")
        for rel in relationships.findall("r:Relationship", REL_NS)
    }
    result = []
    for sheet in workbook.findall("m:sheets/m:sheet", NS):
        target = targets[sheet.attrib[SHEET_REL]]
        if not target.startswith("xl/"):
            target = f"xl/{target}"
        result.append((sheet.attrib["name"], target))
    return result


def cell_value(cell: ET.Element, strings: list[str]):
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iterfind(".//m:t", NS))
    raw = cell.findtext("m:v", default="", namespaces=NS)
    if raw == "":
        return None
    if cell_type == "s":
        return strings[int(raw)]
    if cell_type == "b":
        return raw == "1"
    if cell_type in {"str", "e"}:
        return raw
    try:
        number = float(raw)
        return int(number) if number.is_integer() else number
    except ValueError:
        return raw


def read_rows(archive: zipfile.ZipFile, target: str, strings: list[str]) -> list[list]:
    root = ET.fromstring(archive.read(target))
    rows = []
    for row in root.findall(".//m:sheetData/m:row", NS):
        mapped = {}
        max_index = -1
        for cell in row.findall("m:c", NS):
            index = column_index(cell.attrib.get("r", "A1"))
            mapped[index] = cell_value(cell, strings)
            max_index = max(max_index, index)
        rows.append([mapped.get(index) for index in range(max_index + 1)])
    return rows


def normalize_records(rows: list[list]) -> list[dict]:
    if not rows:
        return []
    headers = [str(value).strip() if value is not None else "" for value in rows[0]]
    records = []
    for row in rows[1:]:
        record = {}
        for index, header in enumerate(headers):
            if not header:
                continue
            value = row[index] if index < len(row) else None
            if header in DATE_HEADERS and isinstance(value, (int, float)):
                value = excel_date(value)
            record[header] = value
        if any(value not in (None, "") for value in record.values()):
            records.append(record)
    return records


def build(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(source) as archive:
        strings = shared_strings(archive)
        sheets = {
            name: normalize_records(read_rows(archive, target, strings))
            for name, target in workbook_sheets(archive)
        }

    missing = sorted(REQUIRED_SHEETS - set(sheets))
    if missing:
        raise SystemExit(f"Faltan hojas requeridas: {', '.join(missing)}")
    sheets["Herramientas"] = normalize_tools(sheets["Herramientas"])
    sheets["Links"] = normalize_quick_links(sheets["Links"])

    payload = {
        "schemaVersion": 2,
        "source": source.name,
        "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "sheets": {name: sheets[name] for name in sheets},
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    cms = Path(sys.argv[1] if len(sys.argv) > 1 else "../Starbucks_Hub_CMS.xlsx")
    output = Path(sys.argv[2] if len(sys.argv) > 2 else "data/cms.json")
    build(cms.resolve(), output.resolve())
    print(f"CMS procesado: {output}")
