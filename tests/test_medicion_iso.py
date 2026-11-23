"""Mediciones ISO/IEC 25012 y 25010 (E2): se calculan sobre archivos reales y la evidencia versionada coincide con lo que producen."""
import json
from pathlib import Path

from pipeline import medicion_iso as mi

RAIZ = Path(__file__).resolve().parents[1]
EVID = RAIZ / "docs" / "E2" / "evidencia"
OCHO = ["Adecuación funcional", "Eficiencia de desempeño", "Compatibilidad", "Capacidad de interacción", "Fiabilidad", "Seguridad", "Mantenibilidad", "Portabilidad"]


def _hojas(x, ruta=""):
    if isinstance(x, dict) and "cumple" in x:
        yield ruta, x
    elif isinstance(x, dict):
        for k, v in x.items():
            if k not in ("corte", "conjuntos"):
                yield from _hojas(v, f"{ruta}/{k}")


def test_los_datos_estables_de_datatur_coinciden_con_la_evidencia_versionada():
    """DataTur no crece: sus métricas deben regenerarse idénticas. (Las de DENUE cambian con las capturas diarias.)"""
    nueva = dict(_hojas(mi.medir_25012(corte="2026-11-22")))
    vieja = dict(_hojas(json.loads((EVID / "iso25012.json").read_text(encoding="utf-8"))))
    estables = [k for k in nueva if "datatur" in k or k.startswith("/conformidad") or "manzanillo_ocupacion_mensual" in k]
    assert len(estables) >= 12 and all(nueva[k] == vieja[k] for k in estables)


def test_exactitud_y_consistencia_de_denue_cumplen_con_los_datos_reales():
    r = mi.medir_25012(corte="2026-11-22")
    assert r["exactitud"]["denue_ageb_espacial_frente_a_ageb_del_denue"]["cumple"]
    assert all(v["cumple"] for k, v in r["exactitud"].items() if k.startswith("denue"))
    assert all(v["cumple"] for k, v in r["consistencia"].items() if k.startswith("denue"))
    assert r["trazabilidad"]["cadenas_verificadas_frente_a_registros"]["cumple"]
    assert r["confidencialidad"]["ageb_con_1_o_2_establecimientos_con_conteo_exacto"]["valor"] == 0


def test_los_incumplimientos_se_informan_y_no_se_ocultan():
    r = mi.medir_25012(corte="2026-11-22")
    assert r["actualidad"]["datatur_rezago_en_meses"]["valor"] == 23 and not r["actualidad"]["datatur_rezago_en_meses"]["cumple"]
    assert not r["comprensibilidad"]["columnas_documentadas_en_el_diccionario"]["manzanillo_oferta_ageb"]["cumple"]
    texto = (RAIZ / "docs" / "E2" / "iso25012.md").read_text(encoding="utf-8")
    assert "23 meses" in texto and "0 de 12 columnas" in texto               # el documento declara lo mismo que mide el código


