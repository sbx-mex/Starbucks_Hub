#!/usr/bin/env python3
"""Construye Starbucks Hub público sin el CMS fuente ni accesos privados."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist"
ROOT_FILES = ("index.html", "styles.css", "app.js", "sw.js", "manifest.webmanifest")
ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".woff", ".woff2"}
SENSITIVE = re.compile(
    r"(?i)(?:https?://[^\s\"']*(?:sharepoint\.com|1drv\.ms|onedrive\.live\.com)"
    r"|(?<![\w.+-])[\w.+-]+@[\w.-]+\.[a-z]{2,}(?![\w.-])"
    r"|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    r"|(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})"
)
DROP = object()


def sanitize(value: object) -> object:
    if isinstance(value, str):
        return DROP if SENSITIVE.search(value) else value
    if isinstance(value, list):
        cleaned = (sanitize(item) for item in value)
        return [item for item in cleaned if item is not DROP]
    if isinstance(value, dict):
        if any(isinstance(item, str) and SENSITIVE.search(item) for item in value.values()):
            return DROP
        result: dict[str, object] = {}
        for key, item in value.items():
            cleaned = sanitize(item)
            if cleaned is not DROP:
                result[str(key)] = cleaned
        return result
    return value


def copy_file(relative: str, temporary: Path) -> None:
    source = (ROOT / relative).resolve()
    if ROOT not in source.parents or source.is_symlink() or not source.is_file():
        raise RuntimeError(f"Fuente pública insegura o ausente: {relative}")
    target = temporary / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def build() -> None:
    temporary = Path(tempfile.mkdtemp(prefix=".public-build-", dir=ROOT))
    try:
        for relative in ROOT_FILES:
            copy_file(relative, temporary)
        for source in sorted((ROOT / "assets").rglob("*")):
            if source.is_file() and not source.is_symlink() and source.suffix.lower() in ASSET_SUFFIXES:
                copy_file(source.relative_to(ROOT).as_posix(), temporary)
        payload = json.loads((ROOT / "data/cms.json").read_text(encoding="utf-8-sig"))
        cleaned = sanitize(payload)
        if cleaned is DROP:
            cleaned = [] if isinstance(payload, list) else {}
        target = temporary / "data/cms.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (temporary / ".nojekyll").write_text("", encoding="utf-8")
        if OUTPUT.exists():
            if OUTPUT.is_symlink():
                raise RuntimeError("dist no puede ser un enlace simbólico")
            shutil.rmtree(OUTPUT)
        os.replace(temporary, OUTPUT)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


if __name__ == "__main__":
    build()
    print(f"Artefacto público creado: {sum(p.is_file() for p in OUTPUT.rglob('*'))} archivos")
