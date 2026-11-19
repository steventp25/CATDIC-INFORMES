# BACKEND/tests/test_asistido_importar.py
# Etapa 5 · A3b — importar propuesta.json con anclaje (SINTÉTICO: textos inventados sobre un plano vigente de prueba).
import copy
import json

import pytest
from test_extractor import (DATOS_COMPLETOS, _elementos, _extraer, _obra, _planta_basica, _vectorial,  # noqa: F401
                            entorno)

import database
from importadores.validador_diseno import CONFIRMADO
from plano.asistido import importar as imp

TEXTOS_BASE = [
    ("COLUMNA C1", [5, 200, 60, 210]), ("FUNDACIONES @ E-3", [5, 300, 90, 310]), ("0.60", [10, 10, 30, 20]),
    ('36Ø1"', [100, 100, 130, 110]), ('9 EST. ∅3/8"', [10, 40, 50, 50]), ("@0.10", [52, 41, 80, 51]),
    ("0.25", [200, 10, 220, 20]), ("EJE A-1", [300, 10, 340, 20]), ("NIVEL 2", [400, 10, 440, 20]), ("L1", [450, 10, 460, 20]),
    ("Nota: plano anterior", [500, 500, 600, 510])]


def _sha(pid):
    conn = database.get_connection()
    try:
        return conn.execute("SELECT vectorial_sha256 FROM planos WHERE proyecto_id = ? AND estado = 'vigente'",
                            (pid,)).fetchone()[0]
    finally:
        conn.close()


def _textos(sha):
    return {"version": 1, "archivo": "vec.pdf", "sha256": sha, "pagina": 14, "hoja": "13",
            "textos": [{"n": n, "texto": t, "bbox": b, "tam": 8} for n, (t, b) in enumerate(TEXTOS_BASE, 1)]}


def _columna(**campos):
    return {"tipo_elemento": "COLUMNA", "zona": [1, 2, 3, 4],
            "id_elemento": {"valor": "C1", "citas": [1]}, "nivel_rango": {"valor": "FUNDACIONES @ E-3", "citas": [2]},
            "ejes": {"valor": None, "duda": "El cuadro no da ejes (D11)."},
            "campos": campos or {"b": {"valor": "0.60", "citas": [3]},
                                 "acero_longitudinal": {"valor": '36∅1"', "citas": [4]},
                                 "estribos": {"valor": '9 EST. ∅3/8" @0.10', "citas": [5, 6]}},
            "enlaces": [], "dudas": []}


def _propuesta(sha, elementos, **extra):
    return {"version": 1, "archivo": "vec.pdf", "sha256": sha, "pagina": 14, "hoja": "13", "lector": "claude-code",
            "skill": "extraer-plano@1", "elementos": elementos, "dudas_hoja": [], "comprobaciones": [], **extra}


@pytest.fixture
def ctx(entorno, tmp_path):
    c = entorno
    pid = _obra(c, _vectorial(_planta_basica), DATOS_COMPLETOS)
    sha = _sha(pid)
    carpeta = tmp_path / "lectura" / "p14"
    carpeta.mkdir(parents=True)

    def poner(propuesta, textos=None):
        (carpeta / "propuesta.json").write_text(json.dumps(propuesta, ensure_ascii=False), encoding="utf-8")
        (carpeta / "textos.json").write_text(json.dumps(textos or _textos(sha), ensure_ascii=False), encoding="utf-8")

    return {"c": c, "pid": pid, "sha": sha, "carpeta": carpeta, "poner": poner,
            "importar": lambda: imp.importar_hoja(pid, carpeta, "prueba")}


def _sql(q, *a):
    conn = database.get_connection()
    try:
        return [dict(r) for r in conn.execute(q, a)]
    finally:
        conn.close()


def _conteos():
    return {t: _sql(f"SELECT COUNT(*) n FROM {t}")[0]["n"]
            for t in ("elementos_diseno", "dudas_y_hallazgos", "auditoria")}


