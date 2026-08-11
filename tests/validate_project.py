#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "index.html",
    "styles.css",
    "app.js",
    "data/cms.json",
    "manifest.webmanifest",
    "sw.js",
    "scripts/audit_obsolete.py",
    ".github/workflows/cleanup-obsolete.yml",
    "assets/icons/starbucks_hub.png",
    "assets/about/Kike_pbt.jpeg",
    "assets/about/George_pbt.jpeg",
    "assets/duty-roster/lunes_food.png",
    "assets/duty-roster/lunes_showcase.png",
    "assets/duty-roster/martes_lobby.png",
    "assets/duty-roster/martes_pic.png",
    "assets/duty-roster/miercoles_boh.png",
    "assets/duty-roster/jueves_espresso.png",
    "assets/duty-roster/jueves_lobby.png",
    "assets/duty-roster/viernes_cafe_filtrado.png",
    "assets/duty-roster/sabado_cbs.png",
    "assets/duty-roster/domingo_drive_thru.png",
    "assets/duty-roster/domingo_lobby.png",
]
FORBIDDEN_VISIBLE = ["#DistritoKike", "#OrgulloCN", "Distrito Goo", "Distrito Go"]
REQUIRED_SHEETS = {
    "Informativo",
    "WFM",
    "Links",
    "Eventos",
    "Actividades_Semanales",
    "Actividades_Diaria",
    "Duty_Roster",
    "Identidad",
}


def fail(message: str) -> None:
    raise AssertionError(message)


for relative in REQUIRED:
    if not (ROOT / relative).is_file():
        fail(f"Falta archivo: {relative}")

html = (ROOT / "index.html").read_text(encoding="utf-8")
javascript = (ROOT / "app.js").read_text(encoding="utf-8")
service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
cms = json.loads((ROOT / "data/cms.json").read_text(encoding="utf-8"))

for term in FORBIDDEN_VISIBLE:
    if term.lower() in html.lower():
        fail(f"Referencia visible prohibida: {term}")

for term in ["#GreenApronService", "JUNTÉMONOS MÁS", "Recordatorio", "Resumen Ops", "Herramientas", "Herramientas para decidir y actuar", "Sugerencias y/o comentarios"]:
    if term not in html:
        fail(f"Falta contenido requerido: {term}")

for term in [
    "Vista ejecutiva",
    'data-view="informativo"',
    'data-view="wfm"',
    'data-view="semanales"',
    'data-view="diaria"',
    'data-view="duty-roster"',
    'data-view="enlaces"',
    "Vista Ops",
    "Consulta operativa",
    ">Sugerencias<",
    "home-summary",
    "home-priorities",
    "home-events",
    "executive-filters",
    "dynamic-filters",
]:
    if term in html:
        fail(f"Permanece contenido eliminado: {term}")

if "https://wa.me/message/ENKDSAHYHIGAN1" not in html:
    fail("Falta el enlace de sugerencias")

if set(cms.get("sheets", {})) != REQUIRED_SHEETS:
    fail("Las hojas del JSON no corresponden al CMS")

for event in cms["sheets"]["Eventos"]:
    for field in ("Fecha Inicio", "Fecha Fin"):
        value = event.get(field)
        if value and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            fail(f"Fecha no normalizada: {value}")

local_references = [
    *(row.get("Link /Imagen") for row in cms["sheets"]["Informativo"]),
    *(row.get("Link / Imagen") for row in cms["sheets"]["Actividades_Diaria"]),
    *(row.get("Link/Imagen") for row in cms["sheets"]["Eventos"]),
]
for reference in local_references:
    text = str(reference or "").strip()
    if text and not re.match(r"^https?://", text):
        target = ROOT / "assets" / "content" / Path(text).name
        if not target.is_file():
            fail(f"Falta recurso local del CMS: {target.name}")

for link in cms["sheets"]["Links"]:
    if not re.match(r"^https?://", str(link.get("URL", ""))):
        fail(f"URL no válida: {link.get('URL')}")

if manifest.get("start_url") != "./" or manifest.get("scope") != "./":
    fail("Manifest no preparado para subruta")

manifest_icons = [entry.get("src") for entry in manifest.get("icons", [])]
if manifest_icons != ["./assets/icons/starbucks_hub.png"]:
    fail("El Manifest no utiliza exclusivamente starbucks_hub.png")

if not all(asset in service_worker for asset in ["./index.html", "./data/cms.json", "./app.js", "./styles.css"]):
    fail("Faltan recursos esenciales en el Service Worker")

for relative in (item for item in REQUIRED if item.startswith("assets/")):
    expected = f'./{relative}'
    if expected not in service_worker:
        fail(f"Falta recurso en caché PWA: {expected}")

if "starbucks-hub-v5" not in service_worker:
    fail("No se incrementó la versión de caché")

