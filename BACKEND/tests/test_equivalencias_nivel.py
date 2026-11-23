# BACKEND/tests/test_equivalencias_nivel.py
# Etapa 7 · T6 — Cruce por ID + nivel cuando el diseño no trae EJES, con la equivalencia de niveles que da el usuario.
# Todo SINTÉTICO (obra, plano, elementos y visita inventados solo para probar las reglas; no son datos de un proyecto).
import json

import pytest
from fastapi.testclient import TestClient

import config
import database
import equivalencias_nivel as eq
import main
import procesador_cola as pc
from reglas_ingenieria import PENDIENTE
from test_procesar_cola import (CAMPOS_DISENO, PID, _abiertas, _bd, _diseno, _elemento_visita,  # noqa: F401 (fixture)
                                _procesar, entorno)

MAPEO_COL = {"col": {"filas": {"a": "fc_kgcm2"}, "medidas": {}}}  # SINTÉTICO: el mapeo real lo decide Steven
RANGO = "E-3 @ E-8"  # SINTÉTICO


def _equivalencia(nivel="S-2", rango=RANGO):
    with _bd() as conn:
        conn.execute("INSERT INTO equivalencias_nivel (proyecto_id, nivel_visita, rango_impreso, actualizado_por, "
                     "actualizado) VALUES (?, ?, ?, 'prueba', 'x')", (PID, nivel, rango))


def _columna(uid="ed-0001", nivel=RANGO, ejes=PENDIENTE, id_elemento="C1"):
    _diseno(uid, id_elemento, nivel, ejes, tipo="COLUMNA RECTANGULAR")


def _visita_columna(entorno, etiqueta="C1 D4", id_elemento="C1", ejes="EJE D-4", nivel="S-2", orden=1):
    _elemento_visita(entorno, orden, etiqueta, id_elemento, ejes, nivel)


def _listos(eventos):
    return [e for e in eventos if e["tipo"] == "elemento_listo"]


def _dudas(eventos, campo):
    return [e for e in eventos if e["tipo"] == "duda" and e["campo"] == campo]


# ---------- Normalización exacta ----------

@pytest.mark.parametrize("texto, esperado", [
    ("SOTANO S - 2", "SOTANO S-2"),
    ("sotano  s -2", "SOTANO S-2"),
    ("E-3 @ E-8", "E-3@E-8"),
    ("E-3@E-8", "E-3@E-8"),
    ("  e-3   @e-8 ", "E-3@E-8"),
    ("FUNDACIONES @ E-3", "FUNDACIONES@E-3"),
    ("E-12 @ TECHO", "E-12@TECHO"),
    ("SOTANO -4", "SOTANO-4"),
    ("", ""),
    (None, ""),
])
def test_normalizar_nivel_es_exacta(texto, esperado):
    assert eq.normalizar_nivel(texto) == esperado


def test_normalizar_nivel_no_hace_nada_mas():
    assert eq.normalizar_nivel("SÓTANO S-2") == "SÓTANO S-2"  # no se quitan acentos
    assert eq.normalizar_nivel("S-2") != eq.normalizar_nivel("S-3")
    assert eq.normalizar_nivel("E-3 @ E-8") != eq.normalizar_nivel("E-3 @ E-9")  # un rango no se expande ni se recorta


@pytest.mark.parametrize("texto, esperado", [("S-2", "S-2"), ("s2", "S-2"), (" S - 2 ", "S-2"), ("S-02", "S-2"),
                                             ("NIVEL 4@8", "NIVEL 4@8"), ("E-3 @ E-8", "E-3@E-8")])
def test_clave_del_nivel_de_la_visita(texto, esperado):
    assert eq.clave_nivel_visita(texto) == esperado


# ---------- Cruce ----------

def test_con_equivalencia_el_diseno_sin_ejes_cruza_y_los_ejes_son_los_de_la_visita(entorno, monkeypatch):
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_COL)
    _columna()
    _equivalencia()
    _visita_columna(entorno)
    _, eventos = _procesar()
    listos = _listos(eventos)
    assert len(listos) == 1
    assert listos[0]["titulo"] == "COLUMNA RECTANGULAR-C1-EJE D-4"  # EJES de la visita, no 'pendiente de verificar'
    assert not [d for d in _abiertas() if d["campo_afectado"].startswith("cruce:")]