def _dudas_ia(pid):
    return _sql("SELECT * FROM dudas_y_hallazgos WHERE proyecto_id = ? AND campo_afectado LIKE 'IA:%' AND resuelta = 0", pid)


def _sin_confirmados(pid):
    for f in _sql("SELECT estado_campos_json FROM elementos_diseno WHERE proyecto_id = ?", pid):
        assert CONFIRMADO not in json.loads(f["estado_campos_json"]).values()


def test_columna_buena_entra_nueva_y_todo_pendiente(ctx):  # SINTÉTICO
    ctx["poner"](_propuesta(ctx["sha"], [_columna()]))
    r = ctx["importar"]()
    assert r["estado"] == "importada" and r["nuevo"] == 1
    f = _sql("SELECT * FROM elementos_diseno WHERE id_elemento = 'C1'")[0]
    assert json.loads(f["fuente_json"])["extractor"] == "IA:claude-code"
    d = json.loads(f["datos_diseno_json"])
    assert d["b"] == "0.60" and d["acero_longitudinal"] == '36Ø1"' and d["estribos"] == '9 EST. ∅3/8" @0.10'
    assert f["ejes"] == "pendiente de verificar" and f["nivel_rango"] == "FUNDACIONES @ E-3"
    estado = json.loads(f["estado_campos_json"])
    assert estado["datos_diseno.b"] == "pendiente_de_verificar"
    _sin_confirmados(ctx["pid"])
    fuente = json.loads(f["fuente_json"])["valores"]["estribos"]
    assert fuente["citas"] == [5, 6] and fuente["pagina"] == 14 and fuente["hoja"] == "13" and fuente["sha256"] == ctx["sha"]
    assert json.loads((ctx["carpeta"] / "importacion.json").read_text(encoding="utf-8"))["estado"] == "importada"
    aud = _sql("SELECT * FROM auditoria WHERE modulo = 'ASISTIDO' AND accion = 'IMPORTAR_PROPUESTA'")
    assert len(aud) == 1 and aud[0]["entidad_id"] == ctx["pid"]


def test_valor_sin_ancla_y_valor_distinto_quedan_pendientes_con_duda(ctx):  # SINTÉTICO
    el = _columna(b={"valor": "0.65", "citas": [3]}, h={"valor": "1", "citas": [4]})
    ctx["poner"](_propuesta(ctx["sha"], [el]))
    r = ctx["importar"]()
    d = json.loads(_sql("SELECT datos_diseno_json FROM elementos_diseno WHERE id_elemento = 'C1'")[0]["datos_diseno_json"])
    assert d["b"] == "pendiente de verificar" and d["h"] == "pendiente de verificar"
    textos = [x["descripcion_pregunta"] for x in _dudas_ia(ctx["pid"])]
    assert any("propuso '0.65' pero el texto citado dice '0.60'" in t for t in textos)
    assert any("propuso '1'" in t for t in textos)
    assert r["dudas_abiertas"] == len(_dudas_ia(ctx["pid"]))
    _sin_confirmados(ctx["pid"])


def test_rechazos_no_escriben_en_la_bd(ctx):  # SINTÉTICO
    antes = _conteos()
    ctx["poner"](_propuesta("0" * 64, [_columna()]), _textos("0" * 64))  # plano cambiado
    r = ctx["importar"]()
    assert r["estado"] == "rechazada" and "sha256" in r["motivo"]
    mala = _propuesta(ctx["sha"], [_columna()])
    mala["elementos"][0]["id_elemento"]["citas"] = [999]
    ctx["poner"](mala)
    r = ctx["importar"]()
    assert r["estado"] == "rechazada" and "999" in r["motivo"]
    assert _conteos() == antes
    assert json.loads((ctx["carpeta"] / "importacion.json").read_text(encoding="utf-8"))["estado"] == "rechazada"


