# Calidad: registros PSP, objetivos y bitácora de capturas

| Archivo | Qué es | Quién lo llena |
|---|---|---|
| `defectos-integrante-a.csv`, `defectos-integrante-b.csv` | Registro **individual** de defectos (formato del Kit TDL) | Cada integrante, solo el suyo |
| `tiempo-integrante-a.csv`, `tiempo-integrante-b.csv` | Registro **individual** de tiempo (formato del Kit TDL) | Cada integrante, solo el suyo |
| [`objetivos.md`](objetivos.md) | Tres objetivos de calidad medibles | Equipo |
| [`fiabilidad_e1.json`](fiabilidad_e1.json) | Informe de fiabilidad calculado desde la bitácora (`python -m pipeline.fiabilidad --escribir`); método y límites en [`docs/E1/fiabilidad.md`](../docs/E1/fiabilidad.md) | Automática (la regenera quien mide) |
| `bitacora_capturas.jsonl` | Una línea por ejecución de la captura (la escribe el extractor; no editar a mano). Aparece con la primera ejecución real. | Automática |
| `revision_calidad.md` | Responsable de revisión por entrega y lista de comprobación de E0 | Equipo |
| [`auditorias.md`](auditorias.md), [`lista_verificacion_auditoria.md`](lista_verificacion_auditoria.md) | Proceso y registro de la revisión cruzada; lista reutilizable | Quien audita |
| [`riesgos.md`](riesgos.md) | Riesgos pendientes (distintos de defectos) | Equipo |

**Estado de los registros (2026-11-15).** A: E0 750 min (prototipo 480 + desarrollo formal 270) + E1 **960 min** (870 del desarrollo original + 90 de las mejoras de E1) = **1,710 min** en total y **1,230 min sin el prototipo**; 28 defectos. La versión etiquetada `e1` registraba 1,380 min de E1 y 22 defectos; el historial de Git conserva ese registro. B: E0 633 min + E1 118 min en 23 intervalos con inicio y fin, y 14 defectos (no se modifican). Los tiempos de A son estimaciones retrospectivas de su dedicación personal, sin horarios inventados.

**Mejoras de E1 (desde 2026-11-13, 90 min).** Su tiempo está en `tiempo-mejoras-e1-integrante-a.csv` (mismo formato, 8 filas con `(MEJ)`), sin repetir filas del registro principal. Son estimaciones retrospectivas de la participación personal de A (instrucciones, revisión de resultados, documentación y comprobaciones; no la ejecución autónoma de herramientas). **La fecha de cada fila es la del commit de Git que respalda esa actividad, no la de una sesión de trabajo; no se conocen los horarios.** Desde ahora se registran `inicio`, `fin` e `interrupcion_min` reales.

**Compatibilidad con el formato del Kit.** Los CSV de defectos tienen exactamente las 8 columnas del Kit. Los de tiempo tienen las **6 columnas del Kit en el mismo orden** y una 7.ª, `minutos_estimados`, al final, que existe solo porque las filas retrospectivas no tienen `inicio` ni `fin` (la duración no se puede calcular); una lectura que use solo las columnas del Kit sigue funcionando. Las filas con horarios reales (desde la entrega, `tiempo-posentrega-integrante-a.csv`) dejan `minutos_estimados` vacío.
**Minutos de corrección.** Los 28 defectos de A llevan `minutos_correccion` (440 min en total), **estimaciones retrospectivas sujetas a confirmación**: cada descripción lo declara y no son mediciones (los commits dan fechas, no esfuerzo). Ese tiempo **ya está dentro** del bloque donde se corrigió y no se suma al total de desarrollo. Una celda vacía significa «no registrado».
**Totales de A:** 1,710 min = prototipo (`[PROTOTIPO]`) 480 + E0 formal 270 + E1 960 (870 + 90 de mejoras); sin prototipo, 1,230. Detalle en [`psp-e0-integrante-a-respaldo.md`](psp-e0-integrante-a-respaldo.md) y [`psp-e1-integrante-a-respaldo.md`](psp-e1-integrante-a-respaldo.md).

