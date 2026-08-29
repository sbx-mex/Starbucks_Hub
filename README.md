# Starbucks Hub

PWA estática y responsive para consulta ejecutiva y operativa en GitHub Pages.

## Motor CMS

```text
Starbucks_Hub_CMS.xlsx → scripts/build_cms.py → data/cms.json → PWA
```

El CMS mantiene nueve hojas. `Herramientas` y `Links` son catálogos independientes.

Python localiza cada encabezado por su nombre dentro de las primeras 25 filas; no depende de una posición fija. Tolera filas informativas superiores, columnas reordenadas, acentos, mayúsculas, espacios laterales y columnas editoriales nuevas. Si falta o se duplica un encabezado obligatorio, la publicación se detiene antes de generar datos incompletos.

### Contrato de Links

`Links` solo utiliza:

```text
ID | Nombre | URL | Notas
```

El motor descarta columnas extra, valida URLs web, elimina URLs duplicadas, ordena A–Z por `Nombre` y normaliza IDs. Para retirar un link se elimina su fila del Excel. La interfaz no expone un directorio completo: muestra coincidencias únicamente cuando el usuario busca.

Actualización:

```bash
python scripts/build_cms.py
python tests/validate_project.py
```

## Navegación

- **Inicio**: prioridades y buscador global.
- **Resumen Ops**: WFM y operación diaria.
- **Herramientas**: catálogo operativo existente.
- **Links**: buscador discreto de accesos internos.
- **Agenda**: eventos publicados.
- **Acerca de**: información del proyecto.

Atajos: `Ctrl/Cmd + K` abre el buscador global y `/` abre el buscador de Herramientas.

## Rendimiento PWA

El Service Worker precarga solo el núcleo de la aplicación. Imágenes y recursos secundarios se almacenan en caché cuando se utilizan, reduciendo el peso de la primera instalación. `data/cms.json` usa estrategia network-first con límite de espera de 3.5 segundos y recuperación desde caché. La interfaz renderiza cada módulo cuando se abre, evitando construir Agenda, Ops y catálogos que el usuario aún no consulta.

## Mantenimiento

`.github/workflows/cleanup-obsolete.yml` valida ramas y audita semanalmente residuos seguros. `scripts/audit_obsolete.py` elimina únicamente archivos temporales, ZIP de actualización, copias de respaldo y recursos declarados como obsoletos; el modo estricto falla si alguno permanece. Los posibles huérfanos o duplicados se reportan para revisión manual.

Diseñado: Jorge Alcantar Aguiar & Enrique César Flores
