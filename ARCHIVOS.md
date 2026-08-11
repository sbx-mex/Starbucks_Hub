# Relación de archivos

## Nuevos

- `index.html`: entrada principal.
- `styles.css`: diseño corporativo y adaptativo.
- `app.js`: lógica de vistas, filtros y consumo del CMS.
- `data/cms.json`: salida procesada del Excel.
- `manifest.webmanifest`: configuración de la PWA.
- `sw.js`: caché offline con rutas relativas.
- `.nojekyll`: compatibilidad con GitHub Pages.
- `assets/icons/starbucks_hub.png`: identidad visual e ícono de la PWA.
- `assets/duty-roster/*`: once imágenes operativas organizadas de lunes a domingo.
- `assets/content/*`: únicamente recursos mencionados por el CMS.
- `scripts/build_cms.py`: pipeline local Excel → JSON; mantiene `Herramientas` y `Links` como módulos independientes.
- `Starbucks_Hub_CMS.xlsx` (fuera de la carpeta publicada): motor local de actualización; `Links` puede estar oculto y usa `Decisión` para publicar accesos.
- `tests/validate_project.py`: validación estática y de integridad.
- `README.md`: actualización y publicación.

## Adaptados

No se adaptaron archivos del proyecto original. Distrito Goo se utilizó únicamente como referencia de arquitectura, responsive, PWA y recursos señalados por el nuevo CMS.

## Eliminados

No se eliminó ningún archivo de Distrito Goo. El nuevo proyecto omite deliberadamente datos distritales, personas, celebraciones, concursos, módulos y recursos que no forman parte de `Starbucks_Hub_CMS.xlsx`.
