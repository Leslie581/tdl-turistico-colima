"""Confirmación del experimento 2^3 (laboratorio/experimento/confirmacion.py): plan, ejecución segura y criterios."""
import json
import shutil
import socket
import subprocess

import numpy as np
import pytest

pytest.importorskip("pyarrow")
pytest.importorskip("orjson")
pytest.importorskip("scipy")

from laboratorio.experimento import arnes as ar  # noqa: E402
from laboratorio.experimento import confirmacion as cf  # noqa: E402

DIAS = sorted(p for p in ar.BRONCE_DENUE.iterdir() if p.is_dir() and any(p.glob("*_02_BuscarAreaAct.json")))[:2]


@pytest.fixture
def bronce(tmp_path):
    if len(DIAS) < 2:
        pytest.skip("requiere dos días de bronce DENUE")
    destino = tmp_path / "bronce_denue"
    for d in DIAS:
        shutil.copytree(d, destino / d.name)
    return destino


def _registros(ruta, t1, t8, estado="ok"):
    filas = [{"semilla": cf.SEMILLA, "piloto": False, "etiqueta": e, "estado": estado, "tiempo_s": t, "tasa_error": 0.0}
             for e, ts in (("T1", t1), ("T8", t8)) for t in ts]
    ruta.write_text("\n".join(json.dumps(f) for f in filas) + "\n", encoding="utf-8")
    return ruta


# ---------------------------------------------------------------- plan
def test_plan_de_12_corridas_6_por_tratamiento_aleatorizado_y_reproducible():
    p = cf.plan()
    assert [x["orden"] for x in p] == list(range(1, 13))
    assert sum(x["etiqueta"] == "T1" for x in p) == sum(x["etiqueta"] == "T8" for x in p) == 6
    assert p == cf.plan() and [x["etiqueta"] for x in p] != [x["etiqueta"] for x in cf.plan(1)]
    assert [x["etiqueta"] for x in p] != ["T1"] * 6 + ["T8"] * 6
    assert cf.TRATAMIENTOS["T1"] == {"tratamiento": 1, "procesos": 1, "analizador": "json", "formato": "csv"}
    assert cf.TRATAMIENTOS["T8"] == {"tratamiento": 8, "procesos": 4, "analizador": "orjson", "formato": "parquet"}


# ---------------------------------------------------------------- ejecución
def test_ejecuta_t1_y_t8_de_verdad_en_el_orden_del_plan_y_no_repite(tmp_path, bronce):
    salida = tmp_path / "c.jsonl"
    hechas = cf.ejecutar(salida, copias=1, bronce=bronce, piloto=True, calentamiento=False, solo=[1, 2])
    assert [(r["orden"], r["etiqueta"]) for r in hechas] == [(p["orden"], p["etiqueta"]) for p in cf.plan()[:2]]
    t8, t1 = (next(r for r in hechas if r["etiqueta"] == e) for e in ("T8", "T1"))
    assert t8["evidencia_factores"]["trabajo_fuera_del_proceso_principal"] and t8["evidencia_factores"]["es_parquet"]
    assert t8["evidencia_factores"]["pids_distintos"] >= 2           # con pocas capturas no siempre arrancan las 4
    assert t1["evidencia_factores"]["pids_distintos"] == 1 and not t1["evidencia_factores"]["es_parquet"]
    assert t8["evidencia_factores"]["analizador"].endswith("analizar_orjson")
    for r in hechas:
        assert r["estado"] == "ok" and r["tasa_error"] == 0.0 and r["sesion"] == "confirmacion" and r["piloto"]
        assert {"commit", "codigo_modificado", "entorno", "condiciones", "carga", "fecha_local", "semilla"} <= set(r)
    assert cf.ejecutar(salida, copias=1, bronce=bronce, piloto=True, calentamiento=False, solo=[1, 2]) == []


def test_protege_los_archivos_oficiales_y_exige_codigo_confirmado(tmp_path, monkeypatch):
    with pytest.raises(ValueError):
        cf.ejecutar(cf.SALIDA, piloto=True)
    with pytest.raises(ValueError):
        cf.ejecutar(ar.SALIDA)                                  # nunca escribe en las corridas factoriales
    monkeypatch.setattr(ar, "codigo_modificado", lambda *_: True)
    with pytest.raises(RuntimeError):
        cf.ejecutar(tmp_path / "c.jsonl")


