# Experimento de dos factores: carga × procesos (ANOVA de dos vías)

Integrante B (Eimy), con asistencia de Claude Code. Diseño fijado el **2026-11-22, antes de las corridas oficiales** (commit `adf26fa`); corridas oficiales el mismo día (§5). Código: [`laboratorio/experimento/dos_factores.py`](../../laboratorio/experimento/dos_factores.py); pruebas: [`tests/test_dos_factores_experimento.py`](../../tests/test_dos_factores_experimento.py).

> **Rendimiento, no datos turísticos.** La respuesta es el tiempo que tarda el pipeline en procesar una carga técnica: copias byte a byte del bronce DENUE real, preparadas fuera del repositorio. Las copias no son observaciones turísticas nuevas y no entran en plata ni en oro.

## 1. Objetivo e hipótesis
**Objetivo:** medir cómo escala el tiempo de bronce → plata (procesar, escribir y releer) con el volumen de capturas, y si la paralelización con 4 procesos compensa su costo de arranque según la carga.

**Hipótesis (α = 0.05):**
- H₀A: la carga no cambia el tiempo medio.
- H₀B: el número de procesos no cambia el tiempo medio.
- H₀AB: el efecto de usar 4 procesos es el mismo en las tres cargas (no hay interacción).

La hipótesis de trabajo es que sí hay interacción. Con poca carga, arrancar 4 procesos con `spawn` debería costar más de lo que ahorra; con más carga, el ahorro debería crecer.

## 2. Factores y niveles
| Factor | Niveles | Cómo se aplica | Evidencia registrada en cada corrida |
|---|---|---|---|
| A: carga | 1×, 5× y 10× (copias del bronce: 14, 70 y 140 capturas) | `arnes.preparar_carga(…, copias)` | `capturas`, `carga_manifiesto` y `bytes_salida` |
| B: procesos | 1 y 4 | `arnes.ejecutar_corrida(…, procesos)` | `pids_distintos` y `trabajo_fuera_del_proceso_principal` |

**Por qué estos niveles son comparables:** todas las cargas son la misma tarea repetida (las mismas 14 capturas, `sha256_capturas_fuente` fijo), así que el trabajo crece de forma proporcional. En el piloto la salida CSV midió 0.76, 3.78 y 7.56 MB. Los dos niveles de procesos son los del 2³.

**Constantes:**
- Analizador `json` y formato `csv`: es la configuración de producción de E1 (T1).
  - El tamaño del CSV crece en proporción a la carga. Parquet comprime las copias repetidas (§9.2 de [`anova_2x3.md`](anova_2x3.md)), lo que habría mezclado su efecto con el de la carga.
  - En el 2³ ni el analizador ni el formato fueron significativos, así que fijarlos no esconde un efecto conocido.
- Máquina y entorno virtual, con las versiones que registra `entorno`.
- Definición de `tiempo_s` y de `tasa_error`, y reglas del pipeline y de la puerta de calidad: las de `arnes.ejecutar_corrida`, sin cambios.

## 3. Diseño, aleatorización y réplicas
- **Diseño:** factorial 3 × 2 en **bloques completos aleatorizados**, con 4 réplicas, es decir, 24 corridas.
- **Bloques:** cada bloque es un tramo consecutivo de la sesión con los 6 tratamientos. El bloqueo responde a una fuente de variación real ya identificada: la deriva del tiempo con el orden de ejecución observada en la confirmación del 2³ (pendiente de +0.46 s por corrida, §9.2 de `anova_2x3.md`).
- **Aleatorización:** dentro de cada bloque, con la semilla **20261124**. La matriz queda en [`resultados/matriz_3x2.csv`](../../laboratorio/experimento/resultados/matriz_3x2.csv).
- **Modelo:** `tiempo_s ~ C(bloque) + C(carga) * C(procesos)`, con codificación de suma y ANOVA tipo II (en un diseño equilibrado coincide con los tipos I y III). Grados de libertad: bloque 3, A 2, B 1, AB 2, residuo 15.
- **Calentamiento:** una corrida por nivel de carga antes de empezar, que no se registra.

