# BACKEND/tests/test_zona_planta.py
# Etapa 7 · T12 — LOCALIZACION = solo la planta (sin cajetín), con su zona por hoja (PLANES/etapa-7.md, T12).
# Todo # SINTÉTICO: el vectorial se dibuja aquí con PyMuPDF (retícula de globos, cuerpo de planta, cajetín con textos
# sueltos y una tabla); no hay ningún dato de obra real.
import io
import json

import pymupdf
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import config
import database
import main
import visor
from generators.comun import localizacion
from plano import zona_planta
from reglas_ingenieria import PENDIENTE, calcular_grosor_recuadro_rojo

AZUL = (0, 0, 255)
CAJETIN = pymupdf.Rect(830, 40, 980, 760)


def _globo(pag, cx, cy, texto, direccion):
    pag.draw_circle((cx, cy), 9.5, color=(0, 0, 0), width=0.7)
    pag.insert_text((cx - 3, cy + 3.5), texto, fontsize=9)
    pag.draw_line((cx + direccion[0] * 9.5, cy + direccion[1] * 9.5), (cx + direccion[0] * 60, cy + direccion[1] * 60),
                  color=(0, 0, 0), width=0.7)


def _cajetin_y_tabla(pag):
    """Cajetín a la derecha (relleno azul para detectarlo en la imagen), textos sueltos y una tabla de rótulos."""
    pag.draw_rect(CAJETIN, color=(0, 0, 0), fill=(0.8, 0.8, 1), width=1)
    pag.insert_text((850, 100), "1", fontsize=9)         # sueltos: ni alineados ni distintos entre sí
    pag.insert_text((905, 300), "A", fontsize=9)
    for i, t in enumerate("ABC"):                          # fila de encabezados de tabla (3 rótulos distintos, más chicos)
        pag.insert_text((850 + 35 * i, 450), t, fontsize=6)
    for j in range(4):                                     # columna de celdas repetidas
        pag.insert_text((860, 500 + 20 * j), "1", fontsize=6)


def _pdf(un_lado=True, letras="ABCD", numeros="1234", con_cuerpo=True) -> bytes:
    """
    Hoja 1: planta con retícula. `un_lado=True`: los globos solo en la fila de abajo y la columna de la izquierda (como en
    una hoja real: fuera del contorno, y la planta se extiende más allá de ellos hacia arriba y a la derecha).
    `un_lado=False`: globos en los dos extremos. Hoja 2: solo texto (sin ejes).
    """
    doc = pymupdf.open()
    p = doc.new_page(width=1000, height=800)
    xs = [200 + 120 * i for i in range(len(letras))]
    ys = [200 + 100 * i for i in range(len(numeros))]
    if con_cuerpo:
        p.draw_rect(pymupdf.Rect(150, 130, 700, 660), color=(0, 0, 0), width=2)      # contorno: sobrepasa la retícula
        p.draw_rect(pymupdf.Rect(300, 300, 360, 360), color=(0, 0, 0), fill=(0, 0, 0))
    for x, t in zip(xs, letras):
        _globo(p, x, 700, t, (0, -1))
        if not un_lado:
            _globo(p, x, 100, t, (0, 1))
    for y, t in zip(ys, numeros):
        _globo(p, 100, y, t, (1, 0))
        if not un_lado:
            _globo(p, 760, y, t, (-1, 0))
    _cajetin_y_tabla(p)
    q = doc.new_page(width=1000, height=800)
    q.insert_text((100, 100), "NOTAS GENERALES", fontsize=14)
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
        yield c, tmp_path


def _obra(c, vectorial: bytes) -> str:
    pid = c.post("/api/proyectos", json={"nombre": "Obra Zona"}).json()["proyecto"]["id"]
    r = c.post(f"/api/proyectos/{pid}/planos", files={"vectorial": ("vec.pdf", vectorial, "application/pdf"),
                                                       "sellado": ("sel.pdf", _sellado(), "application/pdf")},
               data={"certifico": "true"})
    assert r.status_code == 201, r.text
    return pid


def _filas(sql, *args):
    conn = database.get_connection()
    try:
        return [dict(f) for f in conn.execute(sql, args)]
    finally:
        conn.close()


