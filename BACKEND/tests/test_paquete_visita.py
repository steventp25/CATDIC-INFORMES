# BACKEND/tests/test_paquete_visita.py
# Paquete de visita v1 de CATDIC Campo -> elementos_visita (PLANES/paquete-visita-v1.md).
# Todo SINTÉTICO: paquetes, fotos y visita se generan en la prueba.
import base64
import io
import json
import sqlite3

import pytest
from PIL import Image

import config
import database
from reglas_ingenieria import PENDIENTE
from sync import lector_visita, paquete_visita

CARPETA = "7. VERTICALES S-7 PARCIAL 20-11-2026"  # SINTÉTICO
VISITA_ID = "obra-sint-7-verticales-s-7"


def _foto_b64(color=(120, 110, 100), tam=(1600, 1200), orientacion=None):
    buf = io.BytesIO()
    img = Image.new("RGB", tam, color)
    if orientacion:
        exif = Image.Exif()
        exif[0x0112] = orientacion
        img.save(buf, format="JPEG", quality=90, exif=exif.tobytes())
    else:
        img.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _el(orden, numeros, tipo="COLUMNA", ident="C2", caso="cruce_puntual", l1="F", l2="", n1="11", n2="",
        mediciones="", descripcion="", nivel="", texto_libre=""):
    return {"orden": orden, "tipo": tipo, "id": ident, "nivel": nivel,
            "ejes": {"caso": caso, "letra_1": l1, "letra_2": l2, "num_1": n1, "num_2": n2},
            "ejes_texto": "lo que diga Campo (no se usa)", "texto_libre": texto_libre,
            "mediciones": mediciones, "estado": "Pendiente", "descripcion": descripcion,
            "fotos": [{"numero": n, "archivo": f"foto_{n:03d}.jpg", "hora": f"2026-11-20T10:{n:02d}:00Z",
                       "mime": "image/jpeg", "base64": _foto_b64((30 * n % 255, 90, 120))} for n in numeros]}


def _paquete(elementos, fecha="2026-11-20", clase="Parcial", nivel="S-7"):
    return {"formato": "catdic-paquete-visita", "version": 1, "generado_por": "CATDIC Campo (prueba)",
            "generado_en": "2026-11-20T12:00:00Z", "obra": "OBRA SINT",
            "visita": {"nombre": "Verticales S-7", "fecha": fecha, "clase": clase, "nivel": nivel},
            "elementos": elementos}


def _escribir(carpeta, paquete, nombre="PAQUETE_VISITA_OBRA_SINT_2026-11-20.catdic-visita.json"):
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / nombre
    ruta.write_text(json.dumps(paquete), encoding="utf-8")
    return ruta


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    (tmp_path / "bd").mkdir()
    monkeypatch.setenv(config.ENV_DB_PATH, str(tmp_path / "bd" / "prueba.db"))
    monkeypatch.setenv(config.ENV_DROPBOX_RAIZ, str(tmp_path / "dropbox"))
    monkeypatch.setenv(lector_visita.ENV_CACHE_RAIZ, str(tmp_path / "cache"))
    database.inicializar_bd()
    carpeta = tmp_path / "dropbox" / CARPETA
    carpeta.mkdir(parents=True)
    conn = database.get_connection()
    conn.execute("INSERT INTO proyectos (id, nombre, tipo, formato_defecto, actualizado) "
                 "VALUES ('obra-sint','Obra Sint','Supervisión','STP-MIVED','x')")
    conn.execute("""INSERT INTO visitas (id, proyecto_id, numero, nombre_carpeta, ruta_carpeta, fecha_visita,
                    clase, estado, formatos_solicitados, actualizado) VALUES (?, 'obra-sint', 7, ?, ?,
                    '2026-11-20', 'Parcial', 'Sin procesar', '["STP-MIVED"]', 'x')""",
                 (VISITA_ID, CARPETA, str(carpeta)))
    conn.commit()
    conn.close()
    return {"tmp": tmp_path, "carpeta": carpeta}


