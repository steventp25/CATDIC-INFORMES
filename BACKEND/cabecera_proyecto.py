# backend/cabecera_proyecto.py
# Etapa 7 · T15 — Cabecera del proyecto editable en la app (GET y PUT /api/proyectos/{id}/cabecera).
# Los 7 campos viven en `proyectos`. Cada campo que cambia deja su fila en `auditoria` (anterior y nuevo); sin cambios
# no se escribe nada. Guardar resuelve la duda de proyecto `proyecto.cabecera_propuesta` si estaba abierta.
# Los valores los escribe Steven: este módulo no deduce ni rellena nada (Regla de Oro).
import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, Body, HTTPException

import config
from database import _respaldar_bd, get_connection, migrar_codia_residente, usuario_auditoria
from sync import cabecera_propuesta as _propuesta

MODULO_AUDITORIA = "CABECERA"
ACCION_EDITAR = "EDITAR_CABECERA"
ACCION_MIGRAR = "MIGRACION_CABECERA_CODIA"
CAMPO_DUDA = _propuesta.CAMPO_DUDA  # 'proyecto.cabecera_propuesta'

# Orden en que se muestran. `codia_residente` no existía en `proyectos`: se añade con ALTER TABLE (no destructivo).
CAMPOS = ("no_solicitud", "no_licencia", "direccion_obra", "provincia", "sector", "residente_obra", "codia_residente")
COLUMNA_NUEVA = "codia_residente"

router = APIRouter()


def _asegurar_columna(conn) -> None:
    """Si falta `codia_residente` (BD que no pasó por `inicializar_bd`), la añade con la migración de
    database.py, que respalda la BD y audita (MIGRACION_CABECERA_CODIA)."""
    columnas = {r[1] for r in conn.execute("PRAGMA table_info(proyectos)")}
    if COLUMNA_NUEVA not in columnas:
        migrar_codia_residente()


def _proyecto(conn, proyecto_id: str):
    _asegurar_columna(conn)
    p = conn.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,)).fetchone()
    if p is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
    return p


def _valores(p) -> Dict[str, str]:
    return {c: (p[c] or "") for c in CAMPOS}


def obtener_cabecera(proyecto_id: str) -> Dict:
    conn = get_connection()
    try:
        p = _proyecto(conn, proyecto_id)
        valores = _valores(p)
        nombre = p["nombre"]
    finally:
        conn.close()
    propuesta = _propuesta.obtener_propuesta(proyecto_id)
    return {"proyecto_id": proyecto_id, "nombre": nombre, "campos": list(CAMPOS), "valores": valores,
            "propuesta": {"hay_propuesta": propuesta["hay_propuesta"], "duda_abierta_id": propuesta["duda_abierta_id"],
                          "campos": {c: propuesta["campos"].get(c) for c in CAMPOS}}}


def guardar_cabecera(proyecto_id: str, cambios: Dict[str, str], usuario: str = None) -> Dict:
    usuario = usuario or usuario_auditoria()
    desconocidos = sorted(set(cambios) - set(CAMPOS))
    if desconocidos:
        raise HTTPException(status_code=422, detail=f"Campos desconocidos: {', '.join(desconocidos)}. "
                                                    f"Permitidos: {', '.join(CAMPOS)}.")
    limpios = {}
    for k, v in cambios.items():
        if not isinstance(v, str):
            raise HTTPException(status_code=422, detail=f"El campo «{k}» debe ser texto.")
        limpios[k] = v.strip()
    conn = get_connection()
    try:
        p = _proyecto(conn, proyecto_id)
        anteriores = _valores(p)
        diff = {k: v for k, v in limpios.items() if v != anteriores[k]}
        if not diff:
            return {"status": "ok", "cambiados": [], "mensaje": "Sin cambios: no se escribió nada.",
                    "duda_resuelta_id": None, "valores": anteriores}
        respaldo = _respaldar_bd(conn, Path(config.obtener_db_path()))
        conn.isolation_level = None
        duda_id = None
        try:
            conn.execute("BEGIN IMMEDIATE")
            ahora = datetime.now().isoformat()
            sets = ", ".join(f"{k} = ?" for k in diff)
            conn.execute(f"UPDATE proyectos SET {sets}, actualizado = CURRENT_TIMESTAMP WHERE id = ?",
                         (*diff.values(), proyecto_id))
            for k, nuevo in diff.items():
                conn.execute("""INSERT INTO auditoria (fecha_hora, usuario, modulo, accion, entidad_id, detalle_json)
                                VALUES (?, ?, ?, ?, ?, ?)""",
                             (ahora, usuario, MODULO_AUDITORIA, ACCION_EDITAR, proyecto_id,
                              json.dumps({"campo": k, "anterior": anteriores[k], "nuevo": nuevo,
                                          "respaldo": Path(respaldo).name}, ensure_ascii=False)))
            duda = conn.execute("""SELECT id FROM dudas_y_hallazgos WHERE proyecto_id = ? AND visita_id IS NULL
                                   AND campo_afectado = ? AND resuelta = 0""", (proyecto_id, CAMPO_DUDA)).fetchone()
            if duda:
                duda_id = duda["id"]
                respuesta = "Cabecera editada y guardada en la app por " + usuario + ": " + ", ".join(diff) + "."
                conn.execute("""UPDATE dudas_y_hallazgos SET resuelta = 1, respuesta_usuario = ?, resuelto_en = ?
                                WHERE id = ?""", (respuesta, ahora, duda_id))
                conn.execute("""INSERT INTO auditoria (fecha_hora, usuario, modulo, accion, entidad_id, detalle_json)
                                VALUES (?, ?, ?, ?, ?, ?)""",
                             (ahora, usuario, MODULO_AUDITORIA, "RESOLVER_DUDA_CABECERA", proyecto_id,
                              json.dumps({"duda_id": duda_id, "campo_afectado": CAMPO_DUDA,
                                          "respuesta_usuario": respuesta}, ensure_ascii=False)))
            conn.execute("COMMIT")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        nuevos = {**anteriores, **diff}
        n = len(diff)
        return {"status": "ok", "cambiados": list(diff), "duda_resuelta_id": duda_id, "valores": nuevos,
                "mensaje": f"{n} campo{'s' if n != 1 else ''} cambiado{'s' if n != 1 else ''}."
                           + (" Se cerró la duda de la cabecera." if duda_id else "")}
    finally:
        conn.close()


@router.get("/api/proyectos/{proyecto_id}/cabecera")
def api_obtener_cabecera(proyecto_id: str):
    return obtener_cabecera(proyecto_id)


@router.put("/api/proyectos/{proyecto_id}/cabecera")
def api_guardar_cabecera(proyecto_id: str, cuerpo: Dict = Body(...), usuario: str = None):
    """Cuerpo: cualquier subconjunto de los 7 campos como texto, p. ej. {"sector": "Cap Cana"}."""
    return guardar_cabecera(proyecto_id, cuerpo, usuario)
