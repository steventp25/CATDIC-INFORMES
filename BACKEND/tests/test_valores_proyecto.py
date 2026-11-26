# BACKEND/tests/test_valores_proyecto.py
# Etapa 7 · T17 — Valores del proyecto confirmados por Steven (valores_proyecto_confirmados.json). Todo SINTÉTICO: la obra
# de prueba es `obra-sint`; los valores sintéticos imitan la FORMA del archivo real (que es de `terra-living`), no sus datos.
import json

import pytest

import procesador_cola as pc
import valores_proyecto as vp
from reglas_ingenieria import PENDIENTE
from test_procesar_cola import PID, _abiertas, _bd, _capturar_fichas, _diseno, _elemento_visita, _procesar, entorno  # noqa: F401


def _v(fila, letra, valor, aplica, **extra):
    return {"proyecto_id": PID, "fila_stp": fila, "letra": letra, "valor": valor, "aplica_a": aplica,
            "confirmado_por": "Steven", "fecha": "2026-11-26", "cita": f"CITA SINT {fila}.{letra}",
            "origen": "informes STP entregados", **extra}


VALORES = [
    _v("col", "e", "2.95", ["COLUMNA"], contraste_campos=["altura_m"]),
    _v("col", "o", "ZONA CENTRAL / 1.08", ["COLUMNA"]),
    _v("muro", "a", "350", ["MURO H.A."]),
    _v("muro", "a", "240", ["MURO DE CONTENCION"], solo_si={"campo": "id_elemento", "contiene_palabra": "PERIMETRAL"}),
    _v("muro", "d", "2.95", ["MURO H.A.", "MURO DE CONTENCION"], contraste_campos=["altura_m"]),
    _v("muro", "e", "SI", ["MURO H.A.", "MURO DE CONTENCION"]),
]
COL = {"b_m": "0.60", "h_m": "1.50", "acero_longitudinal": '36Ø1"', "estribos": '9 EST. Ø3/8" @0.10'}  # SINTÉTICO
MURO = {"espesor": "0.40", "longitud": "1.80", "alma.ASV": 'Ø1/2"@0.10', "alma.ASH": 'Ø3/8"@0.10'}  # SINTÉTICO


@pytest.fixture
def valores(tmp_path, monkeypatch):
    ruta = tmp_path / "valores.json"
    ruta.write_text(json.dumps({"version": 1, "valores": VALORES}), encoding="utf-8")
    monkeypatch.setattr(vp, "RUTA_CONFIGURACION", ruta)
    return ruta


def _fichas(entorno, monkeypatch, elementos):
    """elementos: [(id, ejes, tipo, campos)] -> fichas capturadas (el generador se reemplaza por un falso)."""
    mapeo, _ = pc.cargar_mapeo_stp()  # el mapeo REAL: sin derivación de la altura
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", mapeo)
    monkeypatch.setattr(pc, "MAPEO_CONFIRMADO", False)
    capturado = _capturar_fichas(monkeypatch)
    for i, (id_el, ejes, tipo, campos) in enumerate(elementos, 1):
        _elemento_visita(entorno, i, f"{id_el} X", id_el, ejes)
        _diseno(uid=f"ed-{i:04d}", id_elemento=id_el, ejes=ejes, tipo=tipo, campos=campos)
    _procesar()
    return {f["titulo"]: f for f in capturado.get("fichas", [])}


def _auditoria(accion):
    with _bd() as conn:
        return [json.loads(r["detalle_json"]) for r in conn.execute(
            "SELECT detalle_json FROM auditoria WHERE accion = ? ORDER BY id", (accion,))]


def _campos_abiertos():
    return {d["campo_afectado"] for d in _abiertas()}


# ---------- Cada valor llega a su fila con su origen ----------

def test_columna_recibe_e_y_o_con_su_origen(entorno, monkeypatch, valores):
    f = _fichas(entorno, monkeypatch, [("C1", "EJE D-4", "COLUMNA", COL)])["COLUMNA-C1-EJE D-4"]
    assert f["plano"]["e"] == "2.95" and f["plano"]["o"] == "ZONA CENTRAL / 1.08"
    o = f["origen_filas"]["e"]
    assert o == {"archivo": "valores_proyecto_confirmados.json", "valor": "2.95", "cita": "CITA SINT col.e",
                 "confirmado_por": "Steven", "fecha": "2026-11-26", "origen": "informes STP entregados"}
    assert f["origen_filas"]["o"]["cita"] == "CITA SINT col.o"
    assert not _campos_abiertos() & {"diseno:p001:altura", "diseno:p001:valor.e", "diseno:p001:valor.o"}


