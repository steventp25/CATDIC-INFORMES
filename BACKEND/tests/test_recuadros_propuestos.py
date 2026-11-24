# BACKEND/tests/test_recuadros_propuestos.py
# Etapa 7 · T8 — Recuadros propuestos de DETALLE (zona de propuesta.json) y LOCALIZACION (planta). Todo SINTÉTICO:
# el vectorial se genera aquí con PyMuPDF; no se usa ningún dato ni PDF real.
import json

import pymupdf
import pytest
from fastapi.testclient import TestClient

import config
import database
import main
import visor
from plano import recuadros_propuestos as rp
from reglas_ingenieria import PENDIENTE


def _vectorial() -> bytes:
    doc = pymupdf.open()
    p = doc.new_page(width=1000, height=800)               # hoja 05: planta del sótano S2
    p.insert_text((940, 770), "05", fontsize=14)
    p.insert_text((958, 770), "/36", fontsize=14)
    p.insert_text((60, 770), "PLANTA ESTRUCTURAL DE SOTANO S2", fontsize=15)
    p.insert_text((305, 305), "C1", fontsize=8)             # único en la planta
    p.insert_text((500, 200), "C5", fontsize=8)
    p.insert_text((700, 600), "C5", fontsize=8)             # repetido: ambiguo
    p = doc.new_page(width=1000, height=800)               # hoja 06: otra planta
    p.insert_text((940, 770), "06", fontsize=14)
    p.insert_text((958, 770), "/36", fontsize=14)
    p.insert_text((60, 770), "PLANTA ESTRUCTURAL DE SOTANO S1", fontsize=15)
    datos = doc.tobytes()
    doc.close()
    return datos


def _sellado() -> bytes:
    doc = pymupdf.open()
    doc.new_page(width=300, height=200)
    datos = doc.tobytes()
    doc.close()
    return datos


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    (tmp_path / "bd").mkdir()
    monkeypatch.setenv(config.ENV_DB_PATH, str(tmp_path / "bd" / "prueba.db"))
    monkeypatch.setenv(config.ENV_DROPBOX_RAIZ, str(tmp_path / "dropbox"))
    monkeypatch.setenv(config.ENV_DATOS_RAIZ, str(tmp_path / "datos"))
    monkeypatch.setenv(config.ENV_CACHE_RAIZ, str(tmp_path / "cache"))
    database.inicializar_bd()
    visor._indices.clear()
    with TestClient(main.app) as c:
        pid = c.post("/api/proyectos", json={"nombre": "Obra T8"}).json()["proyecto"]["id"]
        r = c.post(f"/api/proyectos/{pid}/planos", files={"vectorial": ("vec.pdf", _vectorial(), "application/pdf"),
                                                           "sellado": ("sel.pdf", _sellado(), "application/pdf")},
                   data={"certifico": "true"})
        assert r.status_code == 201, r.text
        yield pid, tmp_path


def _sha(pid):
    conn = database.get_connection()
    try:
        return conn.execute("SELECT vectorial_sha256 FROM planos WHERE proyecto_id = ?", (pid,)).fetchone()[0]
    finally:
        conn.close()


def _elemento(pid, uid, id_elemento, nivel="SOTANO S - 2", tipo="COLUMNA", ejes=PENDIENTE):
    conn = database.get_connection()
    plano_id = conn.execute("SELECT id FROM planos WHERE proyecto_id = ?", (pid,)).fetchone()[0]
    conn.execute("""INSERT INTO elementos_diseno (uid, proyecto_id, id_elemento, tipo_elemento, nivel_rango, ejes,
                    hoja_plano_origen, archivo_plano_origen, datos_diseno_json, estado_campos_json, actualizado, plano_id)
                    VALUES (?, ?, ?, ?, ?, ?, '05', 'vec.pdf', '{}', '{}', 'x', ?)""",
                 (uid, pid, id_elemento, tipo, nivel, ejes, plano_id))
    conn.commit()
    conn.close()


def _columna(uid: str, col: str):
    conn = database.get_connection()
    try:
        return json.loads(conn.execute(f"SELECT {col} FROM elementos_diseno WHERE uid = ?", (uid,)).fetchone()[0] or "{}")
    finally:
        conn.close()


def _propuesta(tmp_path, pid, elementos, pagina=1, sha=None, nombre="p01"):
    carpeta = tmp_path / "lote" / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / "propuesta.json"
    ruta.write_text(json.dumps({"version": 1, "archivo": "vec.pdf", "sha256": sha or _sha(pid), "pagina": pagina,
                                "hoja": "05", "lector": "prueba", "elementos": elementos}), encoding="utf-8")
    return ruta


