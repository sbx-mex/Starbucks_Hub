#!/usr/bin/env python3
"""Auditoría segura, rápida y reproducible de Starbucks Hub."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import struct
import time
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "index.html", "app.js", "styles.css", "sw.js", "manifest.webmanifest",
    "Starbucks_Hub_CMS.xlsx", "data/cms.json", "scripts/build_cms.py",
    "scripts/audit_cms.py", "scripts/audit_obsolete.py", "tests/validate_project.py",
}
PROTECTED = REQUIRED | {
    ".github/workflows/cleanup-obsolete.yml", ".gitignore", "README.md",
    "BORRAR_EN_GITHUB.txt",
}
KNOWN_OBSOLETE = {
    "assets/icons/icon.svg", "assets/icons/icon-192.png", "assets/icons/icon-512.png",
}
ROOT_GENERATED_PATTERNS = {
    "*.patch", "Starbucks_Hub*.zip", "links_para_depurar*.xlsx",
    "Starbucks_Hub_CMS (*).xlsx", "Starbucks_Hub_CMS_*backup*.xlsx",
}
TRASH_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
TRASH_SUFFIXES = {".bak", ".pyc", ".tmp", ".swp", ".orig"}
ALLOWED_DUPLICATE_GROUPS = {
    frozenset({"assets/duty-roster/lunes_food.png", "assets/duty-roster/lunes_showcase.png"}),
}
TEXT_SOURCES = {".html", ".css", ".js", ".json", ".webmanifest", ".md", ".py", ".yml", ".yaml"}
PERFORMANCE_BUDGETS = {
    "index.html": 200_000, "styles.css": 250_000, "app.js": 350_000,
    "data/cms.json": 1_500_000, "sw.js": 80_000,
}
CRITICAL_STARTUP = {
    "index.html", "styles.css", "app.js", "manifest.webmanifest",
    "data/cms.json", "sw.js", "assets/icons/starbucks_hub.png",
}
STARTUP_BUDGET = 500_000


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def project_files() -> list[Path]:
    return [path for path in ROOT.rglob("*") if path.is_file() and ".git" not in path.parts]


def safe_manifest_entries(manifest_path: Path) -> tuple[list[str], list[str]]:
    """Lee rutas exactas y rechaza entradas ambiguas o peligrosas."""
    errors: list[str] = []
    entries: list[str] = []
    if not manifest_path.is_file():
        return [], [f"No existe el manifiesto de limpieza: {manifest_path.name}"]
    for number, raw in enumerate(manifest_path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        value = raw.strip()
        if not value or value.startswith("#"):
            continue
        value = value.replace("\\", "/").removeprefix("./")
        candidate = Path(value)
        invalid = (
            candidate.is_absolute() or not value or value.startswith("/")
            or ".." in candidate.parts or value in PROTECTED or value.startswith(".git/")
        )
        if invalid:
            errors.append(f"Línea {number}: ruta no autorizada: {raw}")
            continue
        resolved = (ROOT / candidate).resolve()
        if ROOT not in resolved.parents:
            errors.append(f"Línea {number}: ruta fuera del repositorio: {raw}")
            continue
        if value not in entries:
            entries.append(value)
    return entries, errors


def is_safe_generated(path: Path) -> bool:
    return path.parent == ROOT and any(fnmatch.fnmatch(path.name, pattern) for pattern in ROOT_GENERATED_PATTERNS)


def removable_files(manifest_entries: list[str]) -> list[Path]:
    explicit = set(manifest_entries)
    result: list[Path] = []
    for path in project_files():
        name = relative(path)
        if name in PROTECTED:
            continue
        if (name in explicit or name in KNOWN_OBSOLETE or path.name in TRASH_NAMES
                or path.suffix.lower() in TRASH_SUFFIXES or is_safe_generated(path)):
            result.append(path)
    return sorted(set(result))


def referenced_assets(files: list[Path]) -> set[str]:
    references: set[str] = set()
    pattern = re.compile(r"(?:\./)?assets/[A-Za-z0-9_./%+() -]+")
    source_texts: list[str] = []
    for source in files:
        if source.suffix.lower() not in TEXT_SOURCES:
            continue
        text = source.read_text(encoding="utf-8", errors="ignore")
        source_texts.append(text)
        for match in pattern.findall(text):
            references.add(unquote(match).rstrip("'\"`)},;]").removeprefix("./"))
    combined_text = "\n".join(source_texts)
    assets_root = ROOT / "assets"
    if assets_root.is_dir():
        for asset in assets_root.rglob("*"):
            if asset.is_file() and asset.name in combined_text:
                references.add(relative(asset))
    cms_path = ROOT / "data/cms.json"
    if cms_path.is_file():
        cms = json.loads(cms_path.read_text(encoding="utf-8"))
        for records in cms.get("sheets", {}).values():
            for record in records:
                for value in record.values():
                    text = str(value or "").strip()
                    if re.search(r"\.(?:avif|gif|jpe?g|png|webp)$", text, re.I) and not re.match(r"^https?://", text):
                        references.add(f"assets/content/{Path(text).name}")
    return references


def duplicate_groups(files: list[Path]) -> list[set[str]]:
    groups: dict[str, set[str]] = {}
    for path in files:
        if path.stat().st_size == 0:
            continue
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        groups.setdefault(digest, set()).add(relative(path))
    return [names for names in groups.values() if len(names) > 1 and frozenset(names) not in ALLOWED_DUPLICATE_GROUPS]


def png_dimensions(path: Path) -> tuple[int, int] | None:
    """Obtiene dimensiones PNG desde IHDR sin dependencias externas."""
    try:
        with path.open("rb") as stream:
            header = stream.read(24)
        if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            return None
        return struct.unpack(">II", header[16:24])
    except OSError:
        return None


def validate_structure() -> list[str]:
    issues = [f"Falta archivo crítico: {name}" for name in sorted(REQUIRED) if not (ROOT / name).is_file()]
    for json_name in ("manifest.webmanifest", "data/cms.json"):
        path = ROOT / json_name
        if path.is_file():
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                issues.append(f"JSON inválido en {json_name}: {error}")
    manifest_path = ROOT / "manifest.webmanifest"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for icon in {str(item.get("src", "")).removeprefix("./") for item in manifest.get("icons", [])}:
                if icon and not (ROOT / icon).is_file():
                    issues.append(f"El manifiesto referencia un icono inexistente: {icon}")
            for item in manifest.get("icons", []):
                icon = str(item.get("src", "")).removeprefix("./")
                declared = str(item.get("sizes", ""))
                dimensions = png_dimensions(ROOT / icon) if icon else None
                if dimensions and declared != f"{dimensions[0]}x{dimensions[1]}":
                    issues.append(
                        f"Tamaño PWA incorrecto para {icon}: declara {declared}, mide {dimensions[0]}x{dimensions[1]}"
                    )
        except json.JSONDecodeError:
            pass
    return issues


def performance_metrics(files: list[Path]) -> tuple[dict[str, object], list[str]]:
    sizes = {relative(path): path.stat().st_size for path in files}
    metrics: dict[str, object] = {name: sizes.get(name, 0) for name in PERFORMANCE_BUDGETS}
    warnings = [
        f"Presupuesto excedido: {name} ({metrics[name]} > {limit} bytes)"
        for name, limit in PERFORMANCE_BUDGETS.items() if metrics[name] > limit
    ]
    critical_bytes = sum(sizes.get(name, 0) for name in CRITICAL_STARTUP)
    metrics["criticalStartupBytes"] = critical_bytes
    metrics["startupBudgetBytes"] = STARTUP_BUDGET
    metrics["totalProjectBytes"] = sum(sizes.values())
    metrics["largestFiles"] = [
        {"path": name, "bytes": size}
        for name, size in sorted(sizes.items(), key=lambda item: item[1], reverse=True)[:8]
    ]
    if critical_bytes > STARTUP_BUDGET:
        warnings.append(
            f"Carga inicial excedida: {critical_bytes} > {STARTUP_BUDGET} bytes"
        )
    return metrics, warnings


def write_report(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "BORRAR_EN_GITHUB.txt")
    parser.add_argument("--fix", action="store_true", help="Elimina únicamente archivos autorizados")
    parser.add_argument("--strict", action="store_true", help="Falla si aún existe una ruta del manifiesto")
    parser.add_argument("--strict-performance", action="store_true", help="Falla si se excede el presupuesto inicial")
    parser.add_argument("--report", type=Path, help="Guarda el reporte JSON")
    args = parser.parse_args()
    started = time.perf_counter()

    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    manifest_entries, manifest_errors = safe_manifest_entries(manifest_path)
    candidates = removable_files(manifest_entries)
    removed: list[str] = []
    removal_errors: list[str] = []
    if args.fix and not manifest_errors:
        for path in candidates:
            name = relative(path)
            if path.is_symlink() or not path.is_file():
                removal_errors.append(f"No se elimina una ruta no regular: {name}")
                continue
            path.unlink()
            removed.append(name)

    remaining = [name for name in manifest_entries if (ROOT / name).exists()]
    files = project_files()
    assets_root = ROOT / "assets"
    assets = {relative(path) for path in assets_root.rglob("*") if path.is_file()} if assets_root.is_dir() else set()
    orphans = sorted(assets - referenced_assets(files) - KNOWN_OBSOLETE)
    duplicates = [sorted(group) for group in duplicate_groups(files)]
    issues = manifest_errors + removal_errors + validate_structure()
    if args.strict and remaining:
        issues.append("Persisten rutas marcadas para borrar: " + ", ".join(remaining))
    metrics, performance_warnings = performance_metrics(files)
    if args.strict_performance and performance_warnings:
        issues.extend(performance_warnings)
    payload = {
        "status": "ok" if not issues else "error",
        "durationMs": round((time.perf_counter() - started) * 1000, 2),
        "filesReviewed": len(files), "manifest": manifest_path.name,
        "manifestEntries": manifest_entries,
        "safeCandidates": [relative(path) for path in candidates],
        "removed": removed, "remaining": remaining,
        "performance": metrics, "warnings": performance_warnings,
        "manualReview": {"orphanAssets": orphans, "duplicateGroups": duplicates},
        "errors": issues,
    }
    if args.report:
        write_report(args.report, payload)

    print(f"Archivos revisados: {len(files)} en {payload['durationMs']} ms")
    print(f"Rutas autorizadas: {len(manifest_entries)} · eliminadas: {len(removed)} · pendientes: {len(remaining)}")
    print(
        f"Carga inicial: {metrics['criticalStartupBytes']}/{metrics['startupBudgetBytes']} bytes · "
        f"proyecto: {metrics['totalProjectBytes']} bytes"
    )
    for item in removed:
        print(f"ELIMINADO: {item}")
    for warning in performance_warnings:
        print(f"AVISO: {warning}")
    for issue in issues:
        print(f"ERROR: {issue}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
