# BACKEND/tests/test_procesar_cola.py
# Etapa 3 · T10a — Procesador de la cola (PLANES/etapa-3.md, T10a). Sustituye a las pruebas de la Etapa 1 · T9
# (botón desactivado con 409).
#
# BD, Dropbox, datos, caché y salida temporales. Todo es # SINTÉTICO: obra, plano, elementos de diseño, visita y
# fotos inventados solo para probar las reglas; no son datos de ningún proyecto. Las pruebas que generan el STP
# (Chromium de Playwright) se saltan con un mensaje si el navegador no está instalado.
import base64
import functools
import io
import json
import os
import sqlite3
from pathlib import Path

import pymupdf
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import config
import database
import main
import mesa_dudas
import procesador_cola as pc
from reglas_ingenieria import PENDIENTE
from sync import lector_visita
from sync.sincronizador import estado_tras_cerrar_bloqueantes

PID = "obra-sint"
VID = "obra-sint-18-losa-s-4-completivo-02-10-2026"
CARPETA = "18. LOSA S-4 COMPLETIVO 02-10-2026"  # SINTÉTICO
CAMPOS_DISENO = {"tipo_losa": "MACIZA", "H": "0.25", "TOP X": '2-Ø1/2"', "BOT X": '2-Ø1/2"', "BOT Y": '2-Ø1/2"',
                 "fc_kgcm2": "350"}  # SINTÉTICO
MAPEO_SINT = {"losa": {"filas": {"a": "fc_kgcm2", "h": "TOP X", "i": "BOT X", "n": "BOT Y"},
                       "medidas": {"b": "H"}}}  # SINTÉTICO: el mapeo real lo decide Steven
OBRA_COMPLETA = {"b": 0.20, "obra": {"a": "350", "e": "SI", "f": "0.025", "g": "0.025", "h": '2-Ø1/2"',
                                     "i": '2-Ø1/2"', "n": '2-Ø1/2"'}}  # SINTÉTICO: 0.20 + 2·0.025 = 0.25


# ---------- Material sintético ----------

def _pdf_plano(ruta: Path):
    doc = pymupdf.open()
    hoja = doc.new_page(width=792, height=612)
    hoja.draw_rect(pymupdf.Rect(120, 120, 260, 220), color=(0, 0, 0), width=2)
    hoja.insert_text((300, 300), "PLANTA SINTETICO", fontsize=24)
    doc.save(str(ruta))
    doc.close()


def _jpeg(color) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (768, 1024), color).save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def _pdf_visita(ruta: Path, etiquetas):
    """Una foto por página, la etiqueta (12 pt negrita) y 'Creado el:' debajo, como los PDF de visita."""
    doc = pymupdf.open()
    for i, et in enumerate(etiquetas, start=1):
        hoja = doc.new_page(width=612, height=792)
        hoja.insert_image(pymupdf.Rect(56, 99, 465, 644), stream=_jpeg((40 * i % 255, 100, 120)))
        y = 660
        if et:
            hoja.insert_text((56, y), et, fontname="hebo", fontsize=12)
            y += 20
        hoja.insert_text((56, y), "Creado el:", fontname="hebo", fontsize=10)
        hoja.insert_text((117, y), f"02/10/2026 10:{i:02d}", fontname="helv", fontsize=10)
    doc.save(str(ruta))
    doc.close()


