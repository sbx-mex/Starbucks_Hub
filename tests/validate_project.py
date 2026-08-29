#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "index.html", "styles.css", "app.js", "data/cms.json", "manifest.webmanifest", "sw.js",
    "Starbucks_Hub_CMS.xlsx", "scripts/build_cms.py", "scripts/audit_obsolete.py",
    ".github/workflows/cleanup-obsolete.yml", "INSTRUCCIONES_ACTUALIZACION.md", ".gitignore",
    "BORRAR_EN_GITHUB.txt",
    "assets/icons/starbucks_hub.png",
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


def cms_core(payload: dict) -> dict:
    return {
        "schemaVersion": payload.get("schemaVersion"),
        "source": payload.get("source"),
        "sheets": payload.get("sheets"),
    }


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
if cms.get("source") != "Starbucks_Hub_CMS.xlsx":
    fail("data/cms.json no declara Starbucks_Hub_CMS.xlsx como fuente")

# Prueba fuerte: el JSON versionado debe corresponder exactamente al Excel actual,
# ignorando solo generatedAt para evitar commits semanales sin cambios reales.
with tempfile.TemporaryDirectory() as temp_dir:
    generated = Path(temp_dir) / "cms.json"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_cms.py"), str(ROOT / "Starbucks_Hub_CMS.xlsx"), str(generated)],
        check=True,
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
    )
    fresh = json.loads(generated.read_text(encoding="utf-8"))
if cms_core(fresh) != cms_core(cms):
    fail("data/cms.json está desincronizado respecto a Starbucks_Hub_CMS.xlsx")

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

project_tools = [
    record for record in cms["sheets"]["Herramientas"]
    if str(record.get("Nombre") or "").strip() and not str(record.get("URL") or "").strip()
]
if not project_tools:
    fail("La prueba CMS requiere al menos una Herramienta en proyecto sin URL")

for event in cms["sheets"]["Eventos"]:
    for field in ("Fecha Inicio", "Fecha Fin"):
        value = event.get(field)
        if value and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            fail(f"Fecha no normalizada: {value}")

if "LINK_HEADERS = (\"ID\", \"Nombre\", \"URL\", \"Notas\")" not in builder:
    fail("build_cms.py no declara el contrato mínimo de Links")
if 'allowed = LINK_HEADERS if name == "Links" else None' not in builder:
    fail("El motor no limita la lectura de columnas de Links")
if "normalize_quick_links" not in builder or "sort_text" not in builder:
    fail("El motor no normaliza y ordena Links")
if "SHEET_REQUIRED_HEADERS" not in builder or "validate_sheet_headers" not in builder:
    fail("El motor no protege los encabezados del CMS")
if "REQUIRED_TOOLS" in builder or "REMOVED_TOOLS" in builder:
    fail("Herramientas contiene overrides en código; el Excel debe ser la fuente")
if "comparable(existing) == core" not in builder:
    fail("El generador no evita reescrituras cuando el Excel no cambió")

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
    "herramientas sin URL visibles": "function toolAvailability(record)" in js and "En proyecto" in js,
    "herramientas sin URL no se eliminan": '.filter((record) => String(record.Nombre || "").trim())' in js,
    "búsqueda global conserva proyectos": 'if ((!url && !isTool)' in js and 'class="smart-result is-project"' in js,
    "links usan solo nombre notas url dominio": "hostnameForUrl" in js and "record.Carpeta" not in js,
    "navegación teclado completa": '["ArrowDown", "ArrowUp", "Home", "End"]' in js,
    "alerta WFM martes a viernes": "CRITICAL_WFM_DAYS" in js and "showCriticalWfmAlert" in js,
    "guardas Edge y VPN": "isMicrosoftEdge" in js and 'normalized === "woe web"' in js,
    "render diferido de listas": "content-visibility: auto" in css,
}
failed = [name for name, passed in experience_checks.items() if not passed]
if failed:
    fail("Mejoras de navegación incompletas: " + ", ".join(failed))

if "starbucks-hub-v11" not in sw or "staleWhileRevalidate" not in sw:
    fail("Service Worker no usa la estrategia ligera v11")
if "event.waitUntil(update)" not in sw or "navigationPreload?.enable()" not in sw:
    fail("Service Worker no mantiene la actualización en segundo plano o no usa precarga")
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
for requirement in ["--manifest", "--strict", "PROTECTED", "PERFORMANCE_BUDGETS", "path.is_symlink()"]:
    if requirement not in audit:
        fail(f"Auditoría Python incompleta: {requirement}")
for requirement in ["--strict-performance", "STARTUP_BUDGET", "criticalStartupBytes", "largestFiles"]:
    if requirement not in audit:
        fail(f"Auditoría de rendimiento incompleta: {requirement}")
for requirement in [
    "python scripts/build_cms.py Starbucks_Hub_CMS.xlsx data/cms.json",
    "data: sincronizar CMS",
    "Starbucks_Hub_CMS.xlsx",
    "--manifest BORRAR_EN_GITHUB.txt",
    "--strict",
    "--strict-performance",
    "actions/upload-artifact@v4",
    "git add data/cms.json",
    "git add -u",
]:
    if requirement not in workflow:
        fail(f"Workflow de mantenimiento incompleto: {requirement}")

cleanup_entries = {
    line.strip() for line in (ROOT / "BORRAR_EN_GITHUB.txt").read_text(encoding="utf-8-sig").splitlines()
    if line.strip() and not line.lstrip().startswith("#")
}
for obsolete in {"INSTRUCCIONES.md", "VALIDACION.txt", "VALIDACION_RESTAURACION.txt"}:
    if obsolete not in cleanup_entries:
        fail(f"El manifiesto no retira el archivo temporal: {obsolete}")

if manifest.get("icons", [{}])[0].get("sizes") != "512x512":
    fail("El icono PWA no declara el tamaño optimizado 512x512")
if (ROOT / "assets/icons/starbucks_hub.png").stat().st_size > 100_000:
    fail("El icono principal excede 100 KB")
if html.count('width="44" height="44" decoding="async"') != 2:
    fail("Los logotipos no reservan espacio para evitar saltos visuales")

for text in ["ID | Nombre | URL | Notas", "al menos 2 caracteres", "ordenan automáticamente **A–Z", "elimina su fila", "En proyecto", "Vínculo pendiente"]:
    if text not in instructions:
        fail(f"Falta instrucción CMS: {text}")

print("Validación estática aprobada")
print(f"Mejoras contundentes de exploración/navegación: {sum(experience_checks.values())}/{len(experience_checks)}")
print(f"Links CMS: {len(links)} · columnas: {', '.join(LINK_FIELDS)}")
print(f"Herramientas en proyecto: {len(project_tools)} · se mantienen visibles sin URL")
print("CMS Excel: fuente única · JSON sincronizado · commits sin ruido")
sys.exit(0)
