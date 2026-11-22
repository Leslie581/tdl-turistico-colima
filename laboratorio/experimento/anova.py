"""ANOVA de efectos fijos del experimento 2^3 de E2 con bloques (ruta ingeniería).

    python -m laboratorio.experimento.anova

Datos: SOLO las 16 corridas oficiales de ``resultados/corridas_2x3.jsonl`` (piloto = false, estado = ok). No se
eliminan, sustituyen ni repiten observaciones; el archivo de entrada no se modifica (se registra su SHA-256).
Modelo: ``tiempo_s ~ C(bloque, Sum) + x_proc * x_anal * x_form`` con los factores codificados en -1 / +1 (diseño
equilibrado y ortogonal: las sumas de cuadrados de tipo I, II y III coinciden). Los nombres ``x_*`` evitan el choque
del factor C (formato) con la función ``C()`` de patsy.
Salidas en ``resultados/anova/``: tablas CSV, ``resumen.json`` con supuestos y alternativas, y figuras PNG.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ENTRADA = Path(__file__).resolve().parent / "resultados" / "corridas_2x3.jsonl"
SALIDA = Path(__file__).resolve().parent / "resultados" / "anova"
ALFA = 0.05
SEMILLA_PERMUTACIONES = 20261122
N_PERMUTACIONES = 20000
FACTORES = {"x_proc": ("procesos", 1, 4), "x_anal": ("analizador", "json", "orjson"), "x_form": ("formato", "csv", "parquet")}
TERMINOS = ["x_proc", "x_anal", "x_form", "x_proc:x_anal", "x_proc:x_form", "x_anal:x_form", "x_proc:x_anal:x_form"]
NOMBRES = {"C(bloque, Sum)": "Bloque", "x_proc": "A procesos", "x_anal": "B analizador", "x_form": "C formato",
           "x_proc:x_anal": "AB", "x_proc:x_form": "AC", "x_anal:x_form": "BC", "x_proc:x_anal:x_form": "ABC",
           "Residual": "Residuo"}
FORMULA = "y ~ C(bloque, Sum) + x_proc * x_anal * x_form"


# ---------------------------------------------------------------- datos
def cargar(ruta: Path = ENTRADA) -> pd.DataFrame:
    """Las 16 corridas oficiales, en orden de ejecución. Falla si el diseño no está completo y equilibrado."""
    filas = [json.loads(x) for x in Path(ruta).read_text(encoding="utf-8").splitlines() if x.strip()]
    df = pd.DataFrame([{
        "bloque": r["bloque"], "orden": r["orden_en_bloque"], "tratamiento": r["tratamiento"],
        "procesos": r["procesos"], "analizador": r["analizador"], "formato": r["formato"],
        "x_proc": r["procesos_cod"], "x_anal": r["analizador_cod"], "x_form": r["formato_cod"],
        "tiempo_s": r["tiempo_s"], "t_proc": r["tiempo_procesamiento_s"],
        "t_es": r["tiempo_escritura_s"] + r["tiempo_lectura_s"], "tasa_error": r["tasa_error"], "piloto": r["piloto"], "estado": r["estado"],
    } for r in filas])
    df = df[(~df.piloto) & (df.estado == "ok")].sort_values(["bloque", "orden"]).reset_index(drop=True)
    if len(df) != 16 or set(df.groupby("bloque").size()) != {8} or set(df.groupby("tratamiento").size()) != {2}:
        raise ValueError("se esperan 16 corridas oficiales: 8 tratamientos x 2 bloques, una por bloque")
    if df.duplicated(["bloque", "tratamiento"]).any() or df.tiempo_s.isna().any():
        raise ValueError("tratamiento repetido en un bloque o tiempo ausente")
    for x, (col, bajo, alto) in FACTORES.items():
        if not ((df[x] == -1) == (df[col] == bajo)).all() or not ((df[x] == 1) == (df[col] == alto)).all():
            raise ValueError(f"la codificación de {col} no corresponde a sus niveles")
    df["secuencia"] = range(1, 17)                      # orden global de ejecución (dia_1 y luego dia_2)
    return df


def sha256(ruta: Path) -> str:
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


# ---------------------------------------------------------------- modelo
def ajustar(df: pd.DataFrame, respuesta: str = "tiempo_s"):
    import statsmodels.formula.api as smf
    return smf.ols(FORMULA, data=df.assign(y=df[respuesta])).fit()


def tabla_anova(modelo) -> pd.DataFrame:
    import statsmodels.api as sm
    t = sm.stats.anova_lm(modelo, typ=2).rename(columns={"sum_sq": "SC", "df": "gl", "F": "F", "PR(>F)": "p"})
    t["CM"] = t.SC / t.gl
    sce = t.loc["Residual", "SC"]
    t["eta2_parcial"] = t.SC / (t.SC + sce)
    t.loc["Residual", "eta2_parcial"] = np.nan
    t["eta2"] = t.SC / t.SC.sum()
    t.index = [NOMBRES[i] for i in t.index]
    t = t.loc[["Bloque", "A procesos", "B analizador", "C formato", "AB", "AC", "BC", "ABC", "Residuo"]]
    t.loc["Total"] = [t.SC.sum(), t.gl.sum(), np.nan, np.nan, np.nan, np.nan, 1.0]
    return t[["gl", "SC", "CM", "F", "p", "eta2_parcial", "eta2"]]


def efectos(df: pd.DataFrame, modelo) -> pd.DataFrame:
    """Efecto = media en +1 menos media en -1 (= 2 x coeficiente), con su error estándar e IC del 95 %."""
    from scipy import stats
    ee_coef = np.sqrt(modelo.mse_resid / len(df))              # diseño ortogonal: Var(b) = s^2 / N
    t_crit = stats.t.ppf(1 - ALFA / 2, modelo.df_resid)
    filas = []
    for termino in TERMINOS:
        contraste = np.prod([df[x] for x in termino.split(":")], axis=0)
        efecto = df.tiempo_s[contraste == 1].mean() - df.tiempo_s[contraste == -1].mean()
        assert np.isclose(efecto, 2 * modelo.params[termino])
        filas.append({"termino": NOMBRES[termino], "efecto_s": efecto, "ee_s": 2 * ee_coef,
                      "ic95_inf": efecto - t_crit * 2 * ee_coef, "ic95_sup": efecto + t_crit * 2 * ee_coef,
                      "efecto_pct_media": 100 * efecto / df.tiempo_s.mean(), "p": modelo.pvalues[termino]})
    return pd.DataFrame(filas)


def medias_tratamiento(df: pd.DataFrame, modelo) -> pd.DataFrame:
    from scipy import stats
    g = df.groupby(["tratamiento", "procesos", "analizador", "formato"]).tiempo_s
    m = g.agg(media="mean", dia_1="first", dia_2="last").reset_index()
    ee = np.sqrt(modelo.mse_resid / 2)                          # media de celda con 2 réplicas
    t_crit = stats.t.ppf(1 - ALFA / 2, modelo.df_resid)
    m["ic95_inf"], m["ic95_sup"] = m.media - t_crit * ee, m.media + t_crit * ee
    return m.sort_values("media").reset_index(drop=True)


# ---------------------------------------------------------------- supuestos y alternativas
def no_aditividad_tukey(df: pd.DataFrame, respuesta: str = "tiempo_s") -> dict:
    """Prueba de 1 gl de Tukey para bloque x tratamiento: se agrega (ajustado aditivo)^2 al modelo aditivo."""
    import statsmodels.formula.api as smf
    base = ajustar(df, respuesta)
    d = df.assign(y=df[respuesta], q=(base.fittedvalues - df[respuesta].mean()) ** 2)
    extendido = smf.ols(FORMULA + " + q", data=d).fit()
    f = (base.ssr - extendido.ssr) / (extendido.ssr / extendido.df_resid)
    from scipy import stats
    return {"F": float(f), "gl": [1, int(extendido.df_resid)], "p": float(stats.f.sf(f, 1, extendido.df_resid))}


def box_cox(df: pd.DataFrame, lambdas=np.linspace(-4, 4, 801)) -> dict:
    """Perfil de verosimilitud de Box-Cox para el modelo completo (respuesta normalizada por la media geométrica)."""
    from scipy import stats
    y = df.tiempo_s.to_numpy()
    gm = np.exp(np.log(y).mean())
    sse = []
    for lam in lambdas:
        z = gm * np.log(y) if abs(lam) < 1e-12 else (y ** lam - 1) / (lam * gm ** (lam - 1))
        sse.append(ajustar(df.assign(z=z), "z").ssr)
    sse = np.array(sse)
    llf = -len(y) / 2 * np.log(sse / len(y))
    mejor = lambdas[llf.argmax()]
    dentro = lambdas[llf >= llf.max() - stats.chi2.ppf(0.95, 1) / 2]
    return {"lambda_max_verosimilitud": round(float(mejor), 3), "ic95_lambda": [round(float(dentro.min()), 3),
            round(float(dentro.max()), 3)], "incluye_1": bool(dentro.min() <= 1 <= dentro.max()),
            "incluye_0_log": bool(dentro.min() <= 0 <= dentro.max()),
            "incluye_menos_1_reciproca": bool(dentro.min() <= -1 <= dentro.max()),
            "limite_de_la_rejilla": bool(dentro.min() <= lambdas.min() or dentro.max() >= lambdas.max())}


def prueba_permutacion(df: pd.DataFrame, n: int = N_PERMUTACIONES, semilla: int = SEMILLA_PERMUTACIONES) -> dict:
    """Prueba de aleatorización: se permutan las respuestas DENTRO de cada bloque (como se aleatorizó el diseño) y se
    recalcula el F de cada término. No supone normalidad. Valor p = (1 + #{F* >= F}) / (1 + n)."""
    rng = np.random.default_rng(semilla)
    x = {t: np.prod([df[c].to_numpy() for c in t.split(":")], axis=0).astype(float) for t in TERMINOS}
    X = np.column_stack(list(x.values()))                    # 7 contrastes ortogonales, cada uno con suma 0 por bloque
    bloques = [np.flatnonzero(df.bloque.to_numpy() == b) for b in sorted(df.bloque.unique())]
    y = df.tiempo_s.to_numpy()
    yc = y.copy()
    for idx in bloques:                                       # quitar el efecto del bloque
        yc[idx] -= y[idx].mean()

    def f_terminos(v: np.ndarray) -> np.ndarray:            # v: (k, 16), ya centrada por bloque
        sc = (v @ X) ** 2 / len(y)                           # SC de cada contraste (1 gl)
        sce = (v ** 2).sum(axis=1, keepdims=True) - sc.sum(axis=1, keepdims=True)
        return sc / (sce / 7)

    obs = f_terminos(yc[None, :])[0]
    perm = np.empty((n, len(y)))
    for idx in bloques:
        perm[:, idx] = np.array([rng.permutation(yc[idx]) for _ in range(n)])
    fp = f_terminos(perm)
    p = (1 + (fp >= obs - 1e-12).sum(axis=0)) / (1 + n)
    return {NOMBRES[t]: {"F": float(obs[i]), "p_permutacion": float(p[i])} for i, t in enumerate(TERMINOS)} | {
        "n_permutaciones": n, "semilla": semilla}


def supuestos(df: pd.DataFrame, modelo) -> dict:
    from scipy import stats
    from statsmodels.stats.outliers_influence import OLSInfluence
    from statsmodels.stats.stattools import durbin_watson
    r = modelo.resid.to_numpy()
    inf = OLSInfluence(modelo)
    rstud = inf.resid_studentized_external
    cook = inf.cooks_distance[0]
    sw = stats.shapiro(r)
    homog = {}
    # Por bloque NO se calcula: con 2 réplicas, los residuos del bloque 2 son los del bloque 1 con el signo cambiado
    # (varianzas idénticas por construcción), así que la prueba no es identificable en este diseño.
    for col in ("procesos", "analizador", "formato"):
        grupos = [r[df[col] == v] for v in sorted(df[col].unique())]
        lev = stats.levene(*grupos, center="median")
        homog[col] = {"brown_forsythe_W": float(lev.statistic), "p": float(lev.pvalue),
                      "var_residuo_por_nivel": [float(np.var(g, ddof=1)) for g in grupos]}
    rho_orden = {b: stats.spearmanr(df.orden[df.bloque == b], r[df.bloque == b]) for b in sorted(df.bloque.unique())}
    return {
        "normalidad_shapiro_wilk": {"W": float(sw.statistic), "p": float(sw.pvalue)},
        "homogeneidad_brown_forsythe": homog,
        "independencia": {"durbin_watson_orden_global": float(durbin_watson(r)),
                          "spearman_residuo_vs_orden": {b: {"rho": float(v.statistic), "p": float(v.pvalue)}
                                                        for b, v in rho_orden.items()}},
        "atipicos": {"max_abs_residuo_studentizado": float(np.abs(rstud).max()),
                     "corridas_con_abs_rstud_mayor_3": [int(s) for s in df.secuencia[np.abs(rstud) > 3]],
                     "max_cook": float(cook.max()), "umbral_cook_4_n": 4 / len(df),
                     "palanca_unica": float(inf.hat_matrix_diag[0]),
                     "residuos_simetricos_por_tratamiento": bool(np.allclose(
                         pd.Series(r).groupby(df.tratamiento).sum(), 0, atol=1e-9))},
        "no_aditividad_tukey": no_aditividad_tukey(df),
        "box_cox": box_cox(df),
    }


FILAS = ["Bloque", "A procesos", "B analizador", "C formato", "AB", "AC", "BC", "ABC"]


def sensibilidad(df: pd.DataFrame) -> pd.DataFrame:
    """Valores p del mismo modelo con otras escalas o pesos. Ninguna sustituye al análisis principal (tiempo_s, MCO)."""
    import statsmodels.formula.api as smf
    out = {}
    out["log(tiempo)"] = tabla_anova(ajustar(df.assign(z=np.log(df.tiempo_s)), "z")).loc[FILAS, "p"]
    out["1/tiempo (velocidad)"] = tabla_anova(ajustar(df.assign(z=1 / df.tiempo_s), "z")).loc[FILAS, "p"]
    # MCP: varianza distinta por nivel de procesos (la heterogeneidad detectada), estimada con los residuos del modelo
    r = ajustar(df).resid
    var = r.groupby(df.procesos).var(ddof=1)
    w = 1 / df.procesos.map(var)
    wls = smf.wls(FORMULA, data=df.assign(y=df.tiempo_s), weights=w).fit()
    nombres = {"C(bloque, Sum)[S.dia_1]": "Bloque", **{k: v for k, v in NOMBRES.items() if k in TERMINOS}}
    out["MCP por nivel de procesos"] = pd.Series({nombres[k]: wls.pvalues[k] for k in nombres}).loc[FILAS]
    return pd.DataFrame(out)


def modelo_reducido(df: pd.DataFrame) -> dict:
    """POST HOC (decidido después de ver la tabla): solo efectos principales y bloque, interacciones al residuo."""
    import statsmodels.formula.api as smf
    m = smf.ols("y ~ C(bloque, Sum) + x_proc + x_anal + x_form", data=df.assign(y=df.tiempo_s)).fit()
    pred = m.get_prediction(pd.DataFrame({"bloque": ["dia_1", "dia_2"], "x_proc": [1, 1], "x_anal": [1, 1],
                                          "x_form": [1, 1]})).summary_frame(alpha=ALFA)
    return {"gl_residuo": int(m.df_resid), "cme": float(m.mse_resid),
            "p": {NOMBRES[k]: float(m.pvalues[k]) for k in ("x_proc", "x_anal", "x_form")},
            "prediccion_T8_media_de_bloques_s": float(pred["mean"].mean())}


def efecto_minimo_detectable(modelo, potencia: float = 0.80) -> dict:
    from scipy import stats
    ee = 2 * np.sqrt(modelo.mse_resid / 16)
    t_a, t_b = stats.t.ppf(1 - ALFA / 2, modelo.df_resid), stats.t.ppf(potencia, modelo.df_resid)
    return {"ee_efecto_s": float(ee), "umbral_significancia_s": float(t_a * ee),
            "detectable_con_80pct_potencia_s": float((t_a + t_b) * ee)}


def componentes(df: pd.DataFrame) -> dict:
    """Exploratorio: el tiempo total separado en procesamiento y escritura+lectura (medidos por el arnés)."""
    out = {}
    for col, nombre in (("t_proc", "procesamiento"), ("t_es", "escritura_mas_lectura")):
        m = ajustar(df, col)
        out[nombre] = {NOMBRES[t]: {"efecto_s": float(2 * m.params[t]), "p": float(m.pvalues[t])} for t in TERMINOS[:3]}
    return out


# ---------------------------------------------------------------- figuras
def _guardar(fig, ruta: Path) -> None:
    import matplotlib.pyplot as plt
    fig.tight_layout()
    fig.savefig(ruta, dpi=110, metadata={"Software": None})   # sin versión de matplotlib en los metadatos
    plt.close(fig)


def figuras(df: pd.DataFrame, modelo, carpeta: Path) -> dict[str, Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy import stats
    carpeta.mkdir(parents=True, exist_ok=True)
    r, ajus = modelo.resid, modelo.fittedvalues
    color = df.bloque.map({"dia_1": "#1f77b4", "dia_2": "#d62728"})
    rutas = {}

    fig, ax = plt.subplots(figsize=(5, 4))
    (osm, osr), (pend, inter, _) = stats.probplot(r, dist="norm")
    ax.scatter(osm, osr, c="#1f77b4")
    ax.plot(osm, pend * np.asarray(osm) + inter, color="gray")
    ax.set(title="Q-Q normal de los residuos", xlabel="Cuantil teórico", ylabel="Residuo (s)")
    rutas["qq"] = carpeta / "qq_residuos.png"
    _guardar(fig, rutas["qq"])

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(ajus, r, c=color)
    ax.axhline(0, color="gray", lw=1)
    ax.set(title="Residuos frente a ajustados (azul dia_1, rojo dia_2)", xlabel="Ajustado (s)", ylabel="Residuo (s)")
    rutas["ajustados"] = carpeta / "residuos_vs_ajustados.png"
    _guardar(fig, rutas["ajustados"])

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(df.secuencia, r, marker="o", color="gray", lw=0.8)
    ax.scatter(df.secuencia, r, c=color, zorder=3)
    ax.axhline(0, color="gray", lw=1)
    ax.axvline(8.5, color="black", ls="--", lw=0.8)
    ax.set(title="Residuos frente al orden de ejecución", xlabel="Secuencia (1-8 dia_1, 9-16 dia_2)", ylabel="Residuo (s)")
    rutas["orden"] = carpeta / "residuos_vs_orden.png"
    _guardar(fig, rutas["orden"])

    fig, axs = plt.subplots(1, 3, figsize=(10, 3.6), sharey=True)
    datos_principales = {}
    for ax, (x, (col, bajo, alto)) in zip(axs, FACTORES.items()):
        medias = [df.tiempo_s[df[x] == -1].mean(), df.tiempo_s[df[x] == 1].mean()]
        datos_principales[col] = medias
        ax.plot([str(bajo), str(alto)], medias, marker="o")
        ax.axhline(df.tiempo_s.mean(), color="gray", ls=":", lw=1)
        ax.set(title=col, xlabel="nivel")
    axs[0].set_ylabel("tiempo_s medio (s)")
    fig.suptitle("Efectos principales (8 corridas por nivel)")
    rutas["principales"] = carpeta / "efectos_principales.png"
    _guardar(fig, rutas["principales"])

    fig, axs = plt.subplots(1, 4, figsize=(14, 3.6), sharey=True)
    datos_interaccion = {}
    pares = list(itertools.combinations(FACTORES, 2))
    for ax, (xa, xb) in zip(axs, pares):
        (ca, ba, aa), (cb, bb, ab) = FACTORES[xa], FACTORES[xb]
        for nivel, etiqueta in ((-1, bb), (1, ab)):
            medias = [df.tiempo_s[(df[xa] == s) & (df[xb] == nivel)].mean() for s in (-1, 1)]
            datos_interaccion[f"{ca}x{cb}|{cb}={etiqueta}"] = medias
            ax.plot([str(ba), str(aa)], medias, marker="o", label=f"{cb}={etiqueta}")
        ax.set(title=f"{ca} x {cb}", xlabel=ca)
        ax.legend(fontsize=8)
    ax = axs[3]
    for nivel_f, est in ((-1, "-"), (1, "--")):
        for nivel_b, marca in ((-1, "o"), (1, "s")):
            medias = [df.tiempo_s[(df.x_proc == s) & (df.x_anal == nivel_b) & (df.x_form == nivel_f)].mean() for s in (-1, 1)]
            etiqueta = f"{FACTORES['x_anal'][1 if nivel_b < 0 else 2]}/{FACTORES['x_form'][1 if nivel_f < 0 else 2]}"
            datos_interaccion[f"ABC|{etiqueta}"] = medias
            ax.plot(["1", "4"], medias, ls=est, marker=marca, label=etiqueta)
    ax.set(title="ABC: procesos por analizador/formato", xlabel="procesos")
    ax.legend(fontsize=7)
    axs[0].set_ylabel("tiempo_s medio (s)")
    fig.suptitle("Gráficas de interacción (medias de celda)")
    rutas["interacciones"] = carpeta / "interacciones.png"
    _guardar(fig, rutas["interacciones"])
    rutas_datos = carpeta / "datos_figuras.json"
    rutas_datos.write_bytes((json.dumps({"principales": datos_principales, "interacciones": datos_interaccion},
                                        indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    rutas["datos"] = rutas_datos
    return rutas


# ---------------------------------------------------------------- ejecución completa
def analizar(entrada: Path = ENTRADA, salida: Path = SALIDA, n_perm: int = N_PERMUTACIONES) -> dict:
    df = cargar(entrada)
    modelo = ajustar(df)
    X = modelo.model.exog
    tabla, ef, medias = tabla_anova(modelo), efectos(df, modelo), medias_tratamiento(df, modelo)
    sup = supuestos(df, modelo)
    perm = prueba_permutacion(df, n_perm)
    sens = sensibilidad(df)
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)

    def csv(d: pd.DataFrame, nombre: str, index: bool):
        (salida / nombre).write_bytes(d.round(6).to_csv(index=index, lineterminator="\n").encode("utf-8"))
    csv(tabla, "anova.csv", True)
    csv(ef, "efectos.csv", False)
    csv(medias, "medias_tratamiento.csv", False)
    csv(sens, "sensibilidad.csv", True)
    csv(df.assign(ajustado=modelo.fittedvalues, residuo=modelo.resid), "residuos.csv", False)
    rutas = figuras(df, modelo, salida / "figuras")
    resumen = {
        "entrada": entrada.name, "sha256_entrada": sha256(entrada), "n": len(df), "formula": FORMULA,
        "rango_matriz": int(np.linalg.matrix_rank(X)), "columnas_matriz": int(X.shape[1]),
        "gl_residuo": int(modelo.df_resid), "cme": float(modelo.mse_resid), "r2": float(modelo.rsquared),
        "media_global_s": float(df.tiempo_s.mean()), "alfa": ALFA,
        "tasa_error_todas_las_corridas": sorted(set(df.tasa_error.tolist())),
        "supuestos": sup, "permutacion": perm, "efecto_minimo_detectable": efecto_minimo_detectable(modelo),
        "modelo_reducido_post_hoc": modelo_reducido(df), "componentes_exploratorio": componentes(df),
        "figuras": sorted(p.name for p in rutas.values()),
    }
    (salida / "resumen.json").write_bytes((json.dumps(resumen, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    return {"datos": df, "modelo": modelo, "tabla": tabla, "efectos": ef, "medias": medias, "resumen": resumen,
            "sensibilidad": sens}


def main(argv=None) -> int:
    r = analizar()
    pd.set_option("display.width", 160)
    print(r["tabla"].round(4).to_string())
    print(r["efectos"].round(3).to_string(index=False))
    print(json.dumps({k: r["resumen"][k] for k in ("sha256_entrada", "rango_matriz", "gl_residuo", "cme", "r2")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
