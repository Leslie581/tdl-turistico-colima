"""Fuente geoespacial de E2: extracción de polígonos, unión espacial, agregación con supresión de celdas pequeñas, integridad y linaje."""
import io
import json
import shutil
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
import shapefile
from pyproj import Transformer
from shapely.geometry import Polygon, box

from pipeline import geoespacial as geo
from pipeline import linaje
from pipeline.calidad.cuarentena import Cuarentena
from pipeline.plata_denue import procesar_capturas

RAIZ = Path(__file__).resolve().parents[1]
PRJ_LCC = ('PROJCS["MEXICO_ITRF_2008_LCC",GEOGCS["GCS_ITRF_2008",DATUM["D_ITRF_2008",SPHEROID["GRS_1980",6378137.0,298.257222101]],'
           'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["False_Easting",2500000.0],'
           'PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-102.0],PARAMETER["Standard_Parallel_1",17.5],'
           'PARAMETER["Standard_Parallel_2",29.5],PARAMETER["Latitude_Of_Origin",12.0],UNIT["Meter",1.0]]')


def _capa(campos, filas):
    """SINTÉTICO: capa de polígonos cuadrados en coordenadas LCC (alrededor de Manzanillo) como las del Marco Geoestadístico."""
    a_lcc = Transformer.from_crs(4326, 6372, always_xy=True)
    partes = {e: io.BytesIO() for e in ("shp", "shx", "dbf")}
    w = shapefile.Writer(**partes, shapeType=shapefile.POLYGON, encoding="latin-1")
    for c in campos:
        w.field(c, "C", size=14)
    for valores, (lon0, lat0) in filas:
        x0, y0 = a_lcc.transform(lon0, lat0)
        x1, y1 = a_lcc.transform(lon0 + 0.01, lat0 + 0.01)
        w.poly([[[x0, y0], [x0, y1], [x1, y1], [x1, y0], [x0, y0]]])
        w.record(*valores)
    w.close()
    return {e: p.getvalue() for e, p in partes.items()}


def _zip_sintetico(ruta):
    urb = _capa(["CVEGEO", "CVE_ENT", "CVE_MUN", "CVE_LOC", "CVE_AGEB"], [
        (("0600700010001", "06", "007", "0001", "0001"), (-104.32, 19.05)),
        (("0600700010002", "06", "007", "0001", "0002"), (-104.30, 19.05)),
        (("0600200010003", "06", "002", "0001", "0003"), (-103.80, 19.20)),   # otro municipio: se descarta
    ])
    rur = _capa(["CVEGEO", "CVE_ENT", "CVE_MUN", "CVE_AGEB"], [(("060070004", "06", "007", "004A"), (-104.40, 18.95))])
    with zipfile.ZipFile(ruta, "w") as z:
        for capa, partes in (("06a", urb), ("06ar", rur)):
            for ext, contenido in partes.items():
                z.writestr(f"conjunto_de_datos/{capa}.{ext}", contenido)
            z.writestr(f"conjunto_de_datos/{capa}.prj", PRJ_LCC)


@pytest.fixture()
def ageb_sintetico(tmp_path):
    z = tmp_path / "mg.zip"
    _zip_sintetico(z)
    salida = tmp_path / "ageb.geojson"
    ficha = geo.extraer_ageb(z, salida, descargado_utc="2026-11-22T00:00:00+00:00")
    return salida, ficha


def test_extraer_filtra_el_municipio_reproyecta_y_conserva_procedencia(ageb_sintetico):
    salida, ficha = ageb_sintetico
    g = geo.cargar_ageb(salida)
    assert sorted(g["cve_ageb"]) == ["0001", "0002", "004A"] and set(g["tipo_ageb"]) == {"urbana", "rural"}
    x, y = g.geometry.iloc[0].centroid.x, g.geometry.iloc[0].centroid.y
    assert -104.5 < x < -104.2 and 18.9 < y < 19.1                      # EPSG:4326 de Manzanillo, no metros de LCC
    assert g["area_km2"].between(0.9, 1.3).all()                        # 0.01° x 0.01° ≈ 1.1 km²
    assert ficha["crs_origen"].startswith("EPSG:6372") and len(ficha["sha256_zip"]) == 64 and "INEGI" in ficha["atribucion"]


