# Reparación automática de Starbucks Hub

1. Descomprima este ZIP.
2. Cargue **el contenido de la carpeta** en la raíz de `Starbucks_Hub`, conservando las carpetas `.github`, `scripts` y `tests`.
3. Confirme **Commit changes** en GitHub.
4. Abra **Actions → Auditar y limpiar obsoletos → Run workflow**.
5. El workflow reconstruye el JSON del CMS, elimina únicamente las 20 rutas autorizadas en `BORRAR_EN_GITHUB.txt` y valida nuevamente el CMS, la PWA y el rendimiento.

## Protección

- No se aceptan rutas absolutas, `..`, carpetas, enlaces simbólicos ni archivos críticos.
- El commit automático se cancela si contiene algo distinto de eliminaciones.
- Los reportes JSON quedan disponibles como artefactos de la ejecución durante 14 días.

## Resultado validado

- Restauración de los 6 archivos alterados a la versión sana `8afe10d166a3abcf3655ab76fe3dc89871aff555`.
- Eliminación simulada y comprobada: **20/20 archivos obsoletos**.
- Prueba visual y funcional: **13/13 controles aprobados**.
- CMS Excel y `data/cms.json`: sincronizados.
