"""ANOVA del experimento 2^3 de E2 (laboratorio/experimento/anova.py) sobre las 16 corridas oficiales versionadas."""
import json

import numpy as np
import pytest

pytest.importorskip("statsmodels")
pytest.importorskip("matplotlib")

from laboratorio.experimento import anova as an  # noqa: E402

SHA_16_CORRIDAS = "f5167a79d47513af879f990207069c1ebabd1aa1a83d85eebd0c46506ff31811"
pytestmark = pytest.mark.skipif(not an.ENTRADA.is_file() or an.sha256(an.ENTRADA) != SHA_16_CORRIDAS,
                                reason="requiere las 16 corridas oficiales confirmadas (7309fed)")


@pytest.fixture(scope="module")
def datos():
    return an.cargar()


@pytest.fixture(scope="module")
def modelo(datos):
    return an.ajustar(datos)


def test_lee_las_16_corridas_oficiales_con_factores_y_bloques_correctos(datos):
    assert len(datos) == 16 and datos.groupby("bloque").size().to_dict() == {"dia_1": 8, "dia_2": 8}
    assert (datos.groupby("tratamiento").size() == 2).all() and not datos.duplicated(["bloque", "tratamiento"]).any()
    assert ((datos.x_proc == 1) == (datos.procesos == 4)).all() and ((datos.x_anal == 1) == (datos.analizador == "orjson")).all()
    assert ((datos.x_form == 1) == (datos.formato == "parquet")).all() and not datos.piloto.any()
    assert datos.secuencia.tolist() == list(range(1, 17))


def test_matriz_de_diseno_de_rango_completo_y_grados_de_libertad(modelo):
    X = modelo.model.exog
    assert X.shape == (16, 9) and np.linalg.matrix_rank(X) == 9
    t = an.tabla_anova(modelo)
    assert t.gl.drop("Total").tolist() == [1, 1, 1, 1, 1, 1, 1, 1, 7] and t.loc["Total", "gl"] == 15
    sct = ((modelo.model.endog - modelo.model.endog.mean()) ** 2).sum()
    assert t.SC.drop("Total").sum() == pytest.approx(sct) and t.loc["Total", "SC"] == pytest.approx(sct)


def test_efectos_y_sumas_de_cuadrados_coinciden_con_el_calculo_de_contrastes(datos, modelo):
    ef = an.efectos(datos, modelo).set_index("termino")
    t = an.tabla_anova(modelo)
    for termino, nombre in zip(an.TERMINOS, ["A procesos", "B analizador", "C formato", "AB", "AC", "BC", "ABC"]):
        c = np.prod([datos[x].to_numpy() for x in termino.split(":")], axis=0)
        efecto = datos.tiempo_s.to_numpy() @ c / 8                       # media(+1) - media(-1)
        assert ef.loc[nombre, "efecto_s"] == pytest.approx(efecto)
        assert t.loc[nombre, "SC"] == pytest.approx(4 * efecto ** 2)     # SC = N * (efecto / 2)^2 con N = 16


def test_el_analisis_es_reproducible_y_no_modifica_los_datos(tmp_path):
    antes = an.sha256(an.ENTRADA)
    a = an.analizar(salida=tmp_path / "a", n_perm=999)
    an.analizar(salida=tmp_path / "b", n_perm=999)
    assert an.sha256(an.ENTRADA) == antes == a["resumen"]["sha256_entrada"]
    for nombre in ("anova.csv", "efectos.csv", "medias_tratamiento.csv", "sensibilidad.csv", "resumen.json"):
        assert (tmp_path / "a" / nombre).read_bytes() == (tmp_path / "b" / nombre).read_bytes(), nombre
    r = a["resumen"]
    assert r["rango_matriz"] == 9 and r["gl_residuo"] == 7 and r["supuestos"]["no_aditividad_tukey"]["gl"] == [1, 6]
    assert r["permutacion"]["n_permutaciones"] == 999 and 0 < r["permutacion"]["A procesos"]["p_permutacion"] <= 1


def test_las_figuras_salen_de_los_resultados_originales(tmp_path, datos):
    an.analizar(salida=tmp_path, n_perm=99)
    figs = tmp_path / "figuras"
    for png in ("qq_residuos.png", "residuos_vs_ajustados.png", "residuos_vs_orden.png", "efectos_principales.png",
                "interacciones.png"):
        assert (figs / png).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", png
    dibujado = json.loads((figs / "datos_figuras.json").read_text(encoding="utf-8"))
    for col in ("procesos", "analizador", "formato"):
        esperado = datos.groupby(col).tiempo_s.mean().tolist()
        assert dibujado["principales"][col] == pytest.approx(esperado)
    t8 = datos.tiempo_s[(datos.x_proc == 1) & (datos.x_anal == 1) & (datos.x_form == 1)].mean()
    assert dibujado["interacciones"]["ABC|orjson/parquet"][1] == pytest.approx(t8)


def test_rechaza_datos_incompletos_o_con_pilotos(tmp_path):
    lineas = an.ENTRADA.read_text(encoding="utf-8").splitlines()
    incompleto = tmp_path / "incompleto.jsonl"
    incompleto.write_text("\n".join(lineas[:15]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        an.cargar(incompleto)
    piloto = json.loads(lineas[0]) | {"piloto": True}
    con_piloto = tmp_path / "piloto.jsonl"
    con_piloto.write_text("\n".join(lineas + [json.dumps(piloto)]) + "\n", encoding="utf-8")
    assert len(an.cargar(con_piloto)) == 16                                 # el piloto se ignora, no se mezcla


def test_la_prueba_de_permutacion_es_reproducible_con_su_semilla(datos):
    a, b = an.prueba_permutacion(datos, 500), an.prueba_permutacion(datos, 500)
    assert a == b and a["A procesos"]["F"] == pytest.approx(an.tabla_anova(an.ajustar(datos)).loc["A procesos", "F"])
