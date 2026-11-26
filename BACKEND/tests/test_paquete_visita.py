# BACKEND/tests/test_paquete_visita.py
# Paquete de visita v1 y v2 de CATDIC Campo -> elementos_visita (PLANES/paquete-visita-v1.md y -v2.md).
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
    (lambda p: p.update(version=3), "versión 3"),
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


# ---------- Paquete v2: mediciones guiadas de OBRA ----------

def _v2(elementos, **kw):
    p = _paquete(elementos, **kw)
    p["version"] = 2
    return p


def _el2(orden, numeros, fila="col", textos=None, medidas=None, estado="Conforme", **kw):
    el = _el(orden, numeros, **kw)
    el["estado"] = estado
    el["obra"] = {"fila_stp": fila, "textos": textos or {}, "medidas_acero": medidas or {}}
    return el


def _medidas_json(i=0):
    return json.loads(_filas()[i]["medidas_acero_campo_json"])


def test_v2_completo_construye_el_json_del_contrato(entorno):
    r = _cargar(entorno, _v2([_el2(1, [1], textos={"k": "12", "h": '3/8"'}, medidas={"c": "0.32", "d": "0,42"})]))
    assert r["version"] == 2 and not _dudas()
    assert _medidas_json() == {"c": 0.32, "d": 0.42, "obra": {"k": "12", "h": '3/8"'},
                               "conforme_por_omision": list("abefgijmnoq"), "estado_campo": "Conforme",
                               "origen": "paquete_v2"}
    with _bd() as c:
        a = c.execute("SELECT detalle_json FROM auditoria WHERE accion = 'CARGAR_PAQUETE'").fetchone()
    assert json.loads(a["detalle_json"])["version"] == 2


def test_v2_con_todo_vacio_es_conforme_por_omision(entorno):
    _cargar(entorno, _v2([_el2(1, [1], fila="col")]))
    m = _medidas_json()
    assert m["conforme_por_omision"] == sorted(paquete_visita.JUEGO_V2["col"]) and m["obra"] == {}
    assert "c" in m["conforme_por_omision"] and "d" in m["conforme_por_omision"]  # dimensionales vacías = conformes
    assert not _dudas()


def test_v2_sin_clave_obra_no_se_supone_conforme(entorno):
    el = _el(1, [1])
    el["estado"] = "Conforme"
    _cargar(entorno, _v2([el]))
    # sin `obra` la fila declarada es "" y no coincide con "col": no se usa y hay duda
    assert [d["campo_afectado"] for d in _dudas()] == ["elemento_visita:p001:obra"]
    assert _medidas_json()["conforme_por_omision"] == []


def test_v2_estado_pendiente_no_entra_como_conforme_y_abre_duda(entorno):
    _cargar(entorno, _v2([_el2(1, [1], estado="Pendiente", textos={"k": "12"})]))
    m = _medidas_json()
    assert m["conforme_por_omision"] == [] and m["estado_campo"] == "Pendiente" and m["obra"] == {"k": "12"}
    assert [d["campo_afectado"] for d in _dudas()] == ["elemento_visita:p001:pendiente"]
    assert _visita()["estado"] == "Con dudas"


@pytest.mark.parametrize("valor", ["32 cm", "3/8", "abc", "-0.3", "0", "31", "1e-1", "0.3.2", "0.32 m"])
def test_v2_medida_ilegible_no_se_usa_y_va_a_duda_con_el_valor_literal(entorno, valor):
    _cargar(entorno, _v2([_el2(1, [1], medidas={"c": valor, "d": "0.42"})]))
    m = _medidas_json()
    assert "c" not in m and m["d"] == 0.42
    assert "c" not in m["conforme_por_omision"] and "d" not in m["conforme_por_omision"]
    duda = _dudas()
    assert [d["campo_afectado"] for d in duda] == ["elemento_visita:p001:obra"]
    assert f"'{valor}'" in duda[0]["descripcion_pregunta"]


@pytest.mark.parametrize("valor, esperado", [("0,32", 0.32), (".32", 0.32), ("0.32", 0.32), (" 1,5 ", 1.5), ("30", 30.0)])
def test_v2_medida_con_coma_o_punto(entorno, valor, esperado):
    _cargar(entorno, _v2([_el2(1, [1], medidas={"c": valor})]))
    assert _medidas_json()["c"] == esperado and not _dudas()


