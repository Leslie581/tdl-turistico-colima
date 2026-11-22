"""Experimento de dos factores de E2 (laboratorio/experimento/dos_factores.py): matriz, ejecución segura y ANOVA."""
import json
import shutil
import socket

import numpy as np
import pytest

pytest.importorskip("statsmodels")
pytest.importorskip("matplotlib")

from laboratorio.experimento import arnes as ar  # noqa: E402
from laboratorio.experimento import dos_factores as df2  # noqa: E402

DIAS = sorted(p for p in ar.BRONCE_DENUE.iterdir() if p.is_dir() and any(p.glob("*_02_BuscarAreaAct.json")))[:2]


@pytest.fixture
def bronce(tmp_path):
    if len(DIAS) < 2:
        pytest.skip("requiere dos días de bronce DENUE")
    destino = tmp_path / "bronce_denue"
    for d in DIAS:
        shutil.copytree(d, destino / d.name)
    return destino


def _registros(ruta, semilla_ruido=0, quitar=0, estado_fallo=None):
    """Registros de PRUEBA (no son mediciones): tiempos con efectos conocidos para comprobar los cálculos."""
    rng = np.random.default_rng(semilla_ruido)
    filas = []
    for p in df2.matriz().to_dict("records"):
        t = 0.5 * p["carga"] + (3.0 if p["procesos"] == 4 else 0.0) - (0.25 * p["carga"] if p["procesos"] == 4 else 0.0)
        filas.append({**{k: int(v) if isinstance(v, (np.integer,)) else v for k, v in p.items()},
                      "tiempo_s": t + 0.1 * p["bloque"] + rng.normal(0, 0.3), "tasa_error": 0.0, "capturas": 2 * p["carga"],
                      "estado": "ok", "semilla": df2.SEMILLA, "piloto": False})
    if estado_fallo:
        filas[estado_fallo - 1] |= {"estado": "fallo", "tiempo_s": None}
    filas = filas[: len(filas) - quitar]
    ruta.write_text("\n".join(json.dumps(f) for f in filas) + "\n", encoding="utf-8")
    return ruta


# ---------------------------------------------------------------- matriz
def test_matriz_6_tratamientos_en_4_bloques_completos_aleatorizada_y_reproducible():
    m = df2.matriz()
    assert len(m) == 24 and m.secuencia.tolist() == list(range(1, 25))
    assert (m.groupby("bloque").tratamiento.apply(sorted) == [list(range(1, 7))] * 4).all()
    assert m.equals(df2.matriz()) and not m.tratamiento.equals(df2.matriz(1).tratamiento)
    assert m.tratamiento.tolist() != list(range(1, 7)) * 4                    # no es el orden estándar
    assert {(v["carga"], v["procesos"]) for v in df2.TRATAMIENTOS.values()} == {(c, p) for c in (1, 5, 10) for p in (1, 4)}
    assert set(m.analizador) == {"json"} and set(m.formato) == {"csv"}


# ---------------------------------------------------------------- ejecución
def test_ejecuta_los_niveles_de_verdad_y_no_repite(tmp_path, bronce):
    salida = tmp_path / "e.jsonl"
    m = df2.matriz()
    solo = [int(m.secuencia[(m.carga == c) & (m.procesos == p)].iloc[0]) for c, p in ((1, 1), (5, 4), (10, 1))]
    hechas = df2.ejecutar(salida, bronce=bronce, piloto=True, calentamiento=False, solo=solo)
    assert sorted(r["secuencia"] for r in hechas) == sorted(solo)
    for r in hechas:
        assert r["estado"] == "ok" and r["tasa_error"] == 0.0 and r["sesion"] == "dos_factores" and r["piloto"]
        assert r["capturas"] == r["carga"] * r["carga_manifiesto"]["capturas_fuente"] == r["carga_manifiesto"]["capturas_en_carga"]
        ev = r["evidencia_factores"]
        assert ev["analizador"].endswith("analizar_json") and not ev["es_parquet"]
        assert (ev["pids_distintos"] == 1) == (r["procesos"] == 1) and ev["trabajo_fuera_del_proceso_principal"] == (r["procesos"] == 4)
        assert {"commit", "codigo_modificado", "entorno", "condiciones", "fecha_local", "bloque"} <= set(r)
    bytes_por_carga = {r["carga"]: r["evidencia_factores"]["bytes_salida"] for r in hechas}
    assert bytes_por_carga[1] < bytes_por_carga[5] < bytes_por_carga[10]      # la carga crece de verdad
    assert df2.ejecutar(salida, bronce=bronce, piloto=True, calentamiento=False, solo=solo) == []


def test_protege_archivos_anteriores_y_exige_codigo_confirmado(tmp_path, monkeypatch):
    for p in df2.PROTEGIDOS:
        with pytest.raises(ValueError):
            df2.ejecutar(p, piloto=True)
    with pytest.raises(ValueError):
        df2.ejecutar(df2.SALIDA, piloto=True)
    monkeypatch.setattr(ar, "codigo_modificado", lambda *_: True)
    with pytest.raises(RuntimeError):
        df2.ejecutar(tmp_path / "e.jsonl")


