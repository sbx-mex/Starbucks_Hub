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
CONTROL_HEADERS = {"Inicio", "Visible", "Publicar"}
SHEET_REQUIRED_HEADERS = {
    "Informativo": ("ID", "Actividad", "Descripción", "Link /Imagen", "Frecuencia", "Prioridad", "Categoría", "Icono", "Color", "Visible"),
    "WFM": ("Regla WFM",),
    "Herramientas": ("Categoria", "Grupo", "Vista", "Icono", "Nombre", "Tipo", "URL", "Notas", "Inicio", "Orden"),
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
HEADER_SEARCH_LIMIT = 25


def sort_text(value: object) -> str:
    text = unicodedata.normalize("NFD", str(value or "").strip().casefold())
    return "".join(character for character in text if unicodedata.category(character) != "Mn")


def header_key(value: object) -> str:
    """Compara encabezados ignorando acentos, mayúsculas, espacios y separadores."""
    return re.sub(r"[^a-z0-9]+", " ", sort_text(value)).strip()


def normalize_yes_no(value: object, *, sheet: str, field: str, row: int) -> str:
    """Normaliza controles editoriales sin dejar estados ambiguos en la interfaz."""
    normalized = sort_text(value)
    if value is True or normalized in {"true", "si", "1", "yes"}:
        return "Si"
    if value in (None, "") or value is False or normalized in {"false", "no", "0"}:
        return "No"
    raise SystemExit(f"{sheet}, fila {row}: {field} solo acepta Si o No; se recibió {value!r}.")


def normalize_controls(sheets: dict[str, list[dict]]) -> None:
    """Aplica un contrato común a Inicio, Visible y Publicar en todas las hojas."""
    for sheet_name, records in sheets.items():
        for row_number, record in enumerate(records, start=2):
            for field in CONTROL_HEADERS & record.keys():
                record[field] = normalize_yes_no(
                    record.get(field), sheet=sheet_name, field=field, row=row_number
                )


def normalize_tools(records: list[dict]) -> list[dict]:
    """Ordena y compacta posiciones; si Orden es ambiguo usa el orden visual del Excel."""
    parsed: list[tuple[int, int, dict]] = []
    seen: set[int] = set()
    fallback_to_rows = False
    for row_index, record in enumerate(records, start=1):
        try:
            order = int(float(record.get("Orden")))
            if order < 1 or order in seen:
                raise ValueError
        except (TypeError, ValueError):
            fallback_to_rows = True
            order = row_index
        seen.add(order)
        parsed.append((order, row_index, record))

    if fallback_to_rows:
        print(
            "Aviso Herramientas: Orden vacío, duplicado o inválido; se usa el orden actual de las filas.",
            file=sys.stderr,
        )
        ordered = [record for _, _, record in sorted(parsed, key=lambda item: item[1])]
    else:
        ordered = [record for _, _, record in sorted(parsed, key=lambda item: (item[0], item[1]))]

    for position, record in enumerate(ordered, start=1):
        record["Orden"] = position
    return ordered


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


def validate_sheet_headers(name: str, rows: list[list]) -> list[list]:
    """Encuentra y canoniza encabezados sin depender de fila, orden o formato."""
    if not rows:
        raise SystemExit(f"La hoja {name} no contiene encabezados.")
    required = SHEET_REQUIRED_HEADERS.get(name, ())
    canonical_by_key = {header_key(header): header for header in required}
    required_keys = set(canonical_by_key)

    header_index = None
    best_keys: set[str] = set()
    for index, candidate in enumerate(rows[:HEADER_SEARCH_LIMIT]):
        candidate_keys = {header_key(value) for value in candidate if header_key(value)}
        if len(candidate_keys & required_keys) > len(best_keys & required_keys):
            best_keys = candidate_keys
        if required_keys.issubset(candidate_keys):
            header_index = index
            break
    if header_index is None:
        missing = [header for header in required if header_key(header) not in best_keys]
        raise SystemExit(
            f"La hoja {name} no conserva sus encabezados requeridos en las primeras "
            f"{min(len(rows), HEADER_SEARCH_LIMIT)} filas: {', '.join(missing)}"
        )

    headers = []
    seen: dict[str, str] = {}
    for raw in rows[header_index]:
        clean = str(raw).strip() if raw is not None else ""
        key = header_key(clean)
        canonical = canonical_by_key.get(key, clean)
        canonical_key = header_key(canonical)
        if canonical_key and canonical_key in seen:
            raise SystemExit(
                f"La hoja {name} repite el encabezado {canonical!r}: {seen[canonical_key]!r} y {clean!r}."
            )
        if canonical_key:
            seen[canonical_key] = clean
        headers.append(canonical)
    return [headers, *rows[header_index + 1:]]


def read_cms(source: Path) -> dict:
    with zipfile.ZipFile(source) as archive:
        strings = shared_strings(archive)
        sheets = {}
        for name, target in workbook_sheets(archive):
            rows = read_rows(archive, target, strings)
            rows = validate_sheet_headers(name, rows)
            allowed = LINK_HEADERS if name == "Links" else None
            sheets[name] = normalize_records(rows, allowed)

    missing = sorted(REQUIRED_SHEETS - set(sheets))
    if missing:
        raise SystemExit(f"Faltan hojas requeridas: {', '.join(missing)}")

    normalize_controls(sheets)
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
