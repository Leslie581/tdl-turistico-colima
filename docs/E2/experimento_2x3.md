# Experimento factorial 2³ de E2: procedimiento de ejecución y medición

Corte 2026-11-21 · Redacta: integrante B (Eimy). Diseño heredado de [`docs/E1/ruta_experimento_e2.md`](../E1/ruta_experimento_e2.md) (ruta ingeniería) y de [`laboratorio/experimento/matriz.py`](../../laboratorio/experimento/matriz.py). Código: [`laboratorio/experimento/arnes.py`](../../laboratorio/experimento/arnes.py). Pruebas: [`tests/test_arnes_experimento.py`](../../tests/test_arnes_experimento.py).

**Estado:** el arnés está implementado y probado. **Todavía no hay corridas oficiales.** Los tiempos del §6 son de un piloto de calibración: no son datos del experimento y no entran en el análisis. Este documento no contiene resultados estadísticos.

## 1. Objetivo
Determinar qué configuración de nuestro propio procesamiento da **menor tiempo** con **cero errores**, sobre una copia local de las capturas reales del DENUE. La pregunta es causal **sobre el procesamiento**, no sobre el turismo: asignamos los niveles y aleatorizamos el orden.

## 2. Unidad experimental y tarea medida
Una **corrida** procesa la carga completa (§5) con un tratamiento. La tarea es el tramo bronce → plata del DENUE del pipeline real, `pipeline.plata_denue.procesar_una_captura`, que hace por cada captura:
- integridad por SHA-256;
- privacidad (R-E05);
- esquema (R-E01);
- completitud (R-E02);
- reglas por registro y transformación a las columnas de plata.

Después, la plata se escribe en el formato elegido y se vuelve a leer.

Quedan fuera la deduplicación diaria y la validación pandera final (`validar_plata`): con copias repetidas de la carga, la unicidad (fecha, CLEE) no se cumpliría.

## 3. Factores y niveles
Cada factor cambia el código que se ejecuta, no solo una etiqueta. El registro guarda evidencia de cada uno en `evidencia_factores`.

| Factor | −1 | +1 | Cómo actúa | Evidencia registrada |
|---|---|---|---|---|
| A `procesos` | 1: secuencial en el proceso principal | 4: `ProcessPoolExecutor(max_workers=4)` con contexto `spawn`, una tarea por captura | Reparte las capturas entre procesos; incluye arrancar los trabajadores y devolver los resultados | `pids_distintos`, `trabajo_fuera_del_proceso_principal` |
| B `analizador` | `json`: `json.loads` de la biblioteca estándar (el de E1) | `orjson`: `orjson.loads` 3.13.0 | Convierte los bytes del bronce en objetos de Python dentro de `_cargar_captura` | `analizador` (función usada) |
| C `formato` | `csv`: `to_csv` / `read_csv` | `parquet`: `to_parquet` / `read_parquet` con pyarrow 26.0.1 | Escribe y relee la plata | `cabecera_salida`, `es_parquet`, `bytes_salida` |

Para que el factor B fuera intercambiable, `pipeline/plata_denue.py` recibe el analizador como parámetro; por omisión sigue usando `json`. La plata y el oro regenerados con el cambio son idénticos byte a byte a los anteriores (comprobado el 2026-11-21).

## 4. Variables de respuesta (fijadas antes de correr)
- **Principal: `tiempo_s`.** Segundos de pared medidos con `time.perf_counter` desde el inicio del procesamiento hasta terminar de leer la salida (procesar + escribir + leer). Se registran también las partes por separado. La comparación canónica de la relectura se mide aparte (`tiempo_verificacion_s`) y no forma parte de la respuesta.
- **Secundaria: `tasa_error`**, igual a `capturas_con_error / capturas`. Una captura cuenta como error si:
  - `PUERTA`: la puerta de calidad rechaza el lote (integridad, JSON inválido, esquema, completitud o privacidad);
  - `EXCEPCION`: su procesamiento lanza una excepción no prevista;
  - `SALIDA`: sus filas no se recuperan idénticas al releer el archivo de salida.

  Los registros que una regla manda a cuarentena son calidad del dato, no errores de procesamiento, y se informan aparte (`registros_en_cuarentena`).
- **Previsión (observación O1 de la Auditoría 8):** sobre copias íntegras se espera `tasa_error = 0` en todas las corridas oficiales. Si es así, la tasa no se analiza con ANOVA porque no tiene variación, y se informa como restricción cumplida. El arnés sí sabe contar errores: lo demuestran las pruebas con fallos sintéticos (`--fallos`), que nunca se usan en corridas oficiales.

## 5. Carga de trabajo
- **Qué es:** copias byte a byte de todas las capturas reales de `data/bronce/denue/` (`*_02_BuscarAreaAct.json`, con sus fichas y el `_01_Cuantificar`), repetidas **16 veces** (`COPIAS = 16`, fijado con el piloto del §6).
- **Dónde:** en un directorio temporal **fuera del repositorio**, que se borra al terminar.
- **Naturaleza:** es una **carga sintética de rendimiento** (los datos se repiten). No es dato analítico y no llega a plata ni a oro.
- **Trazabilidad:** el manifiesto (`carga`) guarda el número de copias y de capturas y el `sha256_capturas_fuente`.
- **Protección de los originales:** el arnés comprueba la huella SHA-256 del bronce antes y después de cada bloque; si cambiara, invalida el bloque.
- **Sin red:** no se hace ninguna conexión, y una prueba lo verifica.

