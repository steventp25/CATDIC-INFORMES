# backend/sync/cabecera_propuesta.py
# Etapa 7 · T7 — Cabecera del proyecto PROPUESTA desde los STP-MIVED ya entregados (hoja de inspección, p. 2).
# Solo lectura de los PDF. Lo que se lee se guarda como PROPUESTA (tabla `propuestas_proyecto`) con la cita de cada
# informe (archivo y página); NUNCA se escribe en las columnas de `proyectos`: confirmar es de Steven.
# Regla de Oro: sin interpretar el valor; si dos informes discrepan no se elige uno; si falta, "pendiente de verificar".
# §3.1: la dirección de CATDIC (Arroyo Hondo Viejo) no es la de la obra y se descarta.
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

import pymupdf
from fastapi import APIRouter, HTTPException

import config
from database import _respaldar_bd, get_connection, usuario_auditoria
from reglas_ingenieria import PENDIENTE

MODULO_AUDITORIA = "CABECERA_PROPUESTA"
ACCION_PROPONER = "PROPONER_CABECERA"
CAMPO_DUDA = "proyecto.cabecera_propuesta"
ID_ELEMENTO_DUDA = "(obra)"  # mismo marcador que las dudas de obra de obras.py
ESTADO_PROPUESTA = "propuesta"

# Campo de `proyectos` -> rótulo impreso en la hoja de inspección (texto normalizado, sin los dos puntos)
ROTULOS = {
    "no_solicitud": "NO. SOLICITUD",
    "no_licencia": "LICENCIA",
    "direccion_obra": "DIRECCION",
    "provincia": "PROVINCIA",
    "sector": "SECTOR",
    "residente_obra": "NOMBRE Y COLEGIATURA DEL RESIDENTE DE OBRA",
}
CAMPOS = tuple(ROTULOS)

# Geometría de la hoja de inspección (Carta, puntos): rótulos a la izquierda, valores en la columna de x≈182.
# Los rótulos de la columna derecha (x≈282, p. ej. «NUMERO DE FORMULARIO») quedan fuera de la columna de valores.
X_MAX_ROTULO = 150.0
X_MIN_VALOR, X_MAX_VALOR = 150.0, 275.0
TOL_Y = 4.0

# Direcciones de CATDIC (§3.1): jamás son la de la obra
_MARCAS_CATDIC = ("ARROYO HONDO", "CALLE PROYECTO NO")

router = APIRouter()


# ---------- Lectura de la hoja de inspección ----------

def _norm(texto: str) -> str:
    """Mayúsculas, espacios (incluido el no separable) colapsados. Solo para comparar rótulos y valores."""
    return " ".join(str(texto or "").replace("\xa0", " ").upper().split())


def _sin_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def _clave_rotulo(texto: str) -> str:
    return _sin_acentos(_norm(texto)).rstrip(" :").strip()


def _lineas(pagina) -> List[Dict]:
    """Las líneas de texto de la página con su caja, tal como están (sin reordenar nada)."""
    lineas = []
    for b in pagina.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            txt = "".join(s["text"] for s in l["spans"]).replace("\xa0", " ").strip()
            if txt:
                x0, y0, x1, y1 = l["bbox"]
                lineas.append({"texto": txt, "x0": x0, "y0": y0, "x1": x1, "y1": y1})
    return lineas


def es_hoja_inspeccion(pagina) -> bool:
    t = _sin_acentos(_norm(pagina.get_text()))
    return "NOMBRE DEL PROYECTO" in t and "NO. SOLICITUD" in t


