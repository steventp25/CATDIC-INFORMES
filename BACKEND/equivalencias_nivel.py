# backend/equivalencias_nivel.py
# Etapa 7 · T6 — Equivalencia entre el nivel de la visita (S-2) y el rango impreso del plano (E-1 @ E-2).
# La tabla `equivalencias_nivel` la llena SOLO el usuario (nunca se deduce): el cuadro de columnas del plano no da
# ejes (decisión D11) y el rango impreso no dice a qué sótano corresponde. Sin la fila, el cruce abre una duda.
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import config
from database import _respaldar_bd, get_connection, usuario_auditoria

MODULO_AUDITORIA = "EQUIVALENCIAS_NIVEL"
ACCION_GUARDAR = "GUARDAR_EQUIVALENCIAS_NIVEL"
_MAX_NIVEL, _MAX_RANGO = 60, 80
_RE_SOTANO = re.compile(r"^S-?(\d+)$")

router = APIRouter()


class ErrorEquivalencia(Exception):
    def __init__(self, mensaje: str, status: int = 400):
        super().__init__(mensaje)
        self.status = status


def normalizar_nivel(texto) -> str:
    """
    Normalización EXACTA para comparar niveles: mayúsculas, espacios repetidos colapsados y sin espacios alrededor
    de '-' y '@'. Nada más (no se quitan acentos ni palabras, no se expanden rangos).
    'SOTANO S - 2' -> 'SOTANO S-2'; 'E-3 @ E-8' y 'E-3@E-8' -> 'E-3@E-8'.
    """
    n = " ".join(str(texto or "").upper().split())
    return re.sub(r"\s*([-@])\s*", r"\1", n)


def clave_nivel_visita(texto) -> str:
    """Clave del nivel de la visita en la tabla: normalizado; un sótano se escribe siempre 'S-n' ('S2' -> 'S-2')."""
    n = normalizar_nivel(texto)
    m = _RE_SOTANO.fullmatch(n)
    return f"S-{int(m.group(1))}" if m else n


def equivalencia_de(conn, proyecto_id: str, nivel_visita: str) -> Optional[str]:
    """El rango impreso (tal como lo escribió el usuario) para ese nivel de la visita en esa obra; None si no hay."""
    fila = conn.execute("SELECT rango_impreso FROM equivalencias_nivel WHERE proyecto_id = ? AND nivel_visita = ?",
                        (proyecto_id, clave_nivel_visita(nivel_visita))).fetchone()
    return fila["rango_impreso"] if fila else None


def _ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _proyecto(conn, proyecto_id: str):
    fila = conn.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,)).fetchone()
    if fila is None:
        raise ErrorEquivalencia("Proyecto no encontrado.", 404)


def _rangos_del_diseno(conn, proyecto_id: str) -> List[str]:
    return [r[0] for r in conn.execute("SELECT DISTINCT nivel_rango FROM elementos_diseno WHERE proyecto_id = ? "
                                       "ORDER BY nivel_rango", (proyecto_id,))]


def listar_equivalencias(proyecto_id: str) -> Dict:
    """Las equivalencias de la obra, más los rangos que trae el diseño y los niveles que traen las visitas (ayuda
    para llenar la tabla; no se aplica nada de eso)."""
    conn = get_connection()
    try:
        _proyecto(conn, proyecto_id)
        filas = [dict(r) for r in conn.execute(
            "SELECT nivel_visita, rango_impreso, actualizado_por, actualizado FROM equivalencias_nivel "
            "WHERE proyecto_id = ? ORDER BY nivel_visita", (proyecto_id,))]
        niveles = [r[0] for r in conn.execute(
            """SELECT DISTINCT ev.nivel FROM elementos_visita ev JOIN visitas v ON v.id = ev.visita_id
               WHERE v.proyecto_id = ? ORDER BY ev.nivel""", (proyecto_id,))]
        rangos = _rangos_del_diseno(conn, proyecto_id)
    finally:
        conn.close()
    return {"proyecto_id": proyecto_id, "equivalencias": filas, "rangos_en_diseno": rangos,
            "niveles_en_visitas": niveles}


