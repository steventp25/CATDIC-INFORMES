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


def test_revisar_dato_guarda_el_trozo_literal_del_plano():  # SINTÉTICO
    por_n = es.textos_por_n(TEXTOS)
    r = revisar_dato({"valor": '36∅1"', "citas": [3]}, por_n)  # Claude escribe ∅; el plano trae Ø
    assert r["valor"] == '36Ø1"' and r["fuente"]["textos"] == ['36Ø1"']
    assert revisar_dato({"valor": "C1", "citas": [74]}, por_n)["valor"] == "C1"


@pytest.mark.parametrize("valor,citados", [("E-3", ["E-3"]), ("A-B", ["A-B"]), ("2-3", ["2-3"]),
                                           ("0.25", ["H=0.25M"]), ("3", ["E - 3"]), ("A", ["EJE A"])])
def test_guion_y_punto_que_si_anclan(valor, citados):  # SINTÉTICO
    assert anclar(valor, citados)


@pytest.mark.parametrize("valor,citados", [("3", ["E-3"]), ("E", ["E-3"]), ("A", ["A-B"]), ("B", ["A-B"]),
                                           ("3", ["2-3"]), ("2", ["2-3"]), ("25", ["0.25"])])
def test_guion_y_punto_pegados_no_anclan(valor, citados):  # SINTÉTICO
    assert not anclar(valor, citados)


# ---------- Evidencias (§5.1, A3d) ----------

def _tx(*textos, ancho=1000, alto=800):
    return {**TEXTOS, "ancho_pt": ancho, "alto_pt": alto,
            "textos": [{"n": n, "texto": t, "bbox": [n, n, n + 10, n + 5], "tam": 8} for n, t in enumerate(textos, 1)]}


def _rev(dato, *textos, hoja=True, **kw):
    t = _tx(*textos, **kw)
    return revisar_dato(dato, es.textos_por_n(t), t if hoja else None)


def _prop_con(dato_campo):
    p = _buena()
    p["elementos"][0]["campos"] = {"x": dato_campo}
    return validar_propuesta(p, TEXTOS)


def test_reglas_de_conversion():  # SINTÉTICO
    R = es.REGLAS_CONVERSION
    assert R["decimales_2"](["1.5"]) == "1.50" and R["decimales_2"](["1"]) == "1.00"
    assert R["decimales_2"](["0.25"]) == "0.25"
    assert R["cm_a_m"](["60"]) == "0.60" and R["cm_a_m"](["125cm"]) == "1.25"
    assert R["suma"](["0.30", "1.20"]) == "1.50" and R["suma"](["0.3", "1.25"]) == "1.55"
    assert R["suma"](["1", "2"]) == "3"
    assert set(R) == {"decimales_2", "cm_a_m", "suma"}


@pytest.mark.parametrize("regla,entradas", [
    ("decimales_2", ["1.505"]), ("decimales_2", ["abc"]), ("decimales_2", ["1", "2"]), ("decimales_2", ["1,5"]),
    ("cm_a_m", ["1.5"]), ("cm_a_m", ["abc"]), ("cm_a_m", ["60", "1"]),
    ("suma", ["0.3"]), ("suma", ["0.3", "abc"]), ("suma", ["0.3", "1,2"])])
def test_reglas_que_fallan(regla, entradas):  # SINTÉTICO
    with pytest.raises(ValueError):
        es.REGLAS_CONVERSION[regla](entradas)


# (b) partes
def _partes(valor='9 EST. ∅3/8" @0.10'):
    return {"valor": valor, "evidencia": "partes",
            "partes": [{"valor": '9 EST. ∅3/8"', "citas": [1]}, {"valor": "@0.10", "citas": [2]}]}


def test_partes_entra_y_guarda_cada_parte():  # SINTÉTICO
    r = _rev(_partes(), '9 EST. Ø3/8"', "@0.10")
    assert r["valor"] == '9 EST. Ø3/8" @0.10' and r["duda"] is None and r["evidencia"] == "partes"
    assert [p["citas"] for p in r["fuente"]["partes"]] == [[1], [2]]
    assert r["fuente"]["bbox"] == [1, 1, 12, 7]


def test_partes_que_fallan():  # SINTÉTICO
    assert _rev(_partes(), '9 EST. Ø3/8"', "@0.20")["valor"] is None  # una parte no ancla
    mal = _rev(_partes('9 EST. ∅3/8" @0.15'), '9 EST. Ø3/8"', "@0.10")  # la unión no es el valor
    assert mal["valor"] is None and "@0.10" in mal["duda"] and mal["duda"].startswith("IA:")


# (c) zona
def _zona(zona, valor="0.60"):
    return {"valor": valor, "evidencia": "zona", "zona": zona}


def test_zona_dentro_de_la_hoja_da_valor_y_duda_de_revision_visual():  # SINTÉTICO
    r = _rev(_zona([10, 10, 100, 50]), "x")
    assert r["valor"] == "0.60" and r["duda"].startswith("IA: revisión visual: ")
    assert "[10, 10, 100, 50]" in r["duda"] and "0.60" in r["duda"]
    assert r["fuente"] == {"evidencia": "zona", "zona": [10, 10, 100, 50], "lectura": "0.60", "citas": []}


@pytest.mark.parametrize("zona", [[10, 10, 1001, 50], [10, 10, 100, 801], [-1, 0, 5, 5], [50, 10, 50, 20],
                                  [60, 10, 50, 20], [10, 30, 20, 20]])
def test_zona_fuera_de_la_hoja_o_invertida_no_da_valor(zona):  # SINTÉTICO
    r = _rev(_zona(zona), "x")
    assert r["valor"] is None and r["duda"].startswith("IA:")


