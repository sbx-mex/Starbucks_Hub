# Starbucks Hub

PWA estática y responsive para consulta ejecutiva y operativa en GitHub Pages.

## Motor CMS

```text
Starbucks_Hub_CMS.xlsx → scripts/build_cms.py → data/cms.json → PWA
```

El CMS mantiene nueve hojas. `Herramientas` y `Links` son catálogos independientes.

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

El Service Worker precarga solo el núcleo de la aplicación. Imágenes y recursos secundarios se almacenan en caché cuando se utilizan, reduciendo el peso de la primera instalación. `data/cms.json` usa estrategia network-first para recibir contenido actualizado.

## Mantenimiento

`.github/workflows/cleanup-obsolete.yml` audita semanalmente residuos seguros. `scripts/audit_obsolete.py` elimina únicamente archivos temporales, copias de respaldo y recursos declarados como obsoletos; los posibles huérfanos o duplicados se reportan para revisión manual.

Diseñado: Jorge Alcantar Aguiar & Enrique César Flores
