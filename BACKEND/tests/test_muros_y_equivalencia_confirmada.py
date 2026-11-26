# BACKEND/tests/test_muros_y_equivalencia_confirmada.py
# Etapa 7 · T13 (ejes de muros desde el plano y «MC») y T14 (equivalencia S-2 confirmada por Steven, 26/11/2026).
# Todo SINTÉTICO: obra, plano, elementos y visita inventados solo para probar las reglas; imitan la FORMA de la visita 24
# de Terra Living (MH2, MH3 y el muro de contención del eje 4') pero no son sus datos ni sus ejes.
import json

import pytest
from fastapi.testclient import TestClient

import equivalencias_nivel as eq
import main
import procesador_cola as pc
from reglas_ingenieria import PENDIENTE
from test_procesar_cola import PID, VID, _abiertas, _bd, _diseno, _elemento_visita, _procesar, entorno  # noqa: F401

MAPEO = {"muro": {"filas": {"a": "fc_kgcm2"}, "medidas": {}},
         "col": {"filas": {"a": "fc_kgcm2"}, "medidas": {}}}  # SINTÉTICO: el mapeo real lo decide Steven
EJES_SINT = "EJE D-E,4"  # SINTÉTICO


@pytest.fixture
def mapeo(monkeypatch):
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO)


def _muro(uid, id_elemento, nivel, ejes=EJES_SINT, tipo="MURO H.A."):
    _diseno(uid, id_elemento, nivel, ejes, tipo=tipo)


def _visita(entorno, orden, etiqueta, id_elemento, ejes=PENDIENTE, nivel="S-2", tipo="MURO H.A."):
    """Elemento de la visita como lo deja el paquete de Campo: ID dado, ejes sin llenar."""
    _elemento_visita(entorno, orden, etiqueta, id_elemento, ejes, nivel)
    with _bd() as conn:
        conn.execute("UPDATE elementos_visita SET tipo_elemento = ? WHERE visita_id = ? AND orden_en_log = ?",
                     (tipo, VID, orden))


def _duda_importador(orden, etiqueta, resuelta=False):
    """La duda `elemento_visita:pNNN` que abre el importador cuando la visita no trae los ejes."""
    with _bd() as conn:
        conn.execute("""INSERT INTO dudas_y_hallazgos (proyecto_id, visita_id, id_elemento, categoria, campo_afectado,
                        descripcion_pregunta, resuelta, creado)
                        VALUES (?, ?, ?, 'DUDA_BLOQUEANTE', ?, 'SINT: faltan los ejes', ?, 'x')""",
                     (PID, VID, etiqueta, f"elemento_visita:p{orden:03d}", int(resuelta)))


def _dudas_de_identificacion():
    """Dudas abiertas que son de obra (importador), de cruce o de ejes del diseño; las de generación del STP no cuentan."""
    return [d["campo_afectado"] for d in _abiertas()
            if d["campo_afectado"].split(":")[0] in ("elemento_visita", "cruce") or d["campo_afectado"].endswith(":ejes")]


def _listos(eventos):
    return [e for e in eventos if e["tipo"] == "elemento_listo"]


def _dudas(eventos, campo):
    return [e for e in eventos if e["tipo"] == "duda" and e["campo"] == campo]


def _equivalencia(nivel="S-2", rango="FUNDACIONES @ E-1"):
    with _bd() as conn:
        conn.execute("INSERT INTO equivalencias_nivel (proyecto_id, nivel_visita, rango_impreso, actualizado_por, "
                     "actualizado) VALUES (?, ?, ?, 'prueba', 'x')", (PID, nivel, rango))


def _auditoria(accion):
    with _bd() as conn:
        return [json.loads(r["detalle_json"]) for r in conn.execute(
            "SELECT detalle_json FROM auditoria WHERE accion = ? ORDER BY id", (accion,))]


# ---------- T13: muro con ID único en el nivel, visita sin ejes ----------

