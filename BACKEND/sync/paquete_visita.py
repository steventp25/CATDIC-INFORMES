# BACKEND/sync/paquete_visita.py
# Importador del paquete de visita v1 de CATDIC Campo (PLANES/paquete-visita-v1.md).
#
# El técnico ya eligió en Campo el tipo, el ID y los ejes de cada elemento con casillas guiadas: aquí
# se cargan a `elementos_visita` sin leer el PDF ni interpretar texto libre. Regla de Oro #1: nada se
# completa por adivinanza. Los ejes se recalculan con formatear_campo_ejes (no se confía en el texto
# del paquete); lo que no valida queda "pendiente de verificar" con UNA duda por elemento.
# Dropbox es SOLO LECTURA: el paquete se lee y las fotos reducidas van a la caché local.
import base64
import binascii
import getpass
import io
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageOps, UnidentifiedImageError

import config
from database import get_connection, _respaldar_bd
from reglas_ingenieria import CATEGORIA_POR_TIPO, PENDIENTE, formatear_campo_ejes
from sync import lector_visita
from sync.parser_visitas import CAMPO_CLASE, CAMPO_FECHA, CLASE_COMPLETIVO, CLASE_PARCIAL

EXTENSION = ".catdic-visita.json"
FORMATO = "catdic-paquete-visita"
VERSION = 1
CAMPO_PAQUETE = "paquete_visita"
MODULO_AUDITORIA = "PAQUETE_VISITA"
ACCION_CARGAR = "CARGAR_PAQUETE"
ACCION_RECHAZAR = "RECHAZAR_PAQUETE"
RESPUESTA_PAQUETE = "dato del paquete de Campo"
RESPUESTA_LECTOR = "resuelta: la visita se cargó del paquete de Campo"
DUDA = lector_visita.DUDA

# Caso de ejes que corresponde a cada tipo de Campo (misma tabla que TIPOS_ELEMENTO en Campo).
CASO_POR_TIPO = {
    "COLUMNA": {"cruce_puntual"},
    "ZAPATA": {"cruce_puntual"},
    "MURO H.A.": {"muro_entre_letras"},
    "MURO DE CONTENCION": {"muro_entre_letras"},
    "VIGA": {"viga_recta_sobre_letra", "viga_sin_eje_letra"},
    "PORTICO": {"tramo_portico"},
    "LOSA": {"losa"},
    "PLATEA": {"area"},
}
_RE_ID = re.compile(r"[A-Z0-9][A-Z0-9'.\-]{0,11}")
_RE_FECHA = re.compile(r"\d{4}-\d{2}-\d{2}")


# ---------- Búsqueda y lectura (solo lectura) ----------

def buscar_paquete(carpeta: Path) -> Optional[Path]:
    """El paquete de la carpeta de la visita; None si no hay. Con más de uno no se elige: ValueError."""
    carpeta = Path(carpeta)
    if not carpeta.is_dir():
        return None
    paquetes = sorted(p for p in carpeta.iterdir() if p.is_file() and p.name.lower().endswith(EXTENSION))
    if len(paquetes) > 1:
        raise ValueError(f"La carpeta de la visita tiene {len(paquetes)} paquetes de Campo "
                         f"({', '.join(p.name for p in paquetes)}): indica cuál cargar; no se elige uno solo.")
    return paquetes[0] if paquetes else None


def _texto(valor) -> str:
    return valor.strip() if isinstance(valor, str) else ""


def leer_paquete(ruta: Path) -> Dict:
    """Abre y valida la estructura. Un paquete que no es v1 o viene incompleto lanza ValueError (no carga nada)."""
    try:
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f"El paquete '{Path(ruta).name}' no se puede leer como JSON: {e}") from e
    if not isinstance(datos, dict) or datos.get("formato") != FORMATO:
        raise ValueError(f"'{Path(ruta).name}' no es un paquete de visita de CATDIC Campo.")
    if datos.get("version") != VERSION:
        raise ValueError(f"El paquete '{Path(ruta).name}' es de la versión {datos.get('version')!r}; "
                         f"este programa solo carga la versión {VERSION}.")
    elementos = datos.get("elementos")
    if not isinstance(elementos, list) or not elementos:
        raise ValueError(f"El paquete '{Path(ruta).name}' no trae elementos.")
    numeros = []
    for i, el in enumerate(elementos, 1):
        fotos = el.get("fotos") if isinstance(el, dict) else None
        if not isinstance(fotos, list) or not fotos:
            raise ValueError(f"El elemento {i} del paquete no trae fotos.")
        for f in fotos:
            n = f.get("numero") if isinstance(f, dict) else None
            if not isinstance(n, int) or isinstance(n, bool) or n < 1 or not isinstance(f.get("base64"), str):
                raise ValueError(f"El elemento {i} del paquete trae una foto sin número o sin imagen.")
            numeros.append(n)
    if len(numeros) != len(set(numeros)):
        raise ValueError("El paquete repite números de foto: no se sabe el orden del log.")
    if any(el["fotos"][0]["numero"] >= sig["fotos"][0]["numero"] for el, sig in zip(elementos, elementos[1:])):
        raise ValueError("Los elementos del paquete no vienen en el orden de sus fotos.")
    return datos