def leer_hoja_inspeccion(pagina) -> Dict[str, str]:
    """
    Valor que sigue a cada rótulo de CAMPOS, por posición: el texto de la columna de valores cuya fila cae
    bajo el rótulo (el rótulo del residente ocupa dos líneas). Sin interpretar: se devuelve el texto tal cual
    (espacios colapsados). Un rótulo sin valor da "" y un rótulo que no está en la hoja no aparece.
    """
    lineas = _lineas(pagina)
    corte = next((l["y0"] for l in lineas if _clave_rotulo(l["texto"]) == "OBSERVACIONES DURANTE LA INSPECCION"),
                 float("inf"))
    lineas = [l for l in lineas if l["y0"] < corte]
    # Rótulos: líneas de la columna izquierda; una sin «:» continúa en la siguiente («...RESIDENTE DE» + «OBRA :»)
    rotulos: List[Dict] = []
    continua = False
    for l in sorted((l for l in lineas if l["x0"] < X_MAX_ROTULO), key=lambda l: l["y0"]):
        if continua and rotulos:
            rotulos[-1]["texto"] += " " + l["texto"]
            rotulos[-1]["y1"] = l["y1"]
        else:
            rotulos.append({"texto": l["texto"], "y0": l["y0"], "y1": l["y1"], "valores": []})
        continua = ":" not in l["texto"]
    for l in sorted((l for l in lineas if X_MIN_VALOR <= l["x0"] < X_MAX_VALOR), key=lambda l: (l["y0"], l["x0"])):
        centro = (l["y0"] + l["y1"]) / 2
        previos = [r for r in rotulos if r["y0"] - TOL_Y <= centro]
        if previos:
            previos[-1]["valores"].append(l["texto"])
    por_clave = {_clave_rotulo(r["texto"]): " ".join(" ".join(r["valores"]).split()) for r in rotulos}
    return {campo: por_clave[_clave_rotulo(rot)] for campo, rot in ROTULOS.items() if _clave_rotulo(rot) in por_clave}


def _es_direccion_catdic(valor: str) -> bool:
    v = _sin_acentos(_norm(valor))
    return any(m in v for m in _MARCAS_CATDIC)


def _fecha_nombre(nombre: str):
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})", nombre)
    return (m.group(3), m.group(2), m.group(1)) if m else ("", "", "")


def listar_stp(fuente: Union[str, Path, Sequence]) -> List[Path]:
    """Los STP-MIVED (`* - STP - *.pdf`) de una carpeta (recursivo) o de una lista; sin VERSIONES ANTERIORES."""
    if isinstance(fuente, (str, Path)):
        base = Path(fuente)
        candidatos = sorted(p for p in base.rglob("*") if p.is_file()) if base.is_dir() else []
    else:
        candidatos = [Path(p) for p in fuente]
    salida = []
    for p in candidatos:
        if p.suffix.lower() != ".pdf" or " - stp - " not in p.name.lower():
            continue
        if any("VERSIONES ANTERIORES" in _norm(parte) for parte in p.parts):
            continue
        salida.append(p)
    return salida


# ---------- Consolidación ----------

def _cita(pdf: Path, pagina: int, base: Optional[Path]) -> Dict:
    try:
        archivo = str(pdf.relative_to(base)) if base else pdf.name
    except ValueError:
        archivo = pdf.name
    return {"archivo": archivo, "pagina": pagina}


def leer_informes(pdfs: Sequence[Path], base: Optional[Path] = None) -> Dict:
    """Lee la hoja de cada informe (solo lectura). Devuelve los valores por informe y las notas de lo que no se pudo."""
    informes, notas = [], []
    for pdf in sorted(pdfs, key=lambda p: (_fecha_nombre(p.name), p.name)):
        try:
            with pymupdf.open(str(pdf)) as doc:
                hoja = next((i for i, pg in enumerate(doc) if es_hoja_inspeccion(pg)), None)
                valores = leer_hoja_inspeccion(doc[hoja]) if hoja is not None else None
        except Exception as exc:  # PDF dañado o ilegible: se anota y se sigue
            notas.append(f"{pdf.name}: no se pudo leer ({type(exc).__name__}).")
            continue
        if valores is None:
            notas.append(f"{pdf.name}: no tiene hoja de inspección (NOMBRE DEL PROYECTO / NO. SOLICITUD).")
            continue
        informes.append({"cita": _cita(pdf, hoja + 1, base), "valores": valores})
    return {"informes": informes, "notas": notas}


