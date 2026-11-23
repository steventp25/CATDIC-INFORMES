# BACKEND/tests/test_dudas_refs.py
# Etapa 5 · B3e — GET /api/dudas/{id}/refs: de qué elemento, plano y página de la visita sale una duda.
# Todo SINTÉTICO: la BD de prueba vive en tmp_path y los eventos `duda` se insertan a mano (como los deja el
# procesador de la cola); ninguna cifra ni ubicación es dato de un proyecto real.
import json

import pytest
from fastapi.testclient import TestClient

import config
import database
import main


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    (tmp_path / "bd").mkdir()
    monkeypatch.setenv(config.ENV_DB_PATH, str(tmp_path / "bd" / "prueba.db"))
    monkeypatch.setenv(config.ENV_DROPBOX_RAIZ, str(tmp_path / "dropbox"))
    monkeypatch.setenv(config.ENV_DATOS_RAIZ, str(tmp_path / "datos"))
    monkeypatch.setenv(config.ENV_CACHE_RAIZ, str(tmp_path / "cache"))
    database.inicializar_bd()
    with TestClient(main.app) as c:
        yield c


def _bd(sql, params=()):
    conn = database.get_connection()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _obra(pid):
    _bd("INSERT INTO proyectos (id, nombre, tipo, formato_defecto, actualizado) VALUES (?, ?, 'Supervisión', 'STP-MIVED', 'x')", (pid, f"Obra sintética {pid}"))


def _duda(pid, campo="cruce:p001"):
    return _bd("""INSERT INTO dudas_y_hallazgos (proyecto_id, visita_id, id_elemento, categoria, campo_afectado,
                  descripcion_pregunta, creado) VALUES (?, NULL, 'C1', 'DUDA_BLOQUEANTE', ?, 'Pregunta sintética', '2026-11-22T10:00:00')""",
               (pid, campo))


def _trabajo(tid="trab-sintetico"):
    if not database.get_connection().execute("SELECT 1 FROM trabajos WHERE id = ?", (tid,)).fetchone():
        _bd("""INSERT INTO trabajos (id, tipo, visitas_json, estado, usuario, creado)
               VALUES (?, 'cola', '[]', 'terminado', 'prueba', '2026-11-22T10:00:00')""", (tid,))
    return tid


def _evento(duda_id, n, creado, refs, tid=None, tipo="duda"):
    datos = {"visita_id": "v-sintetica", "duda_id": duda_id, "nueva": True, "campo": "cruce:p001", "pregunta": "?"}
    datos.update(refs)
    _bd("INSERT INTO trabajo_eventos (trabajo_id, n, tipo, datos_json, creado) VALUES (?, ?, ?, ?, ?)",
        (tid or _trabajo(), n, tipo, json.dumps(datos, ensure_ascii=False), creado))


REFS_A = {"elemento": {"uid": "uid-a", "id_elemento": "C1", "nivel": "S-1", "ejes": "EJE A-1"},
          "plano": {"plano_id": 3, "pagina": 5, "bbox": None, "recuadro": {"rect": [1, 2, 3, 4]}, "uid_diseno": "uid-a"},
          "visita_pdf": {"ruta": "visita-sintetica.pdf", "pagina": 2, "paginas": [2, 3]}}
REFS_B = {"elemento": {"uid": "uid-b", "id_elemento": "C2", "nivel": "S-2", "ejes": "EJE B-2"},
          "plano": {"plano_id": 3, "pagina": 6, "bbox": None, "recuadro": None, "uid_diseno": "uid-b"},
          "visita_pdf": {"ruta": "visita-sintetica.pdf", "pagina": 4, "paginas": [4]}}


def test_duda_con_evento_devuelve_sus_refs(entorno):
    _obra("o1")
    d = _duda("o1")
    _evento(d, 1, "2026-11-22T10:01:00", REFS_A)
    r = entorno.get(f"/api/dudas/{d}/refs")
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["duda_id"] == d
    assert cuerpo["refs"] == REFS_A
    assert cuerpo["refs"]["plano"]["uid_diseno"] == "uid-a"


