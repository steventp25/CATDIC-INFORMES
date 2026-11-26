# BACKEND/tests/test_reglas_c14_c16.py
# Etapa 7 · T18 — C14 (cuantía de OBRA = la del plano en un elemento conforme), C16 (muro en L: c = suma de las alas),
# el mapeo confirmado, la auditoría CERRAR_DUDA con el texto de la duda. Todo SINTÉTICO. Nada escribe en Dropbox: el
# procesador usa la carpeta temporal de la fixture `entorno` (CATDIC_SALIDA_PRUEBAS) y las pruebas del generador no render.
import json

import pytest

import config
import procesador_cola as pc
from generators import stp_mived
from reglas_ingenieria import PENDIENTE
from test_procesar_cola import PID, VID, _abiertas, _bd, _capturar_fichas, _diseno, _elemento_visita, _procesar, entorno  # noqa: F401
from test_valores_proyecto import MURO


# ---------- C14: generador ----------

def _col(**cambios):
    """Ficha de columna SINTÉTICA, conforme: medidas iguales al plano y todas las filas de texto conformes por omisión."""
    ficha = {"titulo": "C1", "tipo_elemento": "COLUMNA", "ejes": "EJE D-4",
             "plano": {"b": "350", "e": "2.95", "f": 'Ø3/8"@0.10', "g": 'Ø3/8"@0.10', "h": '9 EST. Ø3/8"', "i": '6-Ø1"',
                       "j": '14-Ø1"', "k": "36", "m": 'Ø1"', "n": 'Ø1"', "o": "ZONA CENTRAL / 1.08"},
             "medidas": {"c": {"valor_plano_m": 0.60, "medida_acero_campo_m": None},
                         "d": {"valor_plano_m": 1.50, "medida_acero_campo_m": None}},
             "barras": [(36, '1"')], "obra": {},
             "conforme_por_omision": list("bcdefghijkmno")}
    ficha.update(cambios)
    return ficha


def _filas(ficha):
    return stp_mived._filas_de_ficha(ficha, "COLUMNA", "col", None)


def test_c14_elemento_conforme_la_cuantia_de_obra_es_la_del_plano():
    filas, dudas, _ = _filas(_col())
    assert filas["plano"]["p"] == "0.0203" and filas["obra"]["p"] == filas["plano"]["p"]
    assert filas["origen_obra"] == {"p": "plano (C14: elemento conforme)"}
    assert filas["discrepancias"] == []
    assert not any(d["campo_afectado"] == "obra.p" for d in dudas)


def test_c14_filas_iguales_al_plano_escritas_en_obra_tambien_son_conformes():
    ficha = _col(conforme_por_omision=list("cd"), obra={"b": "350", "e": "2.95", "f": 'Ø3/8"@0.10', "g": 'Ø3/8"@0.10',
                                                       "h": '9 EST. Ø3/8"', "i": '6-Ø1"', "j": '14-Ø1"', "k": "36",
                                                       "m": 'Ø1"', "n": 'Ø1"', "o": "ZONA CENTRAL / 1.08"})
    filas, _, _ = _filas(ficha)
    assert filas["obra"]["p"] == "0.0203"


def test_c14_una_fila_de_obra_distinta_al_plano_deja_la_cuantia_vacia():
    ficha = _col(conforme_por_omision=list("bcdefgijkmno"), obra={"h": "8 EST. Ø3/8\""})
    filas, _, _ = _filas(ficha)
    assert filas["obra"]["h"] != filas["plano"]["h"] and filas["obra"]["p"] == "" and filas["origen_obra"] == {}


def test_c14_una_fila_sin_dato_de_obra_ni_omision_deja_la_cuantia_vacia():
    filas, _, _ = _filas(_col(conforme_por_omision=list("bcdefgijkmno")))  # falta la h
    assert filas["obra"]["h"] == "" and filas["obra"]["p"] == ""


def test_c14_una_discrepancia_abierta_deja_la_cuantia_vacia():
    ficha = _col(conforme_por_omision=list("befghijkmno"),
                 medidas={"c": {"valor_plano_m": 0.60, "medida_acero_campo_m": 0.20},  # 0.20 + 0.08 != 0.60
                          "d": {"valor_plano_m": 1.50, "medida_acero_campo_m": None}})
    filas, _, _ = _filas(ficha)
    assert filas["discrepancias"] and filas["obra"]["p"] == ""