def consolidar(informes: List[Dict]) -> Dict[str, Dict]:
    """
    Por campo: 'coincide' (todos los que lo traen dicen lo mismo), 'discrepa' (no se elige) o 'pendiente'
    (ningún informe lo trae). `informes` va ordenado del más antiguo al más reciente.
    """
    resultado = {}
    for campo in CAMPOS:
        con_valor: Dict[str, Dict] = {}  # valor normalizado -> {literales, citas}
        sin_valor, notas = [], []
        for inf in informes:
            crudo = inf["valores"].get(campo, "")
            if crudo and _es_direccion_catdic(crudo):
                notas.append(f"{inf['cita']['archivo']} p. {inf['cita']['pagina']}: trae la dirección de CATDIC "
                             f"(§3.1), no es la de la obra; se descartó.")
                crudo = ""
            if not crudo:
                sin_valor.append(inf["cita"])
                continue
            g = con_valor.setdefault(_norm(crudo), {"literales": [], "citas": []})
            g["literales"].append(crudo)
            g["citas"].append(inf["cita"])
        base = {"informes_leidos": len(informes), "informes_sin_valor": sin_valor, "notas": notas}
        if not con_valor:
            resultado[campo] = {"situacion": "pendiente", "valor": PENDIENTE, "fuente": {**base, "valores": []}}
            continue
        valores = [{"valor": max(set(g["literales"]), key=g["literales"].count), "conteo": len(g["citas"]),
                    "informes": g["citas"], "mas_reciente": g["citas"][-1]} for g in con_valor.values()]
        if len(valores) == 1:
            resultado[campo] = {"situacion": "coincide", "valor": valores[0]["valor"],
                                "fuente": {**base, "valores": valores}}
        else:
            resultado[campo] = {"situacion": "discrepa", "valor": PENDIENTE, "fuente": {**base, "valores": valores}}
    return resultado


# ---------- Persistencia ----------