def test_duda_sin_evento_da_refs_nulas(entorno):
    _obra("o1")
    d = _duda("o1")
    r = entorno.get(f"/api/dudas/{d}/refs")
    assert r.status_code == 200
    assert r.json() == {"duda_id": d, "refs": None}


def test_evento_sin_algunas_claves_las_deja_en_nulo(entorno):
    _obra("o1")
    d = _duda("o1")
    _evento(d, 1, "2026-11-22T10:01:00", {"visita_pdf": {"ruta": "x.pdf"}})
    refs = entorno.get(f"/api/dudas/{d}/refs").json()["refs"]
    assert refs == {"elemento": None, "plano": None, "visita_pdf": {"ruta": "x.pdf"}}


def test_con_dos_eventos_gana_el_mas_reciente(entorno):
    _obra("o1")
    d = _duda("o1")
    _evento(d, 1, "2026-11-22T10:01:00", REFS_A)
    _evento(d, 2, "2026-11-22T10:05:00", REFS_B)
    assert entorno.get(f"/api/dudas/{d}/refs").json()["refs"] == REFS_B
    # El orden de inserción no manda: manda `creado`
    d2 = _duda("o1")
    _evento(d2, 3, "2026-11-22T11:00:00", REFS_B)
    _evento(d2, 4, "2026-11-22T09:00:00", REFS_A)
    assert entorno.get(f"/api/dudas/{d2}/refs").json()["refs"] == REFS_B


def test_si_empatan_en_creado_gana_el_mayor_n(entorno):
    _obra("o1")
    d = _duda("o1")
    _evento(d, 7, "2026-11-22T10:00:00", REFS_A)
    _evento(d, 8, "2026-11-22T10:00:00", REFS_B)
    assert entorno.get(f"/api/dudas/{d}/refs").json()["refs"] == REFS_B


def test_las_dudas_de_otra_obra_no_se_mezclan(entorno):
    _obra("o1")
    _obra("o2")
    d1, d2, d3 = _duda("o1"), _duda("o2"), _duda("o2")
    _evento(d1, 1, "2026-11-22T10:01:00", REFS_A)
    _evento(d2, 2, "2026-11-22T10:02:00", REFS_B)
    assert entorno.get(f"/api/dudas/{d1}/refs").json()["refs"] == REFS_A
    assert entorno.get(f"/api/dudas/{d2}/refs").json()["refs"] == REFS_B
    assert entorno.get(f"/api/dudas/{d3}/refs").json()["refs"] is None


def test_otros_tipos_de_evento_no_cuentan(entorno):
    _obra("o1")
    d = _duda("o1")
    _evento(d, 1, "2026-11-22T10:01:00", REFS_A, tipo="aviso")
    assert entorno.get(f"/api/dudas/{d}/refs").json()["refs"] is None


def test_duda_inexistente_da_404(entorno):
    r = entorno.get("/api/dudas/99999/refs")
    assert r.status_code == 404
    assert "99999" in r.json()["detail"]


def test_solo_lectura_no_cambia_la_bd(entorno):
    _obra("o1")
    d = _duda("o1")
    _evento(d, 1, "2026-11-22T10:01:00", REFS_A)
    antes = [tuple(f) for f in database.get_connection().execute("SELECT * FROM dudas_y_hallazgos")]
    n_aud = database.get_connection().execute("SELECT COUNT(*) FROM auditoria").fetchone()[0]
    entorno.get(f"/api/dudas/{d}/refs")
    assert [tuple(f) for f in database.get_connection().execute("SELECT * FROM dudas_y_hallazgos")] == antes
    assert database.get_connection().execute("SELECT COUNT(*) FROM auditoria").fetchone()[0] == n_aud