def _el(id_, nivel="SOTANO S - 2", zona="falta"):
    e = {"tipo_elemento": "COLUMNA", "id_elemento": {"valor": id_, "citas": [1]}, "nivel_rango": {"valor": nivel, "citas": [2]}}
    if zona != "falta":
        e["zona"] = zona
    return e


def _no(r, id_, recuadro):
    return [n for n in r["no_propuestos"] if n["id_elemento"] == id_ and n["recuadro"] == recuadro]


# ---------- DETALLE: zona presente, ausente e inválida ----------

def test_zona_presente_se_guarda_pendiente_con_su_cita(entorno):
    pid, tmp = entorno
    _elemento(pid, "u1", "C1")
    ruta = _propuesta(tmp, pid, [_el("C1", zona=[100, 60, 720, 600])])
    r = rp.proponer_desde_propuestas(pid, [ruta])
    assert r["escrito"] and [p["recuadro"] for p in r["propuestos"]] == ["detalle"]
    d = _columna("u1", "recorte_detalle_json")
    assert d["estado"] == PENDIENTE and d["estado"] != "confirmado"
    assert d["rect"] == [100.0, 60.0, 720.0, 600.0] and d["pagina"] == 1
    assert d["plano_id"] == _columna_plano(pid)
    assert d["fuente"]["archivo"] == "propuesta.json" and d["fuente"]["pagina"] == 1
    assert _columna("u1", "recorte_planta_json") == {}


def _columna_plano(pid):
    conn = database.get_connection()
    try:
        return conn.execute("SELECT id FROM planos WHERE proyecto_id = ?", (pid,)).fetchone()[0]
    finally:
        conn.close()


def test_zona_ausente_no_propone_y_lo_anota(entorno):
    pid, tmp = entorno
    _elemento(pid, "u1", "C1")
    r = rp.proponer_desde_propuestas(pid, [_propuesta(tmp, pid, [_el("C1")])])
    assert r["propuestos"] == [] and not r["escrito"] and r["respaldo"] is None
    assert "no trae 'zona'" in _no(r, "C1", "detalle")[0]["motivo"]
    assert _columna("u1", "recorte_detalle_json") == {}


@pytest.mark.parametrize("zona", [
    [10, 10, 5, 50],                      # x0 >= x1
    [10, 10, 50, 10],                     # y0 >= y1
    [-5, 10, 50, 60],                     # fuera de la hoja por la izquierda
    [10, 10, 1200, 60],                   # fuera de la hoja por la derecha (hoja de 1000 pt)
    [10, 10, 12, 60],                     # lado menor al mínimo
    [10, 10, 50],                         # no son 4 números
    ["a", 10, 50, 60],                    # texto
    [True, 10, 50, 60],                   # booleano
    [float("nan"), 10, 50, 60],           # NaN
    "10,10,50,60",                        # ni siquiera es lista
])
def test_zona_invalida_no_se_propone(entorno, zona):
    pid, tmp = entorno
    _elemento(pid, "u1", "C1")
    r = rp.proponer_desde_propuestas(pid, [_propuesta(tmp, pid, [_el("C1", zona=zona)])])
    assert r["propuestos"] == [] and not r["escrito"]
    assert _no(r, "C1", "detalle") and _columna("u1", "recorte_detalle_json") == {}


def test_propuesta_de_otro_pdf_no_se_propone(entorno):
    pid, tmp = entorno
    _elemento(pid, "u1", "C1")
    r = rp.proponer_desde_propuestas(pid, [_propuesta(tmp, pid, [_el("C1", zona=[10, 10, 50, 60])], sha="0" * 64)])
    assert r["propuestos"] == [] and "otro PDF" in _no(r, "C1", "detalle")[0]["motivo"]
    assert _columna("u1", "recorte_detalle_json") == {}


def test_elemento_no_importado_o_con_otro_nivel_no_se_propone(entorno):
    pid, tmp = entorno
    _elemento(pid, "u1", "C1", nivel="E-3 @ E-8")
    r = rp.proponer_desde_propuestas(pid, [_propuesta(tmp, pid, [_el("C1", zona=[10, 10, 50, 60]), _el("C9", zona=[10, 10, 50, 60])])])
    assert r["propuestos"] == []
    assert len(_no(r, "C1", "detalle")) == 1 and len(_no(r, "C9", "detalle")) == 1


def test_acepta_una_carpeta_con_pNN(entorno):
    pid, tmp = entorno
    _elemento(pid, "u1", "C1")
    _propuesta(tmp, pid, [_el("C1", zona=[100, 60, 720, 600])])
    r = rp.proponer_desde_propuestas(pid, tmp / "lote")
    assert len(r["propuestos"]) == 1


# ---------- Recuadro confirmado: no se pisa ----------

