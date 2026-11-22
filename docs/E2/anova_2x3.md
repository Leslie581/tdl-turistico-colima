# ANOVA del experimento factorial 2³ con bloques (E2)

Corte 2026-11-22 · Integrante B (Eimy), con asistencia de Claude Code. El diseño y la ejecución están en [`experimento_2x3.md`](experimento_2x3.md).
- **Código:** [`laboratorio/experimento/anova.py`](../../laboratorio/experimento/anova.py), que se ejecuta con `python -m laboratorio.experimento.anova`.
- **Pruebas:** [`tests/test_anova_experimento.py`](../../tests/test_anova_experimento.py).
- **Salidas:** [`laboratorio/experimento/resultados/anova/`](../../laboratorio/experimento/resultados/anova/).

## 1. Datos y modelo
- **Datos:** las 16 corridas oficiales de [`corridas_2x3.jsonl`](../../laboratorio/experimento/resultados/corridas_2x3.jsonl), SHA-256 `f5167a79…6ff31811`, del commit `7309fed`. Son 8 tratamientos × 2 bloques (`dia_1` el 2026-11-21 y `dia_2` el 2026-11-22). No se eliminó, sustituyó ni repitió ninguna observación, y los pilotos de calibración no entran.
- **Respuesta:** `tiempo_s`. La `tasa_error` vale 0 en las 16 corridas: no tiene variación, así que no se analiza y se informa como restricción cumplida.
- **Modelo de efectos fijos:** `tiempo_s ~ C(bloque, Sum) + x_proc * x_anal * x_form`, con A = procesos (1 / 4), B = analizador (json / orjson) y C = formato (csv / parquet), codificados en −1 / +1. Los nombres `x_*` evitan el choque del factor C con `C()` de patsy.
- **Matriz del diseño:** 16 × 9 de rango completo (9). Es ortogonal, así que las sumas de cuadrados de tipo I, II y III coinciden.
- **Grados de libertad:** 1 para el bloque, 7 para los tratamientos (3 efectos principales, 3 interacciones dobles y 1 triple) y 7 para el residuo; 15 en total.

## 2. Tabla ANOVA (α = 0.05)
| Fuente | gl | SC | CM | F | p | η² parcial |
|---|---|---|---|---|---|---|
| Bloque | 1 | 7.000 | 7.000 | 1.671 | 0.237 | 0.193 |
| A procesos | 1 | 11.064 | 11.064 | 2.641 | 0.148 | 0.274 |
| B analizador | 1 | 0.218 | 0.218 | 0.052 | 0.826 | 0.007 |
| C formato | 1 | 12.351 | 12.351 | 2.949 | 0.130 | 0.296 |
| AB | 1 | 3.506 | 3.506 | 0.837 | 0.391 | 0.107 |
| AC | 1 | 0.427 | 0.427 | 0.102 | 0.759 | 0.014 |
| BC | 1 | 1.974 | 1.974 | 0.471 | 0.515 | 0.063 |
| ABC | 1 | 0.103 | 0.103 | 0.025 | 0.880 | 0.004 |
| Residuo | 7 | 29.323 | 4.189 | | | |
| Total | 15 | 65.965 | | | | |

R² = 0.555. **Ningún término es significativo al 5 %.**

## 3. Efectos estimados
El efecto es la media en el nivel +1 menos la media en el nivel −1. El error estándar es 1.023 s para todos y el intervalo de confianza del 95 % usa t con 7 gl. Archivo: [`efectos.csv`](../../laboratorio/experimento/resultados/anova/efectos.csv).

| Término | Efecto (s) | IC 95 % | % de la media (7.362 s) |
|---|---|---|---|
| A procesos (4 frente a 1) | −1.663 | [−4.083, 0.757] | −22.6 % |
| B analizador (orjson frente a json) | −0.233 | [−2.653, 2.187] | −3.2 % |
| C formato (parquet frente a csv) | −1.757 | [−4.177, 0.663] | −23.9 % |
| AB | −0.936 | [−3.356, 1.484] | −12.7 % |
| AC | −0.327 | [−2.746, 2.093] | −4.4 % |
| BC | −0.703 | [−3.122, 1.717] | −9.5 % |
| ABC | +0.161 | [−2.259, 2.581] | +2.2 % |