def test_v2_letra_fuera_del_juego_va_a_duda(entorno):
    # 'p' (cuantía) no se pide; 'c' (dimensional) no va como texto; 'z' no existe; 'a' no es dimensional
    _cargar(entorno, _v2([_el2(1, [1], textos={"p": "1", "c": "0.3", "z": "x", "k": "12"}, medidas={"a": "0.3"})]))
    m = _medidas_json()
    assert m["obra"] == {"k": "12"}
    assert all(l not in m["conforme_por_omision"] for l in "pcz")
    assert [d["campo_afectado"] for d in _dudas()] == ["elemento_visita:p001:obra"]


def test_v2_fila_stp_que_no_coincide_no_usa_la_obra(entorno):
    _cargar(entorno, _v2([_el2(1, [1], fila="viga", textos={"k": "12"}, medidas={"c": "0.3"})]))
    m = _medidas_json()
    assert m["obra"] == {} and m["conforme_por_omision"] == [] and "c" not in m
    assert [d["campo_afectado"] for d in _dudas()] == ["elemento_visita:p001:obra"]


def test_v2_tipo_sin_stp_lleva_fila_vacia_y_nada_conforme(entorno):
    _cargar(entorno, _v2([_el2(1, [1], fila="", tipo="ZAPATA", ident="Z1")]))
    assert _medidas_json()["conforme_por_omision"] == [] and not _dudas()


def test_v2_juegos_por_tipo_salen_de_los_rotulos_del_generador(entorno):
    from generators import stp_mived
    for fila, juego in paquete_visita.JUEGO_V2.items():
        assert juego <= {l for l, _ in stp_mived.ROTULOS[fila]}
    _cargar(entorno, _v2([_el2(1, [1], tipo="LOSA", ident="L5", caso="losa", l1="", n1="", fila="losa",
                               medidas={"b": "0.20"})]))
    assert _medidas_json()["conforme_por_omision"] == list("cdefghijkmnop") and _medidas_json()["b"] == 0.2


def test_v2_recarga_idempotente_y_actualiza_si_cambia_la_obra(entorno):
    p = _v2([_el2(1, [1], textos={"k": "12"})])
    _cargar(entorno, p)
    r2 = _cargar(entorno, p)
    assert (r2["filas_nuevas"], r2["filas_actualizadas"], r2["sin_cambios"]) == (0, 0, 1)
    p["elementos"][0]["obra"]["textos"]["k"] = "16"
    r3 = _cargar(entorno, p)
    assert r3["filas_actualizadas"] == 1 and _medidas_json()["obra"] == {"k": "16"}


def test_v1_no_toca_medidas_acero_campo_json(entorno):
    _cargar(entorno, _paquete([_el(1, [1])]))
    assert _filas()[0]["medidas_acero_campo_json"] == "{}"
    with _bd() as c:  # lo que haya en la columna (p. ej. de un v2 previo) un v1 no lo borra
        c.execute("""UPDATE elementos_visita SET medidas_acero_campo_json = '{"c": 0.3}'""")
    r = _cargar(entorno, _paquete([_el(1, [1])]))
    assert r["sin_cambios"] == 1 and _filas()[0]["medidas_acero_campo_json"] == '{"c": 0.3}'


def test_estado_desconocido_se_trata_como_pendiente(entorno):
    _cargar(entorno, _v2([_el2(1, [1], estado="Revisar")]))
    assert _medidas_json()["estado_campo"] == "Pendiente" and _medidas_json()["conforme_por_omision"] == []
    assert any("no se reconoce" in d["descripcion_pregunta"] for d in _dudas())


def test_estado_vacio_es_observacion_y_acepta_sin_acento(entorno):
    _cargar(entorno, _v2([_el2(1, [1], estado=""), _el2(2, [2], estado="observacion")]))
    assert [json.loads(f["medidas_acero_campo_json"])["estado_campo"] for f in _filas()] == ["Observación"] * 2
    assert not _dudas()
