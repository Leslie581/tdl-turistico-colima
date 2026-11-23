"""Mediciones de calidad de E2: ISO/IEC 25012 (datos de la capa oro) y la parte medible por código de ISO/IEC 25010 (producto).

    python -m pipeline.medicion_iso 25012 [--corte 2026-11-22]     -> docs/E2/evidencia/iso25012.json
    python -m pipeline.medicion_iso 25010 [--herramientas]         -> docs/E2/evidencia/iso25010.json

Todo sale de archivos reales del repositorio (oro, bronce y fichas). Cada métrica trae su valor, su umbral y si lo cumple; los umbrales los
fija esta evaluación (docs/E2/iso25012.md) y no son requisitos del PDF. ``--herramientas`` ejecuta ``ruff`` y ``pip-audit`` (esta última requiere red).
La evaluación completa, con lo que no se mide aquí, está en docs/E2/iso25010.md y docs/E2/iso25012.md.
"""
from __future__ import annotations

import argparse
import ast
import json
import platform
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd

from .calidad import reglas_denue as rd
from .config import CAJA_COLIMA, RAIZ
from .linaje import verificar_linaje

SALIDA = RAIZ / "docs" / "E2" / "evidencia"
CORTE_POR_OMISION = "2026-11-22"
UMBRALES = {"completitud": 1.0, "completitud_captura_min": 0.98, "completitud_captura_max": 1.02, "exactitud_dif_max": 1e-5, "consistencia_violaciones": 0,
            "rezago_datatur_meses": 12, "rezago_denue_dias": 2, "trazabilidad": 1.0, "comprension": 1.0}
PERSONALES = ("telefono", "correo", "razon_social", "nombre", "calle", "domicilio", "latitud", "longitud", "clee")


def _m(valor, umbral, cumple, nota=""):
    return {"valor": valor, "umbral": umbral, "cumple": bool(cumple), **({"nota": nota} if nota else {})}


def _oro(raiz: Path, nombre: str) -> pd.DataFrame:
    return pd.read_csv(raiz / "data" / "oro" / nombre, dtype=str, keep_default_na=False)


def _capturas_bronce(raiz: Path) -> list[dict]:
    """Por cada captura DENUE: total anunciado por ``Cuantificar`` y registros guardados de ``BuscarAreaAct``."""
    salida = []
    for cuant in sorted((raiz / "data" / "bronce" / "denue").glob("*/*_01_Cuantificar.json")):
        busc = cuant.with_name(cuant.name.replace("_01_Cuantificar", "_02_BuscarAreaAct"))
        if not busc.is_file():
            continue
        total = int(json.loads(cuant.read_text(encoding="utf-8-sig"))[0]["Total"])
        n = len(json.loads(busc.read_text(encoding="utf-8-sig")))
        salida.append({"fecha": cuant.parent.name, "total": total, "registros": n, "razon": n / total})
    return salida