def test_c14_con_barras_medidas_en_obra_se_calcula_con_ellas():
    filas, _, _ = _filas(_col(barras_obra=[(32, '1"')]))
    assert filas["obra"]["p"] == "0.0180" and filas["obra"]["p"] != filas["plano"]["p"]  # 32 × 5.07 / 9000


def test_c14_no_toca_el_muro_que_no_lleva_cuantia():
    ficha = {"titulo": "MH3", "tipo_elemento": "MURO H.A.", "ejes": "EJE C ENTRE 2-3",
             "plano": {"a": "350", "c": "1.80", "d": "2.95", "e": "SI", "h": 'Ø1/2"@0.10', "i": 'Ø1/2"@0.10',
                       "j": 'Ø3/8"@0.10', "k": 'Ø3/8"@0.10'},
             "medidas": {"b": {"valor_plano_m": 0.40, "medida_acero_campo_m": None}}, "obra": {},
             "conforme_por_omision": list("abcdefghijk")}
    filas, _, _ = stp_mived._filas_de_ficha(ficha, "MURO H.A.", "muro", None)
    assert "p" not in filas["obra"] and filas["origen_obra"] == {}


# ---------- C16: regla pura ----------

@pytest.mark.parametrize("texto,esperado", [("3.80 + 3.85", "7.65"), ("3.80+3.85", "7.65"), ("3,80 + 3,85", "7.65"),
                                            ("3.8 + 3.85", "7.65"), ("1.50 + 2 + 0.25", "3.75"), ("2 + 3", "5"),
                                            ("1.80", "1.80"), ("18.45", "18.45"), ("1,80", "1,80")])
def test_c16_suma_de_alas_y_numero_solo(texto, esperado):
    assert pc._longitud_muro_suma_alas(texto) == esperado


@pytest.mark.parametrize("texto", ["3.80 m + 3.85 m", "3.80 + 3.85 m", "3.80 y 3.85", "3.80 - 3.85", "3.80 + ", "+ 3.85",
                                   "3.80 + 3.85 + GAN.", "0 + 3.85", "3.80 + 0.00", "3.80 + x", "1.80 m", "180 cm", "dos alas",
                                   PENDIENTE, "", None, 3.8, "3.80 ++ 3.85", "3.80 + (3.85)", "3.80 × 2"])
def test_c16_cualquier_otra_forma_da_none(texto):
    assert pc._longitud_muro_suma_alas(texto) is None


# ---------- C16 en el procesador, con el mapeo REAL ----------

def _mapeo_confirmado(monkeypatch):
    mapeo, confirmado = pc.cargar_mapeo_stp()
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", mapeo)
    monkeypatch.setattr(pc, "MAPEO_CONFIRMADO", confirmado)
    return _capturar_fichas(monkeypatch)


def _muro(entorno, monkeypatch, longitud, **extra):
    capturado = _mapeo_confirmado(monkeypatch)
    _elemento_visita(entorno, 1, "MH2 C2", "MH2", "EJE C ENTRE 2-3")
    campos = {**MURO, "longitud": longitud, **extra}
    _diseno(id_elemento="MH2", ejes="EJE C ENTRE 2-3", tipo="MURO H.A.", campos=campos)  # SINTÉTICO
    _procesar()
    return capturado


def test_c16_muro_en_l_suma_las_alas_en_la_fila_c(entorno, monkeypatch):
    capturado = _muro(entorno, monkeypatch, "3.80 + 3.85")
    assert capturado["fichas"][0]["plano"]["c"] == "7.65"
    assert not [d for d in _abiertas() if "derivacion.c" in d["campo_afectado"]]


def test_c16_un_numero_solo_se_copia_como_hoy(entorno, monkeypatch):
    capturado = _muro(entorno, monkeypatch, "1.80")
    assert capturado["fichas"][0]["plano"]["c"] == "1.80"


@pytest.mark.parametrize("texto", ["3.80 m + 3.85 m", "3.80 y 3.85", "180 cm"])
def test_c16_otra_forma_abre_la_duda_con_el_texto_y_la_ficha_espera(entorno, monkeypatch, texto):
    capturado = _muro(entorno, monkeypatch, texto)
    assert "fichas" not in capturado
    d = [d for d in _abiertas() if d["campo_afectado"] == "diseno:p001:derivacion.c"]
    assert len(d) == 1 and texto in d[0]["descripcion_pregunta"]


