# Antecedentes normativos: ISO/IEC 9126, familia ISO/IEC 25000 (SQuaRE) e ISO 9001

Corte 2026-11-22 · Integrante A. Requisito (PDF, pág. 18): un cuadro que relacione la ISO/IEC 9126 del temario con la familia ISO/IEC 25000 que la sustituyó, y la ISO 9001 vigente con su enfoque a procesos.
**Nota de fuentes:** las normas ISO son de pago y no se consultó su texto; esta síntesis se basa en el temario del curso, en el PDF del proyecto y en descripciones públicas de las normas. Los nombres y el número de características cambian entre ediciones de la 25010; esta evaluación sigue las ocho características que fija el PDF.

## 1. Cuadro comparativo
| | ISO/IEC 9126 | Familia ISO/IEC 25000 (SQuaRE) | ISO 9001 |
|---|---|---|---|
| **Qué es** | Modelo de calidad del **producto de software** (y métricas asociadas), de la década de 2000 | Familia de normas de **calidad y evaluación de productos y datos**; sustituyó a la 9126 y a la ISO/IEC 14598 | Norma de **sistema de gestión de la calidad** de una organización (edición vigente: 2015) |
| **Objeto** | El producto: calidad interna, externa y en uso | El producto/sistema (25010) **y los datos** (25012), con medición (serie 2502n), requisitos (25030) y evaluación (25040) | La organización y sus procesos, no el producto en sí |
| **Estructura** | Seis características con sub-características: funcionalidad, fiabilidad, usabilidad, eficiencia, mantenibilidad y portabilidad | **25010:** modelo de calidad de producto (en el PDF, ocho características: adecuación funcional, eficiencia de desempeño, compatibilidad, capacidad de interacción, fiabilidad, seguridad, mantenibilidad y portabilidad). **25012:** modelo de calidad de datos | Requisitos sobre contexto, liderazgo, planificación, apoyo, operación, evaluación del desempeño y mejora |
| **Enfoque** | Descomposición del producto en características | Modelos de calidad + proceso de medición y evaluación; añade el modelo de **datos** | **Enfoque a procesos**: ciclo planificar–hacer–verificar–actuar, pensamiento basado en riesgos y mejora continua |
| **Estado** | Sustituida (retirada) por la familia 25000 | Vigente; se evalúa con métricas medibles | Vigente; certificable por terceros |
| **Qué cambia respecto de la anterior** | — | La 25010 mueve la seguridad y la interoperabilidad (antes parte de funcionalidad) a características propias (seguridad y compatibilidad), renombra usabilidad como capacidad de interacción y agrega los datos como objeto de evaluación | No sustituye a la 25000: la 9001 gestiona los procesos que producen la calidad; la 25000 la describe y la mide |

## 2. Equivalencias entre el modelo de la 9126 y el de la 25010 (según el PDF)
| 9126 | 25010 |
|---|---|
| Funcionalidad | Adecuación funcional (la seguridad y la interoperabilidad pasan a otras características) |
| Fiabilidad | Fiabilidad |
| Usabilidad | Capacidad de interacción |
| Eficiencia | Eficiencia de desempeño |
| Mantenibilidad | Mantenibilidad |
| Portabilidad | Portabilidad |
| — | Compatibilidad (nueva) |
| — | Seguridad (característica propia) |

## 3. Aplicación al proyecto
| Norma | Dónde se aplica | Evidencia |
|---|---|---|
| **9126 → 25010** | Los requerimientos no funcionales de E1 están agrupados por las mismas ideas (disponibilidad y fiabilidad, seguridad, mantenibilidad, privacidad); el producto se evalúa con las ocho características de la 25010 | [`requerimientos.md`](../E1/requerimientos.md), [`iso25010.md`](iso25010.md) |
| **25012** | Calidad de los datos de la capa oro de DataTur y DENUE, con métricas y umbrales explícitos | [`iso25012.md`](iso25012.md), [`pipeline/medicion_iso.py`](../../pipeline/medicion_iso.py) |
| **25000 (medición y evaluación)** | Cada métrica se define, se mide con un procedimiento reproducible y se registra la evidencia en JSON | [`evidencia/`](evidencia/) |
| **ISO 9001 (procesos)** | El plan SQA organiza el trabajo como un ciclo: planificar (plan de trabajo y objetivos), hacer (pipeline y laboratorio), verificar (CI, auditorías, revisión cruzada) y actuar (acciones correctivas y registro de desviaciones); los riesgos se llevan en un registro | [`plan_sqa.md`](../E1/plan_sqa.md), [`auditorias.md`](../../calidad/auditorias.md), [`riesgos.md`](../../calidad/riesgos.md) |

## 4. Alcance y límites
- El proyecto **aplica el enfoque** de la ISO 9001 (procesos, verificación, mejora) pero **no** pretende un sistema de gestión certificado.
- Los modelos 25010 y 25012 se usan para medir el observatorio; los umbrales son del equipo y no vienen de la norma.
- Las relaciones de este cuadro son una síntesis académica y no sustituyen la lectura de las normas.