def medir_25012(raiz: Path = RAIZ, corte: str = CORTE_POR_OMISION) -> dict:
    """Características de calidad de datos medidas sobre el oro de DataTur (mensual) y de DENUE (oferta y AGEB)."""
    raiz = Path(raiz)
    m = _oro(raiz, "manzanillo_ocupacion_mensual.csv")
    num = {c: pd.to_numeric(m[c]) for c in ("ocupacion_pct", "cuartos_disponibles", "cuartos_ocupados", "cuartos_ocupados_residentes",
                                            "cuartos_ocupados_no_residentes", "pct_cuartos_no_residentes")}
    ofe, ag = _oro(raiz, "manzanillo_oferta_hospedaje.csv"), _oro(raiz, "manzanillo_oferta_ageb.csv")
    ficha_ag = json.loads((raiz / "data" / "oro" / "manzanillo_oferta_ageb.meta.json").read_text(encoding="utf-8"))
    caps = _capturas_bronce(raiz)
    esperados = pd.period_range("2016-01", "2024-12", freq="M").astype(str)
    out: dict = {"corte": corte, "conjuntos": {"DataTur": "data/oro/manzanillo_ocupacion_mensual.csv", "DENUE": ["data/oro/manzanillo_oferta_hospedaje.csv", "data/oro/manzanillo_oferta_ageb.csv"]}}

    # --- Completitud
    nulos = int((m == "").sum().sum())
    razones = [c["razon"] for c in caps]
    ocultas = ag["n_establecimientos"] == ""
    out["completitud"] = {
        "datatur_celdas_no_nulas": _m(1 - nulos / m.size, UMBRALES["completitud"], nulos == 0),
        "datatur_periodos_presentes": _m(f"{len(set(m['periodo']) & set(esperados))} de {len(esperados)}", "108 de 108", set(esperados) <= set(m["periodo"])),
        "denue_registros_frente_a_cuantificar": _m({"capturas": len(caps), "razon_min": round(min(razones), 4), "razon_max": round(max(razones), 4)},
                                                  "0.98 a 1.02 (regla R-E02)", all(0.98 <= r <= 1.02 for r in razones)),
        "denue_oferta_celdas_no_nulas": _m(1 - int((ofe == "").sum().sum()) / ofe.size, UMBRALES["completitud"], int((ofe == "").sum().sum()) == 0),
        "denue_ageb_vacios_no_intencionales": _m(int((ag == "").sum().sum()) - (2 * int(ocultas.sum()) + int((ag["tipo_ageb"] == "rural").sum())), 0,
                                                 int((ag == "").sum().sum()) == 2 * int(ocultas.sum()) + int((ag["tipo_ageb"] == "rural").sum()),
                                                 "los vacíos esperados son el conteo y la densidad de las celdas de 1-2 (privacidad) y la localidad de las AGEB rurales (no aplica)"),
    }
    # --- Exactitud
    from laboratorio.pronosticos import datos
    ref = datos.derivar_referencia()
    dif_ref = float((ref["ocupacion_pct"].to_numpy() - num["ocupacion_pct"].to_numpy()).__abs__().max())
    recalc = num["cuartos_ocupados"] / num["cuartos_disponibles"] * 100
    dif_calc = float((recalc - num["ocupacion_pct"]).abs().max())
    from .calidad.cuarentena import Cuarentena
    from .plata_denue import procesar_capturas
    plata = procesar_capturas(raiz / "data" / "bronce" / "denue", Cuarentena(f"{corte}T00:00:00+00:00"))
    ult = plata[plata["fecha_captura_local"] == plata["fecha_captura_local"].max()]
    en_caja = ult["latitud"].between(*CAJA_COLIMA["lat"]) & ult["longitud"].between(*CAJA_COLIMA["lon"])
    out["exactitud"] = {
        "datatur_frente_a_derivacion_independiente_desde_el_bronce": _m(dif_ref, UMBRALES["exactitud_dif_max"], dif_ref <= UMBRALES["exactitud_dif_max"],
                                                                      "máxima diferencia absoluta en puntos porcentuales, 108 meses"),
        "datatur_ocupacion_recalculada": _m(dif_calc, UMBRALES["exactitud_dif_max"], dif_calc <= UMBRALES["exactitud_dif_max"]),
        "datatur_valores_fuera_de_0_100": _m(int(((num["ocupacion_pct"] < 0) | (num["ocupacion_pct"] > 100)).sum()), 0, ((num["ocupacion_pct"] < 0) | (num["ocupacion_pct"] > 100)).sum() == 0),
        "denue_coordenadas_en_la_caja_de_colima": _m(float(en_caja.mean()), 1.0, en_caja.all(), f"{len(ult)} establecimientos de la captura {ult['fecha_captura_local'].iloc[0]}"),
        "denue_clase_scian_en_el_catalogo": _m(float(ult["scian_clase"].isin(list(rd.CATALOGO_HOSPEDAJE)).mean()), 1.0, ult["scian_clase"].isin(list(rd.CATALOGO_HOSPEDAJE)).all()),
        "denue_ageb_espacial_frente_a_ageb_del_denue": _m(ficha_ag["concordancia_ageb_denue_poligono"], 1.0, ficha_ag["concordancia_ageb_denue_poligono"] == 1.0,
                                                          f"{ficha_ag['establecimientos_con_ageb']} de {ficha_ag['establecimientos_en_plata']} ubicados"),
    }
    # --- Consistencia
    v = {
        "ocupados_mayor_que_disponibles": int((num["cuartos_ocupados"] > num["cuartos_disponibles"]).sum()),
        "residentes_mas_no_residentes_distinto_de_ocupados": int(((num["cuartos_ocupados_residentes"] + num["cuartos_ocupados_no_residentes"]) != num["cuartos_ocupados"]).sum()),
        "periodos_repetidos_o_desordenados": int(not m["periodo"].is_monotonic_increasing) + int(m["periodo"].duplicated().sum()),
        "version_de_contrato_distinta": int(m["version_contrato"].nunique() - 1),
    }
    visibles = int(pd.to_numeric(ag.loc[~ocultas, "n_establecimientos"]).sum())
    n_ocultas = int(ocultas.sum())
    codigos = set(ofe["scian_clase"])
    out["consistencia"] = {
        "datatur_reglas_de_dominio": {k: _m(x, UMBRALES["consistencia_violaciones"], x == 0) for k, x in v.items()},
        "denue_oferta_clases_en_el_catalogo": _m(sorted(codigos - set(rd.CATALOGO_HOSPEDAJE)), [], codigos <= set(rd.CATALOGO_HOSPEDAJE)),
        "denue_oferta_un_solo_municipio": _m(sorted(set(ofe["municipio_clave"])), ["06007"], set(ofe["municipio_clave"]) == {"06007"}),
        "denue_ageb_claves_unicas": _m(int(ag["cvegeo"].duplicated().sum()), 0, not ag["cvegeo"].duplicated().any()),
        "denue_ageb_total_compatible_con_la_captura": _m({"visibles": visibles, "celdas_ocultas": n_ocultas, "total_de_la_captura": ficha_ag["establecimientos_con_ageb"]},
                                                         "visibles + [1, 2] por celda oculta incluye el total",
                                                         visibles + n_ocultas <= ficha_ag["establecimientos_con_ageb"] <= visibles + 2 * n_ocultas),
    }
    # --- Actualidad
    ult_per = pd.Period(m["periodo"].iloc[-1], "M")
    f_corte = date.fromisoformat(corte)
    rezago_m = (f_corte.year - ult_per.year) * 12 + (f_corte.month - ult_per.month)
    fechas = sorted({c["fecha"] for c in caps})
    huecos = [(date.fromisoformat(b) - date.fromisoformat(a)).days for a, b in zip(fechas, fechas[1:])]
    rezago_d = (f_corte - date.fromisoformat(fechas[-1])).days
    out["actualidad"] = {
        "datatur_rezago_en_meses": _m(rezago_m, UMBRALES["rezago_datatur_meses"], rezago_m <= UMBRALES["rezago_datatur_meses"],
                                      f"último periodo {ult_per}; la fuente abierta se actualizó por última vez en mayo de 2025 (docs/fuentes/datatur.md)"),
        "denue_rezago_en_dias": _m(rezago_d, UMBRALES["rezago_denue_dias"], rezago_d <= UMBRALES["rezago_denue_dias"], f"última captura {fechas[-1]}"),
        "denue_capturas_distintas_y_hueco_maximo_en_dias": _m({"capturas": len(fechas), "hueco_max_dias": max(huecos) if huecos else 0}, "hueco máximo de 3 días", (max(huecos) if huecos else 0) <= 3),
    }
    # --- Trazabilidad
    lin = verificar_linaje(raiz)
    out["trazabilidad"] = {"cadenas_verificadas_frente_a_registros": _m(round(lin["cadenas_verificadas"] / (lin["registros_mensuales"] + lin["capturas_de_oferta"] + lin["agebs"]), 4),
                                                                      UMBRALES["trazabilidad"], lin["completo"],
                                                                      f"{lin['cadenas_verificadas']} cadenas: {lin['registros_mensuales']} meses, {lin['capturas_de_oferta']} capturas y {lin['agebs']} AGEB")}
    # --- Credibilidad
    fichas = [json.loads(p.read_text(encoding="utf-8")) for p in (raiz / "data" / "bronce" / "denue").glob("*/*.json.meta.json")]
    oficiales = [f for f in fichas if f.get("origen") == "oficial" and f.get("estado_http") == 200]
    ver = json.loads((raiz / "docs" / "fuentes" / "evidencias" / "verificacion_base70_20261109_B.json").read_text(encoding="utf-8"))
    out["credibilidad"] = {
        "denue_fichas_de_origen_oficial_con_http_200": _m(len(oficiales) / len(fichas), 1.0, len(oficiales) == len(fichas), f"{len(fichas)} fichas de bronce"),
        "datatur_archivo_identico_al_oficial": _m(bool(ver["identico"]), True, ver["identico"] is True, "comparación por SHA-256 con la descarga oficial del 2026-11-09"),
    }
    # --- Conformidad
    from .interfaz import cargar_oro_mensual                         # valida con pandera (ESQUEMA_ORO) y lanza error si no cumple el contrato
    cargar_oro_mensual(raiz / "data" / "oro" / "manzanillo_ocupacion_mensual.csv")
    out["conformidad"] = {"datatur_esquema_del_contrato_1_0_0": _m("validado con pandera (ESQUEMA_ORO)", "sin errores", True, f"{m.shape[1]} columnas, {len(m)} filas")}
    # --- Confidencialidad
    columnas = [c for nombre in ("manzanillo_ocupacion_mensual", "manzanillo_oferta_hospedaje", "manzanillo_oferta_ageb") for c in _oro(raiz, nombre + ".csv").columns]
    con_dato = [c for c in columnas if any(p in c.lower() for p in PERSONALES)]
    exactos = int((~ocultas & (ag["rango"] == "1-2")).sum())
    out["confidencialidad"] = {
        "columnas_de_datos_personales_o_de_establecimientos_individuales": _m(con_dato, [], not con_dato),
        "ageb_con_1_o_2_establecimientos_con_conteo_exacto": _m(exactos, 0, exactos == 0),
    }
    # --- Comprensibilidad
    dic = pd.read_csv(raiz / "data" / "oro" / "diccionario_datos.csv", dtype=str)
    docs = set(zip(dic["dataset"], dic["columna"]))
    cobertura = {}
    for nombre in ("manzanillo_ocupacion_mensual", "manzanillo_oferta_hospedaje", "manzanillo_oferta_ageb"):
        cols = list(_oro(raiz, nombre + ".csv").columns)
        cobertura[nombre] = round(sum((nombre, c) in docs for c in cols) / len(cols), 4)
    out["comprensibilidad"] = {"columnas_documentadas_en_el_diccionario": {k: _m(x, UMBRALES["comprension"], x == 1.0) for k, x in cobertura.items()}}
    return out


