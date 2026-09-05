#!/usr/bin/env python3
"""Bloquea archivos o valores privados dentro del artefacto público."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "dist").resolve()
FORBIDDEN = {".csv", ".tsv", ".xls", ".xlsx", ".xlsm", ".xlsb", ".pdf", ".md", ".txt", ".py", ".yml", ".yaml", ".zip", ".sql", ".db"}
TEXT = {".html", ".css", ".js", ".json", ".svg"}
ALLOWED_ROOT = {".nojekyll", "index.html", "styles.css", "app.js", "sw.js", "manifest.webmanifest"}
ALLOWED_PREFIXES = ("assets/", "data/")
FORBIDDEN_NAMES = {".env", ".gitignore", ".gitattributes"}
PATTERNS = {
    "SharePoint/OneDrive": re.compile(r"(?i)https?://[^\s\"']*(?:sharepoint\.com|1drv\.ms|onedrive\.live\.com)"),
    "correo": re.compile(r"(?i)(?<![\w.+-])[\w.+-]+@[\w.-]+\.[a-z]{2,}(?![\w.-])"),
    "clave privada": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "token": re.compile(r"(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}"),
    "secreto asignado": re.compile(r"(?i)(?:client[_-]?secret|api[_-]?key|access[_-]?token|password|passwd)\s*[:=]\s*[\"'][^\"']{6,}[\"']"),
}


def main() -> int:
    errors: list[str] = []
    if not ROOT.is_dir() or ROOT.is_symlink():
        errors.append("dist no existe o es inseguro")
    else:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() and not path.is_symlink():
                continue
            relative = path.relative_to(ROOT).as_posix()
            if path.is_symlink():
                errors.append(f"enlace simbólico: {relative}")
                continue
            if "/" not in relative and relative not in ALLOWED_ROOT:
                errors.append(f"archivo raíz no autorizado: {relative}")
            if "/" in relative and not relative.startswith(ALLOWED_PREFIXES):
                errors.append(f"carpeta no autorizada: {relative}")
            if path.name.lower() in FORBIDDEN_NAMES:
                errors.append(f"archivo privado: {relative}")
            if path.suffix.lower() in FORBIDDEN:
                errors.append(f"formato privado: {relative}")
            if path.stat().st_size > 25_000_000:
                errors.append(f"archivo demasiado grande: {relative}")
            if path.suffix.lower() in TEXT:
                content = path.read_text(encoding="utf-8")
                for label, pattern in PATTERNS.items():
                    if pattern.search(content):
                        errors.append(f"{label}: {relative}")
        for required in ("index.html", "app.js", "sw.js", "manifest.webmanifest", "data/cms.json"):
            if not (ROOT / required).is_file():
                errors.append(f"falta archivo requerido: {required}")
    if errors:
        for error in errors:
            print(f"::error title=Publicación bloqueada::{error}")
        return 1
    print("Publicación segura aprobada: 0 riesgos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
