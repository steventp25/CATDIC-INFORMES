# BACKEND/tests/test_cabecera_propuesta.py
# Etapa 7 · T7 — Cabecera propuesta desde STP entregados. PDF y datos SINTÉTICOS (nada de informes reales;
# nombres, licencias y direcciones inventados solo para probar las reglas).
import json
import sqlite3
from pathlib import Path

import pymupdf
import pytest
from fastapi.testclient import TestClient

import config
import database
import main
from reglas_ingenieria import PENDIENTE
from sync import cabecera_propuesta as cp

PID = "obra-sint"
DIR_CATDIC = "CALLE PROYECTO NO.10, ARROYO HONDO VIEJO, SANTO DOMINGO D.N."
BASE = {"no_solicitud": "SOL-0001", "no_licencia": "LIC-0001", "provincia": "PROV SINT", "sector": "SECTOR SINT",
        "direccion_obra": "CALLE SINT 1, CIUDAD", "residente_obra": "RESIDENTE SINT CODIA 00000"}


def _hoja(pagina, v):
    """Imita la hoja de inspección: rótulos en x=33, valores en x=182, rótulos de la columna derecha en x=282."""
    def t(x, y, s):
        pagina.insert_text((x, y + 8), s, fontsize=8)
    t(33, 36, "No. DE LA INSPECCION :")
    t(282, 36, "NUMERO DE FORMULARIO :")
    t(33, 53, "FECHA DE LA INSPECCION :")
    t(182, 53, "01/01/2026")
    t(282, 53, "FECHA DEL INFORME :")
    t(33, 84, "NOMBRE DEL PROYECTO :")
    t(182, 84, "OBRA SINTETICA")
    filas = [(101, "NO. SOLICITUD :", "no_solicitud"), (117, "LICENCIA :", "no_licencia"),
             (134, "INICIO DE OBRA :", None), (150, "PROVINCIA :", "provincia"), (167, "SECTOR :", "sector"),
             (183, "DIRECCION :", "direccion_obra")]
    for y, rot, campo in filas:
        t(33, y, rot)
        if campo and v.get(campo):
            t(182, y, v[campo])
    t(33, 200, "NIVEL/ELEMENTOS A INSPECCIONAR:")
    t(182, 200, "VERTICALES SOTANO S1 - PARCIAL")
    t(33, 215, "NOMBRE Y COLEGIATURA DEL RESIDENTE DE")
    t(33, 225, "OBRA :")
    if v.get("residente_obra"):
        t(182, 220, v["residente_obra"])
    t(33, 240, "SUPERVISOR :")
    t(235, 278, "OBSERVACIONES DURANTE LA INSPECCION")
    t(40, 310, "SE VERIFICO EL ARMADO. DIRECCION : texto suelto de observaciones")


def _pdf(ruta, **cambios):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    v = {**BASE, **cambios}
    doc = pymupdf.open()
    doc.new_page().insert_text((100, 100), "Portada")
    _hoja(doc.new_page(), v)
    doc.save(str(ruta))
    doc.close()
    return ruta


