# Starbucks Hub · Motor de actualización

## Estructura

- `Starbucks_Hub_CMS.xlsx`: motor local de contenido.
- `Starbucks_Hub-main/`: proyecto web que se publica en GitHub Pages.

## Qué cambió

- `Herramientas` permanece como módulo independiente y conserva su contenido.
- `Links` se integró como hoja adicional oculta dentro del CMS.
- Solo las filas de `Links` con `Decisión = Dejar` y una URL web válida llegan a `data/cms.json`.
- Inicio incorpora búsqueda inteligente sobre Herramientas + Links.
- El módulo Links mantiene el directorio oculto hasta escribir o pulsar “Ver directorio completo”.

## Actualizar el sitio desde Excel

1. Edita `Starbucks_Hub_CMS.xlsx`.
2. Si necesitas cambiar Links, muestra temporalmente la hoja `Links` en Excel.
3. Usa `Dejar`, `Eliminar` o `Revisar` en la columna `Decisión`.
4. Desde la carpeta `Starbucks_Hub-main` ejecuta:

```bash
python scripts/build_cms.py ../Starbucks_Hub_CMS.xlsx data/cms.json
python tests/validate_project.py
```

5. Publica únicamente la carpeta `Starbucks_Hub-main`. El Excel maestro se mantiene local.

## Atajos de búsqueda

- `Ctrl/Cmd + K`: buscador inteligente de Inicio.
- `/`: buscador de Herramientas existente.