def _definiciones_de_prueba(raiz: Path) -> int:
    """Cuenta las definiciones ``def test_*`` en tests/test_*.py (análisis estático). No expande parametrizaciones: no es el número de casos que ejecuta pytest."""
    return sum(isinstance(n, ast.FunctionDef) and n.name.startswith("test_") for p in (raiz / "tests").glob("test_*.py") for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))))


def _lineas(carpetas: list[Path]) -> int:
    total = 0
    for c in carpetas:
        for p in c.rglob("*.py"):
            total += sum(1 for linea in p.read_text(encoding="utf-8").splitlines() if linea.strip() and not linea.strip().startswith("#"))
    return total


def _posterior_a_la_correccion(validas: list[dict], ventanas: list[dict], objetivo: float) -> dict:
    """Indicador COMPLEMENTARIO, separado del histórico: las mismas ventanas de 7 días, pero solo las que empiezan en el primer éxito posterior
    al último fallo (el cierre del incidente). No sustituye ni modifica el dictamen histórico de O1 y no se extrapola: describe lo observado."""
    orden = sorted(validas, key=lambda f: f["inicio_utc"])
    ultimo_fallo = max((i for i, f in enumerate(orden) if f["resultado"] == "fallo"), default=None)
    if ultimo_fallo is None:
        return {"aplica": False, "motivo": "no hay fallos: el histórico ya es el indicador"}
    cierre = next((f for f in orden[ultimo_fallo + 1:] if f["resultado"] == "exito"), None)
    if cierre is None:
        return {"aplica": False, "motivo": "el último fallo sigue abierto (sin éxito posterior)"}
    desde = [w for w in ventanas if w["inicio_utc"] >= cierre["inicio_utc"]]
    if not desde:
        return {"aplica": False, "motivo": "aún no hay una ventana completa de 7 días posterior a la corrección"}
    peor = min(desde, key=lambda x: (x["tasa"], x["inicio_utc"]))
    bajo = [w for w in desde if w["tasa"] < objetivo]
    return {"aplica": True, "referencia_de_la_correccion_utc": cierre["inicio_utc"], "ventanas_completas_posteriores": len(desde), "ventanas_por_debajo_del_objetivo": len(bajo),
            "peor_ventana_posterior": peor, "resultado_observado": "todas las ventanas completas posteriores alcanzan el objetivo" if not bajo else "hay ventanas posteriores por debajo del objetivo",
            "nota": "Complementario: no cambia el dictamen histórico (NO CUMPLE). Son ventanas traslapadas de un solo régimen y pocas ejecuciones; no demuestra que la tasa verdadera sea >= 95 % ni se extrapola al futuro."}


