#!/usr/bin/env python3
"""Convierte Starbucks_Hub_CMS.xlsx a data/cms.json sin dependencias externas.

El Excel es la única fuente editorial. El generador puede normalizar formato,
fechas, orden e IDs técnicos, pero no agrega, elimina ni sustituye contenido de
Herramientas fuera de lo que exista en Starbucks_Hub_CMS.xlsx.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
SHEET_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
DATE_HEADERS = {"Fecha", "Fecha Inicio", "Fecha Fin", "Vigencia Inicio", "Vigencia Fin"}
LINK_HEADERS = ("ID", "Nombre", "URL", "Notas")
SHEET_REQUIRED_HEADERS = {
    "Informativo": ("ID", "Actividad", "Descripción", "Link /Imagen", "Frecuencia", "Prioridad", "Categoría", "Icono", "Color", "Visible"),
    "WFM": ("Regla WFM",),
    "Herramientas": ("Categoria", "Grupo", "Vista", "Icono", "Nombre", "Tipo", "URL", "Notas", "Favorito", "Orden"),
    "Links": LINK_HEADERS,
    "Eventos": ("ID", "Nombre Evento", "Descripción", "Fecha Inicio", "Fecha Fin", "Región", "Distrito", "Tienda", "Publicar", "Link/Imagen", "Imagen"),
    "Actividades_Semanales": ("ID", "Actividad", "Descripción", "Día", "Hora / Corte", "Icono", "Color", "Link"),
    "Actividades_Diaria": ("ID", "Actividad", "Descripción", "Link / Imagen", "Frecuencia", "Prioridad", "Categoría", "Icono", "Color", "Visible"),
    "Duty_Roster": ("Orden", "Día", "Estaciones", "Imágenes", "Color", "Enfoque"),
    "Identidad": ("Identificador", "Sección", "Campo", "Valor", "Color", "Estilo", "Visible", "Notas"),
}
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


def sort_text(value: object) -> str:
    text = unicodedata.normalize("NFD", str(value or "").strip().casefold())
    return "".join(character for character in text if unicodedata.category(character) != "Mn")


def normalize_tools(records: list[dict]) -> list[dict]:
    """Ordena Herramientas sin inventar ni reemplazar contenido fuera del Excel."""
    return sorted(
        records,
        key=lambda record: (
            float(record.get("Orden") or 999),
            sort_text(record.get("Nombre")),
        ),
    )


def normalize_quick_links(records: list[dict]) -> list[dict]:
    """Normaliza Links con solo cuatro campos, deduplica URL y ordena A-Z."""
    result: list[dict] = []
    seen_urls: set[str] = set()
    skipped = 0

    for record in records:
        name = str(record.get("Nombre") or "").strip()
        url = str(record.get("URL") or "").strip()
        notes = str(record.get("Notas") or "").strip() or None
        if not name or not re.match(r"^https?://", url, flags=re.IGNORECASE):
            skipped += 1
            continue
        if url in seen_urls:
            skipped += 1
            continue
        seen_urls.add(url)
        result.append({"ID": None, "Nombre": name, "URL": url, "Notas": notes})

    result.sort(key=lambda record: sort_text(record["Nombre"]))
    for index, record in enumerate(result, start=1):
        record["ID"] = index

    if skipped:
        print(
            f"Aviso Links: {skipped} fila(s) omitidas por URL duplicada/inválida o nombre vacío.",
            file=sys.stderr,
        )
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
    return [
        "".join(node.text or "" for node in item.iterfind(".//m:t", NS))
        for item in root.findall("m:si", NS)
    ]


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


def normalize_records(rows: list[list], allowed_headers: tuple[str, ...] | None = None) -> list[dict]:
    if not rows:
        return []
    headers = [str(value).strip() if value is not None else "" for value in rows[0]]
    allowed = set(allowed_headers) if allowed_headers else None
    records = []
    for row in rows[1:]:
        record = {}
        for index, header in enumerate(headers):
            if not header or (allowed is not None and header not in allowed):
                continue
            value = row[index] if index < len(row) else None
            if header in DATE_HEADERS and isinstance(value, (int, float)):
                value = excel_date(value)
            record[header] = value
        if any(value not in (None, "") for value in record.values()):
            if allowed_headers:
                record = {header: record.get(header) for header in allowed_headers}
            records.append(record)
    return records


def validate_sheet_headers(name: str, rows: list[list]) -> None:
    """Protege el contrato del CMS sin alterar sus encabezados editoriales."""
    if not rows:
        raise SystemExit(f"La hoja {name} no contiene encabezados.")
    headers = tuple(str(value).strip() if value is not None else "" for value in rows[0])
    required = SHEET_REQUIRED_HEADERS.get(name, ())
    missing = [header for header in required if header not in headers]
    if missing:
        raise SystemExit(f"La hoja {name} no conserva sus encabezados requeridos: {', '.join(missing)}")


def read_cms(source: Path) -> dict:
    with zipfile.ZipFile(source) as archive:
        strings = shared_strings(archive)
        sheets = {}
        for name, target in workbook_sheets(archive):
            rows = read_rows(archive, target, strings)
            validate_sheet_headers(name, rows)
            allowed = LINK_HEADERS if name == "Links" else None
            sheets[name] = normalize_records(rows, allowed)

    missing = sorted(REQUIRED_SHEETS - set(sheets))
    if missing:
        raise SystemExit(f"Faltan hojas requeridas: {', '.join(missing)}")

    sheets["Herramientas"] = normalize_tools(sheets["Herramientas"])
    sheets["Links"] = normalize_quick_links(sheets["Links"])
    return {
        "schemaVersion": 3,
        "source": source.name,
        "sheets": {name: sheets[name] for name in sheets},
    }


def comparable(payload: dict) -> dict:
    return {
        "schemaVersion": payload.get("schemaVersion"),
        "source": payload.get("source"),
        "sheets": payload.get("sheets"),
    }


def build(source: Path, destination: Path) -> bool:
    core = read_cms(source)
    if destination.is_file():
        try:
            existing = json.loads(destination.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}
        if comparable(existing) == core:
            return False

    payload = {
        "schemaVersion": core["schemaVersion"],
        "source": core["source"],
        "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "sheets": core["sheets"],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return True


if __name__ == "__main__":
    cms = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "Starbucks_Hub_CMS.xlsx"
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data/cms.json"
    changed = build(cms.resolve(), output.resolve())
    print(f"CMS {'actualizado' if changed else 'sin cambios'}: {output}")