def test_no_modifica_el_bronce_ni_abre_conexiones(tmp_path, bronce, monkeypatch):
    def prohibido(*a, **k):
        raise AssertionError("conexión de red")
    monkeypatch.setattr(socket.socket, "connect", prohibido)
    monkeypatch.setattr(socket, "create_connection", prohibido)
    monkeypatch.setattr(cf, "condiciones_equipo", lambda: {})
    antes = ar.huella_bronce(bronce)
    t1 = [p["orden"] for p in cf.plan() if p["etiqueta"] == "T1"][:2]   # en el proceso principal (sin trabajadores)
    assert len(cf.ejecutar(tmp_path / "c.jsonl", copias=1, bronce=bronce, piloto=True, calentamiento=False, solo=t1)) == 2
    assert ar.huella_bronce(bronce) == antes


def test_una_corrida_fallida_se_registra_y_bloquea_la_evaluacion(tmp_path, bronce, monkeypatch):
    def falla(*a, **k):
        raise OSError("disco lleno")
    monkeypatch.setattr(ar, "escribir_salida", falla)
    salida = tmp_path / "c.jsonl"
    t1 = [p["orden"] for p in cf.plan() if p["etiqueta"] == "T1"][:1]
    (r,) = cf.ejecutar(salida, copias=1, bronce=bronce, piloto=True, calentamiento=False, solo=t1)
    assert r["estado"] == "fallo" and r["tiempo_s"] is None
    a = cf.analizar(salida, incluir_piloto=True)
    assert a["evaluable"] is False and a["corridas_fallidas"] == 1 and "criterios" not in a


def test_condiciones_del_equipo_sin_powershell_quedan_en_none(monkeypatch):
    def sin(*a, **k):
        raise OSError("no hay powershell")
    monkeypatch.setattr(subprocess, "run", sin)
    c = cf.condiciones_equipo()
    assert c["corriente_alterna"] is None and c["procesos_onedrive"] is None and c["plan_energia"] is None


# ---------------------------------------------------------------- estadística y criterios
def test_welch_e_intervalo_coinciden_con_el_calculo_manual(tmp_path):
    t1, t8 = [8.0, 9.0, 10.0, 8.5, 9.5, 9.0], [4.0, 4.5, 5.0, 4.2, 4.8, 4.5]
    a = cf.analizar(_registros(tmp_path / "c.jsonl", t1, t8))
    x, y = np.array(t1), np.array(t8)
    v1, v2 = x.var(ddof=1) / 6, y.var(ddof=1) / 6
    t = (x.mean() - y.mean()) / np.sqrt(v1 + v2)
    gl = (v1 + v2) ** 2 / (v1 ** 2 / 5 + v2 ** 2 / 5)
    from scipy import stats
    assert a["welch_unilateral"]["t"] == pytest.approx(t) and a["gl_welch"] == pytest.approx(gl)
    assert a["welch_unilateral"]["p"] == pytest.approx(stats.t.sf(t, gl))
    h = stats.t.ppf(0.975, gl) * np.sqrt(v1 + v2)
    assert a["ic95_diferencia_s"] == pytest.approx([x.mean() - y.mean() - h, x.mean() - y.mean() + h])
    assert a["mejora_relativa"] == pytest.approx(1 - y.mean() / x.mean()) and a["confirmada"] is True


def test_cada_criterio_se_evalua_por_separado(tmp_path):
    a = cf.analizar(_registros(tmp_path / "a.jsonl", [5.0, 5.2, 5.1, 4.9, 5.0, 5.1], [4.4, 4.5, 4.3, 4.6, 4.4, 4.5]))
    c = a["criterios"]                                         # mejora ~12 %: Welch sí, 20 % no
    assert c["1_media_T8_en_intervalo_de_prediccion"]["cumple"] and c["2a_welch_unilateral_p_menor_005"]["cumple"]
    assert not c["2b_mejora_al_menos_20pct"]["cumple"] and a["confirmada"] is False
    b = cf.analizar(_registros(tmp_path / "b.jsonl", [20, 21, 19, 20, 22, 21], [9, 9.5, 9.2, 9.1, 9.3, 9.4]))
    assert not b["criterios"]["1_media_T8_en_intervalo_de_prediccion"]["cumple"] and b["confirmada"] is False


def test_el_intervalo_de_prediccion_es_el_fijado_con_el_factorial():
    pytest.importorskip("statsmodels")
    from scipy import stats

    from laboratorio.experimento import anova as an
    if an.sha256(an.ENTRADA) != "f5167a79d47513af879f990207069c1ebabd1aa1a83d85eebd0c46506ff31811":
        pytest.skip("requiere las 16 corridas oficiales")
    d = an.cargar()
    m = an.ajustar(d)
    t8 = d.tiempo_s[d.tratamiento == 8].mean()
    h = stats.t.ppf(0.975, m.df_resid) * np.sqrt(m.mse_resid * (1 / 2 + 1 / 6))
    assert (round(t8 - h, 2), round(t8 + h, 2)) == cf.INTERVALO_PREDICCION_T8