def _o1_por_ventanas(filas: list[dict], dias: int = 7, objetivo: float = 0.95) -> dict:
    """Objetivo O1 (calidad/objetivos.md): éxitos / (éxitos + fallos) >= 95 % en CUALQUIER ventana de 7 días, sin contar las omitidas por duplicado.

    Se evalúan las ventanas de 7 × 24 h que empiezan en cada ejecución válida y caben completas en la bitácora. Distinto de la tasa global de
    toda la bitácora (que es el criterio de ``verificar_e0 --solo disponibilidad``): aquí basta una ventana por debajo de 95 % para no cumplir.
    """
    from datetime import datetime, timedelta
    v = [f for f in filas if f.get("resultado") in ("exito", "fallo")]
    t = lambda x: datetime.fromisoformat(x)  # noqa: E731
    fin = max(t(f["fin_utc"]) for f in v)
    ventanas = []
    for f in v:
        a = t(f["inicio_utc"])
        if a + timedelta(days=dias) > fin:
            continue
        w = [g for g in v if a <= t(g["inicio_utc"]) < a + timedelta(days=dias)]
        e = sum(g["resultado"] == "exito" for g in w)
        ventanas.append({"inicio_utc": a.isoformat(), "exitos": e, "fallos": len(w) - e, "tasa": round(e / len(w), 4)})
    peor = min(ventanas, key=lambda x: (x["tasa"], x["inicio_utc"]))
    bajo = [x for x in ventanas if x["tasa"] < objetivo]
    ex = sum(f["resultado"] == "exito" for f in v)
    return {"posterior_a_la_correccion": _posterior_a_la_correccion(v, ventanas, objetivo), "criterio": f"tasa de éxito >= {objetivo:.0%} en cualquier ventana de {dias} días (se excluyen las omitidas por duplicado)",
            "dictamen": "NO CUMPLE" if bajo else "CUMPLE", "ventanas_evaluadas": len(ventanas), "ventanas_por_debajo_del_objetivo": len(bajo), "peor_ventana": peor,
            "tasa_global_de_la_bitacora": {"exitos": ex, "validas": len(v), "tasa": round(ex / len(v), 4), "cumple_el_objetivo": ex / len(v) >= objetivo},
            "nota": "las ventanas son de 7 x 24 h desde cada ejecución válida; con ventanas por día local la ventana inicial daría 8 de 9 (88.9 %), también por debajo del objetivo"}


