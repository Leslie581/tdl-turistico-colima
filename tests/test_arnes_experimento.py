"""Arnés del experimento 2^3 de E2 (laboratorio/experimento/arnes.py): factores reales, registro, errores y seguridad.

Usa una copia de dos capturas reales del bronce DENUE en un directorio temporal; nunca escribe en el repositorio.
"""
import json
import shutil
import socket
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("pyarrow")
pytest.importorskip("orjson")

from laboratorio.experimento import arnes as ar  # noqa: E402
from laboratorio.experimento import matriz as mz  # noqa: E402

DIAS = sorted(p for p in ar.BRONCE_DENUE.iterdir() if p.is_dir() and any(p.glob("*_02_BuscarAreaAct.json")))[:2]
pytestmark = pytest.mark.skipif(len(DIAS) < 2, reason="requiere al menos dos días de bronce DENUE")


@pytest.fixture
def bronce(tmp_path):
    destino = tmp_path / "bronce_denue"
    for d in DIAS:
        shutil.copytree(d, destino / d.name)
    return destino


@pytest.fixture
def carga(tmp_path, bronce):
    return ar.preparar_carga(tmp_path / "carga", copias=2, bronce=bronce)


def _sin_red(monkeypatch):
    def prohibido(*a, **k):
        raise AssertionError("el arnés intentó abrir una conexión de red")
    monkeypatch.setattr(socket.socket, "connect", prohibido)
    monkeypatch.setattr(socket, "create_connection", prohibido)


# ---------------------------------------------------------------- matriz, réplicas y orden
def test_el_bloque_sigue_el_orden_aleatorizado_de_la_matriz_y_asigna_la_replica(tmp_path, bronce):
    salida = tmp_path / "r.jsonl"
    hechos = ar.ejecutar_bloque("dia_2", salida, copias=1, bronce=bronce, piloto=True, calentamiento=False, solo=[1, 2, 3, 4])
    esperado = mz.matriz().query("bloque == 'dia_2' and tratamiento <= 4").sort_values("corrida")
    assert [r["tratamiento"] for r in hechos] == esperado.tratamiento.tolist()
    assert {r["replica"] for r in hechos} == {2} and all(r["semilla"] == mz.SEMILLA for r in hechos)
    for r, (_, f) in zip(hechos, esperado.iterrows()):
        assert (r["procesos"], r["analizador"], r["formato"]) == (f.procesos, f.analizador, f.formato)
        assert (r["procesos_cod"], r["analizador_cod"], r["formato_cod"]) == (f.procesos_cod, f.analizador_cod, f.formato_cod)


def test_cada_tratamiento_tiene_dos_replicas_una_por_bloque():
    m = mz.matriz()
    assert (m.groupby("tratamiento").bloque.nunique() == 2).all() and len(m) == 16
    assert [mz.BLOQUES.index(b) + 1 for b in mz.BLOQUES] == [1, 2]


def test_no_repite_tratamientos_ya_registrados(tmp_path, bronce):
    salida = tmp_path / "r.jsonl"
    primera = ar.ejecutar_bloque("dia_1", salida, copias=1, bronce=bronce, piloto=True, calentamiento=False, solo=[1, 3])
    segunda = ar.ejecutar_bloque("dia_1", salida, copias=1, bronce=bronce, piloto=True, calentamiento=False, solo=[1, 3])
    assert len(primera) == 2 and segunda == [] and len(ar.leer_registros(salida)) == 2


# ---------------------------------------------------------------- los factores cambian el procesamiento
def test_factor_procesos_reparte_el_trabajo_en_otros_procesos(tmp_path, carga):
    uno = ar.ejecutar_corrida(carga, 1, "json", "csv", tmp_path / "a")
    cuatro = ar.ejecutar_corrida(carga, 4, "json", "csv", tmp_path / "b")
    assert uno["estado"] == cuatro["estado"] == "ok"
    assert uno["evidencia_factores"]["pids_distintos"] == 1 and not uno["evidencia_factores"]["trabajo_fuera_del_proceso_principal"]
    assert cuatro["evidencia_factores"]["trabajo_fuera_del_proceso_principal"] and cuatro["evidencia_factores"]["pids_distintos"] >= 2
    assert uno["registros_salida"] == cuatro["registros_salida"] > 0