def _bd():
    conn = sqlite3.connect(config.obtener_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _arbol(raiz: Path):
    return sorted((str(p.relative_to(raiz)), p.stat().st_size, p.stat().st_mtime_ns) for p in raiz.rglob("*"))


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    for nombre in ("bd", "dropbox", "datos", "cache", "salida"):
        (tmp_path / nombre).mkdir()
    monkeypatch.setenv(config.ENV_DB_PATH, str(tmp_path / "bd" / "prueba.db"))
    monkeypatch.setenv(config.ENV_DROPBOX_RAIZ, str(tmp_path / "dropbox"))
    monkeypatch.setenv(config.ENV_DATOS_RAIZ, str(tmp_path / "datos"))
    monkeypatch.setenv(config.ENV_CACHE_RAIZ, str(tmp_path / "cache"))
    monkeypatch.setenv(lector_visita.ENV_CACHE_RAIZ, str(tmp_path / "cache"))
    monkeypatch.setenv(config.ENV_SALIDA_PRUEBAS, str(tmp_path / "salida"))
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", {})
    database.inicializar_bd()
    obra = tmp_path / "dropbox" / "OBRA SINT"
    (obra / "INFORMES" / "2.DATA PROCESADA").mkdir(parents=True)
    carpeta_visita = obra / "LEVANTAMIENTO" / "VISITA A OBRA" / CARPETA
    carpeta_visita.mkdir(parents=True)
    planos = tmp_path / "datos" / PID / "planos" / "r01"
    planos.mkdir(parents=True)
    vectorial = planos / "vectorial.pdf"
    _pdf_plano(vectorial)
    with _bd() as conn:
        conn.execute("""INSERT INTO proyectos (id, nombre, tipo, formato_defecto, carpeta_dropbox, no_solicitud,
                        no_licencia, direccion_obra, provincia, sector, residente_obra, actualizado)
                        VALUES (?, 'Obra Sintetica', 'Supervisión', 'STP-MIVED', ?, 'SOL-SINT', 'LIC-SINT',
                        'CALLE SINT 1', 'PROV SINT', 'SECTOR SINT', 'RESIDENTE SINT', 'x')""", (PID, str(obra)))
        conn.execute("""INSERT INTO planos (proyecto_id, revision, estado, vectorial_archivo, vectorial_ruta,
                        vectorial_sha256, vectorial_bytes, vectorial_paginas, sellado_archivo, sellado_ruta, sellado_sha256,
                        sellado_bytes, sellado_paginas, certificado_por, certificado_en, certificacion_texto, subido_en)
                        VALUES (?, 1, 'vigente', 'vectorial.pdf', ?, 'x', 1, 1, 'sellado.pdf', ?, 'x', 1, 1, 'prueba',
                        'x', 'x', 'x')""", (PID, str(vectorial), str(planos / "sellado.pdf")))
        conn.execute("""INSERT INTO visitas (id, proyecto_id, numero, nombre_carpeta, ruta_carpeta, fecha_visita, clase,
                        estado, formatos_solicitados, archivos_json, actualizado)
                        VALUES (?, ?, 18, ?, ?, '2026-10-02', 'Completivo', 'Sin procesar', '["STP-MIVED"]', ?, 'x')""",
                     (VID, PID, CARPETA, str(carpeta_visita),
                      json.dumps([{"nombre": "visita.pdf", "ruta": str(carpeta_visita / "visita.pdf")}])))
    return {"tmp": tmp_path, "obra": obra, "carpeta_visita": carpeta_visita, "vectorial": vectorial}


def _diseno(uid="ed-0001", id_elemento="L5", nivel="SOTANO S4", ejes="—", confirmado=True, recuadros=True,
            tipo="LOSA MACIZA", campos=None):
    campos = CAMPOS_DISENO if campos is None else campos
    estado = {k: ("confirmado" if confirmado else "pendiente_de_verificar")
              for k in ["id_elemento", "tipo_elemento", "nivel_rango", "ejes"] + [f"datos_diseno.{c}" for c in campos]}
    loc = {"plano_id": 1, "pagina": 1, "rect": [100, 100, 300, 250], "estado": "confirmado"} if recuadros else {}
    det = {"plano_id": 1, "pagina": 1, "rect": [0, 0, 300, 200], "estado": "confirmado"} if recuadros else {}
    with _bd() as conn:
        conn.execute("""INSERT INTO elementos_diseno (uid, proyecto_id, id_elemento, tipo_elemento, nivel_rango, ejes,
                        hoja_plano_origen, archivo_plano_origen, datos_diseno_json, estado_campos_json,
                        recorte_planta_json, recorte_detalle_json, actualizado, fuente_json, plano_id)
                        VALUES (?, ?, ?, ?, ?, ?, '21', 'vectorial.pdf', ?, ?, ?, ?, 'x', ?, 1)""",
                     (uid, PID, id_elemento, tipo, nivel, ejes, json.dumps(campos), json.dumps(estado),
                      json.dumps(loc), json.dumps(det),
                      json.dumps({"tabla": "p1:acero_en_losa", "bbox_id": [[10, 10, 20, 20]]})))


def _elemento_visita(entorno, orden=1, etiqueta="L5 —", id_elemento="L5", ejes="—", nivel="S-4", medidas=None):
    """Capa 2 ya leída (como la deja el lector), con sus fotos en la caché."""
    cache = entorno["tmp"] / "cache"
    rel = f"{PID}/{VID}/p{orden:03d}.jpg"
    (cache / rel).parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (400, 300), (200, 60, 60)).save(cache / rel, format="JPEG")
    with _bd() as conn:
        conn.execute("""INSERT INTO elementos_visita (uid, visita_id, orden_en_log, etiqueta_original, id_elemento,
                        tipo_elemento, nivel, ejes, fotos_json, medidas_acero_campo_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                     (f"{VID}-{orden:03d}", VID, orden, etiqueta, id_elemento, PENDIENTE, nivel, ejes,
                      json.dumps([{"pagina": orden, "etiqueta": etiqueta, "cache": rel}]), json.dumps(medidas or {})))


def _duda_lector(orden=1, etiqueta="L5", resuelta=False, respuesta=""):
    with _bd() as conn:
        cur = conn.execute("""INSERT INTO dudas_y_hallazgos (proyecto_id, visita_id, id_elemento, categoria,
                              campo_afectado, descripcion_pregunta, respuesta_usuario, resuelta, creado)
                              VALUES (?, ?, ?, 'DUDA_BLOQUEANTE', ?, 'SINT', ?, ?, 'x')""",
                           (PID, VID, etiqueta, f"elemento_visita:p{orden:03d}", respuesta, int(resuelta)))
        return cur.lastrowid


def _procesar(visita_id=VID):
    t = pc.lanzar_trabajo([visita_id], en_hilo=False, usuario="prueba")
    t = pc.obtener_trabajo(t["id"])
    eventos = pc.listar_eventos(t["id"])["eventos"]
    return t, eventos


def _visita():
    with _bd() as conn:
        return dict(conn.execute("SELECT * FROM visitas WHERE id = ?", (VID,)).fetchone())


def _abiertas():
    with _bd() as conn:
        return [dict(d) for d in conn.execute("""SELECT * FROM dudas_y_hallazgos WHERE visita_id = ? AND resuelta = 0
                                                 AND categoria = 'DUDA_BLOQUEANTE' ORDER BY id""", (VID,))]


@functools.lru_cache(maxsize=1)
def _chromium_disponible() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            return Path(p.chromium.executable_path).exists()
    except Exception:  # noqa: BLE001
        return False


def _exigir_chromium():
    if not _chromium_disponible():
        pytest.skip("Chromium de Playwright no está instalado en esta máquina (python -m playwright install chromium)")


# ---------- Unidades ----------

def test_niveles_del_sotano_y_clave_completa():
    assert pc.niveles_de_diseno("S-4") == {"S-4", "SOTANO S4", "SOTANO S-4", "SOTANO -4"}
    assert pc.niveles_de_diseno("NIVEL 4@8") == {"NIVEL 4@8"}  # un rango nunca se expande solo
    assert pc.clave_nivel_completa("S-4") == "SOTANO -4"
    assert pc.clave_nivel_completa(PENDIENTE) is None


@pytest.mark.parametrize("texto, esperado", [
    ("C1 A4", {"id": "C1", "ejes": "EJE A-4"}),
    ("c1 4a", {"id": "C1", "ejes": "EJE A-4"}),
    ("L5 —", {"id": "L5", "ejes": "—"}),
    ("L5", {"id": "L5", "ejes": None}),
    ("ed-00ab", {"uid": "ed-00ab"}),
    ("pertenece al anterior", {"anterior": True}),
    ("es la losa de al lado", None),
    ("Mh4", {"id": "MH4", "ejes": None}),  # el ID que escribe Steven, en mayúsculas (normalización aprobada)
    ("Mh4 pantalla eje 3", None),
    ("", None),
])
def test_respuesta_de_steven_se_lee_de_forma_estricta(texto, esperado):
    assert pc.interpretar_respuesta(texto) == esperado


# ---------- Cruce (§4.2) y Regla de Oro ----------

def test_sin_candidato_en_el_plano_crea_duda_con_referencias_y_el_trabajo_sigue(entorno):
    _elemento_visita(entorno, 1, "L5 —", "L5", "—")
    _elemento_visita(entorno, 2, "L9 —", "L9", "—")
    _diseno()
    t, eventos = _procesar()
    assert t["estado"] == "terminado"
    tipos = [e["tipo"] for e in eventos]
    assert tipos[0] == "visita_inicio" and tipos[-1] == "fin" and "visita_fin" in tipos
    assert tipos.count("elemento_inicio") == 2  # la duda del primero no detuvo el segundo
    dudas = [e for e in eventos if e["tipo"] == "duda"]
    cruce = next(d for d in dudas if d["campo"] == "cruce:p002")
    assert "ningún elemento de diseño" in cruce["pregunta"]
    assert cruce["visita_pdf"]["pagina"] == 2 and cruce["visita_pdf"]["ruta"].endswith("visita.pdf")
    assert cruce["plano"]["plano_id"] == 1 and cruce["elemento"]["etiqueta"] == "L9 —"
    assert _visita()["estado"] == "Con dudas"


def test_varios_candidatos_no_se_elige_uno(entorno):
    _elemento_visita(entorno, 1, "L5", "L5", PENDIENTE)
    _duda_lector(1, resuelta=True, respuesta="L5")  # solo el ID
    _diseno("ed-0001", ejes="—")
    _diseno("ed-0002", nivel="SOTANO -4", ejes="—")
    _, eventos = _procesar()
    d = next(e for e in eventos if e["tipo"] == "duda" and e["campo"] == "cruce:p001")
    assert "2 elementos de diseño" in d["pregunta"] and "ed-0001" in d["pregunta"] and "ed-0002" in d["pregunta"]


def test_diseno_sin_confirmar_es_duda_con_la_hoja_del_plano(entorno):
    _elemento_visita(entorno, 1)
    _diseno(confirmado=False)
    _, eventos = _procesar()
    d = next(e for e in eventos if e["tipo"] == "duda" and e["campo"] == "diseno:p001")
    assert "sin confirmar" in d["pregunta"] and "datos_diseno.H" in d["pregunta"]
    assert d["plano"] == {"plano_id": 1, "pagina": 1, "bbox": [[10, 10, 20, 20]], "uid_diseno": "ed-0001",
                          "recuadro": {"plano_id": 1, "pagina": 1, "rect": [100, 100, 300, 250], "estado": "confirmado"}}
    assert not list((entorno["tmp"] / "salida").rglob("*.pdf"))


def test_sin_mapeo_de_filas_aprobado_el_elemento_queda_en_espera(entorno):
    _elemento_visita(entorno, 1)
    _diseno()
    _, eventos = _procesar()
    assert any(e["tipo"] == "duda" and e["campo"] == "diseno:p001:mapeo" for e in eventos)
    assert not any(e["tipo"] == "pdf_generado" for e in eventos)


def test_recuadros_sin_confirmar_son_duda(entorno, monkeypatch):
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_SINT)
    _elemento_visita(entorno, 1)
    _diseno(recuadros=False)
    _procesar()
    campos = {d["campo_afectado"] for d in _abiertas()}
    assert {"diseno:p001:localizacion", "diseno:p001:detalle"} <= campos


def test_la_etiqueta_nunca_se_usa_como_id(entorno):
    # 'L5' suelta: el lector la dejó pendiente con su duda. Aunque L5 existe en el plano, no se cruza.
    _elemento_visita(entorno, 1, "L5", PENDIENTE, PENDIENTE)
    lector = _duda_lector(1)
    _diseno()
    _, eventos = _procesar()
    assert not any(e["tipo"] == "elemento_listo" for e in eventos)
    d = [e for e in eventos if e["tipo"] == "duda"]
    assert d[0]["duda_id"] == lector and d[0]["nueva"] is False
    assert not any(x["campo_afectado"].startswith("cruce:") for x in _abiertas())


def test_o4_la_respuesta_de_steven_se_aplica_estricta(entorno, monkeypatch):
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_SINT)
    _elemento_visita(entorno, 1, "L5", PENDIENTE, PENDIENTE)
    _elemento_visita(entorno, 2, "losa grande", PENDIENTE, PENDIENTE)
    _duda_lector(1, resuelta=True, respuesta="L5 —")
    _duda_lector(2, "losa grande", resuelta=True, respuesta="es la losa de al lado")
    _diseno()
    _, eventos = _procesar()
    listos = [e for e in eventos if e["tipo"] == "elemento_listo"]
    assert [e["elemento"]["orden_en_log"] for e in listos] == [1]
    d = next(e for e in eventos if e["tipo"] == "duda" and e["campo"] == "cruce:p002:respuesta")
    assert "no se puede aplicar sin" in d["pregunta"]


def test_reintento_antes_de_cerrar_si_steven_responde_mientras_corre(entorno, monkeypatch):
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_SINT)
    _elemento_visita(entorno, 1, "L5", PENDIENTE, PENDIENTE)
    lector = _duda_lector(1)
    _diseno()
    original = pc.ProcesoVisita._elemento

    def con_respuesta(self, ev, reintento=False):
        r = original(self, ev, reintento)
        if not reintento:  # Steven responde en la Mesa mientras el trabajo sigue
            mesa_dudas.responder_duda(lector, "L5 —")
        return r
    monkeypatch.setattr(pc.ProcesoVisita, "_elemento", con_respuesta)
    _, eventos = _procesar()
    inicios = [e for e in eventos if e["tipo"] == "elemento_inicio"]
    assert [e["reintento"] for e in inicios] == [False, True]
    assert any(e["tipo"] == "elemento_listo" for e in eventos)


def test_una_respuesta_que_ya_no_hace_falta_cierra_la_duda_propia(entorno, monkeypatch):
    _elemento_visita(entorno, 1)
    _diseno(confirmado=False)
    _procesar()
    assert any(d["campo_afectado"] == "diseno:p001" for d in _abiertas())
    with _bd() as conn:  # se confirman los datos en el plano (T7n)
        estado = {k: "confirmado" for k in json.loads(conn.execute(
            "SELECT estado_campos_json FROM elementos_diseno").fetchone()[0])}
        conn.execute("UPDATE elementos_diseno SET estado_campos_json = ?", (json.dumps(estado),))
    _procesar()
    campos = {d["campo_afectado"] for d in _abiertas()}
    assert "diseno:p001" not in campos and "diseno:p001:mapeo" in campos
    with _bd() as conn:
        assert conn.execute("""SELECT respuesta_usuario FROM dudas_y_hallazgos WHERE campo_afectado = 'diseno:p001'""").fetchone()[0] \
            == pc.RESPUESTA_CIERRE


# ---------- Visita: lector, P3 (O5), clase, cabecera ----------

def test_lector_corre_si_la_visita_no_fue_leida_y_queda_con_dudas(entorno):
    _pdf_visita(entorno["carpeta_visita"] / "visita.pdf", ["Mh4", "", "Tramo D-B"])
    _, eventos = _procesar()
    with _bd() as conn:
        assert conn.execute("SELECT COUNT(*) FROM elementos_visita WHERE visita_id = ?", (VID,)).fetchone()[0] == 2
    assert any(e["tipo"] == "aviso" and "Visita leída" in e["texto"] for e in eventos)
    assert _visita()["estado"] == "Con dudas"  # O1 del lector
    assert {d["campo_afectado"] for d in _abiertas()} >= {"elemento_visita:p001", "elemento_visita:p003"}


def test_con_paquete_de_campo_se_carga_el_paquete_y_no_el_pdf(entorno):
    # SINTÉTICO. La visita no tiene su PDF en la carpeta: con el paquete no hace falta.
    buf = io.BytesIO()
    Image.new("RGB", (800, 600), (90, 90, 90)).save(buf, format="JPEG")
    foto = base64.b64encode(buf.getvalue()).decode("ascii")
    paquete = {"formato": "catdic-paquete-visita", "version": 1, "visita": {"nivel": "S-4"}, "elementos": [
        {"orden": 1, "tipo": "LOSA", "id": "L5", "ejes": {"caso": "losa"},
         "fotos": [{"numero": 1, "base64": foto}, {"numero": 2, "base64": foto}]}]}
    (entorno["carpeta_visita"] / "P.catdic-visita.json").write_text(json.dumps(paquete), encoding="utf-8")
    _, eventos = _procesar()
    with _bd() as conn:
        filas = conn.execute("SELECT id_elemento, ejes, nivel FROM elementos_visita WHERE visita_id = ?", (VID,)).fetchall()
    assert [tuple(f) for f in filas] == [("L5", "—", "S-4")]
    assert any(e["tipo"] == "aviso" and "paquete de Campo" in e["texto"] for e in eventos)
    assert not [d for d in _abiertas() if d["campo_afectado"] in ("lector_visita", "paquete_visita")]


def test_o5_si_ya_hay_un_stp_de_su_fecha_no_se_regenera(entorno, monkeypatch):
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_SINT)
    stp = entorno["obra"] / "INFORMES" / "2.DATA PROCESADA" / "Obra Sintetica - STP - Losa S4 Completivo - 02-10-2026.pdf"
    stp.write_bytes(b"%PDF-1.4 SINT")
    _elemento_visita(entorno, 1, medidas=OBRA_COMPLETA)
    _diseno()
    antes = _arbol(entorno["tmp"] / "dropbox")
    _, eventos = _procesar()
    estado = next(d for d in _abiertas() if d["campo_afectado"] == "estado")
    assert stp.name in estado["descripcion_pregunta"] and estado["id_elemento"] == ""
    assert json.loads(_visita()["origen_datos_json"])["stp_candidatos"] == [[stp.name]]
    assert not any(e["tipo"] == "pdf_generado" for e in eventos)
    assert _arbol(entorno["tmp"] / "dropbox") == antes  # Dropbox solo lectura


def test_visita_mixta_y_cabecera_vacia_son_dudas_de_la_visita(entorno):
    _elemento_visita(entorno, 1)
    _diseno()
    with _bd() as conn:
        conn.execute("UPDATE visitas SET clase = 'Mixta' WHERE id = ?", (VID,))
        conn.execute("UPDATE proyectos SET residente_obra = '' WHERE id = ?", (PID,))
    _procesar()
    campos = {d["campo_afectado"]: d for d in _abiertas()}
    assert "procesador:clase" in campos and "residente_obra" in campos["proyecto:cabecera"]["descripcion_pregunta"]
    with _bd() as conn:  # Steven llena la cabecera: la duda propia se recalcula y se cierra sola
        conn.execute("UPDATE proyectos SET residente_obra = 'RESIDENTE SINT' WHERE id = ?", (PID,))
        conn.execute("UPDATE visitas SET estado = 'Sin procesar' WHERE id = ?", (VID,))
    _procesar()
    assert "proyecto:cabecera" not in {d["campo_afectado"] for d in _abiertas()}


def test_catdic_stp_se_omite_con_aviso(entorno):
    _elemento_visita(entorno, 1)
    _diseno()
    with _bd() as conn:
        conn.execute("""UPDATE visitas SET formatos_solicitados = '["STP-MIVED", "CATDIC-STP"]' WHERE id = ?""", (VID,))
    _, eventos = _procesar()
    assert any(e["tipo"] == "aviso" and "CATDIC-STP" in e["texto"] for e in eventos)
    assert "procesador:formatos" not in {d["campo_afectado"] for d in _abiertas()}


# ---------- Generación y cierre ----------

def test_visita_completa_queda_procesada_con_su_stp(entorno, monkeypatch):
    _exigir_chromium()
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_SINT)
    _elemento_visita(entorno, 1, medidas=OBRA_COMPLETA)
    _diseno()
    antes = _arbol(entorno["tmp"] / "dropbox")
    t, eventos = _procesar()
    pdf = [e for e in eventos if e["tipo"] == "pdf_generado"]
    assert len(pdf) == 1 and pdf[0]["con_dudas"] is False
    ruta = Path(pdf[0]["ruta"])
    assert ruta.name == "Obra Sintetica - STP - LOSA S-4 Completivo - 02-10-2026.pdf"
    assert ruta.parent == entorno["tmp"] / "salida" and ruta.stat().st_size < 30_000_000
    assert not (entorno["tmp"] / "salida" / pc.CARPETA_DE_PASO).exists()
    v = _visita()
    assert v["estado"] == "Procesada" and json.loads(v["salida_json"])["procesador"][0]["ruta"] == str(ruta)
    assert _abiertas() == [] and t["resumen"]["pdf"][0]["ruta"] == str(ruta)
    assert _arbol(entorno["tmp"] / "dropbox") == antes
    # Una segunda corrida (tras volver a la cola) no sobrescribe: v2
    with _bd() as conn:
        conn.execute("UPDATE visitas SET estado = 'Sin procesar' WHERE id = ?", (VID,))
    _, eventos = _procesar()
    assert Path(next(e for e in eventos if e["tipo"] == "pdf_generado")["ruta"]).name.endswith("02-10-2026 v2.pdf")


def test_sin_datos_de_obra_el_pdf_se_nombra_con_dudas_y_la_visita_no_se_procesa(entorno, monkeypatch):
    _exigir_chromium()
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_SINT)
    _elemento_visita(entorno, 1)  # sin medidas ni columna OBRA
    _diseno()
    _, eventos = _procesar()
    pdf = next(e for e in eventos if e["tipo"] == "pdf_generado")
    assert pdf["con_dudas"] is True and Path(pdf["ruta"]).name.endswith(" - 02-10-2026 - CON DUDAS.pdf")
    obra = next(d for d in _abiertas() if d["campo_afectado"] == "obra:p001")
    assert "OBRA" in obra["descripcion_pregunta"]
    assert _visita()["estado"] == "Con dudas" and json.loads(_visita()["salida_json"]) == {}


def test_un_error_en_una_visita_no_detiene_el_trabajo(entorno, monkeypatch):
    _elemento_visita(entorno, 1)
    _diseno()
    with _bd() as conn:
        conn.execute("""INSERT INTO visitas (id, proyecto_id, numero, nombre_carpeta, ruta_carpeta, fecha_visita, clase,
                        estado, formatos_solicitados, actualizado) VALUES ('otra', ?, 19, '19. OTRA S-4 PARCIAL 03-10-2026',
                        'x', '2026-10-03', 'Parcial', 'Sin procesar', '["STP-MIVED"]', 'x')""", (PID,))
    original = pc.ProcesoVisita._procesar

    def falla(self, visita):
        if self.visita_id == VID:
            raise RuntimeError("fallo SINTÉTICO")
        return original(self, visita)
    monkeypatch.setattr(pc.ProcesoVisita, "_procesar", falla)
    t = pc.lanzar_trabajo([VID, "otra"], tipo="cola", en_hilo=False, usuario="prueba")
    t = pc.obtener_trabajo(t["id"])
    assert t["estado"] == "fallido" and "fallo SINTÉTICO" in t["error"]
    assert [v["visita_id"] for v in t["resumen"]["visitas"]] == [VID, "otra"]
    assert _visita()["estado"] == "Sin procesar"  # vuelve al estado que tenía


# ---------- API ----------

@pytest.fixture
def cliente(entorno):
    with TestClient(main.app) as c:
        yield c


def test_api_lanza_el_trabajo_y_entrega_los_eventos_desde_n(cliente, entorno):
    _elemento_visita(entorno, 1)
    _diseno(confirmado=False)
    r = cliente.post(f"/api/visitas/{VID}/procesar")
    assert r.status_code == 202
    tid = r.json()["trabajo"]["id"]
    pc.esperar(tid, 60)
    t = cliente.get(f"/api/trabajos/{tid}").json()
    assert t["estado"] == "terminado" and t["visitas"] == [VID] and t["eventos"] >= 5
    todos = cliente.get(f"/api/trabajos/{tid}/eventos").json()
    assert [e["n"] for e in todos["eventos"]] == list(range(1, t["eventos"] + 1))
    resto = cliente.get(f"/api/trabajos/{tid}/eventos", params={"desde": 3}).json()
    assert [e["n"] for e in resto["eventos"]] == list(range(4, t["eventos"] + 1)) and resto["ultimo"] == t["eventos"]
    assert {"visita_inicio", "elemento_inicio", "duda", "visita_fin", "fin"} <= {e["tipo"] for e in todos["eventos"]}
    with _bd() as conn:
        acciones = {f[0] for f in conn.execute("SELECT accion FROM auditoria WHERE modulo = 'PROCESADOR'")}
    assert {"LANZAR_TRABAJO", "ABRIR_DUDA", "PROCESAR_VISITA", "TERMINAR_TRABAJO"} <= acciones


def test_api_errores_404_y_409(cliente, entorno):
    assert cliente.post("/api/visitas/no-existe/procesar").status_code == 404
    assert cliente.get("/api/trabajos/no-existe").status_code == 404
    assert cliente.get("/api/trabajos/no-existe/eventos").status_code == 404
    with _bd() as conn:
        conn.execute("UPDATE visitas SET estado = 'Procesada' WHERE id = ?", (VID,))
    r = cliente.post(f"/api/visitas/{VID}/procesar")
    assert r.status_code == 409 and "Procesada" in r.json()["detail"]
    with _bd() as conn:
        conn.execute("UPDATE visitas SET estado = 'Sin procesar' WHERE id = ?", (VID,))
        conn.execute("""INSERT INTO trabajos (id, tipo, visitas_json, estado, usuario, creado)
                        VALUES ('trab-sint', 'visita', '[]', 'corriendo', 'prueba', 'x')""")
    r = cliente.post(f"/api/visitas/{VID}/procesar")
    assert r.status_code == 409 and "trab-sint" in r.json()["detail"]


def test_api_procesar_cola_toma_solo_sin_procesar_y_en_cola(cliente, entorno):
    with _bd() as conn:
        conn.execute("UPDATE visitas SET estado = 'Con dudas' WHERE id = ?", (VID,))
    r = cliente.post("/api/visitas/procesar-cola")
    assert r.status_code == 202 and r.json()["trabajo"] is None
    with _bd() as conn:
        conn.execute("UPDATE visitas SET estado = 'En cola' WHERE id = ?", (VID,))
    r = cliente.post("/api/visitas/procesar-cola", params={"proyecto_id": PID})
    t = pc.esperar(r.json()["trabajo"]["id"], 60)
    assert t["tipo"] == "cola" and t["visitas"] == [VID] and t["estado"] == "terminado", t["error"]


def test_trabajos_huerfanos_al_arrancar(entorno):
    with _bd() as conn:
        conn.execute("""INSERT INTO trabajos (id, tipo, visitas_json, estado, usuario, creado)
                        VALUES ('trab-viejo', 'visita', ?, 'corriendo', 'prueba', 'x')""", (json.dumps([VID]),))
        conn.execute("UPDATE visitas SET estado = 'En proceso', origen_datos_json = ? WHERE id = ?",
                     (json.dumps({"procesador": {"trabajo": "trab-viejo", "estado_anterior": "Sin procesar"}}), VID))
    r = pc.marcar_huerfanos(usuario="prueba")
    assert r == {"trabajos": ["trab-viejo"], "visitas_restauradas": [VID]}
    assert pc.obtener_trabajo("trab-viejo")["estado"] == "fallido" and _visita()["estado"] == "Sin procesar"
    assert pc.marcar_huerfanos(usuario="prueba") == {"trabajos": [], "visitas_restauradas": []}


# ---------- O1 de T4b: el STP elegido en la Mesa debe seguir existiendo ----------

@pytest.mark.parametrize("existe", [True, False])
def test_o1_estado_tras_cerrar_bloqueantes_comprueba_el_stp(entorno, existe):
    stp = entorno["obra"] / "INFORMES" / "2.DATA PROCESADA" / "Obra Sintetica - STP - X Completivo - 02-10-2026.pdf"
    if existe:
        stp.write_bytes(b"%PDF-1.4 SINT")
    origen = {"estado_mesa": {"estado": "Procesada", "stp": [str(stp)]}, "stp_candidatos": [[stp.name]]}
    conn = database.get_connection()
    try:
        cambios = estado_tras_cerrar_bloqueantes(conn, VID, "Con dudas", origen)
        nuevas = conn.execute("SELECT * FROM dudas_y_hallazgos WHERE visita_id = ? AND campo_afectado = 'estado'",
                              (VID,)).fetchall()
    finally:
        conn.rollback()
        conn.close()
    if existe:
        assert cambios["estado"] == "Procesada" and not nuevas
    else:
        assert cambios == {} and len(nuevas) == 1 and "ya no está" in nuevas[0]["descripcion_pregunta"]
        assert "estado_mesa" not in origen and origen["estado_mesa_anulado"]["motivo"]


# ---------- Paquete v2 de Campo en la cola (Etapa 7, T3) ----------

def test_t3_elemento_pendiente_de_campo_queda_en_revision_y_no_se_procesa(entorno, monkeypatch):
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_SINT)
    _elemento_visita(entorno, 1, medidas={**OBRA_COMPLETA, "estado_campo": "Pendiente", "conforme_por_omision": []})
    _diseno()
    _, eventos = _procesar()
    assert not any(e["tipo"] == "pdf_generado" for e in eventos)
    duda = next(d for d in _abiertas() if d["campo_afectado"] == "elemento_visita:p001:pendiente")
    assert "en revisión" in duda["descripcion_pregunta"]
    assert _visita()["estado"] == "Con dudas"


def test_t3_pendiente_con_su_duda_resuelta_se_procesa(entorno, monkeypatch):
    _exigir_chromium()
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_SINT)
    _elemento_visita(entorno, 1, medidas={**OBRA_COMPLETA, "estado_campo": "Pendiente"})
    _diseno()
    with _bd() as conn:
        conn.execute("""INSERT INTO dudas_y_hallazgos (proyecto_id, visita_id, id_elemento, categoria, campo_afectado,
                        descripcion_pregunta, resuelta, respuesta_usuario, creado)
                        VALUES (?, ?, 'L5', 'DUDA_BLOQUEANTE', 'elemento_visita:p001:pendiente', 'SINT', 1, 'ok', 'x')""",
                     (PID, VID))
    _, eventos = _procesar()
    assert any(e["tipo"] == "pdf_generado" for e in eventos)


def test_t3_conforme_por_omision_llega_al_generador_y_la_visita_se_procesa(entorno, monkeypatch):
    _exigir_chromium()
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_SINT)
    # b (medida) vacía y las demás filas de texto vacías = conformes; solo 'e' (calzos) la trae Campo
    _elemento_visita(entorno, 1, medidas={"obra": {"e": "SI"}, "conforme_por_omision": list("abfghin"),
                                          "estado_campo": "Conforme", "origen": "paquete_v2"})
    _diseno()
    _, eventos = _procesar()
    pdf = next(e for e in eventos if e["tipo"] == "pdf_generado")
    assert pdf["con_dudas"] is False
    assert not [d for d in _abiertas() if d["campo_afectado"].startswith(("obra", "medidas"))]
    assert _visita()["estado"] == "Procesada"


# ---------- T4 (Etapa 7): mapeo de filas del STP en generators/mapeo_stp.json ----------

def test_t4_carga_del_json_valido_roto_y_ausente(tmp_path):
    ok = tmp_path / "ok.json"
    ok.write_text(json.dumps({"confirmado": True, "filas_stp": {"col": {"medidas": {"c": "b_m"}}, "muro": {}}}),
                  encoding="utf-8")
    assert pc.cargar_mapeo_stp(ok) == ({"col": {"filas": {}, "medidas": {"c": "b_m"}, "barras": None, "derivaciones": {}},
                                        "muro": {"filas": {}, "medidas": {}, "barras": None, "derivaciones": {}}}, True)
    sin_confirmar = tmp_path / "sc.json"
    sin_confirmar.write_text(json.dumps({"confirmado": "true", "filas_stp": {}}), encoding="utf-8")
    assert pc.cargar_mapeo_stp(sin_confirmar) == ({}, False)  # solo True exacto confirma
    roto = tmp_path / "roto.json"
    roto.write_text("{ no es json", encoding="utf-8")
    forma = tmp_path / "forma.json"
    forma.write_text(json.dumps({"confirmado": True, "filas_stp": {"col": ["x"]}}), encoding="utf-8")
    for ruta in (roto, forma, tmp_path / "no-existe.json"):
        assert pc.cargar_mapeo_stp(ruta) == ({}, False)


def test_t4_el_json_entregado_es_propuesta_sin_confirmar():
    mapeo, confirmado = pc.cargar_mapeo_stp()
    assert confirmado is False
    assert mapeo["col"]["filas"] == {} and mapeo["col"]["medidas"] == {"c": "b_m", "d": "h_m"}
    assert mapeo["col"]["barras"] == "acero_longitudinal"
    assert mapeo["col"]["derivaciones"] == {  # T9: propuesta, confirmado sigue en false
        "h": {"campo": "estribos", "regla": "estribos_cantidad_diametro"},
        "f": {"campo": "estribos", "regla": "estribos_espaciamiento_unico"},
        "g": {"campo": "estribos", "regla": "estribos_espaciamiento_unico"},
        "m": {"campo": "acero_longitudinal", "regla": "barras_diametro_unico"},
        "n": {"campo": "acero_longitudinal", "regla": "barras_diametro_unico"},
        "k": {"campo": "acero_longitudinal", "regla": "barras_total_unico"},  # T11b
        "b": {"campo": "fc", "regla": "fc_kgcm2"},  # T11
        "e": {"campo": "altura_m", "regla": "metros_impresos"},
        "i": {"campo": "barras_cara_x", "regla": "barras_por_cara",
              "apoyo": {"par": "barras_cara_y", "acero": "acero_longitudinal"}},
        "j": {"campo": "barras_cara_y", "regla": "barras_por_cara",
              "apoyo": {"par": "barras_cara_x", "acero": "acero_longitudinal"}}}
    assert mapeo["muro"]["medidas"] == {"b": "espesor"}
    assert mapeo["muro"]["filas"] == {"c": "longitud", "h": "alma.ASV", "i": "alma.ASV", "j": "alma.ASH", "k": "alma.ASH"}
    assert "viga" not in mapeo and "losa" not in mapeo  # fuera de alcance: siguen con la duda de mapeo


def test_t4_sin_salida_de_pruebas_y_sin_confirmar_no_se_genera(entorno, monkeypatch):
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_SINT)
    monkeypatch.setattr(pc, "MAPEO_CONFIRMADO", False)
    monkeypatch.delenv(config.ENV_SALIDA_PRUEBAS)
    llamado = []
    monkeypatch.setattr(pc.stp_mived, "generar_stp_mived", lambda *a, **k: llamado.append(1))
    _elemento_visita(entorno, 1, medidas=OBRA_COMPLETA)
    _diseno()
    antes = _arbol(entorno["tmp"] / "dropbox")
    _, eventos = _procesar()
    assert not llamado and not any(e["tipo"] == "pdf_generado" for e in eventos)
    d = next(d for d in _abiertas() if d["campo_afectado"] == "generacion:STP-MIVED")
    assert "mapeo sin confirmar" in d["descripcion_pregunta"] and config.ENV_SALIDA_PRUEBAS in d["descripcion_pregunta"]
    assert _visita()["estado"] == "Con dudas"
    assert _arbol(entorno["tmp"] / "dropbox") == antes
    assert not list((entorno["obra"] / "INFORMES" / "2.DATA PROCESADA").iterdir())


def test_t4_sin_confirmar_el_borrador_solo_va_a_la_salida_de_pruebas_con_la_marca(entorno, monkeypatch):
    _exigir_chromium()
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_SINT)
    monkeypatch.setattr(pc, "MAPEO_CONFIRMADO", False)
    _elemento_visita(entorno, 1, medidas=OBRA_COMPLETA)
    _diseno()
    antes = _arbol(entorno["tmp"] / "dropbox")
    _, eventos = _procesar()
    ruta = Path(next(e for e in eventos if e["tipo"] == "pdf_generado")["ruta"])
    assert ruta.parent == entorno["tmp"] / "salida"
    assert not list((entorno["obra"] / "INFORMES" / "2.DATA PROCESADA").iterdir())
    assert _arbol(entorno["tmp"] / "dropbox") == antes
    doc = pymupdf.open(str(ruta))
    try:
        texto = doc[0].get_text()
    finally:
        doc.close()
    assert "BORRADOR" in texto and "mapeo sin confirmar" in texto


def test_t4_confirmado_la_portada_no_lleva_la_marca(entorno, monkeypatch):
    _exigir_chromium()
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_SINT)
    monkeypatch.setattr(pc, "MAPEO_CONFIRMADO", True)
    _elemento_visita(entorno, 1, medidas=OBRA_COMPLETA)
    _diseno()
    _, eventos = _procesar()
    doc = pymupdf.open(next(e for e in eventos if e["tipo"] == "pdf_generado")["ruta"])
    try:
        assert "BORRADOR" not in doc[0].get_text()
    finally:
        doc.close()


def _capturar_fichas(monkeypatch):
    capturado = {}

    def falso(proyecto, visita, fichas, **k):
        capturado["fichas"], capturado["marca"] = fichas, k.get("marca_borrador")
        return {"ok": False, "ruta": None, "errores": [], "dudas": [], "discrepancias": [], "excluidos": []}
    monkeypatch.setattr(pc.stp_mived, "generar_stp_mived", falso)
    return capturado


def test_t4_columna_con_b_m_y_h_m_llena_las_medidas_c_y_d(entorno, monkeypatch):
    mapeo, _ = pc.cargar_mapeo_stp()
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", mapeo)
    monkeypatch.setattr(pc, "MAPEO_CONFIRMADO", False)
    capturado = _capturar_fichas(monkeypatch)
    _elemento_visita(entorno, 1, "C1 D4", "C1", "EJE D-4")
    _diseno(id_elemento="C1", ejes="EJE D-4", tipo="COLUMNA",  # SINTÉTICO
            campos={"b_m": "0.60", "h_m": "1.50", "acero_longitudinal": '36∅1"', "estribos": '9 EST. ∅3/8" @0.10'})
    _procesar()
    ficha = capturado["fichas"][0]
    assert ficha["fila_stp"] == "col"
    assert ficha["medidas"] == {"c": {"valor_plano_m": 0.60, "medida_acero_campo_m": None},
                                "d": {"valor_plano_m": 1.50, "medida_acero_campo_m": None}}
    assert ficha["barras"] == [(36, '1"')]  # conversión exacta de 36∅1"
    # T9: f, g, h, m, n derivados (propuesta); k y la cuantía las calcula/comprueba el generador, no se copian
    assert ficha["plano"] == {"h": '9 EST. ∅3/8"', "f": '∅3/8"@0.10', "g": '∅3/8"@0.10', "m": '∅1"', "n": '∅1"',
                              "k": "36"}  # T11b: k = total del único grupo
    assert capturado["marca"] == pc.MARCA_BORRADOR
    assert not any(d["campo_afectado"] == "diseno:p001:mapeo" for d in _abiertas())


def test_t4_conversion_exacta_de_barras():
    assert pc.convertir_barras('36∅1"') == [[36, '1"']]
    assert pc.convertir_barras(' 28 Ø 3/4 ” ') == [[28, '3/4"']]
    assert pc.convertir_barras('14ø3/4″') == [[14, '3/4"']]
    for malo in ('4Ø1" 22Ø3/4" 2Ø1"(ESQUINA)', '36∅1" COMPRIMIDAS', '36∅1', '∅1"', '0∅1"', 'pendiente de verificar',
                 '36∅1" + 4∅3/4"', '', None, 36):
        assert pc.convertir_barras(malo) is None


def test_t4_barras_que_no_cuadran_abren_duda_y_no_se_adivinan(entorno, monkeypatch):
    mapeo, _ = pc.cargar_mapeo_stp()
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", mapeo)
    capturado = _capturar_fichas(monkeypatch)
    _elemento_visita(entorno, 1, "C1 D4", "C1", "EJE D-4")
    _diseno(id_elemento="C1", ejes="EJE D-4", tipo="COLUMNA",  # SINTÉTICO
            campos={"b_m": "0.60", "h_m": "1.00", "acero_longitudinal": '4∅1" 22∅3/4"', "estribos": 'x'})
    _procesar()
    assert "fichas" not in capturado or "barras" not in capturado["fichas"][0]
    assert "diseno:p001:barras" in {d["campo_afectado"] for d in _abiertas()}


def test_t4_muro_llena_espesor_y_filas(entorno, monkeypatch):
    mapeo, _ = pc.cargar_mapeo_stp()
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", mapeo)
    capturado = _capturar_fichas(monkeypatch)
    _elemento_visita(entorno, 1, "MH3 C2", "MH3", "EJE C ENTRE 2-3")
    _elemento_visita(entorno, 2, "MC EJE4", "MURO DE CONTENCION PERIMETRAL", "EJE 4 ENTRE A-D")
    _diseno(uid="ed-0001", id_elemento="MH3", ejes="EJE C ENTRE 2-3", tipo="MURO H.A.",  # SINTÉTICO
            campos={"espesor": "0.40", "longitud": "1.80", "alma.ASV": 'Ø1/2"@0.10', "alma.ASH": 'Ø3/8"@0.10'})
    _diseno(uid="ed-0002", id_elemento="MURO DE CONTENCION PERIMETRAL", ejes="EJE 4 ENTRE A-D",
            tipo="MURO DE CONTENCION", campos={"espesor": "0.25", "longitud": PENDIENTE,
                                              "alma.ASV": PENDIENTE, "alma.ASH": PENDIENTE})
    _procesar()
    assert not {d["campo_afectado"] for d in _abiertas()} & {"diseno:p001:mapeo", "diseno:p002:mapeo"}
    muros = {f["id_elemento"] if "id_elemento" in f else f["titulo"]: f for f in capturado.get("fichas", [])
             if f["fila_stp"] == "muro"}
    mh3 = next(f for t, f in muros.items() if "MH3" in t)
    assert mh3["plano"] == {"c": "1.80", "h": 'Ø1/2"@0.10', "i": 'Ø1/2"@0.10', "j": 'Ø3/8"@0.10', "k": 'Ø3/8"@0.10'}
    assert mh3["medidas"]["b"]["valor_plano_m"] == 0.40
    cont = next(f for t, f in muros.items() if "CONTENCION" in t)
    assert cont["plano"] == {} and cont["medidas"]["b"]["valor_plano_m"] == 0.25  # lo pendiente no se rellena


def test_t4_la_viga_sigue_con_la_duda_de_mapeo(entorno, monkeypatch):
    mapeo, _ = pc.cargar_mapeo_stp()
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", mapeo)
    _elemento_visita(entorno, 1, "V1 B4", "V1", "EJE B, ENTRE 1-2")
    _diseno(id_elemento="V1", ejes="EJE B, ENTRE 1-2", tipo="VIGA", campos={"b_m": "0.30"})  # SINTÉTICO
    _procesar()
    assert "diseno:p001:mapeo" in {d["campo_afectado"] for d in _abiertas()}


# ---------- T9 (Etapa 7): derivación de f, g, h, m, n de COLUMNA (propuesta) ----------

def _mapeo_real(monkeypatch, confirmado=False):
    mapeo, _ = pc.cargar_mapeo_stp()
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", mapeo)
    monkeypatch.setattr(pc, "MAPEO_CONFIRMADO", confirmado)
    return mapeo


def test_t9_los_textos_reales_del_plano_se_derivan_exactos():
    # Evidencia: STP entregado de la visita 24 (p. 5, C1) y datos de T1 (C1, C3). El plano imprime Ø (U+00D8).
    assert pc._estribos_cantidad_diametro('9 EST. Ø3/8" @0.10') == '9 EST. Ø3/8"'
    assert pc._estribos_espaciamiento_unico('9 EST. Ø3/8" @0.10') == 'Ø3/8"@0.10'
    assert pc._estribos_cantidad_diametro('10 EST. Ø3/8"@0.10') == '10 EST. Ø3/8"'
    assert pc._estribos_espaciamiento_unico('10 EST. Ø3/8"@0.10') == 'Ø3/8"@0.10'
    assert pc._barras_diametro_unico('36Ø1"') == 'Ø1"'
    # el símbolo y la comilla se copian como vienen impresos
    assert pc._estribos_cantidad_diametro('9 EST. ∅3/8″ @0,10') == '9 EST. ∅3/8″'
    assert pc._estribos_espaciamiento_unico('9 EST. ø3/8” @0,10') == 'ø3/8”@0,10'
    assert pc._barras_diametro_unico('28ø3/4″') == 'ø3/4″'


@pytest.mark.parametrize("texto", ['4 EST.+GAN. Ø3/8" @0.10', '9 EST. Ø3/8" @0.10 Y 5 EST. Ø3/8" @0.15', '9 EST. Ø3/8"',
                                   '9 EST. Ø3/8" @0.10 NODOS', '0 EST. Ø3/8" @0.10', 'EST. Ø3/8" @0.10', '', None, 9,
                                   PENDIENTE, '9 EST. Ø3/8" @ 10', '9 EST Ø3/8" @0.10'])
def test_t9_estribos_que_no_cuadran_dan_none(texto):
    assert pc._estribos_cantidad_diametro(texto) is None
    assert pc._estribos_espaciamiento_unico(texto) is None


@pytest.mark.parametrize("texto", ['4Ø1" 22Ø3/4"', '36Ø1" + 4Ø3/4"', '36Ø1"+GAN.', '36Ø1', 'Ø1"', '0Ø1"', PENDIENTE, '', None])
def test_t9_barras_que_no_cuadran_dan_none(texto):
    assert pc._barras_diametro_unico(texto) is None


def test_t9_el_json_con_regla_desconocida_es_mapeo_roto(tmp_path):
    ruta = tmp_path / "m.json"
    ruta.write_text(json.dumps({"confirmado": True, "filas_stp": {"col": {"derivaciones": {"f": {"campo": "x", "regla": "inventada"}}}}}),
                    encoding="utf-8")
    assert pc.cargar_mapeo_stp(ruta) == ({}, False)


def test_t9_c1_y_c3_llenan_f_g_h_m_n_y_la_cuantia_no_se_copia(entorno, monkeypatch):
    _mapeo_real(monkeypatch)
    capturado = _capturar_fichas(monkeypatch)
    _elemento_visita(entorno, 1, "C1 D4", "C1", "EJE D-4")
    _elemento_visita(entorno, 2, "C3 B4", "C3", "EJE B-4")
    _diseno(uid="ed-0001", id_elemento="C1", ejes="EJE D-4", tipo="COLUMNA",  # SINTÉTICO
            campos={"b_m": "0.60", "h_m": "1.50", "acero_longitudinal": '36Ø1"', "estribos": '9 EST. Ø3/8" @0.10',
                    "cuantia": "9.99"})
    _diseno(uid="ed-0002", id_elemento="C3", ejes="EJE B-4", tipo="COLUMNA",
            campos={"b_m": "0.60", "h_m": "1.50", "acero_longitudinal": '40Ø1"', "estribos": '10 EST. Ø3/8"@0.10',
                    "cuantia": "9.99"})
    _procesar()
    c1, c3 = capturado["fichas"]
    assert c1["plano"] == {"h": '9 EST. Ø3/8"', "f": 'Ø3/8"@0.10', "g": 'Ø3/8"@0.10', "m": 'Ø1"', "n": 'Ø1"', "k": "36"}
    assert c3["plano"] == {"h": '10 EST. Ø3/8"', "f": 'Ø3/8"@0.10', "g": 'Ø3/8"@0.10', "m": 'Ø1"', "n": 'Ø1"', "k": "40"}
    for f in (c1, c3):  # error 12: la cuantía (p) no sale de la derivación ni se copia; k (T11b) es el total del rótulo
        assert "p" not in f["plano"] and "9.99" not in json.dumps(f)
    assert c1["barras"] == [(36, '1"')] and c3["barras"] == [(40, '1"')]
    assert not [d for d in _abiertas() if "derivacion." in d["campo_afectado"]]


def test_t9_la_duda_f_igual_g_no_bloquea_y_es_una_por_ficha(entorno, monkeypatch):
    _mapeo_real(monkeypatch)
    capturado = _capturar_fichas(monkeypatch)
    _elemento_visita(entorno, 1, "C1 D4", "C1", "EJE D-4")
    _diseno(id_elemento="C1", ejes="EJE D-4", tipo="COLUMNA",  # SINTÉTICO
            campos={"b_m": "0.60", "h_m": "1.50", "acero_longitudinal": '36Ø1"', "estribos": '9 EST. Ø3/8" @0.10'})
    _procesar()
    assert capturado["fichas"]  # la ficha sigue: la duda no bloquea
    d = [d for d in _abiertas() if d["campo_afectado"] == "diseno:p001:derivacion_igual"]
    assert len(d) == 1
    assert "f = g" in d[0]["descripcion_pregunta"] and "m = n" in d[0]["descripcion_pregunta"]
    assert "PROPUESTA" in d[0]["descripcion_pregunta"] and "no bloquea" in d[0]["descripcion_pregunta"]
    _procesar()  # otra corrida no la duplica
    assert len([d for d in _abiertas() if d["campo_afectado"] == "diseno:p001:derivacion_igual"]) == 1


def test_t9_la_duda_igual_no_se_repite_si_steven_ya_la_resolvio_ni_con_mapeo_confirmado(entorno, monkeypatch):
    _mapeo_real(monkeypatch)
    _capturar_fichas(monkeypatch)
    _elemento_visita(entorno, 1, "C1 D4", "C1", "EJE D-4")
    _diseno(id_elemento="C1", ejes="EJE D-4", tipo="COLUMNA",  # SINTÉTICO
            campos={"b_m": "0.60", "h_m": "1.50", "acero_longitudinal": '36Ø1"', "estribos": '9 EST. Ø3/8" @0.10'})
    _procesar()
    with _bd() as conn:
        conn.execute("UPDATE dudas_y_hallazgos SET resuelta = 1, respuesta_usuario = 'f = g, de acuerdo' "
                     "WHERE campo_afectado = 'diseno:p001:derivacion_igual'")
    _procesar()
    assert "diseno:p001:derivacion_igual" not in {d["campo_afectado"] for d in _abiertas()}
    with _bd() as conn:
        conn.execute("DELETE FROM dudas_y_hallazgos WHERE campo_afectado = 'diseno:p001:derivacion_igual'")
    monkeypatch.setattr(pc, "MAPEO_CONFIRMADO", True)  # confirmado el mapeo, Steven ya decidió
    _procesar()
    assert "diseno:p001:derivacion_igual" not in {d["campo_afectado"] for d in _abiertas()}


def test_t9_texto_que_no_cuadra_abre_duda_con_el_texto_y_la_fila_queda_sin_llenar(entorno, monkeypatch):
    _mapeo_real(monkeypatch)
    capturado = _capturar_fichas(monkeypatch)
    _elemento_visita(entorno, 1, "C1 D4", "C1", "EJE D-4")
    _diseno(id_elemento="C1", ejes="EJE D-4", tipo="COLUMNA",  # SINTÉTICO
            campos={"b_m": "0.60", "h_m": "1.50", "acero_longitudinal": '4Ø1" 22Ø3/4"', "estribos": '4 EST.+GAN. Ø3/8" @0.10'})
    _procesar()
    assert "fichas" not in capturado  # la ficha queda en espera: no se genera con datos adivinados
    por_campo = {d["campo_afectado"]: d["descripcion_pregunta"] for d in _abiertas()}
    for letra in "hfgmn":
        assert f"diseno:p001:derivacion.{letra}" in por_campo
    assert '4 EST.+GAN. Ø3/8" @0.10' in por_campo["diseno:p001:derivacion.f"]
    assert '4Ø1" 22Ø3/4"' in por_campo["diseno:p001:derivacion.m"]
    assert "diseno:p001:derivacion_igual" not in por_campo  # sin ficha lista no hay nota


def test_t9_una_fila_mapeada_directo_manda_sobre_la_derivacion(entorno, monkeypatch):
    mapeo = _mapeo_real(monkeypatch)
    mapeo["col"] = {**mapeo["col"], "filas": {"f": "esp_nodos"}}
    capturado = _capturar_fichas(monkeypatch)
    _elemento_visita(entorno, 1, "C1 D4", "C1", "EJE D-4")
    _diseno(id_elemento="C1", ejes="EJE D-4", tipo="COLUMNA",  # SINTÉTICO
            campos={"b_m": "0.60", "h_m": "1.50", "acero_longitudinal": '36Ø1"', "estribos": '9 EST. Ø3/8" @0.10',
                    "esp_nodos": '0.075'})
    _procesar()
    plano = capturado["fichas"][0]["plano"]
    assert plano["f"] == "0.075" and plano["g"] == 'Ø3/8"@0.10' and plano["h"] == '9 EST. Ø3/8"'
    # f no se derivó, así que ya no hay par f = g: la nota solo cubre m = n
    d = next(d for d in _abiertas() if d["campo_afectado"] == "diseno:p001:derivacion_igual")
    assert "m = n" in d["descripcion_pregunta"] and "f = g" not in d["descripcion_pregunta"]


def test_t9_campo_vacio_no_abre_duda_de_derivacion(entorno, monkeypatch):
    _mapeo_real(monkeypatch)
    capturado = _capturar_fichas(monkeypatch)
    _elemento_visita(entorno, 1, "C1 D4", "C1", "EJE D-4")
    _diseno(id_elemento="C1", ejes="EJE D-4", tipo="COLUMNA",  # SINTÉTICO
            campos={"b_m": "0.60", "h_m": "1.50", "acero_longitudinal": '36Ø1"', "estribos": PENDIENTE})
    _procesar()
    assert capturado["fichas"][0]["plano"] == {"m": 'Ø1"', "n": 'Ø1"', "k": "36"}  # lo pendiente no se rellena
    assert not [d for d in _abiertas() if "derivacion." in d["campo_afectado"]]


# ---------- T11 (Etapa 7): filas b, e, i, j de COLUMNA (propuesta) ----------

@pytest.mark.parametrize("texto", ["350", " 350 ", "350 Kg/cm2", "350 kg/cm²", "350kg/cm2", "f'c = 350 kg/cm²",
                                   "F'C=350 KG/CM2", "f’c = 350 kg / cm2"])
def test_t11_fc_en_kgcm2_da_el_entero(texto):
    assert pc._fc_kgcm2(texto) == "350"


@pytest.mark.parametrize("texto", ["35 MPa", "350 MPa", "5000 psi", "350 N/mm2", "5 ksi", "350.5", "350,5 kg/cm2", "300-350",
                                   "280 350", "350 kg/cm3", "f'c = 350", "fc alto", "0350", "0", "", None, 350, PENDIENTE])
def test_t11_fc_en_otra_unidad_o_texto_da_none(texto):
    assert pc._fc_kgcm2(texto) is None


@pytest.mark.parametrize("texto,esperado", [("2.95", "2.95"), ("2,95", "2.95"), ("2.95 m", "2.95"), ("2.95m", "2.95"),
                                            ("3", "3"), ("2.950", "2.950"), ("30", "30")])
def test_t11_altura_en_metros(texto, esperado):
    assert pc._metros_impresos(texto) == esperado


@pytest.mark.parametrize("texto", ["295 cm", "2.95 cm", "2.95 mm", "NPT +3.00 - NPT +0.05", "3.00-0.05", "2.95 y 3.10", "0",
                                   "0.0", "31", "-2.95", "alta", "", None, 2.95, PENDIENTE])
def test_t11_altura_que_no_es_metros_da_none(texto):
    assert pc._metros_impresos(texto) is None


def test_t11_barras_por_cara_con_los_datos_reales_de_t10():
    c1 = {"par": "14", "acero": '36∅1"'}
    c3 = {"par": "16", "acero": '40∅1"'}
    assert pc._barras_por_cara("6", c1) == '6-∅1"' and pc._barras_por_cara("14", {**c1, "par": "6"}) == '14-∅1"'
    assert pc._barras_por_cara("6", c3) == '6-∅1"' and pc._barras_por_cara("16", {**c3, "par": "6"}) == '16-∅1"'
    assert pc._barras_por_cara("6", {"par": "14", "acero": '36Ø3/4"'}) == '6-Ø3/4"'  # símbolo y comilla tal como vienen


@pytest.mark.parametrize("x,y,acero", [("6", "15", '36∅1"'), ("6", "14", '40∅1"'), ("6", "14", '4∅1" 22∅3/4"'),
                                       ("6", "14", '36∅1" + 4∅3/4"'), ("6", "14", "36∅1"), ("6", "14", PENDIENTE),
                                       ("6.5", "14", '36∅1"'), ("seis", "14", '36∅1"'), ("0", "14", '36∅1"'),
                                       ("06", "14", '36∅1"'), ("6 barras", "14", '36∅1"'), ("-6", "14", '36∅1"'),
                                       ("6", "catorce", '36∅1"'), ("", "14", '36∅1"'), (None, "14", '36∅1"')])
def test_t11_barras_por_cara_que_no_cuadran_dan_none(x, y, acero):
    assert pc._barras_por_cara(x, {"par": y, "acero": acero}) is None


def test_t11_barras_por_cara_con_la_otra_cara_pendiente_no_comprueba_pero_exige_acero():
    assert pc._barras_por_cara("6", {"par": PENDIENTE, "acero": '36∅1"'}) == '6-∅1"'
    assert pc._barras_por_cara("6", {"par": None, "acero": '36∅1"'}) == '6-∅1"'
    assert pc._barras_por_cara("6", {"par": "14", "acero": PENDIENTE}) is None
    assert pc._barras_por_cara("6", {"par": None, "acero": None}) is None


def test_t11_el_json_con_apoyo_mal_formado_o_ausente_es_mapeo_roto(tmp_path):
    def cargar(der):
        ruta = tmp_path / "m.json"
        ruta.write_text(json.dumps({"confirmado": True, "filas_stp": {"col": {"derivaciones": der}}}), encoding="utf-8")
        return pc.cargar_mapeo_stp(ruta)
    assert cargar({"i": {"campo": "x", "regla": "barras_por_cara"}}) == ({}, False)  # esta regla exige apoyo
    assert cargar({"i": {"campo": "x", "regla": "barras_por_cara", "apoyo": {"par": 5}}}) == ({}, False)
    ok = cargar({"i": {"campo": "x", "regla": "barras_por_cara", "apoyo": {"par": "y", "acero": "z"}}})[0]
    assert ok["col"]["derivaciones"]["i"]["apoyo"] == {"par": "y", "acero": "z"}


_C1_REAL = {"b_m": "0.60", "h_m": "1.50", "fc": PENDIENTE, "altura_m": PENDIENTE, "barras_cara_x": "6", "barras_cara_y": "14",
            "acero_longitudinal": '36∅1"', "estribos": '9 EST. ∅3/8" @0.10'}
_C3_REAL = {"b_m": "0.60", "h_m": "1.50", "fc": PENDIENTE, "altura_m": PENDIENTE, "barras_cara_x": "6", "barras_cara_y": "16",
            "acero_longitudinal": '40∅1"', "estribos": '10 EST. ∅3/8"@0.10'}


def _una_columna(entorno, monkeypatch, campos, mapeo_filas=None):
    mapeo = _mapeo_real(monkeypatch)
    if mapeo_filas:
        mapeo["col"] = {**mapeo["col"], "filas": mapeo_filas}
    capturado = _capturar_fichas(monkeypatch)
    _elemento_visita(entorno, 1, "C1 D4", "C1", "EJE D-4")
    _diseno(id_elemento="C1", ejes="EJE D-4", tipo="COLUMNA", campos=campos)  # SINTÉTICO (textos copiados de T10)
    _procesar()
    return capturado


def test_t11_c1_y_c3_reales_llenan_i_j_y_dejan_b_y_e_vacias(entorno, monkeypatch):
    _mapeo_real(monkeypatch)
    capturado = _capturar_fichas(monkeypatch)
    _elemento_visita(entorno, 1, "C1 D4", "C1", "EJE D-4")
    _elemento_visita(entorno, 2, "C3 B4", "C3", "EJE B-4")
    _diseno(uid="ed-0001", id_elemento="C1", ejes="EJE D-4", tipo="COLUMNA", campos=_C1_REAL)  # SINTÉTICO
    _diseno(uid="ed-0002", id_elemento="C3", ejes="EJE B-4", tipo="COLUMNA", campos=_C3_REAL)
    _procesar()
    c1, c3 = capturado["fichas"]
    assert c1["plano"]["i"] == '6-∅1"' and c1["plano"]["j"] == '14-∅1"'
    assert c3["plano"]["i"] == '6-∅1"' and c3["plano"]["j"] == '16-∅1"'
    for f in (c1, c3):  # lo pendiente jamás llega al STP
        assert "b" not in f["plano"] and "e" not in f["plano"]
        assert PENDIENTE not in json.dumps(f["plano"], ensure_ascii=False)
    assert not [d for d in _abiertas() if "derivacion." in d["campo_afectado"]]


@pytest.mark.parametrize("fc", ["350", "350 Kg/cm2", "f'c = 350 kg/cm²"])
def test_t11_fc_valido_llena_b(entorno, monkeypatch, fc):
    capturado = _una_columna(entorno, monkeypatch, {**_C1_REAL, "fc": fc})
    assert capturado["fichas"][0]["plano"]["b"] == "350"


def test_t11_altura_2_coma_95_llena_e(entorno, monkeypatch):
    capturado = _una_columna(entorno, monkeypatch, {**_C1_REAL, "altura_m": "2,95"})
    assert capturado["fichas"][0]["plano"]["e"] == "2.95"


@pytest.mark.parametrize("campo,texto,letra", [("fc", "35 MPa", "b"), ("fc", "5000 psi", "b"), ("fc", "alto", "b"),
                                               ("altura_m", "295 cm", "e"), ("altura_m", "NPT +3.00", "e"),
                                               ("barras_cara_x", "seis", "i"), ("barras_cara_x", "6.5", "i")])
def test_t11_unidad_o_texto_que_no_cuadra_abre_duda_con_el_texto(entorno, monkeypatch, campo, texto, letra):
    capturado = _una_columna(entorno, monkeypatch, {**_C1_REAL, campo: texto})
    assert "fichas" not in capturado  # la ficha espera: nada adivinado ni convertido
    por_campo = {d["campo_afectado"]: d["descripcion_pregunta"] for d in _abiertas()}
    assert texto in por_campo[f"diseno:p001:derivacion.{letra}"]


def test_t11_total_que_no_cuadra_deja_i_y_j_vacias_con_duda_y_textos_literales(entorno, monkeypatch):
    capturado = _una_columna(entorno, monkeypatch, {**_C1_REAL, "barras_cara_y": "15"})
    assert "fichas" not in capturado
    por_campo = {d["campo_afectado"]: d["descripcion_pregunta"] for d in _abiertas()}
    for letra in "ij":
        texto = por_campo[f"diseno:p001:derivacion.{letra}"]
        assert "'6'" in texto and "'15'" in texto and '36∅1"' in texto and "barras_cara_x" in texto


@pytest.mark.parametrize("campo,letra", [("fc", "b"), ("altura_m", "e"), ("barras_cara_x", "i"), ("barras_cara_y", "j"),
                                         ("estribos", "h")])
def test_t11_pendiente_nunca_llega_al_stp(entorno, monkeypatch, campo, letra):
    capturado = _una_columna(entorno, monkeypatch, {**_C1_REAL, campo: PENDIENTE})
    plano = capturado["fichas"][0]["plano"]
    assert letra not in plano
    assert PENDIENTE not in json.dumps(plano, ensure_ascii=False)


@pytest.mark.parametrize("valor", ["", None, "   "])
def test_t11_campo_vacio_o_ausente_no_llena_la_fila(entorno, monkeypatch, valor):
    campos = {k: v for k, v in _C1_REAL.items() if k not in ("barras_cara_y", "altura_m")}
    campos["fc"] = valor
    capturado = _una_columna(entorno, monkeypatch, campos)
    plano = capturado["fichas"][0]["plano"]
    assert "b" not in plano and "e" not in plano and "j" not in plano
    assert plano["i"] == '6-∅1"'  # con la otra cara ausente no hay cruce; la cara leída se copia exacta


def test_t11_una_fila_mapeada_directo_manda_sobre_b_e_i_j(entorno, monkeypatch):
    campos = {**_C1_REAL, "fc": "350", "altura_m": "2.95", "otro_b": "280", "otro_i": '8-∅3/4"'}
    capturado = _una_columna(entorno, monkeypatch, campos, mapeo_filas={"b": "otro_b", "i": "otro_i"})
    plano = capturado["fichas"][0]["plano"]
    assert plano["b"] == "280" and plano["i"] == '8-∅3/4"'
    assert plano["e"] == "2.95" and plano["j"] == '14-∅1"'


# ---------- T9: arreglos menores ----------

def test_t9_equivalencias_de_sin_tabla_es_vacia_y_no_la_crea(tmp_path):
    import equivalencias_nivel as eq
    conn = sqlite3.connect(str(tmp_path / "sin_tabla.db"))
    conn.row_factory = sqlite3.Row
    try:
        assert eq.equivalencias_de(conn, "P", "S-2") == []
        assert conn.execute("SELECT name FROM sqlite_master WHERE name = 'equivalencias_nivel'").fetchone() is None
    finally:
        conn.close()


def test_t9_el_procesador_cruza_en_una_bd_sin_tabla_de_equivalencias(entorno):
    with _bd() as conn:
        conn.execute("DROP TABLE equivalencias_nivel")
    _elemento_visita(entorno, 1, "C1 D4", "C1", "EJE D-4")
    _diseno(id_elemento="C9", ejes="EJE D-4", tipo="COLUMNA")  # SINTÉTICO: otro ID, sin candidato
    _procesar()  # no falla con «no such table»
    assert "cruce:p001" in {d["campo_afectado"] for d in _abiertas()}
    with _bd() as conn:
        assert conn.execute("SELECT name FROM sqlite_master WHERE name = 'equivalencias_nivel'").fetchone() is None


def test_t9_inicializar_bd_crea_propuestas_proyecto(entorno):
    with _bd() as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(propuestas_proyecto)")}
    assert {"proyecto_id", "campo", "valor", "situacion", "fuente_json", "estado", "creado"} <= cols


# ---------- T11b (Etapa 7): fila k de COLUMNA y una sola duda con todas las filas que faltan ----------

@pytest.mark.parametrize("texto,esperado", [('36∅1"', "36"), ('40∅1"', "40"), ('36Ø1"', "36"), (' 8 ∅3/4" ', "8")])
def test_t11b_k_es_el_total_del_unico_grupo(texto, esperado):
    assert pc._barras_total_unico(texto) == esperado


@pytest.mark.parametrize("texto", ['36∅1" + 4∅3/4"', '36∅1"+GAN.', '0∅1"', "treinta y seis", PENDIENTE, "", None, 36, "36"])
def test_t11b_k_que_no_cuadra_da_none(texto):
    assert pc._barras_total_unico(texto) is None


def test_t11b_c1_y_c3_llenan_k_36_y_40(entorno, monkeypatch):
    _mapeo_real(monkeypatch)
    capturado = _capturar_fichas(monkeypatch)
    _elemento_visita(entorno, 1, "C1 D4", "C1", "EJE D-4")
    _elemento_visita(entorno, 2, "C3 B4", "C3", "EJE B-4")
    _diseno(uid="ed-0001", id_elemento="C1", ejes="EJE D-4", tipo="COLUMNA", campos=_C1_REAL)  # SINTÉTICO
    _diseno(uid="ed-0002", id_elemento="C3", ejes="EJE B-4", tipo="COLUMNA", campos=_C3_REAL)
    _procesar()
    c1, c3 = capturado["fichas"]
    assert c1["plano"]["k"] == "36" and c3["plano"]["k"] == "40"


@pytest.mark.parametrize("acero", ['36∅1" + 4∅3/4"', '36∅1"+GAN.', '0∅1"', "texto", PENDIENTE])
def test_t11b_k_que_no_cuadra_no_se_llena(entorno, monkeypatch, acero):
    capturado = _una_columna(entorno, monkeypatch, {**_C1_REAL, "acero_longitudinal": acero})
    assert "fichas" not in capturado or "k" not in capturado["fichas"][0]["plano"]
    if "fichas" not in capturado and acero != PENDIENTE:  # pendiente = vacío: sin derivación, falla por 'barras'
        assert "diseno:p001:derivacion.k" in {d["campo_afectado"] for d in _abiertas()}


def _sin_k_ni_b_ni_e(monkeypatch):
    """Mapeo real sin la derivación de k: el generador real ve b, e y k vacías (SINTÉTICO)."""
    mapeo = _mapeo_real(monkeypatch)
    der = dict(mapeo["col"]["derivaciones"])
    der.pop("k")
    mapeo["col"] = {**mapeo["col"], "derivaciones": der}


def _dudas_de_generacion():
    return [d for d in _abiertas() if d["campo_afectado"] == "generacion:p001"]


def test_t11b_una_sola_duda_lista_b_e_k_en_orden_fijo(entorno, monkeypatch):
    _sin_k_ni_b_ni_e(monkeypatch)
    _elemento_visita(entorno, 1, "C1 D4", "C1", "EJE D-4")
    _diseno(id_elemento="C1", ejes="EJE D-4", tipo="COLUMNA", campos=_C1_REAL)  # SINTÉTICO
    _procesar()
    ds = _dudas_de_generacion()
    assert len(ds) == 1
    texto = ds[0]["descripcion_pregunta"]
    assert texto.index("plano.b") < texto.index("plano.e") < texto.index("plano.k")
    assert "faltan 3 dato(s)" in texto and "(1) plano.b" in texto
    _procesar()  # segunda corrida: la misma duda, el mismo texto
    ds = _dudas_de_generacion()
    assert len(ds) == 1 and ds[0]["descripcion_pregunta"] == texto


def test_t11b_el_orden_de_las_obligatorias_no_depende_de_pythonhashseed():
    import subprocess
    import sys
    raiz = Path(pc.__file__).parent
    codigo = ("from generators import stp_mived as s; "
              "r, dudas, _ = s._filas_de_ficha({'titulo': 'C1', 'plano': {}, 'medidas': {}}, 'COLUMNA', 'col', None); "
              "print([d['campo_afectado'] for d in dudas])")
    salidas = {subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, cwd=str(raiz),
                              env={**os.environ, "PYTHONHASHSEED": semilla}, check=True).stdout for semilla in ("1", "2", "3", "4")}
    assert len(salidas) == 1 and "plano.b" in next(iter(salidas))


def test_t11b_al_completar_e_la_misma_duda_se_actualiza_y_se_audita(entorno, monkeypatch):
    _sin_k_ni_b_ni_e(monkeypatch)
    _elemento_visita(entorno, 1, "C1 D4", "C1", "EJE D-4")
    _diseno(id_elemento="C1", ejes="EJE D-4", tipo="COLUMNA", campos=_C1_REAL)  # SINTÉTICO
    _procesar()
    antes = _dudas_de_generacion()[0]
    with _bd() as conn:
        fila = conn.execute("SELECT uid, datos_diseno_json FROM elementos_diseno").fetchone()
        datos = {**json.loads(fila["datos_diseno_json"]), "altura_m": "2.95"}
        conn.execute("UPDATE elementos_diseno SET datos_diseno_json = ? WHERE uid = ?", (json.dumps(datos), fila["uid"]))
    _procesar()
    despues = _dudas_de_generacion()
    assert len(despues) == 1 and despues[0]["id"] == antes["id"]
    assert "plano.e" not in despues[0]["descripcion_pregunta"] and "faltan 2 dato(s)" in despues[0]["descripcion_pregunta"]
    assert "plano.b" in despues[0]["descripcion_pregunta"] and "plano.k" in despues[0]["descripcion_pregunta"]
    with _bd() as conn:
        aud = conn.execute("SELECT usuario, detalle_json FROM auditoria WHERE accion = 'ACTUALIZAR_DUDA' AND entidad_id = ?",
                           (str(antes["id"]),)).fetchall()
    assert len(aud) == 1 and aud[0]["usuario"] == "prueba"
    assert "plano.e" in json.loads(aud[0]["detalle_json"])["pregunta_anterior"]


def test_t11b_sin_faltantes_la_duda_agrupada_se_cierra(entorno, monkeypatch):
    _sin_k_ni_b_ni_e(monkeypatch)
    _elemento_visita(entorno, 1, "C1 D4", "C1", "EJE D-4")
    _diseno(id_elemento="C1", ejes="EJE D-4", tipo="COLUMNA", campos=_C1_REAL)  # SINTÉTICO
    _procesar()
    assert _dudas_de_generacion()
    _mapeo_real(monkeypatch)  # vuelve la derivación de k; b y e se completan en el plano
    with _bd() as conn:
        fila = conn.execute("SELECT uid, datos_diseno_json FROM elementos_diseno").fetchone()
        datos = {**json.loads(fila["datos_diseno_json"]), "altura_m": "2.95", "fc": "350"}
        conn.execute("UPDATE elementos_diseno SET datos_diseno_json = ? WHERE uid = ?", (json.dumps(datos), fila["uid"]))
    _capturar_fichas(monkeypatch)
    _procesar()
    assert not _dudas_de_generacion()
