# Relación de archivos

- `index.html`: estructura accesible y navegación principal.
- `styles.css`: diseño responsive y estados de búsqueda.
- `app.js`: navegación, búsqueda indexada, alertas WFM y consumo del CMS.
- `data/cms.json`: salida generada desde el Excel.
- `manifest.webmanifest`: configuración de instalación PWA.
- `sw.js`: caché ligera; precarga solo el núcleo y carga recursos secundarios bajo demanda.
- `assets/icons/starbucks_hub.png`: icono principal.
- `assets/duty-roster/*`: imágenes operativas por día.
- `assets/content/*`: recursos referidos por el CMS.
- `scripts/build_cms.py`: pipeline Excel → JSON. En `Links` solo lee `ID`, `Nombre`, `URL`, `Notas` y ordena A–Z.
- `scripts/audit_obsolete.py`: auditoría y limpieza segura de residuos conocidos.
- `.github/workflows/cleanup-obsolete.yml`: mantenimiento semanal/manual con validación posterior.
- `tests/validate_project.py`: controles de estructura, CMS, navegación, PWA y mantenimiento.
- `Starbucks_Hub_CMS.xlsx`: motor de contenido; `Links` tiene únicamente cuatro columnas.
- `INSTRUCCIONES_ACTUALIZACION.md`: reglas operativas del CMS.
