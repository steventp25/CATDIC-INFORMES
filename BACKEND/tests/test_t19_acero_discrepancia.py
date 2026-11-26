# BACKEND/tests/test_t19_acero_discrepancia.py
# Etapa 7 · T19 — Acero de OBRA distinto del de PLANOS = discrepancia (Steven, 25/11/2026, pregunta 31: «Sí, que lo marque»).
# Datos SINTÉTICOS; solo se prueba _filas_de_ficha (no se renderiza ni se escribe nada).
import pytest

from generators import stp_mived
from test_reglas_c14_c16 import _col, _filas


def _muro(**cambios):
    ficha = {"titulo": "MURO H.A.-MS1", "tipo_elemento": "MURO H.A.", "ejes": "EJE A-B,1",
             "plano": {"a": "350", "c": "1.80", "d": "2.95", "e": "SI", "h": 'Ø1/2"@0.10', "i": 'Ø1/2"@0.10',
                       "j": 'Ø3/8"@0.10', "k": 'Ø3/8"@0.10'},
             "medidas": {"b": {"valor_plano_m": 0.40, "medida_acero_campo_m": None}},
             "obra": {}, "conforme_por_omision": list("abcdefghijk")}
    ficha.update(cambios)
    return ficha


def _dudas_de(dudas, campo):
    return [d for d in dudas if d["campo_afectado"] == campo]


def test_menos_estribos_en_obra_es_discrepancia_en_h():
    filas, _, _ = _filas(_col(conforme_por_omision=list("bcdefgijkmno"), obra={"h": '8 EST. ∅3/8"'},
                              plano={**_col()["plano"], "h": '9 EST. ∅3/8"'}))
    assert len(filas["discrepancias"]) == 1
    assert "Diam. Est. (Ø)" in filas["discrepancias"][0] and '8 EST. ∅3/8"' in filas["discrepancias"][0]
    assert filas["obra"]["p"] == ""


def test_menos_barras_en_obra_es_discrepancia_en_k():
    filas, _, _ = _filas(_col(conforme_por_omision=list("bcdefghijmno"), obra={"k": "34"}))
    assert len(filas["discrepancias"]) == 1 and "Total barras en obra 34, en planos 36" in filas["discrepancias"][0]


def test_est_sin_punto_y_otra_comilla_es_conforme():
    filas, dudas, _ = _filas(_col(conforme_por_omision=list("bcdefgijkmno"), obra={"h": "9 EST ∅3/8″"},
                                  plano={**_col()["plano"], "h": '9 EST. ∅3/8"'}))
    assert filas["discrepancias"] == [] and filas["obra"]["p"] == "0.0203"
    assert not _dudas_de(dudas, "obra.h.forma")


def test_dos_comillas_simples_cuentan_como_pulgada():
    filas, _, _ = _filas(_col(conforme_por_omision=list("bcdefghjkmno"), obra={"i": "6-Ø1''"}))
    assert filas["discrepancias"] == [] and filas["obra"]["p"] == "0.0203"


def test_una_fila_vacia_en_obra_es_conforme():
    filas, _, _ = _filas(_col())  # todo conforme por omisión: OBRA repite el plano
    assert filas["discrepancias"] == [] and filas["obra"]["p"] == "0.0203"
    filas2, dudas2, _ = _filas(_col(conforme_por_omision=list("bcdefgijkmno")))  # h vacía y sin omisión
    assert filas2["discrepancias"] == [] and _dudas_de(dudas2, "obra.h")  # su duda de siempre, no una discrepancia


def test_forma_ilegible_abre_duda_y_no_discrepancia():
    filas, dudas, _ = _filas(_col(conforme_por_omision=list("bcdefgijkmno"), obra={"h": "ESTRIBOS COMO EN PLANO"}))
    assert filas["discrepancias"] == []
    d = _dudas_de(dudas, "obra.h.forma")
    assert len(d) == 1 and not d[0]["bloquea"] and "ESTRIBOS COMO EN PLANO" in d[0]["descripcion_pregunta"]
    assert filas["obra"]["p"] == "0.0203"  # h (estribos) no entra en As: C14 no depende de ella (Evaluación 12)
    filas2, dudas2, _ = _filas(_col(conforme_por_omision=list("bcdefghijmno"), obra={"k": "TREINTA Y SEIS"}))
    assert filas2["discrepancias"] == [] and _dudas_de(dudas2, "obra.k.forma")
    assert filas2["obra"]["p"] == ""  # una fila de As sin comprobar: no se da la cuantía del plano


def test_solo_cambia_el_simbolo_de_diametro_abre_duda():
    """El símbolo no se normaliza (T19): Ø frente a ∅ con el mismo contenido no se da por igual ni por distinto."""
    filas, dudas, _ = _filas(_col(conforme_por_omision=list("bcdefghjkmno"), obra={"i": '6-∅1"'}))
    assert filas["discrepancias"] == [] and _dudas_de(dudas, "obra.i.forma")


def test_la_fila_o_descriptiva_no_se_compara():
    filas, dudas, _ = _filas(_col(conforme_por_omision=list("bcdefghijkmn"), obra={"o": "Empalme inicia a 0.60"}))
    assert filas["discrepancias"] == [] and not _dudas_de(dudas, "obra.o.forma")


@pytest.mark.parametrize("letra,valor", [("f", 'Ø3/8"@0.15'), ("g", 'Ø3/8"@0.20'), ("m", 'Ø3/4"'), ("n", 'Ø3/4"'),
                                         ("i", '5-Ø1"'), ("j", '13-Ø1"')])
def test_cada_fila_de_acero_de_columna_se_compara(letra, valor):
    filas, _, _ = _filas(_col(conforme_por_omision=[l for l in "bcdefghijkmno" if l != letra], obra={letra: valor}))
    assert len(filas["discrepancias"]) == 1


def test_muro_acero_distinto_es_discrepancia_y_descriptivas_no():
    ficha = _muro(conforme_por_omision=list("abcdefgijk"), obra={"h": 'Ø3/8"@0.10'})
    filas, _, _ = stp_mived._filas_de_ficha(ficha, "MURO H.A.", "muro", None)
    assert len(filas["discrepancias"]) == 1 and "As Vert. Interno" in filas["discrepancias"][0]
    filas2, _, _ = stp_mived._filas_de_ficha(_muro(conforme_por_omision=list("bcdefghijk"), obra={"a": "280"}),
                                             "MURO H.A.", "muro", None)
    assert filas2["discrepancias"] == []  # a (resistencia, valor del proyecto) no se compara