def test_factor_analizador_usa_orjson_de_verdad_y_da_el_mismo_resultado(tmp_path, carga, monkeypatch):
    import orjson
    llamadas = []
    original = orjson.loads
    monkeypatch.setattr(orjson, "loads", lambda b: llamadas.append(1) or original(b))
    r = ar.ejecutar_corrida(carga, 1, "orjson", "csv", tmp_path / "o")
    assert r["estado"] == "ok" and len(llamadas) == r["capturas"]
    assert r["evidencia_factores"]["analizador"].endswith("analizar_orjson")
    contenido = carga["archivos"][0].read_bytes()
    assert ar.ANALIZADORES["json"](contenido) == ar.ANALIZADORES["orjson"](contenido)
    assert ar.ANALIZADORES["orjson"](ar.BOM + b'[{"a": 1}]') == [{"a": 1}]


def test_factor_formato_escribe_csv_o_parquet_real(tmp_path, carga):
    csv = ar.ejecutar_corrida(carga, 1, "json", "csv", tmp_path / "c")
    par = ar.ejecutar_corrida(carga, 1, "json", "parquet", tmp_path / "p")
    assert par["evidencia_factores"]["es_parquet"] and not csv["evidencia_factores"]["es_parquet"]
    assert bytes.fromhex(csv["evidencia_factores"]["cabecera_salida"]) == b"fech"          # encabezado del CSV
    assert csv["evidencia_factores"]["bytes_salida"] != par["evidencia_factores"]["bytes_salida"]
    assert csv["tasa_error"] == par["tasa_error"] == 0.0                                    # ambos formatos se releen idénticos


# ---------------------------------------------------------------- registro de las mediciones
def test_el_registro_trae_niveles_tiempos_errores_entorno_codigo_y_carga(tmp_path, bronce):
    salida = tmp_path / "r.jsonl"
    ar.ejecutar_bloque("dia_1", salida, copias=1, bronce=bronce, piloto=True, calentamiento=False, solo=[2])
    (r,) = [json.loads(x) for x in salida.read_text(encoding="utf-8").splitlines()]
    for clave in ("bloque", "replica", "orden_en_bloque", "tratamiento", "procesos", "analizador", "formato", "tiempo_s",
                  "tasa_error", "capturas", "capturas_con_error", "errores", "inicio_utc", "fin_utc", "fecha_local",
                  "semilla", "commit", "codigo_modificado", "version_arnes", "entorno", "carga", "piloto"):
        assert clave in r, clave
    assert r["piloto"] is True and r["estado"] == "ok"
    partes = r["tiempo_procesamiento_s"] + r["tiempo_escritura_s"] + r["tiempo_lectura_s"]
    assert r["tiempo_s"] == pytest.approx(partes, abs=1e-5) and r["tiempo_s"] > 0
    assert r["carga"]["capturas_en_carga"] == r["capturas"] and "sintética" in r["carga"]["tipo_carga"]
    assert len(r["entorno"]["equipo_id"]) == 12 and r["entorno"]["bibliotecas"]["orjson"]


# ---------------------------------------------------------------- datos originales, red y carga fuera del repositorio
def test_no_modifica_el_bronce_ni_prepara_la_carga_dentro_del_repositorio(tmp_path, bronce):
    antes = ar.huella_bronce(bronce)
    ar.ejecutar_bloque("dia_1", tmp_path / "r.jsonl", copias=1, bronce=bronce, piloto=True, calentamiento=False, solo=[1])
    assert ar.huella_bronce(bronce) == antes
    with pytest.raises(ValueError, match="fuera del repositorio"):
        ar.preparar_carga(ar.RAIZ / "data" / "tmp_carga", copias=1, bronce=bronce)
    assert not (ar.RAIZ / "data" / "tmp_carga").exists()


def test_no_abre_conexiones_de_red(tmp_path, carga, monkeypatch):
    _sin_red(monkeypatch)
    for analizador in ("json", "orjson"):
        assert ar.ejecutar_corrida(carga, 1, analizador, "parquet", tmp_path / analizador)["estado"] == "ok"
    fuente = Path(ar.__file__).read_text(encoding="utf-8")
    for modulo in ("requests", "urllib", "http.client", "socket", "extractores"):
        assert f"import {modulo}" not in fuente and f"from {modulo}" not in fuente


