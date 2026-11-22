"""Experimento de dos factores de E2: carga (1x, 5x, 10x) x procesos (1, 4), ANOVA de dos vías con interacción.

    python -m laboratorio.experimento.dos_factores --matriz            # escribe resultados/matriz_3x2.csv
    python -m laboratorio.experimento.dos_factores --ejecutar          # 24 corridas oficiales (código confirmado)
    python -m laboratorio.experimento.dos_factores --analizar          # ANOVA, supuestos, figuras -> resultados/dos_factores/

Diseño (docs/E2/dos_factores_3x2.md): 6 tratamientos en 4 bloques completos; cada bloque es un tramo consecutivo de la
sesión con los 6 tratamientos en orden aleatorio (semilla 20261124). El bloqueo absorbe la deriva con el orden que se
observó en la confirmación del 2^3. Analizador ``json`` y formato ``csv`` fijos (configuración de E1). Cada corrida usa
``arnes.ejecutar_corrida``: misma tarea y mismas definiciones de ``tiempo_s`` y ``tasa_error`` que el 2^3. La carga son
copias byte a byte del bronce DENUE fuera del repositorio: es carga técnica de rendimiento, no datos turísticos nuevos.
Resultados en un archivo APARTE (``resultados/dos_factores_3x2.jsonl``). Sin red. El bronce se comprueba por hash.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from laboratorio.experimento import arnes as ar
from laboratorio.experimento.confirmacion import condiciones_equipo

SEMILLA = 20261124
CARGAS = (1, 5, 10)                 # factor A: copias del bronce real (1x, 5x, 10x)
PROCESOS = (1, 4)                   # factor B
BLOQUES = 4                         # réplicas, una por bloque temporal
ANALIZADOR, FORMATO = "json", "csv"  # constantes (configuración de E1)
TRATAMIENTOS = {i: {"carga": c, "procesos": p} for i, (c, p) in enumerate(itertools.product(CARGAS, PROCESOS), start=1)}
CARPETA = ar.SALIDA.parent
SALIDA = CARPETA / "dos_factores_3x2.jsonl"
MATRIZ = CARPETA / "matriz_3x2.csv"
RESUMEN = CARPETA / "dos_factores"
PROTEGIDOS = (ar.SALIDA, CARPETA / "confirmacion_2x3.jsonl")
FORMULA = "y ~ C(bloque, Sum) + C(carga, Sum) * C(procesos, Sum)"
NOMBRES = {"C(bloque, Sum)": "Bloque", "C(carga, Sum)": "A carga", "C(procesos, Sum)": "B procesos",
           "C(carga, Sum):C(procesos, Sum)": "AB carga x procesos", "Residual": "Residuo"}
ALFA = 0.05


# ---------------------------------------------------------------- matriz
def matriz(semilla: int = SEMILLA, bloques: int = BLOQUES) -> pd.DataFrame:
    """Bloques completos: en cada bloque, los 6 tratamientos en orden aleatorio; ``secuencia`` es el orden global."""
    rng = np.random.default_rng(semilla)
    filas = []
    for b in range(1, bloques + 1):
        for t in rng.permutation(list(TRATAMIENTOS)):
            filas.append({"bloque": b, "tratamiento": int(t), **TRATAMIENTOS[int(t)]})
    df = pd.DataFrame(filas)
    df.insert(0, "secuencia", range(1, len(df) + 1))
    return df.assign(analizador=ANALIZADOR, formato=FORMATO)


def _no_protegido(salida: Path) -> None:
    if any(salida.resolve() == p.resolve() for p in PROTEGIDOS):
        raise ValueError("este experimento no escribe en los archivos de experimentos anteriores")


# ---------------------------------------------------------------- ejecución
def ejecutar(salida: Path = SALIDA, semilla: int = SEMILLA, bronce: Path = ar.BRONCE_DENUE, piloto: bool = False,
             calentamiento: bool = True, declaracion: str = "", solo: list[int] | None = None) -> list[dict]:
    """Corre las corridas de la matriz que faltan en ``salida`` (no repite). Exige código confirmado salvo piloto."""
    salida = Path(salida)
    _no_protegido(salida)
    if piloto and salida.resolve() == SALIDA.resolve():
        raise ValueError("un piloto no se escribe en el archivo oficial")
    modificado = ar.codigo_modificado(salida)
    if not piloto and modificado is not False:
        raise RuntimeError("corrida oficial: confirme el código en git antes de ejecutar (o use piloto)")
    hechos = {r["secuencia"] for r in ar.leer_registros(salida) if r.get("semilla") == semilla}
    pendientes = [p for p in matriz(semilla).to_dict("records")
                  if p["secuencia"] not in hechos and (not solo or p["secuencia"] in solo)]
    if not pendientes:
        return []
    comun = {"sesion": "dos_factores", "version_arnes": ar.VERSION_ARNES, "semilla": semilla,
             "commit": ar._git("rev-parse", "HEAD") or None, "codigo_modificado": modificado, "piloto": bool(piloto),
             "entorno": ar.entorno(), "condiciones": condiciones_equipo(), "declaracion_condiciones": declaracion}
    huella = ar.huella_bronce(bronce)
    salida.parent.mkdir(parents=True, exist_ok=True)
    hechas = []
    with tempfile.TemporaryDirectory(prefix="tdl_e2_2f_") as tmp:
        cargas = {c: ar.preparar_carga(Path(tmp) / f"carga_{c:02d}x", c, bronce)
                  for c in sorted({p["carga"] for p in pendientes})}
        if calentamiento:                                   # una corrida no registrada por nivel de carga
            for c, carga in cargas.items():
                ar.ejecutar_corrida(carga, 1, ANALIZADOR, FORMATO, Path(tmp) / f"calentamiento_{c}")
        for p in pendientes:
            carga = cargas[p["carga"]]
            rec = ar.ejecutar_corrida(carga, p["procesos"], ANALIZADOR, FORMATO, Path(tmp) / f"s{p['secuencia']}")
            rec = {**p, "fecha_local": datetime.now().astimezone().date().isoformat(), **rec, **comun,
                   "carga_manifiesto": {k: v for k, v in carga.items() if k not in ("raiz", "archivos")},
                   "calentamiento_previo": bool(calentamiento)}
            with salida.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True, default=int) + "\n")
            hechas.append(rec)
    if ar.huella_bronce(bronce) != huella:
        raise RuntimeError("el bronce original cambió durante el experimento: las corridas no son válidas")
    return hechas


# ---------------------------------------------------------------- análisis
def cargar(ruta: Path = SALIDA, semilla: int = SEMILLA, incluir_piloto: bool = False) -> pd.DataFrame:
    """Lee las corridas válidas; exige la matriz completa (sin fallos ni huecos) para no rellenar nada."""
    rs = [r for r in ar.leer_registros(ruta) if r.get("semilla") == semilla and (incluir_piloto or not r.get("piloto"))]
    fallidas = [r["secuencia"] for r in rs if r["estado"] != "ok"]
    if fallidas:
        raise ValueError(f"corridas fallidas {fallidas}: el diseño queda incompleto y no se analiza")
    df = pd.DataFrame([{k: r[k] for k in ("secuencia", "bloque", "tratamiento", "carga", "procesos", "tiempo_s",
                                          "tasa_error", "capturas")} for r in rs])
    esperado = matriz(semilla)
    if len(df) != len(esperado) or df.duplicated("secuencia").any() or \
            not df.sort_values("secuencia")[["secuencia", "bloque", "tratamiento"]].reset_index(drop=True).equals(
                esperado[["secuencia", "bloque", "tratamiento"]]):
        raise ValueError("las corridas no coinciden con la matriz completa")
    return df.sort_values("secuencia").reset_index(drop=True)


def ajustar(df: pd.DataFrame, respuesta: str = "tiempo_s"):
    import statsmodels.formula.api as smf
    return smf.ols(FORMULA, df.assign(y=df[respuesta])).fit()


def tabla_anova(modelo, robusto: str | None = None) -> pd.DataFrame:
    """ANOVA tipo II (balanceado: igual a tipo I y III) con eta^2 parcial y omega^2 parcial."""
    from statsmodels.stats.anova import anova_lm
    t = anova_lm(modelo, typ=2, robust=robusto).rename(index=NOMBRES)
    t.columns = ["SC", "gl", "F", "p"]
    t.insert(2, "CM", t.SC / t.gl)
    sce, cme, n = t.loc["Residuo", "SC"], t.loc["Residuo", "CM"], modelo.nobs
    ef = t.drop("Residuo")
    t["eta2_parcial"] = ef.SC / (ef.SC + sce)
    t["omega2_parcial"] = (ef.SC - ef.gl * cme) / (ef.SC + (n - ef.gl) * cme)
    t.loc["Total"] = [t.SC.sum(), t.gl.sum(), np.nan, np.nan, np.nan, np.nan, np.nan]
    return t


def medias(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    g = df.groupby(["carga", "procesos"]).tiempo_s
    celdas = g.agg(n="size", media_s="mean", de_s="std", min_s="min", max_s="max").reset_index()
    return {"celdas": celdas,
            "carga": df.groupby("carga").tiempo_s.agg(n="size", media_s="mean", de_s="std").reset_index(),
            "procesos": df.groupby("procesos").tiempo_s.agg(n="size", media_s="mean", de_s="std").reset_index()}


def efectos_simples(df: pd.DataFrame, modelo) -> pd.DataFrame:
    """1 frente a 4 procesos en cada carga, con el CME del modelo y corrección de Holm (3 comparaciones)."""
    from scipy import stats
    from statsmodels.stats.multitest import multipletests
    r = df.groupby(["carga", "procesos"]).size().min()
    ee = np.sqrt(2 * modelo.mse_resid / r)
    tc = stats.t.ppf(1 - ALFA / 2, modelo.df_resid)
    filas = []
    for c in CARGAS:
        m1, m4 = (df.tiempo_s[(df.carga == c) & (df.procesos == p)].mean() for p in PROCESOS)
        t = (m1 - m4) / ee
        filas.append({"carga": c, "media_1_proceso_s": m1, "media_4_procesos_s": m4, "diferencia_s": m1 - m4,
                      "ic95_inf_s": m1 - m4 - tc * ee, "ic95_sup_s": m1 - m4 + tc * ee, "aceleracion": m1 / m4,
                      "t": t, "p": 2 * stats.t.sf(abs(t), modelo.df_resid)})
    out = pd.DataFrame(filas)
    out["p_holm"] = multipletests(out.p, method="holm")[1]
    return out


def box_cox(df: pd.DataFrame, lambdas=np.linspace(-2, 2, 401)) -> dict:
    from scipy import stats
    y = df.tiempo_s.to_numpy()
    gm = np.exp(np.log(y).mean())
    sse = np.array([ajustar(df.assign(z=gm * np.log(y) if abs(lam) < 1e-12 else (y ** lam - 1) / (lam * gm ** (lam - 1))),
                            "z").ssr for lam in lambdas])
    llf = -len(y) / 2 * np.log(sse / len(y))
    dentro = lambdas[llf >= llf.max() - stats.chi2.ppf(0.95, 1) / 2]
    return {"lambda_max_verosimilitud": round(float(lambdas[llf.argmax()]), 3),
            "ic95_lambda": [round(float(dentro.min()), 3), round(float(dentro.max()), 3)],
            "incluye_1": bool(dentro.min() <= 1 <= dentro.max()), "incluye_0_log": bool(dentro.min() <= 0 <= dentro.max())}


def supuestos(df: pd.DataFrame, modelo) -> dict:
    from scipy import stats
    from statsmodels.stats.stattools import durbin_watson
    res = modelo.resid.to_numpy()
    infl = modelo.get_influence()
    est = infl.resid_studentized_external
    cook = infl.cooks_distance[0]
    tiempos = [df.tiempo_s[(df.carga == c) & (df.procesos == p)].to_numpy() for c, p in (v.values() for v in TRATAMIENTOS.values())]
    deriva = np.polyfit(df.secuencia, res, 1)[0]
    r_orden = stats.pearsonr(df.secuencia, res)
    return {
        "normalidad_shapiro_residuos": {"W": float(stats.shapiro(res).statistic), "p": float(stats.shapiro(res).pvalue)},
        "homogeneidad_brown_forsythe_celdas": {"F": float(stats.levene(*tiempos, center="median").statistic),
                                               "p": float(stats.levene(*tiempos, center="median").pvalue)},
        "de_por_celda_s": {f"{v['carga']}x/{v['procesos']}p": float(np.std(t, ddof=1))
                           for v, t in zip(TRATAMIENTOS.values(), tiempos)},
        "razon_varianzas_max_min": float(max(np.var(t, ddof=1) for t in tiempos) / min(np.var(t, ddof=1) for t in tiempos)),
        "independencia_durbin_watson": float(durbin_watson(res)),
        "residuo_vs_secuencia": {"pendiente_s_por_corrida": float(deriva), "r": float(r_orden.statistic),
                                 "p": float(r_orden.pvalue)},
        "atipicos": {"max_abs_residuo_studentizado": float(np.abs(est).max()),
                     "secuencias_abs_mayor_3": df.secuencia[np.abs(est) > 3].tolist(),
                     "max_cook": float(cook.max()), "umbral_cook_4_n": 4 / len(df),
                     "secuencias_cook_mayor_4_n": df.secuencia[cook > 4 / len(df)].tolist()},
        "adecuacion": {"r2": float(modelo.rsquared), "r2_ajustado": float(modelo.rsquared_adj),
                       "cme": float(modelo.mse_resid), "gl_residuo": int(modelo.df_resid)},
        "box_cox": box_cox(df),
    }


def sensibilidad(df: pd.DataFrame) -> pd.DataFrame:
    """Análisis complementarios (no sustituyen al principal): log(t), errores robustos HC3 y Kruskal-Wallis por celda."""
    from scipy import stats
    filas = []
    for nombre, t in (("log(tiempo_s)", tabla_anova(ajustar(df.assign(lt=np.log(df.tiempo_s)), "lt"))),
                      ("tiempo_s con HC3", tabla_anova(ajustar(df), robusto="hc3"))):
        for termino in ("A carga", "B procesos", "AB carga x procesos"):
            filas.append({"analisis": nombre, "termino": termino, "F": t.loc[termino, "F"], "p": t.loc[termino, "p"]})
    kw = stats.kruskal(*[df.tiempo_s[df.tratamiento == i] for i in TRATAMIENTOS])
    filas.append({"analisis": "Kruskal-Wallis (6 celdas)", "termino": "tratamiento", "F": kw.statistic, "p": kw.pvalue})
    return pd.DataFrame(filas)


def figuras(df: pd.DataFrame, modelo, carpeta: Path) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy import stats

    from laboratorio.experimento.anova import _guardar
    carpeta.mkdir(parents=True, exist_ok=True)
    datos = {"principales": {f: df.groupby(f).tiempo_s.mean().tolist() for f in ("carga", "procesos")},
             "interaccion": {str(p): df[df.procesos == p].groupby("carga").tiempo_s.mean().tolist() for p in PROCESOS}}
    fig, ax = plt.subplots(1, 2, figsize=(8, 3.4), sharey=True)
    for a, f in zip(ax, ("carga", "procesos")):
        m = df.groupby(f).tiempo_s.mean()
        a.plot([str(x) for x in m.index], m.values, "o-", color="#1f5f99")
        a.set_xlabel("carga (copias del bronce)" if f == "carga" else "procesos")
    ax[0].set_ylabel("tiempo medio (s)")
    fig.suptitle("Efectos principales")
    _guardar(fig, carpeta / "efectos_principales.png")
    fig, a = plt.subplots(figsize=(5.2, 3.6))
    for p, color in zip(PROCESOS, ("#1f5f99", "#c0612b")):
        g = df[df.procesos == p].groupby("carga").tiempo_s
        a.errorbar([str(c) for c in CARGAS], g.mean().values, yerr=g.std().values, fmt="o-", capsize=3, color=color,
                   label=f"{p} proceso{'s' if p > 1 else ''}")
    a.set_xlabel("carga (copias del bronce)")
    a.set_ylabel("tiempo medio (s) ± DE")
    a.set_title("Interacción carga × procesos")
    a.legend()
    _guardar(fig, carpeta / "interaccion.png")
    res, aj = modelo.resid, modelo.fittedvalues
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
    stats.probplot(res, plot=ax[0])
    ax[0].set_title("Q-Q de residuos")
    ax[1].scatter(aj, res, color="#1f5f99")
    ax[1].axhline(0, color="gray", lw=0.8)
    ax[1].set_xlabel("ajustados (s)")
    ax[1].set_ylabel("residuo (s)")
    ax[1].set_title("Residuos frente a ajustados")
    ax[2].plot(df.secuencia, res, "o-", color="#1f5f99")
    ax[2].axhline(0, color="gray", lw=0.8)
    ax[2].set_xlabel("secuencia")
    ax[2].set_title("Residuos frente al orden")
    _guardar(fig, carpeta / "residuos.png")
    (carpeta / "datos_figuras.json").write_text(json.dumps(datos, indent=1) + "\n", encoding="utf-8")
    return datos


def analizar(entrada: Path = SALIDA, salida: Path = RESUMEN, incluir_piloto: bool = False) -> dict:
    df = cargar(entrada, incluir_piloto=incluir_piloto)
    modelo = ajustar(df)
    t = tabla_anova(modelo)
    m = medias(df)
    es = efectos_simples(df, modelo)
    sens = sensibilidad(df)
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    t.round(6).to_csv(salida / "anova.csv", lineterminator="\n")
    m["celdas"].round(6).to_csv(salida / "medias_tratamiento.csv", index=False, lineterminator="\n")
    es.round(6).to_csv(salida / "efectos_simples.csv", index=False, lineterminator="\n")
    sens.round(6).to_csv(salida / "sensibilidad.csv", index=False, lineterminator="\n")
    df.assign(ajustado=modelo.fittedvalues.round(6), residuo=modelo.resid.round(6)).to_csv(
        salida / "residuos.csv", index=False, lineterminator="\n")
    resumen = {"sha256_entrada": ar.sha256_archivo(Path(entrada)), "n": int(len(df)), "formula": FORMULA,
               "rango_matriz": int(np.linalg.matrix_rank(modelo.model.exog)), "gl_residuo": int(modelo.df_resid),
               "tasa_error_max": float(df.tasa_error.max()),
               "medias_carga": m["carga"].round(6).to_dict("records"),
               "medias_procesos": m["procesos"].round(6).to_dict("records"),
               "supuestos": supuestos(df, modelo)}
    (salida / "resumen.json").write_bytes((json.dumps(resumen, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    figuras(df, modelo, salida / "figuras")
    return {"anova": t, "medias": m, "efectos_simples": es, "sensibilidad": sens, "resumen": resumen}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Experimento carga x procesos (dos factores) de E2")
    ap.add_argument("--matriz", action="store_true")
    ap.add_argument("--ejecutar", action="store_true")
    ap.add_argument("--analizar", action="store_true")
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--resumen", default=str(RESUMEN))
    ap.add_argument("--piloto", action="store_true")
    ap.add_argument("--declaracion", default="", help="condiciones que declara quien ejecuta (p. ej. OneDrive en pausa)")
    a = ap.parse_args(argv)
    if a.matriz:
        matriz().to_csv(MATRIZ, index=False, lineterminator="\n")
        print(MATRIZ)
    if a.ejecutar:
        for r in ejecutar(Path(a.salida), piloto=a.piloto, declaracion=a.declaracion):
            print(f"#{r['secuencia']} b{r['bloque']} {r['carga']}x/{r['procesos']}p: {r['estado']} "
                  f"tiempo_s={r['tiempo_s']} tasa_error={r['tasa_error']}")
    if a.analizar:
        r = analizar(Path(a.salida), Path(a.resumen), incluir_piloto=a.piloto)
        with pd.option_context("display.width", 160, "display.max_columns", 20):
            print(r["anova"].round(4), r["efectos_simples"].round(4), r["sensibilidad"].round(4), sep="\n\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