def _png(r) -> Image.Image:
    assert r.status_code == 200, r.text
    return Image.open(io.BytesIO(r.content)).convert("RGB")


# ---------- Rótulos de ejes ----------

def test_detecta_la_reticula_de_un_lado_y_no_se_deja_enganar_por_cajetin_ni_tabla():
    with pymupdf.open(stream=_pdf(), filetype="pdf") as doc:
        d = zona_planta.detectar_rotulos_ejes(doc[0])
    assert sorted(r["texto"] for r in d["letras"]) == list("ABCD")
    assert sorted(r["texto"] for r in d["numeros"]) == list("1234")
    x0, y0, x1, y1 = d["ejes_rect"]
    assert x1 < CAJETIN.x0 and 90 < x0 < 110 and y1 < 720      # ninguna «A»/«1» del cajetín ni de la tabla
    assert d["motivo"] is None


def test_detecta_los_globos_de_los_dos_extremos_como_un_solo_conjunto():
    with pymupdf.open(stream=_pdf(un_lado=False), filetype="pdf") as doc:
        d = zona_planta.detectar_rotulos_ejes(doc[0])
    assert len(d["letras"]) == 8 and len(d["numeros"]) == 8
    x0, y0, x1, y1 = d["ejes_rect"]
    assert y0 < 105 and y1 > 700 and x0 < 105 and x1 > 755    # envuelve los dos extremos


@pytest.mark.parametrize("letras,numeros", [("A", "1234"), ("ABCD", "1")])
def test_con_una_letra_o_un_numero_no_hay_ejes(letras, numeros):
    with pymupdf.open(stream=_pdf(letras=letras, numeros=numeros), filetype="pdf") as doc:
        d = zona_planta.detectar_rotulos_ejes(doc[0])
    assert d["ejes_rect"] is None and "al menos 2 letras y 2 números" in d["motivo"]


def test_el_primo_y_los_rotulos_repetidos_en_fila_no_cuentan_como_ejes():
    doc = pymupdf.open()
    p = doc.new_page(width=500, height=500)
    for i in range(4):                       # «1 1 1 1» en una fila: tabla, no retícula
        p.insert_text((100 + 50 * i, 100), "1", fontsize=9)
    p.insert_text((100, 300), "A'", fontsize=9)
    p.insert_text((200, 300), "B", fontsize=9)
    d = zona_planta.detectar_rotulos_ejes(p)
    assert d["numeros"] == [] and d["ejes_rect"] is None
    doc.close()


# ---------- Propuesta ----------

def test_propuesta_es_la_envolvente_con_margen_incluye_el_cuerpo_y_deja_fuera_el_cajetin(entorno):
    c, _ = entorno
    pid = _obra(c, _pdf())
    r = c.post(f"/api/proyectos/{pid}/visor/hojas/1/zona-planta/propuesta")
    assert r.status_code == 200, r.text
    z = r.json()
    assert z["estado"] == "pendiente de verificar" and z["origen"] == "propuesta_ejes" and z["escrito"] is True
    x0, y0, x1, y1 = z["rect"]
    ex0, ey0, ex1, ey1 = z["ejes_rect"]
    assert z["fuente"]["margen_pt"] == zona_planta.MARGEN_PT == 30.0
    # contiene todos los ejes con el margen y el contorno de la planta (que sobrepasa la retícula) con su margen
    assert x0 <= ex0 - 30 + 0.5 and y1 >= ey1 + 30 - 0.5
    assert x1 >= 700 + 30 - 1 and y0 <= 130 - 30 + 1
    assert x1 < CAJETIN.x0                                   # sin cajetín
    assert zona_planta.contiene(z["rect"], z["ejes_rect"])
    # la duda de proyecto y la auditoría con el usuario del proceso
    dudas = _filas("SELECT * FROM dudas_y_hallazgos WHERE campo_afectado LIKE 'plano:%:zona_planta'")
    assert len(dudas) == 1 and dudas[0]["visita_id"] is None and dudas[0]["campo_afectado"] == f"plano:1:p1:zona_planta"
    aud = _filas("SELECT * FROM auditoria WHERE modulo = 'ZONA_PLANTA'")
    assert [a["accion"] for a in aud] == ["PROPONER_ZONA"]
    # GET la devuelve igual, con ejes_rect
    g = c.get(f"/api/proyectos/{pid}/visor/hojas/1/zona-planta").json()
    assert g["rect"] == z["rect"] and g["ejes_rect"] == z["ejes_rect"] and g["estado"] == "pendiente de verificar"


