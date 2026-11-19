# BACKEND/tests/test_asistido_esquema.py
# Etapa 5 · A3a — esquema de propuesta.json y regla de anclaje (SINTÉTICO: textos inventados, sin PDF).
import copy

import pytest

from plano.asistido import esquema as es
from plano.asistido.esquema import PropuestaInvalida, anclar, revisar_dato, validar_propuesta

SHA = "ab" * 32
TEXTOS = {"version": 1, "archivo": "e.pdf", "sha256": SHA, "pagina": 14, "hoja": "13", "textos": [
    {"n": 1, "texto": '9 EST. ∅3/8"', "bbox": [10, 10, 50, 20], "tam": 8},
    {"n": 2, "texto": "@0.10", "bbox": [52, 11, 80, 21], "tam": 8},
    {"n": 3, "texto": '36Ø1"', "bbox": [100, 100, 130, 110], "tam": 8},
    {"n": 74, "texto": "COLUMNA C1", "bbox": [5, 200, 60, 210], "tam": 8},
    {"n": 76, "texto": "FUNDACIONES @ E-3", "bbox": [5, 300, 90, 310], "tam": 8}]}


def _buena():
    return {"version": 1, "archivo": "e.pdf", "sha256": SHA, "pagina": 14, "hoja": "13",
            "lector": "claude-code", "skill": "extraer-plano@1",
            "elementos": [{"tipo_elemento": "COLUMNA", "zona": [1, 2, 3, 4],
                           "id_elemento": {"valor": "C1", "citas": [74]},
                           "nivel_rango": {"valor": "FUNDACIONES @ E-3", "citas": [76]},
                           "ejes": {"valor": None, "duda": "No hay ejes (D11)."},
                           "campos": {"acero_longitudinal": {"valor": '36∅1"', "citas": [3]},
                                      "estribos": {"valor": '9 EST. ∅3/8" @0.10', "citas": [1, 2]}},
                           "enlaces": [], "dudas": []}],
            "dudas_hoja": [{"texto": "nota", "citas": [74]}], "comprobaciones": []}


def test_propuesta_buena():  # SINTÉTICO
    p = validar_propuesta(_buena(), TEXTOS)
    assert p["elementos"][0]["campos"]["estribos"]["citas"] == [1, 2]
    assert p["elementos"][0]["ejes"]["valor"] is None


def _cambia(f):
    p = _buena()
    f(p)
    return p


MALAS = {
    "falta_clave": lambda p: p.pop("skill"),
    "tipo_equivocado": lambda p: p.update(hoja=13),
    "version": lambda p: p.update(version=2),
    "sha256": lambda p: p.update(sha256="x"),
    "pagina": lambda p: p.update(pagina=15),
    "sin_citas": lambda p: p["elementos"][0]["id_elemento"].update(citas=[]),
    "cita_inexistente": lambda p: p["elementos"][0]["id_elemento"].update(citas=[999]),
    "cita_no_entera": lambda p: p["elementos"][0]["id_elemento"].update(citas=["74"]),
    "null_sin_duda": lambda p: p["elementos"][0]["ejes"].pop("duda"),
    "tipo_desconocido": lambda p: p["elementos"][0].update(tipo_elemento="PUENTE"),
    "zona_corta": lambda p: p["elementos"][0].update(zona=[1, 2, 3]),
    "zona_no_numerica": lambda p: p["elementos"][0].update(zona=[1, 2, 3, "4"]),
    "campo_sin_citas": lambda p: p["elementos"][0]["campos"]["estribos"].pop("citas"),
    "cita_inexistente_en_duda_hoja": lambda p: p["dudas_hoja"][0].update(citas=[5000]),
}


@pytest.mark.parametrize("causa", sorted(MALAS))
def test_causas_de_propuesta_invalida(causa):  # SINTÉTICO
    p = _buena()
    MALAS[causa](p)
    with pytest.raises(PropuestaInvalida):
        validar_propuesta(p, TEXTOS)


def test_no_modifica_la_entrada():  # SINTÉTICO
    p = _buena()
    antes = copy.deepcopy(p)
    validar_propuesta(p, TEXTOS)
    assert p == antes


@pytest.mark.parametrize("valor,citados", [
    ("C1", ["COLUMNA C1"]),
    ("0.25", ["H=0.25M"]),
    ('36∅1"', ['36Ø1"']),
    ('9 EST. ∅3/8" @0.10', ['9 EST. ∅3/8"', "@0.10"]),
    ("FUNDACIONES @ E-3", ["FUNDACIONES @ E-3"]),
    ("FUNDACIONES @ E-3", ["FUNDACIONES   @  E-3"]),
    ("0.50", ["e=0.50m"]),
])
def test_anclas_que_pasan(valor, citados):  # SINTÉTICO
    assert anclar(valor, citados)


@pytest.mark.parametrize("valor,citados", [
    ("1", ['36∅1"']),
    ("25", ["0.25"]),
    ("0.5", ["0.50"]),
    ("1.50", ["11.50"]),
    ("c1", ["C1"]),
    ("0.25", ["H=0.25MM"]),
    ("", ["algo"]),
    ("A", []),
])
def test_anclas_que_fallan(valor, citados):  # SINTÉTICO
    assert not anclar(valor, citados)


def test_ancla_busca_otra_aparicion_valida():  # SINTÉTICO
    assert anclar("25", ["0.25 y luego 25"])


def test_revisar_dato_tres_salidas():  # SINTÉTICO
    por_n = es.textos_por_n(TEXTOS)
    ok = revisar_dato({"valor": '9 EST. ∅3/8" @0.10', "citas": [1, 2]}, por_n)
    assert ok["valor"] == '9 EST. ∅3/8" @0.10' and ok["duda"] is None
    assert ok["fuente"] == {"citas": [1, 2], "textos": ['9 EST. ∅3/8"', "@0.10"], "bbox": [10, 10, 80, 21]}
    nulo = revisar_dato({"valor": None, "duda": "sin ejes"}, por_n)
    assert nulo == {"valor": None, "fuente": None, "duda": "sin ejes"}
    mal = revisar_dato({"valor": "C2", "citas": [74]}, por_n)
    assert mal == {"valor": None, "fuente": None, "duda": "IA: propuso 'C2' pero el texto citado dice 'COLUMNA C1'"}


def test_revisar_dato_guarda_el_diametro_normalizado():  # SINTÉTICO
    r = revisar_dato({"valor": '36Ø1"', "citas": [3]}, es.textos_por_n(TEXTOS))
    assert r["valor"] == '36∅1"' and r["fuente"]["textos"] == ['36Ø1"']
