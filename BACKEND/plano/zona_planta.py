# BACKEND/plano/zona_planta.py
# Etapa 7 · T12 — Zona de planta de una hoja del plano vigente (PLANES/etapa-7.md, T12).
#
# LOCALIZACION es la planta estructural ENTERA recortada a su dibujo: sin cajetín, tablas, notas ni otros dibujos de
# la hoja. La zona se propone una vez por hoja y se confirma en el visor; todos los elementos de esa planta la
# comparten (tabla `zonas_planta`, una fila por (plano_id, pagina)).
#
# Propuesta (siempre «pendiente de verificar»; nunca pisa una zona confirmada):
#   1. Rótulos de ejes: spans de texto cuyo contenido completo es una letra (`A`, `A'`) o un número de 1-2 cifras
#      (`1`, `2'`), del mismo tamaño y alineados (mismo centro y ±3 pt) en una fila o una columna, con rótulos TODOS
#      DISTINTOS (una fila de «1 1 1» o una columna de la misma letra es una tabla o un texto repetido, no una
#      retícula). Se elige la pareja (fila de letras + columna de números, o al revés, con el MISMO tamaño de texto:
#      los globos de una retícula comparten tamaño; así el encabezado «A B C» de una tabla no se une a una columna
#      de números de otro tamaño) de más rótulos y se suman
#      sus gemelos del extremo opuesto (mismo tamaño y mismo conjunto de rótulos). Hacen falta al menos 2 letras y
#      2 números; si no, la zona queda `vacia` con su motivo y su duda.
#   2. `ejes_rect` = envolvente de esos rótulos (sin margen).
#   3. La retícula casi nunca rodea la planta: en una hoja real los globos están en una fila y una columna de cotas,
#      fuera del contorno, y la planta se extiende más allá de ellos. Por eso la propuesta crece desde los rótulos por
#      el DIBUJO CONECTADO: la hoja se rasteriza a baja resolución, se dilata `HUECO_CONEXION_PT` y se toma el conjunto
#      conexo que toca los rótulos (cotas, retícula, contorno y cuerpo de la planta quedan unidos; el cajetín, las
#      tablas y los demás dibujos están separados por más de ese hueco). Se recorta la dilatación y se une con
#      `ejes_rect`.
#   4. Margen fijo `MARGEN_PT` = 30 pt alrededor de esa envolvente, recortado a los límites de la hoja.
#   Regla anti-zoom (error 1): al confirmar, si hay ejes detectados la zona debe contenerlos todos.
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re

import pymupdf
from PIL import Image, ImageDraw, ImageFilter

from database import ESQUEMA_ZONAS_PLANTA, get_connection, usuario_auditoria
from obras import ErrorObra, _proyecto, _transaccion
from reglas_ingenieria import PENDIENTE

MARGEN_PT = 30.0              # margen fijo de la propuesta alrededor de la envolvente (ejes + dibujo conectado)
TOLERANCIA_ALINEACION_PT = 3.0
TOLERANCIA_TAMANO_PT = 0.3    # dos rótulos de la misma retícula tienen el mismo tamaño de letra
HUECO_CONEXION_PT = 48.0      # separación máxima entre dos trazos para considerarlos el mismo dibujo
DPI_CRECIMIENTO = 24          # resolución del rasterizado con el que se agrupa el dibujo conectado
UMBRAL_BLANCO = 235           # un píxel más oscuro que esto es trazo
TOLERANCIA_CONTIENE_PT = 0.05
MODULO_AUDITORIA = "ZONA_PLANTA"
ESTADOS = ("vacia", "pendiente de verificar", "confirmado")

_RE_LETRA = re.compile(r"^[A-Z]'?$")
_RE_NUMERO = re.compile(r"^\d{1,2}'?$")


def _ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ---------- 1. Rótulos de ejes ----------

def _spans_candidatos(page) -> List[Dict]:
    m = page.rotation_matrix
    out = []
    for b in page.get_text("dict")["blocks"]:
        if b["type"] != 0:
            continue
        for l in b["lines"]:
            for s in l["spans"]:
                t = s["text"].replace("\xa0", " ").strip().replace("’", "'")
                clase = "letra" if _RE_LETRA.match(t) else "numero" if _RE_NUMERO.match(t) else None
                if clase:
                    r = pymupdf.Rect(s["bbox"]) * m
                    out.append({"texto": t, "clase": clase, "rect": r, "tam": float(s["size"])})
    return out