def test_la_evidencia_de_25010_trae_las_metricas_y_el_documento_cubre_las_ocho_caracteristicas():
    ev = json.loads((EVID / "iso25010.json").read_text(encoding="utf-8"))
    assert {"adecuacion_funcional", "eficiencia_de_desempeno", "capacidad_de_interaccion", "fiabilidad", "mantenibilidad", "seguridad"} <= set(ev)
    assert ev["adecuacion_funcional"]["definiciones_de_prueba"] > 400 and "no incluye la expansión" in ev["adecuacion_funcional"]["nota_definiciones_de_prueba"]
    assert ev["eficiencia_de_desempeno"]["experimento_corridas_oficiales"] == 16 and ev["mantenibilidad"]["ruff"]["codigo_de_salida"] == 0
    assert all("sin vulnerabilidades" in v for v in ev["seguridad"]["pip_audit"].values())
    doc = (RAIZ / "docs" / "E2" / "iso25010.md").read_text(encoding="utf-8")
    ef = ev["eficiencia_de_desempeno"]
    conf, dos = ef["carga_tecnica_confirmacion_t8_frente_t1"], ef["carga_tecnica_dos_factores_carga_x_procesos"]
    res = RAIZ / "laboratorio" / "experimento" / "resultados"
    fuente = json.loads((res / "confirmacion" / "resumen.json").read_text(encoding="utf-8"))
    assert conf["corridas"] == fuente["corridas_registradas"] == 12 and conf["confirmada"] is fuente["confirmada"] is True
    assert conf["p_welch_unilateral"] == round(fuente["welch_unilateral"]["p"], 4) and conf["mejora_relativa"] == round(fuente["mejora_relativa"], 4)
    assert dos["corridas"] == len((res / "dos_factores_3x2.jsonl").read_text(encoding="utf-8").splitlines()) == 24 and dos["p_interaccion"] < 0.001
    assert "36.8 %" in doc and "p = 0.0143" in doc and "p = 0.0002" in doc and "mide el pipeline, no el tablero" in doc
    assert f"{ev['mantenibilidad']['lineas_de_prueba']:,}" in doc and f"{ev['adecuacion_funcional']['definiciones_de_prueba']} definiciones de prueba" in doc
    # O1 por ventanas de 7 días: se recalcula desde la bitácora y el dictamen del documento coincide con el del código
    from pipeline.medicion_iso import _duracion_captura, _o1_por_ventanas, _rf01_desde_bitacora
    bit = [json.loads(x) for x in (RAIZ / "calidad" / "bitacora_capturas.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    o1 = _o1_por_ventanas(bit)
    assert ev["fiabilidad"]["objetivo_o1_por_ventanas_de_7_dias"] == o1
    assert o1["dictamen"] == "NO CUMPLE" and o1["peor_ventana"]["tasa"] < 0.95 and o1["tasa_global_de_la_bitacora"]["tasa"] < 0.95
    assert "NO CUMPLE" in doc and f"{o1['peor_ventana']['exitos']} de {o1['peor_ventana']['exitos'] + o1['peor_ventana']['fallos']}" in doc
    assert ev["adecuacion_funcional"]["rf01_recalculado_con_la_bitacora"] == _rf01_desde_bitacora(bit)
    assert ev["eficiencia_de_desempeno"]["operativa_captura_diaria_duracion"] == _duracion_captura(bit)
    assert ev["compatibilidad"]["consumidores_de_la_capa_oro_de_datatur"]["misma_ocupacion_pct"] is True
    assert all(v["ok"] is True for v in ev["seguridad"]["verificar_e0"].values())
    for c in OCHO:
        fila = next(x for x in doc.splitlines() if x.startswith(f"| **{c}**"))
        assert any(n in fila for n in ("**Comprobada**", "**Parcial**")), c


def _fila(dia, hora, resultado):
    from datetime import datetime, timezone
    t = datetime(2026, 11, dia, hora, tzinfo=timezone.utc)
    return {"inicio_utc": t.isoformat(), "fin_utc": t.isoformat(), "resultado": resultado}


def test_indicador_posterior_a_la_correccion_es_complementario_y_no_cambia_el_historico():
    from pipeline.medicion_iso import _o1_por_ventanas
    bit = [_fila(1, 0, "fallo")] + [_fila(d, 1, "exito") for d in range(1, 12)]
    o1 = _o1_por_ventanas(bit)
    assert o1["dictamen"] == "NO CUMPLE" and o1["peor_ventana"]["tasa"] < 0.95                  # el histórico conserva la ventana con el fallo
    post = o1["posterior_a_la_correccion"]
    assert post["aplica"] and post["ventanas_por_debajo_del_objetivo"] == 0 and post["peor_ventana_posterior"]["tasa"] == 1.0
    assert post["referencia_de_la_correccion_utc"] == bit[1]["inicio_utc"]
    nuevo_fallo = _o1_por_ventanas(bit + [_fila(12, 2, "fallo"), _fila(13, 2, "exito")] + [_fila(d, 3, "exito") for d in range(14, 23)])["posterior_a_la_correccion"]
    assert nuevo_fallo["referencia_de_la_correccion_utc"] == _fila(13, 2, "exito")["inicio_utc"]    # la referencia es el cierre del ÚLTIMO fallo
    sin_fallos = _o1_por_ventanas([_fila(d, 1, "exito") for d in range(1, 12)])
    assert sin_fallos["dictamen"] == "CUMPLE" and sin_fallos["posterior_a_la_correccion"]["aplica"] is False
    abierto = _o1_por_ventanas([_fila(d, 1, "exito") for d in range(1, 10)] + [_fila(10, 1, "fallo")])
    assert abierto["posterior_a_la_correccion"]["aplica"] is False and "abierto" in abierto["posterior_a_la_correccion"]["motivo"]
