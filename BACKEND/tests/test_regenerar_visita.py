# BACKEND/tests/test_regenerar_visita.py
# Etapa 5 · B3g-2 — Regenerar el informe de una visita ya «Procesada» (BACKEND/regenerar_visita.py).
#
# Mismo modelo y mismo material que test_procesar_cola.py: BD, Dropbox, datos, caché y salida temporales, todo
# SINTÉTICO (obra, plano, elementos, fotos y «formularios» inventados solo para probar las reglas). Las pruebas que generan
# el STP (Chromium de Playwright) se saltan con un mensaje si el navegador no está instalado.
import hashlib
import json
from pathlib import Path

import pytest

import informes_obra
import procesador_cola as pc
import regenerar_visita as rg
from test_procesar_cola import (MAPEO_SINT, OBRA_COMPLETA, PID, VID, _abiertas, _arbol, _bd, _diseno,  # noqa: F401
                                _elemento_visita, _exigir_chromium, _procesar, _visita, cliente, entorno)


def _sha(ruta) -> str:
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def _procesada(entorno, monkeypatch):
    """Una visita que el procesador dejó «Procesada» con su STP (necesita Chromium). Devuelve la ruta del original."""
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_SINT)
    _elemento_visita(entorno, 1, medidas=OBRA_COMPLETA)
    _diseno()
    _, eventos = _procesar()
    assert _visita()["estado"] == "Procesada"
    return Path(next(e for e in eventos if e["tipo"] == "pdf_generado")["ruta"])


def _marcar_procesada():
    with _bd() as conn:
        conn.execute("UPDATE visitas SET estado = 'Procesada' WHERE id = ?", (VID,))


def _regenerar(visita_id=VID):
    t = rg.lanzar_regeneracion(visita_id, en_hilo=False, usuario="prueba")
    t = pc.obtener_trabajo(t["id"])
    return t, pc.listar_eventos(t["id"])["eventos"]


def _conteos():
    with _bd() as conn:
        return (conn.execute("SELECT COUNT(*) FROM elementos_visita WHERE visita_id = ?", (VID,)).fetchone()[0],
                conn.execute("SELECT COUNT(*) FROM dudas_y_hallazgos WHERE visita_id = ?", (VID,)).fetchone()[0])


def _acciones():
    with _bd() as conn:
        return [(f["accion"], json.loads(f["detalle_json"])) for f in conn.execute(
            "SELECT accion, detalle_json FROM auditoria WHERE modulo = 'PROCESADOR' ORDER BY id")]


# ---------- Con Chromium: la versión nueva ----------

def test_regenera_la_v2_y_luego_la_v3_sin_tocar_el_original(entorno, monkeypatch):
    _exigir_chromium()
    original = _procesada(entorno, monkeypatch)
    sha, salida_antes, filas = _sha(original), _visita()["salida_json"], _conteos()

    t, eventos = _regenerar()
    assert t["estado"] == "terminado" and t["tipo"] == "visita" and t["resumen"]["regenerar"] is True
    inicio = next(e for e in eventos if e["tipo"] == "visita_inicio")
    assert inicio["regenerar"] is True and inicio["estado_anterior"] == "Procesada"
    pdf = [e for e in eventos if e["tipo"] == "pdf_generado"]
    assert len(pdf) == 1 and pdf[0]["con_dudas"] is False
    v2 = Path(pdf[0]["ruta"])
    assert v2.name == "Obra Sintetica - STP - LOSA S-4 Completivo - 02-10-2026 v2.pdf" and v2.parent == original.parent
    assert v2.stat().st_size < 30_000_000
    assert _sha(original) == sha                      # el original, intacto (§5.2)
    assert not (entorno["tmp"] / "salida" / pc.CARPETA_DE_PASO).exists()
    fin = next(e for e in eventos if e["tipo"] == "visita_fin")
    assert fin["regenerar"] is True and fin["estado"] == "Procesada" and fin["generado"] is True
    assert [e["tipo"] for e in eventos][-1] == "fin" and eventos[-1]["regenerar"] is True
    v = _visita()
    assert v["estado"] == "Procesada" and v["salida_json"] == salida_antes   # el estado y la salida no cambian
    assert _conteos() == filas and _abiertas() == []                          # no se borra ni se abre nada

    _, eventos = _regenerar()                                                  # una segunda regeneración
    v3 = Path(next(e for e in eventos if e["tipo"] == "pdf_generado")["ruta"])
    assert v3.name.endswith("02-10-2026 v3.pdf") and _sha(original) == sha


