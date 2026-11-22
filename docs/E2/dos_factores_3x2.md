# Experimento de dos factores: carga × procesos (ANOVA de dos vías)

Integrante B (Eimy), con asistencia de Claude Code. Diseño fijado el **2026-11-22, antes de las corridas oficiales**. Código: [`laboratorio/experimento/dos_factores.py`](../../laboratorio/experimento/dos_factores.py); pruebas: [`tests/test_dos_factores_experimento.py`](../../tests/test_dos_factores_experimento.py).

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
*Pendiente: las 24 corridas oficiales todavía no se han ejecutado.* Requieren que el código esté confirmado en git.

## 6. ANOVA e interacciones
*Pendiente.*

## 7. Diagnóstico de supuestos
*Pendiente.*

## 8. Interpretación y limitaciones
*Pendiente para la interpretación.* Limitaciones conocidas de antemano:
- Un solo equipo y una sola sesión.
- La carga es un volumen técnico de copias, no datos más variados.
- El ruido es bimodal y la autocorrelación también apareció en el piloto.
- La aceleración depende del costo de `spawn` en Windows.

## 9. Evidencias y conclusiones
*Pendiente.* Las evidencias irán en `resultados/dos_factores_3x2.jsonl` y `resultados/dos_factores/`.