def _bd():
    conn = sqlite3.connect(config.obtener_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _dir_bd() -> Path:
    return Path(config.obtener_db_path()).parent


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    for n in ("bd", "informes"):
        (tmp_path / n).mkdir()
    monkeypatch.setenv(config.ENV_DB_PATH, str(tmp_path / "bd" / "prueba.db"))
    monkeypatch.delenv(config.ENV_DROPBOX_RAIZ, raising=False)
    database.inicializar_bd()
    with _bd() as conn:
        conn.execute("""INSERT INTO proyectos (id, nombre, tipo, formato_defecto, carpeta_dropbox, carpeta_salida,
                        actualizado) VALUES (?, 'Obra Sintetica', 'Supervisión', 'STP-MIVED', ?, 'informes', 'x')""",
                     (PID, str(tmp_path)))
    return tmp_path / "informes"


def _nombre(n, fecha):
    return f"{n:02d} - Obra Sintetica - STP - Verticales Sotano S{n} Parcial - {fecha}.pdf"


def _filas():
    with _bd() as conn:
        return {f["campo"]: f for f in conn.execute("SELECT * FROM propuestas_proyecto WHERE proyecto_id = ?", (PID,))}


def _n(sql, *args):
    with _bd() as conn:
        return conn.execute(sql, args).fetchone()[0]


def test_todos_coinciden_cita_archivo_y_pagina(entorno):
    _pdf(entorno / "A" / _nombre(1, "01-01-2026"))
    _pdf(entorno / "B" / _nombre(2, "02-02-2026"))
    r = cp.proponer_cabecera(PID, entorno)
    assert r["escrito"] and r["informes_leidos"] == 2
    for campo, valor in BASE.items():
        c = r["campos"][campo]
        assert c["situacion"] == "coincide" and c["valor"] == valor
        v = c["fuente"]["valores"][0]
        assert v["conteo"] == 2 and v["mas_reciente"]["archivo"].endswith("02-02-2026.pdf")
        assert {i["pagina"] for i in v["informes"]} == {2}
    filas = _filas()
    assert set(filas) == set(BASE) and all(f["estado"] == "propuesta" for f in filas.values())
    assert json.loads(filas["sector"]["fuente_json"])["valores"][0]["informes"][0]["archivo"].startswith(("A", "B"))


def test_rotulo_de_dos_lineas_toma_el_valor_de_su_fila(entorno):
    _pdf(entorno / _nombre(1, "01-01-2026"))
    r = cp.proponer_cabecera(PID, entorno, escribir=False)
    assert r["campos"]["residente_obra"]["valor"] == BASE["residente_obra"]
    assert r["campos"]["no_licencia"]["valor"] == "LIC-0001"  # no se mezcla con el rótulo de al lado


def test_discrepan_queda_en_duda_y_no_se_elige(entorno):
    _pdf(entorno / _nombre(1, "01-01-2026"))
    _pdf(entorno / _nombre(2, "02-02-2026"), sector="OTRO SECTOR")
    r = cp.proponer_cabecera(PID, entorno)
    c = r["campos"]["sector"]
    assert c["situacion"] == "discrepa" and c["valor"] == PENDIENTE
    assert {v["valor"] for v in c["fuente"]["valores"]} == {"SECTOR SINT", "OTRO SECTOR"}
    assert r["campos"]["provincia"]["situacion"] == "coincide"
    assert _filas()["sector"]["valor"] == PENDIENTE


def test_falta_el_valor_queda_pendiente(entorno):
    _pdf(entorno / _nombre(1, "01-01-2026"), residente_obra="")
    c = cp.proponer_cabecera(PID, entorno)["campos"]["residente_obra"]
    assert c["situacion"] == "pendiente" and c["valor"] == PENDIENTE


def test_falta_la_hoja_no_inventa(entorno):
    ruta = entorno / _nombre(1, "01-01-2026")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open()
    doc.new_page().insert_text((100, 100), "Portada sin hoja de inspeccion")
    doc.save(str(ruta))
    doc.close()
    r = cp.proponer_cabecera(PID, entorno)
    assert r["informes_leidos"] == 0 and not r["escrito"] and r["notas"]
    assert _n("SELECT COUNT(*) FROM propuestas_proyecto") == 0  # la tabla la crea inicializar_bd (T9); no se escribió nada


def test_falta_el_rotulo_queda_pendiente(entorno):
    ruta = entorno / _nombre(1, "01-01-2026")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open()
    pg = doc.new_page()
    for y, s in ((84, "NOMBRE DEL PROYECTO :"), (101, "NO. SOLICITUD :")):
        pg.insert_text((33, y + 8), s, fontsize=8)
    pg.insert_text((182, 101 + 8), "SOL-0009", fontsize=8)
    doc.save(str(ruta))
    doc.close()
    r = cp.proponer_cabecera(PID, entorno, escribir=False)
    assert r["campos"]["no_solicitud"]["valor"] == "SOL-0009"
    assert r["campos"]["sector"]["situacion"] == "pendiente"


def test_un_informe_sin_el_campo_no_contradice_a_otro_que_si_lo_trae(entorno):
    _pdf(entorno / _nombre(1, "01-01-2026"), provincia="")
    _pdf(entorno / _nombre(2, "02-02-2026"))
    c = cp.proponer_cabecera(PID, entorno)["campos"]["provincia"]
    assert c["situacion"] == "coincide" and c["valor"] == "PROV SINT" and len(c["fuente"]["informes_sin_valor"]) == 1


def test_excluye_versiones_anteriores_y_otros_pdf(entorno):
    _pdf(entorno / "S1" / _nombre(1, "01-01-2026"))
    viejo = _pdf(entorno / "S1" / "VERSIONES ANTERIORES" / _nombre(2, "02-02-2026"), sector="SECTOR VIEJO")
    _pdf(entorno / "S1" / "Otro documento.pdf", sector="NO ES STP")
    r = cp.proponer_cabecera(PID, entorno)
    assert r["informes_encontrados"] == 1
    assert r["campos"]["sector"]["situacion"] == "coincide" and r["campos"]["sector"]["valor"] == "SECTOR SINT"
    assert cp.listar_stp([viejo]) == []


def test_descarta_la_direccion_de_catdic(entorno):
    _pdf(entorno / _nombre(1, "01-01-2026"), direccion_obra=DIR_CATDIC)
    c = cp.proponer_cabecera(PID, entorno)["campos"]["direccion_obra"]
    assert c["situacion"] == "pendiente" and c["valor"] == PENDIENTE
    assert any("CATDIC" in n for n in c["fuente"]["notas"])
    assert "ARROYO" not in _filas()["direccion_obra"]["valor"].upper()


def test_acepta_lista_de_pdf_y_en_seco_no_escribe(entorno):
    a = _pdf(entorno / _nombre(1, "01-01-2026"))
    r = cp.proponer_cabecera(PID, [a], escribir=False)
    assert r["informes_leidos"] == 1 and not r["escrito"]
    assert _n("SELECT COUNT(*) FROM propuestas_proyecto") == 0  # la tabla la crea inicializar_bd (T9); no se escribió nada
    assert _n("SELECT COUNT(*) FROM auditoria WHERE modulo = ?", cp.MODULO_AUDITORIA) == 0


def test_no_toca_proyectos_pero_si_deja_duda_auditoria_y_respaldo(entorno):
    _pdf(entorno / _nombre(1, "01-01-2026"))
    with _bd() as conn:
        antes = tuple(conn.execute("SELECT * FROM proyectos WHERE id = ?", (PID,)).fetchone())
    r = cp.proponer_cabecera(PID, entorno)
    with _bd() as conn:
        assert tuple(conn.execute("SELECT * FROM proyectos WHERE id = ?", (PID,)).fetchone()) == antes
        dudas = conn.execute("SELECT * FROM dudas_y_hallazgos WHERE campo_afectado = ?", (cp.CAMPO_DUDA,)).fetchall()
        assert len(dudas) == 1 and dudas[0]["visita_id"] is None and dudas[0]["resuelta"] == 0
        assert dudas[0]["descripcion_pregunta"].startswith("Cabecera propuesta desde STP entregados: confirma o corrige")
        aud = conn.execute("SELECT * FROM auditoria WHERE modulo = ?", (cp.MODULO_AUDITORIA,)).fetchall()
        assert len(aud) == 1 and aud[0]["accion"] == cp.ACCION_PROPONER
    assert (_dir_bd() / r["respaldo"]).exists()


def test_idempotente_al_repetir(entorno):
    _pdf(entorno / _nombre(1, "01-01-2026"))
    assert cp.proponer_cabecera(PID, entorno)["escrito"]
    with _bd() as conn:
        snap = [tuple(f) for f in conn.execute(
            "SELECT campo, valor, fuente_json, creado FROM propuestas_proyecto ORDER BY campo")]
    n_bd = len(list(_dir_bd().glob("*.db")))
    assert not cp.proponer_cabecera(PID, entorno)["escrito"]
    with _bd() as conn:
        assert snap == [tuple(f) for f in conn.execute(
            "SELECT campo, valor, fuente_json, creado FROM propuestas_proyecto ORDER BY campo")]
    assert _n("SELECT COUNT(*) FROM auditoria WHERE modulo = ?", cp.MODULO_AUDITORIA) == 1
    assert _n("SELECT COUNT(*) FROM dudas_y_hallazgos WHERE campo_afectado = ?", cp.CAMPO_DUDA) == 1
    assert len(list(_dir_bd().glob("*.db"))) == n_bd  # sin respaldo nuevo


def test_cambia_la_fuente_actualiza_sin_duplicar_la_duda(entorno):
    _pdf(entorno / _nombre(1, "01-01-2026"))
    cp.proponer_cabecera(PID, entorno)
    _pdf(entorno / _nombre(2, "02-02-2026"), sector="OTRO")
    assert cp.proponer_cabecera(PID, entorno)["escrito"]
    assert _filas()["sector"]["situacion"] == "discrepa"
    assert _n("SELECT COUNT(*) FROM dudas_y_hallazgos WHERE campo_afectado = ?", cp.CAMPO_DUDA) == 1


def test_propuesta_ya_confirmada_no_se_pisa(entorno):
    _pdf(entorno / _nombre(1, "01-01-2026"))
    cp.proponer_cabecera(PID, entorno)
    with _bd() as conn:
        conn.execute("UPDATE propuestas_proyecto SET estado = 'confirmada', valor = 'CORREGIDO' WHERE campo = 'sector'")
    _pdf(entorno / _nombre(2, "02-02-2026"), sector="OTRO")
    cp.proponer_cabecera(PID, entorno)
    assert _filas()["sector"]["valor"] == "CORREGIDO"


def test_proyecto_inexistente(entorno):
    with pytest.raises(cp.ErrorCabecera):
        cp.proponer_cabecera("no-existe", entorno)


def test_get_solo_lectura(entorno):
    c = TestClient(main.app)
    assert c.get(f"/api/proyectos/{PID}/cabecera-propuesta").json()["hay_propuesta"] is False
    _pdf(entorno / _nombre(1, "01-01-2026"))
    cp.proponer_cabecera(PID, entorno)
    r = c.get(f"/api/proyectos/{PID}/cabecera-propuesta").json()
    assert r["hay_propuesta"] and r["duda_abierta_id"]
    assert r["campos"]["no_licencia"]["valor"] == "LIC-0001" and r["campos"]["no_licencia"]["actual_en_proyecto"] == ""
    assert c.get("/api/proyectos/nada/cabecera-propuesta").status_code == 404
    assert c.post(f"/api/proyectos/{PID}/cabecera-propuesta").status_code == 405


def test_la_carpeta_sale_de_la_tabla_proyectos(entorno):
    _pdf(entorno / _nombre(1, "01-01-2026"))
    r = cp.proponer_cabecera(PID, escribir=False)  # sin fuente: carpeta_dropbox + carpeta_salida
    assert r["informes_leidos"] == 1