def test_importar_dos_veces_es_idempotente(ctx):  # SINTÉTICO
    el = _columna(b={"valor": "0.65", "citas": [3]})
    ctx["poner"](_propuesta(ctx["sha"], [el], dudas_hoja=[{"texto": "nota", "citas": [11]}]))
    ctx["importar"]()
    antes = _conteos()
    r = ctx["importar"]()
    assert r["sin_cambios"] == 1 and r["nuevo"] == 0 and r["dudas_abiertas"] == 0
    assert _conteos()["elementos_diseno"] == antes["elementos_diseno"]
    assert _conteos()["dudas_y_hallazgos"] == antes["dudas_y_hallazgos"]


def _losa(ejes=None):
    return {"tipo_elemento": "LOSA", "zona": [1, 2, 3, 4], "id_elemento": {"valor": "L1", "citas": [10]},
            "nivel_rango": {"valor": "NIVEL 2", "citas": [9]},
            "ejes": ejes or {"valor": None, "duda": "Las losas llevan —."},
            "campos": {"H": {"valor": "0.25", "citas": [7]}}, "enlaces": [], "dudas": []}


def _con_t6n(ctx):
    _extraer(ctx["c"], ctx["pid"])
    f = _elementos(ctx["pid"])[("L1", "NIVEL 2")]
    assert json.loads(f["fuente_json"])["extractor"] == "T6n"
    return f


def test_losa_contra_fila_t6n_que_coincide_suma_comprobacion(ctx):  # SINTÉTICO
    f = _con_t6n(ctx)
    assert json.loads(f["datos_diseno_json"])["H"] == "0.25"
    ctx["poner"](_propuesta(ctx["sha"], [_losa()]))
    antes = _sql("SELECT * FROM elementos_diseno WHERE id_elemento = 'L1'")
    r = ctx["importar"]()
    assert r["comprobaciones"] == 1 and r["nuevo"] == r["actualizado"] == r["sin_cambios"] == 0
    assert _sql("SELECT * FROM elementos_diseno WHERE id_elemento = 'L1'") == antes
    assert not [d for d in _dudas_ia(ctx["pid"]) if "doble_lectura" in d["campo_afectado"]]


def test_losa_contra_fila_t6n_que_difiere_abre_duda(ctx):  # SINTÉTICO
    _con_t6n(ctx)
    el = _losa()
    textos = _textos(ctx["sha"])
    textos["textos"][6]["texto"] = "0.250"  # el plano dice 0.250, T6n guardó 0.25
    el["campos"]["H"] = {"valor": "0.250", "citas": [7]}
    ctx["poner"](_propuesta(ctx["sha"], [el]), textos)
    antes = _sql("SELECT * FROM elementos_diseno WHERE id_elemento = 'L1'")
    r = ctx["importar"]()
    assert r["comprobaciones"] == 0
    assert _sql("SELECT * FROM elementos_diseno WHERE id_elemento = 'L1'") == antes
    d = [x for x in _dudas_ia(ctx["pid"]) if "doble_lectura.H" in x["campo_afectado"]]
    assert len(d) == 1 and d[0]["categoria"] == "DUDA_BLOQUEANTE" and "'0.25'" in d[0]["descripcion_pregunta"]


def test_losa_con_ejes_se_guarda_con_guion(ctx):  # SINTÉTICO
    ctx["poner"](_propuesta(ctx["sha"], [_losa({"valor": "EJE A-1", "citas": [8]})]))
    assert ctx["importar"]()["nuevo"] == 1
    assert _sql("SELECT ejes FROM elementos_diseno WHERE id_elemento = 'L1'")[0]["ejes"] == "—"
    _sin_confirmados(ctx["pid"])


def test_columna_con_ejes_null_queda_pendiente_con_duda(ctx):  # SINTÉTICO
    ctx["poner"](_propuesta(ctx["sha"], [_columna()]))
    ctx["importar"]()
    assert _sql("SELECT ejes FROM elementos_diseno WHERE id_elemento = 'C1'")[0]["ejes"] == "pendiente de verificar"
    assert any("D11" in d["descripcion_pregunta"] for d in _dudas_ia(ctx["pid"]))


