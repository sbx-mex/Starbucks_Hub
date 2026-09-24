#!/usr/bin/env python3
"""Auditoría editorial del CMS y de la navegación generada para Starbucks Hub."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

from build_cms import (
    LINK_HEADERS, REQUIRED_SHEETS, SHEET_REQUIRED_HEADERS, normalize_records,
    read_cms, read_rows, shared_strings, sort_text, validate_sheet_headers,
    workbook_sheets,
)

ROOT = Path(__file__).resolve().parents[1]
WEB_URL = re.compile(r"^https?://", re.IGNORECASE)


def source_link_errors(source: Path) -> list[str]:
    """Inspect the Excel rows before normalization can silently omit any link."""
    with zipfile.ZipFile(source) as archive:
        strings = shared_strings(archive)
        for name, target in workbook_sheets(archive):
            if name == "Links":
                rows = validate_sheet_headers(name, read_rows(archive, target, strings))
                records = normalize_records(rows, LINK_HEADERS)
                break
        else:
            return ["Falta la hoja Links en el Excel"]

    errors = []
    seen_urls = set()
    for index, record in enumerate(records, start=1):
        name = str(record.get("Nombre") or "").strip()
        url = str(record.get("URL") or "").strip()
        if not name or not url:
            errors.append(f"Links registro {index}: faltan Nombre o URL")
            continue
        try:
            parsed = urlsplit(url)
            valid = parsed.scheme.lower() in {"http", "https"} and bool(parsed.hostname)
        except ValueError:
            valid = False
        if not valid or any(c.isspace() for c in url):
            errors.append(f"Links registro {index}: URL inválida")
        if url in seen_urls:
            errors.append(f"Links registro {index}: URL duplicada")
        seen_urls.add(url)
    return errors


def duplicate_values(records: list[dict], field: str) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for record in records:
        value = str(record.get(field) or "").strip()
        normalized = sort_text(value)
        if not normalized:
            continue
        if normalized in seen:
            duplicates.add(value)
        seen.add(normalized)
    return sorted(duplicates, key=sort_text)


def audit(source: Path, generated: Path) -> dict:
    errors: list[str] = []
    checks: list[dict] = []
    cms = read_cms(source)
    sheets = cms["sheets"]

    missing_sheets = sorted(REQUIRED_SHEETS - set(sheets))
    checks.append({
        "name": "encabezados_y_hojas",
        "status": "ok" if not missing_sheets else "error",
        "detail": f"{len(sheets)} hojas · encabezados detectados por nombre, fila y orden",
    })
    if missing_sheets:
        errors.append("Faltan hojas: " + ", ".join(missing_sheets))

    controls = []
    for sheet_name, records in sheets.items():
        for row, record in enumerate(records, start=2):
            for field in ("Inicio", "Visible", "Publicar"):
                if field in record:
                    controls.append((sheet_name, row, field, record[field]))
                    if record[field] not in {"Si", "No"}:
                        errors.append(f"{sheet_name} fila {row}: {field}={record[field]!r}")
    checks.append({
        "name": "controles_si_no",
        "status": "ok" if not any("fila" in error for error in errors) else "error",
        "detail": f"{len(controls)} controles normalizados",
    })

    tools = sheets["Herramientas"]
    tool_duplicates = duplicate_values(tools, "Nombre")
    expected_order = list(range(1, len(tools) + 1))
    actual_order = [record.get("Orden") for record in tools]
    if tool_duplicates:
        errors.append("Herramientas duplicadas: " + ", ".join(tool_duplicates))
    if actual_order != expected_order:
        errors.append("Orden de Herramientas no es consecutivo")
    checks.append({
        "name": "altas_bajas_y_orden",
        "status": "ok" if not tool_duplicates and actual_order == expected_order else "error",
        "detail": f"{len(tools)} herramientas · orden 1–{len(tools)}",
    })

    invalid_urls = source_link_errors(source)
    for sheet_name in ("Herramientas", "Links"):
        for row, record in enumerate(sheets[sheet_name], start=2):
            value = str(record.get("URL") or "").strip()
            if value and not WEB_URL.match(value):
                invalid_urls.append(f"{sheet_name} fila {row}")
    duplicate_links = duplicate_values(sheets["Links"], "URL")
    if invalid_urls:
        errors.append("URL inválida: " + ", ".join(invalid_urls))
    if duplicate_links:
        errors.append("Links duplicados: " + ", ".join(duplicate_links))
    checks.append({
        "name": "vinculos",
        "status": "ok" if not invalid_urls and not duplicate_links else "error",
        "detail": f"{len(sheets['Links'])} links · {len(tools)} herramientas",
    })

    home_count = sum(record.get("Inicio") == "Si" for record in tools)
    published_events = sum(record.get("Publicar") == "Si" for record in sheets["Eventos"])
    if not home_count:
        errors.append("Inicio no tiene herramientas seleccionadas")
    generated_matches = False
    if generated.is_file():
        payload = json.loads(generated.read_text(encoding="utf-8"))
        generated_matches = payload.get("sheets") == sheets
    if not generated_matches:
        errors.append("data/cms.json no coincide con el Excel")
    checks.append({
        "name": "navegacion_y_sincronizacion",
        "status": "ok" if home_count and generated_matches else "error",
        "detail": f"Inicio {home_count} · Herramientas {len(tools)} · Links {len(sheets['Links'])} · Agenda {published_events}",
    })

    return {
        "status": "ok" if not errors else "error",
        "source": source.name,
        "requiredHeaders": {name: list(headers) for name, headers in SHEET_REQUIRED_HEADERS.items()},
        "checks": checks,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "Starbucks_Hub_CMS.xlsx")
    parser.add_argument("--generated", type=Path, default=ROOT / "data/cms.json")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    try:
        result = audit(args.source.resolve(), args.generated.resolve())
    except (OSError, ValueError, SystemExit, json.JSONDecodeError) as error:
        result = {"status": "error", "checks": [], "errors": [str(error)]}

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for check in result.get("checks", []):
        marker = "OK" if check["status"] == "ok" else "ERROR"
        print(f"[{marker}] {check['name']}: {check['detail']}")
    for error in result.get("errors", []):
        print(f"ERROR: {error}")
    return 1 if args.strict and result.get("status") != "ok" else 0


if __name__ == "__main__":
    raise SystemExit(main())
