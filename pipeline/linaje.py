"""Linaje de datos (E2): de cada registro de la capa oro al archivo de origen y a su fecha de captura, con hashes que se pueden volver a calcular.

    python -m pipeline.linaje                      # verifica el linaje de todo el oro y resume
    python -m pipeline.linaje --periodo 2020-04    # cadena de un mes del oro mensual
    python -m pipeline.linaje --ageb 060070001009A # cadena de una AGEB del agregado geoespacial

Cadenas que reconstruye (cada eslabón se verifica contra el archivo real, no contra lo que dice la ficha):
  * oro mensual (``manzanillo_ocupacion_mensual.csv``): fila -> ``sha256_bronce`` y ``ejecucion`` -> ``data/bronce/datatur/Base70centros.csv``.
  * oferta DENUE (``manzanillo_oferta_hospedaje.csv``): fila -> ``fecha_captura_local`` -> archivos ``data/bronce/denue/<fecha>/`` con su SHA-256.
  * oferta por AGEB (``manzanillo_oferta_ageb.csv``): fila -> ``sha256_bronce`` de la captura de referencia, ``sha256_poligonos`` ->
    GeoJSON del Marco Geoestadístico -> SHA-256 del zip oficial de INEGI (en la ficha del GeoJSON).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from .config import RAIZ
from .geoespacial import RUTA_AGEB, sha256_archivo

BASE70 = Path("data") / "bronce" / "datatur" / "Base70centros.csv"
ORO_MENSUAL = Path("data") / "oro" / "manzanillo_ocupacion_mensual.csv"
ORO_OFERTA = Path("data") / "oro" / "manzanillo_oferta_hospedaje.csv"
ORO_AGEB = Path("data") / "oro" / "manzanillo_oferta_ageb.csv"


def _leer(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(ruta, dtype=str, keep_default_na=False)


def archivos_bronce_denue(raiz: Path, fecha: str) -> list[dict]:
    """Archivos de la captura ``fecha`` con su SHA-256 recalculado frente al de su ficha ``.meta.json``."""
    carpeta = Path(raiz) / "data" / "bronce" / "denue" / fecha
    salida = []
    for ficha in sorted(carpeta.glob("*.json.meta.json")):
        meta = json.loads(ficha.read_text(encoding="utf-8"))
        archivo = carpeta / meta["archivo"]
        real = sha256_archivo(archivo) if archivo.is_file() else None
        salida.append({"archivo": archivo.relative_to(raiz).as_posix(), "sha256_ficha": meta["sha256"], "sha256_real": real,
                       "capturado_utc": meta.get("capturado_utc"), "coincide": real == meta["sha256"]})
    return salida


def rastrear_mensual(periodo: str, raiz: Path = RAIZ) -> dict:
    fila = _leer(Path(raiz) / ORO_MENSUAL).set_index("periodo").loc[periodo]
    real = sha256_archivo(Path(raiz) / BASE70)
    return {"oro": ORO_MENSUAL.as_posix(), "periodo": periodo, "ejecucion": fila["ejecucion"], "fuente": "DataTur (SECTUR), Base70centros.csv",
            "bronce": BASE70.as_posix(), "sha256_en_el_oro": fila["sha256_bronce"], "sha256_real": real, "coincide": fila["sha256_bronce"] == real}


def rastrear_ageb(cvegeo: str, raiz: Path = RAIZ) -> dict:
    raiz = Path(raiz)
    fila = _leer(raiz / ORO_AGEB).set_index("cvegeo").loc[cvegeo]
    ruta_poligonos = raiz / RUTA_AGEB.relative_to(RAIZ)
    ficha = json.loads(Path(str(ruta_poligonos) + ".meta.json").read_text(encoding="utf-8"))
    bronce = archivos_bronce_denue(raiz, fila["fecha_referencia"])
    real_poligonos = sha256_archivo(ruta_poligonos)
    return {
        "oro": ORO_AGEB.as_posix(), "cvegeo": cvegeo, "fecha_referencia": fila["fecha_referencia"], "ejecucion": fila["ejecucion"],
        "denue": {"archivos": bronce, "sha256_en_el_oro": fila["sha256_bronce"], "en_la_captura": any(b["sha256_real"] == fila["sha256_bronce"] for b in bronce)},
        "poligonos": {"archivo": RUTA_AGEB.relative_to(RAIZ).as_posix(), "sha256_en_el_oro": fila["sha256_poligonos"], "sha256_real": real_poligonos,
                      "coincide": real_poligonos == fila["sha256_poligonos"], "fuente_zip": ficha["fuente_zip"], "sha256_zip_inegi": ficha["sha256_zip"]},
        "coincide": all(b["coincide"] for b in bronce) and real_poligonos == fila["sha256_poligonos"]
        and any(b["sha256_real"] == fila["sha256_bronce"] for b in bronce),
    }


def verificar_linaje(raiz: Path = RAIZ) -> dict:
    """Recorre todo el oro y devuelve cuántos registros tienen cadena completa y cuáles fallan."""
    raiz = Path(raiz)
    fallas: list[str] = []
    real_base70 = sha256_archivo(raiz / BASE70)
    mensual = _leer(raiz / ORO_MENSUAL)
    for _, f in mensual.iterrows():
        if f["sha256_bronce"] != real_base70:
            fallas.append(f"mensual {f['periodo']}: sha256_bronce no coincide con {BASE70.name}")
    fechas = sorted(_leer(raiz / ORO_OFERTA)["fecha_captura_local"].unique())
    for fecha in fechas:
        b = archivos_bronce_denue(raiz, fecha)
        if not b:
            fallas.append(f"oferta {fecha}: sin archivos de bronce")
        fallas += [f"oferta {fecha}: {x['archivo']} no coincide con su ficha" for x in b if not x["coincide"]]
    ageb = _leer(raiz / ORO_AGEB)
    for cve in ageb["cvegeo"]:
        if not rastrear_ageb(cve, raiz)["coincide"]:
            fallas.append(f"ageb {cve}: cadena rota")
    return {"registros_mensuales": int(len(mensual)), "capturas_de_oferta": len(fechas), "agebs": int(len(ageb)),
            "cadenas_verificadas": int(len(mensual) + len(fechas) + len(ageb) - len(fallas)), "fallas": fallas, "completo": not fallas}


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--periodo")
    ap.add_argument("--ageb")
    a = ap.parse_args(argv)
    if a.periodo:
        r = rastrear_mensual(a.periodo)
    elif a.ageb:
        r = rastrear_ageb(a.ageb)
    else:
        r = verificar_linaje()
    print(json.dumps(r, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if r.get("coincide", r.get("completo", True)) else 1


if __name__ == "__main__":
    sys.exit(main())