- **Potencia:** con CME = 4.189 y 7 gl, un efecto solo resulta significativo si supera **2.42 s** en valor absoluto. Para detectarlo con un 80 % de potencia haría falta un efecto de unos **3.34 s**. El diseño no tiene potencia para efectos del tamaño observado (de 1.7 a 1.8 s).
- **Gráficas:** [`efectos_principales.png`](../../laboratorio/experimento/resultados/anova/figuras/efectos_principales.png) e [`interacciones.png`](../../laboratorio/experimento/resultados/anova/figuras/interacciones.png). Las líneas de AB se cruzan (orjson es más lento con 1 proceso y más rápido con 4), pero AB tiene p = 0.39: no hay evidencia de interacción.

## 4. Supuestos
Detalle en [`resumen.json`](../../laboratorio/experimento/resultados/anova/resumen.json).

| Supuesto | Prueba o diagnóstico | Resultado | Lectura |
|---|---|---|---|
| Normalidad | Shapiro-Wilk de los residuos; [Q-Q](../../laboratorio/experimento/resultados/anova/figuras/qq_residuos.png) | W = 0.986, p = 0.994 | Sin indicios en contra |
| Homogeneidad | Brown-Forsythe (Levene centrado en la mediana) de los residuos por nivel; [residuos frente a ajustados](../../laboratorio/experimento/resultados/anova/figuras/residuos_vs_ajustados.png) | procesos: **p = 0.0008** (varianza 3.61 con 1 proceso frente a 0.58 con 4); analizador: p = 0.47; formato: p = 0.48 | **Falla para procesos**: las corridas secuenciales son mucho más variables |
| Independencia | Durbin-Watson en el orden de ejecución; Spearman entre residuo y orden dentro de cada bloque; [residuos frente al orden](../../laboratorio/experimento/resultados/anova/figuras/residuos_vs_orden.png) | DW = 1.77; `dia_1`: ρ = 0.67, p = 0.071; `dia_2`: ρ = −0.10, p = 0.82 | Sin autocorrelación clara. En `dia_1` hay una tendencia ascendente casi significativa (las corridas posteriores salieron más lentas) |
| Atípicos | Residuo studentizado externo; distancia de Cook | Máximo de \|r\| = 2.36 (ninguno pasa de 3); Cook = 0.48 en las corridas 5 y 16 (las dos réplicas de T4) frente al umbral 4/n = 0.25 | T4 es influyente: sus réplicas difieren en 3.65 s. **No se elimina** |
| Aditividad bloque × tratamiento | Prueba de 1 gl de Tukey | F(1, 6) = 0.06, p = 0.81 | Sin indicios de no aditividad |
| Escala | Perfil de Box-Cox | λ̂ = −1.24, IC 95 % [−3.37, 1.31] | La escala original (λ = 1), la logarítmica (0) y la recíproca (−1) son todas compatibles: los datos no permiten elegir |

**Limitaciones de las pruebas con este diseño:**
- **Grados de libertad:** con 2 réplicas, los 16 residuos solo tienen 7 gl, y dentro de cada tratamiento son pares de signo opuesto. Por eso Shapiro-Wilk tiene poca potencia, y Brown-Forsythe por nivel compara en realidad 4 diferencias entre réplicas por nivel (su valor p es aproximado).
- **Prueba no identificable:** la homogeneidad por bloque no se puede probar, porque los residuos de un bloque son los del otro con el signo cambiado. Se omitió.
- **Palanca:** es igual en todas las corridas (h = 0.5625).

## 5. Alternativas ante la heterogeneidad y sensibilidad
Archivo: [`sensibilidad.csv`](../../laboratorio/experimento/resultados/anova/sensibilidad.csv). Valores p:

