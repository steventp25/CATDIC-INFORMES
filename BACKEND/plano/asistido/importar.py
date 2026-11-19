# BACKEND/plano/asistido/importar.py
# Etapa 5 · A3b — Paso 3 de la lectura asistida: importar la propuesta.json de una hoja.
# Cada valor debe anclarse en el texto que Claude citó (esquema.revisar_dato); lo que no, queda "pendiente de verificar"
# con una duda `IA:`. Nada nace confirmado. Toda la hoja va en UNA transacción: entra entera o no entra.
import json
from pathlib import Path
from typing import Dict, List, Optional

from database import get_connection
from importadores.validador_diseno import EJE_SIN_LETRA
from obras import ErrorObra, _ahora, _proyecto, _transaccion, _usuario
from plano import extractor as ex
from plano.asistido import esquema as es
from reglas_ingenieria import PENDIENTE, _normalizar_texto

ORIGEN_FUENTE = "IA:claude-code"  # fuente_json.extractor de lo que escribe esta lectura
ORIGEN_DUDA = "IA:"               # prefijo de campo_afectado de sus dudas
TIPOS_LOSA = {"LOSA", "LOSA ALIGERADA", "LOSA MACIZA"}


def _colapsar(s) -> str:
    return " ".join(str(s).split())


class _Hoja:
    """Acumula las dudas y las cuentas de una hoja."""

    def __init__(self, pagina: int):
        self.pagina = pagina
        self.dudas: List[Dict] = []
        self.cuenta = {"nuevo": 0, "actualizado": 0, "sin_cambios": 0, "choque": 0, "dudas_abiertas": 0,
                       "comprobaciones": 0}

    def duda(self, id_elemento: str, lugar: str, texto: str):
        self.dudas.append({"id_elemento": id_elemento or "(sin id)", "campo": f"p{self.pagina:02d}.{lugar}",
                           "texto": texto})


def _rechazar(carpeta: Path, motivo: str, ahora: str) -> Dict:
    res = {"estado": "rechazada", "motivo": motivo, "nuevo": 0, "actualizado": 0, "sin_cambios": 0, "choque": 0,
           "dudas_abiertas": 0, "comprobaciones": 0, "fecha": ahora}
    _escribir_importacion(carpeta, res)
    return res