def _cadenas(items: List[Dict], clave, tolerancia: float) -> List[List[Dict]]:
    """Agrupa por cadena: un elemento se une al grupo si su clave dista <= tolerancia del vecino anterior."""
    grupos: List[List[Dict]] = []
    for it in sorted(items, key=clave):
        if grupos and clave(it) - clave(grupos[-1][-1]) <= tolerancia:
            grupos[-1].append(it)
        else:
            grupos.append([it])
    return grupos


def _grupos_alineados(spans: List[Dict]) -> List[Dict]:
    """Grupos {clase, orientacion ('fila'|'columna'), miembros} del mismo tamaño, alineados y de rótulos distintos."""
    grupos = []
    for clase in ("letra", "numero"):
        propios = [s for s in spans if s["clase"] == clase]
        for orient, centro in (("fila", lambda s: (s["rect"].y0 + s["rect"].y1) / 2),
                               ("columna", lambda s: (s["rect"].x0 + s["rect"].x1) / 2)):
            for por_tam in _cadenas(propios, lambda s: s["tam"], TOLERANCIA_TAMANO_PT):
                for g in _cadenas(por_tam, centro, TOLERANCIA_ALINEACION_PT):
                    if len(g) >= 2 and len({s["texto"] for s in g}) == len(g):
                        grupos.append({"clase": clase, "orientacion": orient, "miembros": g})
    return grupos


def _con_gemelos(grupo: Dict, todos: List[Dict]) -> List[Dict]:
    """Miembros del grupo y los de los grupos del mismo tamaño, orientación y conjunto de rótulos (extremo opuesto)."""
    textos = {s["texto"] for s in grupo["miembros"]}
    tam = grupo["miembros"][0]["tam"]
    miembros = []
    for g in todos:
        if (g["clase"], g["orientacion"]) == (grupo["clase"], grupo["orientacion"]) \
                and {s["texto"] for s in g["miembros"]} == textos \
                and abs(g["miembros"][0]["tam"] - tam) <= TOLERANCIA_TAMANO_PT:
            miembros += g["miembros"]
    return miembros


def _union(rects) -> pymupdf.Rect:
    u = pymupdf.Rect(rects[0])
    for r in rects[1:]:
        u |= r
    return u


def _rect_lista(r) -> List[float]:
    return [round(float(v), 2) for v in (r.x0, r.y0, r.x1, r.y1)]


def detectar_rotulos_ejes(page) -> Dict:
    """
    Rótulos de los ejes de la hoja (ver el encabezado). Devuelve {letras, numeros, ejes_rect, motivo}: cada rótulo es
    {texto, bbox}; `ejes_rect` es la envolvente de los rótulos (sin margen) o None si no hay al menos 2 letras y
    2 números distintos alineados; `motivo` explica por qué no (o None).
    """
    spans = _spans_candidatos(page)
    grupos = _grupos_alineados(spans)
    mejor = None
    for letras in (g for g in grupos if g["clase"] == "letra"):
        for numeros in (g for g in grupos if g["clase"] == "numero" and g["orientacion"] != letras["orientacion"]
                        and abs(g["miembros"][0]["tam"] - letras["miembros"][0]["tam"]) <= TOLERANCIA_TAMANO_PT):
            ml, mn = _con_gemelos(letras, grupos), _con_gemelos(numeros, grupos)
            puntaje = (len(letras["miembros"]) + len(numeros["miembros"]),
                       letras["miembros"][0]["tam"] + numeros["miembros"][0]["tam"])
            if mejor is None or puntaje > mejor[0]:
                mejor = (puntaje, ml, mn)
    if mejor is None:
        n_l = max((len(g["miembros"]) for g in grupos if g["clase"] == "letra"), default=0)
        n_n = max((len(g["miembros"]) for g in grupos if g["clase"] == "numero"), default=0)
        return {"letras": [], "numeros": [], "ejes_rect": None,
                "motivo": (f"No hay una retícula de ejes legible: se necesitan al menos 2 letras y 2 números distintos "
                           f"alineados (una fila y una columna del mismo tamaño); la mejor fila/columna tiene {n_l} "
                           f"letra(s) y {n_n} número(s).")}
    _, ml, mn = mejor
    envolvente = _union([s["rect"] for s in ml + mn])
    rotulo = lambda s: {"texto": s["texto"], "bbox": _rect_lista(s["rect"])}  # noqa: E731
    return {"letras": [rotulo(s) for s in ml], "numeros": [rotulo(s) for s in mn],
            "ejes_rect": _rect_lista(envolvente), "motivo": None}