| Término | MCO con `tiempo_s` (principal) | log(tiempo) | 1/tiempo (velocidad) | MCP, varianza por nivel de procesos | Permutación dentro de bloques (20,000) |
|---|---|---|---|---|---|
| Bloque | 0.237 | 0.225 | 0.209 | 0.098 | — |
| A procesos | 0.148 | 0.153 | 0.152 | 0.148 | 0.146 |
| B analizador | 0.826 | 0.784 | 0.705 | 0.826 | 0.819 |
| C formato | 0.130 | 0.101 | 0.074 | 0.130 | 0.128 |
| AB | 0.391 | 0.315 | 0.238 | 0.391 | 0.386 |
| AC | 0.759 | 0.658 | 0.546 | 0.759 | 0.745 |
| BC | 0.515 | 0.408 | 0.304 | 0.515 | 0.504 |
| ABC | 0.880 | 0.934 | 0.710 | 0.880 | 0.876 |

- **La conclusión no depende de la escala, de los pesos ni del supuesto de normalidad:** ningún término es significativo al 5 % con ningún método.
- **La prueba de permutación** reproduce la aleatorización real: permuta las respuestas dentro de cada bloque, con la semilla 20261122. No supone normalidad, pero sí que las respuestas sean intercambiables bajo la hipótesis nula, algo que la heterogeneidad debilita.
- **Modelo reducido, decidido después de ver la tabla:** con solo los efectos principales y el bloque (11 gl de residuo, CME = 3.21) da A p = 0.090, B p = 0.80 y C p = 0.076. Tampoco es significativo, y por haberse decidido *a posteriori* no sustituye al modelo planeado.

## 6. Descomposición del tiempo (exploratorio)
El arnés registra por separado el procesamiento y la escritura más la lectura. Este análisis no estaba planeado y se presenta solo como explicación.
- **Escritura más lectura:** el formato tiene un efecto **claro**: −0.762 s (parquet frente a csv), con p = 1.5 × 10⁻⁶. El formato sí cambia lo que debe cambiar.
- **Procesamiento:** el formato aparece con −0.995 s (p = 0.35), aunque el formato no interviene en esa fase, que ocurre antes de escribir. Ese valor es **ruido del equipo** que el diseño no logra separar. Por eso el efecto total del formato (−1.757 s) es mayor que su efecto mecánico (−0.76 s).

## 7. Interpretación
- **Evidencia estadística:** ninguna. Ni los efectos principales ni las interacciones son significativos al 5 %; los más cercanos son C formato (p = 0.13) y A procesos (p = 0.15).
- **Relevancia práctica:** los efectos estimados de A y C (unos −1.7 s, alrededor de −23 %) serían relevantes si se confirmaran. Sus intervalos de confianza incluyen el 0 y también mejoras de hasta unos 4 s. Que no sean significativos no demuestra que no haya efecto: el diseño tiene poca potencia (§3).
- **Bloqueo:** el bloque explica el 10.6 % de la suma de cuadrados total (`dia_2` es 1.32 s más lento en promedio), con p = 0.24. No es significativo. Aun así, conservarlo en el modelo es correcto porque formaba parte del diseño: quitarlo pasaría esa variación al residuo.
- **Ruido dominante:** la mayor parte de la variación está en el residuo (44 % de la SC). Las corridas secuenciales (1 proceso) caen en dos niveles, unos 5 s o unos 9–10 s, sin relación con el factor. La causa más probable es un estado del equipo que no se controló, como la gestión de energía o el turbo de la CPU, la sincronización de OneDrive u otros procesos.
- **Menor tiempo observado:** T8 (4 procesos, orjson, parquet), con una media de **4.633 s** (réplicas 4.312 y 4.954) e IC 95 % de la media de celda [1.21, 8.06]. La configuración de E1, T1 (1 proceso, json, csv), tiene una media de 8.126 s. La diferencia T1 − T8 es de 3.493 s (43.0 %), con IC 95 % [−1.35, 8.33] y p = 0.132.
- **No hay base para hablar de un óptimo estadístico:** los intervalos de las 8 celdas se solapan. T8 queda como **configuración candidata** para la confirmación (§9).