def _rf01_desde_bitacora(filas: list[dict], dias_requeridos: int = 7) -> dict:
    """RF-01 (docs/E1/requerimientos.md): al menos 1 captura exitosa por día local, ejecuciones por ``schedule`` y ventana >= 7 días."""
    from datetime import datetime
    v = [f for f in filas if f.get("resultado") in ("exito", "fallo")]
    dias = {f["fecha_local"] for f in v}
    con_exito = {f["fecha_local"] for f in v if f["resultado"] == "exito"}
    ventana = (max(datetime.fromisoformat(f["fin_utc"]) for f in v) - min(datetime.fromisoformat(f["inicio_utc"]) for f in v)).total_seconds() / 86400
    sched = sum(f["resultado"] == "exito" and f.get("disparador") == "schedule" for f in v)
    return {"dias_locales_con_ejecucion": len(dias), "dias_locales_con_captura_exitosa": len(con_exito), "ejecuciones_schedule_exitosas": sched,
            "ventana_dias": round(ventana, 2), "cumple": con_exito == dias and sched > 0 and ventana >= dias_requeridos}


def _duracion_captura(filas: list[dict]) -> dict:
    d = pd.Series([f["duracion_s"] for f in filas if f.get("resultado") == "exito"], dtype=float)
    return {"n": int(len(d)), "mediana_s": round(float(d.median()), 2), "p90_s": round(float(d.quantile(0.9)), 2), "min_s": round(float(d.min()), 2),
            "max_s": round(float(d.max()), 2), "nota": "duracion_s de cada captura exitosa en calidad/bitacora_capturas.jsonl; p90 por interpolación lineal"}


