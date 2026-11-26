# backend/equivalencias_nivel.py
# Etapa 7 · T6 — Equivalencia entre el nivel de la visita (S-2) y los rangos impresos del plano (E-1 @ E-2, ...).
# Un nivel admite VARIOS rangos por obra (decisión del Líder, 23/11, corrida 1 de T5).
# La tabla `equivalencias_nivel` la llena SOLO el usuario (nunca se deduce): el cuadro de columnas del plano no da
# ejes (decisión D11) y el rango impreso no dice a qué sótano corresponde. Sin la fila, el cruce abre una duda.
import json
import logging
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import config
from database import _respaldar_bd, get_connection, usuario_auditoria

# T14: equivalencias CONFIRMADAS por el usuario, versionadas en git junto al código (no se escriben en la BD).
# Forma: {"reglas": [{"proyecto_id", "nivel_visita", "rango_empieza_con", "confirmado_por", "fecha", "cita", "nota"}]}.
# Cada regla se expande contra los rangos impresos que trae el diseño de ESE proyecto (comparación normalizada).
RUTA_CONFIGURACION = Path(__file__).resolve().parent / "equivalencias_confirmadas.json"
ORIGEN_BD, ORIGEN_CONFIGURACION = "bd", "configuracion_confirmada"
_CAMPOS_REGLA = ("proyecto_id", "nivel_visita", "rango_empieza_con")
log = logging.getLogger(__name__)

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


