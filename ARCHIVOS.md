# Relación de archivos

- `index.html`: estructura accesible y navegación principal.
- `styles.css`: diseño responsive y estados de búsqueda.
- `app.js`: navegación por vistas bajo demanda, búsqueda indexada, alertas WFM y consumo del CMS.
- `data/cms.json`: salida generada desde el Excel.
- `manifest.webmanifest`: configuración de instalación PWA.
- `sw.js`: caché ligera; precarga el núcleo y recupera el CMS desde caché si la red tarda más de 3.5 segundos.
- `assets/icons/starbucks_hub.png`: icono principal.
- `assets/duty-roster/*`: imágenes operativas por día.
- `assets/content/*`: recursos referidos por el CMS.
- `scripts/build_cms.py`: pipeline Excel → JSON; detecta encabezados por nombre, fila y orden. En `Links` solo lee `ID`, `Nombre`, `URL`, `Notas` y ordena A–Z.
- `scripts/audit_obsolete.py`: auditoría y limpieza segura de residuos conocidos.
- `.github/workflows/cleanup-obsolete.yml`: mantenimiento semanal/manual con validación posterior.
- `tests/validate_project.py`: controles de estructura, CMS, navegación, PWA y mantenimiento.
- `Starbucks_Hub_CMS.xlsx`: motor de contenido; `Links` tiene únicamente cuatro columnas.
- `INSTRUCCIONES_ACTUALIZACION.md`: reglas operativas del CMS.