def test_proponer_dos_veces_es_idempotente(entorno):
    c, _ = entorno
    pid = _obra(c, _pdf())
    c.post(f"/api/proyectos/{pid}/visor/hojas/1/zona-planta/propuesta")
    r = c.post(f"/api/proyectos/{pid}/visor/hojas/1/zona-planta/propuesta").json()
    assert r["escrito"] is False
    assert len(_filas("SELECT * FROM auditoria WHERE modulo = 'ZONA_PLANTA'")) == 1
    assert len(_filas("SELECT * FROM dudas_y_hallazgos WHERE campo_afectado LIKE 'plano:%'")) == 1


def test_hoja_sin_ejes_queda_vacia_con_motivo_y_duda(entorno):
    c, _ = entorno
    pid = _obra(c, _pdf())
    z = c.post(f"/api/proyectos/{pid}/visor/hojas/2/zona-planta/propuesta").json()
    assert z["estado"] == "vacia" and z["rect"] is None and z["ejes_rect"] is None
    assert "al menos 2 letras y 2 números" in z["motivo"]
    duda = _filas("SELECT * FROM dudas_y_hallazgos WHERE campo_afectado = 'plano:1:p2:zona_planta' AND resuelta = 0")
    assert len(duda) == 1 and PENDIENTE in duda[0]["descripcion_pregunta"]


def test_con_una_sola_letra_la_propuesta_queda_vacia(entorno):
    c, _ = entorno
    pid = _obra(c, _pdf(letras="A"))
    z = c.post(f"/api/proyectos/{pid}/visor/hojas/1/zona-planta/propuesta").json()
    assert z["estado"] == "vacia" and z["rect"] is None


def test_la_propuesta_no_pisa_una_zona_confirmada(entorno):
    c, _ = entorno
    pid = _obra(c, _pdf())
    prop = c.post(f"/api/proyectos/{pid}/visor/hojas/1/zona-planta/propuesta").json()
    r = c.put(f"/api/proyectos/{pid}/visor/hojas/1/zona-planta", json={"rect": prop["rect"]})
    assert r.status_code == 200 and r.json()["estado"] == "confirmado" and r.json()["origen"] == "propuesta_ejes"
    otra = c.post(f"/api/proyectos/{pid}/visor/hojas/1/zona-planta/propuesta").json()
    assert otra["estado"] == "confirmado" and otra["escrito"] is False and otra["rect"] == prop["rect"]
    assert [a["accion"] for a in _filas("SELECT accion FROM auditoria WHERE modulo = 'ZONA_PLANTA' ORDER BY id")] \
        == ["PROPONER_ZONA", "CONFIRMAR_ZONA"]


# ---------- Confirmar y regla anti-zoom ----------

def test_una_zona_que_corta_un_eje_es_zoom_parcial_y_se_rechaza(entorno):
    c, _ = entorno
    pid = _obra(c, _pdf())
    r = c.put(f"/api/proyectos/{pid}/visor/hojas/1/zona-planta", json={"rect": [300, 130, 700, 660]})  # sin los globos de la izquierda
    assert r.status_code == 400
    assert "la zona corta la planta (zoom parcial, error 1): debe contener todos los ejes" in r.json()["detail"]
    assert _filas("SELECT * FROM zonas_planta") == []


def test_confirmar_una_zona_ajustada_es_manual_y_cierra_la_duda(entorno):
    c, _ = entorno
    pid = _obra(c, _pdf())
    prop = c.post(f"/api/proyectos/{pid}/visor/hojas/1/zona-planta/propuesta").json()
    x0, y0, x1, y1 = prop["rect"]
    r = c.put(f"/api/proyectos/{pid}/visor/hojas/1/zona-planta", json={"rect": [x0 - 5, y0, x1 + 5, y1]})
    assert r.status_code == 200
    z = r.json()
    assert z["estado"] == "confirmado" and z["origen"] == "manual"
    assert _filas("SELECT resuelta FROM dudas_y_hallazgos WHERE campo_afectado = 'plano:1:p1:zona_planta'")[0]["resuelta"] == 1
    aud = _filas("SELECT * FROM auditoria WHERE accion = 'CONFIRMAR_ZONA'")
    assert len(aud) == 1 and json.loads(aud[0]["detalle_json"])["origen"] == "manual"