def test_zona_sin_hoja_no_da_valor():  # SINTÉTICO
    assert _rev(_zona([10, 10, 100, 50]), "x", hoja=False)["valor"] is None
    t = _tx("x")
    del t["ancho_pt"]
    assert revisar_dato(_zona([10, 10, 100, 50]), es.textos_por_n(t), t)["valor"] is None


# (d) conversion
def _conv(regla, entradas, valor=None):
    d = {"evidencia": "conversion", "conversion": {"regla": regla, "entradas": [
        {"valor": v, "citas": [n]} for n, v in enumerate(entradas, 1)]}}
    if valor is not None:
        d["valor"] = valor
    return d


def test_conversion_entra_y_guarda_regla_y_entradas():  # SINTÉTICO
    r = _rev(_conv("suma", ["0.30", "1.20"], "1.50"), "e=0.30m", "1.20")
    assert r["valor"] == "1.50" and r["duda"] is None and r["evidencia"] == "conversion"
    assert r["fuente"]["regla"] == "suma" and [e["literal"] for e in r["fuente"]["entradas"]] == ["0.30", "1.20"]
    assert r["fuente"]["bbox"] == [1, 1, 12, 7] and r["fuente"]["citas"] == [1, 2]
    assert _rev(_conv("cm_a_m", ["60"]), "60")["valor"] == "0.60"  # sin valor de la IA


@pytest.mark.parametrize("dato,textos", [
    (_conv("no_existe", ["1"]), ("1",)),                      # regla desconocida
    (_conv("cm_a_m", ["70"]), ("60",)),                       # entrada que no ancla
    (_conv("decimales_2", ["1.505"]), ("1.505",)),            # la regla falla
    (_conv("cm_a_m", ["60"], "0.65"), ("60",)),               # el valor de la IA no es el calculado
])
def test_conversion_que_falla(dato, textos):  # SINTÉTICO
    r = _rev(dato, *textos)
    assert r["valor"] is None and r["duda"].startswith("IA:") and r["fuente"] is None


# Formato
def _intenta(dato):
    with pytest.raises(PropuestaInvalida):
        _prop_con(dato)


def test_rechazos_de_formato_de_evidencia():  # SINTÉTICO
    _intenta({"valor": "1", "evidencia": "inventada", "citas": [1]})
    _intenta({"valor": "1", "evidencia": "partes", "partes": [{"valor": "1", "citas": [1]}]})  # una sola parte
    _intenta({"valor": "1", "evidencia": "partes",
              "partes": [{"valor": "1", "citas": [999]}, {"valor": "2", "citas": [1]}]})
    _intenta({"valor": "1", "evidencia": "partes"})
    _intenta({"valor": "1", "evidencia": "zona"})
    _intenta({"valor": "1", "evidencia": "zona", "zona": [1, 2, 3]})
    _intenta({"valor": "1", "evidencia": "conversion"})
    _intenta({"evidencia": "conversion", "conversion": {"regla": 5, "entradas": [{"valor": "1", "citas": [1]}]}})
    _intenta({"evidencia": "conversion", "conversion": {"regla": "suma", "entradas": []}})
    _intenta({"evidencia": "conversion",
              "conversion": {"regla": "suma", "entradas": [{"valor": "1", "citas": [999]}]}})


@pytest.mark.parametrize("extra", [{"evidencia": "zona", "zona": [1, 2, 3, 4]},
                                   {"evidencia": "conversion", "conversion": {"regla": "suma", "entradas": [
                                       {"valor": "1", "citas": [1]}]}},
                                   {"zona": [1, 2, 3, 4]}])
@pytest.mark.parametrize("dato", ["id_elemento", "nivel_rango", "ejes"])
def test_zona_o_conversion_en_la_identidad_rechazan_la_hoja(dato, extra):  # SINTÉTICO
    p = _buena()
    p["elementos"][0][dato] = {"valor": "C1", "citas": [74], **extra}
    with pytest.raises(PropuestaInvalida):
        validar_propuesta(p, TEXTOS)


def test_evidencias_buenas_se_normalizan_y_partes_no_piden_citas():  # SINTÉTICO
    d = _prop_con(_partes())["elementos"][0]["campos"]["x"]
    assert d["evidencia"] == "partes" and len(d["partes"]) == 2
    z = _prop_con({"valor": "0.6", "evidencia": "zona", "zona": [1, 2, 3, 4]})["elementos"][0]["campos"]["x"]
    assert z["zona"] == [1, 2, 3, 4]
    c = _prop_con(_conv("suma", ["0.3", "1"]))["elementos"][0]["campos"]["x"]
    assert c["valor"] is None and c["conversion"]["regla"] == "suma"
    q = _buena()  # el id sí admite partes
    q["elementos"][0]["id_elemento"] = {"valor": "COLUMNA C1", "evidencia": "partes",
                                        "partes": [{"valor": "COLUMNA", "citas": [74]}, {"valor": "C1", "citas": [74]}]}
    validar_propuesta(q, TEXTOS)


def test_null_con_duda_vale_con_cualquier_evidencia():  # SINTÉTICO
    for ev in ("literal", "partes", "zona", "conversion"):
        d = {"valor": None, "duda": "no se ve", "evidencia": ev}
        assert _prop_con(d)["elementos"][0]["campos"]["x"]["duda"] == "no se ve"
        assert _rev(d, "x")["valor"] is None and _rev(d, "x")["duda"] == "no se ve"


def test_evidencia_desconocida_rechaza_la_hoja_aunque_el_valor_sea_null():  # SINTÉTICO (revisión del Líder)
    _intenta({"valor": None, "duda": "no se ve", "evidencia": "otra"})