def _escribir_importacion(carpeta: Path, res: Dict):
    (carpeta / "importacion.json").write_bytes(
        (json.dumps(res, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))


def _fuente(f: Optional[Dict], pagina: int, hoja: str, sha: str) -> Optional[Dict]:
    return None if f is None else {**f, "pagina": pagina, "hoja": hoja, "sha256": sha}


def _doble_lectura(conn, proyecto_id: str, clave, campos: Dict[str, Optional[str]], h: _Hoja, i: int, id_el: str) -> bool:
    """Si la fila ya la escribió T6n, no se escribe: se compara campo por campo. True = se atendió aquí."""
    previo = conn.execute("""SELECT fuente_json, datos_diseno_json FROM elementos_diseno WHERE proyecto_id = ?
                             AND id_elemento = ? AND nivel_rango = ? AND ejes = ?""", (proyecto_id, *clave)).fetchone()
    if previo is None or json.loads(previo["fuente_json"] or "{}").get("extractor") != ex.EXTRACTOR:
        return False
    datos = json.loads(previo["datos_diseno_json"] or "{}")
    for campo, valor in campos.items():
        if valor is None or campo not in datos:
            continue
        if _colapsar(datos[campo]) == _colapsar(valor):
            h.cuenta["comprobaciones"] += 1
        else:
            h.duda(id_el, f"elementos[{i}].doble_lectura.{campo}",
                   f"IA: la lectura asistida da '{valor}' para {campo} de {id_el}, pero T6n (tabla de aplicación) "
                   f"tiene '{datos[campo]}'. No se escribe nada ({PENDIENTE}).")
    return True


def _elemento(conn, proyecto_id: str, plano: Dict, textos: Dict, el: Dict, i: int, h: _Hoja, vistas: Dict, ahora: str):
    por_n = es.textos_por_n(textos)
    pagina, hoja, sha = textos["pagina"], textos["hoja"], textos["sha256"]
    rev = {k: es.revisar_dato(el[k], por_n) for k in es.DATOS_FIJOS}
    campos = {c: es.revisar_dato(d, por_n) for c, d in el["campos"].items()}
    id_el = rev["id_elemento"]["valor"]
    explicados = set()
    for nombre, r in list(rev.items()) + [(f"campos.{c}", r) for c, r in campos.items()]:
        if r["duda"]:
            h.duda(id_el, f"elementos[{i}].{nombre}", r["duda"])
            explicados.add(nombre.removeprefix("campos."))
    for j, d in enumerate(el["dudas"]):
        h.duda(id_el, f"elementos[{i}].dudas[{j}]", f"IA: {d['texto']}")
    for j, e in enumerate(el["enlaces"]):
        h.duda(id_el, f"elementos[{i}].enlaces[{j}]",
               f"IA: enlace sin resolver, no da ningún valor: {json.dumps({k: v for k, v in e.items() if k != 'citas'}, ensure_ascii=False)}")
    nivel = rev["nivel_rango"]["valor"]
    if id_el is None or nivel is None:
        h.duda(id_el, f"elementos[{i}].sin_clave",
               f"IA: el elemento {i} de la hoja {hoja} no se escribe: falta el ID o el nivel ({PENDIENTE}).")
        return
    tipo = el["tipo_elemento"]
    if _normalizar_texto(tipo) in TIPOS_LOSA:
        ejes = EJE_SIN_LETRA  # error #11: las losas siempre llevan '—', traiga lo que traiga
    else:
        ejes = rev["ejes"]["valor"] or PENDIENTE
    clave = (id_el, nivel, ejes)
    if clave in vistas:
        h.cuenta["choque"] += 1
        h.duda(id_el, f"elementos[{i}].clave_unica",
               f"IA: el elemento {i} repite la clave (ID {id_el}, nivel '{nivel}', ejes '{ejes}') del elemento "
               f"{vistas[clave]} de esta hoja. No se fusionan ({PENDIENTE}).")
        return
    vistas[clave] = i
    if _doble_lectura(conn, proyecto_id, clave, {c: r["valor"] for c, r in campos.items()}, h, i, id_el):
        return
    prop = {"id_elemento": id_el, "tipo_elemento": tipo, "nivel_rango": nivel, "ejes": ejes,
            "hoja_plano_origen": hoja, "archivo_plano_origen": plano["vectorial_archivo"],
            "datos": {c: {"valor": r["valor"] if r["valor"] is not None else PENDIENTE,
                          "fuente": _fuente(r["fuente"], pagina, hoja, sha)} for c, r in campos.items()},
            "tabla": f"IA:p{pagina:02d}", "explicados": explicados,
            "bbox_id": (rev["id_elemento"]["fuente"] or {}).get("bbox") or [], "confirmados": set()}
    v = ex._validar(prop)
    res, uid = ex._escribir_elemento(conn, proyecto_id, plano, prop, v, ahora, origen=ORIGEN_FUENTE)
    h.cuenta[res] += 1
    if res == "choque":
        h.duda(id_el, f"elementos[{i}].clave_unica",
               f"IA: ya existe un elemento {id_el} (nivel '{nivel}', ejes '{ejes}', uid {uid or '?'}) que no viene de "
               f"esta lectura; no se toca ({PENDIENTE}).")
        return
    for d in v["dudas"]:
        h.duda(id_el, f"elementos[{i}].{d['campo_afectado']}", d["descripcion_pregunta"])
    for d in prop["dudas_extra"]:
        h.duda(d["id_elemento"], f"elementos[{i}].{d['campo']}", d["texto"])


def importar_hoja(proyecto_id: str, carpeta_pagina: Path, usuario: Optional[str] = None) -> Dict:
    """Importa `propuesta.json` de la carpeta de una página. Devuelve (y escribe) importacion.json."""
    carpeta = Path(carpeta_pagina)
    usuario = usuario or _usuario()
    ahora = _ahora()
    try:
        propuesta = json.loads((carpeta / "propuesta.json").read_text(encoding="utf-8"))
        textos = json.loads((carpeta / "textos.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return _rechazar(carpeta, f"No se pudo leer propuesta.json o textos.json: {e}", ahora)
    conn = get_connection()
    try:
        _proyecto(conn, proyecto_id)
        plano = conn.execute("SELECT * FROM planos WHERE proyecto_id = ? AND estado = 'vigente'", (proyecto_id,)).fetchone()
        if plano is None:
            raise ErrorObra("La obra no tiene un plano vigente: sube primero el vectorial y el sellado.", 409)
        plano = dict(plano)
        try:
            propuesta = es.validar_propuesta(propuesta, textos)
        except es.PropuestaInvalida as e:
            return _rechazar(carpeta, f"Propuesta mal formada: {e}", ahora)
        if not (propuesta["sha256"] == textos["sha256"] == plano["vectorial_sha256"]):
            return _rechazar(carpeta, "El sha256 de la propuesta, el de textos.json y el del plano vigente no son "
                                      "iguales: la hoja no se carga.", ahora)
        h = _Hoja(textos["pagina"])
        _transaccion(conn)
        try:
            vistas: Dict = {}
            for i, el in enumerate(propuesta["elementos"]):
                _elemento(conn, proyecto_id, plano, textos, el, i, h, vistas, ahora)
            for j, d in enumerate(propuesta["dudas_hoja"]):
                h.duda(f"hoja {textos['hoja']}", f"dudas_hoja[{j}]", f"IA: {d['texto']}")
            for d in h.dudas:
                h.cuenta["dudas_abiertas"] += ex._abrir_duda(conn, proyecto_id, d["id_elemento"], d["campo"], d["texto"],
                                                             origen=ORIGEN_DUDA)
            res = {"estado": "importada", "motivo": "", **h.cuenta, "fecha": ahora,
                   "comprobaciones_de_claude": propuesta["comprobaciones"]}
            conn.execute("INSERT INTO auditoria (fecha_hora, usuario, modulo, accion, entidad_id, detalle_json) "
                         "VALUES (?, ?, 'ASISTIDO', 'IMPORTAR_PROPUESTA', ?, ?)",
                         (ahora, usuario, proyecto_id, json.dumps({
                             "pagina": textos["pagina"], "hoja": textos["hoja"], "sha256": textos["sha256"],
                             "archivo": textos["archivo"], "lector": propuesta["lector"], "skill": propuesta["skill"],
                             **h.cuenta}, ensure_ascii=False)))
            conn.execute("COMMIT")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()
    _escribir_importacion(carpeta, res)
    return res