def test_sin_ejes_detectables_se_acepta_la_zona_manual_y_se_audita(entorno):
    c, _ = entorno
    pid = _obra(c, _pdf())
    r = c.put(f"/api/proyectos/{pid}/visor/hojas/2/zona-planta", json={"rect": [50, 50, 400, 300]})
    assert r.status_code == 200 and r.json()["estado"] == "confirmado" and r.json()["origen"] == "manual"
    d = json.loads(_filas("SELECT detalle_json FROM auditoria WHERE accion = 'CONFIRMAR_ZONA'")[0]["detalle_json"])
    assert d["sin_ejes_detectables"] is True


def test_usuario_explicito_en_las_funciones_se_audita_tal_cual(entorno):
    c, _ = entorno
    pid = _obra(c, _pdf())
    zona_planta.proponer_zona(pid, 1, usuario="prueba-t12a")
    z = zona_planta.obtener_zona(pid, 1)
    zona_planta.guardar_zona(pid, 1, z["rect"], usuario="prueba-t12a")
    assert {a["usuario"] for a in _filas("SELECT usuario FROM auditoria WHERE modulo = 'ZONA_PLANTA'")} == {"prueba-t12a"}


def test_rect_invalido_y_hoja_inexistente(entorno):
    c, _ = entorno
    pid = _obra(c, _pdf())
    assert c.put(f"/api/proyectos/{pid}/visor/hojas/1/zona-planta", json={"rect": [0, 0, 5000, 5000]}).status_code == 422
    assert c.get(f"/api/proyectos/{pid}/visor/hojas/9/zona-planta").status_code == 404
    assert c.post("/api/proyectos/no-existe/visor/hojas/1/zona-planta/propuesta").status_code == 404


def test_get_sin_propuesta_es_vacia_pero_trae_ejes_rect(entorno):
    c, _ = entorno
    pid = _obra(c, _pdf())
    g = c.get(f"/api/proyectos/{pid}/visor/hojas/1/zona-planta").json()
    assert g["estado"] == "vacia" and g["rect"] is None and g["origen"] is None and g["ejes_rect"] is not None


# ---------- Generador: recorte, caja trasladada, grosor ----------

def _plano_en_disco(tmp_path):
    ruta = tmp_path / "plano.pdf"
    ruta.write_bytes(_pdf())
    return ruta


def test_el_recorte_traslada_la_caja_y_calcula_el_grosor_sobre_la_imagen_recortada(tmp_path):
    ruta = _plano_en_disco(tmp_path)
    dpi = 200
    k = dpi / 72
    zona_pt = [70, 110, 740, 740]
    caja_pt = [300, 300, 360, 360]
    celda = (750, 520)
    img = localizacion.generar_localizacion(ruta, 0, tuple(v * k for v in caja_pt), *celda, dpi=dpi,
                                            zona=tuple(v * k for v in zona_pt))
    zx0, zy0 = int(zona_pt[0] * k), int(zona_pt[1] * k)
    assert abs(img.width - (zona_pt[2] - zona_pt[0]) * k) <= 2 and abs(img.height - (zona_pt[3] - zona_pt[1]) * k) <= 2
    # el recuadro está en la posición trasladada, con el grosor calculado sobre el tamaño ya recortado
    grosor = calcular_grosor_recuadro_rojo(img.width, img.height, *celda)
    ancho_hoja_completa = calcular_grosor_recuadro_rojo(round(1000 * k), round(800 * k), *celda)
    assert grosor != ancho_hoja_completa
    y_medio = int((caja_pt[1] + caja_pt[3]) / 2 * k) - zy0
    x_borde = int(caja_pt[0] * k) - zx0
    fila = [img.getpixel((x, y_medio)) for x in range(x_borde - 2, x_borde + grosor + 2)]
    rojos = [p for p in fila if p == (220, 0, 0)]
    assert len(rojos) == grosor
    assert img.getpixel((x_borde - 3, y_medio)) != (220, 0, 0)