def _asegurar_tabla(conn) -> None:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS propuestas_proyecto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proyecto_id TEXT NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
        campo TEXT NOT NULL,                 -- columna de `proyectos` a la que se refiere
        valor TEXT NOT NULL,                 -- el valor propuesto, o 'pendiente de verificar' (discrepa / no viene)
        situacion TEXT NOT NULL CHECK(situacion IN ('coincide', 'discrepa', 'pendiente')),
        fuente_json TEXT NOT NULL,           -- citas: archivo y página de cada informe, conteos, notas
        estado TEXT NOT NULL DEFAULT 'propuesta',   -- 'propuesta' (sin confirmar); solo Steven la confirma
        creado TEXT NOT NULL,
        UNIQUE(proyecto_id, campo)
    )""")


def _ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def _texto_duda(consolidado: Dict[str, Dict]) -> str:
    por = {s: [c for c in CAMPOS if consolidado[c]["situacion"] == s] for s in ("coincide", "discrepa", "pendiente")}
    partes = []
    if por["coincide"]:
        partes.append(f"coinciden en todos los informes: {', '.join(por['coincide'])}")
    if por["discrepa"]:
        partes.append(f"los informes discrepan (no se eligió ninguno): {', '.join(por['discrepa'])}")
    if por["pendiente"]:
        partes.append(f"ningún informe lo trae ({PENDIENTE}): {', '.join(por['pendiente'])}")
    return ("Cabecera propuesta desde STP entregados: confirma o corrige " + ", ".join(CAMPOS) + ". "
            + "; ".join(partes).capitalize() + ". Nada se escribió en los datos de la obra.")


def _proyecto(conn, proyecto_id: str):
    p = conn.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,)).fetchone()
    if p is None:
        raise ErrorCabecera("Proyecto no encontrado.", 404)
    return p


class ErrorCabecera(Exception):
    def __init__(self, mensaje: str, status: int = 400):
        super().__init__(mensaje)
        self.status = status


def _carpeta_informes(proyecto) -> Path:
    """Carpeta de salida de la obra, de la tabla `proyectos` (nunca quemada)."""
    return Path(proyecto["carpeta_dropbox"] or "") / Path(str(proyecto["carpeta_salida"] or "").replace("\\", "/"))


def proponer_cabecera(proyecto_id: str, fuente: Union[str, Path, Sequence, None] = None, escribir: bool = True,
                      usuario: Optional[str] = None) -> Dict:
    """
    Lee los STP-MIVED (carpeta o lista de PDF; por omisión la carpeta de salida de la obra) y propone la cabecera.
    `escribir=False` solo calcula. Con `escribir=True` guarda la propuesta SIN confirmar, abre UNA duda de
    proyecto y deja auditoría, con respaldo previo de la BD. Idempotente: si nada cambió no escribe nada.
    Una propuesta que Steven ya confirmó o descartó (estado distinto de 'propuesta') no se pisa.
    """
    usuario = usuario or usuario_auditoria()
    conn = get_connection()
    try:
        proyecto = _proyecto(conn, proyecto_id)
        if fuente is None:
            fuente = _carpeta_informes(proyecto)
        base = Path(fuente) if isinstance(fuente, (str, Path)) else None
        pdfs = listar_stp(fuente)
        lectura = leer_informes(pdfs, base if base and base.is_dir() else None)
        consolidado = consolidar(lectura["informes"])
        actual = {c: (proyecto[c] if c in proyecto.keys() else "") for c in CAMPOS}
        resultado = {"proyecto_id": proyecto_id, "informes_leidos": len(lectura["informes"]),
                     "informes_encontrados": len(pdfs), "notas": lectura["notas"], "escrito": False,
                     "campos": {c: {"situacion": consolidado[c]["situacion"], "valor": consolidado[c]["valor"],
                                    "fuente": consolidado[c]["fuente"], "actual_en_proyecto": actual[c]}
                                for c in CAMPOS}}
        if not escribir:
            return resultado
        if not lectura["informes"]:
            resultado["notas"].append("Sin informes legibles: no se guardó ninguna propuesta.")
            return resultado
        _asegurar_tabla(conn)
        existentes = {f["campo"]: f for f in conn.execute(
            "SELECT * FROM propuestas_proyecto WHERE proyecto_id = ?", (proyecto_id,))}
        cambios = []
        for c in CAMPOS:
            nuevo = consolidado[c]
            ex = existentes.get(c)
            if ex is not None and ex["estado"] != ESTADO_PROPUESTA:
                continue  # ya la resolvió Steven
            if ex is not None and (ex["valor"], ex["situacion"], ex["fuente_json"]) == (
                    nuevo["valor"], nuevo["situacion"], _json(nuevo["fuente"])):
                continue
            cambios.append((c, nuevo, ex is not None))
        pendientes = [c for c in CAMPOS if (existentes.get(c) is None or existentes[c]["estado"] == ESTADO_PROPUESTA)]
        duda = conn.execute("""SELECT id, descripcion_pregunta FROM dudas_y_hallazgos WHERE proyecto_id = ?
                               AND visita_id IS NULL AND campo_afectado = ? AND resuelta = 0""",
                            (proyecto_id, CAMPO_DUDA)).fetchone()
        texto = _texto_duda(consolidado)
        duda_cambia = bool(pendientes) and (duda is None or duda["descripcion_pregunta"] != texto)
        if not cambios and not duda_cambia:
            return resultado  # idempotente: nada que escribir, sin respaldo ni auditoría
        respaldo = _respaldar_bd(conn, Path(config.obtener_db_path()))
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        try:
            ahora = _ahora()
            for c, nuevo, existe in cambios:
                if existe:
                    conn.execute("""UPDATE propuestas_proyecto SET valor = ?, situacion = ?, fuente_json = ?, creado = ?
                                    WHERE proyecto_id = ? AND campo = ?""",
                                 (nuevo["valor"], nuevo["situacion"], _json(nuevo["fuente"]), ahora, proyecto_id, c))
                else:
                    conn.execute("""INSERT INTO propuestas_proyecto (proyecto_id, campo, valor, situacion, fuente_json,
                                    estado, creado) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                 (proyecto_id, c, nuevo["valor"], nuevo["situacion"], _json(nuevo["fuente"]),
                                  ESTADO_PROPUESTA, ahora))
            duda_id = duda["id"] if duda else None
            if duda_cambia:
                if duda:
                    conn.execute("UPDATE dudas_y_hallazgos SET descripcion_pregunta = ? WHERE id = ?", (texto, duda_id))
                else:
                    duda_id = conn.execute("""INSERT INTO dudas_y_hallazgos (proyecto_id, visita_id, id_elemento,
                        categoria, campo_afectado, descripcion_pregunta, creado) VALUES (?, NULL, ?, 'DUDA_BLOQUEANTE',
                        ?, ?, ?)""", (proyecto_id, ID_ELEMENTO_DUDA, CAMPO_DUDA, texto, ahora)).lastrowid
            conn.execute("""INSERT INTO auditoria (fecha_hora, usuario, modulo, accion, entidad_id, detalle_json)
                            VALUES (?, ?, ?, ?, ?, ?)""",
                         (ahora, usuario, MODULO_AUDITORIA, ACCION_PROPONER, proyecto_id, _json({
                             "informes_leidos": len(lectura["informes"]),
                             "campos": {c: n["situacion"] for c, n, _ in cambios},
                             "duda_id": duda_id, "respaldo": Path(respaldo).name,
                             "nota": "propuesta sin confirmar; `proyectos` no se modificó"})))
            conn.execute("COMMIT")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        resultado.update({"escrito": True, "duda_id": duda_id, "respaldo": Path(respaldo).name})
        return resultado
    finally:
        conn.close()


