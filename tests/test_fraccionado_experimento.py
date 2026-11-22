"""Matrices teóricas 2^4 y 2^(4-1) (laboratorio/experimento/fraccionado.py): ortogonalidad, generador, alias y CSV."""
import itertools

import numpy as np
import pytest

from laboratorio.experimento import fraccionado as fr


def test_completa_16_tratamientos_distintos_codificados_y_con_niveles_correctos():
    c = fr.completa()
    assert len(c) == 16 and not c.duplicated(list("ABCD")).any()
    assert set(map(tuple, c[list("ABCD")].to_numpy())) == set(itertools.product((-1, 1), repeat=4))
    assert c[list("ABCD")].isin([-1, 1]).all().all()
    for x, (nombre, bajo, alto) in fr.FACTORES.items():
        assert (c[nombre] == np.where(c[x] == 1, alto, bajo)).all()
    assert c.A.tolist()[:4] == [-1, 1, -1, 1] and c.D.tolist() == [-1] * 8 + [1] * 8        # orden estándar
    assert set(c.mediciones) == {"ninguna (matriz teórica)"}


def test_completa_ortogonal_con_los_15_efectos_separables():
    c = fr.completa()
    assert len(fr.efectos()) == 15
    X = np.column_stack([np.ones(16)] + [fr.contraste(c, e) for e in fr.efectos()])
    assert np.array_equal(X.T @ X, 16 * np.eye(16))                          # intercepto, 4 principales y 11 interacciones
    assert all(fr.contraste(c, e).sum() == 0 for e in fr.efectos())          # columnas equilibradas


def test_fraccion_8_corridas_con_generador_d_abc_y_relacion_definidora_abcd():
    f, c = fr.fraccion(), fr.completa()
    assert len(f) == 8 and not f.duplicated(list("ABCD")).any()
    assert (f.D == f.A * f.B * f.C).all() and (fr.contraste(f, "ABCD") == 1).all()
    completa_abcd = {tuple(r) for r in c[list("ABCD")].to_numpy() if np.prod(r) == 1}
    assert {tuple(r) for r in f[list("ABCD")].to_numpy()} == completa_abcd   # es la mitad principal del 2^4
    X = np.column_stack([np.ones(8)] + [fr.contraste(f, e) for e in "ABCD"])
    assert np.array_equal(X.T @ X, 8 * np.eye(5))                            # principales ortogonales entre sí


@pytest.mark.parametrize("efecto,alias", [("A", "BCD"), ("B", "ACD"), ("C", "ABD"), ("D", "ABC"),
                                          ("AB", "CD"), ("AC", "BD"), ("AD", "BC"), ("ABCD", "I")])
def test_alias_algebraicos_y_columnas_identicas_en_la_fraccion(efecto, alias):
    assert fr.alias(efecto) == alias and fr.alias(alias) == ("ABCD" if alias == "I" else efecto)
    f = fr.fraccion()
    a = np.ones(8) if alias == "I" else fr.contraste(f, alias)
    assert np.array_equal(fr.contraste(f, efecto), a)                        # confundidos: misma columna de contraste


def test_resolucion_iv_y_estructura_completa_de_alias():
    assert fr.resolucion() == 4 and fr.producto("A", "A") == "I" and fr.producto("AB", "BC") == "AC"
    ea = fr.estructura_alias()
    assert len(ea) == 15 and all(fr.alias(a) == e for e, a in ea.items() if a != "I")
    f = fr.fraccion()
    principales = [fr.contraste(f, x) for x in "ABCD"]
    dobles = [fr.contraste(f, "".join(p)) for p in itertools.combinations("ABCD", 2)]
    assert all(abs(p @ d) == 0 for p in principales for d in dobles)         # IV: principales libres de dobles
    assert any(np.array_equal(d1, d2) for d1, d2 in itertools.combinations(dobles, 2))  # dobles confundidos entre sí


def test_ahorro_de_corridas_y_resumen():
    r = fr.resumen()
    assert (r["corridas_completa"], r["corridas_fraccion"], r["ahorro_corridas"], r["ahorro_pct"]) == (16, 8, 8, 50.0)
    assert r["generador"] == "D = ABC" and r["definidora"] == "I = ABCD" and r["resolucion"] == 4
    assert r["alias"] == {"A": "BCD", "B": "ACD", "C": "ABD", "D": "ABC", "AB": "CD", "AC": "BD", "AD": "BC", "ABCD": "I"}


def test_csv_reproducibles_con_lf_e_iguales_a_los_versionados(tmp_path, monkeypatch):
    monkeypatch.setattr(fr, "CARPETA", tmp_path)
    monkeypatch.setattr(fr, "COMPLETA", tmp_path / fr.COMPLETA.name)
    monkeypatch.setattr(fr, "FRACCION", tmp_path / fr.FRACCION.name)
    a = [p.read_bytes() for p in fr.escribir()]
    b = [p.read_bytes() for p in fr.escribir()]
    assert a == b and all(b"\r" not in x for x in a)
    for nuevo, nombre in zip(a, ("matriz_2a4_completa.csv", "matriz_2a4-1_fraccion.csv")):
        versionado = fr.CARPETA.__class__(__file__).resolve().parents[1] / "laboratorio" / "experimento" / "resultados" / nombre
        if versionado.is_file():
            assert versionado.read_bytes().replace(b"\r\n", b"\n") == nuevo, nombre