def test_el_pdf_nuevo_sale_primero_en_la_lista_de_informes(entorno, monkeypatch):
    _exigir_chromium()
    original = _procesada(entorno, monkeypatch)
    _, eventos = _regenerar()
    nuevo = next(e for e in eventos if e["tipo"] == "pdf_generado")["ruta"]
    informes = informes_obra.informes_de_obra(PID)
    assert [i["ruta"] for i in informes] == [nuevo, str(original)]
    assert informes[0]["version"] == 2 and informes[1]["version"] == 1 and informes[0]["existe"] is True
    assert informes_obra.ruta_registrada(nuevo)       # se abre con /api/informes/archivo


def test_los_fi_no_se_tocan_ni_se_generan(entorno, monkeypatch):
    _exigir_chromium()
    original = _procesada(entorno, monkeypatch)
    fi = entorno["obra"] / "FORMULARIOS" / "MIVED" / "FORMULARIOS NO FIRMADOS"
    fi.mkdir(parents=True)
    ruta_fi = fi / "MIVED - OBRA SINT-LOSAS Y VIGAS COMPLETIVO SOTANO -4.PDF"
    ruta_fi.write_bytes(b"%PDF-1.4 FI SINT")
    with _bd() as conn:  # la visita ahora también pide el FI-02: la regeneración igual no lo toca
        conn.execute("""UPDATE visitas SET formatos_solicitados = '["STP-MIVED", "FI-02"]' WHERE id = ?""", (VID,))

    def no_debe_llamarse(self, *a, **k):
        raise AssertionError("la regeneración no debe generar FI")
    monkeypatch.setattr(pc.ProcesoVisita, "_generar_fi", no_debe_llamarse)
    antes = _arbol(entorno["tmp"] / "dropbox")
    sha_fi = _sha(ruta_fi)
    _, eventos = _regenerar()
    pdf = [e for e in eventos if e["tipo"] == "pdf_generado"]
    assert [e["formato"] for e in pdf] == ["STP-MIVED"] and Path(pdf[0]["ruta"]).name.endswith(" v2.pdf")
    assert _sha(ruta_fi) == sha_fi and _arbol(entorno["tmp"] / "dropbox") == antes   # Dropbox y FI, intactos
    assert _sha(original)
    fin = next(a for a in _acciones() if a[0] == "REGENERAR_VISITA")[1]
    assert fin["fi"] == "sin tocar" and fin["estado"] == "Procesada"


def test_la_auditoria_registra_el_salto_de_p3_aunque_ya_haya_un_stp_de_su_fecha(entorno, monkeypatch):
    _exigir_chromium()
    original = _procesada(entorno, monkeypatch)
    # Un STP de la fecha en INFORMES\2.DATA PROCESADA haría saltar P3 en el procesador normal: aquí no.
    stp = entorno["obra"] / "INFORMES" / "2.DATA PROCESADA" / "Obra Sintetica - STP - Losa S4 Completivo - 02-10-2026.pdf"
    stp.write_bytes(b"%PDF-1.4 SINT")
    antes = _arbol(entorno["tmp"] / "dropbox")
    _, eventos = _regenerar()
    assert any(e["tipo"] == "pdf_generado" for e in eventos) and _abiertas() == []
    assert _arbol(entorno["tmp"] / "dropbox") == antes and _sha(original)
    p3 = [d for a, d in _acciones() if a == "REGENERAR_SIN_P3"]
    assert len(p3) == 1 and p3[0]["visita_id"] == VID and "P3" in p3[0]["motivo"] and p3[0]["trabajo"]
    assert {"LANZAR_REGENERACION", "REGENERAR_VISITA", "PUBLICAR_PDF", "TERMINAR_TRABAJO"} <= {a for a, _ in _acciones()}
    lanzar = next(d for a, d in _acciones() if a == "LANZAR_REGENERACION")
    assert lanzar["regenerar"] is True and lanzar["visitas"] == [VID]


