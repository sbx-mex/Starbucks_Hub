# Starbucks Hub · Motor CMS

## Fuente única

`Starbucks_Hub_CMS.xlsx` es la **fuente editorial única** del Hub. No edites `data/cms.json` manualmente: el workflow lo reconstruye desde el Excel cuando detecta ajustes y solo publica el JSON si el contenido realmente cambió.

`Herramientas` también se administra únicamente desde el Excel. El generador puede ordenar registros, normalizar fechas o IDs técnicos, pero no agrega ni sustituye herramientas desde código.

### Estado de Herramientas

- Conserva los encabezados actuales de la hoja **Herramientas**; el CMS depende de ellos.
- Puedes **mover columnas**: Python identifica los encabezados por nombre y no por posición.
- Mayúsculas, acentos y espacios laterales se normalizan automáticamente. No elimines un encabezado obligatorio ni dupliques su nombre.
- Para agregar, quitar o reorganizar contenido, trabaja con la **fila completa**. La interfaz ajusta las tarjetas y los conteos sin modificar HTML.
- La columna **Inicio** decide cuáles herramientas aparecen en el menú principal:
  - `Si`: muestra la herramienta en **Inicio**.
  - `No`: la conserva únicamente en **Herramientas**.
- La columna **Orden** define la posición. Después de una baja, Python compacta la numeración; si encuentra valores vacíos o repetidos utiliza temporalmente el orden visible de las filas.
- Usa el selector `Si` / `No` incorporado en las celdas; no escribas otros valores.
- Una fila con **Nombre** y una `URL` web válida se publica como acceso disponible.
- Una fila con **Nombre** y `URL` vacía no se elimina: se muestra como **En proyecto** con su icono y notas. Al pegar posteriormente la URL, se convierte en acceso disponible sin modificar código.
- Si una URL contiene texto pero no inicia con `http://` o `https://`, se conserva para corrección y se muestra como **Vínculo pendiente**.

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
   - En `Herramientas`, elige `Inicio = Si` para publicar el acceso en la portada o `Inicio = No` para ocultarlo de la portada.
   - Ajusta `Orden` para cambiar la posición sin tocar `app.js`.
2. Guarda el archivo con ese nombre exacto en la raíz del proyecto.
3. Súbelo a `main`.
4. GitHub Actions ejecuta automáticamente:
   - `python scripts/build_cms.py Starbucks_Hub_CMS.xlsx data/cms.json`
   - `python scripts/audit_cms.py --strict` para validar encabezados, controles, altas/bajas, vínculos y navegación;
   - auditoría de residuos seguros;
   - validación del proyecto;
   - publicación de `data/cms.json` solo si el Excel produjo un cambio real.

Para validar localmente:

```bash
python scripts/build_cms.py
python tests/validate_project.py
```

## Navegación

- `Ctrl/Cmd + K`: foco en el buscador global de Inicio.
- `/`: foco en el buscador de Herramientas.
- Links: búsqueda por Nombre, Notas, dominio o URL; no muestra directorio completo.
- Humanet V7 muestra aviso de uso exclusivo en Microsoft Edge.
- WOE Web muestra aviso de VPN.
- Martes a viernes se conserva la alerta crítica WFM al abrir el sitio.

## Mantenimiento de obsoletos

El workflow `.github/workflows/cleanup-obsolete.yml` se ejecuta al cambiar el Excel CMS, manualmente y cada lunes. `scripts/audit_obsolete.py` elimina únicamente residuos definidos como seguros. Los recursos huérfanos o duplicados no se borran automáticamente: quedan registrados para revisión manual.