**Análisis fijado antes de correr:**
1. ANOVA de dos vías sobre `tiempo_s`, con η² parcial y ω² parcial como tamaños de efecto.
2. Si AB es significativa, los efectos principales se interpretan a través de los **efectos simples**: 1 frente a 4 procesos en cada carga, con el CME del modelo y corrección de Holm para 3 comparaciones.
3. Supuestos:
   - Shapiro-Wilk de los residuos.
   - Brown-Forsythe entre las 6 celdas.
   - Durbin-Watson y residuo frente a secuencia.
   - Residuos studentizados mayores que 3 y distancia de Cook mayor que 4/n.
   - Box-Cox.
4. **Complementarios, fijados por el piloto (§4):** la razón de varianzas entre celdas fue de alrededor de 98 y el IC de Box-Cox excluyó λ = 1 e incluyó λ = 0. Por eso se informa también el ANOVA de **log(tiempo_s)**, que modela efectos multiplicativos (la aceleración), además de errores robustos HC3 y Kruskal-Wallis. No sustituyen al análisis principal ni excluyen datos.

## 4. Procedimiento reproducible
```bash
python -m laboratorio.experimento.dos_factores --matriz        # matriz (determinista)
python -m laboratorio.experimento.dos_factores --ejecutar --declaracion "…"   # exige código confirmado en git
python -m laboratorio.experimento.dos_factores --analizar      # resultados/dos_factores/ (CSV, JSON y figuras)
python -m pytest -q tests/test_dos_factores_experimento.py
```

**Condiciones de la sesión oficial:** las mismas que en la confirmación: equipo conectado a la corriente (se verifica y se registra), OneDrive en pausa, otras aplicaciones cerradas y código confirmado en git.

**Protecciones del ejecutor:**
- Escribe solo en `resultados/dos_factores_3x2.jsonl`; rechaza `corridas_2x3.jsonl` y `confirmacion_2x3.jsonl`.
- Nunca repite una secuencia que ya está registrada.
- Una corrida fallida se registra como `fallo` y el análisis se niega a trabajar con la matriz incompleta.
- No usa red; el bronce se comprueba por hash antes y después.

**Piloto técnico** (2026-11-22, de 16:25 a 16:27, 24 corridas, fuera del repositorio, marcado `piloto`; **no es un resultado**):
- Las 24 corridas terminaron `ok` con tasa de error 0; el análisis se ejecutó de principio a fin.
- Con 1×, la corrida con 4 procesos tardó de 3 a 4 s frente a alrededor de 0.6 s con 1 proceso, por el arranque de los trabajadores.
- Con 10× los dos niveles quedaron cerca, con tiempos bimodales (unos 4 s o unos 7 s), como el ruido ya visto en el 2³.
- Durbin-Watson ≈ 1.16, lo que indica autocorrelación positiva. Es otro motivo para bloquear.

## 5. Resultados reales
**Sesión oficial:** 2026-11-22, de 16:38:04 a 16:39:52, sobre el commit `adf26fa` con el código sin modificar.
- Alimentación verificada antes de correr con WMI (`BatteryStatus = 2`) y .NET (`Online`); `corriente_alterna = true` quedó registrado en las 24 corridas.
- Eimy declaró de forma explícita, y quedó guardado en cada registro: «OneDrive en pausa, aplicaciones cerradas, conectado a la corriente».
- Mismo equipo (`equipo_id 3cab0f42ae72`), Python 3.14.3 y las mismas bibliotecas que el 2³ y la confirmación.
- Las **24 corridas terminaron `ok` con `tasa_error = 0`**, en el orden de la matriz y sin repeticiones.
- La evidencia de los factores coincide con los niveles:
  - capturas: 14, 70 y 140;
  - CSV: 756,184, 3,779,960 y 7,559,680 bytes;
  - `pids_distintos`: 1 con 1 proceso y 4 con 4 procesos.

**Tiempos por tratamiento** (`tiempo_s`, 4 réplicas cada uno):

| Carga | Procesos | Media (s) | DE (s) | Mín. | Máx. |
|---|---|---|---|---|---|
| 1× | 1 | 0.505 | 0.156 | 0.359 | 0.645 |
| 1× | 4 | 3.011 | 0.625 | 2.375 | 3.558 |
| 5× | 1 | 2.479 | 0.795 | 1.773 | 3.198 |
| 5× | 4 | 3.777 | 0.801 | 2.945 | 4.494 |
| 10× | 1 | 5.441 | 1.254 | 3.714 | 6.374 |
| 10× | 4 | 5.293 | 0.725 | 4.211 | 5.713 |

