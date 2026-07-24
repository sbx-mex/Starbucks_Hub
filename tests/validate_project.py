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
    "assets/icons/starbucks_hub.png",
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

for term in ["#GreenApronService", "JUNTÉMONOS MÁS", "Vista ejecutiva", "Herramientas de mayor uso", "Sugerencias y/o comentarios"]:
    if term not in html:
        fail(f"Falta contenido requerido: {term}")

for term in [
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

for relative in REQUIRED[6:]:
    expected = f'./{relative}'
    if expected not in service_worker:
        fail(f"Falta recurso en caché PWA: {expected}")

if "starbucks-hub-v2" not in service_worker:
    fail("No se incrementó la versión de caché")

if not all(fragment in javascript for fragment in ["renderExecutive", "renderEvents", "renderWfm", "renderDuty", "renderLinks"]):
    fail("Faltan vistas funcionales")

if "renderOps" in javascript or "renderExecutiveFilters" in javascript:
    fail("Permanece lógica exclusiva de vistas o filtros eliminados")

for tool_name in [
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

print("Validación estática aprobada")
print(f"Hojas CMS: {len(cms['sheets'])}")
print(f"Enlaces: {len(cms['sheets']['Links'])}")
print(f"Eventos: {len(cms['sheets']['Eventos'])}")
sys.exit(0)
