# BACKEND/tests/test_informes_obra.py
# Etapa 5 · B3g — Informes de una obra (solo lectura): lista y apertura del PDF.
# BD y carpeta de PDF temporales; los eventos `pdf_generado` se insertan directo (no se lanza el procesador).
# Todo es SINTÉTICO: obras, visitas y PDF inventados solo para probar las reglas.
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

import config
import database
import informes_obra
import main

PID, OTRA = "obra-a", "obra-b"
V1, V2, VB = "obra-a-1", "obra-a-2", "obra-b-1"   # SINTÉTICO
PDF = b"%PDF-1.4\n% sintetico\n"


def _bd():
    conn = sqlite3.connect(config.obtener_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _evento(conn, trabajo, n, visita, formato, ruta, creado, con_dudas=False, bytes_=len(PDF), tipo="pdf_generado"):
    conn.execute("INSERT OR IGNORE INTO trabajos (id, tipo, visitas_json, estado, usuario, creado) VALUES (?, 'cola', '[]', 'terminado', 'prueba', 'x')",
                 (trabajo,))
    conn.execute("INSERT INTO trabajo_eventos (trabajo_id, n, tipo, datos_json, creado) VALUES (?, ?, ?, ?, ?)",
                 (trabajo, n, tipo, json.dumps({"visita_id": visita, "formato": formato, "ruta": str(ruta),
                                                "con_dudas": con_dudas, "bytes": bytes_}), creado))


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    (tmp_path / "bd").mkdir()
    (tmp_path / "pdf").mkdir()
    monkeypatch.setenv(config.ENV_DB_PATH, str(tmp_path / "bd" / "prueba.db"))
    monkeypatch.setenv(config.ENV_DROPBOX_RAIZ, str(tmp_path / "dropbox"))
    monkeypatch.setenv(config.ENV_SALIDA_PRUEBAS, str(tmp_path / "salida"))
    database.inicializar_bd()
    with _bd() as conn:
        for pid in (PID, OTRA):
            conn.execute("INSERT INTO proyectos (id, nombre, tipo, formato_defecto, actualizado) VALUES (?, ?, 'Supervisión', 'STP-MIVED', 'x')",
                         (pid, f"Obra {pid}"))
        for vid, pid, num in ((V1, PID, 1), (V2, PID, 2), (VB, OTRA, 1)):
            conn.execute("""INSERT INTO visitas (id, proyecto_id, numero, nombre_carpeta, ruta_carpeta, fecha_visita, clase, estado,
                            formatos_solicitados, actualizado) VALUES (?, ?, ?, ?, ?, '2026-10-02', 'Parcial', 'Procesada', '["STP-MIVED"]', 'x')""",
                         (vid, pid, num, f"{num}. CARPETA {vid}", f"C:/sint/{vid}"))
    return tmp_path


def _pdf(entorno, nombre):
    p = entorno / "pdf" / nombre
    p.write_bytes(PDF)
    return p


@pytest.fixture
def cliente(entorno):
    with TestClient(main.app) as c:
        yield c


def test_lista_vacia(cliente):
    r = cliente.get(f"/api/proyectos/{PID}/informes")
    assert r.status_code == 200 and r.json() == {"informes": []}


def test_orden_del_mas_nuevo_al_mas_viejo_y_campos(cliente, entorno):
    a = _pdf(entorno, "Obra - STP - Losas - 01-10-2026.pdf")
    b = _pdf(entorno, "Obra - STP - Losas - 01-10-2026 v2.pdf")
    c = _pdf(entorno, "MIVED - OBRA-LOSAS - CON DUDAS.PDF")
    with _bd() as conn:
        _evento(conn, "t1", 1, V1, "STP-MIVED", a, "2026-11-20T10:00:00")
        _evento(conn, "t3", 1, V2, "FI-02", c, "2026-11-22T09:30:00", con_dudas=True)
        _evento(conn, "t2", 1, V1, "STP-MIVED", b, "2026-11-21T08:15:00")
    inf = cliente.get(f"/api/proyectos/{PID}/informes").json()["informes"]
    assert [i["nombre"] for i in inf] == [c.name, b.name, a.name]
    nuevo = inf[0]
    assert nuevo["formato"] == "FI-02" and nuevo["con_dudas"] is True and nuevo["existe"] is True
    assert nuevo["visita"] == {"id": V2, "numero": 2, "nombre_carpeta": f"2. CARPETA {V2}"}
    assert nuevo["fecha"] == "2026-11-22T09:30:00" and nuevo["bytes"] == len(PDF) and nuevo["trabajo_id"] == "t3"


def test_version_se_lee_del_nombre(cliente, entorno):
    nombres = ["Obra - STP - X.pdf", "Obra - STP - X v2.pdf", "Obra - STP - X v12.pdf", "Obra - V3 - X.pdf"]
    with _bd() as conn:
        for i, nom in enumerate(nombres):
            _evento(conn, "t1", i + 1, V1, "STP-MIVED", _pdf(entorno, nom), f"2026-11-2{i}T10:00:00")
    inf = cliente.get(f"/api/proyectos/{PID}/informes").json()["informes"]
    assert {i["nombre"]: i["version"] for i in inf} == {"Obra - STP - X.pdf": 1, "Obra - STP - X v2.pdf": 2,
                                                        "Obra - STP - X v12.pdf": 12, "Obra - V3 - X.pdf": 1}
    assert informes_obra.version_del_nombre("") == 1 and informes_obra.version_del_nombre(None) == 1


def test_archivo_que_ya_no_existe_se_marca_y_sigue_en_la_lista(cliente, entorno):
    ya_no = entorno / "pdf" / "borrado.pdf"
    with _bd() as conn:
        _evento(conn, "t1", 1, V1, "STP-MIVED", ya_no, "2026-11-20T10:00:00")
        _evento(conn, "t1", 2, V1, "FI-01", _pdf(entorno, "esta.pdf"), "2026-11-20T10:00:01")
    inf = cliente.get(f"/api/proyectos/{PID}/informes").json()["informes"]
    assert {i["nombre"]: i["existe"] for i in inf} == {"borrado.pdf": False, "esta.pdf": True}


def test_datos_nulos_no_rompen_la_lista(cliente, entorno):
    with _bd() as conn:
        conn.execute("INSERT INTO trabajos (id, tipo, visitas_json, estado, usuario, creado) VALUES ('t1', 'cola', '[]', 'terminado', 'p', 'x')")
        conn.execute("INSERT INTO trabajo_eventos (trabajo_id, n, tipo, datos_json, creado) VALUES ('t1', 1, 'pdf_generado', ?, 'x')",
                     (json.dumps({"visita_id": V1}),))
    inf = cliente.get(f"/api/proyectos/{PID}/informes").json()["informes"]
    assert len(inf) == 1 and inf[0]["formato"] is None and inf[0]["nombre"] is None and inf[0]["bytes"] is None
    assert inf[0]["existe"] is False and inf[0]["version"] == 1 and inf[0]["con_dudas"] is False


def test_otros_eventos_y_obra_ajena_no_se_mezclan(cliente, entorno):
    mio, ajeno = _pdf(entorno, "mio.pdf"), _pdf(entorno, "ajeno.pdf")
    with _bd() as conn:
        _evento(conn, "t1", 1, V1, "STP-MIVED", mio, "2026-11-20T10:00:00")
        _evento(conn, "t1", 2, VB, "STP-MIVED", ajeno, "2026-11-20T10:00:01")
        _evento(conn, "t1", 3, V1, "STP-MIVED", _pdf(entorno, "otro-evento.pdf"), "2026-11-20T10:00:02", tipo="aviso")
    assert [i["nombre"] for i in cliente.get(f"/api/proyectos/{PID}/informes").json()["informes"]] == ["mio.pdf"]
    assert [i["nombre"] for i in cliente.get(f"/api/proyectos/{OTRA}/informes").json()["informes"]] == ["ajeno.pdf"]


def test_obra_inexistente_da_404(cliente):
    r = cliente.get("/api/proyectos/no-existe/informes")
    assert r.status_code == 404 and r.json()["detail"]


def test_abrir_un_pdf_registrado_es_en_linea(cliente, entorno):
    p = _pdf(entorno, "Obra - STP - Ñandú 01-10-2026.pdf")
    with _bd() as conn:
        _evento(conn, "t1", 1, V1, "STP-MIVED", p, "2026-11-20T10:00:00")
    r = cliente.get("/api/informes/archivo", params={"ruta": str(p)})
    assert r.status_code == 200 and r.content == PDF and r.headers["content-type"] == "application/pdf"
    assert r.headers["content-disposition"].startswith("inline")


def test_ruta_no_registrada_da_404_aunque_exista(cliente, entorno):
    registrado = _pdf(entorno, "registrado.pdf")
    libre = _pdf(entorno, "libre.pdf")
    with _bd() as conn:
        _evento(conn, "t1", 1, V1, "STP-MIVED", registrado, "2026-11-20T10:00:00")
    assert libre.exists()
    assert cliente.get("/api/informes/archivo", params={"ruta": str(libre)}).status_code == 404
    # ni con '..', ni con otra forma de la misma ruta, ni vacía, ni la base de datos
    assert cliente.get("/api/informes/archivo", params={"ruta": str(entorno / "pdf" / ".." / "pdf" / "registrado.pdf")}).status_code == 404
    assert cliente.get("/api/informes/archivo", params={"ruta": str(registrado).upper()}).status_code == 404
    assert cliente.get("/api/informes/archivo", params={"ruta": ""}).status_code == 404
    assert cliente.get("/api/informes/archivo").status_code == 404
    assert cliente.get("/api/informes/archivo", params={"ruta": str(config.obtener_db_path())}).status_code == 404
    assert cliente.get("/api/informes/archivo", params={"ruta": str(registrado)}).status_code == 200


def test_ruta_registrada_cuyo_archivo_falta_da_404_con_detalle(cliente, entorno):
    falta = entorno / "pdf" / "falta.pdf"
    with _bd() as conn:
        _evento(conn, "t1", 1, V1, "STP-MIVED", falta, "2026-11-20T10:00:00")
    r = cliente.get("/api/informes/archivo", params={"ruta": str(falta)})
    assert r.status_code == 404 and "ya no está" in r.json()["detail"]


def test_solo_lectura_no_cambia_la_bd_ni_los_archivos(cliente, entorno):
    p = _pdf(entorno, "x.pdf")
    with _bd() as conn:
        _evento(conn, "t1", 1, V1, "STP-MIVED", p, "2026-11-20T10:00:00")
    def foto():
        with _bd() as conn:
            return [tuple(r) for r in conn.execute("SELECT * FROM trabajo_eventos")], [tuple(r) for r in conn.execute("SELECT * FROM auditoria")]
    antes = foto(), sorted(q.name for q in (entorno / "pdf").iterdir()), p.read_bytes()
    cliente.get(f"/api/proyectos/{PID}/informes"); cliente.get("/api/informes/archivo", params={"ruta": str(p)})
    assert (foto(), sorted(q.name for q in (entorno / "pdf").iterdir()), p.read_bytes()) == antes