def test_dudas_de_hoja_enlaces_y_dudas_del_elemento(ctx):  # SINTÉTICO
    el = _columna()
    el["enlaces"] = [{"de": "S-2", "a": "SECCION 2-2'", "citas": [1]}]
    el["dudas"] = ["contradicción planta/detalle"]
    ctx["poner"](_propuesta(ctx["sha"], [el], dudas_hoja=[{"texto": "Nota de modificación", "citas": [11]}]))
    ctx["importar"]()
    d = _dudas_ia(ctx["pid"])
    assert all(x["categoria"] == "DUDA_BLOQUEANTE" and x["campo_afectado"].startswith("IA:p14.") for x in d)
    campos = [x["campo_afectado"] for x in d]
    assert "IA:p14.dudas_hoja[0]" in campos and "IA:p14.elementos[0].enlaces[0]" in campos
    assert "IA:p14.elementos[0].dudas[0]" in campos
    assert len(set(campos)) == len(campos)


def test_sin_id_no_se_escribe_el_elemento(ctx):  # SINTÉTICO
    el = _columna()
    el["id_elemento"] = {"valor": None, "duda": "Ilegible."}
    ctx["poner"](_propuesta(ctx["sha"], [el]))
    r = ctx["importar"]()
    assert r["estado"] == "importada" and r["nuevo"] == 0
    assert _sql("SELECT * FROM elementos_diseno WHERE id_elemento = 'C1'") == []
    assert _dudas_ia(ctx["pid"])


def test_choque_con_fila_manual_abre_duda(ctx):  # SINTÉTICO
    conn = database.get_connection()
    conn.execute("""INSERT INTO elementos_diseno (uid, proyecto_id, id_elemento, tipo_elemento, nivel_rango, ejes,
                    hoja_plano_origen, archivo_plano_origen, datos_diseno_json, estado_campos_json, actualizado)
                    VALUES ('m-1', ?, 'C1', 'COLUMNA', 'FUNDACIONES @ E-3', 'pendiente de verificar', '1', 'x.pdf',
                    '{}', '{}', 'x')""", (ctx["pid"],))
    conn.commit()
    conn.close()
    ctx["poner"](_propuesta(ctx["sha"], [_columna()]))
    r = ctx["importar"]()
    assert r["choque"] == 1 and r["nuevo"] == 0
    assert any("m-1" in d["descripcion_pregunta"] for d in _dudas_ia(ctx["pid"]))


# ---------- Condiciones del Director (19/11): losa duplicada y campos descartados ----------

def _losa_con_nivel(ctx, texto_nivel, campos=None):
    textos = _textos(ctx["sha"])
    textos["textos"][8]["texto"] = texto_nivel  # n=9 es el nivel
    el = _losa()
    el["nivel_rango"] = {"valor": texto_nivel, "citas": [9]}
    if campos:
        el["campos"].update(campos)
    ctx["poner"](_propuesta(ctx["sha"], [el]), textos)


def test_losa_con_nivel_escrito_distinto_no_se_duplica(ctx):  # SINTÉTICO
    _con_t6n(ctx)
    antes = _sql("SELECT * FROM elementos_diseno WHERE id_elemento = 'L1'")
    _losa_con_nivel(ctx, "PLANTA ESTRUCTURAL DE  Nivel 2")
    r = ctx["importar"]()
    assert r["nuevo"] == 0 and r["comprobaciones"] == 1
    assert _sql("SELECT * FROM elementos_diseno WHERE id_elemento = 'L1'") == antes
    assert [d for d in _dudas_ia(ctx["pid"]) if "nivel_distinto" in d["campo_afectado"]]


def test_losa_en_nivel_que_t6n_no_tiene_abre_duda_y_no_crea_otra(ctx):  # SINTÉTICO
    _con_t6n(ctx)
    antes = _sql("SELECT * FROM elementos_diseno WHERE id_elemento = 'L1'")
    _losa_con_nivel(ctx, "NIVEL 3")
    r = ctx["importar"]()
    assert r["nuevo"] == 0 and r["descartados"] == 1
    assert _sql("SELECT * FROM elementos_diseno WHERE id_elemento = 'L1'") == antes
    assert [d for d in _dudas_ia(ctx["pid"]) if "posible_duplicado" in d["campo_afectado"]]
    guardado = json.loads((ctx["carpeta"] / "importacion.json").read_text(encoding="utf-8"))
    assert guardado["descartados_detalle"] == [{"elemento": 0, "id_elemento": "L1", "campo": "H", "valor": "0.25",
                                                 "motivo": "posible losa duplicada de una fila T6n"}]


