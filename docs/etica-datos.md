# Declaración de ética y legalidad de datos

Corte 2026-11-22 · Integrante A. Alcance: las tres fuentes que alimentan el observatorio: **DataTur** (ocupación hotelera), **DENUE** (oferta de hospedaje) y el **Marco Geoestadístico** (polígonos AGEB, E2). Los términos se leyeron en las páginas citadas en la fecha indicada; no se contactó a ninguna institución ni se solicitó autorización. Lo que no se pudo verificar se marca como tal.

## 1. Resumen por fuente
| | DataTur (SECTUR) | DENUE (INEGI) | Marco Geoestadístico (INEGI) |
|---|---|---|---|
| **Procedencia** | `Base70centros.csv`, conjunto «Ocupación hotelera en los 70 destinos principales monitoreados», datos.gob.mx | API de consulta del DENUE, subsector SCIAN 721, Manzanillo (06007), una captura diaria | Marco Geoestadístico, Censo de Población y Vivienda 2020, zip del estado 06 ([ficha](https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=889463807469)) |
| **Base legal de uso** | Datos abiertos del gobierno federal publicados en datos.gob.mx | Información del INEGI bajo sus términos de libre uso | Ídem |
| **Licencia o términos** | Creative Commons Attribution 4.0, declarada en la ficha del conjunto (verificada el 2026-11-09, [`datatur.md`](fuentes/datatur.md) C1) | [Términos de libre uso del INEGI](https://www.inegi.org.mx/inegi/terminos.html) (verificados el 2026-11-22): copiar, difundir, adaptar y explotar comercialmente, con crédito «Fuente: INEGI, producto» y aviso de que el análisis no es del INEGI | Ídem |
| **Acceso** | Descarga manual con navegador; no se usa la API CKAN (su `robots.txt` la prohíbe) | API con token gratuito (`INEGI_TOKEN`, secreto de GitHub); máximo 2–3 solicitudes por ejecución, pausa ≥ 1.5 s, lectura de `robots.txt` | Un solo `GET` del zip (29 MB) con User-Agent identificable; la ruta `/contenidos/productos` está permitida en el `robots.txt` de INEGI (leído el 2026-11-22) |
| **Qué se redistribuye** | Agregado mensual de Manzanillo, 2 a 5 estrellas | Conteos por municipio y por AGEB; **sin** CLEE, nombres ni coordenadas | AGEB del municipio 06007 en GeoJSON, reproyectadas a EPSG:4326 |
| **Atribución** | «Secretaría de Turismo (SECTUR), DataTur… CC BY 4.0» | «Fuente: INEGI, DENUE… Agregado propio; no es un producto del INEGI» | «Fuente: INEGI, Marco Geoestadístico, Censo de Población y Vivienda 2020. Transformación propia… no avalada por el INEGI» |

## 2. Privacidad
- **DataTur:** datos agregados por destino y mes; no hay personas ni establecimientos individuales.
- **DENUE:** directorio de unidades económicas, con riesgo propio: 63 de 134 establecimientos de la muestra inicial tienen 0 a 5 personas (micronegocios) y su domicilio puede ser una vivienda. Mitigaciones aplicadas antes de escribir en bronce: se excluyen teléfono, correo, sitio web, razón social, **nombre comercial** y domicilio ([`denue.md`](fuentes/denue.md)); los agregados no llevan CLEE ni coordenadas; el mapa por AGEB **oculta el conteo exacto cuando hay 1 o 2 establecimientos** (rango «1-2»). El tablero no muestra establecimientos individuales (una prueba lo comprueba). **Riesgo residual:** el bronce conserva coordenadas, AGEB, manzana y CLEE, que el INEGI publica; no se redistribuyen.
- **Marco Geoestadístico:** límites geográficos, sin datos de personas.

## 3. Sesgos conocidos y mitigación
| Fuente | Sesgo o limitación | Mitigación |
|---|---|---|
| DataTur | Cobertura de los hoteles que reporta el sistema oficial; solo categorías de 2 a 5 estrellas (decisión D1 del contrato); la ocupación es un cociente de sumas, así que los hoteles con más cuartos pesan más; el conjunto puede incluir actualizaciones retroactivas; datos hasta 2024-12 | Decisiones documentadas en [`contrato_datos.md`](E1/contrato_datos.md); la proyección se rotula como histórica; no se afirma nada sobre establecimientos individuales |
| DENUE | Es un directorio, no un censo continuo: puede omitir alojamiento informal o no registrado (no medido aquí) y su actualización no está documentada; las coordenadas son del INEGI y su precisión no se verificó | El mapa se rotula como **oferta registrada, no ocupación ni demanda**; se compara la AGEB espacial con la clave AGEB del propio DENUE (concordancia de 134 de 134) |
| Marco Geoestadístico | Los límites geoestadísticos no siempre coinciden con los político-administrativos y pueden cambiar entre ediciones (INEGI los llama provisionales cuando carecen de sustento legal); el tamaño de las AGEB varía mucho (efecto del área de agregación): las rurales abarcan cientos de km² | Se usa la edición 2020 con su atribución; se muestra el tipo de AGEB (urbana o rural) y se declara el encuadre del mapa |

## 4. Uso secundario y restricciones
- **Uso previsto:** análisis académico del observatorio. No se enlazan los datos con otras fuentes para identificar personas ni establecimientos.
- **Pendiente de aclarar (no se asume permiso):** el Sistema de Monitoreo Hotelero de SECTUR, cuya automatización y publicación **no** están autorizadas ni aclaradas ([`datatur.md`](fuentes/datatur.md) §1 y §3); el repositorio no lo usa. Los términos generales del portal gob.mx restringen el uso a fines personales ([`datatur.md`](fuentes/datatur.md) R1); el repositorio se apoya solo en la licencia CC BY 4.0 declarada por el propio conjunto, y la tensión entre ambos textos no está resuelta.
- **Declaración de IA generativa:** [`ENTREGA.md`](E1/ENTREGA.md).