def test_t13_muros_sin_ejes_en_la_visita_toman_los_ejes_del_plano_sin_duda_de_obra(entorno, mapeo):
    _muro("ed-0002", "MH2", "SOTANO S-2", "EJE D-E,4")
    _muro("ed-0003", "MH3", "SOTANO S2", "EJE A-B,7")
    for orden, id_el in ((1, "MH2"), (2, "MH3")):
        _visita(entorno, orden, id_el, id_el)
        _duda_importador(orden, id_el)  # la del importador por ejes que faltan
    _, eventos = _procesar()
    assert sorted(e["titulo"] for e in _listos(eventos)) == ["MURO H.A.-MH2-EJE D-E,4", "MURO H.A.-MH3-EJE A-B,7"]
    assert _dudas_de_identificacion() == []  # sin duda de obra ni de cruce
    notas = _auditoria("EJES_DEL_PLANO")
    assert len(notas) == 2 and all(n["motivo"] == "ejes tomados del plano (ID único en el nivel)" for n in notas)
    assert {n["id_elemento"] for n in notas} == {"MH2", "MH3"}
    cierres = [n for n in _auditoria("CERRAR_DUDA") if n["motivo"] == pc.NOTA_EJES_DEL_PLANO]
    assert len(cierres) == 2


def test_t13_el_muro_unico_sin_la_duda_del_importador_tambien_cruza(entorno, mapeo):
    _muro("ed-0002", "MH2", "SOTANO S-2")
    _visita(entorno, 1, "MH2", "MH2")
    _, eventos = _procesar()
    assert [e["titulo"] for e in _listos(eventos)] == ["MURO H.A.-MH2-EJE D-E,4"]


def test_t13_la_ficha_anota_que_los_ejes_vienen_del_plano(entorno, mapeo, monkeypatch):
    _muro("ed-0002", "MH2", "SOTANO S-2")
    _visita(entorno, 1, "MH2", "MH2")
    proceso = pc.ProcesoVisita("trab-prueba", VID, "prueba")
    monkeypatch.setattr(pc, "_evento", lambda *a, **k: 0)
    proceso.pdf_visita = None
    proceso.contexto = proceso._contexto(proceso._visita())
    with _bd() as conn:
        ev = conn.execute("SELECT * FROM elementos_visita WHERE visita_id = ?", (VID,)).fetchone()
    r = proceso._elemento(ev)
    assert r["estado"] == "listo" and r["ficha"]["ejes_origen"] == pc.EJES_DEL_PLANO
    assert r["ficha"]["ejes"] == EJES_SINT


def test_t13_dos_muros_con_el_mismo_id_en_el_nivel_es_duda_y_no_se_elige(entorno, mapeo):
    _muro("ed-0001", "MH1", "FUNDACIONES @ E-1", "EJE A-B,1")
    _muro("ed-0002", "MH1", "E-1 @ E-2", "EJE C-D,2")
    _equivalencia("S-2", "FUNDACIONES @ E-1")
    _equivalencia("S-2", "E-1 @ E-2")
    _visita(entorno, 1, "MH1", "MH1")
    _, eventos = _procesar()
    assert not _listos(eventos) and _abiertas()
    assert not _auditoria("EJES_DEL_PLANO")


def test_t13_muro_unico_sin_ejes_en_el_plano_es_duda_de_diseno_pendiente_de_verificar(entorno, mapeo):
    _muro("ed-0002", "MH2", "FUNDACIONES @ E-1", ejes=PENDIENTE)
    _equivalencia()
    _visita(entorno, 1, "MH2", "MH2")
    _duda_importador(1, "MH2")
    _, eventos = _procesar()
    assert not _listos(eventos)
    d = _dudas(eventos, "diseno:p001:ejes")
    assert len(d) == 1 and PENDIENTE in d[0]["pregunta"] and "ed-0002" in d[0]["pregunta"]
    assert not _dudas(eventos, "cruce:p001:ejes") and not _dudas(eventos, "cruce:p001")
    assert [x["campo_afectado"] for x in _abiertas()] == ["diseno:p001:ejes"]  # la de obra (importador) ya no está


def test_t13_columna_sin_ejes_en_la_visita_sigue_como_antes(entorno, mapeo):
    _diseno("ed-0001", "C1", "FUNDACIONES @ E-1", EJES_SINT, tipo="COLUMNA RECTANGULAR")
    _equivalencia()
    _visita(entorno, 1, "C1", "C1", tipo="COLUMNA RECTANGULAR")
    _, eventos = _procesar()
    assert not _listos(eventos) and _dudas(eventos, "cruce:p001")
    assert not _auditoria("EJES_DEL_PLANO")


