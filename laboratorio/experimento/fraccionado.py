"""Matrices TEÓRICAS 2^4 (completa) y 2^(4-1) (fracción con D = ABC) para comparar diseños de E2.

    python -m laboratorio.experimento.fraccionado      # escribe resultados/matriz_2a4_completa.csv y matriz_2a4-1_fraccion.csv

No contienen mediciones: son planes de corrida (docs/E2/diseno_completo_fraccionado.md). Los factores A, B y C son los del
2^3; D es la segunda validación pandera de la plata (R-E07, ``reglas.validar_plata``), que el arnés actual no ejecuta
(las corridas del 2^3 equivalen a D = -1). Ejecutar D = +1 requeriría ampliar el arnés; no se hace aquí.
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

FACTORES = {"A": ("procesos", 1, 4), "B": ("analizador", "json", "orjson"), "C": ("formato", "csv", "parquet"),
            "D": ("validacion_r_e07", "desactivada", "activada")}
LETRAS = tuple(FACTORES)
GENERADOR = ("D", "ABC")
DEFINIDORA = "ABCD"                 # I = ABCD (fracción principal: A·B·C·D = +1)
SEMILLA_ORDEN = 20261125            # orden aleatorio sugerido si algún día se ejecutan
CARPETA = Path(__file__).resolve().parent / "resultados"
COMPLETA = CARPETA / "matriz_2a4_completa.csv"
FRACCION = CARPETA / "matriz_2a4-1_fraccion.csv"


def efectos() -> list[str]:
    """Los 15 efectos factoriales de 2^4: A, B, ..., AB, ..., ABCD."""
    return ["".join(c) for k in range(1, 5) for c in itertools.combinations(LETRAS, k)]


def producto(*palabras: str) -> str:
    """Producto de palabras con x^2 = I (diferencia simétrica de letras). 'I' o '' es la identidad."""
    letras: set[str] = set()
    for p in palabras:
        letras ^= set(p.replace("I", ""))
    return "".join(sorted(letras)) or "I"


def contraste(df: pd.DataFrame, efecto: str) -> np.ndarray:
    return np.prod([df[x].to_numpy() for x in efecto], axis=0)


def _con_niveles(df: pd.DataFrame, semilla: int) -> pd.DataFrame:
    for x, (nombre, bajo, alto) in FACTORES.items():
        df[nombre] = np.where(df[x] == 1, alto, bajo)
    df["orden_aleatorio_sugerido"] = np.random.default_rng(semilla).permutation(len(df)) + 1
    df["mediciones"] = "ninguna (matriz teórica)"
    return df


def completa(semilla: int = SEMILLA_ORDEN) -> pd.DataFrame:
    """2^4 en orden estándar (A cambia más rápido): 16 tratamientos, codificación -1/+1."""
    filas = [dict(zip(LETRAS, reversed(v))) for v in itertools.product((-1, 1), repeat=4)]
    df = pd.DataFrame(filas)[list(LETRAS)]
    df.insert(0, "corrida_estandar", range(1, 17))
    return _con_niveles(df, semilla)


def fraccion(semilla: int = SEMILLA_ORDEN) -> pd.DataFrame:
    """2^(4-1): 2^3 completo en A, B, C y D = ABC (generador), es decir, I = ABCD. 8 tratamientos."""
    filas = [dict(zip("ABC", reversed(v))) for v in itertools.product((-1, 1), repeat=3)]
    df = pd.DataFrame(filas)
    df["D"] = df.A * df.B * df.C
    df.insert(0, "corrida_estandar", range(1, 9))
    return _con_niveles(df, semilla)


def alias(efecto: str, definidora: str = DEFINIDORA) -> str:
    return producto(efecto, definidora)


def estructura_alias(definidora: str = DEFINIDORA) -> dict[str, str]:
    """Cada efecto con su alias (pares; ABCD queda confundido con la media I)."""
    return {e: alias(e, definidora) for e in efectos()}


def resolucion(definidora: str = DEFINIDORA) -> int:
    """Longitud de la palabra más corta de la relación definidora (aquí una sola palabra)."""
    return min(len(p) for p in definidora.split("="))


def resumen() -> dict:
    c, f = completa(), fraccion()
    return {"corridas_completa": len(c), "corridas_fraccion": len(f), "ahorro_corridas": len(c) - len(f),
            "ahorro_pct": 100 * (len(c) - len(f)) / len(c), "generador": f"{GENERADOR[0]} = {GENERADOR[1]}",
            "definidora": f"I = {DEFINIDORA}", "resolucion": resolucion(),
            "alias": {e: a for e, a in estructura_alias().items()
                      if a == "I" or (len(e), e) < (len(a), a)}}                # cada par una vez, el efecto corto primero


def escribir(semilla: int = SEMILLA_ORDEN) -> tuple[Path, Path]:
    CARPETA.mkdir(parents=True, exist_ok=True)
    completa(semilla).to_csv(COMPLETA, index=False, lineterminator="\n")
    fraccion(semilla).to_csv(FRACCION, index=False, lineterminator="\n")
    return COMPLETA, FRACCION


def main(argv=None) -> int:
    for p in escribir():
        print(p)
    r = resumen()
    print({k: v for k, v in r.items() if k != "alias"})
    print("alias:", ", ".join(f"{e} = {a}" for e, a in r["alias"].items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