# ---------- Sin Chromium: bloqueos, estados y errores ----------

def test_con_una_duda_abierta_no_genera_y_la_visita_sigue_procesada(entorno, monkeypatch):
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_SINT)
    _elemento_visita(entorno, 1, medidas=OBRA_COMPLETA)
    _diseno()
    _marcar_procesada()
    with _bd() as conn:  # una duda de la visita sin responder
        conn.execute("""INSERT INTO dudas_y_hallazgos (proyecto_id, visita_id, id_elemento, categoria, campo_afectado,
                        descripcion_pregunta, creado) VALUES (?, ?, '(visita)', 'DUDA_BLOQUEANTE', 'clase', 'SINT', 'x')""",
                     (PID, VID))
    filas = _conteos()
    t, eventos = _regenerar()
    assert t["estado"] == "terminado"
    assert not any(e["tipo"] == "pdf_generado" for e in eventos)
    assert not list((entorno["tmp"] / "salida").rglob("*.pdf"))
    aviso = next(e for e in eventos if e["tipo"] == "aviso")
    assert "No se generó ninguna versión nueva" in aviso["texto"] and "dudas de la visita abiertas" in aviso["texto"]
    fin = next(e for e in eventos if e["tipo"] == "visita_fin")
    assert fin["estado"] == "Procesada" and fin["generado"] is False and fin["pdf"] == []
    assert _visita()["estado"] == "Procesada" and _conteos() == filas
    assert any(d["campo_afectado"] == "clase" for d in _abiertas())   # la duda sigue abierta: no se borra ni se cierra


def test_elementos_en_espera_abren_su_duda_pero_no_cambian_el_estado(entorno, monkeypatch):
    _elemento_visita(entorno, 1)
    _diseno(confirmado=False)            # plano con datos sin confirmar
    _marcar_procesada()
    _, eventos = _regenerar()
    assert any(e["tipo"] == "duda" and e["campo"] == "diseno:p001" for e in eventos)
    assert not any(e["tipo"] == "pdf_generado" for e in eventos)
    assert "1 elementos en espera" in next(e for e in eventos if e["tipo"] == "aviso")["texto"]
    assert _visita()["estado"] == "Procesada"
    assert any(d["campo_afectado"] == "diseno:p001" for d in _abiertas())
    assert [a for a, _ in _acciones() if a == "REGENERAR_SIN_P3"]    # el salto de P3 se audita aunque no se genere


def test_no_corre_el_lector_ni_relee_la_visita(entorno, monkeypatch):
    _elemento_visita(entorno, 1)
    _diseno(confirmado=False)
    _marcar_procesada()

    def prohibido(*a, **k):
        raise AssertionError("la regeneración no debe leer el PDF de la visita")
    monkeypatch.setattr(pc.ProcesoVisita, "_correr_lector", prohibido)
    monkeypatch.setattr(pc.lector_visita, "cargar_visita", prohibido)
    filas = _conteos()
    t, _ = _regenerar()
    assert t["estado"] == "terminado" and _conteos()[0] == filas[0]


def test_una_visita_sin_stp_entre_sus_formatos_no_se_regenera(entorno, monkeypatch):
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_SINT)
    _elemento_visita(entorno, 1, medidas=OBRA_COMPLETA)
    _diseno()
    _marcar_procesada()
    with _bd() as conn:
        conn.execute("""UPDATE visitas SET formatos_solicitados = '["FI-02"]' WHERE id = ?""", (VID,))
    _, eventos = _regenerar()
    assert not any(e["tipo"] == "pdf_generado" for e in eventos)
    assert "el único formato que se regenera" in next(e for e in eventos if e["tipo"] == "aviso")["texto"]


