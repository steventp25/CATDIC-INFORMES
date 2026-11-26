# BACKEND/informes_obra.py
# Etapa 5 · B3g — Informes de una obra, de SOLO LECTURA. No hay una tabla de informes: cada PDF que publica el
# procesador de la cola queda en un evento `pdf_generado` de `trabajo_eventos` con
# {visita_id, formato, ruta, con_dudas, bytes}; `creado` es la fecha del evento.
# - informes_de_obra(proyecto_id): los PDF de las visitas de esa obra, del más nuevo al más viejo. Un archivo que ya no
#   está en disco se marca (`existe: false`) y NO se oculta.
# - ruta_registrada(ruta): True solo si `ruta` aparece TAL CUAL en un evento `pdf_generado`. La ruta del archivo que
#   se abre en el navegador solo se sirve si pasa por aquí: no hay rutas libres ni `..`.
# Nunca mueve, borra ni escribe nada (ni en disco ni en la BD).
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from database import get_connection

RE_VERSION = re.compile(r"\s+v(\d+)\.pdf$", re.IGNORECASE)


class ObraNoEncontrada(LookupError):
    """La obra no existe (el endpoint la responde con 404)."""


def version_del_nombre(nombre: str) -> int:
    """La N del sufijo final ' vN' (CLAUDE.md §5.2). Sin sufijo es la primera versión."""
    m = RE_VERSION.search(nombre or "")
    return int(m.group(1)) if m else 1


def _datos(txt) -> Dict:
    try:
        d = json.loads(txt or "{}")
    except (TypeError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def _nombre_de(ruta) -> str:
    # El nombre del archivo, sea cual sea el separador que haya quedado en la ruta registrada.
    return str(ruta or "").replace("\\", "/").rstrip("/").split("/")[-1]


def _existe(ruta) -> bool:
    try:
        return bool(ruta) and Path(ruta).is_file()
    except (OSError, ValueError):
        return False


def informes_de_obra(proyecto_id: str) -> List[Dict]:
    conn = get_connection()
    try:
        if conn.execute("SELECT 1 FROM proyectos WHERE id = ?", (proyecto_id,)).fetchone() is None:
            raise ObraNoEncontrada("Proyecto no encontrado.")
        filas = conn.execute("""
            SELECT e.trabajo_id, e.n, e.datos_json, e.creado, v.id AS visita_id, v.numero, v.nombre_carpeta
            FROM trabajo_eventos e JOIN visitas v ON v.id = json_extract(e.datos_json, '$.visita_id')
            WHERE e.tipo = 'pdf_generado' AND v.proyecto_id = ?
            ORDER BY e.creado DESC, e.trabajo_id DESC, e.n DESC""", (proyecto_id,)).fetchall()
    finally:
        conn.close()
    informes = []
    for f in filas:
        d = _datos(f["datos_json"])
        ruta = d.get("ruta")
        nombre = _nombre_de(ruta)
        bytes_ = d.get("bytes")
        informes.append({
            "formato": d.get("formato"),
            "visita": {"id": f["visita_id"], "numero": f["numero"], "nombre_carpeta": f["nombre_carpeta"]},
            "trabajo_id": f["trabajo_id"],
            "fecha": f["creado"],
            "nombre": nombre or None,
            "version": version_del_nombre(nombre),
            "bytes": bytes_ if isinstance(bytes_, int) and not isinstance(bytes_, bool) else None,
            "con_dudas": bool(d.get("con_dudas")),
            "existe": _existe(ruta),
            "ruta": ruta,
        })
    return informes


def ruta_registrada(ruta: Optional[str]) -> bool:
    """True si `ruta` aparece, igual carácter por carácter, en algún evento `pdf_generado`."""
    if not ruta:
        return False
    conn = get_connection()
    try:
        filas = conn.execute("SELECT datos_json FROM trabajo_eventos WHERE tipo = 'pdf_generado'").fetchall()
    finally:
        conn.close()
    return any(_datos(f["datos_json"]).get("ruta") == ruta for f in filas)
