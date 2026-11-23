"""Fuente geoespacial de E2: oferta de hospedaje DENUE por AGEB, con unión espacial real en GeoPandas.

    python -m pipeline.geoespacial extraer --zip 06_colima.zip      # una vez: polígonos AGEB de Manzanillo desde el zip oficial
    python -m pipeline.geoespacial extraer --descargar               # igual, descargando el zip (29 MB) de INEGI
    python -m pipeline.geoespacial agregar                           # DENUE (plata) x AGEB -> data/oro/manzanillo_oferta_ageb.csv

Fuentes y condiciones (detalle en docs/etica-datos.md):
  * Polígonos (data/oro/manzanillo_ageb_poligonos.geojson): «Fuente: INEGI, Marco Geoestadístico, Censo de Población y Vivienda 2020», términos de libre uso del INEGI.
    Se conservan solo las AGEB (urbanas y rurales) del municipio 06007 y se reproyectan de EPSG:6372 (ITRF2008 / LCC) a EPSG:4326.
  * Puntos: las coordenadas de la plata de DENUE (E1). Solo se usan para la unión espacial; el agregado no lleva CLEE, nombres
    ni coordenadas de establecimientos.

Salida agregada: un renglón por AGEB, con el total de establecimientos de la captura de referencia. Las celdas con 1 o 2
establecimientos no publican el conteo exacto (rango «1-2»), con el mismo umbral de 3 que usa el aviso RNF-PRI-03 de E1.
Lo que mide: oferta registrada en DENUE, no ocupación hotelera. GDAL no es necesario: los polígonos se leen con pyshp y se guardan como GeoJSON.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pandera.pandas as pa
import shapefile
import shapely
from pyproj import CRS
from shapely.geometry import shape

from .config import MUNICIPIO_CLAVE, RAIZ

URL_MG = ("https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/geografia/marcogeo/"
          "889463807469/06_colima.zip")
FICHA_MG = "https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=889463807469"
TERMINOS_INEGI = "https://www.inegi.org.mx/inegi/terminos.html"
ATRIBUCION_MG = ("Fuente: INEGI, Marco Geoestadístico, Censo de Población y Vivienda 2020. Transformación propia (filtro del "
                 "municipio 06007 y reproyección a EPSG:4326); no es un producto del INEGI ni está avalada por él.")
CRS_MG = CRS.from_epsg(6372)        # Mexico ITRF2008 / LCC, la proyección de los .prj del Marco Geoestadístico
CRS_SALIDA = "EPSG:4326"
CVE_ENT, CVE_MUN = MUNICIPIO_CLAVE[:2], MUNICIPIO_CLAVE[2:]
UMBRAL_CELDA = 3
RANGOS = ((1, 2, "1-2"), (3, 5, "3-5"), (6, 10, "6-10"))

RUTA_AGEB = RAIZ / "data" / "oro" / "manzanillo_ageb_poligonos.geojson"
RUTA_AGREGADO = RAIZ / "data" / "oro" / "manzanillo_oferta_ageb.csv"
COLUMNAS_AGREGADO = ["fecha_referencia", "cvegeo", "cve_loc", "cve_ageb", "tipo_ageb", "area_km2", "n_establecimientos", "rango",
                     "establecimientos_por_km2", "sha256_bronce", "sha256_poligonos", "ejecucion"]

ESQUEMA_AGREGADO = pa.DataFrameSchema({
    "fecha_referencia": pa.Column(str, pa.Check.str_matches(r"^\d{4}-\d{2}-\d{2}$")),
    "cvegeo": pa.Column(str, pa.Check.str_matches(r"^06007\d{4}[0-9A-Z]{4}$|^06007[0-9A-Z]{4}$"), unique=True),
    "cve_loc": pa.Column(str, nullable=True),
    "cve_ageb": pa.Column(str, pa.Check.str_length(min_value=4, max_value=4)),
    "tipo_ageb": pa.Column(str, pa.Check.isin(["urbana", "rural"])),
    "area_km2": pa.Column(float, pa.Check.gt(0)),
    "n_establecimientos": pa.Column("Int64", pa.Check.ge(0), nullable=True),
    "rango": pa.Column(str, pa.Check.isin(["0", "1-2", "3-5", "6-10", "11 o más"])),
    "establecimientos_por_km2": pa.Column(float, pa.Check.ge(0), nullable=True),
    "sha256_bronce": pa.Column(str, pa.Check.str_matches(r"^[0-9a-f]{64}$")),
    "sha256_poligonos": pa.Column(str, pa.Check.str_matches(r"^[0-9a-f]{64}$")),
    "ejecucion": pa.Column(str, pa.Check.str_startswith("geo-")),
}, strict=True, ordered=True, checks=[
    pa.Check(lambda d: (d["n_establecimientos"].isna()) == (d["rango"] == "1-2"), error="solo el rango 1-2 oculta el conteo exacto"),
])


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


# ---------------------------------------------------------------- polígonos AGEB (Marco Geoestadístico)
def descargar_mg(destino: Path, contacto: str = "proyecto academico TDL") -> str:
    """Descarga el zip oficial del estado 06 (una sola petición, con User-Agent identificable) y devuelve su SHA-256."""
    import urllib.request
    req = urllib.request.Request(URL_MG, headers={"User-Agent": f"TDL-turistico-colima ({contacto})"})
    with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310 - URL fija y oficial
        contenido = r.read()
    if not contenido.startswith(b"PK"):
        raise ValueError("la respuesta de INEGI no es un zip")
    Path(destino).write_bytes(contenido)
    return sha256_bytes(contenido)


def _leer_capa(z: zipfile.ZipFile, capa: str) -> gpd.GeoDataFrame:
    partes = {e: io.BytesIO(z.read(f"conjunto_de_datos/{capa}.{e}")) for e in ("shp", "shx", "dbf")}
    prj = z.read(f"conjunto_de_datos/{capa}.prj").decode("ascii", "ignore")
    if "MEXICO_ITRF_2008_LCC" not in prj:
        raise ValueError(f"{capa}.prj no es ITRF2008 / LCC: {prj[:60]}")
    r = shapefile.Reader(**partes, encoding="latin-1")
    filas = []
    for sr in r.iterShapeRecords():
        d = sr.record.as_dict()
        if d["CVE_ENT"] == CVE_ENT and d["CVE_MUN"] == CVE_MUN:
            filas.append({**d, "geometry": shape(sr.shape.__geo_interface__)})
    return gpd.GeoDataFrame(filas, geometry="geometry", crs=CRS_MG)


def extraer_ageb(ruta_zip: Path, salida: Path = RUTA_AGEB, descargado_utc: str | None = None, url: str = URL_MG) -> dict:
    """Zip oficial -> GeoJSON de las AGEB del municipio (urbanas y rurales) en EPSG:4326, con su ficha de procedencia."""
    contenido = Path(ruta_zip).read_bytes()
    with zipfile.ZipFile(io.BytesIO(contenido)) as z:
        urb, rur = _leer_capa(z, "06a"), _leer_capa(z, "06ar")
    if urb.empty:
        raise ValueError("el zip no trae AGEB urbanas del municipio 06007")
    urb = urb.assign(cve_loc=urb["CVE_LOC"], tipo_ageb="urbana")
    rur = rur.assign(cve_loc=None, tipo_ageb="rural")
    g = pd.concat([urb, rur], ignore_index=True)
    g = gpd.GeoDataFrame({"cvegeo": g["CVEGEO"], "cve_loc": g["cve_loc"], "cve_ageb": g["CVE_AGEB"], "tipo_ageb": g["tipo_ageb"],
                          "geometry": g.geometry}, geometry="geometry", crs=CRS_MG)
    g["area_km2"] = (g.geometry.area / 1e6).round(6)
    g = g.to_crs(CRS_SALIDA)
    g["geometry"] = shapely.set_precision(g.geometry.values, 1e-6)   # ~0.1 m; evita arrastrar decimales sin sentido
    g = g.sort_values("cvegeo").reset_index(drop=True)
    texto = g.to_json(drop_id=True, na="null", ensure_ascii=False) + "\n"
    Path(salida).parent.mkdir(parents=True, exist_ok=True)
    Path(salida).write_bytes(texto.encode("utf-8"))
    ficha = {
        "archivo": Path(salida).name, "sha256_geojson": sha256_bytes(texto.encode("utf-8")), "poligonos": int(len(g)),
        "poligonos_urbanos": int((g.tipo_ageb == "urbana").sum()), "poligonos_rurales": int((g.tipo_ageb == "rural").sum()),
        "fuente_zip": url, "ficha_producto": FICHA_MG, "terminos_de_uso": TERMINOS_INEGI, "edicion": "Marco Geoestadístico, Censo de Población y Vivienda 2020",
        "sha256_zip": sha256_bytes(contenido), "bytes_zip": len(contenido), "procesado_utc": descargado_utc or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "capas_usadas": ["06a (AGEB urbanas)", "06ar (AGEB rurales)"], "filtro": f"CVE_ENT={CVE_ENT}, CVE_MUN={CVE_MUN}",
        "crs_origen": "EPSG:6372 (Mexico ITRF2008 / LCC)", "crs_salida": CRS_SALIDA, "atribucion": ATRIBUCION_MG,
    }
    Path(str(salida) + ".meta.json").write_bytes((json.dumps(ficha, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return ficha


def cargar_ageb(ruta: Path = RUTA_AGEB, verificar: bool = True) -> gpd.GeoDataFrame:
    """Lee el GeoJSON sin GDAL; con ``verificar`` comprueba su SHA-256 contra la ficha."""
    ruta = Path(ruta)
    crudo = ruta.read_bytes()
    if verificar:
        ficha = json.loads(Path(str(ruta) + ".meta.json").read_text(encoding="utf-8"))
        if sha256_bytes(crudo) != ficha["sha256_geojson"]:
            raise ValueError(f"{ruta.name} no coincide con el SHA-256 de su ficha")
    fc = json.loads(crudo.decode("utf-8"))
    filas = [{**f["properties"], "geometry": shape(f["geometry"])} for f in fc["features"]]
    return gpd.GeoDataFrame(filas, geometry="geometry", crs=CRS_SALIDA)


# ---------------------------------------------------------------- unión espacial y agregado
def referencia(plata: pd.DataFrame, fecha: str | None = None) -> pd.DataFrame:
    """Captura de referencia de la plata: la fecha pedida o la más reciente."""
    fecha = fecha or str(plata["fecha_captura_local"].max())
    sel = plata[plata["fecha_captura_local"] == fecha]
    if sel.empty:
        raise ValueError(f"la plata no tiene la captura {fecha}")
    return sel


def unir_espacial(plata_ref: pd.DataFrame, ageb: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Unión espacial real: cada establecimiento (punto) con la AGEB que lo contiene (``within``)."""
    puntos = gpd.GeoDataFrame(plata_ref.reset_index(drop=True), geometry=gpd.points_from_xy(plata_ref["longitud"], plata_ref["latitud"]),
                              crs=CRS_SALIDA)
    unido = gpd.sjoin(puntos, ageb[["cvegeo", "cve_ageb", "tipo_ageb", "geometry"]], predicate="within", how="left")
    if len(unido) != len(puntos):
        raise ValueError("un punto cae en más de una AGEB: los polígonos se traslapan")
    return unido.drop(columns="index_right")