def test_un_recuadro_confirmado_no_se_pisa(entorno):
    pid, tmp = entorno
    _elemento(pid, "u1", "C1")
    visor.guardar_recuadro(pid, "u1", "detalle", 1, [10, 10, 200, 200], "dibujado")
    visor.guardar_recuadro(pid, "u1", "localizacion", 1, [10, 10, 300, 300], "dibujado")
    antes = (_columna("u1", "recorte_detalle_json"), _columna("u1", "recorte_planta_json"))
    assert antes[0]["estado"] == "confirmado"
    ruta = _propuesta(tmp, pid, [_el("C1", zona=[100, 60, 720, 600])])
    r = rp.proponer_desde_propuestas(pid, [ruta], paginas_planta=[1])
    assert r["propuestos"] == [] and not r["escrito"] and r["respaldo"] is None
    assert "CONFIRMADO" in _no(r, "C1", "detalle")[0]["motivo"] and "CONFIRMADO" in _no(r, "C1", "localizacion")[0]["motivo"]
    assert (_columna("u1", "recorte_detalle_json"), _columna("u1", "recorte_planta_json")) == antes


def test_un_recuadro_ajeno_sin_estado_tampoco_se_pisa_pero_una_propuesta_nuestra_se_renueva(entorno):
    pid, tmp = entorno
    _elemento(pid, "u1", "C1")
    conn = database.get_connection()
    conn.execute("UPDATE elementos_diseno SET recorte_detalle_json = ? WHERE uid = 'u1'",
                 (json.dumps({"pagina": 1, "rect": [1, 1, 50, 50]}),))
    conn.commit()
    conn.close()
    ruta = _propuesta(tmp, pid, [_el("C1", zona=[100, 60, 720, 600])])
    assert rp.proponer_desde_propuestas(pid, [ruta])["propuestos"] == []
    conn = database.get_connection()
    conn.execute("UPDATE elementos_diseno SET recorte_detalle_json = '{}' WHERE uid = 'u1'")
    conn.commit()
    conn.close()
    assert len(rp.proponer_desde_propuestas(pid, [ruta])["propuestos"]) == 1
    ruta = _propuesta(tmp, pid, [_el("C1", zona=[120, 70, 700, 590])])           # nueva propuesta: reemplaza la anterior
    assert len(rp.proponer_desde_propuestas(pid, [ruta])["propuestos"]) == 1
    assert _columna("u1", "recorte_detalle_json")["rect"] == [120.0, 70.0, 700.0, 590.0]


# ---------- LOCALIZACION ----------

def test_localizacion_con_id_unico_en_la_planta_queda_pendiente(entorno):
    pid, tmp = entorno
    _elemento(pid, "u1", "C1")                                   # 'SOTANO S - 2' == rótulo 'SOTANO S2'
    r = rp.proponer_desde_propuestas(pid, [_propuesta(tmp, pid, [_el("C1", zona=[100, 60, 720, 600])])], paginas_planta=[1])
    assert sorted(p["recuadro"] for p in r["propuestos"]) == ["detalle", "localizacion"]
    loc = _columna("u1", "recorte_planta_json")
    assert loc["estado"] == PENDIENTE and loc["pagina"] == 1 and loc["fuente"]["rotulo_planta"] == "SOTANO S2"
    x0, y0, x1, y1 = loc["rect"]
    assert x0 < 305 < x1 and y0 < 305 < y1


def test_id_ambiguo_en_la_planta_no_se_propone(entorno):
    pid, tmp = entorno
    _elemento(pid, "u1", "C5")
    r = rp.proponer_desde_propuestas(pid, [_propuesta(tmp, pid, [_el("C5", zona=[100, 60, 720, 600])])], paginas_planta=[1])
    assert [p["recuadro"] for p in r["propuestos"]] == ["detalle"]
    m = _no(r, "C5", "localizacion")[0]["motivo"]
    assert "2 veces" in m and "no se adivina" in m
    assert _columna("u1", "recorte_planta_json") == {}


def test_nivel_que_no_coincide_con_la_planta_exige_equivalencia_dada(entorno):
    pid, tmp = entorno
    _elemento(pid, "u1", "C1", nivel="E-3 @ E-8")
    ruta = _propuesta(tmp, pid, [_el("C1", nivel="E-3 @ E-8", zona=[100, 60, 720, 600])])
    r = rp.proponer_desde_propuestas(pid, [ruta], paginas_planta=[1])
    assert [p["recuadro"] for p in r["propuestos"]] == ["detalle"] and "equivalencia" in _no(r, "C1", "localizacion")[0]["motivo"]
    r = rp.proponer_desde_propuestas(pid, [ruta], paginas_planta=[1], equivalencias={"SOTANO S-2": ["E-3 @ E-8"]})
    assert "localizacion" in [p["recuadro"] for p in r["propuestos"]]