# ---------- 2. Dibujo conectado ----------

def dibujo_conectado(page, semillas: List[pymupdf.Rect]) -> Optional[List[float]]:
    """
    Envolvente (pt, marco visual) del dibujo conexo que toca las semillas: se rasteriza la hoja a DPI_CRECIMIENTO,
    se dilata HUECO_CONEXION_PT/2 por lado y se rellena desde cada semilla. Se devuelve la caja del relleno sin la
    dilatación, o None si ninguna semilla cae sobre trazo.
    """
    esc = DPI_CRECIMIENTO / 72.0
    pix = page.get_pixmap(dpi=DPI_CRECIMIENTO, colorspace=pymupdf.csGRAY, alpha=False)
    gris = Image.frombytes("L", (pix.width, pix.height), pix.samples)
    trazo = gris.point(lambda v: 255 if v < UMBRAL_BLANCO else 0)
    k = max(1, round(HUECO_CONEXION_PT / 2 * esc))
    dil = trazo.filter(ImageFilter.MaxFilter(2 * k + 1))
    for s in semillas:
        p = (min(pix.width - 1, max(0, int((s.x0 + s.x1) / 2 * esc))), min(pix.height - 1, max(0, int((s.y0 + s.y1) / 2 * esc))))
        if dil.getpixel(p) == 255:
            ImageDraw.floodfill(dil, p, 128)
    caja = dil.point(lambda v: 255 if v == 128 else 0).getbbox()
    if caja is None:
        return None
    x0, y0, x1, y1 = caja[0] + k, caja[1] + k, caja[2] - k, caja[3] - k
    if x1 <= x0 or y1 <= y0:
        return None
    return [x0 / esc, y0 / esc, x1 / esc, y1 / esc]


def calcular_propuesta(page) -> Dict:
    """
    {estado, rect, fuente, motivo, ejes_rect}: `rect` ya con margen y recortado a la hoja, o None (estado `vacia`).
    No toca la base de datos.
    """
    ejes = detectar_rotulos_ejes(page)
    if ejes["ejes_rect"] is None:
        return {"estado": "vacia", "rect": None, "fuente": None, "motivo": ejes["motivo"], "ejes_rect": None}
    er = pymupdf.Rect(ejes["ejes_rect"])
    semillas = [pymupdf.Rect(r["bbox"]) for r in ejes["letras"] + ejes["numeros"]]
    conectado = dibujo_conectado(page, semillas)
    base = pymupdf.Rect(er)
    if conectado:
        base |= pymupdf.Rect(conectado)
    m = MARGEN_PT
    rect = pymupdf.Rect(base.x0 - m, base.y0 - m, base.x1 + m, base.y1 + m) & page.rect
    return {"estado": "pendiente de verificar", "rect": _rect_lista(rect), "motivo": None, "ejes_rect": ejes["ejes_rect"],
            "fuente": {"metodo": "ejes_y_dibujo_conectado", "margen_pt": MARGEN_PT, "hueco_conexion_pt": HUECO_CONEXION_PT,
                       "letras": ejes["letras"], "numeros": ejes["numeros"], "ejes_rect": ejes["ejes_rect"],
                       "dibujo_conectado": [round(v, 2) for v in conectado] if conectado else None}}


def contiene(rect: List[float], interior: List[float], tol: float = TOLERANCIA_CONTIENE_PT) -> bool:
    return (rect[0] <= interior[0] + tol and rect[1] <= interior[1] + tol
            and rect[2] >= interior[2] - tol and rect[3] >= interior[3] - tol)


# ---------- 3. Persistencia ----------

def _plano_vigente(conn, proyecto_id: str):
    _proyecto(conn, proyecto_id)
    fila = conn.execute("SELECT * FROM planos WHERE proyecto_id = ? AND estado = 'vigente'", (proyecto_id,)).fetchone()
    if fila is None:
        raise ErrorObra("La obra no tiene plano vigente: sube primero el vectorial y el sellado.", 409)
    return fila


