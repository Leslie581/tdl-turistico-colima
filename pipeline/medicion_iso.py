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
    from . import geoespacial as geo
    ageb = geo.cargar_ageb(raiz / "data" / "oro" / "manzanillo_ageb_poligonos.geojson")
    from .calidad.cuarentena import Cuarentena
    from .plata_denue import procesar_capturas
    plata = procesar_capturas(raiz / "data" / "bronce" / "denue", Cuarentena("2026-11-22T00:00:00+00:00"))
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
    fiab = json.loads(subprocess.run([sys.executable, "-m", "pipeline.fiabilidad"], cwd=raiz, capture_output=True, text=True, check=True).stdout)
    out = {
        "entorno_de_la_medicion": {"sistema": platform.platform(), "python": platform.python_version(), "ci": "ubuntu-latest (.github/workflows/ci.yml)"},
        "adecuacion_funcional": {"requerimientos_funcionales_por_estado": estados["RF"], "requerimientos_no_funcionales_por_estado": estados["RNF"],
                                 "definiciones_de_prueba": _definiciones_de_prueba(raiz),
                                 "nota_definiciones_de_prueba": "cuenta de def test_* en tests/test_*.py; no incluye la expansión de parametrizaciones ni equivale a los casos ejecutados por pytest"},
        "eficiencia_de_desempeno": {
            "experimento_corridas_oficiales": len(oficiales), "tiempo_por_corrida_s": {"min": round(min(tiempos), 3), "media": round(sum(tiempos) / len(tiempos), 3), "max": round(max(tiempos), 3)},
            "tasa_de_error_en_las_corridas": [c["capturas_con_error"] for c in oficiales if "capturas_con_error" in c] and sum(c["capturas_con_error"] for c in oficiales) / sum(c["capturas"] for c in oficiales),
            "union_espacial_y_agregado_s": {"establecimientos": int(len(ref)), "poligonos": int(len(ageb)), "mejor_de_3": round(min(ts), 4)}},
        "capacidad_de_interaccion": {"pestanas_del_tablero": pestanas},
        "fiabilidad": {"periodo": fiab["ventana"], "tasa_de_exito": fiab["tasa_exito"], "mttr": fiab["mttr"], "mtbf_horas_exploratorio": fiab["estimacion_exploratoria"].get("mtbf_horas"),
                       "disponibilidad_exploratoria": fiab["estimacion_exploratoria"].get("disponibilidad_observada_por_tiempo"), "ejecuciones": fiab["ejecuciones"]},
        "mantenibilidad": {"lineas_de_codigo": codigo, "lineas_de_prueba": pruebas, "relacion_prueba_codigo": round(pruebas / codigo, 3)},
    }
    if herramientas:
        ruff = subprocess.run([sys.executable, "-m", "ruff", "check", "."], cwd=raiz, capture_output=True, text=True)
        out["mantenibilidad"]["ruff"] = {"codigo_de_salida": ruff.returncode, "resumen": ruff.stdout.strip().splitlines()[-1] if ruff.stdout.strip() else ""}
        audit = {}
        for archivo in ("requirements.txt", "requirements-lab.txt", "requirements-dev.txt"):
            r = subprocess.run([sys.executable, "-m", "pip_audit", "-r", archivo, "--no-deps", "--disable-pip"], cwd=raiz, capture_output=True, text=True)
            audit[archivo] = "sin vulnerabilidades conocidas" if r.returncode == 0 else r.stdout.strip()[-200:] or "error"
        out["seguridad"] = {"pip_audit": audit}
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