def test_t13_si_el_tipo_de_la_visita_no_es_el_del_plano_no_se_da_por_el_mismo(entorno, mapeo):
    _muro("ed-0002", "MH2", "FUNDACIONES @ E-1")
    _equivalencia()
    _visita(entorno, 1, "MH2", "MH2", tipo="COLUMNA")
    _, eventos = _procesar()
    assert not _listos(eventos) and _dudas(eventos, "cruce:p001")


def test_t13_una_respuesta_de_steven_manda_sobre_la_regla(entorno, mapeo):
    _muro("ed-0002", "MH2", "FUNDACIONES @ E-1", ejes="—")
    _equivalencia()
    _visita(entorno, 1, "MH2", "MH2")
    with _bd() as conn:
        conn.execute("""INSERT INTO dudas_y_hallazgos (proyecto_id, visita_id, id_elemento, categoria, campo_afectado,
                        descripcion_pregunta, respuesta_usuario, resuelta, creado)
                        VALUES (?, ?, 'MH2', 'DUDA_BLOQUEANTE', 'elemento_visita:p001', 'SINT', 'ed-0002', 1, 'x')""",
                     (PID, VID))
    _procesar()
    assert not _auditoria("EJES_DEL_PLANO")  # se usó la respuesta (uid), no la regla


# ---------- T13: «MC» ----------

def test_t13_mc_toma_el_unico_muro_de_contencion_del_nivel(entorno, mapeo):
    _muro("ed-0005", "MURO DE CONTENCION PERIMETRAL", "SOTANO S - 2", "EJE A-D,4'", tipo="MURO DE CONTENCION")
    _visita(entorno, 1, "MC", "MC", tipo="MURO DE CONTENCION")
    _, eventos = _procesar()
    assert [e["titulo"] for e in _listos(eventos)] == ["MURO DE CONTENCION-MURO DE CONTENCION PERIMETRAL-EJE A-D,4'"]
    assert len(_auditoria("EJES_DEL_PLANO")) == 1


def test_t13_mc_en_minuscula_como_etiqueta_del_lector_con_su_duda_abierta(entorno, mapeo):
    _muro("ed-0005", "MURO DE CONTENCION PERIMETRAL", "SOTANO S - 2", "EJE A-D,4'", tipo="MURO DE CONTENCION")
    _visita(entorno, 1, "mc", PENDIENTE, tipo=PENDIENTE)  # el lector no interpreta la etiqueta: ID y tipo pendientes
    _duda_importador(1, "mc")
    _, eventos = _procesar()
    assert len(_listos(eventos)) == 1 and _dudas_de_identificacion() == []


def test_t13_mc_con_ejes_en_la_visita_cruza_aunque_el_plano_no_traiga_ejes(entorno, mapeo):
    _muro("ed-0005", "MURO DE CONTENCION PERIMETRAL", "SOTANO S - 2", PENDIENTE, tipo="MURO DE CONTENCION")
    _visita(entorno, 1, "MC", "MC", ejes="EJE A-D,4'", tipo="MURO DE CONTENCION")
    _, eventos = _procesar()
    assert [e["titulo"] for e in _listos(eventos)] == ["MURO DE CONTENCION-MURO DE CONTENCION PERIMETRAL-EJE A-D,4'"]
    assert not _auditoria("EJES_DEL_PLANO")  # los ejes eran de la visita


def test_t13_varios_mc_sin_ejes_en_la_visita_es_duda_nunca_por_cercania(entorno, mapeo):
    _muro("ed-0005", "MC-NORTE", "SOTANO S - 2", "EJE A-D,4'", tipo="MURO DE CONTENCION")
    _muro("ed-0006", "MC-SUR", "SOTANO S - 2", "EJE A-D,1", tipo="MURO DE CONTENCION")
    _visita(entorno, 1, "MC", "MC", tipo="MURO DE CONTENCION")
    _, eventos = _procesar()
    assert not _listos(eventos) and _abiertas()