def test_la_equivalencia_se_normaliza_al_comparar(entorno, monkeypatch):
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_COL)
    _columna(nivel="E-3@E-8")  # impreso sin espacios
    _equivalencia(rango="e-3  @  e-8")
    _visita_columna(entorno)
    _, eventos = _procesar()
    assert len(_listos(eventos)) == 1


def test_un_rango_sirve_a_varios_niveles_de_visita(entorno, monkeypatch):
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_COL)
    _columna()
    _equivalencia("S-2")
    _equivalencia("S-3")
    _visita_columna(entorno, orden=1, nivel="S-2")
    _visita_columna(entorno, "C1 D5", "C1", "EJE D-5", "S-3", orden=2)
    _, eventos = _procesar()
    assert sorted(e["titulo"] for e in _listos(eventos)) == ["COLUMNA RECTANGULAR-C1-EJE D-4",
                                                              "COLUMNA RECTANGULAR-C1-EJE D-5"]


def test_sin_equivalencia_abre_la_duda_y_nunca_adivina(entorno):
    _columna()
    _visita_columna(entorno)
    _, eventos = _procesar()
    assert not _listos(eventos)
    d = _dudas(eventos, "cruce:p001:equivalencia")
    assert len(d) == 1
    assert "falta la equivalencia S-2" in d[0]["pregunta"] and "rango impreso" in d[0]["pregunta"]
    assert RANGO in d[0]["pregunta"] and f"/api/proyectos/{PID}/equivalencias-nivel" in d[0]["pregunta"]
    assert [x["campo_afectado"] for x in _abiertas()] == ["cruce:p001:equivalencia"]


def test_la_equivalencia_de_otro_nivel_no_sirve(entorno):
    _columna()
    _equivalencia("S-3")  # la visita es de S-2
    _visita_columna(entorno)
    _, eventos = _procesar()
    assert not _listos(eventos) and _dudas(eventos, "cruce:p001:equivalencia")


def test_equivalencia_que_no_cae_en_ningun_rango_del_id_es_duda(entorno):
    _columna()
    _equivalencia(rango="E-1 @ E-2")  # el plano no trae ese rango para C1
    _visita_columna(entorno)
    _, eventos = _procesar()
    d = _dudas(eventos, "cruce:p001:equivalencia")
    assert not _listos(eventos) and len(d) == 1
    assert "no corresponde a ningún rango de C1" in d[0]["pregunta"] and "E-1 @ E-2" in d[0]["pregunta"]


def test_dos_candidatos_es_duda_y_no_se_elige_uno(entorno):
    _columna("ed-0001", nivel=RANGO)
    _columna("ed-0002", nivel="S-2")  # el rango literal del nivel y el traducido: dos candidatos
    _equivalencia()
    _visita_columna(entorno)
    _, eventos = _procesar()
    d = _dudas(eventos, "cruce:p001")
    assert not _listos(eventos) and len(d) == 1
    assert "2 elementos de diseño" in d[0]["pregunta"] and "ed-0001" in d[0]["pregunta"] and "ed-0002" in d[0]["pregunta"]


def test_nivel_literal_del_diseno_cruza_sin_tabla_con_espacios_normalizados(entorno, monkeypatch):
    # Muro de contención: el plano imprime 'SOTANO S - 2'; la visita trae 'S-2'. Regla exacta, sin tabla.
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", {"muro": {"filas": {"a": "fc_kgcm2"}, "medidas": {}}})
    _diseno("ed-0009", "MC1", "SOTANO S - 2", PENDIENTE, tipo="MURO DE CONTENCION")
    _visita_columna(entorno, "MC1 D4", "MC1", "EJE D-4", "S-2")
    _, eventos = _procesar()
    assert [e["titulo"] for e in _listos(eventos)] == ["MURO DE CONTENCION-MC1-EJE D-4"]