def test_la_imagen_final_no_contiene_el_cajetin(tmp_path):
    ruta = _plano_en_disco(tmp_path)
    k = 200 / 72
    img = localizacion.generar_localizacion(ruta, 0, (300 * k, 300 * k, 360 * k, 360 * k), 750, 520, dpi=200,
                                            zona=tuple(v * k for v in (70, 110, 740, 740)))
    azules = sum(1 for p in img.getdata() if p[2] > 200 and p[0] < 60 and p[1] < 60)
    assert azules == 0
    assert img.width < (CAJETIN.x0 - 70 + 30) * k and img.width < 1000 * k * 0.7     # mide el tamaño: sin la franja derecha
    # con la hoja entera sí aparecería el cajetín (la prueba mide algo)
    entera = localizacion.rasterizar_pagina_completa(ruta, 0)
    assert any(p == (204, 204, 255) for p in entera.getdata())


def test_caja_fuera_de_la_zona_o_sin_zona_es_error_pendiente_de_verificar(tmp_path):
    ruta = _plano_en_disco(tmp_path)
    k = 200 / 72
    zona = tuple(v * k for v in (70, 110, 740, 740))
    with pytest.raises(ValueError, match="pendiente de verificar"):
        localizacion.generar_localizacion(ruta, 0, (60 * k, 300 * k, 360 * k, 360 * k), 750, 520, dpi=200, zona=zona)   # sale por la izquierda
    with pytest.raises(ValueError, match="pendiente de verificar"):
        localizacion.generar_localizacion(ruta, 0, (300 * k, 300 * k, 360 * k, 360 * k), 750, 520, dpi=200, zona=None)  # sin vuelta a la hoja entera
    with pytest.raises(ValueError, match="pendiente de verificar"):
        localizacion.generar_localizacion(ruta, 0, (300 * k, 300 * k, 360 * k, 360 * k), 750, 520, dpi=200,
                                          zona=(0, 0, 99999, 99999))


# ---------- Vista previa ----------

def test_la_vista_previa_usa_la_zona_enviada_o_la_guardada(entorno):
    c, _ = entorno
    pid = _obra(c, _pdf())
    cuerpo = {"tipo": "localizacion", "pagina": 1, "rect": [300, 300, 360, 360]}
    con_zona = _png(c.post(f"/api/proyectos/{pid}/visor/vista-previa", json={**cuerpo, "zona": [70, 110, 740, 740]}))
    assert abs(con_zona.width / con_zona.height - (740 - 70) / (740 - 110)) < 0.02
    c.put(f"/api/proyectos/{pid}/visor/hojas/1/zona-planta", json={"rect": [70, 110, 740, 740]})
    guardada = _png(c.post(f"/api/proyectos/{pid}/visor/vista-previa", json=cuerpo))
    assert guardada.size == con_zona.size


def test_la_vista_previa_sin_zona_muestra_la_hoja_entera_con_la_franja(entorno):
    c, _ = entorno
    pid = _obra(c, _pdf())
    img = _png(c.post(f"/api/proyectos/{pid}/visor/vista-previa",
                      json={"tipo": "localizacion", "pagina": 1, "rect": [300, 300, 360, 360]}))
    assert abs(img.width / img.height - 1000 / 800) < 0.01
    naranja = sum(1 for p in img.crop((0, 0, img.width, 12)).getdata() if p[0] > 200 and 100 < p[1] < 170 and p[2] < 60)
    assert naranja > img.width // 2


def test_la_vista_previa_con_la_caja_fuera_de_la_zona_se_rechaza(entorno):
    c, _ = entorno
    pid = _obra(c, _pdf())
    r = c.post(f"/api/proyectos/{pid}/visor/vista-previa",
               json={"tipo": "localizacion", "pagina": 1, "rect": [10, 300, 360, 360], "zona": [70, 110, 740, 740]})
    assert r.status_code == 422 and "no cae entero dentro de la zona" in r.json()["detail"]