# ---------- API ----------

def test_api_202_y_el_trabajo_se_sigue_como_cualquier_otro(cliente, entorno):
    _elemento_visita(entorno, 1)
    _diseno(confirmado=False)
    _marcar_procesada()
    r = cliente.post(f"/api/visitas/{VID}/regenerar")
    assert r.status_code == 202
    t = r.json()["trabajo"]
    assert t["tipo"] == "visita" and t["visitas"] == [VID] and r.json()["mensaje"] == "Regeneración lanzada."
    pc.esperar(t["id"], 60)
    eventos = cliente.get(f"/api/trabajos/{t['id']}/eventos").json()
    assert eventos["estado"] == "terminado"
    assert {"visita_inicio", "elemento_inicio", "duda", "aviso", "visita_fin", "fin"} <= {e["tipo"] for e in eventos["eventos"]}


def test_api_visita_inexistente_404_y_no_procesada_409(cliente, entorno):
    r = cliente.post("/api/visitas/no-existe/regenerar")
    assert r.status_code == 404 and "no-existe" in r.json()["detail"]
    for estado in ("Sin procesar", "En cola", "Con dudas", "En proceso"):
        with _bd() as conn:
            conn.execute("UPDATE visitas SET estado = ? WHERE id = ?", (estado, VID))
        r = cliente.post(f"/api/visitas/{VID}/regenerar")
        assert r.status_code == 409 and estado in r.json()["detail"] and "Procesar" in r.json()["detail"]
    with _bd() as conn:
        assert conn.execute("SELECT COUNT(*) FROM trabajos").fetchone()[0] == 0   # un 409/404 no crea trabajo


def test_api_con_un_trabajo_en_curso_da_409_con_el_mismo_cerrojo(cliente, entorno):
    _marcar_procesada()
    with _bd() as conn:
        conn.execute("""INSERT INTO trabajos (id, tipo, visitas_json, estado, usuario, creado)
                        VALUES ('trab-sint', 'visita', '[]', 'corriendo', 'prueba', 'x')""")
    r = cliente.post(f"/api/visitas/{VID}/regenerar")
    assert r.status_code == 409 and "trab-sint" in r.json()["detail"]
    with _bd() as conn:  # y a la inversa: mientras corre una regeneración, «procesar» también da 409
        conn.execute("UPDATE trabajos SET estado = 'terminado'")
        conn.execute("UPDATE visitas SET estado = 'Sin procesar' WHERE id = ?", (VID,))
        conn.execute("""INSERT INTO trabajos (id, tipo, visitas_json, estado, usuario, creado)
                        VALUES ('trab-regen', 'visita', '[]', 'corriendo', 'prueba', 'x')""")
    assert cliente.post(f"/api/visitas/{VID}/procesar").status_code == 409


def test_procesar_sigue_sin_aceptar_una_visita_procesada(cliente, entorno):
    _marcar_procesada()
    r = cliente.post(f"/api/visitas/{VID}/procesar")
    assert r.status_code == 409 and "Procesada" in r.json()["detail"]


def test_un_error_se_registra_y_la_visita_sigue_procesada(entorno, monkeypatch):
    _marcar_procesada()

    def falla(self, visita):
        raise RuntimeError("fallo SINTÉTICO")
    monkeypatch.setattr(rg.ProcesoRegeneracion, "_procesar", falla)
    t, eventos = _regenerar()
    assert t["estado"] == "fallido" and "fallo SINTÉTICO" in t["error"]
    assert next(e for e in eventos if e["tipo"] == "visita_fin")["regenerar"] is True
    assert _visita()["estado"] == "Procesada"      # nunca pasó por «En proceso»