def test_muro_ha_recibe_a_350_d_y_e(entorno, monkeypatch, valores):
    f = _fichas(entorno, monkeypatch, [("MH3", "EJE C ENTRE 2-3", "MURO H.A.", MURO)])["MURO H.A.-MH3-EJE C ENTRE 2-3"]
    assert (f["plano"]["a"], f["plano"]["d"], f["plano"]["e"]) == ("350", "2.95", "SI")
    assert set(f["origen_filas"]) == {"a", "d", "e"} and f["origen_filas"]["a"]["valor"] == "350"
    assert f["plano"]["c"] == "1.80"  # lo del dibujo sigue igual


def test_muro_marcado_perimetral_en_su_id_recibe_240(entorno, monkeypatch, valores):
    f = _fichas(entorno, monkeypatch, [("MURO DE CONTENCION PERIMETRAL", "EJE 4 ENTRE A-D", "MURO DE CONTENCION",
                                        {**MURO, "longitud": PENDIENTE})])
    f = next(iter(f.values()))
    assert f["plano"]["a"] == "240" and f["origen_filas"]["a"]["cita"] == "CITA SINT muro.a"
    assert f["plano"]["d"] == "2.95" and f["plano"]["e"] == "SI"


def test_las_demas_filas_no_cambian(entorno, monkeypatch, valores):
    f = _fichas(entorno, monkeypatch, [("C1", "EJE D-4", "COLUMNA", COL)])["COLUMNA-C1-EJE D-4"]
    assert f["plano"] == {"h": '9 EST. Ø3/8"', "f": 'Ø3/8"@0.10', "g": 'Ø3/8"@0.10', "m": 'Ø1"', "n": 'Ø1"', "k": "36",
                          "e": "2.95", "o": "ZONA CENTRAL / 1.08"}
    assert "b" not in f["plano"] and "p" not in f["plano"]


def test_la_auditoria_guarda_el_origen_de_las_filas(entorno, monkeypatch, valores):
    _fichas(entorno, monkeypatch, [("C1", "EJE D-4", "COLUMNA", COL)])
    a = _auditoria("ORIGEN_FILAS")
    assert len(a) == 1 and a[0]["id_elemento"] == "C1" and {"e", "o"} <= set(a[0]["origen_filas"])
    assert a[0]["origen_filas"]["e"]["cita"] == "CITA SINT col.e"


# ---------- El 240 solo con la marca de perimetral ----------

@pytest.mark.parametrize("id_elemento", ["MC", "MURO DE CONTENCION", "MURO DE CONTENCION PERIMETRALES", "XPERIMETRAL"])
def test_muro_de_contencion_sin_la_marca_no_recibe_240_y_abre_la_duda(entorno, monkeypatch, valores, id_elemento):
    f = _fichas(entorno, monkeypatch, [(id_elemento, "EJE 4 ENTRE A-D", "MURO DE CONTENCION", MURO)])
    assert not f  # la ficha queda en espera
    d = [d for d in _abiertas() if d["campo_afectado"] == "diseno:p001:valor.a"]
    assert len(d) == 1 and "240" in d[0]["descripcion_pregunta"] and "PERIMETRAL" in d[0]["descripcion_pregunta"]
    assert "no se deduce por el tipo" in d[0]["descripcion_pregunta"]


def test_el_muro_ha_nunca_recibe_240_aunque_diga_perimetral(entorno, monkeypatch, valores):
    f = _fichas(entorno, monkeypatch, [("MH-PERIMETRAL", "EJE C ENTRE 2-3", "MURO H.A.", MURO)])
    assert next(iter(f.values()))["plano"]["a"] == "350"


# ---------- Altura ----------

def test_altura_legible_distinta_abre_la_duda_con_el_texto_literal_y_deja_la_fila_vacia(entorno, monkeypatch, valores):
    f = _fichas(entorno, monkeypatch, [("C1", "EJE D-4", "COLUMNA", {**COL, "altura_m": "3.00"})])
    assert not f  # la ficha queda en espera
    d = [d for d in _abiertas() if d["campo_afectado"] == "diseno:p001:altura"]
    assert len(d) == 1 and "altura_m = '3.00'" in d[0]["descripcion_pregunta"] and "2.95" in d[0]["descripcion_pregunta"]


def test_altura_distinta_en_muro_tambien_abre_la_duda(entorno, monkeypatch, valores):
    f = _fichas(entorno, monkeypatch, [("MH3", "EJE C ENTRE 2-3", "MURO H.A.", {**MURO, "altura_m": "3,10 m"})])
    assert not f and "diseno:p001:altura" in _campos_abiertos()


@pytest.mark.parametrize("impreso", ["2.95", "2,95", "2.95 m", "2.950", PENDIENTE, "", None, "295 cm"])
def test_altura_igual_o_sin_dato_legible_usa_2_95_sin_calcular(entorno, monkeypatch, valores, impreso):
    campos = {**COL, "altura_m": impreso} if impreso is not None else dict(COL)
    f = _fichas(entorno, monkeypatch, [("C1", "EJE D-4", "COLUMNA", campos)])["COLUMNA-C1-EJE D-4"]
    assert f["plano"]["e"] == "2.95" and "diseno:p001:altura" not in _campos_abiertos()