def test_diseno_con_ejes_reales_sigue_exigiendo_los_mismos_ejes(entorno, monkeypatch):
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_COL)
    _columna(nivel="SOTANO S2", ejes="EJE D-4")
    _equivalencia(rango="SOTANO S2")  # aunque haya equivalencia, los ejes reales mandan
    _visita_columna(entorno, "C1 D5", "C1", "EJE D-5", "S-2")  # otros ejes
    _, eventos = _procesar()
    assert not _listos(eventos)
    d = _dudas(eventos, "cruce:p001")
    assert d and "ningún elemento de diseño" in d[0]["pregunta"] and "EJE D-5" in d[0]["pregunta"]


def test_diseno_con_ejes_reales_iguales_cruza_como_antes(entorno, monkeypatch):
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_COL)
    _columna(nivel="SOTANO S2", ejes="EJE D-4")
    _visita_columna(entorno)
    _, eventos = _procesar()
    assert [e["titulo"] for e in _listos(eventos)] == ["COLUMNA RECTANGULAR-C1-EJE D-4"]


def test_la_equivalencia_no_se_aplica_a_un_diseno_con_ejes_reales(entorno):
    _columna(nivel=RANGO, ejes="EJE D-4")  # ejes reales y nivel solo por rango
    _equivalencia()
    _visita_columna(entorno)
    _, eventos = _procesar()
    assert not _listos(eventos) and _dudas(eventos, "cruce:p001")


def test_la_duda_de_equivalencia_se_cierra_sola_al_definirla(entorno, monkeypatch):
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", MAPEO_COL)
    _columna()
    _visita_columna(entorno)
    _procesar()
    assert [d["campo_afectado"] for d in _abiertas()] == ["cruce:p001:equivalencia"]
    _equivalencia()
    _, eventos = _procesar()
    assert len(_listos(eventos)) == 1
    assert not [d for d in _abiertas() if d["campo_afectado"].startswith("cruce:")]


def test_visita_sin_ejes_y_diseno_sin_ejes_pide_el_cruce(entorno):
    _columna()
    _equivalencia()
    _elemento_visita(entorno, 1, "C1", "C1", PENDIENTE, "S-2")
    with _bd() as conn:  # la respuesta de Steven trae solo el ID
        conn.execute("""INSERT INTO dudas_y_hallazgos (proyecto_id, visita_id, id_elemento, categoria, campo_afectado,
                        descripcion_pregunta, respuesta_usuario, resuelta, creado)
                        VALUES (?, ?, 'C1', 'DUDA_BLOQUEANTE', 'elemento_visita:p001', 'SINT', 'C1', 1, 'x')""",
                     (PID, "obra-sint-18-losa-s-4-completivo-02-10-2026"))
    _, eventos = _procesar()
    assert not _listos(eventos)
    assert _dudas(eventos, "cruce:p001:ejes")


# ---------- Endpoints, respaldo y auditoría ----------

@pytest.fixture
def cliente(entorno):
    return TestClient(main.app), entorno


def _auditoria():
    with _bd() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM auditoria WHERE modulo = ? ORDER BY id",
                                              (eq.MODULO_AUDITORIA,))]


def _respaldos(entorno):
    return list((entorno["tmp"] / "bd").glob("*.backup-*.db"))


def test_get_vacio_lista_ayudas_sin_aplicar_nada(cliente):
    c, entorno = cliente
    _columna()
    _visita_columna(entorno)
    r = c.get(f"/api/proyectos/{PID}/equivalencias-nivel")
    assert r.status_code == 200
    assert r.json() == {"proyecto_id": PID, "equivalencias": [], "rangos_en_diseno": [RANGO], "niveles_en_visitas": ["S-2"]}