def _limpiar(item: Dict) -> tuple:
    nivel = clave_nivel_visita(item.get("nivel_visita", ""))
    rango = " ".join(str(item.get("rango_impreso", "")).split())  # tal cual está impreso (solo espacios colapsados)
    if not nivel:
        raise ErrorEquivalencia("Cada equivalencia necesita el nivel de la visita (p. ej. S-2).")
    if len(nivel) > _MAX_NIVEL or len(rango) > _MAX_RANGO:
        raise ErrorEquivalencia(f"El nivel '{nivel[:20]}…' o su rango impreso es demasiado largo.")
    return nivel, rango


def guardar_equivalencias(proyecto_id: str, items: List[Dict], usuario: Optional[str] = None) -> Dict:
    """
    Guarda (o cambia) la equivalencia de cada nivel de la visita. Un `rango_impreso` vacío borra la fila de ese nivel.
    Respalda la BD antes y deja una fila de auditoría con el valor anterior y el nuevo.
    """
    usuario = usuario or usuario_auditoria()
    if not items:
        raise ErrorEquivalencia("No hay equivalencias que guardar.")
    limpios = [_limpiar(i) for i in items]
    repetidos = sorted({n for n, _ in limpios if [x for x, _ in limpios].count(n) > 1})
    if repetidos:  # un nivel de visita solo puede tener una equivalencia por obra
        raise ErrorEquivalencia(f"El nivel {', '.join(repetidos)} viene más de una vez: solo puede tener una equivalencia.")
    conn = get_connection()
    conn.isolation_level = None
    try:
        _proyecto(conn, proyecto_id)
        respaldo = _respaldar_bd(conn, Path(config.obtener_db_path()))
        conn.execute("BEGIN IMMEDIATE")
        try:
            ahora, cambios = _ahora(), []
            for nivel, rango in limpios:
                previo = conn.execute("SELECT rango_impreso FROM equivalencias_nivel WHERE proyecto_id = ? AND "
                                      "nivel_visita = ?", (proyecto_id, nivel)).fetchone()
                anterior = previo["rango_impreso"] if previo else None
                if rango:
                    conn.execute("""INSERT INTO equivalencias_nivel (proyecto_id, nivel_visita, rango_impreso,
                                    actualizado_por, actualizado) VALUES (?, ?, ?, ?, ?)
                                    ON CONFLICT(proyecto_id, nivel_visita) DO UPDATE SET
                                    rango_impreso = excluded.rango_impreso, actualizado_por = excluded.actualizado_por,
                                    actualizado = excluded.actualizado""", (proyecto_id, nivel, rango, usuario, ahora))
                else:
                    conn.execute("DELETE FROM equivalencias_nivel WHERE proyecto_id = ? AND nivel_visita = ?",
                                 (proyecto_id, nivel))
                cambios.append({"nivel_visita": nivel, "anterior": anterior, "nuevo": rango or None})
            conn.execute("""INSERT INTO auditoria (fecha_hora, usuario, modulo, accion, entidad_id, detalle_json)
                            VALUES (?, ?, ?, ?, ?, ?)""",
                         (ahora, usuario, MODULO_AUDITORIA, ACCION_GUARDAR, proyecto_id,
                          json.dumps({"cambios": cambios, "respaldo": Path(respaldo).name}, ensure_ascii=False)))
            conn.execute("COMMIT")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        rangos = {normalizar_nivel(r) for r in _rangos_del_diseno(conn, proyecto_id)}
    finally:
        conn.close()
    # Aviso (no bloquea): el rango escrito no es ninguno de los que trae el diseño de la obra
    avisos = [f"El rango '{r}' del nivel {n} no coincide con ningún rango impreso del diseño de la obra."
              for n, r in limpios if r and normalizar_nivel(r) not in rangos]
    return {"guardadas": len(cambios), "cambios": cambios, "avisos": avisos, "respaldo": Path(respaldo).name}


# ---------- API ----------

class EquivalenciaNivel(BaseModel):
    nivel_visita: str
    rango_impreso: str


class EquivalenciasNivel(BaseModel):
    items: List[EquivalenciaNivel]


@router.get("/api/proyectos/{proyecto_id}/equivalencias-nivel")
def api_listar_equivalencias(proyecto_id: str):
    try:
        return listar_equivalencias(proyecto_id)
    except ErrorEquivalencia as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc))


@router.put("/api/proyectos/{proyecto_id}/equivalencias-nivel")
def api_guardar_equivalencias(proyecto_id: str, cuerpo: EquivalenciasNivel):
    try:
        return guardar_equivalencias(proyecto_id, [i.model_dump() for i in cuerpo.items])
    except ErrorEquivalencia as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc))