def _abrir_hoja(plano, pagina: int):
    if not 1 <= pagina <= plano["vectorial_paginas"]:
        raise ErrorObra(f"La hoja {pagina} no existe: el vectorial tiene {plano['vectorial_paginas']} hojas.", 404)
    try:
        return pymupdf.Document(plano["vectorial_ruta"])
    except Exception:  # noqa: BLE001  (archivo ausente o ilegible)
        raise ErrorObra("El archivo del vectorial vigente no está en la carpeta de datos.", 409) from None


def _asegurar_tabla(conn) -> None:
    conn.execute(ESQUEMA_ZONAS_PLANTA)


def _fila(conn, plano_id: int, pagina: int):
    existe = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='zonas_planta'").fetchone()
    if not existe:
        return None
    return conn.execute("SELECT * FROM zonas_planta WHERE plano_id = ? AND pagina = ?", (plano_id, pagina)).fetchone()


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def _vista(fila, ejes_rect: Optional[List[float]], plano_id: int, pagina: int) -> Dict:
    if fila is None:
        return {"plano_id": plano_id, "pagina": pagina, "estado": "vacia", "rect": None, "origen": None, "fuente": None,
                "motivo": "Todavía no se ha propuesto la zona de planta de esta hoja.", "ejes_rect": ejes_rect}
    return {"plano_id": plano_id, "pagina": pagina, "estado": fila["estado"],
            "rect": json.loads(fila["rect_json"]) if fila["rect_json"] else None, "origen": fila["origen"],
            "fuente": json.loads(fila["fuente_json"]) if fila["fuente_json"] else None, "motivo": fila["motivo"],
            "ejes_rect": ejes_rect, "actualizado_por": fila["actualizado_por"], "actualizado": fila["actualizado"]}


def _campo_duda(plano_id: int, pagina: int) -> str:
    return f"plano:{plano_id}:p{pagina}:zona_planta"


def _duda_abierta(conn, proyecto_id: str, campo: str):
    return conn.execute("""SELECT id, descripcion_pregunta FROM dudas_y_hallazgos WHERE proyecto_id = ? AND visita_id IS NULL
                           AND campo_afectado = ? AND resuelta = 0""", (proyecto_id, campo)).fetchone()


def _abrir_duda(conn, proyecto_id: str, campo: str, texto: str) -> int:
    d = _duda_abierta(conn, proyecto_id, campo)
    if d:
        if d["descripcion_pregunta"] != texto:
            conn.execute("UPDATE dudas_y_hallazgos SET descripcion_pregunta = ? WHERE id = ?", (texto, d["id"]))
        return d["id"]
    return conn.execute("""INSERT INTO dudas_y_hallazgos (proyecto_id, visita_id, id_elemento, categoria, campo_afectado,
                           descripcion_pregunta, creado) VALUES (?, NULL, '(obra)', 'DUDA_BLOQUEANTE', ?, ?, ?)""",
                        (proyecto_id, campo, texto, _ahora())).lastrowid


def _auditar(conn, usuario: str, accion: str, entidad: str, detalle: Dict) -> None:
    conn.execute("""INSERT INTO auditoria (fecha_hora, usuario, modulo, accion, entidad_id, detalle_json)
                    VALUES (?, ?, ?, ?, ?, ?)""", (_ahora(), usuario, MODULO_AUDITORIA, accion, entidad, _json(detalle)))


def obtener_zona(proyecto_id: str, pagina: int) -> Dict:
    """Solo lectura: la zona guardada de la hoja (o `vacia` sin propuesta) con `ejes_rect` detectado en el vectorial."""
    conn = get_connection()
    try:
        plano = _plano_vigente(conn, proyecto_id)
        fila = _fila(conn, plano["id"], pagina)
    finally:
        conn.close()
    with _abrir_hoja(plano, pagina) as doc:
        ejes = detectar_rotulos_ejes(doc[pagina - 1])
    return _vista(fila, ejes["ejes_rect"], plano["id"], pagina)