def test_campo_que_t6n_no_tiene_se_cuenta_como_descartado(ctx):  # SINTÉTICO
    _con_t6n(ctx)
    _losa_con_nivel(ctx, "NIVEL 2", {"Bw9": {"valor": "0.60", "citas": [3]}})
    r = ctx["importar"]()
    assert r["comprobaciones"] == 1 and r["descartados"] == 1
    assert r["descartados_detalle"][0]["campo"] == "Bw9" and r["descartados_detalle"][0]["valor"] == "0.60"


def test_losa_sin_fila_t6n_entra_nueva(ctx):  # SINTÉTICO
    _losa_con_nivel(ctx, "NIVEL 3")
    assert ctx["importar"]()["nuevo"] == 1


# ---------- Evidencias (§5.1, A3d) ----------

def _textos_con_hoja(sha, extra=()):
    t = _textos(sha)
    t["ancho_pt"], t["alto_pt"] = 1000, 800
    for k, (texto, bbox) in enumerate(extra, len(t["textos"]) + 1):
        t["textos"].append({"n": k, "texto": texto, "bbox": bbox, "tam": 8})
    return t


def _fuente_de(campo, id_elemento="C1"):
    f = _sql("SELECT fuente_json FROM elementos_diseno WHERE id_elemento = ?", id_elemento)[0]["fuente_json"]
    return json.loads(f)["valores"][campo]


def test_zona_escribe_el_valor_y_abre_la_duda_de_revision_visual(ctx):  # SINTÉTICO
    el = _columna(h={"valor": "1.50", "evidencia": "zona", "zona": [10, 10, 100, 50]})
    ctx["poner"](_propuesta(ctx["sha"], [el]), _textos_con_hoja(ctx["sha"]))
    r = ctx["importar"]()
    assert r["nuevo"] == 1
    f = _sql("SELECT * FROM elementos_diseno WHERE id_elemento = 'C1'")[0]
    assert json.loads(f["datos_diseno_json"])["h"] == "1.50"
    assert json.loads(f["estado_campos_json"])["datos_diseno.h"] == "pendiente_de_verificar"
    fuente = _fuente_de("h")
    assert fuente["evidencia"] == "zona" and fuente["zona"] == [10, 10, 100, 50] and fuente["lectura"] == "1.50"
    visual = [d for d in _dudas_ia(ctx["pid"]) if d["descripcion_pregunta"].startswith("IA: revisión visual: ")]
    assert len(visual) == 1 and visual[0]["campo_afectado"] == "IA:p14.elementos[0].campos.h"
    _sin_confirmados(ctx["pid"])


def test_zona_fuera_de_la_hoja_queda_pendiente_sin_valor(ctx):  # SINTÉTICO
    el = _columna(h={"valor": "1.50", "evidencia": "zona", "zona": [10, 10, 5000, 50]})
    ctx["poner"](_propuesta(ctx["sha"], [el]), _textos_con_hoja(ctx["sha"]))
    ctx["importar"]()
    assert json.loads(_sql("SELECT datos_diseno_json FROM elementos_diseno")[0]["datos_diseno_json"])["h"] == "pendiente de verificar"
    assert not [d for d in _dudas_ia(ctx["pid"]) if "revisión visual" in d["descripcion_pregunta"]]