# ---------------------------------------------------------------- manejo de errores
def test_cuenta_como_error_las_capturas_que_la_puerta_rechaza(tmp_path, bronce):
    carga = ar.preparar_carga(tmp_path / "carga", copias=2, bronce=bronce, fallos=2)
    r = ar.ejecutar_corrida(carga, 1, "json", "csv", tmp_path / "t")
    assert r["estado"] == "ok" and r["capturas_con_error"] == 2
    assert r["tasa_error"] == pytest.approx(2 / r["capturas"])
    assert {(e["tipo"], e["regla"]) for e in r["errores"]} == {("PUERTA", "INTEGRIDAD")}
    assert carga["fallos_sinteticos_inyectados"] == 2


def test_un_analizador_que_falla_se_registra_como_excepcion_sin_inventar_filas(tmp_path, carga, monkeypatch):
    def roto(_):
        raise ImportError("orjson no instalado")
    monkeypatch.setitem(ar.ANALIZADORES, "orjson", roto)
    r = ar.ejecutar_corrida(carga, 1, "orjson", "csv", tmp_path / "t")
    assert r["tasa_error"] == 1.0 and r["registros_salida"] == 0
    assert {e["tipo"] for e in r["errores"]} == {"EXCEPCION"}


def test_una_corrida_que_falla_queda_como_fallo_y_sin_tiempo(tmp_path, carga, monkeypatch):
    def falla(*a, **k):
        raise OSError("disco lleno")
    monkeypatch.setattr(ar, "escribir_salida", falla)
    r = ar.ejecutar_corrida(carga, 1, "json", "csv", tmp_path / "t")
    assert r["estado"] == "fallo" and r["tiempo_s"] is None and r["tasa_error"] is None and "disco lleno" in r["error_corrida"]


def test_detecta_filas_que_no_se_recuperan_al_releer():
    df = pd.DataFrame({"archivo_bronce": ["a", "a", "b"], "v": ["1", "2", "3"]})
    assert ar.archivos_no_recuperados(df, df.copy()) == set()
    assert ar.archivos_no_recuperados(df, df.assign(v=["1", "2", "X"])) == {"b"}
    assert ar.archivos_no_recuperados(df, df.iloc[:2]) == {"a", "b"}


def test_rechaza_niveles_fuera_del_diseno_y_protege_el_archivo_oficial(tmp_path, carga):
    with pytest.raises(ValueError):
        ar.ejecutar_corrida(carga, 2, "json", "csv", tmp_path / "t")
    with pytest.raises(ValueError):
        ar.ejecutar_bloque("dia_1", ar.SALIDA, piloto=True)
    with pytest.raises(RuntimeError):
        ar.ejecutar_bloque("dia_1", tmp_path / "r.jsonl", fallos=1)
    with pytest.raises(ValueError):
        ar.ejecutar_bloque("dia_3", tmp_path / "r.jsonl", piloto=True)


# ---------------------------------------------------------------- reproducibilidad
def test_el_procedimiento_es_reproducible(tmp_path, bronce):
    a = ar.preparar_carga(tmp_path / "a", copias=2, bronce=bronce)
    b = ar.preparar_carga(tmp_path / "b", copias=2, bronce=bronce)
    assert a["sha256_capturas_fuente"] == b["sha256_capturas_fuente"] and a["capturas_en_carga"] == b["capturas_en_carga"]
    r = [ar.ejecutar_corrida(a, 1, an, fo, tmp_path / f"{an}{fo}") for an in ("json", "orjson") for fo in ("csv", "parquet")]
    assert len({x["registros_salida"] for x in r}) == 1 and all(x["tasa_error"] == 0.0 for x in r)
    raiz = str(a["raiz"])
    plata = [ar.procesar_archivo((str(p), raiz, an))["filas"] for p in a["archivos"][:2] for an in ("json", "orjson")]
    assert plata[0].equals(plata[1]) and plata[2].equals(plata[3])                         # json y orjson: plata idéntica


def test_el_arnes_no_cambia_la_plata_del_pipeline(bronce):
    from pipeline.calidad.cuarentena import Cuarentena
    from pipeline.plata_denue import procesar_capturas
    plata = procesar_capturas(bronce, Cuarentena("prueba"))
    assert len(plata) > 0 and list(plata.columns) == ar.plata_denue.COLUMNAS_PLATA
