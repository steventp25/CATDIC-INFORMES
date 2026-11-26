# BACKEND/tests/test_cabecera_proyecto.py
# Etapa 7 · T15 — Cabecera del proyecto editable (GET/PUT). Datos SINTÉTICOS, BD temporal.
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

import config
import database
import main
from sync import cabecera_propuesta as cp

PID = "obra-sint"
URL = f"/api/proyectos/{PID}/cabecera"


def _bd():
    conn = sqlite3.connect(config.obtener_db_path())
    conn.row_factory = sqlite3.Row
    return conn


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    (tmp_path / "bd").mkdir()
    monkeypatch.setenv(config.ENV_DB_PATH, str(tmp_path / "bd" / "prueba.db"))
    monkeypatch.delenv(config.ENV_DROPBOX_RAIZ, raising=False)
    database.inicializar_bd()
    with _bd() as conn:
        conn.execute("""INSERT INTO proyectos (id, nombre, tipo, formato_defecto, no_solicitud, no_licencia, sector,
                        actualizado) VALUES (?, 'Obra Sintetica', 'Supervisión', 'STP-MIVED', 'SOL-1', 'LIC-1',
                        'SECTOR A', 'x')""", (PID,))
    return TestClient(main.app)


def _auditoria():
    with _bd() as conn:
        return [(f["accion"], json.loads(f["detalle_json"])) for f in
                conn.execute("SELECT * FROM auditoria WHERE modulo = 'CABECERA' ORDER BY id")]


def test_get_devuelve_los_7_campos(cliente):
    r = cliente.get(URL)
    assert r.status_code == 200
    j = r.json()
    assert len(j["campos"]) == 7 and "codia_residente" in j["campos"]
    assert j["valores"]["no_solicitud"] == "SOL-1" and j["valores"]["codia_residente"] == ""
    assert j["propuesta"]["hay_propuesta"] is False


def test_get_incluye_la_propuesta_de_t7(cliente):
    with _bd() as conn:
        cp._asegurar_tabla(conn)
        conn.execute("""INSERT INTO propuestas_proyecto (proyecto_id, campo, valor, situacion, fuente_json, estado, creado)
                        VALUES (?, 'sector', 'SECTOR B', 'coincide', '{}', 'propuesta', 'x')""", (PID,))
    j = cliente.get(URL).json()
    assert j["propuesta"]["hay_propuesta"] and j["propuesta"]["campos"]["sector"]["valor"] == "SECTOR B"
    assert j["propuesta"]["campos"]["provincia"] is None


def test_put_un_campo_audita_anterior_y_nuevo(cliente):
    r = cliente.put(URL, json={"sector": "  SECTOR B  "}, params={"usuario": "steven"})
    assert r.status_code == 200 and r.json()["cambiados"] == ["sector"]
    assert cliente.get(URL).json()["valores"]["sector"] == "SECTOR B"
    aud = _auditoria()
    assert len(aud) == 1 and aud[0][0] == "EDITAR_CABECERA"
    assert aud[0][1]["campo"] == "sector" and aud[0][1]["anterior"] == "SECTOR A" and aud[0][1]["nuevo"] == "SECTOR B"
    with _bd() as conn:
        assert conn.execute("SELECT usuario FROM auditoria WHERE accion = 'EDITAR_CABECERA'").fetchone()[0] == "steven"


def test_put_sin_cambios_no_escribe_nada(cliente):
    cliente.get(URL)  # migra la columna una vez
    with _bd() as conn:
        antes = conn.execute("SELECT COUNT(*) FROM auditoria").fetchone()[0]
    r = cliente.put(URL, json={"sector": "SECTOR A", "no_licencia": " LIC-1 "})
    assert r.status_code == 200 and r.json()["cambiados"] == []
    with _bd() as conn:
        assert conn.execute("SELECT COUNT(*) FROM auditoria").fetchone()[0] == antes


def test_campo_desconocido_se_rechaza(cliente):
    r = cliente.put(URL, json={"sector": "X", "nombre": "otro"})
    assert r.status_code == 422 and "nombre" in r.json()["detail"]
    assert cliente.get(URL).json()["valores"]["sector"] == "SECTOR A"
    assert cliente.put(URL, json={"sector": 5}).status_code == 422


def test_vaciar_un_campo_queda_auditado(cliente):
    r = cliente.put(URL, json={"no_licencia": ""})
    assert r.status_code == 200
    assert cliente.get(URL).json()["valores"]["no_licencia"] == ""
    aud = _auditoria()
    assert aud[-1][1] == {**aud[-1][1], "campo": "no_licencia", "anterior": "LIC-1", "nuevo": ""}


def test_guardar_resuelve_la_duda_de_cabecera(cliente):
    with _bd() as conn:
        conn.execute("""INSERT INTO dudas_y_hallazgos (proyecto_id, visita_id, id_elemento, categoria, campo_afectado,
                        descripcion_pregunta, creado) VALUES (?, NULL, '(obra)', 'DUDA_BLOQUEANTE', ?, 'q', 'x')""",
                     (PID, cp.CAMPO_DUDA))
    r = cliente.put(URL, json={"provincia": "PROV X", "codia_residente": "CODIA 0"})
    assert r.status_code == 200 and r.json()["duda_resuelta_id"]
    with _bd() as conn:
        d = conn.execute("SELECT * FROM dudas_y_hallazgos").fetchone()
        assert d["resuelta"] == 1 and "provincia" in d["respuesta_usuario"] and d["resuelto_en"]
    assert [a[0] for a in _auditoria()].count("RESOLVER_DUDA_CABECERA") == 1
    assert len(_auditoria()) == 3  # 2 campos + la duda


def test_proyecto_inexistente_404(cliente):
    assert cliente.get("/api/proyectos/nada/cabecera").status_code == 404
    assert cliente.put("/api/proyectos/nada/cabecera", json={"sector": "x"}).status_code == 404


def test_inicializar_bd_migra_codia_residente_al_arrancar(tmp_path, monkeypatch):
    """Una BD vieja sin `codia_residente` la recibe al arrancar (inicializar_bd), con respaldo y auditoría."""
    (tmp_path / "bd").mkdir()
    ruta = tmp_path / "bd" / "vieja.db"
    monkeypatch.setenv(config.ENV_DB_PATH, str(ruta))
    monkeypatch.delenv(config.ENV_DROPBOX_RAIZ, raising=False)
    database.inicializar_bd()
    with _bd() as conn:
        conn.execute("ALTER TABLE proyectos DROP COLUMN codia_residente")
        conn.execute("DELETE FROM auditoria WHERE accion = 'MIGRACION_CABECERA_CODIA'")
    database.inicializar_bd()
    with _bd() as conn:
        assert "codia_residente" in {r[1] for r in conn.execute("PRAGMA table_info(proyectos)")}
        auds = conn.execute("SELECT detalle_json FROM auditoria WHERE accion = 'MIGRACION_CABECERA_CODIA'").fetchall()
    assert len(auds) == 1
    assert (ruta.parent / json.loads(auds[0][0])["respaldo"]).exists()
    assert database.migrar_codia_residente()["migrada"] is False  # idempotente