def _rango(n: int) -> str:
    if n == 0:
        return "0"
    for lo, hi, etiqueta in RANGOS:
        if lo <= n <= hi:
            return etiqueta
    return "11 o más"


def agregar_por_ageb(unido: gpd.GeoDataFrame, ageb: gpd.GeoDataFrame, fecha: str, sha_bronce: str, sha_poligonos: str) -> pd.DataFrame:
    """Un renglón por AGEB del municipio; conteo exacto solo si hay 3 o más establecimientos."""
    n = unido.dropna(subset=["cvegeo"]).groupby("cvegeo").size()
    base = pd.DataFrame(ageb.drop(columns="geometry")).copy()
    base["n_real"] = base["cvegeo"].map(n).fillna(0).astype(int)
    base["rango"] = base["n_real"].map(_rango)
    oculto = (base["n_real"] > 0) & (base["n_real"] < UMBRAL_CELDA)
    base["n_establecimientos"] = pd.array(base["n_real"].where(~oculto, None), dtype="Int64")
    base["establecimientos_por_km2"] = (base["n_real"] / base["area_km2"]).where(~oculto, None).astype(float).round(3)
    base["fecha_referencia"] = fecha
    base["sha256_bronce"], base["sha256_poligonos"] = sha_bronce, sha_poligonos
    base["ejecucion"] = f"geo-{sha_bronce[:12]}-{sha_poligonos[:12]}-v1"
    return base[COLUMNAS_AGREGADO].sort_values("cvegeo").reset_index(drop=True)