def test_pagina_sin_titulo_de_planta_no_propone_localizacion(entorno):
    pid, tmp = entorno
    _elemento(pid, "u1", "C1")
    r = rp.proponer_desde_propuestas(pid, [_propuesta(tmp, pid, [_el("C1", zona=[100, 60, 720, 600])])], paginas_planta=[9])
    assert "no existe" in _no(r, "C1", "localizacion")[0]["motivo"] and _columna("u1", "recorte_planta_json") == {}


# ---------- Nunca confirmado, en seco, respaldo y auditoría ----------

def test_nunca_se_escribe_confirmado_y_queda_respaldo_y_auditoria(entorno):
    pid, tmp = entorno
    for uid, id_ in (("u1", "C1"), ("u2", "C5")):
        _elemento(pid, uid, id_)
    ruta = _propuesta(tmp, pid, [_el("C1", zona=[100, 60, 720, 600]), _el("C5", zona=[10, 10, 90, 90])])
    r = rp.proponer_desde_propuestas(pid, [ruta], paginas_planta=[1])
    assert r["escrito"] and r["respaldo"] and (tmp / "bd").joinpath(r["respaldo"].split("\\")[-1].split("/")[-1]).is_file()
    for uid in ("u1", "u2"):
        for col in ("recorte_detalle_json", "recorte_planta_json"):
            assert _columna(uid, col).get("estado", PENDIENTE) != "confirmado"
    conn = database.get_connection()
    filas = conn.execute("SELECT accion, detalle_json FROM auditoria WHERE accion = 'PROPONER_RECUADRO'").fetchall()
    conn.close()
    assert len(filas) == len(r["propuestos"]) == 3
    assert all(json.loads(f["detalle_json"])["nuevo"]["estado"] == PENDIENTE for f in filas)


def test_en_seco_no_escribe_ni_respalda_ni_audita(entorno):
    pid, tmp = entorno
    _elemento(pid, "u1", "C1")
    ruta = _propuesta(tmp, pid, [_el("C1", zona=[100, 60, 720, 600])])
    r = rp.proponer_desde_propuestas(pid, [ruta], paginas_planta=[1], escribir=False)
    assert len(r["propuestos"]) == 2 and not r["escrito"] and r["respaldo"] is None
    assert _columna("u1", "recorte_detalle_json") == {} and _columna("u1", "recorte_planta_json") == {}
    conn = database.get_connection()
    assert conn.execute("SELECT COUNT(*) FROM auditoria WHERE accion = 'PROPONER_RECUADRO'").fetchone()[0] == 0
    conn.close()
    assert list((tmp / "bd").glob("*backup*")) == []


# ---------- Tabla equivalencias_nivel (T6) ----------

def test_con_la_tabla_llena_propone_la_localizacion(entorno):
    import equivalencias_nivel
    pid, tmp = entorno
    _elemento(pid, "u1", "C1", nivel="E-3 @ E-8")
    equivalencias_nivel.guardar_equivalencias(pid, [{"nivel_visita": "S-2", "rangos_impresos": ["E-3 @ E-8", "E-1 @ E-2"]}])
    ruta = _propuesta(tmp, pid, [_el("C1", nivel="E-3 @ E-8", zona=[100, 60, 720, 600])])
    r = rp.proponer_desde_propuestas(pid, [ruta], paginas_planta=[1])
    assert sorted(p["recuadro"] for p in r["propuestos"]) == ["detalle", "localizacion"]
    assert _columna("u1", "recorte_planta_json")["estado"] == PENDIENTE


def test_con_la_tabla_vacia_o_de_otro_nivel_no_propone_y_dice_falta_equivalencia(entorno):
    import equivalencias_nivel
    pid, tmp = entorno
    _elemento(pid, "u1", "C1", nivel="E-3 @ E-8")
    ruta = _propuesta(tmp, pid, [_el("C1", nivel="E-3 @ E-8", zona=[100, 60, 720, 600])])
    r = rp.proponer_desde_propuestas(pid, [ruta], paginas_planta=[1])
    assert "falta equivalencia" in _no(r, "C1", "localizacion")[0]["motivo"]
    equivalencias_nivel.guardar_equivalencias(pid, [{"nivel_visita": "S-1", "rangos_impresos": ["E-3 @ E-8"]}])
    r = rp.proponer_desde_propuestas(pid, [ruta], paginas_planta=[1])
    assert "falta equivalencia" in _no(r, "C1", "localizacion")[0]["motivo"]
    assert _columna("u1", "recorte_planta_json") == {}