# ---------- Identidad sin adivinar ----------

def _nivel(valor: str) -> str:
    return " ".join(_texto(valor).upper().split())


def identidad_de_elemento(el: Dict, nivel_carpeta: str, nivel_visita: str) -> Dict:
    """
    tipo, id, ejes y nivel del elemento, cada uno validado por separado. Lo que no valida queda
    PENDIENTE y su motivo va en `faltas` (texto de la duda).
    """
    faltas: List[str] = []
    tipo = _texto(el.get("tipo")).upper()
    if tipo not in CATEGORIA_POR_TIPO:
        faltas.append("el tipo" if not tipo else f"el tipo ('{tipo}' no es un tipo que el programa conozca)")
        tipo_ok = PENDIENTE
    else:
        tipo_ok = tipo

    ident = _texto(el.get("id")).upper()
    id_ok = ident if _RE_ID.fullmatch(ident) else PENDIENTE
    if id_ok == PENDIENTE:
        faltas.append("el ID" if not ident else f"el ID ('{ident}' no se reconoce)")

    ejes = el.get("ejes") if isinstance(el.get("ejes"), dict) else {}
    caso = _texto(ejes.get("caso"))
    if tipo_ok == PENDIENTE:
        ejes_ok = PENDIENTE
        faltas.append("los ejes (dependen del tipo)")
    elif caso not in CASO_POR_TIPO.get(tipo_ok, set()):
        ejes_ok = PENDIENTE
        faltas.append(f"los ejes (el tipo {tipo_ok} no tiene un formato de ejes definido)" if tipo_ok not in CASO_POR_TIPO
                      else "los ejes (el caso no corresponde al tipo)")
    else:
        def casilla(clave):  # misma normalización aprobada para la visita (§4.4): prima ’ -> ' y mayúsculas
            return _texto(ejes.get(clave)).replace("’", "'").upper() or None
        ejes_ok = formatear_campo_ejes(caso, eje_letra_1=casilla("letra_1"), eje_letra_2=casilla("letra_2"),
                                       eje_num_1=casilla("num_1"), eje_num_2=casilla("num_2"))
        if ejes_ok == PENDIENTE:
            faltas.append("los ejes (las casillas están vacías o no forman un eje válido)")

    nivel_paquete = _nivel(el.get("nivel")) or _nivel(nivel_visita)
    if nivel_carpeta != PENDIENTE:
        nivel_ok = nivel_carpeta
        if nivel_paquete and nivel_paquete != nivel_carpeta:
            nivel_ok = PENDIENTE
            faltas.append(f"el nivel (la carpeta dice {nivel_carpeta} y el paquete {nivel_paquete})")
    elif nivel_paquete:
        nivel_ok = nivel_paquete
    else:
        nivel_ok = PENDIENTE
        faltas.append("el nivel")

    return {"tipo_elemento": tipo_ok, "id_elemento": id_ok, "ejes": ejes_ok, "nivel": nivel_ok, "faltas": faltas,
            "reconocido": not faltas}


def etiqueta_del_elemento(el: Dict) -> str:
    """Lo que el técnico declaró, literal (para mostrarlo y auditarlo; no se reinterpreta)."""
    libre = _texto(el.get("texto_libre"))
    if libre:
        return libre
    partes = [_texto(el.get("tipo")).upper(), _texto(el.get("id")).upper()]
    ejes = _texto(el.get("ejes_texto"))
    if ejes and ejes != PENDIENTE:
        partes.append(ejes)
    return " ".join(p for p in partes if p)


