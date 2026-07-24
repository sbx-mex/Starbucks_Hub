# Starbucks Hub

PWA estática y responsive para consulta ejecutiva y operativa. Está preparada para publicarse desde la subruta:

`https://[organizacion].github.io/Starbucks_Hub/`

## Fuente de contenido

El contenido se genera desde `Starbucks_Hub_CMS.xlsx`:

```text
Starbucks_Hub_CMS.xlsx → scripts/build_cms.py → data/cms.json → interfaz
```

Para actualizar los datos sin cambiar la estructura del proyecto:

```bash
python scripts/build_cms.py ../Starbucks_Hub_CMS.xlsx data/cms.json
```

El proceso valida las ocho hojas requeridas y conserva fechas como valores ISO `YYYY-MM-DD` para evitar interpretaciones regionales ambiguas.

## Publicación en GitHub Pages

1. Copiar el contenido de este proyecto en el repositorio `Starbucks_Hub`.
2. Conservar las rutas relativas.
3. Publicar la rama seleccionada mediante GitHub Pages.
4. Verificar que `manifest.webmanifest`, `sw.js` y `data/cms.json` respondan correctamente desde `/Starbucks_Hub/`.

No requiere backend, tokens, credenciales, CDN ni dependencias de ejecución.

## Archivos principales

- `index.html`: estructura accesible y navegación.
- `styles.css`: sistema visual corporativo y responsive.
- `app.js`: carga del CMS, filtros, vistas y navegación.
- `data/cms.json`: datos locales procesados.
- `manifest.webmanifest`: instalación PWA.
- `sw.js`: caché y funcionamiento sin conexión después de la primera carga.
- `scripts/build_cms.py`: actualización reproducible desde Excel.

## Vistas

- Inicio
- Vista ejecutiva
- Informativo
- Agenda y Eventos
- WFM
- Actividades semanales
- Actividad diaria
- Duty Roster
- Enlaces
- Acerca de

Inicio concentra ocho herramientas de mayor uso. Duty Roster organiza once imágenes de lunes a domingo y las abre en un visor interno accesible. La navegación lateral puede contraerse en escritorio y funciona como panel superpuesto en móvil.

Diseñado: Jorge Alcantar Aguiar & Enrique César Flores
