#!/usr/bin/env python3
"""Audita residuos del proyecto y elimina solo patrones explícitamente seguros."""

from __future__ import annotations

import argparse
import fnmatch
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
ROOT_GENERATED_PATTERNS = {
    "*.patch",
    "Starbucks_Hub*.zip",
    "links_para_depurar*.xlsx",
    "Starbucks_Hub_CMS (*).xlsx",
    "Starbucks_Hub_CMS_*backup*.xlsx",
}
TRASH_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
TRASH_SUFFIXES = {".bak", ".pyc", ".tmp", ".swp", ".orig"}
ALLOWED_DUPLICATE_GROUPS = {
    frozenset({"assets/duty-roster/lunes_food.png", "assets/duty-roster/lunes_showcase.png"}),
}
TEXT_SOURCES = {".html", ".css", ".js", ".json", ".webmanifest", ".md", ".py", ".yml", ".yaml"}


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def project_files() -> list[Path]:
    return [path for path in ROOT.rglob("*") if path.is_file() and ".git" not in path.parts]


def is_safe_generated(path: Path) -> bool:
    if path.parent != ROOT:
        return False
    return any(fnmatch.fnmatch(path.name, pattern) for pattern in ROOT_GENERATED_PATTERNS)


def removable_files() -> list[Path]:
    result = []
    for path in project_files():
        name = relative(path)
        if (
            name in KNOWN_OBSOLETE
            or path.name in TRASH_NAMES
            or path.suffix.lower() in TRASH_SUFFIXES
            or is_safe_generated(path)
        ):
            result.append(path)
    return sorted(set(result))


def referenced_assets() -> set[str]:
    references: set[str] = set()
    pattern = re.compile(r"(?:\./)?assets/[A-Za-z0-9_./%+() -]+")
    source_texts: list[str] = []
    for source in project_files():
        if source.suffix.lower() not in TEXT_SOURCES:
            continue
        text = source.read_text(encoding="utf-8", errors="ignore")
        source_texts.append(text)
        for match in pattern.findall(text):
            candidate = unquote(match).rstrip("'\"`)},;]")
            references.add(candidate.removeprefix("./"))

    # Algunas galerías construyen la ruta en tiempo de ejecución y solo guardan
    # el nombre del archivo en JavaScript. Si el basename aparece en una fuente,
    # se considera una referencia válida y no se marca como huérfano.
    combined_text = "\n".join(source_texts)
    for asset in (ROOT / "assets").rglob("*"):
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
    manifest_path = ROOT / "manifest.webmanifest"
    if not manifest_path.is_file():
        return issues
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for icon in {str(item.get("src", "")).removeprefix("./") for item in manifest.get("icons", [])}:
        if icon and not (ROOT / icon).is_file():
            issues.append(f"El manifiesto referencia un icono inexistente: {icon}")
    return issues


def write_report(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="Elimina solo residuos autorizados por la política segura")
    parser.add_argument("--report", type=Path, help="Guarda un reporte JSON de la auditoría")
    args = parser.parse_args()

    candidates = removable_files()
    removed: list[str] = []
    if args.fix:
        for path in candidates:
            removed.append(relative(path))
            path.unlink()
        for directory in sorted(ROOT.rglob("__pycache__"), reverse=True):
            if directory.is_dir() and not any(directory.iterdir()):
                directory.rmdir()

    assets = {relative(path) for path in (ROOT / "assets").rglob("*") if path.is_file()}
    orphans = sorted(assets - referenced_assets() - KNOWN_OBSOLETE)
    duplicates = [sorted(group) for group in duplicate_groups()]
    issues = validate_structure()
    payload = {
        "filesReviewed": len(project_files()),
        "safeCandidates": [relative(path) for path in candidates],
        "removed": removed,
        "manualReview": {"orphanAssets": orphans, "duplicateGroups": duplicates},
        "errors": issues,
    }
    if args.report:
        write_report(args.report, payload)

    print(f"Archivos revisados: {payload['filesReviewed']}")
    print(f"Residuos seguros detectados: {len(candidates)}")
    print(f"Residuos eliminados: {len(removed)}")
    print(f"Recursos para revisión manual: {len(orphans)}")
    print(f"Duplicados para revisión manual: {len(duplicates)}")
    for item in removed:
        print(f"ELIMINADO: {item}")
    for issue in issues:
        print(f"ERROR: {issue}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