def _nota(el: Dict) -> str:
    partes = []
    if _texto(el.get("mediciones")):
        partes.append(f"Medidas en obra: {_texto(el.get('mediciones'))}")
    if _texto(el.get("descripcion")):
        partes.append(_texto(el.get("descripcion")))
    return " · ".join(partes)


def _texto_duda(el: Dict, ident: Dict) -> str:
    fotos = el["fotos"]
    primera, ultima = fotos[0]["numero"], fotos[-1]["numero"]
    cuales = f"foto {primera}" if primera == ultima else f"fotos {primera} a {ultima}"
    etiqueta = etiqueta_del_elemento(el)
    titulo = f" ('{etiqueta}')" if etiqueta else ""
    return (f"Paquete de Campo, elemento {el.get('orden', '?')}{titulo}, {cuales}: falta o no valida "
            f"{', '.join(ident['faltas'])}. Indica el dato correcto; no se completa por adivinanza.")


# ---------- Fotos ----------

def _guardar_foto(base64_txt: str, destino: Path) -> None:
    """Decodifica la foto, la endereza y la reduce (máx. 1000×1000, JPG q72, §5.2)."""
    try:
        crudo = base64.b64decode(base64_txt, validate=True)
        img = Image.open(io.BytesIO(crudo))
        img.load()
    except (binascii.Error, ValueError, UnidentifiedImageError, OSError) as e:
        raise ValueError(f"Una foto del paquete no es una imagen válida ({destino.stem}): {e}") from e
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((lector_visita.LADO_MAXIMO_PX, lector_visita.LADO_MAXIMO_PX), Image.LANCZOS)
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino, format="JPEG", quality=lector_visita.CALIDAD_JPG)


# ---------- Fecha y clase de la visita ----------

def _fecha_valida(valor: str) -> Optional[str]:
    if not _RE_FECHA.fullmatch(valor):
        return None
    try:
        datetime.strptime(valor, "%Y-%m-%d")
    except ValueError:
        return None
    return valor


def _ahora() -> str:
    return datetime.now().isoformat()


def _json(valor) -> str:
    return json.dumps(valor, ensure_ascii=False)


def _auditar(conn, usuario: str, accion: str, entidad: str, detalle: Dict) -> None:
    conn.execute("""INSERT INTO auditoria (fecha_hora, usuario, modulo, accion, entidad_id, detalle_json)
                    VALUES (?, ?, ?, ?, ?, ?)""", (_ahora(), usuario, MODULO_AUDITORIA, accion, entidad, _json(detalle)))


def _aplicar_fecha_clase(conn, visita, paquete: Dict, usuario: str) -> Dict:
    """Llena fecha/clase pendientes con el dato del paquete; ante un valor distinto abre una duda y no cambia nada."""
    datos = paquete.get("visita") if isinstance(paquete.get("visita"), dict) else {}
    candidatos = {
        CAMPO_FECHA: ("fecha_visita", _fecha_valida(_texto(datos.get("fecha"))), "la fecha"),
        CAMPO_CLASE: ("clase", _texto(datos.get("clase")).capitalize() or None, "la clase"),
    }
    if candidatos[CAMPO_CLASE][1] not in (CLASE_PARCIAL, CLASE_COMPLETIVO):
        candidatos[CAMPO_CLASE] = ("clase", None, "la clase")
    llenados, conflictos, dudas_cerradas = {}, [], []
    for campo, (columna, valor, nombre) in candidatos.items():
        actual = visita[columna]
        if valor is None or actual == valor:
            continue
        if actual != PENDIENTE:
            if lector_visita._insertar_duda(conn, visita, "(visita)", f"{CAMPO_PAQUETE}:{columna}",
                                            f"El paquete de Campo dice que {nombre} de la visita es '{valor}', pero la "
                                            f"carpeta dice '{actual}'. ¿Cuál es la correcta? No se cambia sola."):
                conflictos.append(columna)
            continue
        conn.execute(f"UPDATE visitas SET {columna} = ?, actualizado = ? WHERE id = ?", (valor, _ahora(), visita["id"]))
        llenados[columna] = valor
        for (duda_id,) in conn.execute("""SELECT id FROM dudas_y_hallazgos WHERE visita_id = ? AND campo_afectado = ?
                                           AND categoria = ? AND resuelta = 0""", (visita["id"], campo, DUDA)).fetchall():
            conn.execute("UPDATE dudas_y_hallazgos SET resuelta = 1, respuesta_usuario = ?, resuelto_en = ? WHERE id = ?",
                         (RESPUESTA_PAQUETE, _ahora(), duda_id))
            _auditar(conn, usuario, "CERRAR_DUDA", str(duda_id), {"visita_id": visita["id"], "campo": campo,
                                                                   "valor": valor, "motivo": RESPUESTA_PAQUETE})
            dudas_cerradas.append(duda_id)
    return {"llenados": llenados, "conflictos": conflictos, "dudas_cerradas": dudas_cerradas}