def test_la_alteracion_del_geojson_se_detecta(ageb_sintetico, tmp_path):
    salida, _ = ageb_sintetico
    copia = tmp_path / "otra.geojson"
    shutil.copy(salida, copia)
    shutil.copy(str(salida) + ".meta.json", str(copia) + ".meta.json")
    copia.write_text(copia.read_text(encoding="utf-8").replace("0001", "9999", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256"):
        geo.cargar_ageb(copia)


def _plata(puntos):
    return pd.DataFrame({"fecha_captura_local": "2026-11-21", "clee": [f"C{i}" for i in range(len(puntos))], "ageb": [p[2] for p in puntos],
                         "longitud": [p[0] for p in puntos], "latitud": [p[1] for p in puntos], "sha256_bronce": "a" * 64})


def test_union_espacial_asigna_cada_punto_a_su_poligono_y_deja_fuera_los_ajenos(ageb_sintetico):
    ageb = geo.cargar_ageb(ageb_sintetico[0])
    plata = _plata([(-104.315, 19.055, "0001"), (-104.295, 19.055, "0002"), (-104.0, 19.5, "0003")])
    u = geo.unir_espacial(plata, ageb)
    assert list(u["cve_ageb"].fillna("fuera")) == ["0001", "0002", "fuera"]
    assert (u.dropna(subset=["cve_ageb"])["ageb"] == u.dropna(subset=["cve_ageb"])["cve_ageb"]).all()


def test_poligonos_traslapados_se_rechazan():
    a = gpd.GeoDataFrame({"cvegeo": ["x1", "x2"], "cve_ageb": ["1", "2"], "tipo_ageb": ["urbana"] * 2}, geometry=[box(0, 0, 2, 2), box(1, 1, 3, 3)], crs=4326)
    plata = pd.DataFrame({"longitud": [1.5], "latitud": [1.5]})
    with pytest.raises(ValueError, match="traslapan"):
        geo.unir_espacial(plata, a)


def test_agregado_cuenta_oculta_celdas_de_1_o_2_y_valida_el_esquema(ageb_sintetico):
    ageb = geo.cargar_ageb(ageb_sintetico[0])
    ageb["cvegeo"] = ["060070001" + c if len(c) == 4 and t == "urbana" else "06007" + c for c, t in zip(ageb["cve_ageb"], ageb["tipo_ageb"])]
    ageb["cve_loc"] = [("0001" if t == "urbana" else None) for t in ageb["tipo_ageb"]]
    pts = [(-104.315, 19.055, "0001")] * 4 + [(-104.295, 19.055, "0002")]          # 4 en la AGEB 0001, 1 en la 0002
    u = geo.unir_espacial(_plata(pts), ageb)
    ag = geo.agregar_por_ageb(u, ageb, "2026-11-21", "a" * 64, "b" * 64).set_index("cve_ageb")
    assert ag.loc["0001", "n_establecimientos"] == 4 and ag.loc["0001", "rango"] == "3-5"
    assert pd.isna(ag.loc["0002", "n_establecimientos"]) and ag.loc["0002", "rango"] == "1-2" and pd.isna(ag.loc["0002", "establecimientos_por_km2"])
    assert ag.loc["004A", "rango"] == "0" and ag.loc["004A", "n_establecimientos"] == 0
    geo.ESQUEMA_AGREGADO.validate(ag.reset_index()[geo.COLUMNAS_AGREGADO])
    assert not {"clee", "latitud", "longitud", "nombre"} & set(ag.columns)


def test_esquema_rechaza_un_conteo_exacto_en_el_rango_1_2():
    fila = {"fecha_referencia": "2026-11-21", "cvegeo": "060070001009A", "cve_loc": "0001", "cve_ageb": "009A", "tipo_ageb": "urbana", "area_km2": 1.0,
            "n_establecimientos": pd.array([2], dtype="Int64")[0], "rango": "1-2", "establecimientos_por_km2": 2.0, "sha256_bronce": "a" * 64,
            "sha256_poligonos": "b" * 64, "ejecucion": "geo-aaaaaaaaaaaa-bbbbbbbbbbbb-v1"}
    df = pd.DataFrame([fila]).astype({"n_establecimientos": "Int64"})
    with pytest.raises(Exception):
        geo.ESQUEMA_AGREGADO.validate(df)


# ---------------------------------------------------------------- con los datos reales versionados
FICHA = json.loads((RAIZ / "data" / "oro" / "manzanillo_oferta_ageb.meta.json").read_text(encoding="utf-8"))


def test_el_agregado_versionado_ubica_todos_los_establecimientos_y_concuerda_con_denue():
    assert FICHA["establecimientos_sin_ageb"] == 0 and FICHA["establecimientos_con_ageb"] == FICHA["establecimientos_en_plata"]
    assert FICHA["concordancia_ageb_denue_poligono"] == 1.0                  # la AGEB espacial coincide con la clave AGEB que trae el DENUE
    df = pd.read_csv(RAIZ / "data" / "oro" / "manzanillo_oferta_ageb.csv", dtype=str)
    assert list(df.columns) == geo.COLUMNAS_AGREGADO and len(df) == FICHA["filas"] == 154
    assert geo.sha256_archivo(RAIZ / "data" / "oro" / "manzanillo_oferta_ageb.csv") == FICHA["sha256_csv"]
    assert geo.sha256_archivo(geo.RUTA_AGEB) == json.loads(Path(str(geo.RUTA_AGEB) + ".meta.json").read_text(encoding="utf-8"))["sha256_geojson"]


def test_el_agregado_se_regenera_identico_desde_el_bronce(tmp_path):
    """Reproducibilidad: DENUE real (bronce) x polígonos versionados -> el mismo CSV, byte a byte."""
    plata = procesar_capturas(RAIZ / "data" / "bronce" / "denue", Cuarentena("2026-11-22T00:00:00+00:00"))
    (tmp_path / "data" / "oro").mkdir(parents=True)
    for nombre in ("manzanillo_ageb_poligonos.geojson", "manzanillo_ageb_poligonos.geojson.meta.json"):
        shutil.copy(RAIZ / "data" / "oro" / nombre, tmp_path / "data" / "oro" / nombre)
    ficha = geo.ejecutar(raiz=tmp_path, plata=plata, fecha=FICHA["fecha_referencia"])
    assert ficha["sha256_csv"] == FICHA["sha256_csv"]
    assert (tmp_path / "data/oro/manzanillo_oferta_ageb.csv").read_bytes() == (RAIZ / "data/oro/manzanillo_oferta_ageb.csv").read_bytes()


# ---------------------------------------------------------------- linaje
def test_el_linaje_del_oro_esta_completo():
    r = linaje.verificar_linaje(RAIZ)
    assert r["completo"], r["fallas"][:3]
    assert r["registros_mensuales"] == 108 and r["agebs"] == 154 and r["capturas_de_oferta"] >= 4


def test_la_cadena_de_una_ageb_llega_al_zip_oficial_de_inegi():
    c = linaje.rastrear_ageb("060070001009A", RAIZ)
    assert c["coincide"] and c["denue"]["en_la_captura"] and c["poligonos"]["coincide"]
    assert c["poligonos"]["fuente_zip"].startswith("https://www.inegi.org.mx/") and len(c["poligonos"]["sha256_zip_inegi"]) == 64
    assert linaje.rastrear_mensual("2020-04", RAIZ)["coincide"]


def test_un_archivo_de_bronce_alterado_rompe_el_linaje(tmp_path):
    origen = RAIZ / "data" / "bronce" / "denue" / FICHA["fecha_referencia"]
    destino = tmp_path / "data" / "bronce" / "denue" / FICHA["fecha_referencia"]
    shutil.copytree(origen, destino)
    assert all(x["coincide"] for x in linaje.archivos_bronce_denue(tmp_path, FICHA["fecha_referencia"]))
    archivo = next(destino.glob("*BuscarAreaAct.json"))
    archivo.write_bytes(archivo.read_bytes() + b" ")
    assert not all(x["coincide"] for x in linaje.archivos_bronce_denue(tmp_path, FICHA["fecha_referencia"]))


def test_un_poligono_es_valido_y_dentro_de_manzanillo():
    g = geo.cargar_ageb()
    assert g.geometry.is_valid.all() and g.geometry.map(lambda p: isinstance(p, Polygon) or p.geom_type == "MultiPolygon").all()
    # El municipio incluye islas oceánicas (rurales, sin establecimientos): los polígonos con establecimientos sí están en el continente.
    ag = pd.read_csv(RAIZ / "data" / "oro" / "manzanillo_oferta_ageb.csv", dtype={"cvegeo": str})
    con = g[g["cvegeo"].isin(ag.loc[ag["rango"] != "0", "cvegeo"])]
    minx, miny, maxx, maxy = con.total_bounds
    assert -104.9 < minx and maxx < -103.9 and 18.6 < miny and maxy < 19.5