def hash_bronce(plata_ref: pd.DataFrame) -> str:
    """SHA-256 que identifica la captura de referencia: el de su respuesta de BuscarAreaAct (o el combinado si fueran varias)."""
    hashes = sorted(plata_ref["sha256_bronce"].unique())
    return hashes[0] if len(hashes) == 1 else sha256_bytes("".join(hashes).encode())


def ejecutar(raiz: Path = RAIZ, plata: pd.DataFrame | None = None, fecha: str | None = None) -> dict:
    """DENUE (plata) x AGEB -> ``data/oro/manzanillo_oferta_ageb.csv`` y su ficha."""
    if plata is None:
        from .calidad.cuarentena import Cuarentena
        from .plata_denue import procesar_capturas
        plata = procesar_capturas(Path(raiz) / "data" / "bronce" / "denue", Cuarentena(datetime.now(timezone.utc).isoformat(timespec="seconds")))
    ruta_ageb = Path(raiz) / RUTA_AGEB.relative_to(RAIZ)
    ageb = cargar_ageb(ruta_ageb)
    ref = referencia(plata, fecha)
    unido = unir_espacial(ref, ageb)
    sin_ageb = int(unido["cvegeo"].isna().sum())
    ok = unido.dropna(subset=["cvegeo"])
    concordancia = float((ok["ageb"] == ok["cve_ageb"]).mean()) if len(ok) else 0.0
    fecha_ref = str(ref["fecha_captura_local"].iloc[0])
    agregado = agregar_por_ageb(unido, ageb, fecha_ref, hash_bronce(ref), sha256_archivo(ruta_ageb))
    ESQUEMA_AGREGADO.validate(agregado)
    if int(agregado["n_establecimientos"].fillna(0).sum() + 0) > len(ok):
        raise ValueError("el agregado cuenta más establecimientos que los unidos")
    salida = Path(raiz) / RUTA_AGREGADO.relative_to(RAIZ)
    csv = agregado.to_csv(index=False, float_format="%.6f", lineterminator="\n")
    salida.write_bytes(csv.encode("utf-8"))
    ficha = {
        "archivo": salida.name, "sha256_csv": sha256_bytes(csv.encode("utf-8")), "filas": int(len(agregado)), "fecha_referencia": fecha_ref,
        "establecimientos_en_plata": int(len(ref)), "establecimientos_con_ageb": int(len(ok)), "establecimientos_sin_ageb": sin_ageb,
        "agebs_con_establecimientos": int((agregado["rango"] != "0").sum()), "agebs_con_conteo_oculto": int((agregado["rango"] == "1-2").sum()),
        "concordancia_ageb_denue_poligono": round(concordancia, 4), "umbral_celda": UMBRAL_CELDA,
        "fuentes": {"denue": f"plata de DENUE, captura {fecha_ref} (data/bronce/denue/{fecha_ref}/)", "poligonos": RUTA_AGEB.name, "sha256_bronce": agregado["sha256_bronce"].iloc[0],
                    "sha256_poligonos": agregado["sha256_poligonos"].iloc[0]},
        "atribucion": ATRIBUCION_MG + " Establecimientos: Fuente: INEGI, DENUE (términos de libre uso del INEGI).",
        "nota": "Conteo de establecimientos del DENUE por AGEB; no es ocupación hotelera ni mide demanda. Sin CLEE, nombres ni coordenadas.",
    }
    Path(str(salida).replace(".csv", ".meta.json")).write_bytes((json.dumps(ficha, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return ficha


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="orden", required=True)
    e = sub.add_parser("extraer", help="zip oficial del Marco Geoestadístico -> GeoJSON de AGEB de Manzanillo")
    g = e.add_mutually_exclusive_group(required=True)
    g.add_argument("--zip", type=Path)
    g.add_argument("--descargar", action="store_true")
    a = sub.add_parser("agregar", help="DENUE x AGEB -> data/oro/manzanillo_oferta_ageb.csv")
    a.add_argument("--fecha", default=None)
    args = ap.parse_args(argv)
    if args.orden == "extraer":
        ruta, momento = args.zip, None
        if args.descargar:
            ruta = Path("06_colima.zip")
            descargar_mg(ruta)
            momento = datetime.now(timezone.utc).isoformat(timespec="seconds")
        print(json.dumps(extraer_ageb(ruta, descargado_utc=momento), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(ejecutar(fecha=args.fecha), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