def _cerrar_duda_lector(conn, visita, usuario: str) -> List[int]:
    """
    Pierden su causa: la duda 'no hay un único PDF / el PDF no se lee' (la visita se cargó del paquete) y la de
    un paquete rechazado antes (el de ahora sí carga).
    """
    ids = [f[0] for f in conn.execute("""SELECT id FROM dudas_y_hallazgos WHERE visita_id = ? AND campo_afectado IN (?, ?)
                                          AND categoria = ? AND resuelta = 0""",
                                       (visita["id"], lector_visita.CAMPO_PDF_VISITA, CAMPO_PAQUETE, DUDA))]
    for i in ids:
        conn.execute("UPDATE dudas_y_hallazgos SET resuelta = 1, respuesta_usuario = ?, resuelto_en = ? WHERE id = ?",
                     (RESPUESTA_LECTOR, _ahora(), i))
        _auditar(conn, usuario, "CERRAR_DUDA", str(i), {"visita_id": visita["id"], "motivo": RESPUESTA_LECTOR})
    return ids


# ---------- Carga ----------

def rechazar(visita_id: str, motivo: str, ruta: Optional[Path] = None, usuario: Optional[str] = None) -> None:
    """Paquete inválido o ambiguo: una duda de visita (campo paquete_visita) y auditoría; no se carga nada."""
    usuario = usuario or getpass.getuser()
    conn = get_connection()
    conn.isolation_level = None
    try:
        visita = conn.execute("SELECT * FROM visitas WHERE id = ?", (visita_id,)).fetchone()
        if visita is None:
            raise LookupError(f"No existe la visita '{visita_id}'.")
        conn.execute("BEGIN")
        if not lector_visita._insertar_duda(conn, visita, "(visita)", CAMPO_PAQUETE, motivo):
            conn.execute("""UPDATE dudas_y_hallazgos SET resuelta = 0, respuesta_usuario = '', resuelto_en = '',
                            descripcion_pregunta = ? WHERE visita_id = ? AND campo_afectado = ? AND categoria = ?""",
                         (motivo, visita_id, CAMPO_PAQUETE, DUDA))
        lector_visita._marcar_con_dudas(conn, visita)
        _auditar(conn, usuario, ACCION_RECHAZAR, visita_id, {"paquete": str(ruta) if ruta else None, "motivo": motivo})
        conn.execute("COMMIT")
    finally:
        conn.close()