def cargar_configuracion() -> tuple:
    """
    Reglas confirmadas de la configuración y los avisos de lo que se ignoró. Archivo ausente, JSON roto o regla
    incompleta: se ignora (con aviso en el log y en la lista); nunca rompe el cruce.
    """
    avisos: List[str] = []
    nombre = Path(RUTA_CONFIGURACION).name
    try:
        datos = json.loads(Path(RUTA_CONFIGURACION).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        avisos.append(f"Equivalencias confirmadas ignoradas: no se pudo leer {nombre} ({exc}).")
        log.warning(avisos[-1])
        return [], avisos
    crudas = datos.get("reglas") if isinstance(datos, dict) else None
    if not isinstance(crudas, list):
        avisos.append(f"Equivalencias confirmadas ignoradas: {nombre} no trae la lista `reglas`.")
        log.warning(avisos[-1])
        return [], avisos
    reglas = []
    for i, r in enumerate(crudas, 1):
        if not isinstance(r, dict) or not all(isinstance(r.get(c), str) and r[c].strip() for c in _CAMPOS_REGLA):
            avisos.append(f"Regla {i} de {nombre} ignorada: faltan {', '.join(_CAMPOS_REGLA)}.")
            log.warning(avisos[-1])
            continue
        reglas.append(r)
    return reglas, avisos


def _rangos_de_diseno_si_hay(conn, proyecto_id: str) -> List[str]:
    try:
        return _rangos_del_diseno(conn, proyecto_id)
    except sqlite3.OperationalError as exc:
        if "no such table" in str(exc).lower():
            return []
        raise


def _expandir_regla(regla: Dict, rangos_diseno: List[str]) -> List[str]:
    """Los rangos impresos del diseño que empiezan por `rango_empieza_con` (normalizado), tal como están impresos."""
    prefijo = normalizar_nivel(regla["rango_empieza_con"])
    return [r for r in rangos_diseno if normalizar_nivel(r).startswith(prefijo)]


def reglas_confirmadas_de(conn, proyecto_id: str, nivel_visita: Optional[str] = None) -> List[Dict]:
    """Reglas de la configuración de ese proyecto (y nivel, si se da), cada una con sus `rangos_impresos` ya expandidos."""
    reglas, _ = cargar_configuracion()
    mias = [r for r in reglas if r["proyecto_id"] == proyecto_id
            and (nivel_visita is None or clave_nivel_visita(r["nivel_visita"]) == clave_nivel_visita(nivel_visita))]
    if not mias:
        return []
    rangos = _rangos_de_diseno_si_hay(conn, proyecto_id)
    return [{**r, "nivel_visita": clave_nivel_visita(r["nivel_visita"]), "rangos_impresos": _expandir_regla(r, rangos),
             "origen": ORIGEN_CONFIGURACION} for r in mias]


def equivalencias_bd(conn, proyecto_id: str, nivel_visita: str) -> List[str]:
    """Solo las filas de la tabla (las que escribió el usuario con el PUT)."""
    try:
        return [r["rango_impreso"] for r in conn.execute(
            "SELECT rango_impreso FROM equivalencias_nivel WHERE proyecto_id = ? AND nivel_visita = ? ORDER BY id",
            (proyecto_id, clave_nivel_visita(nivel_visita)))]
    except sqlite3.OperationalError as exc:
        if "no such table" in str(exc).lower():  # BD que no pasó por inicializar_bd(): sin tabla = sin equivalencias
            return []
        raise


def equivalencias_de(conn, proyecto_id: str, nivel_visita: str) -> List[str]:
    """
    Los rangos impresos de ese nivel de la visita en esa obra: filas de la BD (tal como las escribió el usuario) más las
    reglas confirmadas de la configuración, expandidas contra los rangos del diseño. Sin duplicados (comparación
    normalizada); [] si no hay.
    """
    resultado, vistos = [], set()
    otros = [r for regla in reglas_confirmadas_de(conn, proyecto_id, nivel_visita) for r in regla["rangos_impresos"]]
    for rango in equivalencias_bd(conn, proyecto_id, nivel_visita) + otros:
        if normalizar_nivel(rango) not in vistos:
            vistos.add(normalizar_nivel(rango))
            resultado.append(rango)
    return resultado


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
    """Las equivalencias de la obra (por nivel, la lista de rangos), más los rangos que trae el diseño y los niveles
    que traen las visitas (ayuda para llenar la tabla; no se aplica nada de eso)."""
    conn = get_connection()
    try:
        _proyecto(conn, proyecto_id)
        por_nivel: Dict[str, Dict] = {}
        for r in conn.execute("SELECT nivel_visita, rango_impreso, actualizado_por, actualizado FROM equivalencias_nivel "
                              "WHERE proyecto_id = ? ORDER BY nivel_visita, id", (proyecto_id,)):
            f = por_nivel.setdefault(r["nivel_visita"], {"nivel_visita": r["nivel_visita"], "rangos_impresos": [],
                                                         "actualizado_por": r["actualizado_por"], "actualizado": r["actualizado"],
                                                         "origen": ORIGEN_BD})
            f["rangos_impresos"].append(r["rango_impreso"])
            f["actualizado"] = max(f["actualizado"], r["actualizado"])
        niveles = [r[0] for r in conn.execute(
            """SELECT DISTINCT ev.nivel FROM elementos_visita ev JOIN visitas v ON v.id = ev.visita_id
               WHERE v.proyecto_id = ? ORDER BY ev.nivel""", (proyecto_id,))]
        rangos = _rangos_del_diseno(conn, proyecto_id)
        confirmadas = reglas_confirmadas_de(conn, proyecto_id)
    finally:
        conn.close()
    # `equivalencias` = solo la BD (lo editable con el PUT); `equivalencias_confirmadas` = la configuración en git (solo lectura)
    return {"proyecto_id": proyecto_id, "equivalencias": list(por_nivel.values()),
            "equivalencias_confirmadas": confirmadas, "avisos": cargar_configuracion()[1],
            "rangos_en_diseno": rangos, "niveles_en_visitas": niveles}


def _limpiar(item: Dict) -> tuple:
    nivel = clave_nivel_visita(item.get("nivel_visita", ""))
    crudos = item.get("rangos_impresos", [])
    if not isinstance(crudos, (list, tuple)):
        raise ErrorEquivalencia("`rangos_impresos` debe ser una lista de rangos.")
    rangos, vistos = [], set()
    for r in crudos:
        r = " ".join(str(r).split())  # tal cual está impreso (solo espacios colapsados)
        if r and normalizar_nivel(r) not in vistos:  # un rango repetido (o vacío) se ignora
            vistos.add(normalizar_nivel(r))
            rangos.append(r)
    if not nivel:
        raise ErrorEquivalencia("Cada equivalencia necesita el nivel de la visita (p. ej. S-2).")
    if len(nivel) > _MAX_NIVEL or any(len(r) > _MAX_RANGO for r in rangos):
        raise ErrorEquivalencia(f"El nivel '{nivel[:20]}…' o uno de sus rangos impresos es demasiado largo.")
    return nivel, rangos


def guardar_equivalencias(proyecto_id: str, items: List[Dict], usuario: Optional[str] = None) -> Dict:
    """
    Para cada nivel de la visita REEMPLAZA su lista de rangos impresos (un nivel admite varios; los da el usuario).
    Una lista vacía borra el nivel. Respalda la BD antes y deja una fila de auditoría con la lista anterior y la nueva.
    """
    usuario = usuario or usuario_auditoria()
    if not items:
        raise ErrorEquivalencia("No hay equivalencias que guardar.")
    limpios = [_limpiar(i) for i in items]
    niveles = [n for n, _ in limpios]
    repetidos = sorted({n for n in niveles if niveles.count(n) > 1})
    if repetidos:  # la lista de un nivel va completa en un solo elemento
        raise ErrorEquivalencia(f"El nivel {', '.join(repetidos)} viene más de una vez: manda todos sus rangos juntos.")
    conn = get_connection()
    conn.isolation_level = None
    try:
        _proyecto(conn, proyecto_id)
        respaldo = _respaldar_bd(conn, Path(config.obtener_db_path()))
        conn.execute("BEGIN IMMEDIATE")
        try:
            ahora, cambios = _ahora(), []
            for nivel, rangos in limpios:
                anterior = equivalencias_bd(conn, proyecto_id, nivel)
                conn.execute("DELETE FROM equivalencias_nivel WHERE proyecto_id = ? AND nivel_visita = ?",
                             (proyecto_id, nivel))
                for r in rangos:
                    conn.execute("""INSERT INTO equivalencias_nivel (proyecto_id, nivel_visita, rango_impreso,
                                    actualizado_por, actualizado) VALUES (?, ?, ?, ?, ?)""",
                                 (proyecto_id, nivel, r, usuario, ahora))
                cambios.append({"nivel_visita": nivel, "anterior": anterior, "nuevo": rangos})
            conn.execute("""INSERT INTO auditoria (fecha_hora, usuario, modulo, accion, entidad_id, detalle_json)
                            VALUES (?, ?, ?, ?, ?, ?)""",
                         (ahora, usuario, MODULO_AUDITORIA, ACCION_GUARDAR, proyecto_id,
                          json.dumps({"cambios": cambios, "respaldo": Path(respaldo).name}, ensure_ascii=False)))
            conn.execute("COMMIT")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        en_diseno = {normalizar_nivel(r) for r in _rangos_del_diseno(conn, proyecto_id)}
    finally:
        conn.close()
    # Aviso (no bloquea): el rango escrito no es ninguno de los que trae el diseño de la obra
    avisos = [f"El rango '{r}' del nivel {n} no coincide con ningún rango impreso del diseño de la obra."
              for n, rangos in limpios for r in rangos if normalizar_nivel(r) not in en_diseno]
    return {"guardadas": len(cambios), "cambios": cambios, "avisos": avisos, "respaldo": Path(respaldo).name}


# ---------- API ----------

class EquivalenciaNivel(BaseModel):
    nivel_visita: str
    rangos_impresos: List[str]  # todos los rangos del nivel; lista vacía = borrar el nivel


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