def proponer_zona(proyecto_id: str, pagina: int, escribir: bool = True, usuario: Optional[str] = None) -> Dict:
    """
    Propone la zona de la hoja (ver el encabezado). `escribir=False` solo calcula. Con `escribir=True` guarda la fila
    `pendiente de verificar` (o `vacia` con su motivo), abre la duda de proyecto `plano:<id>:p<N>:zona_planta` y audita.
    Nunca pisa una zona `confirmado`; es idempotente (si nada cambió no escribe ni audita).
    """
    usuario = usuario or usuario_auditoria()
    conn = get_connection()
    try:
        plano = _plano_vigente(conn, proyecto_id)
        fila = _fila(conn, plano["id"], pagina)
    finally:
        conn.close()
    with _abrir_hoja(plano, pagina) as doc:
        prop = calcular_propuesta(doc[pagina - 1])
    if fila is not None and fila["estado"] == "confirmado":
        r = _vista(fila, prop["ejes_rect"], plano["id"], pagina)
        r["escrito"] = False
        r["nota"] = "La zona ya está confirmada: no se pisa."
        return r
    if not escribir:
        return {"plano_id": plano["id"], "pagina": pagina, "estado": prop["estado"], "rect": prop["rect"],
                "origen": "propuesta_ejes", "fuente": prop["fuente"], "motivo": prop["motivo"],
                "ejes_rect": prop["ejes_rect"], "escrito": False}
    rect_json = _json(prop["rect"]) if prop["rect"] else None
    fuente_json = _json(prop["fuente"]) if prop["fuente"] else None
    if fila is not None and (fila["estado"], fila["rect_json"], fila["fuente_json"], fila["motivo"], fila["origen"]) == (
            prop["estado"], rect_json, fuente_json, prop["motivo"], "propuesta_ejes"):
        r = _vista(fila, prop["ejes_rect"], plano["id"], pagina)
        r["escrito"] = False
        return r
    campo = _campo_duda(plano["id"], pagina)
    if prop["estado"] == "vacia":
        texto = (f"No se pudo proponer la zona de planta de la hoja {pagina}: {prop['motivo']} Dibuja la zona en el visor "
                 f"({PENDIENTE}).")
    else:
        texto = (f"Confirma o ajusta la zona de planta propuesta para la hoja {pagina} {prop['rect']} (envolvente de los "
                 f"ejes y del dibujo conectado, con margen de {MARGEN_PT:.0f} pt). LOCALIZACION sale solo de esta zona.")
    conn = get_connection()
    try:
        _asegurar_tabla(conn)
        _transaccion(conn)
        try:
            ahora = _ahora()
            if fila is None:
                conn.execute("""INSERT INTO zonas_planta (proyecto_id, plano_id, pagina, rect_json, estado, origen, fuente_json,
                                motivo, actualizado_por, actualizado) VALUES (?, ?, ?, ?, ?, 'propuesta_ejes', ?, ?, ?, ?)""",
                             (proyecto_id, plano["id"], pagina, rect_json, prop["estado"], fuente_json, prop["motivo"],
                              usuario, ahora))
            else:
                conn.execute("""UPDATE zonas_planta SET rect_json = ?, estado = ?, origen = 'propuesta_ejes', fuente_json = ?,
                                motivo = ?, actualizado_por = ?, actualizado = ? WHERE plano_id = ? AND pagina = ?""",
                             (rect_json, prop["estado"], fuente_json, prop["motivo"], usuario, ahora, plano["id"], pagina))
            duda_id = _abrir_duda(conn, proyecto_id, campo, texto)
            _auditar(conn, usuario, "PROPONER_ZONA", f"{proyecto_id}:{plano['id']}:p{pagina}",
                     {"proyecto_id": proyecto_id, "plano_id": plano["id"], "pagina": pagina, "estado": prop["estado"],
                      "rect": prop["rect"], "motivo": prop["motivo"], "duda_id": duda_id,
                      "anterior": None if fila is None else {"estado": fila["estado"], "rect": fila["rect_json"]}})
            conn.execute("COMMIT")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        fila = _fila(conn, plano["id"], pagina)
    finally:
        conn.close()
    r = _vista(fila, prop["ejes_rect"], plano["id"], pagina)
    r["escrito"] = True
    r["duda_id"] = duda_id
    return r


