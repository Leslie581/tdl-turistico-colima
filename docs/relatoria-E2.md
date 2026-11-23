# Relatoría E2 · Observatorio de Ocupación Hotelera de Colima — Manzanillo

Equipo: Leslie Valadez Macías (A) y Eimy Melissa Urbina Meza (B) · Periodo documentado: 2026-11-21 a 2026-11-22 (entrega: 2026-11-23) · **Estado: borrador. La auditoría cruzada con otro equipo está PENDIENTE y no hay conformidad registrada de A ni de B.**
Horas de la Ciudad de México (UTC−6). Los tiempos de B tienen horario de inicio y fin en su PSP; los de A son estimaciones retrospectivas confirmadas por Leslie.

## 1. Qué nos propusimos
Integrar una fuente geoespacial visible en el tablero, sin datos personales y con linaje; correr un experimento factorial 2³ con aleatorización, réplicas y bloqueo, un diseño de dos factores y la comparación 2⁴ frente a 2⁴⁻¹, con una corrida de confirmación; y medir el producto y los datos con ISO/IEC 25010 y 25012 (una métrica por característica).

## 2. Qué hicimos
| Fecha | Qué | Quién | Tiempo | Evidencia |
|---|---|---|---|---|
| 21-nov | Arnés del 2³ y primer bloque | B | 19 min | `8c09877`, `2784148` |
| 22-nov | Segundo bloque y ANOVA 2³ | B | 9 min | `7309fed`, `b27f1a8` |
| 22-nov | Confirmación T8 frente a T1 (12 corridas) | B | 9 min | `c5a9ce2`, `6e1cbe8` |
| 22-nov | Diseño 3×2 y ANOVA de dos vías (24 corridas) | B | 10 min | `adf26fa`, `e99f40f` |
| 22-nov | Matrices 2⁴ y 2⁴⁻¹ | B | 3 min | `a38ccb0` |
| 22-nov | Fuente geoespacial: unión espacial, mapa, linaje y ética | A | 90 min | `aa4bf67` |
| 22-nov | ISO 25010 y 25012, antecedentes normativos | A | 120 min | `d79f387`, `99047e8` |
| 22-nov | Integración de la evidencia estadística, objetivo O1 y validación previa de la captura | A | 113 min | PR #24 (`c3bea67`) |
| 22-nov | Corrección del CI de `a38ccb0` | B | 12 min | `9abfaa9` |
| 22-nov | Aclaración del p90 y revisión cruzada de los PR #23 a #26 | A y B | sin registrar | PR #25, #26 |

Total en el PSP: A, 323 min (estimados); B, 70 min en E2 (incluye 8 min de un borrador de ISO que no se integró).

## 3. Qué decidimos y por qué
1. **Fuente geoespacial:** DENUE ya capturado en E1 unido a las AGEB del Marco Geoestadístico, con conteos por AGEB. Se descartó publicar coordenadas o conteos exactos de 1 o 2 establecimientos, siguiendo el criterio de RNF-PRI-03 (ninguna celda con menos de 3), y se oculta ese rango. Los polígonos se leen con `pyshp` porque Windows bloquea GDAL (defecto 29).
2. **Experimento:** bloques por día en el 2³ y criterios de confirmación fijados antes de correr. El 3×2 usó bloques por la deriva con el orden de ejecución y `json` y CSV fijos, porque Parquet comprime las copias repetidas. No se eliminó ninguna observación; la heterogeneidad se informó con log, HC3 y Kruskal-Wallis.
3. **Objetivo O1:** se conservó el dictamen histórico NO CUMPLE y se añadió un indicador posterior, separado, en lugar de redefinir la ventana o excluir el fallo inicial.

## 4. Qué salió mal y cómo lo corregimos
- **O1 no se cumple:** la peor ventana de 7 días tiene 9 éxitos y 1 fallo (90 %); la tasa global es 93.8 % (15 de 16). El único fallo fue el **10-nov**, en la puesta en marcha, sin `INEGI_TOKEN` configurado, y sigue en la bitácora. Las 8 ventanas completas posteriores dan 100 % (observado, sin extrapolar). Se añadió `--validar-configuracion`; no se ha probado en GitHub.
- **ISO 25012:** no cumplen la actualidad de DataTur (23 meses) ni la comprensibilidad del agregado AGEB (0 de 12 columnas en el diccionario; queda para E3).
- **Defectos de A (sin minutos medidos):** 29 (GDAL bloqueado), 30 (clave de AGEB rural rechazada), 32 (encuadre del mapa con islas) y 33 (columna inexistente en el medidor).
- **Defectos de B:** 23 (el check `calidad` falló en `a38ccb0` por diferencias numéricas entre Windows y Ubuntu; corregido en `9abfaa9`) y 21 (CRLF en un JSON); del 24 al 26, errores de documentación en su borrador de ISO (no integrado), incluido el método del p90.
- **Pendiente:** la etapa geoespacial es un comando aparte (`python -m pipeline.geoespacial`) que no corre en `pipeline.ejecutar`; el agregado conserva la captura del 21-nov (la del 22 trae los mismos 134 establecimientos).

## 5. Qué aprendimos
**Ingeniería de Datos.** La unión espacial ubicó 134 de 134 establecimientos y coincidió con la AGEB del propio DENUE. La captura del 22 difirió de la del 21 solo en el orden y el hash: el linaje se apoya en el contenido y los hashes.
**Análisis Estadístico.** El 2³ no halló efectos significativos (mínimo detectable: 2.42 s), pero la confirmación fijada de antemano dio una mejora de T8 de 36.8 % (p = 0.0143). El 3×2 mostró interacción (p = 0.0002): 4 procesos son más lentos con carga 1× y 5× y empatan con 10×. Un diseño sin potencia no prueba que no haya efecto.
**Calidad.** Con una captura diaria, una ventana de 7 días trae unas 7 ejecuciones y un solo fallo la lleva bajo 95 %; medir por ventanas no es lo mismo que la tasa global. El p90 depende del método (4.26 s con `lower`, 4.98 s lineal).

## 6. Evidencias
PR #23 a #26 (aprobados por la otra integrante; checks de `main` en verde en `26f7ee0`) · [`ENTREGA.md`](E2/ENTREGA.md), que enlaza cada evidencia por criterio · [`calidad/`](../calidad/README.md).

## Uso de IA generativa
Claude Code (Anthropic), en ambas cuentas: código, pruebas, análisis, documentación y verificaciones. Los PSP de B lo marcan fila por fila. No cuenta como revisión independiente.