def obtener_propuesta(proyecto_id: str) -> Dict:
    """Solo lectura: la propuesta guardada, con el valor actual de `proyectos` al lado y la duda abierta."""
    conn = get_connection()
    try:
        proyecto = _proyecto(conn, proyecto_id)
        existe = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='propuestas_proyecto'").fetchone()
        filas = list(conn.execute("SELECT * FROM propuestas_proyecto WHERE proyecto_id = ?", (proyecto_id,))) if existe else []
        duda = conn.execute("""SELECT id FROM dudas_y_hallazgos WHERE proyecto_id = ? AND visita_id IS NULL
                               AND campo_afectado = ? AND resuelta = 0""", (proyecto_id, CAMPO_DUDA)).fetchone()
    finally:
        conn.close()
    por_campo = {f["campo"]: f for f in filas}
    campos = {}
    for c in CAMPOS:
        f = por_campo.get(c)
        campos[c] = None if f is None else {"valor": f["valor"], "situacion": f["situacion"], "estado": f["estado"],
                                            "fuente": json.loads(f["fuente_json"]), "creado": f["creado"],
                                            "actual_en_proyecto": proyecto[c]}
    return {"proyecto_id": proyecto_id, "hay_propuesta": bool(filas), "duda_abierta_id": duda["id"] if duda else None,
            "campos": campos}


@router.get("/api/proyectos/{proyecto_id}/cabecera-propuesta")
def api_cabecera_propuesta(proyecto_id: str):
    """Solo lectura. Confirmar o corregir los datos de la obra es de Steven (PATCH /api/proyectos/{id})."""
    try:
        return obtener_propuesta(proyecto_id)
    except ErrorCabecera as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc))
