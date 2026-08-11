#!/usr/bin/env python3
"""Audita y limpia únicamente residuos conocidos sin tocar contenido operativo."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "index.html",
    "app.js",
    "styles.css",
    "sw.js",
    "manifest.webmanifest",
    "data/cms.json",
    "scripts/build_cms.py",
    "tests/validate_project.py",
}
KNOWN_OBSOLETE = {
    "assets/icons/icon.svg",
    "assets/icons/icon-192.png",
    "assets/icons/icon-512.png",
}
TRASH_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
TRASH_SUFFIXES = {".bak", ".pyc", ".tmp", ".swp"}
ALLOWED_DUPLICATE_GROUPS = {
    frozenset({"assets/duty-roster/lunes_food.png", "assets/duty-roster/lunes_showcase.png"}),
}
TEXT_SOURCES = {".html", ".css", ".js", ".json", ".webmanifest", ".md", ".py", ".yml", ".yaml"}


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def project_files() -> list[Path]:
    return [
        path for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    ]


def removable_files() -> list[Path]:
    result = []
    for path in project_files():
        name = relative(path)
        if name in KNOWN_OBSOLETE or path.name in TRASH_NAMES or path.suffix.lower() in TRASH_SUFFIXES:
            result.append(path)
    return sorted(result)


def referenced_assets() -> set[str]:
    references: set[str] = set()
    pattern = re.compile(r"(?:\./)?assets/[A-Za-z0-9_./%+() -]+")
    for source in project_files():
        if source.suffix.lower() not in TEXT_SOURCES:
            continue
        text = source.read_text(encoding="utf-8", errors="ignore")
        for match in pattern.findall(text):
            candidate = unquote(match).rstrip("'\"`)},;]")
            references.add(candidate.removeprefix("./"))
    cms = json.loads((ROOT / "data/cms.json").read_text(encoding="utf-8"))
    for records in cms.get("sheets", {}).values():
        for record in records:
            for value in record.values():
                text = str(value or "").strip()
                if re.search(r"\.(?:avif|gif|jpe?g|png|webp)$", text, re.I) and not re.match(r"^https?://", text):
                    references.add(f"assets/content/{Path(text).name}")
    return references


def duplicate_groups() -> list[set[str]]:
    groups: dict[str, set[str]] = {}
    for path in project_files():
        if path.stat().st_size == 0:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        groups.setdefault(digest, set()).add(relative(path))
    return [names for names in groups.values() if len(names) > 1 and frozenset(names) not in ALLOWED_DUPLICATE_GROUPS]


def validate_structure() -> list[str]:
    issues = [f"Falta archivo crítico: {name}" for name in sorted(REQUIRED) if not (ROOT / name).is_file()]
    manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
    icon_paths = {str(item.get("src", "")).removeprefix("./") for item in manifest.get("icons", [])}
    for icon in icon_paths:
        if icon and not (ROOT / icon).is_file():
            issues.append(f"El manifiesto referencia un icono inexistente: {icon}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="Elimina solo residuos permitidos por la política segura")
    args = parser.parse_args()

    candidates = removable_files()
    if args.fix:
        for path in candidates:
            path.unlink()
        for directory in sorted(ROOT.rglob("__pycache__"), reverse=True):
            if directory.is_dir() and not any(directory.iterdir()):
                directory.rmdir()

    assets = {relative(path) for path in (ROOT / "assets").rglob("*") if path.is_file()}
    orphans = sorted(assets - referenced_assets() - KNOWN_OBSOLETE)
    duplicates = duplicate_groups()
    issues = validate_structure()
    if orphans:
        issues.append("Recursos sin referencia (revisión manual): " + ", ".join(orphans))
    if duplicates:
        issues.extend("Duplicados no autorizados: " + ", ".join(sorted(group)) for group in duplicates)
    if not args.fix and candidates:
        issues.append("Residuos seguros por limpiar: " + ", ".join(relative(path) for path in candidates))

    print(f"Archivos revisados: {len(project_files())}")
    print(f"Residuos eliminados: {len(candidates) if args.fix else 0}")
    print(f"Recursos huérfanos: {len(orphans)}")
    print(f"Duplicados no autorizados: {len(duplicates)}")
    if issues:
        print("\n".join(f"ERROR: {issue}" for issue in issues))
        return 1
    print("Auditoría de obsoletos aprobada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