@pytest.mark.parametrize("texto", [PENDIENTE, "", None])
def test_c16_sin_dato_legible_la_fila_c_queda_vacia_con_su_duda_que_no_bloquea(entorno, monkeypatch, texto):
    capturado = _muro(entorno, monkeypatch, texto)
    assert "c" not in capturado["fichas"][0]["plano"]  # la ficha sigue; nada inventado
    d = [d for d in _abiertas() if d["campo_afectado"] == "diseno:p001:derivacion.c"]
    assert len(d) == 1 and "queda vacía" in d[0]["descripcion_pregunta"] and "No bloquea" in d[0]["descripcion_pregunta"]


# ---------- Mapeo confirmado ----------

def test_el_mapeo_entregado_esta_confirmado_y_su_nota_lo_dice():
    ruta = pc.RUTA_MAPEO_STP
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos["confirmado"] is True and "CONFIRMADO por Steven el 26/11/2026" in datos["nota"]
    assert "PROPUESTA" not in datos["nota"]
    assert pc.MAPEO_CONFIRMADO is True


def test_con_el_mapeo_confirmado_el_stp_no_sale_como_borrador_y_escribe_solo_en_la_salida_de_pruebas(entorno, monkeypatch):
    mapeo, _ = pc.cargar_mapeo_stp()
    monkeypatch.setattr(pc, "MAPEO_DISENO_A_STP", mapeo)
    monkeypatch.setattr(pc, "MAPEO_CONFIRMADO", True)
    visto = {}

    def falso(proyecto, visita, fichas, **k):
        visto["marca"], visto["carpeta"] = k.get("marca_borrador"), k.get("carpeta_salida")
        return {"ok": False, "ruta": None, "errores": [], "dudas": [], "discrepancias": [], "excluidos": []}
    monkeypatch.setattr(pc.stp_mived, "generar_stp_mived", falso)
    _elemento_visita(entorno, 1, "MH2 C2", "MH2", "EJE C ENTRE 2-3")
    _diseno(id_elemento="MH2", ejes="EJE C ENTRE 2-3", tipo="MURO H.A.", campos=MURO)  # SINTÉTICO
    _procesar()
    assert visto["marca"] is None
    from pathlib import Path
    salida = config.obtener_salida_pruebas().resolve()
    assert salida == (entorno["tmp"] / "salida").resolve()
    assert Path(visto["carpeta"]).resolve().is_relative_to(salida)
    assert not Path(visto["carpeta"]).resolve().is_relative_to(config.obtener_dropbox_raiz().resolve())


# ---------- Observación 1 de la Evaluación 10: CERRAR_DUDA guarda el texto de la duda cerrada ----------

def test_cerrar_duda_de_ejes_del_plano_guarda_el_texto_de_la_duda_cerrada(entorno, monkeypatch):
    _mapeo_confirmado(monkeypatch)
    _diseno(id_elemento="MH2", ejes="EJE C ENTRE 2-3", tipo="MURO H.A.", nivel="SOTANO S-2", campos=MURO)
    _elemento_visita(entorno, 1, "MH2 X", "MH2", PENDIENTE, "S-2")
    with _bd() as conn:
        conn.execute("UPDATE elementos_visita SET tipo_elemento = 'MURO H.A.' WHERE orden_en_log = 1")
        conn.execute("""INSERT INTO dudas_y_hallazgos (proyecto_id, visita_id, id_elemento, categoria, campo_afectado,
                        descripcion_pregunta, resuelta, creado)
                        VALUES (?, ?, 'MH2 X', 'DUDA_BLOQUEANTE', 'elemento_visita:p001', 'SINT: faltan los ejes de MH2', 0, 'x')""",
                     (PID, VID))
    _procesar()
    with _bd() as conn:
        filas = conn.execute("SELECT detalle_json FROM auditoria WHERE accion = 'CERRAR_DUDA'").fetchall()
    cierres = [json.loads(f["detalle_json"]) for f in filas if json.loads(f["detalle_json"]).get("motivo") == pc.NOTA_EJES_DEL_PLANO]
    assert len(cierres) == 1 and cierres[0]["texto_duda"] == "SINT: faltan los ejes de MH2"