def medir_25010(raiz: Path = RAIZ, herramientas: bool = False) -> dict:
    """Métricas de ISO/IEC 25010 que se calculan sobre el repositorio; el resto de la evaluación está en docs/E2/iso25010.md."""
    raiz = Path(raiz)
    req = (raiz / "docs" / "E1" / "requerimientos.md").read_text(encoding="utf-8")
    estados: dict[str, dict[str, int]] = {"RF": {}, "RNF": {}}
    for linea in req.splitlines():
        mm = re.match(r"\| \*\*(RF|RNF)-[A-Z0-9-]+\*\* \|", linea)
        if mm:
            est = re.match(r"\*\*(CUMPLIDO|PARCIAL|NO CUMPLIDO|PENDIENTE|PROPUESTO)", [c.strip() for c in linea.strip("|").split("|")][-1])
            if est:
                estados[mm.group(1)][est.group(1)] = estados[mm.group(1)].get(est.group(1), 0) + 1
    corridas = [json.loads(x) for x in (raiz / "laboratorio" / "experimento" / "resultados" / "corridas_2x3.jsonl").read_text(encoding="utf-8").splitlines()]
    oficiales = [c for c in corridas if not c.get("piloto")]
    tiempos = [c["tiempo_s"] for c in oficiales if "tiempo_s" in c]
    res = raiz / "laboratorio" / "experimento" / "resultados"
    conf = json.loads((res / "confirmacion" / "resumen.json").read_text(encoding="utf-8"))
    anova2 = pd.read_csv(res / "dos_factores" / "anova.csv", index_col=0)
    simples = pd.read_csv(res / "dos_factores" / "efectos_simples.csv")
    corridas2 = [json.loads(x) for x in (res / "dos_factores_3x2.jsonl").read_text(encoding="utf-8").splitlines()]
    from . import geoespacial as geo
    ageb = geo.cargar_ageb(raiz / "data" / "oro" / "manzanillo_ageb_poligonos.geojson")
    from .calidad.cuarentena import Cuarentena
    from .plata_denue import procesar_capturas
    tp = []
    for _ in range(3):
        t0 = time.perf_counter()
        plata = procesar_capturas(raiz / "data" / "bronce" / "denue", Cuarentena("2026-11-22T00:00:00+00:00"))
        tp.append(time.perf_counter() - t0)
    ref = geo.referencia(plata)
    ts = []
    for _ in range(3):
        t0 = time.perf_counter()
        u = geo.unir_espacial(ref, ageb)
        geo.agregar_por_ageb(u, ageb, "2026-11-21", "a" * 64, "b" * 64)
        ts.append(time.perf_counter() - t0)
    app = (raiz / "tablero" / "streamlit_app.py").read_text(encoding="utf-8")
    pestanas = re.search(r"st\.tabs\(\s*\[(.*?)\]\)", app, flags=re.S).group(1).count('"') // 2
    codigo = _lineas([raiz / c for c in ("pipeline", "extractores", "laboratorio", "tablero")])
    pruebas = _lineas([raiz / "tests"])
    bitacora = [json.loads(x) for x in (raiz / "calidad" / "bitacora_capturas.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    from laboratorio.pronosticos import datos as lab_datos
    from tablero import cargador as tab_cargador
    oro_lab, oro_tab = lab_datos.cargar_oro(raiz / "data" / "oro" / "manzanillo_ocupacion_mensual.csv"), tab_cargador.cargar_oro(raiz)
    from . import verificar_e0
    bronce = raiz / "data" / "bronce"
    e0 = {n: getattr(verificar_e0, n)(bronce) for n in ("historico", "integridad", "privacidad")}
    rf01 = _rf01_desde_bitacora(bitacora)
    rf = estados["RF"]
    rf_cumplidos = rf.get("CUMPLIDO", 0) + (rf.get("PARCIAL", 0) if rf01["cumple"] and rf.get("PARCIAL", 0) == 1 else 0)
    fiab = json.loads(subprocess.run([sys.executable, "-m", "pipeline.fiabilidad"], cwd=raiz, capture_output=True, text=True, check=True).stdout)
    out = {
        "entorno_de_la_medicion": {"sistema": platform.platform(), "python": platform.python_version(), "ci": "ubuntu-latest (.github/workflows/ci.yml)"},
        "adecuacion_funcional": {"requerimientos_funcionales_por_estado": estados["RF"], "requerimientos_no_funcionales_por_estado": estados["RNF"],
                                 "rf01_recalculado_con_la_bitacora": rf01,
                                 "requerimientos_funcionales_cumplidos_recalculados": {"cumplidos": rf_cumplidos, "total": sum(rf.values()),
                                                                                       "nota": "RF-01 figuraba PARCIAL en E1 solo porque la ventana era de 3.83 de 7 días; se recalcula con su propio criterio y la bitácora actual (docs/E1/requerimientos.md no se modifica)"},
                                 "definiciones_de_prueba": _definiciones_de_prueba(raiz),
                                 "nota_definiciones_de_prueba": "cuenta de def test_* en tests/test_*.py; no incluye la expansión de parametrizaciones ni equivale a los casos ejecutados por pytest"},
        "eficiencia_de_desempeno": {
            "experimento_corridas_oficiales": len(oficiales), "tiempo_por_corrida_s": {"min": round(min(tiempos), 3), "media": round(sum(tiempos) / len(tiempos), 3), "max": round(max(tiempos), 3)},
            "tasa_de_error_en_las_corridas": [c["capturas_con_error"] for c in oficiales if "capturas_con_error" in c] and sum(c["capturas_con_error"] for c in oficiales) / sum(c["capturas"] for c in oficiales),
            "carga_tecnica_confirmacion_t8_frente_t1": {
                "corridas": conf["corridas_registradas"], "tasa_de_error": conf["tasa_error"], "media_t1_s": round(conf["por_tratamiento"]["T1"]["media_s"], 3),
                "media_t8_s": round(conf["por_tratamiento"]["T8"]["media_s"], 3), "mejora_relativa": round(conf["mejora_relativa"], 4),
                "ic95_diferencia_s": [round(x, 2) for x in conf["ic95_diferencia_s"]], "p_welch_unilateral": round(conf["welch_unilateral"]["p"], 4), "confirmada": conf["confirmada"]},
            "carga_tecnica_dos_factores_carga_x_procesos": {
                "corridas": len(corridas2), "tasa_de_error_maxima": max(c["tasa_error"] for c in corridas2), "f_interaccion": round(float(anova2.loc["AB carga x procesos", "F"]), 2),
                "p_interaccion": round(float(anova2.loc["AB carga x procesos", "p"]), 4),
                "efectos_simples_p_holm": {f"{int(r.carga)}x": round(float(r.p_holm), 4) for r in simples.itertuples()}},
            "operativa_captura_diaria_duracion": _duracion_captura(bitacora),
            "operativa_pipeline_bronce_a_plata_denue_s": {"repeticiones": 3, "min": round(min(tp), 2), "max": round(max(tp), 2), "capturas_en_la_plata": int(plata["archivo_bronce"].nunique()),
                                                          "nota": "procesar_capturas en memoria (sin escribir), esta máquina; no es el experimento estadístico ni la carga técnica de 16 copias"},
            "union_espacial_y_agregado_s": {"establecimientos": int(len(ref)), "poligonos": int(len(ageb)), "mejor_de_3": round(min(ts), 4)}},
        "compatibilidad": {"consumidores_de_la_capa_oro_de_datatur": {"consumidores": ["tablero.cargador.cargar_oro", "laboratorio.pronosticos.datos.cargar_oro"], "meses": [int(len(oro_tab)), int(len(oro_lab))],
                                                                       "misma_ocupacion_pct": bool((oro_tab["ocupacion_pct"].to_numpy() == oro_lab["ocupacion_pct"].to_numpy()).all()),
                                                                       "mismos_periodos": bool(list(oro_tab["periodo"]) == list(oro_lab.index.astype(str)))}},
        "capacidad_de_interaccion": {"pestanas_del_tablero": pestanas},
        "fiabilidad": {"periodo": fiab["ventana"], "tasa_de_exito": fiab["tasa_exito"], "mttr": fiab["mttr"], "mtbf_horas_exploratorio": fiab["estimacion_exploratoria"].get("mtbf_horas"),
                       "disponibilidad_exploratoria": fiab["estimacion_exploratoria"].get("disponibilidad_observada_por_tiempo"), "ejecuciones": fiab["ejecuciones"],
                       "objetivo_o1_por_ventanas_de_7_dias": _o1_por_ventanas(bitacora)},
        "mantenibilidad": {"lineas_de_codigo": codigo, "lineas_de_prueba": pruebas, "relacion_prueba_codigo": round(pruebas / codigo, 3)},
    }
    out["seguridad"] = {"verificar_e0": {n: {"estado": r["estado"], "ok": r["ok"]} for n, r in e0.items()}}
    if herramientas:
        ruff = subprocess.run([sys.executable, "-m", "ruff", "check", "."], cwd=raiz, capture_output=True, text=True)
        out["mantenibilidad"]["ruff"] = {"codigo_de_salida": ruff.returncode, "resumen": ruff.stdout.strip().splitlines()[-1] if ruff.stdout.strip() else ""}
        audit = {}
        for archivo in ("requirements.txt", "requirements-lab.txt", "requirements-dev.txt"):
            r = subprocess.run([sys.executable, "-m", "pip_audit", "-r", archivo, "--no-deps", "--disable-pip"], cwd=raiz, capture_output=True, text=True)
            audit[archivo] = "sin vulnerabilidades conocidas" if r.returncode == 0 else r.stdout.strip()[-200:] or "error"
        out["seguridad"]["pip_audit"] = audit
    return out


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("norma", choices=("25010", "25012"))
    ap.add_argument("--corte", default=CORTE_POR_OMISION)
    ap.add_argument("--herramientas", action="store_true")
    a = ap.parse_args(argv)
    res = medir_25012(corte=a.corte) if a.norma == "25012" else medir_25010(herramientas=a.herramientas)
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / f"iso{a.norma}.json").write_bytes((json.dumps(res, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n").encode("utf-8"))
    print(json.dumps(res, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
