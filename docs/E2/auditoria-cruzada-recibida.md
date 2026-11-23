# Auditoría cruzada E2 recibida: informe del Observatorio inmobiliario de Colima sobre nuestro proyecto

| | |
|---|---|
| **Equipo auditor** | Observatorio inmobiliario de Colima (TRUSTED DATA LAB, trabajo individual) |
| **Documento original** | [`docs/E2/calidad/AUDITORIA_CRUZADA_E2_TDL_TURISTICO.md`](https://github.com/chareyesjaramillo17801-rgb/trusted-data-lab-colima/blob/65c80cc0f7bd9b82706ece7ac7bcc1bad3cf7522/docs/E2/calidad/AUDITORIA_CRUZADA_E2_TDL_TURISTICO.md), en el repositorio de ese equipo (commit `65c80cc`) |
| **Versión de nuestro proyecto que auditaron** | `73e741ca3bc9130ad63bb0bb2f6a1a865210b359`: nuestro `main` tras el PR #32 |
| **Fecha del informe** | 2026-11-23 |
| **Estado del informe** | Borrador del equipo auditor, «listo para revisión y firma»; sin firma ni acta de entrega. Este documento lo registra, lo verifica y lo valora; **no es su respuesta formal** |
| **Quién lo valora** | Equipo TDL de Ocupación Hotelera de Colima. Valoración elaborada por A con asistencia de Claude Code; revisada en conjunto por A y B (ver [`auditoria-cruzada-realizada.md`](auditoria-cruzada-realizada.md), sección 13); sin firmas |

Este documento separa tres cosas: lo que **dice** el informe recibido (sección 1), lo que **verificamos** contra nuestro repositorio (sección 3) y lo que **concluimos** (secciones 2, 4 y 5). La auditoría que **realizamos** al otro equipo está en [`auditoria-cruzada-realizada.md`](auditoria-cruzada-realizada.md).

## 1. Qué dice el informe recibido

- **Metodología.** Revisión de la ficha de entrega E2, de las evaluaciones ISO/IEC 25010 y 25012 y del documento geoespacial, más una verificación técnica complementaria por clonación independiente: lectura de CSV y JSON y búsqueda estática de referencias en código y workflows. **No ejecutó nuestras pruebas** y lo declara.
- **Hallazgos.** Cuatro: dos mayores y dos menores, **todos sustentados en limitaciones que nosotros ya habíamos declarado**.

| ID | Severidad | Resumen |
|---|---|---|
| AC-E2-01 | Mayor | Incumplimiento de RNF-PRI-03: 28 de 88 celdas con 1 o 2 establecimientos en `manzanillo_oferta_hospedaje.csv` |
| AC-E2-02 | Mayor | Objetivo O1 no alcanzado: peor ventana de 9 de 10 (90 %) y tasa global de 15 de 16 (93.8 %) |
| AC-E2-03 | Menor | Diccionario sin las 12 columnas del agregado AGEB |
| AC-E2-04 | Menor | Etapa geoespacial fuera de `pipeline.ejecutar` y de la captura diaria |

- **Observaciones sin clasificar como defecto.** El rezago de 23 meses de DataTur, las matrices 2⁴ y 2⁴⁻¹ teóricas y el carácter documental de la revisión.
- **Dictamen.** «Dos hallazgos mayores y dos menores… no se identificó un defecto crítico», sin aprobar ni rechazar E2 y sujeto a validación técnica independiente.

## 2. Valoración del informe

| Aspecto | Observación | Valor |
|---|---|---|
| **Estructura** | Metodología, hallazgos con criterio, evidencia, impacto, recomendación y fuentes; observaciones aparte y dictamen. Cada hallazgo se puede seguir hasta un archivo | Fortaleza |
| **Honestidad del alcance** | Declara que no es una ejecución independiente de pruebas ni una certificación ISO, y que las cifras son las publicadas por nosotros | Fortaleza |
| **Trazabilidad** | Fija el commit auditado y reproduce las cuentas (88 filas, 28 con valor 1 o 2, 31.82 %) | Fortaleza |
| **Precisión de las cifras** | Todas se verifican (sección 3) | Fortaleza |
| **Metodología técnica** | Documental y estática. No ejecutó el pipeline ni las pruebas, no comprobó los 266 enlaces de linaje ni la asignación geoespacial, y no consultó el CI ni el tablero | Mejorable |
| **Cobertura de ISO** | No recorre las ocho características de ISO/IEC 25010 ni las de ISO/IEC 25012 con una matriz de criterio, evidencia y estado, que es lo que pide el PDF | Mejorable |
| **Contribución independiente** | Los cuatro hallazgos ya estaban en nuestra documentación; no aporta defectos que no hubiéramos declarado | Mejorable |
| **Fortalezas** | No registra fortalezas comprobadas | Mejorable |
| **Severidades** | Razonables y sin exageración; no explica el criterio con el que clasifica | Mejorable |
| **Recomendaciones** | Concretas y accionables. Una (añadir validación previa de configuración) ya estaba implementada | Fortaleza, con un matiz |
| **Estado del documento** | «Borrador listo para revisión y firma» sin indicar si se entregó; no hay sección de respuesta ni de revalidación | Mejorable |

**Lo que tomamos para nuestro informe:** una matriz explícita por característica con criterio, evidencia, método, resultado y estado; ejecución real de las pruebas y del pipeline; fortalezas comprobadas; criterio de severidad escrito; clasificación de lo declarado y lo no declarado; evidencia fijada a un commit; y la verificación de lo que no se puede comprobar como NO VERIFICABLE y no como falla. **No copiamos sus hallazgos ni sus conclusiones.**

## 3. Verificación de sus hallazgos contra nuestro repositorio

Verificado el 2026-11-23 sobre el mismo commit que auditaron (`73e741c`).

| ID | Qué afirman | Qué comprobamos | Veredicto |
|---|---|---|---|
| AC-E2-01 | 88 filas; 28 con 1 o 2 (12 con 1 y 16 con 2); 31.82 % | `manzanillo_oferta_hospedaje.csv`: 88 celdas, 28 con menos de 3 (12 con 1 y 16 con 2), 31.82 % | **Confirmado** |
| AC-E2-02 | Peor ventana de 9 éxitos y 1 fallo; tasa global 15 de 16; ocho ventanas posteriores sin fallos; dictamen propio NO CUMPLE | Coincide con [`evidencia/iso25010.json`](evidencia/iso25010.json) y con [`iso25010.md`](iso25010.md). **Matiz:** recomiendan «añadir validación previa de configuración», y ya existe (`--validar-configuracion` y la opción `solo_validar`, commit `c3bea67`); lo que falta es ejecutarla en GitHub, las alertas de fallo y la medición continua | **Confirmado, con un matiz** |
| AC-E2-03 | El agregado AGEB tiene 12 columnas y el diccionario no tiene entradas con ese `dataset` | El diccionario tiene 45 entradas en 5 `dataset` y **0** de `manzanillo_oferta_ageb`; el agregado tiene 12 columnas | **Confirmado** |
| AC-E2-04 | No hay referencias a la etapa geoespacial en `ejecutar.py`, `captura-diaria.yml` ni `ci.yml` | 0 referencias en los tres archivos; `pipeline/geoespacial.py` existe | **Confirmado** |
| Observaciones | Rezago de DataTur, matrices teóricas y alcance documental | Coinciden con [`iso25012.md`](iso25012.md) y con [`diseno_completo_fraccionado.md`](diseno_completo_fraccionado.md) | **Confirmadas** |

**Severidades.** Coincidimos con las cuatro: los dos mayores son incumplimientos de requisitos propios y los dos menores, mejoras de documentación e integración.

## 4. Nuestra respuesta provisional

Es un borrador **sujeto a la validación de A y B**; solo recoge decisiones y documentos que ya existen y no asume compromisos nuevos.

| ID | Postura | Tratamiento ya documentado | Pendiente |
|---|---|---|---|
| AC-E2-01 | Aceptado | Decisión del 2026-11-23: mantener y documentar, sin suprimir celdas ni tocar bronce, oro o tablero. RNF-PRI-03 y la confidencialidad de ISO/IEC 25012 quedan en NO CUMPLE. Riesgo y mitigación futura en [`etica-datos.md`](../etica-datos.md) §2 | Supresión en el pipeline (acción de E3) |
| AC-E2-02 | Aceptado | El dictamen histórico NO CUMPLE se conserva; el indicador posterior (8 de 8 ventanas) está separado y no lo sustituye; validación previa implementada | Ejecutarla en GitHub, alertas de fallo y medición continua |
| AC-E2-03 | Aceptado | Anotado como acción correctiva de E3 en [`ENTREGA.md`](ENTREGA.md) | Extender `pipeline/oro.py` y regenerar el diccionario |
| AC-E2-04 | Aceptado | Anotado como limitación en [`ENTREGA.md`](ENTREGA.md) | Integrar la etapa o advertir la antigüedad del mapa |

**Estado de seguimiento:** abierto. No hay revalidación por parte del equipo auditor.

## 5. Limitaciones de esta valoración

- Es documental: se contrastó el informe con nuestro repositorio y no se contactó al equipo auditor.
- No consta cómo ni cuándo se nos entregó formalmente el informe; lo conocimos por su repositorio.
- La respuesta de la sección 4 no consta como aprobada ni enviada al equipo auditor; no hay revalidación de su parte.
