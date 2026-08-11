# Starbucks Hub · Motor CMS

## Regla obligatoria para `Links`

La hoja **Links** usa exclusivamente estas cuatro columnas, en este orden:

| ID | Nombre | URL | Notas |
|---|---|---|---|

- No agregues columnas de control, publicación, categoría, orden o decisión.
- Para retirar un acceso, elimina su fila de `Links`.
- El motor ignora cualquier columna extra si alguien la agrega por error.
- Al generar `data/cms.json`, los Links válidos se ordenan automáticamente **A–Z por Nombre** y el `ID` se normaliza de forma consecutiva.
- En la PWA el catálogo completo permanece **oculto**: el usuario ve resultados solo al escribir al menos 2 caracteres.
- `Herramientas` sigue siendo un módulo independiente y conserva su esquema actual.

## Actualizar el sitio

1. Edita `Starbucks_Hub_CMS.xlsx`.
2. Guarda el archivo con ese nombre exacto en la raíz del proyecto.
3. Ejecuta:

```bash
python scripts/build_cms.py
python tests/validate_project.py
```

4. Sube únicamente los archivos que cambiaron. El archivo que consume la PWA es `data/cms.json`.

## Navegación

- `Ctrl/Cmd + K`: foco en el buscador global de Inicio.
- `/`: foco en el buscador de Herramientas.
- Links: búsqueda por Nombre, Notas, dominio o URL; no muestra directorio completo.
- Humanet V7 muestra aviso de uso exclusivo en Microsoft Edge.
- WOE Web muestra aviso de VPN.
- Martes a viernes se conserva la alerta crítica WFM al abrir el sitio.

## Mantenimiento de obsoletos

El workflow `.github/workflows/cleanup-obsolete.yml` se ejecuta cada lunes o manualmente. Solo elimina residuos definidos como seguros por `scripts/audit_obsolete.py`, valida la PWA después de limpiar y publica únicamente eliminaciones. Los recursos huérfanos o duplicados no se borran automáticamente: quedan registrados para revisión manual.
