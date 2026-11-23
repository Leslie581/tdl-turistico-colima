"""Confirmación del experimento 2^3 de E2: T8 (candidata) frente a T1 (configuración de E1).

    python -m laboratorio.experimento.confirmacion --ejecutar          # 12 corridas oficiales (código confirmado)
    python -m laboratorio.experimento.confirmacion --analizar          # criterios fijados en docs/E2/anova_2x3.md §9

Protocolo (fijado ANTES de ejecutar, docs/E2/anova_2x3.md §9): 6 corridas de T1 (1 proceso, json, csv) y 6 de T8
(4 procesos, orjson, parquet) en orden aleatorizado con la semilla 20261123, una sesión nueva, la misma carga (16 copias
del bronce DENUE, fuera del repositorio) y una corrida de calentamiento no registrada. Cada corrida usa
``arnes.ejecutar_corrida``: misma tarea y mismas definiciones de ``tiempo_s`` y ``tasa_error`` que el factorial.
Resultados en un archivo APARTE (``resultados/confirmacion_2x3.jsonl``); ``corridas_2x3.jsonl`` no se lee ni se toca
al ejecutar. Sin red. El bronce se comprueba por hash antes y después.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np

from laboratorio.experimento import arnes as ar

SEMILLA = 20261123
N_POR_TRATAMIENTO = 6
TRATAMIENTOS = {"T1": {"tratamiento": 1, "procesos": 1, "analizador": "json", "formato": "csv"},
                "T8": {"tratamiento": 8, "procesos": 4, "analizador": "orjson", "formato": "parquet"}}
SALIDA = ar.SALIDA.parent / "confirmacion_2x3.jsonl"
RESUMEN = ar.SALIDA.parent / "confirmacion"
# Criterios fijados en docs/E2/anova_2x3.md §9 antes de correr (no se recalculan con los datos de confirmación)
INTERVALO_PREDICCION_T8 = (0.68, 8.58)
MEJORA_MINIMA = 0.20
ALFA = 0.05


def plan(semilla: int = SEMILLA) -> list[dict]:
    """Orden aleatorizado de las 12 corridas: 6 de cada tratamiento."""
    etiquetas = ["T1"] * N_POR_TRATAMIENTO + ["T8"] * N_POR_TRATAMIENTO
    orden = np.random.default_rng(semilla).permutation(len(etiquetas))
    return [{"orden": i, "etiqueta": etiquetas[j], **TRATAMIENTOS[etiquetas[j]]} for i, j in enumerate(orden, start=1)]


def condiciones_equipo() -> dict:
    """Condiciones observables del equipo antes de correr (Windows). Lo que no se puede leer queda en None."""
    def ps(comando: str) -> str | None:
        try:
            return subprocess.run(["powershell", "-NoProfile", "-Command", comando], capture_output=True, text=True,
                                  timeout=30, check=True).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None
    bateria = ps("(Get-CimInstance Win32_Battery | Select-Object -First 1).BatteryStatus")
    onedrive = ps("@(Get-Process OneDrive -ErrorAction SilentlyContinue).Count")
    plan_energia = ps("powercfg /getactivescheme")
    return {
        "corriente_alterna": None if not bateria else bateria == "2",   # BatteryStatus 2 = conectado a la corriente
        "bateria_estado_wmi": bateria or None,
        "procesos_onedrive": int(onedrive) if onedrive and onedrive.isdigit() else None,
        "plan_energia": plan_energia.split("(")[-1].rstrip(")") if plan_energia else None,
        "nota": "la pausa de la sincronización de OneDrive no es legible desde aquí; la declara quien ejecuta",
    }


def ejecutar(salida: Path = SALIDA, copias: int = ar.COPIAS, semilla: int = SEMILLA, bronce: Path = ar.BRONCE_DENUE,
             piloto: bool = False, calentamiento: bool = True, declaracion: str = "", solo: list[int] | None = None) -> list[dict]:
    """Corre las corridas del plan que aún no están en ``salida`` (no repite ninguna). Exige código confirmado salvo piloto."""
    salida = Path(salida)
    if piloto and salida.resolve() == SALIDA.resolve():
        raise ValueError("un piloto no se escribe en el archivo oficial de la confirmación")
    if salida.resolve() == ar.SALIDA.resolve():
        raise ValueError("la confirmación no escribe en el archivo de las corridas factoriales")
    modificado = ar.codigo_modificado(salida)
    if not piloto and modificado is not False:
        raise RuntimeError("corrida oficial: confirme el código en git antes de ejecutar (o use piloto)")
    hechos = {r["orden"] for r in ar.leer_registros(salida) if r.get("semilla") == semilla}
    pendientes = [p for p in plan(semilla) if p["orden"] not in hechos and (not solo or p["orden"] in solo)]
    if not pendientes:
        return []
    comun = {"sesion": "confirmacion", "version_arnes": ar.VERSION_ARNES, "semilla": semilla,
             "commit": ar._git("rev-parse", "HEAD") or None, "codigo_modificado": modificado, "piloto": bool(piloto),
             "entorno": ar.entorno(), "condiciones": condiciones_equipo(), "declaracion_condiciones": declaracion}
    huella = ar.huella_bronce(bronce)
    salida.parent.mkdir(parents=True, exist_ok=True)
    hechas = []
    with tempfile.TemporaryDirectory(prefix="tdl_e2_conf_") as tmp:
        carga = ar.preparar_carga(Path(tmp) / "carga", copias, bronce)
        manifiesto = {k: v for k, v in carga.items() if k not in ("raiz", "archivos")}
        if calentamiento:                                   # igual que en el factorial: no se registra
            ar.ejecutar_corrida(carga, 1, "json", "csv", Path(tmp) / "calentamiento")
        for p in pendientes:
            niveles = {k: p[k] for k in ("procesos", "analizador", "formato")}
            rec = ar.ejecutar_corrida(carga, **niveles, trabajo=Path(tmp) / f"o{p['orden']}")
            rec = {"orden": p["orden"], "etiqueta": p["etiqueta"], "tratamiento": p["tratamiento"], **niveles,
                   "fecha_local": datetime.now().astimezone().date().isoformat(), **rec, **comun,
                   "carga": manifiesto, "calentamiento_previo": bool(calentamiento)}
            with salida.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
            hechas.append(rec)
    if ar.huella_bronce(bronce) != huella:
        raise RuntimeError("el bronce original cambió durante la confirmación: las corridas no son válidas")
    return hechas


# ---------------------------------------------------------------- análisis con los criterios fijados
def analizar(ruta: Path = SALIDA, semilla: int = SEMILLA, incluir_piloto: bool = False) -> dict:
    from scipy import stats
    rs = [r for r in ar.leer_registros(ruta) if r.get("semilla") == semilla and (incluir_piloto or not r.get("piloto"))]
    validas = {e: np.array([r["tiempo_s"] for r in rs if r["etiqueta"] == e and r["estado"] == "ok"]) for e in TRATAMIENTOS}
    fallidas = sum(r["estado"] != "ok" for r in rs)
    out = {"corridas_registradas": len(rs), "corridas_fallidas": fallidas,
           "tasa_error": {e: sorted({r["tasa_error"] for r in rs if r["etiqueta"] == e and r["estado"] == "ok"})
                          for e in TRATAMIENTOS},
           "por_tratamiento": {e: {"n": int(len(v)), "media_s": float(v.mean()) if len(v) else None,
                                   "de_s": float(v.std(ddof=1)) if len(v) > 1 else None,
                                   "tiempos_s": [float(x) for x in v]} for e, v in validas.items()}}
    completo = all(len(v) == N_POR_TRATAMIENTO for v in validas.values())
    out["evaluable"] = completo
    if not completo:
        out["motivo"] = "faltan corridas válidas: los criterios no se evalúan (no se rellenan valores)"
        return out
    t1, t8 = validas["T1"], validas["T8"]
    dif = t1.mean() - t8.mean()
    v1, v8 = t1.var(ddof=1) / len(t1), t8.var(ddof=1) / len(t8)
    ee = float(np.sqrt(v1 + v8))
    gl = float((v1 + v8) ** 2 / (v1 ** 2 / (len(t1) - 1) + v8 ** 2 / (len(t8) - 1)))    # Welch-Satterthwaite
    welch = stats.ttest_ind(t1, t8, equal_var=False, alternative="greater")               # H1: T1 más lento que T8
    tc = stats.t.ppf(1 - ALFA / 2, gl)
    mejora = dif / t1.mean()
    mw = stats.mannwhitneyu(t1, t8, alternative="greater", method="exact")
    c1 = INTERVALO_PREDICCION_T8[0] <= t8.mean() <= INTERVALO_PREDICCION_T8[1]
    c2_welch, c2_mejora = bool(welch.pvalue < ALFA), bool(mejora >= MEJORA_MINIMA)
    out.update({
        "diferencia_T1_menos_T8_s": float(dif), "mejora_relativa": float(mejora), "ee_diferencia_s": ee,
        "gl_welch": gl, "ic95_diferencia_s": [float(dif - tc * ee), float(dif + tc * ee)],
        "welch_unilateral": {"t": float(welch.statistic), "p": float(welch.pvalue)},
        "complementario_mann_whitney_unilateral": {"U": float(mw.statistic), "p": float(mw.pvalue),
                                                   "nota": "no sustituye a Welch; sin supuesto de normalidad"},
        "normalidad_shapiro": {e: float(stats.shapiro(v).pvalue) for e, v in validas.items()},
        "criterios": {
            "1_media_T8_en_intervalo_de_prediccion": {"intervalo_s": list(INTERVALO_PREDICCION_T8),
                                                      "media_T8_s": float(t8.mean()), "cumple": bool(c1)},
            "2a_welch_unilateral_p_menor_005": {"p": float(welch.pvalue), "cumple": c2_welch},
            "2b_mejora_al_menos_20pct": {"mejora": float(mejora), "cumple": c2_mejora},
        },
        "confirmada": bool(c1 and c2_welch and c2_mejora),
    })
    return out


def escribir_resumen(r: dict, carpeta: Path = RESUMEN) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / "resumen.json"
    ruta.write_bytes((json.dumps(r, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    return ruta


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Confirmación T8 frente a T1 (experimento 2^3 de E2)")
    ap.add_argument("--ejecutar", action="store_true")
    ap.add_argument("--analizar", action="store_true")
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--copias", type=int, default=ar.COPIAS)
    ap.add_argument("--piloto", action="store_true")
    ap.add_argument("--declaracion", default="", help="condiciones que declara quien ejecuta (p. ej. OneDrive en pausa)")
    a = ap.parse_args(argv)
    if a.ejecutar:
        for r in ejecutar(Path(a.salida), a.copias, piloto=a.piloto, declaracion=a.declaracion):
            print(f"#{r['orden']} {r['etiqueta']} {r['procesos']}/{r['analizador']}/{r['formato']}: {r['estado']} "
                  f"tiempo_s={r['tiempo_s']} tasa_error={r['tasa_error']}")
    if a.analizar:
        r = analizar(Path(a.salida), incluir_piloto=a.piloto)
        if not a.piloto and Path(a.salida).resolve() == SALIDA.resolve():
            escribir_resumen(r)
        print(json.dumps(r, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