def _bd():
    conn = sqlite3.connect(config.obtener_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _filas():
    with _bd() as c:
        return [dict(f) for f in c.execute("SELECT * FROM elementos_visita ORDER BY orden_en_log")]


def _dudas(abiertas=True):
    with _bd() as c:
        q = "SELECT * FROM dudas_y_hallazgos WHERE categoria = 'DUDA_BLOQUEANTE'" + (" AND resuelta = 0" if abiertas else "")
        return [dict(f) for f in c.execute(q + " ORDER BY id")]


def _visita():
    with _bd() as c:
        return dict(c.execute("SELECT * FROM visitas WHERE id = ?", (VISITA_ID,)).fetchone())


def _cargar(entorno, paquete, **kw):
    ruta = _escribir(entorno["carpeta"], paquete)
    return paquete_visita.cargar_paquete(VISITA_ID, ruta, usuario="prueba", respaldar=False, **kw)


# ---------- Identidad ----------

@pytest.mark.parametrize("el, esperado", [
    (_el(1, [1]), ("COLUMNA", "C2", "EJE F-11")),
    (_el(1, [1], tipo="MURO H.A.", ident="m1", caso="muro_entre_letras", l1="d", l2="e", n1="4"),
     ("MURO H.A.", "M1", "EJE D-E,4")),
    (_el(1, [1], tipo="VIGA", ident="V3", caso="viga_recta_sobre_letra", l1="C", n1="2", n2="3"),
     ("VIGA", "V3", "EJE C, ENTRE 2-3")),
    (_el(1, [1], tipo="VIGA", ident="V9", caso="viga_sin_eje_letra", l1="", n1=""), ("VIGA", "V9", "—")),
    (_el(1, [1], tipo="PORTICO", ident="P1", caso="tramo_portico", l1="1", n1="MC", n2="A"),
     ("PORTICO", "P1", "EJE 1 ENTRE MC-A")),
    (_el(1, [1], tipo="LOSA", ident="L5", caso="losa", l1="", n1=""), ("LOSA", "L5", "—")),
    (_el(1, [1], tipo="PLATEA", ident="PL1", caso="area", l1="A", l2="B", n1="1", n2="2"),
     ("PLATEA", "PL1", "(A-B),(1-2)")),
    (_el(1, [1], l1="A’", n1="1"), ("COLUMNA", "C2", "EJE A'-1")),  # prima tipográfica normalizada
])
def test_identidad_valida_recalcula_los_ejes(el, esperado):
    i = paquete_visita.identidad_de_elemento(el, "S-7", "S-7")
    assert (i["tipo_elemento"], i["id_elemento"], i["ejes"]) == esperado
    assert i["reconocido"] and i["nivel"] == "S-7"


@pytest.mark.parametrize("el, pendientes", [
    (_el(1, [1], tipo="OTRO"), {"tipo_elemento", "ejes"}),
    (_el(1, [1], tipo=""), {"tipo_elemento", "ejes"}),
    (_el(1, [1], tipo="ESCALERA", caso=""), {"ejes"}),           # escalera: sin formato de ejes definido
    (_el(1, [1], ident=""), {"id_elemento"}),
    (_el(1, [1], ident="C 2 ?"), {"id_elemento"}),
    (_el(1, [1], n1=""), {"ejes"}),                               # casilla vacía
    (_el(1, [1], caso="muro_entre_letras", l2="G", n1="4"), {"ejes"}),  # caso que no es el del tipo
    (_el(1, [1], tipo="PORTICO", caso="tramo_portico", l1="F", n1="A", n2="B"), {"ejes"}),  # misma familia
])
def test_lo_que_no_valida_queda_pendiente_con_su_motivo(el, pendientes):
    i = paquete_visita.identidad_de_elemento(el, "S-7", "")
    assert {k for k in ("tipo_elemento", "id_elemento", "ejes") if i[k] == PENDIENTE} == pendientes
    assert not i["reconocido"] and i["faltas"]


def test_nivel_manda_la_carpeta_y_un_nivel_distinto_queda_pendiente():
    assert paquete_visita.identidad_de_elemento(_el(1, [1]), "S-7", "s-7")["nivel"] == "S-7"
    distinto = paquete_visita.identidad_de_elemento(_el(1, [1]), "S-7", "S-6")
    assert distinto["nivel"] == PENDIENTE and "S-6" in distinto["faltas"][0]
    assert paquete_visita.identidad_de_elemento(_el(1, [1]), PENDIENTE, "e-3")["nivel"] == "E-3"
    assert paquete_visita.identidad_de_elemento(_el(1, [1]), PENDIENTE, "")["nivel"] == PENDIENTE


# ---------- Carga ----------

def test_carga_elementos_reconocidos_sin_dudas_y_con_fotos_en_cache(entorno):
    r = _cargar(entorno, _paquete([_el(1, [1, 2], mediciones="L=3.85", descripcion="Conforme"),
                                   _el(2, [3], tipo="LOSA", ident="L5", caso="losa", l1="", n1="")]))
    assert r["elementos"] == 2 and r["fotos"] == 3 and r["reconocidos"] == 2 and r["dudas_nuevas"] == 0
    filas = _filas()
    assert [(f["orden_en_log"], f["tipo_elemento"], f["id_elemento"], f["ejes"], f["nivel"]) for f in filas] == [
        (1, "COLUMNA", "C2", "EJE F-11", "S-7"), (3, "LOSA", "L5", "—", "S-7")]
    assert filas[0]["etiqueta_original"] == "COLUMNA C2 lo que diga Campo (no se usa)"
    fotos = json.loads(filas[0]["fotos_json"])
    assert [f["foto"] for f in fotos] == [1, 2] and fotos[0]["nota"] == "Medidas en obra: L=3.85 · Conforme"
    assert fotos[0]["mediciones"] == "L=3.85" and fotos[1]["nota"] == ""
    assert filas[0]["medidas_acero_campo_json"] == "{}"  # las medidas NUNCA llenan la Capa 2 numérica
    cache = entorno["tmp"] / "cache" / "obra-sint" / VISITA_ID
    for n in (1, 2, 3):
        with Image.open(cache / f"p{n:03d}.jpg") as img:
            assert max(img.size) <= 1000 and img.format == "JPEG"
    assert not _dudas() and _visita()["estado"] == "Sin procesar"


def test_un_elemento_incompleto_abre_una_sola_duda_y_la_visita_queda_con_dudas(entorno):
    _cargar(entorno, _paquete([_el(1, [1]), _el(2, [2, 3], tipo="OTRO", ident="", caso="")]))
    d = _dudas()
    assert [x["campo_afectado"] for x in d] == ["elemento_visita:p002"]
    assert "fotos 2 a 3" in d[0]["descripcion_pregunta"] and "el tipo" in d[0]["descripcion_pregunta"]
    assert _filas()[1]["id_elemento"] == PENDIENTE and _visita()["estado"] == "Con dudas"


def test_segunda_carga_no_duplica_filas_ni_dudas(entorno):
    p = _paquete([_el(1, [1]), _el(2, [2], ident="")])
    _cargar(entorno, p)
    r = _cargar(entorno, p)
    assert r["filas_nuevas"] == 0 and r["sin_cambios"] == 2 and r["dudas_nuevas"] == 0
    assert len(_filas()) == 2 and len(_dudas()) == 1


def test_foto_enderezada_por_exif(entorno):
    el = _el(1, [1])
    el["fotos"][0]["base64"] = _foto_b64(tam=(1600, 1200), orientacion=6)  # girada 90°
    _cargar(entorno, _paquete([el]))
    with Image.open(entorno["tmp"] / "cache" / "obra-sint" / VISITA_ID / "p001.jpg") as img:
        assert img.size[1] > img.size[0]


def test_no_toca_la_carpeta_de_la_visita(entorno):
    ruta = _escribir(entorno["carpeta"], _paquete([_el(1, [1])]))
    antes = sorted((p.name, p.stat().st_mtime_ns) for p in entorno["carpeta"].iterdir())
    paquete_visita.cargar_paquete(VISITA_ID, ruta, usuario="prueba", respaldar=False)
    assert sorted((p.name, p.stat().st_mtime_ns) for p in entorno["carpeta"].iterdir()) == antes


def test_auditoria_de_la_carga(entorno):
    _cargar(entorno, _paquete([_el(1, [1])]))
    with _bd() as c:
        a = c.execute("SELECT * FROM auditoria WHERE modulo = 'PAQUETE_VISITA' AND accion = 'CARGAR_PAQUETE'").fetchone()
    assert a["usuario"] == "prueba" and json.loads(a["detalle_json"])["elementos"] == 1


# ---------- Paquetes inválidos ----------

@pytest.mark.parametrize("estropear, texto", [
    (lambda p: p.update(formato="otra-cosa"), "no es un paquete"),
    (lambda p: p.update(version=2), "versión 2"),
    (lambda p: p.update(elementos=[]), "no trae elementos"),
    (lambda p: p["elementos"][0].update(fotos=[]), "no trae fotos"),
    (lambda p: p["elementos"][1]["fotos"][0].update(numero=1), "repite"),
    (lambda p: p["elementos"].reverse(), "orden"),
    (lambda p: p["elementos"][0]["fotos"][0].update(base64="no-es-imagen"), "no es una imagen"),
])
def test_paquete_invalido_no_carga_nada_y_deja_una_duda(entorno, estropear, texto):
    p = _paquete([_el(1, [1]), _el(2, [2])])
    estropear(p)
    with pytest.raises(ValueError, match=texto):
        _cargar(entorno, p)
    assert not _filas()
    d = _dudas()
    assert [x["campo_afectado"] for x in d] == ["paquete_visita"] and _visita()["estado"] == "Con dudas"


def test_json_ilegible_se_rechaza(entorno):
    ruta = entorno["carpeta"] / "x.catdic-visita.json"
    ruta.write_text("{no es json", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON"):
        paquete_visita.cargar_paquete(VISITA_ID, ruta, usuario="prueba", respaldar=False)


def test_un_paquete_bueno_cierra_la_duda_del_rechazado_y_la_del_pdf(entorno):
    malo = _paquete([_el(1, [1])])
    malo["version"] = 9
    with pytest.raises(ValueError):
        _cargar(entorno, malo)
    with _bd() as c:  # la duda que deja el lector cuando no hay un único PDF
        c.execute("""INSERT INTO dudas_y_hallazgos (proyecto_id, visita_id, id_elemento, categoria, campo_afectado,
                     descripcion_pregunta, creado) VALUES ('obra-sint', ?, '', 'DUDA_BLOQUEANTE', 'lector_visita', 'x', 'x')""",
                  (VISITA_ID,))
    _cargar(entorno, _paquete([_el(1, [1])]))
    assert not _dudas()


# ---------- Búsqueda ----------

def test_buscar_paquete(entorno):
    assert paquete_visita.buscar_paquete(entorno["carpeta"]) is None
    assert paquete_visita.buscar_paquete(entorno["tmp"] / "no-existe") is None
    ruta = _escribir(entorno["carpeta"], _paquete([_el(1, [1])]))
    (entorno["carpeta"] / "visita.pdf").write_bytes(b"%PDF")
    assert paquete_visita.buscar_paquete(entorno["carpeta"]) == ruta
    _escribir(entorno["carpeta"], _paquete([_el(1, [1])]), nombre="OTRO.catdic-visita.json")
    with pytest.raises(ValueError, match="2 paquetes"):
        paquete_visita.buscar_paquete(entorno["carpeta"])


# ---------- Fecha y clase ----------

def _poner_pendiente_con_duda(columna, campo):
    with _bd() as c:
        c.execute(f"UPDATE visitas SET {columna} = ? WHERE id = ?", (PENDIENTE, VISITA_ID))
        c.execute("""INSERT INTO dudas_y_hallazgos (proyecto_id, visita_id, id_elemento, categoria, campo_afectado,
                     descripcion_pregunta, creado) VALUES ('obra-sint', ?, '', 'DUDA_BLOQUEANTE', ?, 'x', 'x')""",
                  (VISITA_ID, campo))


def test_fecha_y_clase_pendientes_se_llenan_del_paquete_y_su_duda_se_cierra(entorno):
    _poner_pendiente_con_duda("fecha_visita", "fecha_visita")
    _poner_pendiente_con_duda("clase", "clase")
    r = _cargar(entorno, _paquete([_el(1, [1])], fecha="2026-11-19", clase="completivo"))
    v = _visita()
    assert (v["fecha_visita"], v["clase"]) == ("2026-11-19", "Completivo")
    assert r["fecha_clase"]["llenados"] == {"fecha_visita": "2026-11-19", "clase": "Completivo"}
    cerradas = [d for d in _dudas(abiertas=False) if d["campo_afectado"] in ("fecha_visita", "clase")]
    assert {d["respuesta_usuario"] for d in cerradas} == {paquete_visita.RESPUESTA_PAQUETE}
    assert all(d["resuelta"] == 1 for d in cerradas)


def test_fecha_distinta_a_la_de_la_carpeta_abre_duda_y_no_cambia(entorno):
    _cargar(entorno, _paquete([_el(1, [1])], fecha="2026-11-21"))
    assert _visita()["fecha_visita"] == "2026-11-20"
    assert [d["campo_afectado"] for d in _dudas()] == ["paquete_visita:fecha_visita"]


@pytest.mark.parametrize("fecha, clase", [("", ""), ("20/11/2026", "Mixta"), ("2026-02-30", "x")])
def test_fecha_o_clase_invalida_no_se_usa(entorno, fecha, clase):
    _poner_pendiente_con_duda("fecha_visita", "fecha_visita")
    _cargar(entorno, _paquete([_el(1, [1])], fecha=fecha, clase=clase))
    assert _visita()["fecha_visita"] == PENDIENTE
    assert [d["campo_afectado"] for d in _dudas()] == ["fecha_visita"]
