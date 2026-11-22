# Fuente geoespacial y linaje de datos (E2)

Corte 2026-11-22 · Integrante A. Requisitos del PDF (pág. 17): una fuente especializada integrada al pipeline y visible en el tablero, sin datos personales; declaración de ética y legalidad ([`etica-datos.md`](../etica-datos.md)); y linaje: cada registro de la capa oro rastreable hasta su fuente y su fecha de captura.

## 1. Fuente y qué mide
Establecimientos de **alojamiento temporal (SCIAN 721) del DENUE** de Manzanillo, ubicados por **unión espacial** en las **AGEB** del Marco Geoestadístico (INEGI, Censo de Población y Vivienda 2020). Reutiliza la integración DENUE de E1 (`pipeline.plata_denue.procesar_capturas`, con coordenadas, `ageb` y hashes). **Mide oferta registrada, no ocupación hotelera ni demanda.**

## 2. Implementación
| Pieza | Archivo | Qué hace |
|---|---|---|
| Extracción de polígonos | [`pipeline/geoespacial.py`](../../pipeline/geoespacial.py) `extraer_ageb` | Lee las capas `06a` (AGEB urbanas) y `06ar` (rurales) del zip oficial, filtra el municipio 06007, reproyecta de EPSG:6372 a EPSG:4326 y escribe [`manzanillo_ageb_poligonos.geojson`](../../data/oro/manzanillo_ageb_poligonos.geojson) con su ficha (URL, SHA-256 del zip y del GeoJSON, CRS, atribución, términos) |
| Unión espacial | `unir_espacial` | `geopandas.sjoin(..., predicate="within")` de la captura de referencia (la más reciente) contra los polígonos; falla si los polígonos se traslapan |
| Agregado | `agregar_por_ageb`, `ejecutar` | Un renglón por AGEB en [`manzanillo_oferta_ageb.csv`](../../data/oro/manzanillo_oferta_ageb.csv) con su ficha; esquema `pandera` (`ESQUEMA_AGREGADO`); **conteo oculto (rango «1-2») si la AGEB tiene 1 o 2 establecimientos**; sin CLEE, nombres ni coordenadas |
| Linaje | [`pipeline/linaje.py`](../../pipeline/linaje.py) | Reconstruye y verifica la cadena de cada registro del oro (§4) |
| Mapa | pestaña «Mapa de oferta» de [`tablero/`](../../tablero/) | Lee el agregado y los polígonos versionados; muestra fuente, fecha de referencia y qué representa |

GDAL no es necesario: los polígonos se leen con `pyshp` y se guardan como GeoJSON (en el equipo de desarrollo, Windows bloquea por directiva de control de aplicaciones la biblioteca GDAL de `pyogrio`; GeoPandas, Shapely y PROJ sí funcionan).

## 3. Resultados (captura de referencia 2026-11-21)
- 154 polígonos AGEB del municipio: 142 urbanos y 12 rurales (incluyen islas oceánicas sin establecimientos).
- **134 de 134 establecimientos ubicados** (sin ninguno fuera de las AGEB); 41 AGEB con establecimientos, 22 de ellas con el conteo oculto.
- **Concordancia de 134 de 134** entre la AGEB que resulta de la unión espacial y la clave AGEB que trae el propio DENUE (validación independiente de la unión).
- El agregado se regenera idéntico, byte a byte, desde el bronce (prueba `test_el_agregado_se_regenera_identico_desde_el_bronce`).

## 4. Linaje (`python -m pipeline.linaje`)
| Capa oro | Cadena verificada contra los archivos reales |
|---|---|
| `manzanillo_ocupacion_mensual.csv` (108 meses) | fila → `sha256_bronce` y `ejecucion` → `data/bronce/datatur/Base70centros.csv` (SHA-256 recalculado) |
| `manzanillo_oferta_hospedaje.csv` (4 capturas) | fila → `fecha_captura_local` → `data/bronce/denue/<fecha>/` (SHA-256 de cada archivo frente a su ficha) |
| `manzanillo_oferta_ageb.csv` (154 AGEB) | fila → `sha256_bronce` de la captura de referencia + `sha256_poligonos` → GeoJSON → SHA-256 del zip de INEGI (en su ficha) |
Resultado actual: **266 cadenas verificadas, 0 fallas** (108 + 4 + 154). `python -m pipeline.linaje --periodo 2020-04` y `--ageb 060070001009A` muestran la cadena completa de un registro. Una prueba comprueba que alterar un archivo de bronce rompe el linaje.

## 5. Reproducción
```powershell
python -m pip install -r requirements.txt -r requirements-lab.txt
python -m pipeline.geoespacial extraer --descargar     # una vez: un GET del zip oficial (29 MB) -> data/oro/manzanillo_ageb_poligonos.geojson
python -m pipeline.geoespacial agregar                  # DENUE x AGEB -> data/oro/manzanillo_oferta_ageb.csv
python -m pipeline.linaje                               # verifica el linaje de todo el oro
python -m streamlit run tablero/streamlit_app.py        # pestaña «Mapa de oferta»
python -m pytest tests/test_geoespacial.py -q
```
Zip fuente: SHA-256 `7f2aea709f5f8c619dad1153cdc9e279a71a4f2c4a4d0d176d6ca76a2941f015` (28,976,703 bytes, `Last-Modified` 2021-01-25, descargado el 2026-11-22).

## 6. Límites
- Edición 2020 del Marco Geoestadístico; existen ediciones posteriores. La concordancia de 134 de 134 con las claves del DENUE no garantiza que futuras capturas usen la misma edición.
- DENUE y los polígonos usan datums distintos (ITRF2008 y el de las coordenadas del DENUE, tratadas como EPSG:4326); la diferencia no se midió (se espera del orden de decímetros o menos) y no afectó la asignación a AGEB observada.
- El agregado es una foto de una captura; no hay serie temporal por AGEB. Las AGEB rurales abarcan áreas muy grandes y se colorean igual que las urbanas.
- La unión usa `within`: un punto exactamente en el límite de dos AGEB no se asigna (no ocurrió).