**Medias marginales:**
- Por carga: 1.758 s (1×), 3.128 s (5×) y 5.367 s (10×).
- Por procesos: 2.809 s (1 proceso) y 4.027 s (4 procesos).

## 6. ANOVA e interacciones
**ANOVA de dos vías con bloques** (análisis principal, `tiempo_s`; R² = 0.957, R² ajustado = 0.934, CME = 0.232):

| Fuente | SC | gl | CM | F | p | η² parcial | ω² parcial |
|---|---|---|---|---|---|---|---|
| Bloque | 7.874 | 3 | 2.625 | 11.29 | 0.0004 | 0.693 | 0.563 |
| A: carga | 53.103 | 2 | 26.552 | 114.23 | < 0.0001 | 0.938 | 0.904 |
| B: procesos | 8.908 | 1 | 8.908 | 38.32 | < 0.0001 | 0.719 | 0.609 |
| **AB: carga × procesos** | 7.062 | 2 | 3.531 | **15.19** | **0.0002** | 0.670 | 0.542 |
| Residuo | 3.487 | 15 | 0.232 | | | | |
| Total | 80.434 | 23 | | | | | |

Se rechazan las tres hipótesis nulas al 5 %.

**La interacción es significativa**, así que el efecto de los procesos se lee a través de los efectos simples y no del efecto principal. Diferencia 1 proceso − 4 procesos en cada carga, con el CME del modelo, 15 gl y corrección de Holm:

| Carga | Diferencia (s) | IC 95 % | Aceleración t₁/t₄ | p (Holm) |
|---|---|---|---|---|
| 1× | −2.506 | [−3.233, −1.779] | 0.17 | < 0.0001 |
| 5× | −1.297 | [−2.024, −0.571] | 0.66 | 0.0035 |
| 10× | +0.148 | [−0.579, 0.875] | 1.03 | 0.671 |

- Con 1× y 5×, **4 procesos son más lentos** que 1, de forma significativa.
- Con 10× la diferencia no es significativa: los dos niveles empatan.
- El bloque es significativo (p = 0.0004): la variación entre tramos de la sesión existía y el bloqueo la retiró del error.

**Exploratorio** (lectura de las medias, no forma parte del análisis fijado):
- El tiempo por cada 1× de carga añadido es de unos 0.55 s con 1 proceso y de unos 0.25 s con 4 procesos.
- Con 4 procesos hay un costo fijo de arranque de unos 2.5 a 2.8 s.
- Interpolando en línea recta, el punto de equilibrio está cerca de 10× (unas 130 a 140 capturas). Con cargas mayores, como las 224 capturas de 16× del 2³, se esperaría ventaja de 4 procesos, lo que es coherente con T8.

Figuras: [`efectos_principales.png`](../../laboratorio/experimento/resultados/dos_factores/figuras/efectos_principales.png), [`interaccion.png`](../../laboratorio/experimento/resultados/dos_factores/figuras/interaccion.png) y [`residuos.png`](../../laboratorio/experimento/resultados/dos_factores/figuras/residuos.png).

## 7. Diagnóstico de supuestos
| Supuesto | Prueba | Resultado | Lectura |
|---|---|---|---|
| Normalidad | Shapiro-Wilk de los residuos | W = 0.974, p = 0.77 | Sin evidencia en contra |
| Homogeneidad | Brown-Forsythe entre las 6 celdas | F = 1.59, p = 0.21 | No se rechaza, pero con n = 4 por celda la prueba tiene poca potencia. La DE va de 0.16 s (1×, 1 proceso) a 1.25 s (10×, 1 proceso), con una razón de varianzas de 64. **Heterogeneidad probable** |
| Independencia | Durbin-Watson; residuo frente a secuencia | DW = 2.04; pendiente −0.001 s por corrida (p = 0.93) | Sin autocorrelación ni deriva **una vez que el bloque está en el modelo** |
| Atípicos | Residuos studentizados; distancia de Cook | Corrida 3 (10×, 1 proceso, 3.71 s) con residuo studentizado de 3.17; Cook mayor que 4/n en las corridas 1, 3 y 19 (máximo 0.42, menor que 1) | Una corrida rápida, coherente con el ruido bimodal que ya se conocía. No es influyente (Cook < 1) y **no se excluye** |
| Adecuación y escala | Box-Cox | λ = 0.15, IC 95 % [−0.04, 0.40]: excluye 1 e incluye 0 | La escala logarítmica es más adecuada que la aditiva |