## 8. Limitaciones
- **Carga sintética repetitiva:** las 16 copias repiten las mismas capturas. Parquet comprime esa repetición (unos 50 KB frente a 11.9 MB de CSV), así que la ventaja de Parquet en escritura y lectura está **sobrestimada** respecto a datos sin repetición. La comparación CSV frente a Parquet vale para esta carga, no para datos reales distintos.
- **Un solo equipo** (Windows, 12 CPU lógicas) y arranque de procesos con `spawn`: el efecto de `procesos` depende de la máquina y del sistema operativo.
- **Dos réplicas** (7 gl de residuo) y heterogeneidad de varianza entre los niveles de procesos.
- **Commit registrado distinto entre bloques** (`8c09877` en `dia_1` y `2784148` en `dia_2`), con el código del arnés idéntico (verificado con `git diff 8c09877 2784148`, salvo resultados y PSP).
- **Respuesta secundaria:** la `tasa_error` es constante en 0, así que no se puede analizar.

## 9. Protocolo de confirmación (fijado antes de ejecutar; no se ha corrido)
**Qué se compara:** la candidata T8 (4 procesos, orjson, parquet) frente a la configuración de E1, T1 (1 proceso, json, csv).

**Condiciones:**
- Una sesión nueva, en el mismo equipo y con el mismo entorno virtual y las mismas versiones (las registra `entorno`).
- La misma carga: 16 copias, `sha256_capturas_fuente = b0789202f77d…`.
- Una corrida de calentamiento no registrada.
- Código confirmado en git.
- Equipo conectado a la corriente, sincronización de OneDrive en pausa y sin otras aplicaciones abiertas. Estas condiciones se anotan como medida para reducir el ruido identificado; no se cambia ningún factor.

**Diseño:** 6 corridas de T8 y 6 de T1 (12 en total), en orden aleatorizado con la semilla fija 20261123. Cada corrida usa `arnes.ejecutar_corrida`, igual que en el factorial. Los resultados van a un archivo **aparte**, `laboratorio/experimento/resultados/confirmacion_2x3.jsonl`; `corridas_2x3.jsonl` no se toca. Ejecutarlo requiere un pequeño ejecutor nuevo (fase siguiente).

**Criterios de aceptación** (los dos deben cumplirse):
1. **Predicción:** la media de las 6 corridas de T8 cae dentro del intervalo de predicción del 95 % del modelo factorial para la media de 6 corridas nuevas: 4.633 ± t₀.₉₇₅;₇·√(CME·(1/2 + 1/6)) = 4.633 ± 3.952, es decir, **[0.68, 8.58] s**. Advertencia: el intervalo no incluye la variación de un día nuevo (un bloque fuera del diseño), así que es optimista.
2. **Mejora frente a E1:** en la misma sesión, T8 debe ser más rápido que T1 según una prueba t de Welch unilateral al 5 %, con una mejora relativa (T1 − T8)/T1 de **al menos el 20 %**. Si se toma como desviación estándar √CME = 2.05 s y como diferencia los 3.49 s observados, la potencia con n = 6 por grupo es de alrededor de 0.86.

**Interpretación del resultado:** si se cumplen ambos criterios, T8 queda **confirmada como mejor que la configuración de E1 en este equipo y con esta carga**; no como óptimo global. Si no se cumplen, se informa igual, sin repetir corridas ni cambiar los criterios.

## 10. Reproducción
```bash
python -m pip install -r requirements.txt -r requirements-lab.txt
python -m laboratorio.experimento.anova           # regenera resultados/anova/ a partir de las 16 corridas
python -m pytest -q tests/test_anova_experimento.py
```
Los CSV y el JSON se reproducen byte a byte (verificado por las pruebas). Los PNG pueden variar con otra versión de matplotlib.
