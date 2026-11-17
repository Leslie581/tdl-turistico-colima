# Entrega E1 · Observatorio de Ocupación Hotelera de Colima — Manzanillo (también: TDL de Ocupación Hotelera de Colima)

Equipo: Leslie Valadez Macías (integrante A, `Leslie581`) y Eimy Melissa Urbina Meza (integrante B, `eimymuz`) · Etiqueta: `e1` (anotada sobre `134c333`, creada el 2026-11-13 a las 23:32 hora local; **no se mueve**) · Tablero: https://tdl-turistico-colima.streamlit.app (responde en público y sirve la versión integrada, véase «Tablero»)
Repositorio: https://github.com/Leslie581/tdl-turistico-colima (el nombre anterior, `observatorio-turistico-colima`, redirige) · Corte: **2026-11-14** (verificación local entre las 03:10 y las 05:00 UTC; 2026-11-13, 21:10 a 23:00, hora de la Ciudad de México) · Estado: el cierre original se fusionó en `main` por el PR #16 (`628136b`); las correcciones posteriores (`372a6ab`, `1a31012` y el commit de cierre) están en `e1/cierre-documental` y **se integraron en `main` por el PR #18 (`3c6cf42`)**

## Resumen en tres líneas
1. Los datos viajan de bronce a oro sin intervención ([`pipeline.md`](pipeline.md)): 31,147 filas de DATATUR leídas, 2 rechazadas a cuarentena con su motivo, 108 meses de oro para Manzanillo; el tablero publica el pronóstico elegido por su error en 2024 (SARIMA, RMSE 2.64 pp), que **no supera** a la referencia ingenua estacional en MAE ni en MAPE ([`pronostico.md`](pronostico.md) §4).
2. Calidad medida, no supuesta, y con resultados que **no cumplen** todos los objetivos: tasa de éxito de la captura 85.7 % (6 de 7; objetivo 95 %), bitácora de **3.83 de 7 días**, MTBF y disponibilidad solo como estimación exploratoria ([`fiabilidad.md`](fiabilidad.md)). Las desviaciones del proceso de revisión están en [`plan_sqa.md`](plan_sqa.md) §5.1. El CI de `main` está en verde.
3. Etiqueta `e1` sobre `134c333` (CI de `main` en verde, ejecución 43561778746), relatoría aprobada por la integrante B en el [PR #19](https://github.com/Leslie581/tdl-turistico-colima/pull/19) y enlace registrado en el formulario. Las limitaciones vigentes están en la última sección.

> Esta ficha enlaza evidencias que existen en el repositorio. El cumplimiento por criterio del PDF, con implementación, pruebas y limitaciones, está en [`matriz_cumplimiento.md`](matriz_cumplimiento.md).

## Lista de comprobación de entregables
**Origen:** *PDF* = lo pide el PDF oficial; *Interno* = regla del equipo; *Extra* = buena práctica adicional; *Mejora* = fortalecimiento de E1 que no está en la versión etiquetada (rama `e1/mejoras-postentrega`).
| Entregable | Origen | Evidencia | Estado |
|---|---|---|---|
| Pipeline automatizado (bronce → plata → oro) | PDF | [`pipeline/ejecutar.py`](../../pipeline/ejecutar.py), [`captura-diaria.yml`](../../.github/workflows/captura-diaria.yml), [`pipeline.md`](pipeline.md) | Cumple |
| Capas plata y oro | PDF | Oro versionado: [`data/oro/`](../../data/oro/); la plata se regenera en cada corrida (está en `.gitignore`) | Cumple |
| Puerta de calidad y cuarentena | PDF | [`pipeline/calidad/`](../../pipeline/calidad/), [`resumen de cuarentena`](../../data/cuarentena/resumen_e1-e6c9a995c9ed.json) | Cumple |
| Diccionario de datos | PDF | [`diccionario_datos.csv`](../../data/oro/diccionario_datos.csv) | Cumple |
| Laboratorio estadístico y cuatro modelos | PDF | [`laboratorio/pronosticos/`](../../laboratorio/pronosticos/README.md), [`comparacion_modelos_2024.csv`](../../laboratorio/pronosticos/resultados/comparacion_modelos_2024.csv), [`pronostico.md`](pronostico.md) | Cumple |
| Notebook reproducible | Extra / Mejora | [`notebooks/pronostico_e1.ipynb`](../../notebooks/pronostico_e1.ipynb) | Ejecutado por una prueba |
| Tablero público | PDF | https://tdl-turistico-colima.streamlit.app, [`tablero.md`](tablero.md) | Cumple (la URL sirve la versión entregada) |
| Plan SQA (IEEE 730 adaptado) | PDF | [`plan_sqa.md`](plan_sqa.md) | Cumple, con la desviación interna de §5.1 |
| Registros PSP individuales | PDF | [`tiempo-integrante-a.csv`](../../calidad/tiempo-integrante-a.csv), [`defectos-integrante-a.csv`](../../calidad/defectos-integrante-a.csv), [`tiempo-integrante-b.csv`](../../calidad/tiempo-integrante-b.csv), [`defectos-integrante-b.csv`](../../calidad/defectos-integrante-b.csv) | Parcial: tiempos estimados y sin minutos de corrección |
| Bitácora y métricas de fiabilidad | PDF | [`bitacora_capturas.jsonl`](../../calidad/bitacora_capturas.jsonl), [`fiabilidad_e1.json`](../../calidad/fiabilidad_e1.json), [`fiabilidad.md`](fiabilidad.md) | Parcial: 3.83 de 7 días |
| Seguridad y respaldo | PDF | [`seguridad.md`](seguridad.md), [`pipeline/respaldo.py`](../../pipeline/respaldo.py), [`calidad/evidencia/`](../../calidad/evidencia/) | Cumple; copia externa confirmada por A (2026-11-15) |
| Requerimientos verificables | PDF | [`requerimientos.md`](requerimientos.md) | Cumple |
| Integración continua | PDF | [`ci.yml`](../../.github/workflows/ci.yml) | Cumple; protección de `main` activa (*Extra*) |
| Relatoría (máx. 2 páginas) | PDF | [`relatoria-E1.md`](../relatoria-E1.md) | Cumple |
| Ficha `ENTREGA.md` con los tres apartados | PDF | Este documento | Cumple |
| Declaración de uso de IA | PDF | Sección «Uso de IA generativa» de este documento y de la relatoría | Cumple |
| Ruta experimental de E2 | PDF | [`ruta_experimento_e2.md`](ruta_experimento_e2.md) | Cumple (no se califica) |

## Ingeniería de Datos
| Criterio de la rúbrica E1 | Evidencia (enlace) | Estado | Nota del equipo |
|---|---|---|---|
| *Plan de recopilación* (criterio de la rúbrica de **E0**, pág. 24; la pág. 14 lo lista como parte de lo que se construye) | [`docs/fuentes/README.md`](../fuentes/README.md), [`datatur.md`](../fuentes/datatur.md), [`denue.md`](../fuentes/denue.md) | CUMPLE con una salvedad | El contenido del `robots.txt` de INEGI no está archivado; los permisos de DATATUR están separados en confirmados, restringidos y no aclarados |
| *Captura y serie histórica* (criterio de la rúbrica de **E0**; listado en la pág. 14) | [`captura-diaria.yml`](../../.github/workflows/captura-diaria.yml), [`Base70centros.csv`](../../data/bronce/datatur/Base70centros.csv) (108 meses), [`data/bronce/denue/`](../../data/bronce/denue/), [`bitacora_capturas.jsonl`](../../calidad/bitacora_capturas.jsonl) | CUMPLE | La ejecución programada (`schedule`) tiene 4 ejecuciones exitosas (10 a 13 de noviembre); GitHub las retrasa varias horas respecto al cron |
| **Valores faltantes**: mecanismo diagnosticado y tratamiento justificado | [`faltantes_y_atipicos.md`](faltantes_y_atipicos.md) §1, [`contrato_datos.md`](contrato_datos.md) §2.3, [`test_faltantes_atipicos.py`](../../tests/test_faltantes_atipicos.py) | CUMPLE con una salvedad | Manzanillo **no tiene faltantes**; Mexicali (1 celda): mecanismo **indeterminado**; El Fuerte (12 meses): no al azar, no se imputa. Simulación de 5 tratamientos con 3 mecanismos: la interpolación lineal es la mejor, pero **ninguna corrige lo no al azar** |
| **Atípicos y ruido**: método justificado y decisión por tipo | [`faltantes_y_atipicos.md`](faltantes_y_atipicos.md) §2, [`contrato_datos.md`](contrato_datos.md) §2.3 | CUMPLE | IQR 1.5 y puntaje z robusto coinciden en 2020-04 a 2020-06 (COVID: **marcar y conservar**); ocupados > disponibles van a cuarentena; ruido: conservar. Sin Isolation Forest |
| **Normalización, discretización y reducción**, con análisis comparativo | [`transformaciones.md`](transformaciones.md) §2 a §8; min-max frente a z-score: [`pronostico.md`](pronostico.md) §2.7; discretización por ancho, frecuencia y **supervisada**: [`comparacion_metodos.csv`](../../laboratorio/exploracion/resultados/discretizacion_supervisada/comparacion_metodos.csv); jerarquías: [`pipeline.md`](pipeline.md) §3.1 | CUMPLE con salvedades | Las tres aplicadas con parámetros solo del entrenamiento; reducción −75.0 % (y −99.65 %) que el pipeline imprime. La supervisada separa mejor la temporada alta en el ajuste (p = 1/501 ≈ 0.002: límite de resolución de 500 permutaciones, 0 excedencias) pero **no generaliza a 2024** (12 meses); sin ganador estable entre min-max y z-score |
| **Integración de fuentes**: conflictos resueltos, sin duplicados | [`contrato_datos.md`](contrato_datos.md) §5, [`pipeline.md`](pipeline.md) §3.1 y §5, [`dim_geografia.csv`](../../data/oro/dim_geografia.csv), [`dim_tiempo.csv`](../../data/oro/dim_tiempo.csv), [`test_pipeline_jerarquias.py`](../../tests/test_pipeline_jerarquias.py) | CUMPLE con una salvedad | Modelo de datos con dimensiones comunes y claves foráneas comprobadas en cada corrida; nombres, fechas, unidades y duplicados resueltos. **No hay unión mes a mes** porque las fuentes no se solapan en el tiempo (2016–2024 frente a 2026) |
| **Puerta de calidad**: validación automática, cuarentena y motivo | [`pipeline/calidad/`](../../pipeline/calidad/), [`contrato_datos.md`](contrato_datos.md) §3, [`resumen de cuarentena`](../../data/cuarentena/resumen_e1-e6c9a995c9ed.json), [`pipeline.md`](pipeline.md) §4 | CUMPLE | `pandera` + reglas R-D01 a R-E06; 2 filas rechazadas con regla y motivo; nada se borra en silencio |
| Capas plata y oro automáticas con diccionario | [`diccionario_datos.csv`](../../data/oro/diccionario_datos.csv) (45 entradas), [`pipeline.md`](pipeline.md) §1 y §4, `pipeline.verificar_oro` | CUMPLE | El oro regenerado coincide con el versionado (comprobación en `ci.yml`); las jerarquías se regeneran en cada corrida |

## Análisis Estadístico para Ciencia de Datos
| Criterio de la rúbrica E1 | Evidencia (enlace) | Estado | Nota del equipo |
|---|---|---|---|
| **Caracterización y descomposición** | [`exploracion.md`](exploracion.md), [`pronostico.md`](pronostico.md) §2.1, §2.2 y §2.6 | CUMPLE | Aditiva, con criterio explícito (errores equivalentes; correlación amplitud–nivel −0.47). La evidencia a favor de aditiva es **débil** (6 años, dominada por 2020) |
| **Estacionariedad y autocorrelación** | [`pronostico.md`](pronostico.md) §2.3 a §2.5 | CUMPLE | ADF y KPSS (d = 1, D = 1 es estacionaria); ACF y PACF interpretadas; correlación cruzada con tres variables: ninguna exógena significativa en ambos escenarios, no se incorporan |
| **Cuatro modelos** | [`pronostico.md`](pronostico.md) §3, [`candidatos_aicc.csv`](../../laboratorio/pronosticos/resultados/candidatos_aicc.csv) | CUMPLE | SES, Holt, Holt-Winters (por AICc) y SARIMA (72 combinaciones por AICc); los parámetros SARIMA se justifican con ACF, PACF y AICc |
| **Selección por error**: MAE, RMSE y MAPE en datos de prueba | [`pronostico.md`](pronostico.md) §4, [`comparacion_modelos_2024.csv`](../../laboratorio/pronosticos/resultados/comparacion_modelos_2024.csv) | CUMPLE con salvedades | Criterio fijado antes de comparar. **Un solo año de prueba:** el ganador no es estable y el ingenuo estacional tiene menor MAE y MAPE |
| **Residuos y comunicación**: Ljung-Box, intervalo explicado al cliente | [`pronostico.md`](pronostico.md) §5 y §6, [`residuos_modelo_elegido.csv`](../../laboratorio/pronosticos/resultados/residuos_modelo_elegido.csv), [`pronostico_modelo_elegido.csv`](../../laboratorio/pronosticos/resultados/pronostico_modelo_elegido.csv) | CUMPLE con salvedades | Ljung-Box p = 0.273 y 0.685; residuos **no normales** (intervalos aproximados); frase para el cliente en §6; intervalos de ±12 a ±21 pp |
| Pronóstico publicado en el tablero | [`tablero.md`](tablero.md), [`tablero/`](../../tablero/), [Auditoría 7](../../calidad/auditorias.md) | CUMPLE | Verificado en la URL pública el 2026-11-14 04:25 UTC (véase «Tablero») |

## Calidad en los Sistemas de Información
| Criterio de la rúbrica E1 | Evidencia (enlace) | Estado | Nota del equipo |
|---|---|---|---|
| *Arranque de calidad* (criterio de la rúbrica de **E0**; la pág. 14 lo lista): registros individuales, bitácora activa, tres objetivos medibles | [`tiempo-integrante-a.csv`](../../calidad/tiempo-integrante-a.csv), [`defectos-integrante-a.csv`](../../calidad/defectos-integrante-a.csv), [`tiempo-integrante-b.csv`](../../calidad/tiempo-integrante-b.csv), [`defectos-integrante-b.csv`](../../calidad/defectos-integrante-b.csv), [`bitacora_capturas.jsonl`](../../calidad/bitacora_capturas.jsonl), [`objetivos.md`](../../calidad/objetivos.md) | **PARCIAL** | A: E0 750 min y E1 960 min (870 + 90 de las mejoras de E1); acumulado 1,710 min, 1,230 sin el prototipo; tiempos y minutos de corrección estimados retrospectivamente, sin tiempo de ejecución autónoma de herramientas; 28 defectos ([`psp-e1-integrante-a-respaldo.md`](../../calidad/psp-e1-integrante-a-respaldo.md)). B: 118 min en 23 intervalos con inicio y fin; 14 defectos |
| **Fiabilidad y disponibilidad**: MTBF, MTTR y disponibilidad con 7 días de bitácora | [`fiabilidad.md`](fiabilidad.md), [`fiabilidad_e1.json`](../../calidad/fiabilidad_e1.json), [`pipeline/fiabilidad.py`](../../pipeline/fiabilidad.py), [`test_fiabilidad.py`](../../tests/test_fiabilidad.py) | **PARCIAL** | Medidas con lo que hay: éxito 85.7 % (6/7, IC 95 % 42.1–99.6 %), MTTR 268 s (n = 1, extremos no corroborados). La bitácora cubre **3.83 de 7 días**; MTBF y disponibilidad solo exploratorios (un incidente). **No cumple el objetivo del 95 %** |
| **Seguridad**: `gitleaks` y `pip-audit` sin hallazgos; respaldo probado | [`seguridad.md`](seguridad.md), [`calidad/evidencia/`](../../calidad/evidencia/), [`test_evidencia_gitleaks.py`](../../tests/test_evidencia_gitleaks.py), [`test_respaldo_bronce.py`](../../tests/test_respaldo_bronce.py), [`test_bloqueo_tablero.py`](../../tests/test_bloqueo_tablero.py) | CUMPLE | `gitleaks` 8.30.1 sin hallazgos (local y CI); `pip-audit` sin vulnerabilidades, también en las transitivas del tablero; respaldo del bronce con manifiesto SHA-256, restauración probada (28 archivos) y copia externa verificada por hash ([`seguridad.md`](seguridad.md) §6.3); bloqueo con hashes del tablero; acciones fijadas por SHA. Protección de `main` activa y comprobada ([`seguridad.md`](seguridad.md) §7) |
| **Requerimientos**: verificables, cada uno con su comprobación | [`requerimientos.md`](requerimientos.md), [`test_requerimientos.py`](../../tests/test_requerimientos.py) | CUMPLE | 43 requerimientos: 36 cumplidos, 3 parciales, 3 no cumplidos, 1 propuesto |
| **Plan SQA**: estructura IEEE 730 adaptada | [`plan_sqa.md`](plan_sqa.md), [`auditorias.md`](../../calidad/auditorias.md) (Auditorías 1 a 8) | CUMPLE con salvedades | Plan versión 1.1; desviaciones y acción correctiva en §5.1; plantilla de PR y `CODEOWNERS` en `.github/` |
| **Integración continua**: pruebas, linter y puerta de datos en cada push | [`ci.yml`](../../.github/workflows/ci.yml), [`test_ci_workflow.py`](../../tests/test_ci_workflow.py), [`pipeline.md`](pipeline.md) §6 | CUMPLE | `ci.yml` ejecuta `ruff`, `pytest` con cobertura (piso de 75 %), la puerta de datos, `verificar_oro`, el verificador de E0, `gitleaks`, `pip-audit` y el bloqueo del tablero; acciones fijadas por SHA. Suite: 432 aprobadas y 2 omitidas (red); cobertura 82 %. Ejecuciones en GitHub: 43557153021 (`4242ea5`) y posteriores, con los cuatro trabajos en éxito |

## Relatoría de etapa
[`docs/relatoria-E1.md`](../relatoria-E1.md) (máximo dos páginas, verificadas al exportar a PDF A4). Conformidad de A y de B (aprobación del PR #19).

## Tablero
- URL: https://tdl-turistico-colima.streamlit.app, desplegada desde `main` con Python 3.13. Lectura del 2026-11-14 04:25 UTC: filtro de periodo, resumen ejecutivo, fechas clave, indicadores 45.9 %, 54.7 %, 1.5 % y 12 de 12, y seis pestañas sin errores.
- El tablero coincide con los CSV del laboratorio (recálculo en la Auditoría 7, V3 a V5).
- No verificado: vista en teléfono y seguimiento de `main` en cada cambio futuro (la configuración de Streamlit Cloud no se lee desde el repositorio). Streamlit Community Cloud puede dejar la aplicación en reposo.
- Cumplimiento por criterio del PDF, con pruebas y evidencias: [`matriz_cumplimiento.md`](matriz_cumplimiento.md).

## Issues de la entrega anterior
La API pública de GitHub (2026-11-14) devuelve 0 issues. No hay observaciones de los docentes registradas como issues; la confirmación con los docentes está pendiente.

## Uso de IA generativa
Ambas integrantes usaron Claude Code (Anthropic) para escribir y revisar código, pruebas y documentos, ejecutar verificaciones y redactar auditorías; los PSP de B lo marcan fila por fila. La asistencia no cuenta como revisión independiente. Cada integrante debe poder explicar lo que entrega en la defensa del 17 y 18 de noviembre.

## Estado de los requisitos de entrega y limitaciones vigentes
| Requisito de entrega (PDF, págs. 5 y 12) | Estado |
|---|---|
| Etiqueta `e1` sobre un commit de `main` | Creada: `134c333`, 2026-11-13 23:32 hora local |
| Enlace de la etiqueta en el formulario de entregas | Registrado por A; no verificable desde el repositorio |
| Los tres docentes como colaboradores | Declarado por la titular (2026-11-13); no verificable desde la API pública |
| Relatoría y registros PSP | Relatoría de 2 páginas; PSP de A con E0 750 + E1 960 min = 1,710 min (1,230 sin el prototipo); PSP de B: 118 min confirmados en la Auditoría 8 |
| Conformidad con el plan SQA | A y B registradas (2026-11-13), [`plan_sqa.md`](plan_sqa.md) §5.1; relatoría aprobada por B en el PR #19 |

| Componente adicional (no lo exige el PDF) | Estado |
|---|---|
| Protección de `main` | Activa desde el 2026-11-15; dos capturas manuales con éxito (una con el ruleset activo) y PR de prueba #21 bloqueado ([`seguridad.md`](seguridad.md) §7) |
| Copia externa del bronce | Hecha (2026-11-15), verificada por hash ([`seguridad.md`](seguridad.md) §6.3) |
| Hashes para las otras tres listas de dependencias; imágenes por *digest* | No implementados |
| Isolation Forest, unión mes a mes, nuevas fuentes | No aplican con los datos disponibles |

| Limitación vigente | Detalle |
|---|---|
| Fiabilidad: bitácora de 3.83 de 7 días, objetivo de 95 % no alcanzado, MTBF y disponibilidad exploratorios | [`fiabilidad.md`](fiabilidad.md) §4.2 |
| Desviaciones del proceso de revisión de PR | [`plan_sqa.md`](plan_sqa.md) §5.1 |
| Mecanismo de la única celda vacía de Base70 (Mexicali) no determinable | [`faltantes_y_atipicos.md`](faltantes_y_atipicos.md) §1 |
| Un año de prueba; el ingenuo estacional supera al SARIMA en MAE y MAPE | [`pronostico.md`](pronostico.md) §4 y §10 |

Próximos pasos: regenerar la fiabilidad con las capturas nuevas como un periodo adicional, repetir `gitleaks` sobre la versión vigente y correr el experimento de E2 ([`ruta_experimento_e2.md`](ruta_experimento_e2.md)).

## Mejoras de E1 (rama `e1/mejoras-postentrega`)
Fortalecimiento y correcciones de los mismos componentes de E1, con fecha de 2026-11-14 en adelante; la etiqueta `e1` (`134c333`) conserva la versión original. No reemplazan ninguna métrica de E1.
| Mejora | Dónde está documentada |
|---|---|
| Intervalos de predicción por bootstrap de bloques y validación de origen móvil; publicados en el tablero; proyección histórica 2025–2027; sin datos oficiales 2025–2026 | [`pronostico.md`](pronostico.md) §10, [`tablero.md`](tablero.md) §12 |
| Esquema pandera de la plata de DENUE (R-E07) | [`pipeline.md`](pipeline.md) §3 |
| Análisis cuantitativo del ruido | [`faltantes_y_atipicos.md`](faltantes_y_atipicos.md) §2.1 |
| Decisión sobre llevar las discretizaciones al oro (no) | [`transformaciones.md`](transformaciones.md) §9 |
| Protección de `main` activa y comprobada, respaldo externo, captura con llave de despliegue | [`seguridad.md`](seguridad.md) §6.3 y §7 |
| PSP de A reorganizado: 870 min del desarrollo original + 90 de las mejoras de E1 por bloque, 6 defectos agregados, minutos de corrección estimados y totales con y sin prototipo | [`calidad/README.md`](../../calidad/README.md), [`psp-e1-integrante-a-respaldo.md`](../../calidad/psp-e1-integrante-a-respaldo.md) |