def test_no_modifica_el_bronce_ni_abre_conexiones(tmp_path, bronce, monkeypatch):
    def prohibido(*a, **k):
        raise AssertionError("conexión de red")
    monkeypatch.setattr(socket.socket, "connect", prohibido)
    monkeypatch.setattr(socket, "create_connection", prohibido)
    monkeypatch.setattr(df2, "condiciones_equipo", lambda: {})
    antes = ar.huella_bronce(bronce)
    m = df2.matriz()
    solo = m.secuencia[(m.procesos == 1) & (m.carga == 1)].tolist()[:2]
    assert len(df2.ejecutar(tmp_path / "e.jsonl", bronce=bronce, piloto=True, calentamiento=False, solo=solo)) == 2
    assert ar.huella_bronce(bronce) == antes


def test_una_corrida_fallida_se_registra_y_bloquea_el_analisis(tmp_path, bronce, monkeypatch):
    def falla(*a, **k):
        raise OSError("disco lleno")
    monkeypatch.setattr(ar, "escribir_salida", falla)
    salida = tmp_path / "e.jsonl"
    (r,) = df2.ejecutar(salida, bronce=bronce, piloto=True, calentamiento=False, solo=[1])
    assert r["estado"] == "fallo" and r["tiempo_s"] is None
    with pytest.raises(ValueError):
        df2.cargar(salida, incluir_piloto=True)
    with pytest.raises(ValueError):
        df2.cargar(_registros(tmp_path / "f.jsonl", estado_fallo=5))
    with pytest.raises(ValueError):
        df2.cargar(_registros(tmp_path / "i.jsonl", quitar=1))


# ---------------------------------------------------------------- ANOVA
def test_tabla_anova_coincide_con_las_sumas_de_cuadrados_manuales(tmp_path):
    d = df2.cargar(_registros(tmp_path / "e.jsonl"))
    t = df2.tabla_anova(df2.ajustar(d))
    assert t.gl.tolist()[:5] == [3, 2, 1, 2, 15] and t.loc["Total", "gl"] == 23
    y, g = d.tiempo_s, d.tiempo_s.mean()
    sct = ((y - g) ** 2).sum()
    sca = 8 * ((d.groupby("carga").tiempo_s.mean() - g) ** 2).sum()
    scb = 12 * ((d.groupby("procesos").tiempo_s.mean() - g) ** 2).sum()
    scbl = 6 * ((d.groupby("bloque").tiempo_s.mean() - g) ** 2).sum()
    scab = 4 * ((d.groupby(["carga", "procesos"]).tiempo_s.mean() - g) ** 2).sum() - sca - scb
    assert t.loc["Total", "SC"] == pytest.approx(sct)
    for fila, sc in (("A carga", sca), ("B procesos", scb), ("Bloque", scbl), ("AB carga x procesos", scab)):
        assert t.loc[fila, "SC"] == pytest.approx(sc)
        assert t.loc[fila, "eta2_parcial"] == pytest.approx(sc / (sc + t.loc["Residuo", "SC"]))
    assert t.loc["AB carga x procesos", "p"] < 0.05                         # la interacción construida se detecta


def test_efectos_simples_y_supuestos(tmp_path):
    d = df2.cargar(_registros(tmp_path / "e.jsonl"))
    m = df2.ajustar(d)
    es = df2.efectos_simples(d, m).set_index("carga")
    for c in (1, 5, 10):
        m1, m4 = (d.tiempo_s[(d.carga == c) & (d.procesos == p)].mean() for p in (1, 4))
        assert es.loc[c, "diferencia_s"] == pytest.approx(m1 - m4) and es.loc[c, "aceleracion"] == pytest.approx(m1 / m4)
    assert (es.p_holm >= es.p).all()
    s = df2.supuestos(d, m)
    assert 0 < s["normalidad_shapiro_residuos"]["p"] <= 1 and 0 < s["independencia_durbin_watson"] < 4
    assert s["adecuacion"]["gl_residuo"] == 15 and len(s["de_por_celda_s"]) == 6


def test_el_analisis_es_reproducible_y_no_modifica_la_entrada(tmp_path):
    entrada = _registros(tmp_path / "e.jsonl")
    antes = entrada.read_bytes()
    a = df2.analizar(entrada, tmp_path / "a")
    df2.analizar(entrada, tmp_path / "b")
    assert entrada.read_bytes() == antes and a["resumen"]["rango_matriz"] == 9
    for n in ("anova.csv", "medias_tratamiento.csv", "efectos_simples.csv", "sensibilidad.csv", "resumen.json",
              "residuos.csv", "figuras/datos_figuras.json"):
        assert (tmp_path / "a" / n).read_bytes() == (tmp_path / "b" / n).read_bytes(), n
    for png in ("efectos_principales.png", "interaccion.png", "residuos.png"):
        assert (tmp_path / "a" / "figuras" / png).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_los_resultados_anteriores_siguen_intactos():
    esperados = {"corridas_2x3.jsonl": "f5167a79d47513af879f990207069c1ebabd1aa1a83d85eebd0c46506ff31811",
                 "confirmacion_2x3.jsonl": "730c34d5ad94776e4d3e556b34b045bb7d3f7b3c05a85e7e095522d5ca42c334"}
    for p in df2.PROTEGIDOS:
        if not p.is_file():
            pytest.skip("requiere los resultados versionados del 2^3")
        assert ar.sha256_archivo(p) == esperados[p.name], p.name
    assert df2.SALIDA.name == "dos_factores_3x2.jsonl" and df2.SALIDA not in df2.PROTEGIDOS