## 6. Calibración (piloto del 2026-11-21; no son datos del experimento)
Pilotos con `--piloto`, escritos fuera del repositorio, sobre el código sin confirmar. Equipo: Windows 11, Python 3.14.3, 12 CPU lógicas. Tiempos en segundos (`tiempo_s`):

| Copias | Capturas | T1 1/json/csv | T4 1/orjson/parquet | T5 4/json/csv | T8 4/orjson/parquet |
|---|---|---|---|---|---|
| 1 | 14 | 0.78 | 0.77 | 4.11 | 4.30 |
| 8 | 112 | 6.19 | 5.44 | 6.18 | 5.90 |
| 24 | 336 | 18.79 | 17.07 | 10.60 | 9.49 |

**Qué dice el piloto:**
- Con poca carga domina el arranque de los trabajadores (`spawn`); hacia 8 copias los dos niveles de A se igualan, y con 24 el paralelismo ya rinde.
- Se fijan 16 copias (224 capturas) para que el procesamiento, y no el arranque, sea la parte principal del tiempo, con bloques de unos dos minutos.
- La primera corrida de una sesión sin calentamiento salió más lenta (1.97 s frente a 0.77 s en el mismo tratamiento). Por eso cada bloque hace **una corrida de calentamiento no registrada** antes de las 8 oficiales.

Este piloto no se usa para estimar efectos.

## 7. Aleatorización, replicación y bloqueo
- **Aleatorización:** orden de las 8 corridas permutado dentro de cada bloque con la semilla fija 20261113, generado por `matriz.py`. El arnés ejecuta exactamente ese orden y se prueba que lo hace.
- **Replicación:** 2 réplicas completas (16 corridas); cada tratamiento aparece una vez por bloque (`replica` = 1 o 2).
- **Bloqueo:** el bloque es la **sesión de ejecución en un día distinto** (`dia_1`, `dia_2`) en el mismo equipo (`equipo_id`, un hash del nombre de la máquina, que no se publica). Las fuentes reales de variación que se bloquean son el estado del equipo (otros procesos, temperatura, caché del disco) y la fecha. Se registran `fecha_local` y `entorno` para comprobarlo.
- **Calendario previsto:** `dia_1` el 2026-11-21 o el 2026-11-22 y `dia_2` el día siguiente, siempre antes de la entrega del 2026-11-23.

## 8. Registro de cada corrida
Archivo: `laboratorio/experimento/resultados/corridas_2x3.jsonl`, una línea JSON por corrida que se agrega al terminar. Cada línea trae:
- **Diseño:** bloque, réplica, orden en el bloque, tratamiento, niveles y códigos ±1.
- **Mediciones:** tiempos (total y por parte), capturas, capturas con error, tasa de error, registros de salida, registros en cuarentena, los errores con su tipo y regla, y la evidencia de cada factor.
- **Contexto:** `inicio_utc`, `fin_utc`, `fecha_local`, semilla, `commit`, `codigo_modificado`, `version_arnes`, entorno (Python, sistema, CPU, versiones de pandas, numpy, pyarrow, orjson y pandera), manifiesto de la carga y si hubo calentamiento.

**Fallos:** una corrida fallida se registra con `estado: "fallo"`, `tiempo_s: null` y el mensaje del error. Nunca se rellena un valor.

**Reglas para las corridas oficiales:**
- Exigen el código confirmado en git (`codigo_modificado: false`).
- No admiten fallos sintéticos.
- Un piloto no puede escribir en el archivo oficial.
- Un tratamiento ya registrado no se repite.

## 9. Cómo reproducir
```bash
python -m pip install -r requirements.txt -r requirements-lab.txt      # incluye orjson 3.13.0 y pyarrow 26.0.1
python -m pytest -q tests/test_arnes_experimento.py tests/test_experimento_e2.py
# corridas oficiales (código confirmado; una sesión por día)
python -m laboratorio.experimento.arnes --bloque dia_1
python -m laboratorio.experimento.arnes --bloque dia_2
# piloto o ensayo (no va al archivo oficial)
python -m laboratorio.experimento.arnes --bloque dia_1 --piloto --salida /tmp/piloto.jsonl --copias 2 --permitir-cambios
```

## 10. Limitaciones conocidas
- **Un solo equipo:** los resultados valen para esta máquina (12 CPU lógicas, Windows). En Linux el arranque de los trabajadores con `spawn` cuesta distinto. Se fuerza `spawn` en ambos sistemas para que el tratamiento sea el mismo.
- **La carga repite datos reales:** mide rendimiento, no calidad del dato.
- **La tarea excluye** la deduplicación diaria y `validar_plata` (§2).
- **Tasa de error:** probablemente constante en cero (§4).
- **Fuera de esta fase:** el ANOVA, el diseño de dos factores, la comparación 2⁴ frente a 2⁴⁻¹ y la corrida de confirmación (fases siguientes de E2).