## Cómo registrar
1. **No renombren** los archivos `...-integrante-a.csv` / `...-integrante-b.csv`: las pruebas y los documentos dependen de esos nombres.
2. **Tiempo:** una fila por bloque de trabajo. `fecha` AAAA-MM-DD, `inicio`/`fin` HH:MM (24 h), `interrupcion_min` entero, `fase` ∈ {planeacion, diseno, codigo, revision, pruebas, documentacion, entrevista}, `actividad` texto corto, `minutos_estimados` (columna añadida a la plantilla del Kit, **al final**, igual para los dos integrantes: solo para duraciones retrospectivas sin horario; si registras `inicio` y `fin` reales, déjala vacía). Las filas retrospectivas llevan `[ESTIMADO RETROSPECTIVO]` en `actividad` y `inicio`, `fin` e `interrupcion_min` vacíos. Registrar al terminar el bloque, no de memoria al final.
3. **Defectos:** una fila por defecto encontrado. `tipo` ∈ los diez de PSP: documentacion, sintaxis, construccion, asignacion, interfaz, verificacion, datos, funcion, sistema, entorno. `fase_introducido` y `fase_eliminado` ∈ las mismas fases que arriba. `minutos_correccion` entero. `defecto_origen`: número del defecto que causó este, si aplica. `numero` consecutivo por archivo.
4. Cada registro se compromete en Git por quien lo hizo (el historial es la evidencia).

Una fila de ejemplo del Kit (`2026-11-03,16:00,17:45,…`) **no** se copia aquí para no confundirla con datos reales.

## Alcance de los registros (reglas)
- Solo actividades, tiempos y defectos **reales**, con evidencia (commit, issue, captura). Las duraciones que no se cronometraron se registran como **estimación retrospectiva** (`minutos_estimados` y la etiqueta `[ESTIMADO RETROSPECTIVO]`), sin inventar horarios de inicio ni fin.
- El trabajo del **prototipo exploratorio** (`staymetrics-prototipo`) figura en el registro de la integrante A con la etiqueta `[PROTOTIPO]`, separado del proyecto definitivo (`[DEFINITIVO]`) y nunca atribuido a otra persona.
- Cada integrante registra únicamente lo suyo; el trabajo hecho por una no se asigna a la otra.
- **Cero defectos es válido:** una actividad con tiempo y sin filas en el CSV de defectos significa que no se detectó ninguno; no se inventan defectos para llenar el registro. Si se quiere dejar constancia, usar la columna `actividad` del tiempo (p. ej. "revisión de X: 0 defectos").
- Los tiempos de revisión cruzada los registra quien revisa; las correcciones, la autora. No se duplican.

## PSP de A: métricas de E3 y confirmaciones pendientes (2026-11-14)
**Qué se puede calcular hoy (con la salvedad de que el tiempo es estimado):** tiempo por fase; defectos por fase de introducción y de eliminación; rendimiento por fase (defectos eliminados en `revision` y `pruebas`); defectos por tipo; densidad por KLOC (las líneas se obtienen de Git); tiempo medio de corrección **estimado** (440 min en 28 defectos, no medido). **Qué no se puede calcular:** exactitud de las estimaciones (nunca hubo una estimación **previa**), tiempo de corrección medido, productividad medida y rendimiento de las revisiones en defectos por hora. **Desde ahora** se registra la estimación previa de cada bloque, `inicio`/`fin`/`interrupcion_min` reales y `minutos_correccion` medido por defecto.
**Tiempo personal frente a ejecución autónoma:** los minutos son dedicación personal de A; no incluyen suites, CI ni escaneos. **Fechas:** la de cada fila de E1 es la del commit que entrega el bloque (no el día en que se trabajó). **Compatibilidad con el Kit:** ver arriba.
**Confirmación de A (2026-11-15):** 750 min de E0, 870 min del desarrollo original de E1 y 90 de las mejoras. Los minutos de corrección y la distribución interna de cada bloque siguen siendo estimaciones retrospectivas; no hay horarios exactos de las sesiones. Ninguna fila se presenta como medición.
