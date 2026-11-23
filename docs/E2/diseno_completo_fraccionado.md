# Diseño factorial completo 2⁴ y fraccionado 2⁴⁻¹

Integrante B (Eimy), con asistencia de Claude Code, 2026-11-22. Generador: [`laboratorio/experimento/fraccionado.py`](../../laboratorio/experimento/fraccionado.py); pruebas: [`tests/test_fraccionado_experimento.py`](../../tests/test_fraccionado_experimento.py).

> **Matrices teóricas.** Los dos archivos son planes de corrida: **no contienen mediciones** y no se ejecutó ninguna corrida nueva. Cada fila lleva la columna `mediciones = "ninguna (matriz teórica)"`. Las mediciones reales de E2 están en [`anova_2x3.md`](anova_2x3.md) (2³ y confirmación) y en [`dos_factores_3x2.md`](dos_factores_3x2.md).

## 1. Factores y niveles
| Factor | Nivel −1 | Nivel +1 | Interpretación técnica |
|---|---|---|---|
| A: procesos | 1 | 4 | Paralelismo del bronce → plata (2³) |
| B: analizador | `json` | `orjson` | Biblioteca para leer el JSON de DENUE (2³) |
| C: formato | CSV | Parquet | Formato de salida de la plata (2³) |
| D: validación R-E07 | desactivada | activada | Segunda verificación con pandera de la plata ya unida (`reglas.validar_plata`: esquema, tipos, rangos, unicidad) |

**Por qué D:**
- Es una etapa real del pipeline: `procesar_capturas` la aplica al final.
- Tiene un costo de cómputo propio que se puede medir.
- Desactivarla **no** deja pasar datos sin controlar: la puerta por captura (integridad, privacidad, esquema y reglas por registro, de R-E01 a R-E05) sigue activa en los dos niveles.

**Análisis teórico frente a ejecución real:**
- El arnés del 2³ (`arnes.ejecutar_corrida`) llama a `procesar_una_captura` y **no** ejecuta R-E07, así que todas las corridas reales hechas hasta ahora están en **D = −1**.
- Ejecutar D = +1 requeriría ampliar el arnés.
- Con la carga de copias repetidas, R-E07 fallaría por **unicidad**: los mismos establecimientos aparecen en cada copia. Habría que validar por copia o deduplicar antes, lo que cambiaría la tarea medida.
- Por eso aquí se construyen y comparan las matrices **sin ejecutarlas**.

## 2. Diseño completo 2⁴
[`resultados/matriz_2a4_completa.csv`](../../laboratorio/experimento/resultados/matriz_2a4_completa.csv): 16 tratamientos en orden estándar (A cambia más rápido), codificación −1/+1, más los niveles reales y un orden aleatorio sugerido (semilla 20261125) por si algún día se ejecuta.

**Verificado por las pruebas:**
- Las 16 combinaciones son distintas y forman exactamente {−1, +1}⁴.
- Cada columna corresponde a sus niveles.
- La matriz con el intercepto y los **15 efectos** (4 principales, 6 dobles, 4 triples y ABCD) cumple **XᵀX = 16·I**: es ortogonal, así que **todos los efectos se estiman por separado**.
- Con una sola réplica no quedan grados de libertad para el error. Habría que replicar, bloquear o suponer despreciables las interacciones de orden alto.

## 3. Diseño fraccionado 2⁴⁻¹
[`resultados/matriz_2a4-1_fraccion.csv`](../../laboratorio/experimento/resultados/matriz_2a4-1_fraccion.csv): un 2³ completo en A, B y C, con D definida por el generador.

- **Generador:** D = ABC.
- **Relación definidora:** I = ABCD (fracción principal; en todas las filas A·B·C·D = +1). Son exactamente las 8 filas del 2⁴ con ABCD = +1.
- **Resolución IV:** la palabra más corta de la relación definidora tiene 4 letras.

**Estructura de alias** (el alias de un efecto es su producto por ABCD, con x² = I):

| Efecto | Alias | Cálculo |
|---|---|---|
| A | BCD | A·ABCD = A²BCD |
| B | ACD | B·ABCD |
| C | ABD | C·ABCD |
| D | ABC | D·ABCD (el generador) |
| AB | CD | AB·ABCD = A²B²CD |
| AC | BD | AC·ABCD |
| AD | BC | AD·ABCD |
| ABCD | I (la media) | — |

**Comprobación:**
- **Algebraica:** `fraccionado.alias`.
- **Numérica:** en la fracción, las columnas de contraste de cada par de alias son **idénticas** (por ejemplo, la de A coincide con la de BCD).
- **Ortogonalidad:** las columnas de A, B, C y D son ortogonales entre sí y con todas las interacciones dobles.

## 4. Comparación
| | Completo 2⁴ | Fraccionado 2⁴⁻¹ (resolución IV) |
|---|---|---|
| Corridas por réplica | 16 | **8** (ahorro de 8, el **50 %**) |
| Columnas de contraste distintas | 15 | 7, cada una con 2 efectos confundidos |
| Efectos principales | Separados | Separados de los demás principales y de las dobles; confundidos con una triple (A = BCD) |
| Interacciones dobles | Las 6, separadas | Solo 3 cadenas: AB+CD, AC+BD y AD+BC. **No se puede saber cuál de las dos dobles de un par actúa** |
| Triples y ABCD | Separadas | Confundidas con los principales y con la media |

**Ventajas del fraccionado:**
- Cuesta la mitad de las corridas.
- Estima los 4 efectos principales sin sesgo, si las interacciones triples son despreciables (lo habitual).
- Es útil para cribar factores.

**Limitaciones del fraccionado:**
- Los efectos confundidos **no se pueden separar** con estos datos.
- Si AB+CD resulta significativa, hacen falta corridas adicionales para atribuirla: la fracción complementaria (I = −ABCD), que junto con esta forma el 2⁴ completo, o un *fold-over* de un factor.
- Con 8 corridas y una réplica quedan pocos grados de libertad para el error.

**Cuándo usar cada uno:**
- **Fraccionado:** para cribar cuando hay muchos factores, las corridas son caras y es razonable suponer que las interacciones de orden alto son despreciables.
- **Completo:** cuando se esperan interacciones dobles importantes y hace falta atribuirlas.

**Aplicación a este pipeline:** el 3×2 mostró una interacción fuerte entre carga y procesos (§6 de `dos_factores_3x2.md`). Una interacción entre procesos y validación (AD) quedaría confundida con analizador × formato (BC). Por eso, si D llegara a ejecutarse, convendría el **completo** o una fracción que deje AD libre.

## 5. Reproducción
```bash
python -m laboratorio.experimento.fraccionado      # regenera los dos CSV (deterministas, con LF)
python -m pytest -q tests/test_fraccionado_experimento.py
```

## 6. Limitaciones
- Matrices teóricas: no hay mediciones de D ni de las 16 u 8 combinaciones.
- El factor D no es ejecutable con el arnés actual sin ampliarlo, y con la carga repetida chocaría con la regla de unicidad (§1).
- La relación entre la resolución y la interpretación supone que las interacciones triples son despreciables; no se comprobó con datos.
