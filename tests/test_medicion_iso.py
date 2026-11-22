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
    assert ev["eficiencia_de_desempeno"]["experimento_corridas_oficiales"] == 16 and ev["mantenibilidad"]["ruff"]["codigo_de_salida"] == 0
    assert all("sin vulnerabilidades" in v for v in ev["seguridad"]["pip_audit"].values())
    doc = (RAIZ / "docs" / "E2" / "iso25010.md").read_text(encoding="utf-8")
    for c in OCHO:
        fila = next(x for x in doc.splitlines() if x.startswith(f"| **{c}**"))
        assert any(n in fila for n in ("**Comprobada**", "**Parcial**")), c