def test_conversion_guarda_la_regla_y_las_entradas_en_la_fuente(ctx):  # SINTÉTICO
    el = _columna(h={"evidencia": "conversion", "valor": "1.25",
                     "conversion": {"regla": "cm_a_m", "entradas": [{"valor": "125cm", "citas": [12]}]}})
    ctx["poner"](_propuesta(ctx["sha"], [el]), _textos_con_hoja(ctx["sha"], [("125cm", [300, 300, 340, 310])]))
    r = ctx["importar"]()
    assert r["nuevo"] == 1
    assert json.loads(_sql("SELECT datos_diseno_json FROM elementos_diseno")[0]["datos_diseno_json"])["h"] == "1.25"
    f = _fuente_de("h")
    assert f["evidencia"] == "conversion" and f["regla"] == "cm_a_m"
    assert f["entradas"][0]["literal"] == "125cm" and f["entradas"][0]["citas"] == [12]
    assert f["bbox"] == [300, 300, 340, 310]
    _sin_confirmados(ctx["pid"])


def test_conversion_con_valor_distinto_queda_pendiente_con_duda(ctx):  # SINTÉTICO
    el = _columna(h={"evidencia": "conversion", "valor": "1.30",
                     "conversion": {"regla": "cm_a_m", "entradas": [{"valor": "125cm", "citas": [12]}]}})
    ctx["poner"](_propuesta(ctx["sha"], [el]), _textos_con_hoja(ctx["sha"], [("125cm", [300, 300, 340, 310])]))
    ctx["importar"]()
    assert json.loads(_sql("SELECT datos_diseno_json FROM elementos_diseno")[0]["datos_diseno_json"])["h"] == "pendiente de verificar"
    assert any("la regla 'cm_a_m' da '1.25'" in d["descripcion_pregunta"] for d in _dudas_ia(ctx["pid"]))


def test_partes_se_guardan_con_cada_parte(ctx):  # SINTÉTICO
    el = _columna(estribos={"valor": '9 EST. ∅3/8" @0.10', "evidencia": "partes", "partes": [
        {"valor": '9 EST. ∅3/8"', "citas": [5]}, {"valor": "@0.10", "citas": [6]}]})
    ctx["poner"](_propuesta(ctx["sha"], [el]))
    ctx["importar"]()
    f = _fuente_de("estribos")
    assert f["evidencia"] == "partes" and [p["citas"] for p in f["partes"]] == [[5], [6]]


def test_el_lector_va_en_la_fuente_de_cada_valor(ctx):  # SINTÉTICO
    ctx["poner"](_propuesta(ctx["sha"], [_columna()]))
    ctx["importar"]()
    for campo in ("b", "acero_longitudinal", "estribos"):
        assert _fuente_de(campo)["lector"] == "claude-code"


def test_con_evidencias_importar_dos_veces_no_cambia_nada(ctx):  # SINTÉTICO
    el = _columna(h={"valor": "1.50", "evidencia": "zona", "zona": [10, 10, 100, 50]},
                  s={"evidencia": "conversion", "conversion": {"regla": "cm_a_m", "entradas": [{"valor": "125cm", "citas": [12]}]}})
    ctx["poner"](_propuesta(ctx["sha"], [el]), _textos_con_hoja(ctx["sha"], [("125cm", [300, 300, 340, 310])]))
    ctx["importar"]()
    antes = (_conteos(), _sql("SELECT * FROM elementos_diseno"))
    r = ctx["importar"]()
    assert r["sin_cambios"] == 1 and r["dudas_abiertas"] == 0
    assert (_conteos(), _sql("SELECT * FROM elementos_diseno"))[1] == antes[1]
    assert _conteos()["dudas_y_hallazgos"] == antes[0]["dudas_y_hallazgos"]


def test_zona_o_conversion_en_el_id_rechaza_la_hoja_sin_escribir(ctx):  # SINTÉTICO
    el = _columna()
    el["id_elemento"] = {"valor": "C1", "evidencia": "zona", "zona": [1, 2, 3, 4]}
    antes = _conteos()
    ctx["poner"](_propuesta(ctx["sha"], [el]), _textos_con_hoja(ctx["sha"]))
    r = ctx["importar"]()
    assert r["estado"] == "rechazada" and _conteos() == antes
