# PSP de la integrante A en E1: respaldo de tiempos y defectos

Este archivo **no es el registro** (el registro son los CSV de `calidad/`): documenta cómo se construyó. Ningún tiempo de A se cronometró. Los minutos son **estimaciones retrospectivas de su dedicación personal** y **no incluyen** el tiempo de ejecución autónoma de herramientas (suites de pruebas, CI, escaneos) ni el trabajo de B. Los horarios de inicio y fin no se inventaron.

## Tiempo de E1: 870 minutos (14 h 30 min)
Confirmado por A el 2026-11-14 como estimación de su dedicación personal en varias sesiones (algunas de unas cinco horas, otras de dos o tres). **Sustituye la estimación anterior de 1,380 min (23 h), que A declaró errónea**; la versión etiquetada `e1` conserva esa cifra en su historial de Git y en sus documentos. La distribución por bloque es de A; el detalle por actividad y la fase de cada fila los asignó el asistente a partir de los archivos y commits de cada bloque, y el reparto interno de cada bloque entre sus filas es una estimación sin duración medida.
| Bloque (código en la columna `actividad`) | Min | Qué incluye y evidencia |
|---|---:|---|
| L0 · contrato de datos y planificación | 45 | Lectura del PDF, diagnóstico con datos reales y contrato 1.0.0: [`contrato_datos.md`](../docs/E1/contrato_datos.md), [`plan_trabajo.md`](../docs/E1/plan_trabajo.md) |
| L1 · pipeline, limpieza e integración | 165 | Plata, reglas y cuarentena, oro, dependencias e integración de `main`: [`pipeline/`](../pipeline/) |
| L2 · transformaciones y calidad de datos | 120 | Transformaciones sin fuga, jerarquías, discretización supervisada, faltantes, atípicos y `verificar_oro`: [`transformaciones.md`](../docs/E1/transformaciones.md), [`faltantes_y_atipicos.md`](../docs/E1/faltantes_y_atipicos.md) |
| L3 · exploración, análisis y visualizaciones | 105 | Estadísticas y gráficas del oro, tablero (commit `9489dc5`) y ruta de E2: [`exploracion.md`](../docs/E1/exploracion.md), [`ruta_experimento_e2.md`](../docs/E1/ruta_experimento_e2.md) |
| SEG · seguridad, `gitleaks` y dependencias | 60 | [`seguridad.md`](../docs/E1/seguridad.md), [`calidad/evidencia/`](evidencia/) |
| PCI · pruebas automáticas y CI | 90 | [`tests/`](../tests/), [`ci.yml`](../.github/workflows/ci.yml) |
| RES · respaldo y restauración | 30 | [`pipeline/respaldo.py`](../pipeline/respaldo.py) |
| AUD · auditorías y corrección de defectos | 120 | Auditorías 6 y 7, auditoría integral contra el PDF, correcciones: [`auditorias.md`](auditorias.md) |
| DOC · documentación, SQA y requerimientos | 90 | [`requerimientos.md`](../docs/E1/requerimientos.md), [`plan_sqa.md`](../docs/E1/plan_sqa.md), [`fiabilidad.md`](../docs/E1/fiabilidad.md) |
| REL · relatoría y revisión final | 45 | [`relatoria-E1.md`](../docs/relatoria-E1.md), [`ENTREGA.md`](../docs/E1/ENTREGA.md) |
| **Total** | **870** | 37 filas en [`tiempo-integrante-a.csv`](tiempo-integrante-a.csv) |

**Fechas.** La fecha de cada fila es el día del commit que entrega el resultado del bloque (L0: contrato `f18e93a`, 2026-11-12 23:17; el resto: 2026-11-13). **No es el día en que se trabajó:** A trabajó antes de esos commits, y los minutos de L0 a L3 no caben en secuencia entre ellos (se trabajó en paralelo con las herramientas o antes del primer commit). Por eso 825 de los 870 min aparecen en un solo día de calendario: es una limitación de la evidencia, no una afirmación de que se trabajaron 13 h 45 min ese día.
**Sin doble conteo.** Cada actividad figura en un solo bloque. El tiempo de corrección de un defecto (`minutos_correccion`) es **parte** del bloque donde se corrigió (casi siempre AUD, PCI o el bloque técnico correspondiente) y **no se suma** al total. La Auditoría 6 (PR #12) y la 7 (PR #15) están solo en AUD.
**Mejoras de E1** (intervalos, esquema DENUE, ruido, notebook, ruleset, reorganización del PSP): no están en estos 870 min. Su tiempo, cuando A lo confirme, irá en [`tiempo-mejoras-e1-integrante-a.csv`](tiempo-mejoras-e1-integrante-a.csv), sin repetir filas del principal.

## Totales de A
| Concepto | Minutos |
|---|---:|
| Prototipo exploratorio `[PROTOTIPO]` (2026-11-08, repositorio `staymetrics-prototipo`) | 480 |
| Desarrollo formal de E0 (2026-11-09) | 270 |
| **E0** | **750** |
| **E1** | **870** |
| **Acumulado general (con prototipo)** | **1,620** (27 h) |
| **Acumulado sin prototipo (E0 formal + E1)** | **1,140** (19 h) |
Para las métricas de E3, el tiempo del prototipo no debe mezclarse con el del desarrollo formal. Una prueba ([`test_calidad_plantillas.py`](../tests/test_calidad_plantillas.py)) comprueba estas sumas.

## Defectos
28 defectos en [`defectos-integrante-a.csv`](defectos-integrante-a.csv): 3 del prototipo, 8 de E0 formal y 17 de E1. Son errores que se introdujeron **y** se corrigieron, con su evidencia en la descripción. Las observaciones de una revisión sobre el trabajo de Eimy no son defectos de A y no se registran. Clasificación revisada el 2026-11-14: el #15 (importaciones sin usar, hallazgo de `ruff`) pasó de `construccion` a `sintaxis`; el #16 (un script que dejó finales de línea CRLF) pasó de `sistema` a `entorno` y su fecha a 2026-11-12, porque se corrigió antes del commit del contrato; el #28 (devcontainer) es una plantilla genérica de Codespaces agregada en `f8811ac` a nombre de A. Los defectos 23 a 28 (Auditoría 8 de B) se agregaron el 2026-11-14; su fecha de introducción y de corrección está en cada descripción.
**Minutos de corrección:** ninguno está registrado. Los commits dan fechas, no esfuerzo; vacío significa «no registrado». Están propuestos en el mensaje de trabajo de esta corrección para que A los confirme; no se convierten en mediciones.
**Defecto 22 (prueba del tablero):** el commit `9489dc5` (2026-11-13 17:08) es de Leslie Valadez; lo corrigieron `80d8b5b` y `eb8f606` de `eimymuz` (20:27 y 20:42) en el PR #15. Se registra en A porque el commit que lo introdujo figura a su nombre; Git no distingue quién redactó qué dentro de ese commit. El defecto 14 de B es otro.

## Métricas de E3: qué se puede calcular
Hoy: tiempo por fase, defectos por fase de introducción y de eliminación, rendimiento por fase (defectos eliminados en revisión y pruebas) y defectos por tipo; densidad por KLOC con las líneas de Git. **No se puede calcular:** exactitud de estimaciones (nunca hubo estimación **previa**), tiempo de corrección por defecto, productividad medida y rendimiento de revisiones en defectos por hora. **Desde ahora** se registra en cada bloque la estimación previa, `inicio`, `fin` e `interrupcion_min` reales y `minutos_correccion` por defecto.
El PSP de B no se tocó.