def test_t13_varios_mc_y_la_visita_con_ejes_elige_el_exacto(entorno, mapeo):
    _muro("ed-0005", "MC-NORTE", "SOTANO S - 2", "EJE A-D,4'", tipo="MURO DE CONTENCION")
    _muro("ed-0006", "MC-SUR", "SOTANO S - 2", "EJE A-D,1", tipo="MURO DE CONTENCION")
    _visita(entorno, 1, "MC", "MC", ejes="EJE A-D,1", tipo="MURO DE CONTENCION")
    _, eventos = _procesar()
    assert [e["titulo"] for e in _listos(eventos)] == ["MURO DE CONTENCION-MC-SUR-EJE A-D,1"]


@pytest.mark.parametrize("texto, esperado", [("MC", {"id": "MC", "ejes": None}), ("mc", {"id": "MC", "ejes": None}),
                                             ("MCX", None)])
def test_t13_la_respuesta_mc_es_un_id_valido(texto, esperado):
    assert pc.interpretar_respuesta(texto) == esperado


# ---------- T14: equivalencia confirmada ----------

def _config(tmp_path, monkeypatch, reglas):
    ruta = tmp_path / "equivalencias_confirmadas.json"
    ruta.write_text(json.dumps({"reglas": reglas}), encoding="utf-8")
    monkeypatch.setattr(eq, "RUTA_CONFIGURACION", ruta)
    return ruta


def _regla(**extra):
    return {"proyecto_id": PID, "nivel_visita": "S-2", "rango_empieza_con": "FUNDACIONES @", "confirmado_por": "Steven",
            "fecha": "2026-11-26", "cita": "CITA SINT", "nota": "NOTA SINT", **extra}


def _rangos_diseno():
    _muro("ed-0001", "C1", "FUNDACIONES @ E-3", PENDIENTE, tipo="COLUMNA RECTANGULAR")
    _muro("ed-0002", "MH2", "FUNDACIONES @ E-1", PENDIENTE)
    _muro("ed-0003", "MH3", "fundaciones  @ E-2", PENDIENTE)  # misma regla con otra escritura: se normaliza al comparar
    _muro("ed-0004", "C1", "E-3 @ E-8", PENDIENTE, tipo="COLUMNA RECTANGULAR")


def test_t14_la_regla_se_expande_contra_los_rangos_del_diseno_del_proyecto(entorno, tmp_path, monkeypatch):
    _config(tmp_path, monkeypatch, [_regla()])
    _rangos_diseno()
    with _bd() as conn:
        r = eq.equivalencias_de(conn, PID, "S-2")
        assert sorted(r) == ["FUNDACIONES @ E-1", "FUNDACIONES @ E-3", "fundaciones  @ E-2"]
        assert eq.equivalencias_de(conn, PID, "s2") == r  # el nivel se normaliza
        assert eq.equivalencias_de(conn, PID, "S-3") == []
        assert eq.equivalencias_de(conn, "otra-obra", "S-2") == []


def test_t14_sin_duplicados_con_las_filas_de_la_bd(entorno, tmp_path, monkeypatch):
    _config(tmp_path, monkeypatch, [_regla()])
    _rangos_diseno()
    _equivalencia("S-2", "FUNDACIONES@E-1")
    _equivalencia("S-2", "E-3 @ E-8")
    with _bd() as conn:
        r = eq.equivalencias_de(conn, PID, "S-2")
        assert r[:2] == ["FUNDACIONES@E-1", "E-3 @ E-8"]  # primero la BD, tal como la escribió el usuario
        assert len(r) == 4 and len({eq.normalizar_nivel(x) for x in r}) == 4


def test_t14_el_listado_marca_el_origen_y_lleva_la_cita(entorno, tmp_path, monkeypatch):
    _config(tmp_path, monkeypatch, [_regla()])
    _rangos_diseno()
    _equivalencia("S-2", "E-3 @ E-8")
    cuerpo = TestClient(main.app).get(f"/api/proyectos/{PID}/equivalencias-nivel").json()
    assert [f["origen"] for f in cuerpo["equivalencias"]] == ["bd"]
    (c,) = cuerpo["equivalencias_confirmadas"]
    assert c["origen"] == "configuracion_confirmada" and c["cita"] == "CITA SINT" and c["confirmado_por"] == "Steven"
    assert c["fecha"] == "2026-11-26" and c["nivel_visita"] == "S-2"
    assert sorted(c["rangos_impresos"]) == ["FUNDACIONES @ E-1", "FUNDACIONES @ E-3", "fundaciones  @ E-2"]
    assert cuerpo["avisos"] == []