def test_put_guarda_respalda_y_audita(cliente):
    c, entorno = cliente
    _columna()
    antes = len(_respaldos(entorno))
    r = c.put(f"/api/proyectos/{PID}/equivalencias-nivel",
              json={"items": [{"nivel_visita": "s2", "rango_impreso": "E-3  @  E-8"}, {"nivel_visita": "S-3", "rango_impreso": RANGO}]})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["guardadas"] == 2 and cuerpo["avisos"] == []
    assert len(_respaldos(entorno)) == antes + 1
    filas = c.get(f"/api/proyectos/{PID}/equivalencias-nivel").json()["equivalencias"]
    assert [(f["nivel_visita"], f["rango_impreso"], f["actualizado_por"]) for f in filas] == [
        ("S-2", RANGO, "steven"), ("S-3", RANGO, "steven")]  # un rango sirve a varios niveles; clave normalizada
    a = _auditoria()
    assert len(a) == 1 and a[0]["accion"] == eq.ACCION_GUARDAR and a[0]["entidad_id"] == PID
    detalle = json.loads(a[0]["detalle_json"])
    assert detalle["cambios"][0] == {"nivel_visita": "S-2", "anterior": None, "nuevo": RANGO}
    assert detalle["respaldo"].endswith(".db")


def test_put_cambia_y_borra_con_valor_anterior_en_la_auditoria(cliente):
    c, _ = cliente
    url = f"/api/proyectos/{PID}/equivalencias-nivel"
    c.put(url, json={"items": [{"nivel_visita": "S-2", "rango_impreso": RANGO}]})
    c.put(url, json={"items": [{"nivel_visita": "S-2", "rango_impreso": "E-1 @ E-2"}]})
    assert [f["rango_impreso"] for f in c.get(url).json()["equivalencias"]] == ["E-1 @ E-2"]  # una sola por nivel
    c.put(url, json={"items": [{"nivel_visita": "S-2", "rango_impreso": ""}]})
    assert c.get(url).json()["equivalencias"] == []
    cambios = [json.loads(a["detalle_json"])["cambios"][0] for a in _auditoria()]
    assert cambios == [{"nivel_visita": "S-2", "anterior": None, "nuevo": RANGO},
                       {"nivel_visita": "S-2", "anterior": RANGO, "nuevo": "E-1 @ E-2"},
                       {"nivel_visita": "S-2", "anterior": "E-1 @ E-2", "nuevo": None}]


def test_put_avisa_si_el_rango_no_esta_en_el_diseno_pero_no_lo_cambia(cliente):
    c, _ = cliente
    _columna()
    r = c.put(f"/api/proyectos/{PID}/equivalencias-nivel", json={"items": [{"nivel_visita": "S-2", "rango_impreso": "E-9 @ E-10"}]})
    assert r.status_code == 200
    assert len(r.json()["avisos"]) == 1 and "E-9 @ E-10" in r.json()["avisos"][0]
    assert c.get(f"/api/proyectos/{PID}/equivalencias-nivel").json()["equivalencias"][0]["rango_impreso"] == "E-9 @ E-10"


def test_put_rechaza_nivel_repetido_vacio_y_proyecto_inexistente_sin_escribir(cliente):
    c, entorno = cliente
    url = f"/api/proyectos/{PID}/equivalencias-nivel"
    repetido = {"items": [{"nivel_visita": "S-2", "rango_impreso": RANGO}, {"nivel_visita": "s2", "rango_impreso": "E-1 @ E-2"}]}
    assert c.put(url, json=repetido).status_code == 400
    assert c.put(url, json={"items": [{"nivel_visita": "  ", "rango_impreso": RANGO}]}).status_code == 400
    assert c.put(url, json={"items": []}).status_code == 400
    assert c.put("/api/proyectos/no-existe/equivalencias-nivel",
                 json={"items": [{"nivel_visita": "S-2", "rango_impreso": RANGO}]}).status_code == 404
    assert c.get("/api/proyectos/no-existe/equivalencias-nivel").status_code == 404
    assert c.get(url).json()["equivalencias"] == [] and _auditoria() == [] and _respaldos(entorno) == []


def test_la_tabla_es_unica_por_obra_y_nivel(entorno):
    _equivalencia()
    with pytest.raises(Exception):
        _equivalencia(rango="E-1 @ E-2")
