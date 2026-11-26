# BACKEND/tests/test_asistido_origen.py
# Etapa 5 · A3a — el parámetro `origen` de _abrir_duda y _escribir_elemento (SINTÉTICO: filas armadas a mano).
import json

import pytest

import config
import database
from importadores.validador_diseno import CONFIRMADO, PENDIENTE_ESTADO
from plano import extractor as ex

IA = "IA:claude-code"
PLANO = {"id": 1, "vectorial_archivo": "e.pdf", "revision": 1, "etiqueta_revision": "R1", "vectorial_sha256": "ab"}


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_DB_PATH, str(tmp_path / "prueba.db"))
    database.inicializar_bd()
    c = database.get_connection()
    c.execute("PRAGMA foreign_keys = OFF")
    yield c
    c.close()


def _prop(h="0.30"):
    return {"tabla": "t1", "bbox_id": "b1", "confirmados": set(), "datos": {"H": {"fuente": {"n": 1}}}}


def _v(h="0.30", estado=PENDIENTE_ESTADO):
    norm = {"id_elemento": "L1", "nivel_rango": "NIVEL 2", "ejes": "—", "tipo_elemento": "LOSA",
            "hoja_plano_origen": "20", "archivo_plano_origen": "e.pdf", "datos_diseno_json": {"H": h}}
    return {"norm": norm, "estado": {"datos_diseno.H": estado, "tipo_elemento": PENDIENTE_ESTADO}}


def _fila(conn):
    return conn.execute("SELECT * FROM elementos_diseno WHERE id_elemento = 'L1'").fetchone()


def _duda(conn):
    return conn.execute("SELECT campo_afectado FROM dudas_y_hallazgos").fetchall()


def test_sin_origen_es_idéntico_a_hoy(conn):  # SINTÉTICO
    assert ex._escribir_elemento(conn, "p", PLANO, _prop(), _v(), "x")[0] == "nuevo"
    assert json.loads(_fila(conn)["fuente_json"])["extractor"] == "T6n"
    assert ex._abrir_duda(conn, "p", "L1", "campo", "texto") is True
    assert _duda(conn)[0]["campo_afectado"] == "T6n:campo"


def test_origen_ia_queda_en_la_fuente(conn):  # SINTÉTICO
    ex._escribir_elemento(conn, "p", PLANO, _prop(), _v(), "x", origen=IA)
    assert json.loads(_fila(conn)["fuente_json"])["extractor"] == IA
    assert ex._escribir_elemento(conn, "p", PLANO, _prop(), _v("0.35"), "y", origen=IA)[0] == "actualizado"


def test_duda_con_origen_ia(conn):  # SINTÉTICO
    assert ex._abrir_duda(conn, "p", "L1", "H", "t", origen="IA:") is True
    assert _duda(conn)[0]["campo_afectado"] == "IA:H"
    assert ex._abrir_duda(conn, "p", "L1", "H", "t", origen="IA:") is False


def test_ia_sobre_fila_t6n_es_choque_y_no_la_toca(conn):  # SINTÉTICO
    ex._escribir_elemento(conn, "p", PLANO, _prop(), _v(), "x")
    antes = tuple(_fila(conn))
    assert ex._escribir_elemento(conn, "p", PLANO, _prop(), _v("0.99"), "y", origen=IA)[0] == "choque"
    assert tuple(_fila(conn)) == antes


def test_t6n_sobre_fila_ia_tambien_es_choque(conn):  # SINTÉTICO
    ex._escribir_elemento(conn, "p", PLANO, _prop(), _v(), "x", origen=IA)
    assert ex._escribir_elemento(conn, "p", PLANO, _prop(), _v("0.99"), "y")[0] == "choque"


def test_campo_confirmado_no_cambia_con_ia(conn):  # SINTÉTICO
    ex._escribir_elemento(conn, "p", PLANO, _prop(), _v("0.30", CONFIRMADO), "x", origen=IA)
    assert ex._escribir_elemento(conn, "p", PLANO, _prop(), _v("0.99"), "y", origen=IA)[0] in ("sin_cambios", "actualizado")
    f = _fila(conn)
    assert json.loads(f["datos_diseno_json"])["H"] == "0.30"
    assert json.loads(f["estado_campos_json"])["datos_diseno.H"] == CONFIRMADO