def guardar_zona(proyecto_id: str, pagina: int, rect: List[float], usuario: Optional[str] = None) -> Dict:
    """
    Confirma la zona de la hoja. Origen `propuesta_ejes` si el rect es el propuesto, `manual` si cambió. Regla anti-zoom
    (error 1): si la hoja tiene ejes detectados, la zona debe contenerlos todos (400); sin ejes detectables se acepta
    y se audita. Cierra la duda de proyecto de la zona.
    """
    from visor import _validar_rect  # import tardío: visor importa este módulo
    usuario = usuario or usuario_auditoria()
    conn = get_connection()
    try:
        plano = _plano_vigente(conn, proyecto_id)
        fila = _fila(conn, plano["id"], pagina)
    finally:
        conn.close()
    rect = _validar_rect(plano, pagina, rect)
    with _abrir_hoja(plano, pagina) as doc:
        ejes = detectar_rotulos_ejes(doc[pagina - 1])
    sin_ejes = ejes["ejes_rect"] is None
    if not sin_ejes and not contiene(rect, ejes["ejes_rect"]):
        raise ErrorObra("la zona corta la planta (zoom parcial, error 1): debe contener todos los ejes "
                        f"{ejes['ejes_rect']} de la hoja {pagina}.", 400)
    origen = "manual"
    if fila is not None and fila["origen"] == "propuesta_ejes" and fila["rect_json"] \
            and all(abs(a - b) < 0.01 for a, b in zip(json.loads(fila["rect_json"]), rect)):
        origen = "propuesta_ejes"
    fuente = json.loads(fila["fuente_json"]) if fila is not None and fila["fuente_json"] else None
    if origen == "manual":
        fuente = {"metodo": "manual", "ejes_rect": ejes["ejes_rect"],
                  "nota": "sin ejes detectables en la hoja: zona aceptada sin la comprobación anti-zoom" if sin_ejes else None}
    conn = get_connection()
    try:
        _asegurar_tabla(conn)
        _transaccion(conn)
        try:
            ahora = _ahora()
            if fila is None:
                conn.execute("""INSERT INTO zonas_planta (proyecto_id, plano_id, pagina, rect_json, estado, origen, fuente_json,
                                motivo, actualizado_por, actualizado) VALUES (?, ?, ?, ?, 'confirmado', ?, ?, NULL, ?, ?)""",
                             (proyecto_id, plano["id"], pagina, _json(rect), origen, _json(fuente), usuario, ahora))
            else:
                conn.execute("""UPDATE zonas_planta SET rect_json = ?, estado = 'confirmado', origen = ?, fuente_json = ?,
                                motivo = NULL, actualizado_por = ?, actualizado = ? WHERE plano_id = ? AND pagina = ?""",
                             (_json(rect), origen, _json(fuente), usuario, ahora, plano["id"], pagina))
            duda = _duda_abierta(conn, proyecto_id, _campo_duda(plano["id"], pagina))
            if duda:
                conn.execute("""UPDATE dudas_y_hallazgos SET resuelta = 1, respuesta_usuario = ?, resuelto_en = ? WHERE id = ?""",
                             (f"Zona confirmada: {rect}", ahora, duda["id"]))
            _auditar(conn, usuario, "CONFIRMAR_ZONA", f"{proyecto_id}:{plano['id']}:p{pagina}",
                     {"proyecto_id": proyecto_id, "plano_id": plano["id"], "pagina": pagina, "rect": rect, "origen": origen,
                      "ejes_rect": ejes["ejes_rect"], "sin_ejes_detectables": sin_ejes,
                      "anterior": None if fila is None else {"estado": fila["estado"], "rect": fila["rect_json"]},
                      "duda_cerrada": duda["id"] if duda else None})
            conn.execute("COMMIT")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        fila = _fila(conn, plano["id"], pagina)
    finally:
        conn.close()
    return _vista(fila, ejes["ejes_rect"], plano["id"], pagina)


def zona_confirmada(conn, plano_id: int, pagina: int) -> Optional[List[float]]:
    """Rect (pt) de la zona confirmada de la hoja, o None. Lo usa el procesador."""
    fila = _fila(conn, plano_id, pagina)
    if fila is None or fila["estado"] != "confirmado" or not fila["rect_json"]:
        return None
    return json.loads(fila["rect_json"])
