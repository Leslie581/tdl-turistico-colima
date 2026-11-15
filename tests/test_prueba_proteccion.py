"""Prueba temporal de la proteccion de main: esta prueba falla a proposito. La rama se borra despues; no debe fusionarse."""


def test_falla_a_proposito():
    assert False, "prueba de la proteccion de main"
