"""Arnés del experimento factorial 2^3 de E2 (ruta ingeniería): ejecuta y mide la matriz de ``matriz.py``.

    python -m laboratorio.experimento.arnes --bloque dia_1            # corridas oficiales de un bloque
    python -m laboratorio.experimento.arnes --bloque dia_1 --piloto --salida <ruta fuera del repo> --copias 2

Qué se mide (unidad experimental = una corrida sobre la carga completa)
  Tarea: el tramo bronce -> plata del DENUE del pipeline real (``pipeline.plata_denue.procesar_una_captura``: integridad
  por SHA-256, privacidad R-E05, esquema R-E01, completitud R-E02, reglas por registro y transformación a columnas de
  plata), seguido de escribir la plata en el formato elegido y volver a leerla.
  Factores (cambian de verdad el procesamiento, no solo una etiqueta):
    A procesos   1 = secuencial en el proceso principal | 4 = ``ProcessPoolExecutor`` con 4 trabajadores (``spawn``)
    B analizador json = ``json.loads`` de la biblioteca estándar | orjson = ``orjson.loads``
    C formato    csv = ``DataFrame.to_csv`` / ``read_csv`` | parquet = ``to_parquet`` / ``read_parquet`` (pyarrow)
  Respuesta principal: ``tiempo_s`` = segundos de pared (``time.perf_counter``) de procesar + escribir + leer.
  Respuesta secundaria: ``tasa_error`` = capturas con error / capturas de la carga. Una captura es un error si (PUERTA) la
  puerta de calidad rechaza el lote, (EXCEPCION) su procesamiento lanza una excepción no prevista o (SALIDA) sus filas no se
  recuperan idénticas al leer el archivo de salida. Los registros que una regla manda a cuarentena NO son errores de
  procesamiento (son calidad del dato) y se informan aparte en ``registros_en_cuarentena``.

Carga de trabajo: copias byte a byte de las capturas reales de ``data/bronce/denue`` (con sus fichas) en un directorio
temporal FUERA del repositorio; ``copias`` multiplica el volumen para que el tiempo sea medible. Es una carga sintética
de rendimiento (los datos se repiten): no se usa como dato analítico ni llega a plata u oro. El bronce original solo se
lee, y su hash se comprueba antes y después de cada bloque. No hay ninguna conexión de red.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as md
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from multiprocessing import get_context
from pathlib import Path

import pandas as pd

from laboratorio.experimento.matriz import BLOQUES, SEMILLA, matriz
from pipeline import plata_denue
from pipeline.calidad.cuarentena import Cuarentena, ErrorPuertaCalidad
from pipeline.config import rutas

VERSION_ARNES = "1.0.0"
RAIZ = Path(__file__).resolve().parents[2]
BRONCE_DENUE = rutas(RAIZ)["bronce_denue"]
SALIDA = Path(__file__).resolve().parent / "resultados" / "corridas_2x3.jsonl"
COPIAS = 16                     # volumen fijado con el piloto del 2026-11-21 (docs/E2/experimento_2x3.md §6); no cambia entre corridas
BOM = b"\xef\xbb\xbf"
FORMATOS = ("csv", "parquet")
PROCESOS = (1, 4)


# ---------------------------------------------------------------- factor B: analizador
def analizar_orjson(contenido: bytes):
    import orjson                                       # import diferido: sin orjson, solo fallan las corridas que lo usan
    return orjson.loads(contenido[3:] if contenido.startswith(BOM) else contenido)


ANALIZADORES = {"json": plata_denue.analizar_json, "orjson": analizar_orjson}


# ---------------------------------------------------------------- carga de trabajo
def sha256_archivo(ruta: Path) -> str:
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def huella_bronce(bronce: Path = BRONCE_DENUE) -> str:
    """Hash de todos los archivos del bronce (nombre relativo + contenido): detecta cualquier cambio en los originales."""
    h = hashlib.sha256()
    for p in sorted(Path(bronce).rglob("*")):
        if p.is_file():
            h.update(p.relative_to(bronce).as_posix().encode() + b"\0" + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def preparar_carga(destino: Path, copias: int = COPIAS, bronce: Path = BRONCE_DENUE, fallos: int = 0) -> dict:
    """Copia las capturas reales ``copias`` veces en ``destino``. Devuelve el manifiesto de la carga.

    ``fallos`` > 0 trunca a propósito esa cantidad de capturas copiadas (fallo SINTÉTICO declarado en el manifiesto) para
    comprobar que el arnés cuenta los errores; las corridas oficiales usan 0.
    """
    if copias < 1:
        raise ValueError("copias debe ser >= 1")
    destino, bronce = Path(destino), Path(bronce)
    if RAIZ in destino.resolve().parents or destino.resolve() == RAIZ:
        raise ValueError("la carga se prepara fuera del repositorio para no tocar datos versionados")
    fuentes = plata_denue.listar_capturas(bronce)
    if not fuentes:
        raise ValueError(f"no hay capturas DENUE en {bronce}")
    archivos = []
    for k in range(1, copias + 1):
        for f in fuentes:
            hermanos = [f, Path(str(f) + ".meta.json")]
            cuant = Path(str(f).replace("_02_BuscarAreaAct.json", "_01_Cuantificar.json"))
            hermanos += [p for p in (cuant, Path(str(cuant) + ".meta.json")) if p.is_file()]
            dia = destino / f"copia_{k:03d}" / f.parent.name
            dia.mkdir(parents=True, exist_ok=True)
            for p in hermanos:
                shutil.copyfile(p, dia / p.name)
            archivos.append(dia / f.name)
    for p in archivos[:fallos]:                            # fallo sintético: el hash deja de coincidir con la ficha
        p.write_bytes(p.read_bytes()[: max(1, p.stat().st_size // 2)])
    origen = sorted((f.relative_to(bronce).as_posix(), sha256_archivo(f)) for f in fuentes)
    return {
        "tipo_carga": "copias_byte_a_byte_del_bronce_real_denue (carga sintética de rendimiento)",
        "copias": copias, "capturas_fuente": len(fuentes), "capturas_en_carga": len(archivos),
        "bytes_capturas": sum(p.stat().st_size for p in archivos),
        "sha256_capturas_fuente": hashlib.sha256("|".join(f"{n}:{h}" for n, h in origen).encode()).hexdigest(),
        "primera_captura": origen[0][0], "ultima_captura": origen[-1][0],
        "fallos_sinteticos_inyectados": int(fallos), "raiz": destino, "archivos": archivos,
    }


# ---------------------------------------------------------------- factor A: una captura por tarea
def procesar_archivo(tarea: tuple[str, str, str]) -> dict:
    """Trabajo de UNA captura (se ejecuta en el proceso principal o en un trabajador). Nunca lanza: devuelve el estado."""
    ruta, raiz, analizador = tarea
    base = {"archivo": Path(ruta).relative_to(raiz).as_posix(), "pid": os.getpid()}
    c = Cuarentena("experimento")
    try:
        out = plata_denue.procesar_una_captura(Path(ruta), Path(raiz), c, ANALIZADORES[analizador])
    except ErrorPuertaCalidad as e:
        return {**base, "estado": "error", "tipo": "PUERTA", "regla": e.regla, "mensaje": e.mensaje[:300]}
    except Exception as e:                                  # noqa: BLE001 - se registra, no se oculta
        return {**base, "estado": "error", "tipo": "EXCEPCION", "regla": type(e).__name__, "mensaje": str(e)[:300]}
    if out is None:
        lote = c.lotes_rechazados[-1] if c.lotes_rechazados else {}
        return {**base, "estado": "error", "tipo": "PUERTA", "regla": lote.get("regla_id", "?"), "mensaje": lote.get("motivo", "")[:300]}
    rechazados = sum(v["rechazados"] for v in c.resumen()["fuentes"].values())
    return {**base, "estado": "ok", "filas": out, "registros_en_cuarentena": rechazados}


def _procesar_todo(tareas: list, procesos: int) -> list[dict]:
    if procesos == 1:
        return [procesar_archivo(t) for t in tareas]
    trozo = max(1, math.ceil(len(tareas) / (procesos * 4)))
    with ProcessPoolExecutor(max_workers=procesos, mp_context=get_context("spawn")) as ex:
        return list(ex.map(procesar_archivo, tareas, chunksize=trozo))


# ---------------------------------------------------------------- factor C: formato de salida
def escribir_salida(df: pd.DataFrame, formato: str, carpeta: Path) -> Path:
    ruta = Path(carpeta) / f"plata_experimento.{formato}"
    if formato == "csv":
        df.to_csv(ruta, index=False, lineterminator="\n")
    elif formato == "parquet":
        df.to_parquet(ruta, index=False, engine="pyarrow")
    else:
        raise ValueError(f"formato desconocido: {formato}")
    return ruta


def leer_salida(ruta: Path, formato: str) -> pd.DataFrame:
    if formato == "csv":
        return pd.read_csv(ruta, dtype=str, keep_default_na=False)
    return pd.read_parquet(ruta, engine="pyarrow")


def _canonica(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    return df[columnas].astype("string").fillna("").reset_index(drop=True)


def archivos_no_recuperados(original: pd.DataFrame, leida: pd.DataFrame) -> set[str]:
    """SALIDA: capturas (``archivo_bronce``) cuyas filas no se leen idénticas a las escritas."""
    columnas = list(original.columns)
    if len(original) != len(leida) or list(leida.columns) != columnas:
        return set(original["archivo_bronce"])
    a, b = _canonica(original, columnas), _canonica(leida, columnas)
    distintas = (a != b).any(axis=1)
    return set(a.loc[distintas, "archivo_bronce"])


# ---------------------------------------------------------------- una corrida
def ejecutar_corrida(carga: dict, procesos: int, analizador: str, formato: str, trabajo: Path) -> dict:
    """Ejecuta un tratamiento sobre la carga y devuelve sus mediciones. Un fallo se registra, nunca se rellena."""
    if procesos not in PROCESOS or analizador not in ANALIZADORES or formato not in FORMATOS:
        raise ValueError(f"nivel fuera del diseño: {procesos}, {analizador}, {formato}")
    raiz = str(carga["raiz"])
    tareas = [(str(p), raiz, analizador) for p in carga["archivos"]]
    rec: dict = {"estado": "fallo", "tiempo_s": None, "tasa_error": None}
    inicio = datetime.now(timezone.utc)
    try:
        t0 = time.perf_counter()
        res = _procesar_todo(tareas, procesos)
        t1 = time.perf_counter()
        ok = [r for r in res if r["estado"] == "ok"]
        if ok:
            df = pd.concat([r["filas"] for r in ok], ignore_index=True)
            for c in ("personal_min", "personal_max"):
                df[c] = df[c].astype("Int64")
        else:
            df = pd.DataFrame(columns=[*plata_denue.COLUMNAS_PLATA, "_capturado_utc"])
        Path(trabajo).mkdir(parents=True, exist_ok=True)
        salida = escribir_salida(df, formato, trabajo)
        t2 = time.perf_counter()
        leida = leer_salida(salida, formato)
        t3 = time.perf_counter()
        perdidos = archivos_no_recuperados(df, leida) if len(df) else set()
        t4 = time.perf_counter()
        errores = [{k: r[k] for k in ("archivo", "tipo", "regla", "mensaje")} for r in res if r["estado"] == "error"]
        errores += [{"archivo": a, "tipo": "SALIDA", "regla": "RELECTURA", "mensaje": "filas distintas al releer la salida"}
                    for a in sorted(perdidos)]
        con_error = len({e["archivo"] for e in errores if e["tipo"] != "SALIDA"}) + len(perdidos)
        cabecera = salida.read_bytes()[:4]
        rec.update({
            "estado": "ok", "tiempo_s": round(t3 - t0, 6),
            "tiempo_procesamiento_s": round(t1 - t0, 6), "tiempo_escritura_s": round(t2 - t1, 6),
            "tiempo_lectura_s": round(t3 - t2, 6), "tiempo_verificacion_s": round(t4 - t3, 6),
            "capturas": len(tareas), "capturas_con_error": con_error, "tasa_error": round(con_error / len(tareas), 6),
            "registros_salida": int(len(df)), "registros_en_cuarentena": int(sum(r["registros_en_cuarentena"] for r in ok)),
            "errores": errores[:50], "errores_omitidos": max(0, len(errores) - 50),
            "evidencia_factores": {
                "pids_distintos": len({r["pid"] for r in res}), "pid_principal": os.getpid(),
                "trabajo_fuera_del_proceso_principal": any(r["pid"] != os.getpid() for r in res),
                "analizador": f"{ANALIZADORES[analizador].__module__}.{ANALIZADORES[analizador].__name__}",
                "bytes_salida": salida.stat().st_size, "cabecera_salida": cabecera.hex(),
                "es_parquet": cabecera == b"PAR1",
            },
        })
    except Exception as e:                                  # noqa: BLE001 - la corrida se registra como fallida
        rec.update({"error_corrida": f"{type(e).__name__}: {e}"[:500], "traza": traceback.format_exc()[-1500:]})
    rec["inicio_utc"] = inicio.isoformat(timespec="seconds")
    rec["fin_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return rec


# ---------------------------------------------------------------- entorno y versión de código
def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, timeout=30, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def codigo_modificado(excluir: Path | None = None) -> bool | None:
    """True si hay cambios sin confirmar en el código (se ignora el propio archivo de resultados). None si no hay git."""
    estado = _git("status", "--porcelain")
    if not _git("rev-parse", "HEAD"):
        return None
    ignorar = excluir.resolve().relative_to(RAIZ).as_posix() if excluir and RAIZ in excluir.resolve().parents else None
    return any(linea[3:].strip() != ignorar for linea in estado.splitlines() if linea.strip())


def entorno() -> dict:
    def version(paquete: str) -> str | None:
        try:
            return md.version(paquete)
        except md.PackageNotFoundError:
            return None
    return {
        "python": platform.python_version(), "implementacion": platform.python_implementation(),
        "sistema": platform.platform(), "arquitectura": platform.machine(), "cpu_logicas": os.cpu_count(),
        "equipo_id": hashlib.sha256(platform.node().encode()).hexdigest()[:12],   # identifica la máquina sin publicar su nombre
        "bibliotecas": {p: version(p) for p in ("pandas", "numpy", "pyarrow", "orjson", "pandera")},
    }


# ---------------------------------------------------------------- un bloque completo
def leer_registros(ruta: Path) -> list[dict]:
    ruta = Path(ruta)
    if not ruta.is_file():
        return []
    return [json.loads(x) for x in ruta.read_text(encoding="utf-8").splitlines() if x.strip()]


def ejecutar_bloque(bloque: str, salida: Path = SALIDA, copias: int = COPIAS, semilla: int = SEMILLA,
                    bronce: Path = BRONCE_DENUE, piloto: bool = False, permitir_cambios: bool = False,
                    calentamiento: bool = True, fallos: int = 0, solo: list[int] | None = None) -> list[dict]:
    """Corre, en el orden aleatorizado de la matriz, los tratamientos del bloque que aún no tienen registro en ``salida``.

    Cada corrida se agrega a ``salida`` (JSON Lines) en cuanto termina. Las corridas oficiales exigen el código confirmado
    en git (``codigo_modificado`` falso), cero fallos sintéticos y el archivo de resultados del repositorio; un piloto se
    marca como tal y debe escribirse fuera del archivo oficial.
    """
    if bloque not in BLOQUES:
        raise ValueError(f"bloque desconocido: {bloque} (válidos: {BLOQUES})")
    salida = Path(salida)
    oficial = salida.resolve() == SALIDA.resolve()
    if piloto and oficial:
        raise ValueError("un piloto no se escribe en el archivo oficial de resultados")
    modificado = codigo_modificado(salida)
    if not piloto and (fallos or (modificado is not False and not permitir_cambios)):
        raise RuntimeError("corrida oficial: confirme el código en git (o use --piloto) y no inyecte fallos")
    plan = matriz(semilla)
    plan = plan[plan.bloque == bloque].sort_values("corrida")
    if solo:
        plan = plan[plan.tratamiento.isin(solo)]
    hechos = {(r["bloque"], r["tratamiento"]) for r in leer_registros(salida) if r.get("semilla") == semilla}
    plan = plan[[(bloque, int(t)) not in hechos for t in plan.tratamiento]]
    if plan.empty:
        return []
    comun = {"version_arnes": VERSION_ARNES, "semilla": semilla, "commit": _git("rev-parse", "HEAD") or None,
             "codigo_modificado": modificado, "piloto": bool(piloto), "entorno": entorno()}
    huella_antes = huella_bronce(bronce)
    salida.parent.mkdir(parents=True, exist_ok=True)
    hechos_ahora = []
    with tempfile.TemporaryDirectory(prefix="tdl_e2_") as tmp:
        carga = preparar_carga(Path(tmp) / "carga", copias, bronce, fallos)
        manifiesto = {k: v for k, v in carga.items() if k not in ("raiz", "archivos")}
        if calentamiento:                                   # no se registra: absorbe importaciones y cachés del primer uso
            ejecutar_corrida(carga, 1, "json", "csv", Path(tmp) / "calentamiento")
        for _, fila in plan.iterrows():
            niveles = {"procesos": int(fila.procesos), "analizador": str(fila.analizador), "formato": str(fila.formato)}
            rec = ejecutar_corrida(carga, **niveles, trabajo=Path(tmp) / f"t{int(fila.tratamiento)}")
            rec = {"bloque": bloque, "replica": BLOQUES.index(bloque) + 1, "orden_en_bloque": int(fila.corrida),
                   "tratamiento": int(fila.tratamiento), **niveles,
                   **{f"{n}_cod": int(fila[f"{n}_cod"]) for n in niveles},
                   "fecha_local": datetime.now().astimezone().date().isoformat(), **rec, **comun,
                   "carga": manifiesto, "calentamiento_previo": bool(calentamiento)}
            with salida.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
            hechos_ahora.append(rec)
            shutil.rmtree(Path(tmp) / f"t{int(fila.tratamiento)}", ignore_errors=True)
    huella_despues = huella_bronce(bronce)
    if huella_antes != huella_despues:
        raise RuntimeError("el bronce original cambió durante el bloque: las corridas no son válidas")
    return hechos_ahora


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Arnés del experimento 2^3 de E2 (copia local; sin red)")
    ap.add_argument("--bloque", required=True, choices=BLOQUES)
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--copias", type=int, default=COPIAS)
    ap.add_argument("--semilla", type=int, default=SEMILLA)
    ap.add_argument("--piloto", action="store_true", help="corrida de prueba: se marca y no va al archivo oficial")
    ap.add_argument("--permitir-cambios", action="store_true", help="admite código sin confirmar (queda registrado)")
    ap.add_argument("--sin-calentamiento", action="store_true")
    ap.add_argument("--fallos", type=int, default=0, help="capturas truncadas a propósito (solo piloto)")
    ap.add_argument("--tratamientos", type=int, nargs="*", help="subconjunto de tratamientos (1-8)")
    a = ap.parse_args(argv)
    hechas = ejecutar_bloque(a.bloque, Path(a.salida), a.copias, a.semilla, piloto=a.piloto,
                             permitir_cambios=a.permitir_cambios, calentamiento=not a.sin_calentamiento,
                             fallos=a.fallos, solo=a.tratamientos)
    for r in hechas:
        print(f"{r['bloque']} #{r['orden_en_bloque']} T{r['tratamiento']} {r['procesos']}/{r['analizador']}/{r['formato']}: "
              f"{r['estado']} tiempo_s={r['tiempo_s']} tasa_error={r['tasa_error']}")
    print(f"{len(hechas)} corridas nuevas en {a.salida}")
    return 0 if all(r["estado"] == "ok" for r in hechas) else 1


if __name__ == "__main__":
    sys.exit(main())