if 'pathname.endsWith("/data/cms.json")' not in service_worker:
    fail("El CMS no utiliza actualización network-first")

if not all(fragment in javascript for fragment in ["renderOps", "renderEvents", "renderDutyForDay", "renderLinks"]):
    fail("Faltan vistas funcionales")

if any(fragment in javascript for fragment in ["renderExecutive", "renderInformativo", "renderWeekly", "renderDaily", "renderWfm", "renderDuty()"]):
    fail("Permanece lógica exclusiva de vistas o filtros eliminados")

for source in ["Informativo", "WFM", "Actividades_Semanales", "Actividades_Diaria", "Duty_Roster"]:
    if source not in javascript:
        fail(f"Resumen Ops no integra la fuente: {source}")

sidebar = re.search(r'<nav class="nav-groups">(.*?)</nav>', html, re.S)
if not sidebar:
    fail("No se encontró el menú lateral")
routes = re.findall(r'data-route-link="([^"]+)"', sidebar.group(1))
if routes != ["inicio", "recordatorio", "resumen-ops", "herramientas", "acerca"]:
    fail(f"Menú lateral inesperado: {routes}")

for name, path in [
    ("Enrique César Flores", "assets/about/Kike_pbt.jpeg"),
    ("Jorge Alcantar Aguiar", "assets/about/George_pbt.jpeg"),
]:
    if name not in html or f"./{path}" not in html:
        fail(f"Falta correspondencia de fotografía: {name}")

for tool_name in [
    "CN Connect",
    "Esfuerzo Operativo",
    "Ranking",
    "Tasa de Éxito DT",
    "Calculadora de Ritmo",
    "Transferencias",
    "Partner Hub",
    "Layout",
    "Code Brew",
    "RSA 2.0",
]:
    if tool_name not in javascript:
        fail(f"Falta herramienta principal: {tool_name}")

for feature in ["openImageModal", "closeImageModal", "sidebarCollapsed", "DUTY_IMAGES_BY_DAY"]:
    if feature not in javascript:
        fail(f"Falta función de interfaz: {feature}")

links_by_name = {row.get("Nombre"): row for row in cms["sheets"]["Links"]}
if "Evidencia Antes / Después" in links_by_name or "Evidencia Antes / Después" in html:
    fail("Permanece el acceso Evidencia Antes / Después")

required_links = {
    "CN Connect": "https://sbx-mx.github.io/CentroNorteConnect/",
    "Esfuerzo Operativo": "https://sbx-mx.github.io/Esfuerzo_Operativo/",
}
for name, url in required_links.items():
    if links_by_name.get(name, {}).get("URL") != url:
        fail(f"Enlace prioritario incorrecto: {name}")

for removed_message in ["Datos actualizados", "Prioridades de consulta para líderes DM y roles superiores."]:
    if removed_message in html or removed_message in javascript:
        fail(f"Permanece mensaje solicitado para limpieza: {removed_message}")

workflow = (ROOT / ".github/workflows/cleanup-obsolete.yml").read_text(encoding="utf-8")
obsolete_audit = (ROOT / "scripts/audit_obsolete.py").read_text(encoding="utf-8")
experience_checks = {
    "ruta rápida operativa": 'class="operational-shortcuts"' in html and html.count('class="operational-shortcuts"') == 1,
    "directorio sin filtros duplicados": html.count('data-tool-filter="favorites"') == 1,
    "búsqueda con respuesta ágil": "toolSearchTimer" in javascript and "}, 120);" in javascript,
    "historial local de herramientas": 'id="recent-section"' in html and "rememberTool" in javascript,
    "navegación anunciada": 'id="route-status"' in html and '$("#route-status").textContent' in javascript,
    "foco accesible por vista": 'heading.focus({ preventScroll: true })' in javascript,
    "título contextual": 'document.title = `${routeLabel} · Starbucks Hub`' in javascript,
    "retorno superior discreto": 'id="back-to-top"' in html and 'window.scrollY < 700' in javascript,
    "almacenamiento tolerante": "function readRecentTools" in javascript and javascript.count("catch {") >= 4,
    "limpieza automatizada segura": "audit_obsolete.py --fix" in workflow and "KNOWN_OBSOLETE" in obsolete_audit,
}
failed_experience = [name for name, passed in experience_checks.items() if not passed]
if failed_experience:
    fail(f"Mejoras de experiencia incompletas: {', '.join(failed_experience)}")

print("Validación estática aprobada")
print(f"Mejoras UX, estabilidad y accesibilidad: {sum(experience_checks.values())}/10")
print(f"Hojas CMS: {len(cms['sheets'])}")
print(f"Enlaces: {len(cms['sheets']['Links'])}")
print(f"Eventos: {len(cms['sheets']['Eventos'])}")
sys.exit(0)