def test_t14_la_configuracion_no_escribe_en_la_bd(entorno, tmp_path, monkeypatch):
    _config(tmp_path, monkeypatch, [_regla()])
    _rangos_diseno()
    with _bd() as conn:
        antes = conn.execute("SELECT COUNT(*) FROM equivalencias_nivel").fetchone()[0]
    TestClient(main.app).get(f"/api/proyectos/{PID}/equivalencias-nivel")
    with _bd() as conn:
        eq.equivalencias_de(conn, PID, "S-2")
        assert conn.execute("SELECT COUNT(*) FROM equivalencias_nivel").fetchone()[0] == antes == 0


@pytest.mark.parametrize("contenido", [None, "{ esto no es json", '{"reglas": "no es lista"}', '[]'])
def test_t14_json_roto_o_ausente_se_ignora_con_aviso_y_no_rompe_el_cruce(entorno, tmp_path, monkeypatch, mapeo, contenido):
    ruta = tmp_path / "equivalencias_confirmadas.json"
    if contenido is not None:
        ruta.write_text(contenido, encoding="utf-8")
    monkeypatch.setattr(eq, "RUTA_CONFIGURACION", ruta)
    _rangos_diseno()
    reglas, avisos = eq.cargar_configuracion()
    assert reglas == [] and len(avisos) == 1 and "ignoradas" in avisos[0]
    with _bd() as conn:
        assert eq.equivalencias_de(conn, PID, "S-2") == []
    cuerpo = TestClient(main.app).get(f"/api/proyectos/{PID}/equivalencias-nivel").json()
    assert cuerpo["equivalencias_confirmadas"] == [] and cuerpo["avisos"] == avisos
    _visita(entorno, 1, "C1", "C1", ejes="EJE D-4", tipo="COLUMNA RECTANGULAR")
    _, eventos = _procesar()  # sin equivalencia: la duda de siempre, no un error
    assert not _listos(eventos) and _dudas(eventos, "cruce:p001:equivalencia")


def test_t14_una_regla_incompleta_se_ignora_y_las_demas_siguen(entorno, tmp_path, monkeypatch):
    _config(tmp_path, monkeypatch, [{"proyecto_id": PID}, _regla()])
    reglas, avisos = eq.cargar_configuracion()
    assert len(reglas) == 1 and len(avisos) == 1 and "Regla 1" in avisos[0]


def test_t14_con_la_configuracion_el_cruce_de_columna_y_muros_funciona_sin_filas_en_la_bd(entorno, tmp_path, monkeypatch, mapeo):
    _config(tmp_path, monkeypatch, [_regla()])
    _diseno("ed-0001", "C1", "FUNDACIONES @ E-3", PENDIENTE, tipo="COLUMNA RECTANGULAR")
    _muro("ed-0002", "MH2", "FUNDACIONES @ E-1", PENDIENTE)  # el plano no trae sus ejes (como el cuadro de Terra Living)
    _visita(entorno, 1, "C1", "C1", ejes="EJE D-4", tipo="COLUMNA RECTANGULAR")
    _visita(entorno, 2, "MH2", "MH2")
    _, eventos = _procesar()
    assert [e["titulo"] for e in _listos(eventos)] == ["COLUMNA RECTANGULAR-C1-EJE D-4"]
    # el muro SÍ cruzó (único en el nivel por la equivalencia): lo que falta son sus ejes en el DISEÑO, no la equivalencia
    assert _dudas(eventos, "diseno:p002:ejes") and not _dudas(eventos, "cruce:p002:equivalencia")


def test_t14_el_archivo_de_configuracion_del_repositorio_trae_la_respuesta_de_steven():
    reglas, avisos = eq.cargar_configuracion()
    assert avisos == []
    (r,) = [x for x in reglas if x["proyecto_id"] == "terra-living" and x["nivel_visita"] == "S-2"]
    assert r["rango_empieza_con"] == "FUNDACIONES @" and r["confirmado_por"] == "Steven" and r["fecha"] == "2026-11-26"
    assert r["cita"] == "S-2 SIGNIFICA SOTANO -2. PERTENECE A FUNDACIONES A @ E-1"
    assert "FUNDACIONES" in r["nota"] and "E-1" in r["nota"]