# ---------- Archivo roto o ausente: no llena nada ----------

def test_archivo_ausente_no_llena_nada_ni_deriva_la_altura(entorno, monkeypatch, tmp_path):
    monkeypatch.setattr(vp, "RUTA_CONFIGURACION", tmp_path / "no_existe.json")
    f = _fichas(entorno, monkeypatch, [("C1", "EJE D-4", "COLUMNA", {**COL, "altura_m": "3.00"})])["COLUMNA-C1-EJE D-4"]
    assert "e" not in f["plano"] and "o" not in f["plano"] and not (set(f["origen_filas"]) & {"e", "o"})


@pytest.mark.parametrize("contenido", ["{no es json", "[]", '{"valores": "x"}'])
def test_archivo_roto_no_llena_nada(entorno, monkeypatch, tmp_path, contenido):
    ruta = tmp_path / "roto.json"
    ruta.write_text(contenido, encoding="utf-8")
    monkeypatch.setattr(vp, "RUTA_CONFIGURACION", ruta)
    f = _fichas(entorno, monkeypatch, [("C1", "EJE D-4", "COLUMNA", COL)])["COLUMNA-C1-EJE D-4"]
    assert "e" not in f["plano"] and "o" not in f["plano"] and not (set(f["origen_filas"]) & {"e", "o"})
    assert vp.cargar_valores(ruta)[0] == [] and vp.cargar_valores(ruta)[1]  # con aviso


def test_un_valor_incompleto_se_ignora_con_aviso_y_los_demas_siguen(tmp_path):
    ruta = tmp_path / "v.json"
    sin_cita = {k: v for k, v in VALORES[0].items() if k != "cita"}
    marca_mala = {**VALORES[3], "solo_si": {"campo": "inventado", "contiene_palabra": "X"}}
    ruta.write_text(json.dumps({"valores": [sin_cita, VALORES[1], marca_mala, "x"]}), encoding="utf-8")
    valores, avisos = vp.cargar_valores(ruta)
    assert [v["letra"] for v in valores] == ["o"] and len(avisos) == 3


def test_otro_proyecto_no_recibe_los_valores(entorno, monkeypatch, tmp_path):
    ruta = tmp_path / "v.json"
    ruta.write_text(json.dumps({"valores": [{**v, "proyecto_id": "otra-obra"} for v in VALORES]}), encoding="utf-8")
    monkeypatch.setattr(vp, "RUTA_CONFIGURACION", ruta)
    f = _fichas(entorno, monkeypatch, [("C1", "EJE D-4", "COLUMNA", COL)])["COLUMNA-C1-EJE D-4"]
    assert "e" not in f["plano"] and not (set(f["origen_filas"]) & {"e", "o"})


# ---------- El archivo real versionado ----------

def test_el_archivo_real_trae_los_seis_valores_completos_con_cita():
    valores, avisos = vp.cargar_valores(vp.RUTA_CONFIGURACION)
    assert avisos == [] and {(v["fila_stp"], v["letra"], v["valor"]) for v in valores} == {
        ("col", "e", "2.95"), ("col", "o", "ZONA CENTRAL / 1.08"), ("muro", "a", "350"), ("muro", "a", "240"),
        ("muro", "d", "2.95"), ("muro", "e", "SI")}
    for v in valores:
        assert v["proyecto_id"] == "terra-living" and v["confirmado_por"] == "Steven" and v["fecha"] == "2026-11-26"
        assert v["cita"].strip() and v["origen"] == "informes STP entregados"
    perimetral = next(v for v in valores if v["valor"] == "240")
    assert perimetral["aplica_a"] == ["MURO DE CONTENCION"] and perimetral["solo_si"]["contiene_palabra"] == "PERIMETRAL"
    assert next(v for v in valores if v["valor"] == "350")["aplica_a"] == ["MURO H.A."]


def test_marca_de_perimetral_palabra_completa_sin_importar_mayusculas():
    v = VALORES[3]
    assert vp.cumple_marca(v, {"id_elemento": "Muro de contencion perimetral"}, {})
    assert not vp.cumple_marca(v, {"id_elemento": "MC"}, {})
    assert not vp.cumple_marca(v, {"id_elemento": "SUBPERIMETRAL"}, {})
    v2 = {**v, "solo_si": {"campo": "datos_diseno.nota", "contiene_palabra": "perimetral"}}
    assert vp.cumple_marca(v2, {"id_elemento": "MC"}, {"nota": "MURO PERIMETRAL"})
    assert not vp.cumple_marca(v2, {"id_elemento": "MC"}, {"nota": None})


def test_el_mapeo_real_no_deriva_la_altura_del_plano():
    mapeo, _ = pc.cargar_mapeo_stp()
    assert "e" not in mapeo["col"]["derivaciones"] and "d" not in mapeo["muro"].get("derivaciones", {})