**Análisis complementarios** (fijados en §3 antes de correr; no sustituyen al principal):

| Análisis | A: carga | B: procesos | AB |
|---|---|---|---|
| ANOVA de log(tiempo_s) | F = 307.8, p < 0.0001 | F = 229.9, p < 0.0001 | F = 123.4, p < 0.0001 |
| `tiempo_s` con errores HC3 | F = 47.5, p < 0.0001 | F = 45.1, p < 0.0001 | F = 7.67, p = 0.0051 |
| Kruskal-Wallis (6 celdas) | H = 19.13, p = 0.0018 | | |

- Las conclusiones no cambian con la escala logarítmica ni con errores robustos a la heterogeneidad.
- Kruskal-Wallis solo confirma que las 6 celdas no son iguales. **No contrasta la interacción** y no sustituye al análisis factorial.

## 8. Interpretación y limitaciones
**Interpretación en términos del pipeline:**
- El tiempo crece con el volumen. El 66 % de la suma de cuadrados total corresponde a la carga.
- La paralelización **no es una mejora general**: depende del volumen. Arrancar 4 procesos con `spawn` en Windows cuesta unos 2.5 s fijos, porque cada trabajador vuelve a importar pandas y el pipeline. Con la carga diaria real (1×, 14 capturas) eso hace la corrida unas 6 veces más lenta.
- Con 10×, el ahorro por captura apenas compensa ese costo.
- Para el volumen actual del observatorio, **1 proceso es la configuración adecuada**. La paralelización solo conviene por encima de unas 140 capturas, y ese umbral es exploratorio.
- Esto acota la conclusión de T8 del 2³: allí la carga era de 16×.

**Limitaciones:**
1. Un solo equipo y una sola sesión de 2 minutos. Los resultados no se extrapolan a otro hardware, a Linux (donde `fork` cambia el costo de arranque) ni a otro día.
2. La carga son copias repetidas del mismo bronce: es un volumen técnico, no datos más variados.
3. Hay heterogeneidad de varianzas probable (razón 64) con solo 4 réplicas por celda. Se cubre con log(t) y HC3, que coinciden.
4. Hay una corrida atípica (la 3), atribuible al ruido bimodal que se observa desde el 2³. No se excluyó.
5. El punto de equilibrio de unas 10× es una interpolación lineal con tres niveles de carga; no está estimado formalmente.
6. Analizador y formato quedaron fijos (`json` y `csv`). Con `orjson` o Parquet el umbral podría moverse.

## 9. Evidencias y conclusiones
**Evidencias:**
- [`resultados/dos_factores_3x2.jsonl`](../../laboratorio/experimento/resultados/dos_factores_3x2.jsonl): 24 registros, SHA-256 `722c1acb8c4a2b69…`.
- [`resultados/dos_factores/resumen.json`](../../laboratorio/experimento/resultados/dos_factores/resumen.json), junto con `anova.csv`, `efectos_simples.csv`, `medias_tratamiento.csv`, `sensibilidad.csv`, `residuos.csv` y las figuras, en la misma carpeta. Se regeneran con `--analizar`, y los CSV y el JSON coinciden byte a byte (lo verifican las pruebas).
- Los resultados anteriores siguen intactos: `corridas_2x3.jsonl` (`f5167a79…`) y `confirmacion_2x3.jsonl` (`730c34d5…`).

**Conclusión:** la carga y el número de procesos afectan al tiempo del pipeline, y **interactúan** (p = 0.0002, η² parcial = 0.67). Los 4 procesos empeoran el tiempo con cargas bajas (1× y 5×) y empatan con 10×. El resultado se mantiene con log(t), con HC3 y con el bloqueo de la deriva temporal.
