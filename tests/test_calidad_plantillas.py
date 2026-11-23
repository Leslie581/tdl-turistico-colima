"""Formato y coherencia de los registros PSP de ambos integrantes (no exige que estén vacíos)."""
import csv
import re
from datetime import date
from pathlib import Path

import pytest

CAL = Path(__file__).resolve().parent.parent / "calidad"
KIT_TIEMPO = ["fecha", "inicio", "fin", "interrupcion_min", "fase", "actividad"]
KIT_DEFECTOS = ["numero", "fecha", "tipo", "fase_introducido", "fase_eliminado", "minutos_correccion",
                "defecto_origen", "descripcion"]
TIPOS_PSP = {"documentacion", "sintaxis", "construccion", "asignacion", "interfaz", "verificacion",
             "datos", "funcion", "sistema", "entorno"}


def _leer(nombre):
    with open(CAL / nombre, encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        return r.fieldnames, list(r)


def test_las_plantillas_de_tiempo_de_ambos_son_compatibles_y_conservan_las_columnas_del_kit():
    ha, _ = _leer("tiempo-integrante-a.csv")
    hb, _ = _leer("tiempo-integrante-b.csv")
    assert ha == hb == KIT_TIEMPO + ["minutos_estimados"]


def test_las_plantillas_de_defectos_conservan_las_columnas_del_kit():
    for n in ("a", "b"):
        assert _leer(f"defectos-integrante-{n}.csv")[0] == KIT_DEFECTOS


def test_tiempos_retrospectivos_no_inventan_horarios():
    _, filas = _leer("tiempo-integrante-a.csv")
    retro = [f for f in filas if "RETROSPECTIVO" in f["actividad"] or "PENDIENTE DE CONFIRMACION" in f["actividad"]]
    assert len(retro) == len(filas)  # ningún tiempo de A se cronometró: son estimaciones o están pendientes de confirmación
    for f in retro:
        assert f["inicio"] == f["fin"] == f["interrupcion_min"] == "" and f["fecha"]


BLOQUES_E1 = {"L0": 45, "L1": 165, "L2": 120, "L3": 105, "SEG": 60, "PCI": 90, "RES": 30, "AUD": 120, "DOC": 90, "REL": 45}


def test_tiempos_de_e1_por_bloque_y_suma_coherente():
    """E1 = 870 min en 10 bloques (estimación retrospectiva confirmada por A el 2026-11-14); cada fila lleva su bloque entre paréntesis."""
    _, filas = _leer("tiempo-integrante-a.csv")
    e1 = [f for f in filas if "2026-11-12" <= f["fecha"] <= "2026-11-15"]
    por_bloque = {b: sum(int(f["minutos_estimados"]) for f in e1 if f["actividad"].rstrip().endswith(f"({b})")) for b in BLOQUES_E1}
    assert por_bloque == BLOQUES_E1
    assert sum(por_bloque.values()) == sum(int(f["minutos_estimados"]) for f in e1) == 870
    assert len(e1) > 30  # el detalle de las actividades se conserva (no se reduce a diez filas)


def test_totales_de_a_separan_prototipo_de_desarrollo_formal():
    _, filas = _leer("tiempo-integrante-a.csv")
    def suma(fs):
        return sum(int(f["minutos_estimados"] or 0) for f in fs)
    e2 = [f for f in filas if f["fecha"] >= "2026-11-22"]
    filas_e1 = [f for f in filas if f["fecha"] <= "2026-11-15"]
    filas = filas_e1
    proto = [f for f in filas if "[PROTOTIPO]" in f["actividad"]]
    e0 = [f for f in filas if f["fecha"] < "2026-11-12"]
    _, mejoras = _leer("tiempo-mejoras-e1-integrante-a.csv")
    assert suma(mejoras) == 90 and all("(MEJ)" in f["actividad"] for f in mejoras)
    assert (suma(proto), suma(e0), suma(filas), suma(filas) - suma(proto)) == (480, 750, 1620, 1140)  # sin las mejoras de E1
    assert (suma(filas) + suma(mejoras), suma(filas) + suma(mejoras) - suma(proto), suma(filas) - suma(e0) + suma(mejoras)) == (1710, 1230, 960)
    # E2: 90 min estimados retrospectivamente por A para el trabajo geoespacial; las demás filas esperan confirmación (sin minutos)
    geo = [f for f in e2 if "(GEO)" in f["actividad"]]
    assert suma(geo) == 90 and len(geo) == 5 and all("ESTIMADO RETROSPECTIVO POR LESLIE" in f["actividad"] for f in geo)
    iso = [f for f in e2 if "(ISO)" in f["actividad"]]
    assert [int(f["minutos_estimados"]) for f in iso] == [35, 35, 25, 25] and all("ESTIMADO RETROSPECTIVO POR LESLIE" in f["actividad"] for f in iso)
    assert suma(iso) == 120 and suma(e2) == 323                       # Calidad 120 + geoespacial 90 + integración 45 + comparación de capturas 15 + O1 35 + validación e indicador posterior 18
    cap = [f for f in e2 if "(CAP)" in f["actividad"]]
    assert len(cap) == 1 and suma(cap) == 15 and "ESTIMADO RETROSPECTIVO POR LESLIE" in cap[0]["actividad"]
    assert not [f for f in e2 if "PENDIENTE DE CONFIRMACION" in f["actividad"]]
    o1 = [f for f in e2 if "(O1)" in f["actividad"]]
    assert len(o1) == 1 and suma(o1) == 35 and "ESTIMADO RETROSPECTIVO POR LESLIE" in o1[0]["actividad"]   # aportaciones ISO 25010 de Eimy y revisión de O1
    val = [f for f in e2 if "(VAL)" in f["actividad"]]
    assert len(val) == 1 and suma(val) == 18 and "ESTIMADO RETROSPECTIVO POR LESLIE" in val[0]["actividad"]   # validación previa e indicador posterior de O1
    integ = [f for f in e2 if "(INT)" in f["actividad"]]
    assert len(integ) == 1 and suma(integ) == 45 and "ESTIMADO RETROSPECTIVO POR LESLIE" in integ[0]["actividad"]   # integración de ISO 25010 con Estadística
    assert suma(filas) + suma(mejoras) + suma(e2) == 2033


def test_el_registro_de_mejoras_no_duplica_tiempo_del_principal():
    _, principal = _leer("tiempo-integrante-a.csv")
    _, mejoras = _leer("tiempo-mejoras-e1-integrante-a.csv")
    claves = {(f["fecha"], f["actividad"]) for f in principal}
    assert not [f for f in mejoras if (f["fecha"], f["actividad"]) in claves]


def test_defectos_a_usan_tipos_psp_y_no_inventan_minutos():
    _, filas = _leer("defectos-integrante-a.csv")
    assert filas and all(f["tipo"] in TIPOS_PSP for f in filas)
    # minutos_correccion: estimaciones retrospectivas (no mediciones); cada fila lo declara en su descripción
    e1 = [f for f in filas if int(f["numero"]) <= 28]
    assert all(f["minutos_correccion"].isdigit() and "estimacion retrospectiva" in f["descripcion"] for f in e1)
    assert sum(int(f["minutos_correccion"]) for f in e1) == 440
    assert all(f["minutos_correccion"] == "" for f in filas if int(f["numero"]) > 28)   # E2: observados, sin minutos medidos ("no registrado")
    assert not any("duplicad" in f["descripcion"].lower() and "fecha" in f["descripcion"].lower() for f in filas)
    assert not any("manova" in f["descripcion"].lower() for f in filas)  # MANOVA es riesgo, no defecto


FASES = {"planeacion", "diseno", "codigo", "revision", "pruebas", "documentacion", "entrevista"}
HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


@pytest.mark.parametrize("nombre", ["a", "b"])
def test_registros_de_tiempo_tienen_formato_y_coherencia(nombre):
    """Valida estructura, no contenido: las filas retrospectivas no inventan horario; las medidas lo tienen completo."""
    _, filas = _leer(f"tiempo-integrante-{nombre}.csv")
    for f in filas:
        date.fromisoformat(f["fecha"])                      # fecha ISO válida
        assert f["fase"] in FASES and f["actividad"].strip()
        if "PENDIENTE DE CONFIRMACION" in f["actividad"]:   # actividad registrada, tiempo aún no confirmado: sin horarios ni minutos
            assert f["inicio"] == f["fin"] == f["interrupcion_min"] == f["minutos_estimados"] == ""
        elif "RETROSPECTIVO" in f["actividad"]:             # estimación: sin horarios, con minutos > 0
            assert f["inicio"] == f["fin"] == f["interrupcion_min"] == ""
            assert int(f["minutos_estimados"]) > 0
        else:                                               # medida: horario real y sin minutos estimados
            assert HORA.match(f["inicio"]) and HORA.match(f["fin"]) and f["minutos_estimados"] == ""
            assert f["interrupcion_min"].isdigit() or f["interrupcion_min"] == ""


@pytest.mark.parametrize("nombre", ["a", "b"])
def test_registros_de_defectos_tienen_formato_y_coherencia(nombre):
    """Cero defectos es válido (archivo solo con encabezado); si hay filas, deben ser coherentes."""
    _, filas = _leer(f"defectos-integrante-{nombre}.csv")
    assert [int(f["numero"]) for f in filas] == list(range(1, len(filas) + 1))
    for f in filas:
        date.fromisoformat(f["fecha"]) if f["fecha"] else None
        assert f["tipo"] in TIPOS_PSP and f["descripcion"].strip()
        assert f["fase_introducido"] in FASES
        assert f["fase_eliminado"] in FASES | {""}
        assert f["minutos_correccion"] == "" or int(f["minutos_correccion"]) > 0


def test_b_conserva_sus_registros_propios_sin_horarios_inventados():
    """B puede tener registros (ya no se exige que estén vacíos); sus estimaciones siguen sin horario."""
    _, filas = _leer("tiempo-integrante-b.csv")
    for f in filas:
        if "RETROSPECTIVO" in f["actividad"]:
            assert f["inicio"] == f["fin"] == ""


def test_defectos_de_a_tienen_numeracion_continua_y_sin_duplicados():
    _, filas = _leer("defectos-integrante-a.csv")
    assert [int(f["numero"]) for f in filas] == list(range(1, len(filas) + 1)) and len(filas) == 33
    assert len({f["descripcion"] for f in filas}) == len(filas)
