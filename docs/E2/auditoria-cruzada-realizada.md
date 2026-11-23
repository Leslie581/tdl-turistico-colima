# Auditoría cruzada E2 realizada: Observatorio inmobiliario de Colima (TRUSTED DATA LAB)

| | |
|---|---|
| **Equipo auditor** | TDL de Ocupación Hotelera de Colima: Leslie Valadez Macías (A) y Eimy Melissa Urbina Meza (B). Informe elaborado por A con asistencia de Claude Code; **revisado en conjunto por A y B, aprobado por B en el [PR #33](https://github.com/Leslie581/tdl-turistico-colima/pull/33) y enviado al equipo auditado; la recepción y la respuesta de ese equipo siguen pendientes de confirmar; no hay firmas** (sección 13) |
| **Equipo auditado** | Observatorio inmobiliario de Colima (trabajo individual) · [repositorio](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima) · [tablero](https://trusted-data-lab-colima-8dbknfsg2lhzub8uvrrhqo.streamlit.app/) |
| **Versión auditada** | Commit `65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522` (lo declara el comentario del ZIP recibido, y coincide con `main` y con la etiqueta `e2` que consultó la API pública de GitHub el 2026-11-23) |
| **Objeto auditado** | El observatorio **en su estado E1** (PDF, pág. 18), evaluado con ISO/IEC 25010 e ISO/IEC 25012 |
| **Fecha de ejecución** | 2026-11-23 (UTC) |
| **Evidencia** | [`evidencia/auditoria_cruzada/`](evidencia/auditoria_cruzada/): [`metricas_auditoria_externa.json`](evidencia/auditoria_cruzada/metricas_auditoria_externa.json) y [`capturas_externas.csv`](evidencia/auditoria_cruzada/capturas_externas.csv) |

Este informe no es una certificación ISO ni otorga el Sello TDL. Los enlaces a archivos del equipo auditado apuntan al commit fijado, de modo que siguen siendo verificables si el repositorio cambia. La auditoría que **recibimos** de ese equipo se documenta por separado en [`auditoria-cruzada-recibida.md`](auditoria-cruzada-recibida.md).

## 1. Resumen ejecutivo

**Dictamen:** el observatorio, en su estado E1, **funciona, se reproduce y es honesto sobre sus límites**, pero **no alcanza sus propios objetivos de fiabilidad** y tiene vacíos de calidad de datos y de documentación que conviene cerrar antes de E3. No se encontró ningún defecto crítico.

- **Reproducibilidad comprobada:** en un entorno nuevo, el pipeline Bronce → Plata → Oro dio exactamente lo que el equipo documenta (2,140 registros SNIIV, 258 SHF, 0 rechazados y 131 comparaciones), las 12 pruebas pasan una vez generado el Oro y las métricas ISO/IEC 25012 que publicó el equipo se regeneran sin ninguna diferencia.
- **ISO/IEC 25010:** de las 8 características, **2 cumplen** (eficiencia de desempeño y compatibilidad) y **6 son parciales** (adecuación funcional, capacidad de interacción, fiabilidad, seguridad, mantenibilidad y portabilidad); en los criterios, 28 criterios: 13 CUMPLE, 11 PARCIAL, 1 NO CUMPLE y 3 NO VERIFICABLE.
- **ISO/IEC 25012:** en los criterios, 17 criterios: 11 CUMPLE, 3 PARCIAL, 0 NO CUMPLE y 3 NO VERIFICABLE; los parciales son la completitud temporal de SNIIV, la fecha de captura de SHF y el diccionario.
- **Hallazgos:** **0 críticos, 1 mayor y 8 menores** (sección 6). El único mayor es la fiabilidad de la captura: objetivo de disponibilidad no cumplido y métricas MTBF, MTTR y disponibilidad sin calcular, aunque el historial público permite calcularlas. La completitud temporal de SNIIV, no diagnosticada, es un hallazgo menor: lo comprobado es la falta de diagnóstico, no un error demostrado en los cálculos.
- **Fortalezas comprobadas:** ocho (sección 7), entre ellas la reproducibilidad, el linaje por hash verificado, el CI en verde y una documentación ética sólida.
- **Sospechas previas:** la etiqueta `e2` desactualizada **se descarta** (apunta al último commit); las evaluaciones ISO incompletas **se confirman** como limitación declarada de su entregable E2; la ausencia de Plata y Oro en el ZIP **está justificada** (sección 8).

## 2. Alcance, material y exclusiones

- **Dentro del alcance:** captura (extractores y workflow), arquitectura Bronce, Plata y Oro, puerta de calidad, linaje, análisis estadístico de E1 como evidencia de calidad, tablero, seguridad, pruebas, CI, SQA y documentación E0 y E1, tal como siguen presentes en `main`.
- **Cómo se aisló el estado E1:** el ZIP es `main`. Entre la etiqueta `e1` (`5c67a0c`) y `main` hay 17 commits y 73 archivos: son aditivos (módulos y documentos de E2, 22 archivos de bronce) salvo `pipeline/ejecutar.py` (columnas de linaje), `dashboard/app.py` (mapa), el workflow de CI, `requirements.txt` y `.gitignore` (según la API de comparación de GitHub). Los criterios E1 se evalúan sobre esos módulos.
- **Fuera del alcance (no se penaliza):** los entregables de E2 del equipo auditado (cruce espacial, experimentos factoriales, su propia evaluación ISO) y los requisitos de E3. Se registran solo como observaciones informativas (sección 9).
- **No se modificó el proyecto auditado.** Se trabajó sobre una copia en un directorio aparte y en un entorno virtual aislado; el repositorio externo y su tablero solo se leyeron (el tablero se cargó una vez y se recorrieron sus secciones, sin pruebas de carga ni de seguridad).

## 3. Metodología y entorno

Cada resultado se etiqueta con su tipo de evidencia:

- **EJECUTADO:** lo corrió la auditoría.
- **OBSERVADO:** se leyó en archivos, código, historial público o en el tablero.
- **NO VERIFICABLE:** no hay acceso o la herramienta no está disponible; no se convierte en hallazgo.

**Severidad.** *Crítico:* impide usar el observatorio, expone datos personales o secretos, o invalida sus resultados. *Mayor:* incumple un requisito explícito (del PDF o propio) con efecto en la confianza de los resultados o en una métrica obligatoria. *Menor:* desviación localizada, documental o de buena práctica que no invalida resultados.

**Entorno:** Windows 11 con Python 3.13.15, entorno virtual nuevo con `requirements-e1.txt` (pandas 2.3.3, numpy 2.5.5, geopandas 1.2.0, statsmodels 0.15.0, pandera 0.36.0, pytest 9.2.0, ruff 0.17.6, streamlit 1.67.0). El CI del equipo usa Python 3.11 sobre Ubuntu.

| Ref. | Verificación | Tipo | Resultado |
|---|---|---|---|
| E1 | `pip install -r requirements-e1.txt` | EJECUTADO | Termina con código 0 |
| E2 | `ruff check pipeline tests` (alcance del CI) y `ruff check .` | EJECUTADO | Sin hallazgos en el alcance del CI; **10 hallazgos de estilo** en `extractores/` |
| E3 | `pytest -q` en clon limpio | EJECUTADO | 10 pasan y **2 fallan**: necesitan el Plata que genera el pipeline |
| E4 | `python -m pipeline.ejecutar` | EJECUTADO | 3.0 s; 2,140 SNIIV y 258 SHF válidos, 0 rechazados, 131 comparaciones |
| E5 | `python -m pipeline.ejecutar_analisis` | EJECUTADO | 3.9 s; MAE 1.270821 (Manzanillo, ARIMA) y 2.165961 (Villa de Álvarez, Holt); ADF de la primera diferencia p = 0.920482 y 0.990787; Ljung-Box de Holt p = 0.000284 |
| E6 | `pytest -q` tras el pipeline, con cobertura | EJECUTADO | 12 pasan; cobertura **31 %** (860 sentencias, 597 sin cubrir) |
| E7 | `pip-audit -r requirements-e1.txt` | EJECUTADO | Sin vulnerabilidades conocidas |
| E8 | `python -m calidad.evaluacion_e2` y comparación con lo publicado | EJECUTADO | 7 productos Oro; **0 diferencias** con `metricas_iso25012.json` |
| E9 | Recómputo del ANOVA 2³ y de la confirmación desde `corridas_aleatorizadas.csv` | EJECUTADO | Diferencia máxima de F de 7.7 × 10⁻¹²; mejora de 47.73 % |
| E10 | `python -m experimentos.e2_estadistica` (18.9 s) | EJECUTADO | Mismos términos significativos en los 4 ANOVA, mismo tratamiento ganador; mejora de confirmación de 44.7 % frente al 47.7 % publicado |
| E11 | Hashes SHA-256 del Oro y del bronce de INEGI | EJECUTADO | 3 de 3 productos Oro y 3 de 3 capturas de INEGI coinciden con su archivo de origen |
| E12 | Análisis del bronce SNIIV (21 capturas) | EJECUTADO | 21 hashes distintos, **0 diferencias de contenido**, 21 de 21 con metadatos; falta el día 2026-11-18 |
| E13 | Historial público de GitHub Actions (API) | OBSERVADO | 39 ejecuciones; capturas, incidentes y CI en [`capturas_externas.csv`](evidencia/auditoria_cruzada/capturas_externas.csv) |
| E14 | Tablero público | OBSERVADO | 8 secciones, 0 excepciones, métricas iguales al pipeline (2,140 / 258 / 0 / 0) y mapa interactivo |
| E15 | Revisión estática de código, workflows y documentos; búsqueda de patrones de secretos | OBSERVADO | Sin patrones de secretos ni llamadas peligrosas |
| NV | `gitleaks`, respaldo del bronce, colaboradores del repositorio, registros de ejecución de Actions (requieren sesión) y exactitud frente a la API viva | NO VERIFICABLE | Ver sección 10 |

## 4. Matriz de cumplimiento ISO/IEC 25010

Estados: CUMPLE, PARCIAL, NO CUMPLE y NO VERIFICABLE. Una característica queda en CUMPLE si todos sus criterios cumplen, en NO CUMPLE si fallan todos los principales y en PARCIAL en cualquier otro caso. Las referencias *Ex* remiten a la tabla de la sección 3 y *IN-nn* a los hallazgos.

### 4.1 Estado de los requerimientos del equipo (criterio AF-1)

| Req. | Requisito (`MATRIZ_REQUISITOS.md`) | Evidencia de la auditoría | Estado |
|---|---|---|---|
| R-01 | Capturar SNIIV y SHF con trazabilidad | SNIIV programado (12 de 13 ejecuciones programadas exitosas), con metadatos en 21 de 21 capturas; SHF incorporado manualmente, y así lo declara el equipo | CUMPLE |
| R-02 | Plata y Oro reproducibles | E4 y E5 | CUMPLE |
| R-03 | Rechazar filas inválidas con motivo | Pruebas `test_sniiv_cuarentena` y `test_sniiv_tipo_invalido_a_cuarentena`; con los datos reales no hay rechazos | CUMPLE |
| R-04 | Conservar granularidad mensual y trimestral | Plata mensual, Oro trimestral | CUMPLE |
| R-05 | Cuatro modelos con prueba retenida | E5: MAE reproducidos | CUMPLE |
| R-06 | Diagnóstico de estacionariedad y residuos | E5: ejecutado; los resultados no son favorables y el equipo lo declara | CUMPLE |
| R-07 | Pronóstico con intervalo validado | El propio equipo lo marca pendiente: las bandas no están calibradas | NO CUMPLE |
| R-08 | Fiabilidad y disponibilidad | Tasa medida; MTBF, MTTR y disponibilidad sin calcular (IN-01) | PARCIAL |
| R-09 | `pip-audit` y `gitleaks` | `pip-audit` ejecutado (E7); `gitleaks` solo documentado | PARCIAL |
| R-10 | Respaldo del bronce | Copia fuera del repositorio: sin acceso | NO VERIFICABLE |
| R-11 | Pruebas, linter y puerta de calidad en CI | 16 de 16 ejecuciones del CI en verde | CUMPLE |
| R-12 | SQA y defectos documentados | `PLAN_SQA.md` con las ocho secciones de IEEE 730 adaptadas | CUMPLE |

**Resultado:** 8 cumplen, 1 no cumple, 2 son parciales y 1 no se puede verificar.

### 4.2 Matriz por característica

| ID | Característica y criterio (umbral) | Evidencia y método | Resultado | Estado |
|---|---|---|---|---|
| AF-1 | **Adecuación funcional.** Requerimientos funcionales cumplidos | Tabla 4.1 | 8 de 12 cumplen | PARCIAL |
| AF-2 | Resultados del pipeline iguales a los documentados | E4, E5 | Coinciden las cuentas, los MAE, ADF y Ljung-Box | CUMPLE |
| EF-1 | **Eficiencia de desempeño.** Pipeline completo en ≤ 5 min (umbral del auditor) | E4, E5; CI (API de Actions) | 3.0 s y 3.9 s; CI de 33 a 74 s (mediana 60 s) | CUMPLE |
| EF-2 | Captura diaria dentro del tiempo límite | API de Actions | Mediana de 26 s y máximo de 31 s en las exitosas | CUMPLE |
| CO-1 | **Compatibilidad.** Ejecución en más de un entorno | CI Python 3.11 y Ubuntu, y E1 a E6 con Python 3.13 y Windows | Funciona en ambos | CUMPLE |
| CO-2 | Formatos abiertos | Parquet, CSV, JSON y GeoJSON leídos con pandas y GeoPandas | Correcto | CUMPLE |
| CO-3 | Despliegue público | E14 | Accesible | CUMPLE |
| CI-1 | **Capacidad de interacción.** Tablero sin errores | E14 | 0 excepciones | CUMPLE |
| CI-2 | Comunicación del pronóstico al cliente (intervalo y frase explicativa) | [`dashboard/app.py` L163-L168](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/dashboard/app.py#L163-L168) | Tabla con bandas y advertencia; sin gráfica ni frase para el cliente (R-07) | PARCIAL |
| CI-3 | Usabilidad con usuarios y accesibilidad | No hay pruebas | Sin dato | NO VERIFICABLE |
| FI-1 | **Fiabilidad.** Objetivo E0: ≥ 95 % de ejecuciones programadas exitosas en 14 días ([`objetivos-calidad.md`](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E0/objetivos-calidad.md)) | E13 | 12 de 13 = **92.31 %** (todas las capturas: 20 de 23 = 86.96 %) | NO CUMPLE |
| FI-2 | MTBF, MTTR y disponibilidad medidos | E13 y método de la nota de la sección 6 | La documentación no los trae. Cálculo de la auditoría: MTBF 97.7 h, MTTR 8.1 h, disponibilidad 0.923 | PARCIAL |
| FI-3 | Bitácora de ejecuciones de la captura | Solo el historial de Actions, sin archivo versionado | Falta | PARCIAL |
| FI-4 | CI estable | E13 | 16 de 16 verdes | CUMPLE |
| FI-5 | Pruebas reproducibles en clon limpio | E3, E6 | 10 de 12 en clon limpio; 12 de 12 tras el pipeline | PARCIAL |
| SE-1 | **Seguridad.** Dependencias sin vulnerabilidades | E7 | Sin hallazgos | CUMPLE |
| SE-2 | Secretos en el historial (`gitleaks`) | Documentado en [`SEGURIDAD_Y_CONFIABILIDAD.md`](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E1/SEGURIDAD_Y_CONFIABILIDAD.md): 0 hallazgos en 61 commits. No se re-ejecutó; la búsqueda de patrones de la auditoría no encontró secretos | Sin acceso a la herramienta | NO VERIFICABLE |
| SE-3 | Mínimo permiso en los workflows | [`captura.yml` L6-L7](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/.github/workflows/captura.yml#L6-L7) y CI | CI en solo lectura; la captura escribe para poder guardar; no usa secretos | CUMPLE |
| SE-4 | Respaldo del bronce probado | Documentado, copia fuera del repositorio | Sin acceso | NO VERIFICABLE |
| SE-5 | Sin datos personales | E15 | Fuentes públicas agregadas | CUMPLE |
| SE-6 | Configuración de desarrollo segura | [`devcontainer.json` L22](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/.devcontainer/devcontainer.json#L22) | Desactiva CORS y XSRF de Streamlit (solo desarrollo) | PARCIAL |
| MA-1 | **Mantenibilidad.** Linter sin hallazgos | E2 | Limpio en el alcance del CI; 10 hallazgos de estilo en `extractores/` | PARCIAL |
| MA-2 | Pruebas y cobertura | E6 | 12 pruebas; cobertura de 31 % (`ejecutar.py` 20 %, extractores 0 %, validación 100 %) | PARCIAL |
| MA-3 | Modularidad y documentación | E15 | Módulos por función, tres capas y documentos E0 a E2 | CUMPLE |
| MA-4 | Legibilidad | `pipeline/ejecutar.py` | Líneas de hasta 495 caracteres y sangría de un espacio en `ejecutar.py` y `validacion.py` | PARCIAL |
| PO-1 | **Portabilidad.** Instalación desde cero | E1 | Código 0 en un entorno nuevo | CUMPLE |
| PO-2 | Dependencias reproducibles | `requirements-e1.txt` | Sin archivo de bloqueo y sin cota superior en numpy, scipy, statsmodels y ruff | PARCIAL |
| PO-3 | Artefactos independientes del sistema operativo | `data/oro/reporte_calidad.json` | Las rutas se guardan con `\` en Windows | PARCIAL |

**Resumen por característica:** CUMPLE en **eficiencia de desempeño** y **compatibilidad**; PARCIAL en **adecuación funcional**, **capacidad de interacción**, **fiabilidad** (con el objetivo FI-1 en NO CUMPLE), **seguridad**, **mantenibilidad** y **portabilidad**. Ninguna característica queda en NO CUMPLE ni sin evaluar.

## 5. Matriz de cumplimiento ISO/IEC 25012

Los umbrales son del auditor cuando el equipo no definió uno, y así se indica.

| ID | Característica y criterio | Evidencia y método | Resultado | Estado |
|---|---|---|---|---|
| EX-1 | **Exactitud sintáctica.** Tipos y rangos válidos | Esquemas `pandera` y reglas por fila (E4, E6) | 0 rechazos; viviendas ≥ 1, índice SHF de 53.37 a 217.26 | CUMPLE |
| EX-2 | **Exactitud semántica.** Contraste con la fuente viva | No se consultó la API de SNIIV | Sin dato | NO VERIFICABLE |
| CM-1 | **Completitud** de celdas | E8 | SNIIV al 100 %; 4 de 7 productos Oro al 100 %; la columna `Global` de SHF está nula en las 258 filas | CUMPLE |
| CM-2 | Completitud temporal de SNIIV | E4 (análisis de la Plata) | 191 de 383 agregados trimestrales (49.9 %) salen de menos de 3 meses observados; solo 8 de 10 municipios tienen registros (faltan Ixtlahuacán y Minatitlán) (IN-02) | PARCIAL |
| CS-1 | **Consistencia.** Claves únicas y congruencia de reglas | E4, E6 | 0 duplicados; claves municipales congruentes; granularidades separadas | CUMPLE |
| CS-2 | Consistencia entre fuentes | Oro `comparacion_municipal` | 131 filas: Manzanillo 65 y Villa de Álvarez 66; la suma trimestral del Oro es igual a la de la Plata (383 de 383) | CUMPLE |
| CR-1 | **Credibilidad.** Origen oficial y verificable | Metadatos (HTTP 200 en 21 de 21), [`etica-datos.md`](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/etica-datos.md) | Fuentes oficiales; el archivo SHF no tiene licencia propia verificada y así se declara | CUMPLE |
| AC-1 | **Actualidad.** Rezago de ≤ 2 trimestres (umbral del auditor) | E4 | SNIIV hasta 2026-08 (≈ 3 meses) y SHF hasta el 2.º trimestre de 2026 (≈ 1 trimestre) | CUMPLE |
| TR-1 | **Trazabilidad.** Cadena del Oro al bronce | E11 | Hash recomputado coincide en 3 de 3 productos; identificadores de Oro únicos | CUMPLE |
| TR-2 | Fecha de captura verificada | [`ejecutar.py` L25-L34](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/pipeline/ejecutar.py#L25-L34) | Para SHF la fecha sale de `mtime_archivo_no_verificado`; el equipo lo declara | PARCIAL |
| CF-1 | **Conformidad.** Esquema y cuarentena | E4, E6 | Cumple | CUMPLE |
| CD-1 | **Confidencialidad.** Sin datos personales | E15 | Fuentes públicas agregadas | CUMPLE |
| CP-1 | **Comprensibilidad.** Diccionario de la capa Oro | [`diccionario_oro.md`](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E1/diccionario_oro.md) frente a las columnas reales | Documenta 4 de 10 columnas de `registros_trimestrales` y 5 de 16 de `comparacion_municipal`; cuatro productos analíticos sin documentar (IN-07) | PARCIAL |
| DS-1 | **Disponibilidad.** Datos accesibles | E4, E14 | El Oro no se versiona, pero se regenera en 3 s; tablero accesible | CUMPLE |
| RC-1 | **Recuperabilidad.** Respaldo probado | Documentado | Sin acceso | NO VERIFICABLE |
| PR-1 | **Portabilidad** de los datos | Formatos | Parquet, CSV y GeoJSON | CUMPLE |
| NE-1 | Precisión, accesibilidad y eficiencia de los datos | El equipo no definió métricas | Sin dato | NO VERIFICABLE |

**Totales de las dos matrices:** ISO/IEC 25010, 28 criterios: 13 CUMPLE, 11 PARCIAL, 1 NO CUMPLE y 3 NO VERIFICABLE; ISO/IEC 25012, 17 criterios: 11 CUMPLE, 3 PARCIAL, 0 NO CUMPLE y 3 NO VERIFICABLE.

## 6. Hallazgos

Ningún hallazgo es crítico. La columna «Declarado» indica si el propio equipo auditado ya reconocía el problema.

| ID | Severidad | Hallazgo | Declarado |
|---|---|---|---|
| IN-01 | **MAYOR** | Fiabilidad de la captura: objetivo no cumplido y métricas MTBF, MTTR y disponibilidad sin calcular | Parcialmente |
| IN-02 | Menor | Completitud temporal y semántica de las ausencias de SNIIV sin diagnosticar | No |
| IN-03 | Menor | Capturas diarias de SNIIV redundantes: contenido idéntico en las 21 | No |
| IN-04 | Menor | Extractores sin reintentos ni identificación de contacto, y workflow que guarda antes de validar | No |
| IN-05 | Menor | Cobertura baja, pruebas dependientes del orden y alcance parcial del linter | Parcialmente |
| IN-06 | Menor | Documentación con cifras y estados contradictorios o desactualizados | No |
| IN-07 | Menor | Diccionario de la capa Oro desactualizado | Parcialmente |
| IN-08 | Menor | PSP fuera del formato del Kit y sin tiempos de E1 y E2 | Parcialmente |
| IN-09 | Menor | Seguridad: `gitleaks` fuera del CI, respaldo sin copia externa verificable y CORS y XSRF desactivados en el entorno de desarrollo | Parcialmente |

**Nota sobre las métricas de fiabilidad.** Se aplican las definiciones de [`docs/E1/fiabilidad.md`](../E1/fiabilidad.md): un incidente es una racha de fallos; su reparación va del inicio del primer fallo al fin del primer éxito posterior; MTBF = (tiempo observado − reparación total) ÷ incidentes; disponibilidad = MTBF ÷ (MTBF + MTTR). Las marcas de tiempo son `run_started_at` y `updated_at` de la API pública de Actions. El tiempo de reparación del incidente del 18-nov es una **cota superior**: el siguiente éxito es la ejecución programada del día siguiente.

### IN-01 · MAYOR · Fiabilidad de la captura

- **Descripción.** El objetivo que fijó el equipo en E0 (≥ 95 % de ejecuciones programadas exitosas en 14 días) **no se cumple**: 12 de 13 programadas dieron éxito (92.31 %), y con todas las ejecuciones, 20 de 23 (86.96 %). La documentación de E1 reconoce que no se alcanza el objetivo, pero **no calcula MTBF, MTTR ni disponibilidad** y afirma que no hay evidencia suficiente. El historial público de Actions sí trae las marcas de tiempo. Con ellas, la auditoría obtiene tres incidentes (ejecuciones 3, 6 y 19), MTTR de 8.1 h, MTBF de 97.7 h y disponibilidad de 0.923. Además, el fallo de la ejecución programada del **2026-11-18** (ejecución 19, paso «Registro SNIIV», 79 s frente a los 20 a 30 s habituales) **no aparece en ningún documento** y deja ese día sin captura.
- **Evidencia.** [`capturas_externas.csv`](evidencia/auditoria_cruzada/capturas_externas.csv); ejecuciones [3](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/actions/runs/42651071773), [6](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/actions/runs/42655282474) y [19](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/actions/runs/44401475440); [`SEGURIDAD_Y_CONFIABILIDAD.md` L13 y L22](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E1/SEGURIDAD_Y_CONFIABILIDAD.md#L13); [`MATRIZ_REQUISITOS.md` L12](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E1/MATRIZ_REQUISITOS.md#L12).
- **Requisito afectado.** Rúbrica E1, «Fiabilidad y disponibilidad» (MTBF, MTTR y disponibilidad medidos con 7 días de bitácora); PDF, «Arranque de calidad» (bitácora de captura activa); objetivo O1 de E0.
- **Impacto.** Una métrica obligatoria queda sin calcular aunque había datos. Como cada captura de SNIIV es una instantánea completa, el día perdido no pierde datos históricos (IN-03); el efecto es sobre la métrica y la confianza.
- **Causa probable.** El fallo del 18-nov ocurrió en la petición a la API de SNIIV; su duración de 79 s es compatible con el límite de 60 s del extractor, pero **sin los registros de la ejecución (requieren sesión) la causa no está confirmada**. Los fallos 3 y 6 fueron defectos del validador, ya corregidos, que el equipo documenta.
- **Recomendación.** Calcular y publicar MTBF, MTTR y disponibilidad con el método anterior; exportar y versionar la bitácora de ejecuciones; documentar el incidente del 18-nov; y medir el objetivo por ventanas móviles.

### IN-02 · Menor · Completitud temporal de SNIIV sin diagnosticar

- **Descripción.** La documentación afirma que no hay nulos en SNIIV y la puerta de calidad solo mira nulos por celda, lo que es cierto. Pero el panel es disperso: de los 383 agregados trimestrales del Oro, **191 (49.9 %) se calculan con menos de 3 meses observados**, y solo 8 de los 10 municipios de Colima tienen registros (faltan Ixtlahuacán y Minatitlán). Por ejemplo, Armería tiene registros en 35 de los 198 meses entre 2010-01 y 2026-06. La puerta de calidad no evalúa continuidad temporal ni cobertura, y los agregados no indican cuántos meses los componen.
- **Evidencia.** Análisis de la Plata generada por E4 (cuentas en [`metricas_auditoria_externa.json`](evidencia/auditoria_cruzada/metricas_auditoria_externa.json)); [`CIERRE_E1.md` L15](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E1/CIERRE_E1.md#L15); [`pipeline/validacion.py`](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/pipeline/validacion.py).
- **Requisito afectado.** Rúbrica E1, «Valores faltantes» (mecanismo diagnosticado y tratamiento justificado); ISO/IEC 25012, completitud.
- **Impacto.** El tablero publica sumas trimestrales de «viviendas» y una suma histórica por municipio sin advertir que muchos trimestres están parcialmente observados. Si una ausencia significa «cero registros», las sumas son correctas; si significa «dato faltante», están subestimadas.
- **Por qué es menor.** Lo comprobado es la **falta de diagnóstico y de documentación** de la completitud temporal; no hay un error demostrado en los cálculos. Se mantiene como hallazgo porque la rúbrica de E1 exige ese diagnóstico.
- **Causa probable.** El cubo de SNIIV solo devuelve filas con registros. Ninguna de las 2,140 filas tiene 0 viviendas (el mínimo es 1) ni nulos, lo que es coherente con un cubo que omite los ceros, **pero no lo demuestra**. **La semántica de la ausencia no está verificada** ni con la documentación de la fuente ni con otra consulta; por eso el hallazgo es el diagnóstico faltante y no un error de cálculo.
- **Recomendación.** Documentar con la fuente qué significa una ausencia, añadir a la puerta de calidad un control de cobertura temporal y un campo `meses_observados` en los agregados, y declarar los municipios sin registros.

### IN-03 · Menor · Capturas diarias redundantes

- **Descripción.** Las 21 capturas de SNIIV tienen 21 hashes distintos, pero **su contenido es idéntico**: mismas claves y mismos valores, y solo cambia el orden de los registros. La captura diaria no aporta información nueva desde el 2026-11-09, ocupa unos 9.5 MB en el repositorio y no hay detección de cambios. Como `id_fila_bronce` es la posición en el archivo, el identificador de un mismo registro cambia de una captura a otra.
- **Evidencia.** E12; [`registro_sniiv.py`](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/extractores/registro_sniiv.py); [`ejecutar.py` L61](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/pipeline/ejecutar.py#L61).
- **Requisito afectado.** ISO/IEC 25012, trazabilidad y eficiencia; ISO/IEC 25010, eficiencia de desempeño.
- **Impacto.** Bajo: la serie «programada» demuestra que la captura corre, pero no mide frescura de datos. Esto no invalida ningún resultado.
- **Recomendación.** Calcular un hash canónico del contenido (con los registros ordenados), conservar solo capturas con cambios y registrar «sin cambios» en la bitácora.

### IN-04 · Menor · Robustez del extractor y orden del workflow

- **Descripción.** Los extractores hacen una sola petición, sin reintentos ni pausa, y no analizan `robots.txt` en el código (el análisis es manual y está documentado). El User-Agent de los tres lleva el contacto sin completar (`completar-correo`). En el workflow, «Guardar captura» (commit y push) va **antes** de «Validar Registro SNIIV»; así, una validación fallida deja la captura ya publicada, y no hay `concurrency` ni sincronización previa al push.
- **Evidencia.** [`registro_sniiv.py` L10 y L14](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/extractores/registro_sniiv.py#L10-L14), [`shf.py` L7](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/extractores/shf.py#L7), [`inventario_sniiv.py` L11](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/extractores/inventario_sniiv.py#L11), [`captura.yml` L31-L39](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/.github/workflows/captura.yml#L31-L39); ejecuciones 3 y 6 (el paso «Validar» falla después de «Guardar captura»).
- **Requisito afectado.** PDF, «Captura funcionando» (el extractor ético del Kit es el punto de partida); ISO/IEC 25010, fiabilidad.
- **Impacto.** Menor: no se observaron bloqueos de las fuentes y el bronce conserva lo que llegó. Un reintento podría haber evitado el fallo del 18-nov, pero eso **no está demostrado**.
- **Recomendación.** Añadir reintentos limitados con espera exponencial y pausa entre peticiones, completar el contacto del User-Agent, validar antes de guardar o marcar el commit con el resultado, y agregar `concurrency`.

### IN-05 · Menor · Pruebas y linter

- **Descripción.** La cobertura medida es de 31 % (`pipeline/ejecutar.py` 20 %, `estadistica.py` 0 %, extractores 0 %); la validación está al 100 %. Dos de las 12 pruebas fallan en un clon limpio porque dependen de que se haya ejecutado antes el pipeline. La prueba del cruce espacial es **circular**: valida puntos derivados de los mismos polígonos, así que no puede fallar salvo que la geometría sea inválida. El linter del CI solo revisa `pipeline` y `tests`, y hay 10 hallazgos de estilo en `extractores/`.
- **Evidencia.** E2, E3 y E6; [`test_analisis_e1.py` L10](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/tests/test_analisis_e1.py#L10); [`e1-calidad.yml` L31](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/.github/workflows/e1-calidad.yml#L31).
- **Requisito afectado.** ISO/IEC 25010, mantenibilidad y fiabilidad. El CI cubre lo que el PDF pide (pruebas, linter y puerta de datos).
- **Impacto.** Menor: el CI genera los datos antes de probar, y la reproducción de E1 documenta el orden correcto.
- **Recomendación.** Preparar los datos en una *fixture*, añadir pruebas del extractor con respuestas simuladas, ampliar el linter a todo el repositorio y fijar un umbral de cobertura.

### IN-06 · Menor · Documentación contradictoria o desactualizada

- **Descripción.** (a) La tasa de éxito aparece como 84.62 % en `MATRIZ_REQUISITOS.md` y en `PLAN_SQA.md`, y como 85.71 % (12 de 14) en `SEGURIDAD_Y_CONFIABILIDAD.md`. (b) `docs/E1/ENTREGA.md` dice que faltan `gitleaks` y el respaldo, y `SEGURIDAD_Y_CONFIABILIDAD.md` los documenta como hechos. (c) `docs/E2/ENTREGA.md` (L7) y `relatoria-E2.md` (L35) dicen que la etiqueta `e2` es anterior a los commits recientes, pero hoy apunta al último commit. (d) `INFORME_ESTADISTICA_E2.md` tiene la codificación rota (por ejemplo «AnÃ¡lisis») y remite a `RESULTADOS_ESTADISTICA_E2.zip`, que el propio equipo eliminó.
- **Evidencia.** [`MATRIZ_REQUISITOS.md` L12](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E1/MATRIZ_REQUISITOS.md#L12), [`SEGURIDAD_Y_CONFIABILIDAD.md` L9](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E1/SEGURIDAD_Y_CONFIABILIDAD.md#L9), [`E1/ENTREGA.md` L32](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E1/ENTREGA.md#L32), [`E2/ENTREGA.md` L7](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E2/ENTREGA.md#L7), [`INFORME_ESTADISTICA_E2.md` L1 y L63](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E2/estadistica/INFORME_ESTADISTICA_E2.md#L63); etiqueta `e2` consultada por la API de GitHub.
- **Requisito afectado.** ISO/IEC 25012, comprensibilidad; la rúbrica pide documentos específicos, honestos y verificables.
- **Impacto.** Menor: los contenidos son honestos, pero un lector puede llevarse cifras distintas según el documento. Además, mover una etiqueta ya publicada debilita su valor como versión entregada.
- **Recomendación.** Unificar la cifra con su fecha de corte, reconciliar `E1/ENTREGA.md`, actualizar los textos sobre la etiqueta, corregir la codificación a UTF-8 y evitar mover etiquetas.

### IN-07 · Menor · Diccionario de la capa Oro desactualizado

- **Descripción.** El diccionario documenta 4 de las 10 columnas de `registros_trimestrales` y 5 de las 16 de `comparacion_municipal`, no incluye las columnas de linaje y no menciona `variables_analiticas_sniiv`, `comparacion_modelos`, `pronosticos_exploratorios` ni `diagnostico_ampliado`.
- **Evidencia.** [`diccionario_oro.md`](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E1/diccionario_oro.md) frente a las columnas de la Plata y el Oro generados en E4 y E5.
- **Requisito afectado.** PDF, E1: capa Oro con diccionario de datos; ISO/IEC 25012, comprensibilidad.
- **Impacto.** Menor: el diccionario era correcto en E1 y quedó atrás con las columnas de linaje de E2.
- **Recomendación.** Generar el diccionario desde el pipeline, como hace nuestro proyecto, y probar que cubre todas las columnas.

### IN-08 · Menor · Registros PSP

- **Descripción.** `calidad/defectos-individual.csv` y `tiempo-individual.csv` no usan las columnas del Kit (tipo de defecto PSP, fase de introducción y de eliminación, minutos de corrección); tienen 2 defectos y 7 filas de tiempo, todas de E0. No hay tiempos de E1 ni de E2, y los defectos de E1 usan otros identificadores (DEF-001 y DEF-002) que los del PSP (D-01 y D-02). El equipo declara que los tiempos son estimaciones retrospectivas y que el registro no está completo.
- **Evidencia.** [`defectos-individual.csv`](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/calidad/defectos-individual.csv), [`tiempo-individual.csv`](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/calidad/tiempo-individual.csv), [`docs/psp.md`](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/psp.md), [`PLAN_SQA.md` §6](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E1/PLAN_SQA.md).
- **Requisito afectado.** PDF, «Arranque de calidad» (registros individuales de defectos y tiempo).
- **Impacto.** Menor: afecta a la medición del proceso, no al producto. La honestidad del registro es una fortaleza.
- **Recomendación.** Adoptar el formato del Kit, unificar los identificadores y registrar las actividades de E1 y E2 con la etiqueta de estimación cuando corresponda.

### IN-09 · Menor · Seguridad operativa

- **Descripción.** `gitleaks` se ejecutó una vez, a mano, y no forma parte del CI; el respaldo del bronce es una sola copia local en el directorio personal; y el contenedor de desarrollo arranca Streamlit con CORS y XSRF desactivados.
- **Evidencia.** [`e1-calidad.yml`](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/.github/workflows/e1-calidad.yml), [`SEGURIDAD_Y_CONFIABILIDAD.md` L53](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E1/SEGURIDAD_Y_CONFIABILIDAD.md#L53), [`devcontainer.json` L22](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/.devcontainer/devcontainer.json#L22).
- **Requisito afectado.** Rúbrica E1, «Seguridad» (`gitleaks` y `pip-audit` sin hallazgos abiertos; respaldo probado).
- **Impacto.** Menor: no se observaron secretos, el bronce es público y el ajuste afecta solo al entorno de desarrollo.
- **Recomendación.** Añadir `gitleaks` al CI, mantener una segunda copia verificable del bronce y quitar las dos opciones del contenedor salvo que sean imprescindibles.

## 7. Fortalezas comprobadas

| ID | Fortaleza | Evidencia |
|---|---|---|
| F-01 | **Reproducibilidad del pipeline:** en un entorno nuevo da exactamente lo documentado y en pocos segundos | E4, E5 |
| F-02 | **Métricas ISO/IEC 25012 publicadas, reproducibles:** 0 diferencias al regenerarlas | E8 |
| F-03 | **Resultados estadísticos reproducibles:** el ANOVA y la confirmación se recomputan desde los datos y la nueva ejecución mantiene los resultados | E9, E10 |
| F-04 | **Linaje por hash verificado:** los hashes de los tres productos Oro y de las tres capturas de INEGI coinciden con sus archivos | E11 |
| F-05 | **CI completo y estable:** Ruff, `pip-audit`, pipeline, análisis y pruebas en cada push y pull request; 16 de 16 en verde | E13 |
| F-06 | **Puerta de calidad con cuarentena y motivo**, y pruebas negativas | `pipeline/validacion.py`; E6 |
| F-07 | **Documentación ética sólida:** cuatro consultas de `robots.txt`, términos y licencias por fuente, y la limitación de la licencia de SHF declarada sin atribuirle una que no se verificó | [`etica-datos.md`](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/etica-datos.md) |
| F-08 | **Honestidad sobre los límites:** declara el objetivo de fiabilidad no alcanzado, las bandas no calibradas, la autocorrelación residual y la fecha de SHF no verificada, y no reclama certificación | `CIERRE_E1.md`, `LINAJE.md` §8 |

Además, los objetivos de calidad de E0 sobre completitud (≥ 98 %) y trazabilidad (100 % de archivos con metadatos) **se cumplen** según esta auditoría (SNIIV al 100 % de celdas y 25 de 25 archivos de bronce con metadatos), aunque la documentación del equipo todavía los marca como pendientes.

## 8. Verificación de las sospechas previas

| Sospecha | Resultado | Evidencia |
|---|---|---|
| Etiqueta `e2` desactualizada | **Descartada como estado actual.** La etiqueta (anotada, creada el 2026-11-23 a las 08:19 UTC) apunta a `65c80cc`, el último commit. Lo que sigue desactualizado es el **texto** de dos documentos (IN-06) | API de GitHub (`git/ref/tags/e2` y `commits/e2`) |
| Evaluaciones ISO incompletas | **Confirmada como limitación declarada** de su entregable E2: de las 8 características, solo la eficiencia tiene una métrica; de ISO/IEC 25012 se miden 3 atributos (completitud, unicidad de fila y presencia de origen y hash). El propio informe lo reconoce. No altera el dictamen sobre el estado E1 (sección 9) | [`INFORME_CALIDAD_E2.md`](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E2/calidad/INFORME_CALIDAD_E2.md); E8 |
| Ausencia de Plata y Oro en el ZIP | **Justificada.** `.gitignore` excluye a propósito Plata, Oro y cuarentena; se regeneran con `python -m pipeline.ejecutar` en 3 s y coinciden con lo documentado. La consecuencia real es de reproducibilidad: 2 pruebas fallan en un clon limpio (IN-05) | [`.gitignore` L7-L14](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/.gitignore#L7-L14); E3, E4 |

## 9. Observaciones sobre los entregables E2 del equipo auditado (fuera del alcance, sin severidad)

- **Evaluación ISO propia incompleta**, declarada por el equipo (sección 8).
- **Cruce espacial circular:** el equipo lo documenta como «validación geométrica interna», no como vinculación de sus datos con los polígonos.
- **Fracción 2⁴⁻¹ seleccionada del factorial completo**, como lo declaran, no una campaña independiente.
- **Experimentos con buena trazabilidad:** E9 y E10 los reproducen; los diagnósticos de normalidad con reservas (Shapiro p ≈ 0.04 y 0.02) están declarados.

## 10. Limitaciones de la verificación

- **No verificables:** la herramienta `gitleaks` (no instalada), el respaldo del bronce (copia local del autor), los colaboradores y docentes del repositorio y los registros detallados de las ejecuciones de Actions (la API devuelve 401 o requiere sesión).
- **No ejecutados:** las capturas contra las fuentes reales (para no cargar las API de terceros ni cambiar su bronce) ni el contraste de exactitud con la API viva de SNIIV.
- **Entorno distinto al del CI:** las pruebas corrieron con Python 3.13 y no con 3.11.
- **Tablero:** se verificó el estado de un instante y no su disponibilidad en el tiempo.
- **Alcance de la IA:** el informe se elaboró con asistencia de IA; no cuenta como revisión independiente de IA; A y B lo revisaron en conjunto (sección 13).
- **Sin pruebas destructivas:** no se atacó ni se estresó ningún sistema del equipo auditado.

## 11. Recomendaciones priorizadas

| Prioridad | Acción | Hallazgos |
|---|---|---|
| **1** (antes de E3) | Calcular y publicar MTBF, MTTR y disponibilidad, versionar la bitácora de ejecuciones y documentar el incidente del 18-nov | IN-01 |
| **2** | Diagnosticar y documentar la semántica de las ausencias de SNIIV, y añadir el control de cobertura temporal y `meses_observados` | IN-02 |
| **2** | Reintentos y contacto del User-Agent en los extractores; validar antes de guardar; deduplicar por contenido | IN-03, IN-04 |
| **2** | Pruebas con *fixtures*, cobertura mínima y linter en todo el repositorio | IN-05 |
| **3** | Reconciliar cifras y textos, regenerar el diccionario, adoptar el formato PSP del Kit y reforzar la seguridad operativa | IN-06 a IN-09 |

## 12. Dictamen final

El observatorio inmobiliario de Colima, en su estado E1, **cumple de forma comprobada** con la reproducibilidad, el linaje por hash, el CI y la honestidad sobre sus límites, y **cumple parcialmente** con el resto de las características de ISO/IEC 25010. **No alcanza** su objetivo de disponibilidad de la captura y no ha diagnosticado la completitud temporal de SNIIV. No se identificó ningún defecto crítico. Este dictamen **no es una certificación ISO ni el Sello TDL**, y su estado de revisión, aprobación y envío se detalla en la sección 13.

## 13. Revisión conjunta, aprobación y envío

Esta sección separa lo que consta en GitHub de lo que se comunica por otros medios.

| Hito | Estado | Evidencia | Observación |
|---|---|---|---|
| Informe realizado | Hecho | [`auditoria-cruzada-realizada.md`](auditoria-cruzada-realizada.md) y [`evidencia/auditoria_cruzada/`](evidencia/auditoria_cruzada/) | Resultado vigente: 0 críticos, 1 mayor y 8 menores |
| Revisión conjunta de A y B | Hecha | Tiempo registrado en los PSP: unos 45 min por integrante, **aproximados, no cronometrados** | No hay acta; el dato lo comunica A. Eimy debe confirmar el suyo |
| Aprobación de B | **Real, en GitHub** | [Aprobación de `eimymuz` en el PR #33](https://github.com/Leslie581/tdl-turistico-colima/pull/33#pullrequestreview-6027166554), enviada el 2026-11-23 a las 18:24:26 UTC (12:24 hora local); el PR lo fusionó `Leslie581` a las 18:29:51 UTC | El PR no tiene comentarios; no hay firmas |
| Informe enviado al equipo externo | **Hecho, según A** | No hay constancia en el repositorio | El canal y la fecha no están registrados |
| **Recepción confirmada** | **PENDIENTE** | — | No hay respuesta ni acuse del equipo externo |
| Respuesta y revalidación del equipo externo | **PENDIENTE** | — | No hay respuesta |

**Informe enviado no equivale a recepción confirmada.** Mientras el equipo externo no responda, la recepción se mantiene como pendiente y no se asume.

## Anexo A. Cómo reproducir las comprobaciones

1. Descargar el ZIP de `main` (o clonar el commit `65c80cc`) en un directorio nuevo y crear un entorno virtual con Python 3.13.
2. `pip install -r requirements-e1.txt pip-audit pytest-cov`
3. `ruff check pipeline tests` y `ruff check .`
4. `pytest -q` (clon limpio), luego `python -m pipeline.ejecutar`, `python -m pipeline.ejecutar_analisis` y `pytest -q --cov=pipeline --cov=extractores`
5. `pip-audit -r requirements-e1.txt`
6. `python -m calidad.evaluacion_e2` y comparar con `resultados/calidad_e2/metricas_iso25012.json`
7. `python -m experimentos.e2_estadistica` (escribe en `resultados/estadistica_e2/`; hacerlo en una copia)
8. Historial de Actions: `GET /repos/chareyesjaramillo17801-rgb/trusted-data-lab-colima/actions/runs`, y para los pasos de cada ejecución, `.../actions/runs/{id}/jobs`.