def cargar_paquete(visita_id: str, ruta_paquete: Path, usuario: Optional[str] = None, respaldar: bool = True) -> Dict:
    """
    Carga el paquete a `elementos_visita`. Idempotente por (visita_id, orden_en_log), como el lector del PDF.
    Un paquete inválido no carga nada: deja su duda (campo paquete_visita) y lanza ValueError.
    """
    usuario = usuario or getpass.getuser()
    cache_raiz = lector_visita._validar_cache(lector_visita.obtener_cache_raiz())
    ruta_paquete = Path(ruta_paquete)
    try:
        paquete = leer_paquete(ruta_paquete)
    except ValueError as e:
        rechazar(visita_id, str(e), ruta_paquete, usuario)
        raise

    conn = get_connection()
    conn.isolation_level = None
    try:
        visita = conn.execute("SELECT * FROM visitas WHERE id = ?", (visita_id,)).fetchone()
        if visita is None:
            raise LookupError(f"No existe la visita '{visita_id}'.")
        datos_visita = paquete.get("visita") if isinstance(paquete.get("visita"), dict) else {}
        nivel_carpeta = lector_visita.nivel_de_carpeta(visita["nombre_carpeta"])
        elementos = [(el, identidad_de_elemento(el, nivel_carpeta, datos_visita.get("nivel"))) for el in paquete["elementos"]]

        carpeta_cache = cache_raiz / visita["proyecto_id"] / visita["id"]
        try:  # primero la caché (sin tocar la BD); una foto dañada rechaza el paquete entero
            for el, _ in elementos:
                for f in el["fotos"]:
                    destino = carpeta_cache / f"p{f['numero']:03d}.jpg"
                    if not destino.exists():
                        _guardar_foto(f["base64"], destino)
        except ValueError as e:
            conn.close()
            rechazar(visita_id, str(e), ruta_paquete, usuario)
            raise

        respaldo = _respaldar_bd(conn, Path(config.obtener_db_path())) if respaldar else None
        nuevas = actualizadas = sin_cambios = dudas_nuevas = 0
        conn.execute("BEGIN")
        try:
            for el, ident in elementos:
                orden = el["fotos"][0]["numero"]
                nota = _nota(el)
                fotos_json = _json([{
                    "foto": f["numero"], "etiqueta": etiqueta_del_elemento(el) if i == 0 else "",
                    "nota": nota if i == 0 else "", "hora": _texto(f.get("hora")),
                    "cache": f"{visita['proyecto_id']}/{visita['id']}/p{f['numero']:03d}.jpg",
                    **({"mediciones": _texto(el.get("mediciones"))} if i == 0 and _texto(el.get("mediciones")) else {}),
                } for i, f in enumerate(el["fotos"])])
                valores = (etiqueta_del_elemento(el), ident["id_elemento"], ident["tipo_elemento"], ident["nivel"],
                           ident["ejes"], fotos_json)
                fila = conn.execute("""SELECT etiqueta_original, id_elemento, tipo_elemento, nivel, ejes, fotos_json
                                       FROM elementos_visita WHERE visita_id = ? AND orden_en_log = ?""",
                                    (visita_id, orden)).fetchone()
                if fila is None:
                    conn.execute("""INSERT INTO elementos_visita (uid, visita_id, orden_en_log, etiqueta_original,
                                    id_elemento, tipo_elemento, nivel, ejes, fotos_json)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                 (f"{visita_id}-{orden:03d}", visita_id, orden, *valores))
                    nuevas += 1
                elif tuple(fila) != valores:
                    conn.execute("""UPDATE elementos_visita SET etiqueta_original = ?, id_elemento = ?, tipo_elemento = ?,
                                    nivel = ?, ejes = ?, fotos_json = ? WHERE visita_id = ? AND orden_en_log = ?""",
                                 (*valores, visita_id, orden))
                    actualizadas += 1
                else:
                    sin_cambios += 1
                if not ident["reconocido"]:
                    if lector_visita._insertar_duda(conn, visita, etiqueta_del_elemento(el) or "(sin datos)",
                                                    f"elemento_visita:p{orden:03d}", _texto_duda(el, ident)):
                        dudas_nuevas += 1
            fecha_clase = _aplicar_fecha_clase(conn, visita, paquete, usuario)
            dudas_lector = _cerrar_duda_lector(conn, visita, usuario)
            estado_anterior = visita["estado"]
            visita = conn.execute("SELECT * FROM visitas WHERE id = ?", (visita_id,)).fetchone()
            estado_nuevo = lector_visita._marcar_con_dudas(conn, visita)
            detalle = {"paquete": str(ruta_paquete), "generado_por": _texto(paquete.get("generado_por")),
                       "elementos": len(elementos), "fotos": sum(len(el["fotos"]) for el, _ in elementos),
                       "reconocidos": sum(1 for _, i in elementos if i["reconocido"]),
                       "filas_nuevas": nuevas, "filas_actualizadas": actualizadas, "sin_cambios": sin_cambios,
                       "dudas_nuevas": dudas_nuevas, "fecha_clase": fecha_clase, "dudas_lector_cerradas": dudas_lector,
                       "estado_anterior": estado_anterior, "estado_nuevo": estado_nuevo or visita["estado"],
                       "cache": str(carpeta_cache), "respaldo": respaldo.name if respaldo else None}
            _auditar(conn, usuario, ACCION_CARGAR, visita_id, detalle)
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        return {**detalle, "elementos_detalle": [
            {"orden_en_log": el["fotos"][0]["numero"], "etiqueta_original": etiqueta_del_elemento(el),
             "fotos": len(el["fotos"]), "tipo_elemento": i["tipo_elemento"], "id_elemento": i["id_elemento"],
             "ejes": i["ejes"], "nivel": i["nivel"]} for el, i in elementos]}
    finally:
        conn.close()
