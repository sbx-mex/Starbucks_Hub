#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "index.html", "styles.css", "app.js", "data/cms.json", "manifest.webmanifest", "sw.js",
    "scripts/build_cms.py", "scripts/audit_obsolete.py", ".github/workflows/cleanup-obsolete.yml",
    "INSTRUCCIONES_ACTUALIZACION.md", ".gitignore", "assets/icons/starbucks_hub.png",
]
REQUIRED_SHEETS = {
    "Informativo", "WFM", "Herramientas", "Links", "Eventos",
    "Actividades_Semanales", "Actividades_Diaria", "Duty_Roster", "Identidad",
}
LINK_FIELDS = ["ID", "Nombre", "URL", "Notas"]


def fail(message: str) -> None:
    raise AssertionError(message)


def sort_text(value: object) -> str:
    text = unicodedata.normalize("NFD", str(value or "").strip().casefold())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


for relative in REQUIRED:
    if not (ROOT / relative).is_file():
        fail(f"Falta archivo: {relative}")

html = (ROOT / "index.html").read_text(encoding="utf-8")
css = (ROOT / "styles.css").read_text(encoding="utf-8")
js = (ROOT / "app.js").read_text(encoding="utf-8")
sw = (ROOT / "sw.js").read_text(encoding="utf-8")
builder = (ROOT / "scripts/build_cms.py").read_text(encoding="utf-8")
audit = (ROOT / "scripts/audit_obsolete.py").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/cleanup-obsolete.yml").read_text(encoding="utf-8")
instructions = (ROOT / "INSTRUCCIONES_ACTUALIZACION.md").read_text(encoding="utf-8")
manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
cms = json.loads((ROOT / "data/cms.json").read_text(encoding="utf-8"))

if set(cms.get("sheets", {})) != REQUIRED_SHEETS:
    fail("Las hojas del JSON no corresponden al CMS")
if cms.get("schemaVersion") != 3:
    fail("El CMS no usa el esquema 3")

links = cms["sheets"]["Links"]
if not links:
    fail("Links no contiene registros")
for index, record in enumerate(links, start=1):
    if list(record.keys()) != LINK_FIELDS:
        fail(f"Links contiene columnas no permitidas: {list(record.keys())}")
    if record.get("ID") != index:
        fail("Los IDs de Links no son consecutivos")
    if str(record.get("Nombre") or "") != str(record.get("Nombre") or "").strip():
        fail(f"Nombre con espacios laterales: {record.get('Nombre')}")
    if not re.match(r"^https?://", str(record.get("URL") or "")):
        fail(f"URL inválida en Links: {record.get('URL')}")

names = [sort_text(row["Nombre"]) for row in links]
if names != sorted(names):
    fail("Links no está ordenado A-Z")
urls = [row["URL"] for row in links]
if len(urls) != len(set(urls)):
    fail("Links contiene URLs duplicadas")

for event in cms["sheets"]["Eventos"]:
    for field in ("Fecha Inicio", "Fecha Fin"):
        value = event.get(field)
        if value and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            fail(f"Fecha no normalizada: {value}")

if "LINK_HEADERS = (\"ID\", \"Nombre\", \"URL\", \"Notas\")" not in builder:
    fail("build_cms.py no declara el contrato mínimo de Links")
if "allowed_headers=LINK_HEADERS" in builder:
    pass
elif "allowed = LINK_HEADERS if name == \"Links\" else None" not in builder:
    fail("El motor no limita la lectura de columnas de Links")
if "normalize_quick_links" not in builder or "sort_text" not in builder:
    fail("El motor no normaliza y ordena Links")

sidebar = re.search(r'<nav class="nav-groups">(.*?)</nav>', html, re.S)
if not sidebar:
    fail("No se encontró el menú lateral")
routes = re.findall(r'data-route-link="([^"]+)"', sidebar.group(1))
expected_routes = ["inicio", "resumen-ops", "herramientas", "links", "recordatorio", "acerca"]
if routes != expected_routes:
    fail(f"Orden de navegación inesperado: {routes}")

if "operational-shortcuts" in html or ".operational-shortcuts" in css:
    fail("Permanece navegación redundante en Inicio")
if "quick-links-directory" in html or "Ver directorio completo" in html:
    fail("Links vuelve a exponer un directorio completo")
if 'id="clear-link-search"' not in html or 'id="link-search-help"' not in html:
    fail("Links no tiene búsqueda limpia y guiada")

home_tools_block = re.search(r"const HOME_TOOL_NAMES = \[(.*?)\];", js, re.S)
if not home_tools_block:
    fail("No se encontró HOME_TOOL_NAMES")
home_tools = re.findall(r'"([^"]+)"', home_tools_block.group(1))
if len(home_tools) != 6:
    fail(f"Inicio debe mostrar 6 accesos frecuentes, no {len(home_tools)}")

experience_checks = {
    "inicio sin navegación redundante": "operational-shortcuts" not in html,
    "orden de menú orientado a tareas": routes == expected_routes,
    "links ocultos hasta buscar": 'query.length < 2' in js and 'resultsContainer.hidden = true' in js,
    "limpiar búsqueda de links": 'id="clear-link-search"' in html and '$("#clear-link-search").addEventListener' in js,
    "índice de búsqueda cacheado": "catalog: []" in js and "state.catalog = buildCatalogIndex()" in js,
    "links usan solo nombre notas url dominio": "hostnameForUrl" in js and "record.Carpeta" not in js,
    "navegación teclado completa": '["ArrowDown", "ArrowUp", "Home", "End"]' in js,
    "alerta WFM martes a viernes": "CRITICAL_WFM_DAYS" in js and "showCriticalWfmAlert" in js,
    "guardas Edge y VPN": "isMicrosoftEdge" in js and 'normalized === "woe web"' in js,
    "render diferido de listas": "content-visibility: auto" in css,
}
failed = [name for name, passed in experience_checks.items() if not passed]
if failed:
    fail("Mejoras de navegación incompletas: " + ", ".join(failed))

if "starbucks-hub-v9" not in sw or "staleWhileRevalidate" not in sw:
    fail("Service Worker no usa la estrategia ligera v9")
for heavy in ["assets/duty-roster/lunes_food.png", "assets/about/Kike_pbt.jpeg"]:
    if heavy in sw:
        fail(f"El precache inicial sigue incluyendo recurso pesado: {heavy}")
for core in ["./index.html", "./styles.css", "./app.js", "./data/cms.json", "./assets/icons/starbucks_hub.png"]:
    if core not in sw:
        fail(f"Falta recurso núcleo en caché: {core}")

if manifest.get("start_url") != "./" or manifest.get("scope") != "./":
    fail("Manifest no preparado para subruta")

if "--report" not in audit or "ROOT_GENERATED_PATTERNS" not in audit:
    fail("La auditoría de obsoletos no genera reporte o no limita patrones")
for requirement in ["audit_obsolete.py --fix --report", "actions/upload-artifact@v4", "git add -u", "grep -Ev '^D"]:
    if requirement not in workflow:
        fail(f"Workflow de obsoletos incompleto: {requirement}")

for text in ["ID | Nombre | URL | Notas", "al menos 2 caracteres", "ordenan automáticamente **A–Z", "elimina su fila"]:
    if text not in instructions:
        fail(f"Falta instrucción CMS: {text}")

print("Validación estática aprobada")
print(f"Mejoras contundentes de exploración/navegación: {sum(experience_checks.values())}/{len(experience_checks)}")
print(f"Links CMS: {len(links)} · columnas: {', '.join(LINK_FIELDS)}")
print("Orden Links: A-Z · directorio completo oculto")
sys.exit(0)
