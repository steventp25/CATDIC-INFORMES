# BACKEND/plano/recuadros_propuestos.py
# Etapa 7 · T8 — Recuadros PROPUESTOS de DETALLE (desde la `zona` de las propuesta.json de la lectura asistida) y de
# LOCALIZACION (con visor._proponer_localizacion sobre la planta del nivel).
#
# Reglas (Regla de Oro #1, M3 y M4):
# - Todo recuadro se guarda como PROPUESTO (estado "pendiente de verificar", el mismo que usa el visor para una
#   propuesta). NUNCA se escribe "confirmado": eso solo lo hace Steven en el visor (visor.guardar_recuadro).
# - Un recuadro ya confirmado (o con cualquier estado distinto de nuestra propia propuesta) no se pisa.
# - La `zona` es [x0, y0, x1, y1] en PUNTOS del marco visual de la hoja (contrato de la Fase A, §4 del contrato
#   asistido): es el mismo marco que guarda el visor (`rect` en pt), así que se copia sin convertir. La zona la estimó
#   una IA mirando la imagen: por eso queda pendiente y con su cita (archivo, página). Si no es una caja válida dentro
#   de la hoja, o la propuesta es de otro PDF (sha256), no se propone y se anota el motivo.
# - LOCALIZACION solo se propone si el nivel_rango del elemento coincide, texto a texto, con el rótulo de la planta
#   ("PLANTA ESTRUCTURAL DE SOTANO S2" ~ "SOTANO S - 2", comparando solo letras y números), o si quien llama pasa una
#   equivalencia explícita (`equivalencias`). Sin eso no se adivina qué rango de un elemento corresponde a la planta.
# - Hay respaldo de la BD antes de escribir y cada recuadro escrito queda en `auditoria`.
#
# Para el Líder de la Fase A (enganche al importador, una línea en la rama claude/etapa5-fase-a-3da668): al terminar
# `importar.importar_hoja(...)`, llamar `recuadros_propuestos.proponer_desde_propuestas(proyecto_id, [ruta_propuesta_json],
# paginas_planta=[...])`; este módulo no toca el importador.
import json
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

import pymupdf

import config
import equivalencias_nivel
import visor
from plano import lector_plano
from database import _respaldar_bd, get_connection
from obras import _ahora, _auditar, _transaccion, _usuario
from reglas_ingenieria import PENDIENTE

CONFIRMADO = "confirmado"
ORIGEN_ZONA = "propuesta_ia_zona"
ORIGEN_PLANTA = "propuesta_programa_planta"
COLUMNAS = {"detalle": "recorte_detalle_json", "localizacion": "recorte_planta_json"}
_RE_PLANTA = re.compile(r"^PLANTA ESTRUCTURAL DE\s+(.+)$", re.IGNORECASE)
_RE_NIVEL_EN_ROTULO = re.compile(r"(?:^|\s)(S-?\d+)$")   # 'SOTANO S2' -> S2


def _norm(texto) -> str:
    """Solo letras y números en mayúscula: 'SOTANO S - 2' == 'SOTANO S2'."""
    return re.sub(r"[^A-Z0-9]", "", str(texto or "").upper())


def _valor(dato):
    """Un dato de propuesta.json puede ser texto o {"valor": ..., "citas": [...]}."""
    return dato.get("valor") if isinstance(dato, dict) else dato


def _zona_valida(zona, ancho: float, alto: float):
    """(zona_en_pt | None, motivo). Cuatro números finitos, x0<x1, y0<y1, dentro de la hoja y de lado >= LADO_MINIMO_PT."""
    if zona is None:
        return None, "el elemento no trae 'zona'"
    if (not isinstance(zona, (list, tuple)) or len(zona) != 4
            or not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in zona)):
        return None, f"la 'zona' {zona!r} no son 4 números"
    x0, y0, x1, y1 = [float(v) for v in zona]
    if not (0 <= x0 < x1 <= ancho and 0 <= y0 < y1 <= alto):
        return None, f"la 'zona' {list(zona)} no es una caja válida dentro de la hoja ({ancho:.0f} x {alto:.0f} pt)"
    if min(x1 - x0, y1 - y0) < visor.LADO_MINIMO_PT:
        return None, f"la 'zona' {list(zona)} es demasiado pequeña (menos de {visor.LADO_MINIMO_PT:.0f} pt de lado)"
    return [round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)], None


def _rutas_propuestas(fuentes: Union[str, Path, Iterable]) -> List[Path]:
    """Carpeta del lote (busca pNN/propuesta.json) o lista de rutas a propuesta.json."""
    if isinstance(fuentes, (str, Path)):
        fuentes = [fuentes]
    rutas: List[Path] = []
    for f in fuentes:
        f = Path(f)
        if f.is_dir():
            rutas += sorted(f.glob("p*/propuesta.json"))
        else:
            rutas.append(f)
    return rutas


def _titulo_de_planta(doc, pagina: int):
    """(clave del nivel | None, motivo). El título impreso dentro de la hoja: 'PLANTA ESTRUCTURAL DE <NIVEL>'."""
    if not 1 <= pagina <= len(doc):
        return None, f"la página {pagina} no existe en el vectorial ({len(doc)} páginas)"
    titulos = []
    for linea in doc[pagina - 1].get_text("text").splitlines():
        m = _RE_PLANTA.match(" ".join(linea.split()))
        if m:
            titulos.append(m.group(1))
    if len(titulos) != 1:
        return None, f"la página {pagina} trae {len(titulos)} títulos 'PLANTA ESTRUCTURAL DE …' (se necesita uno)"
    return titulos[0], None


def _fila_de_diseno(conn, proyecto_id: str, plano_id: int, id_elemento: str, nivel_rango: str):
    return conn.execute("""SELECT * FROM elementos_diseno WHERE proyecto_id = ? AND plano_id = ? AND id_elemento = ?
                           AND nivel_rango = ?""", (proyecto_id, plano_id, id_elemento, nivel_rango)).fetchall()


def _protegido(actual: Dict) -> Optional[str]:
    """Motivo si el recuadro actual NO se puede reemplazar: solo se renueva uno vacío o una propuesta nuestra anterior."""
    if not actual:
        return None
    if actual.get("estado") == CONFIRMADO:
        return "ya hay un recuadro CONFIRMADO: no se pisa"
    if actual.get("estado") == PENDIENTE and actual.get("origen") in (ORIGEN_ZONA, ORIGEN_PLANTA):
        return None
    if actual.get("rect"):
        return "ya hay un recuadro que no es una propuesta de este paso: no se pisa"
    return None


def _ejes_de_visita(conn, proyecto_id: str, id_elemento: str, rotulo_planta: str):
    """
    EJES (no pendientes, cruce puntual) de los elementos de visita de la obra con ese ID y el nivel de la planta.
    Devuelve (ejes | None, cita | None, motivo). Solo sirve si hay exactamente un EJES distinto; si no, no se elige.
    """
    m = _RE_NIVEL_EN_ROTULO.search(equivalencias_nivel.normalizar_nivel(rotulo_planta))
    if not m:
        return None, None, "no se pudo sacar el nivel del rótulo de la planta"
    nivel = equivalencias_nivel.clave_nivel_visita(m.group(1))
    filas = conn.execute("""SELECT ev.visita_id, ev.orden_en_log, ev.nivel, ev.ejes FROM elementos_visita ev
                            JOIN visitas v ON v.id = ev.visita_id WHERE v.proyecto_id = ? AND ev.id_elemento = ?
                            ORDER BY ev.visita_id, ev.orden_en_log""", (proyecto_id, id_elemento)).fetchall()
    validas = [f for f in filas if equivalencias_nivel.clave_nivel_visita(f["nivel"]) == nivel
               and visor._RE_EJE_PUNTUAL.match(f["ejes"] or "")]
    distintos = sorted({f["ejes"] for f in validas})
    if len(distintos) != 1:
        return None, None, ("no hay un elemento de visita con ese ID, nivel y EJES válidos" if not distintos
                            else f"la visita trae EJES distintos ({', '.join(distintos)}): no se elige uno")
    f = validas[0]
    return distintos[0], f"ejes de la visita {f['visita_id']} p{f['orden_en_log']:03d}", ""


def proponer_desde_propuestas(proyecto_id: str, fuentes, paginas_planta: Optional[List[int]] = None,
                              equivalencias: Optional[Dict[str, List[str]]] = None, escribir: bool = True,
                              usuario: Optional[str] = None) -> Dict:
    """
    Propone (nunca confirma) los recuadros de los elementos de diseño importados desde las propuesta.json.
    - `fuentes`: carpeta del lote (pNN/propuesta.json) o lista de rutas a propuesta.json.
    - `paginas_planta`: páginas (desde 1) del vectorial que son plantas; su rótulo impreso decide el nivel.
    - `equivalencias`: {rótulo de la planta: [nivel_rango, ...]} dado por Steven. Si es None se leen de la tabla
      `equivalencias_nivel` de la obra (T6); pasar {} las desactiva.
    - `escribir=False`: en seco; devuelve lo que se escribiría sin tocar la BD.
    Devuelve {"propuestos": [...], "no_propuestos": [{id, nivel_rango, recuadro, motivo}], "respaldo": ruta | None}.
    """
    usuario = usuario or _usuario()
    desde_tabla = equivalencias is None   # sin equivalencias dadas, se leen de la tabla equivalencias_nivel (T6)
    equivalencias = {_norm(k): {_norm(r) for r in v} for k, v in (equivalencias or {}).items()}
    propuestos: List[Dict] = []
    no_propuestos: List[Dict] = []

    def no(id_, nivel, recuadro, motivo, archivo=None):
        no_propuestos.append({"id_elemento": id_, "nivel_rango": nivel, "recuadro": recuadro, "motivo": motivo,
                              **({"archivo": archivo} if archivo else {})})

    conn = get_connection()
    try:
        plano = visor._plano_vigente(conn, proyecto_id)
        plano_id = plano["id"]
        with pymupdf.Document(plano["vectorial_ruta"]) as doc:
            # ---- DETALLE desde la zona ----
            elementos_hallados: List[Dict] = []   # filas de diseño localizadas (para la LOCALIZACION)
            vistos = set()
            for ruta in _rutas_propuestas(fuentes):
                try:
                    prop = json.loads(ruta.read_text(encoding="utf-8"))
                    pagina = int(prop["pagina"])
                    elementos = list(prop["elementos"])
                except (OSError, ValueError, KeyError, TypeError):
                    no(None, None, "detalle", "propuesta.json ilegible o sin 'pagina'/'elementos'", str(ruta))
                    continue
                if prop.get("sha256") != plano["vectorial_sha256"]:
                    for e in elementos:
                        no(_valor(e.get("id_elemento")), _valor(e.get("nivel_rango")), "detalle",
                           "la propuesta es de otro PDF (sha256 distinto al del vectorial vigente): no se propone", str(ruta))
                    continue
                if not 1 <= pagina <= len(doc):
                    for e in elementos:
                        no(_valor(e.get("id_elemento")), _valor(e.get("nivel_rango")), "detalle",
                           f"la página {pagina} no existe en el vectorial", str(ruta))
                    continue
                hoja = doc[pagina - 1].rect   # marco visual, en pt
                for e in elementos:
                    id_, nivel = _valor(e.get("id_elemento")), _valor(e.get("nivel_rango"))
                    filas = _fila_de_diseno(conn, proyecto_id, plano_id, id_, nivel) if id_ and nivel else []
                    if len(filas) != 1:
                        no(id_, nivel, "detalle", "no hay un elemento de diseño con ese ID + nivel_rango en el plano vigente"
                           if not filas else f"hay {len(filas)} elementos de diseño con ese ID + nivel_rango: no se adivina",
                           str(ruta))
                        continue
                    fila = filas[0]
                    if fila["uid"] not in vistos:
                        vistos.add(fila["uid"])
                        elementos_hallados.append(dict(fila))
                    rect, motivo = _zona_valida(e.get("zona"), hoja.width, hoja.height)
                    if rect is None:
                        no(id_, nivel, "detalle", motivo, str(ruta))
                        continue
                    propuestos.append({
                        "uid": fila["uid"], "id_elemento": id_, "nivel_rango": nivel, "recuadro": "detalle",
                        "valor": {"plano_id": plano_id, "pagina": pagina, "rect": rect, "estado": PENDIENTE,
                                  "origen": ORIGEN_ZONA,
                                  "fuente": {"metodo": "zona_de_propuesta", "archivo": ruta.name, "carpeta": ruta.parent.name,
                                             "pagina": pagina, "hoja": prop.get("hoja"), "lector": prop.get("lector"),
                                             "zona": e.get("zona"),
                                             "nota": "zona estimada por la IA al mirar la imagen; confírmala en el visor"},
                                  "propuesto_en": _ahora()}})

            # ---- LOCALIZACION desde la planta ----
            plantas = []   # (pagina, hoja, rótulo, clave)
            if paginas_planta:
                visor.indice_del_plano(proyecto_id)
                with visor._candado_indice:
                    indice = visor._indices[plano_id]
                for pg in paginas_planta:
                    titulo, motivo = _titulo_de_planta(doc, pg)
                    h = next((x for x in indice if x["pagina"] == pg), None)
                    if titulo is None or h is None:
                        for f in elementos_hallados:
                            no(f["id_elemento"], f["nivel_rango"], "localizacion", motivo or f"la página {pg} no está en el índice")
                        continue
                    plantas.append((pg, h["hoja"], titulo, _norm(titulo)))
                    if desde_tabla:   # rótulo -> nivel de la visita ('SOTANO S2' -> 'S-2') -> rangos de la tabla
                        m = _RE_NIVEL_EN_ROTULO.search(equivalencias_nivel.normalizar_nivel(titulo))
                        if m:
                            nivel = equivalencias_nivel.clave_nivel_visita(m.group(1))
                            equivalencias[_norm(titulo)] = {_norm(r) for r in
                                                            equivalencias_nivel.equivalencias_de(conn, proyecto_id, nivel)}
            for f in elementos_hallados:
                if not plantas:
                    no(f["id_elemento"], f["nivel_rango"], "localizacion", "no se indicó la planta del nivel (paginas_planta)")
                    continue
                n = _norm(f["nivel_rango"])
                candidatas = [p for p in plantas if n == p[3] or n in equivalencias.get(p[3], ())]
                if len(candidatas) != 1:
                    rotulos = ", ".join(p[2] for p in plantas)
                    no(f["id_elemento"], f["nivel_rango"], "localizacion",
                       f"falta equivalencia: el nivel_rango no coincide con el rótulo de la planta ({rotulos}) y no hay equivalencia dada por Steven: "
                       "no se sabe qué rango corresponde a esa planta" if not candidatas else
                       "el nivel_rango coincide con varias plantas: no se adivina")
                    continue
                pg, hoja_nn, rotulo, _ = candidatas[0]
                elemento = {**f, "hoja_plano_origen": hoja_nn}   # copia: el diseño no se modifica
                cita_ejes, motivo_ejes = None, ""
                veces = sum(1 for i in lector_plano.ids_en_planta(doc, pg) if i["texto"] == f["id_elemento"])
                if veces != 1 and not visor._RE_EJE_PUNTUAL.match(f["ejes"] or ""):
                    # ID repetido en la planta y EJES pendientes en el diseño: se usan los EJES de la visita (D11) si son únicos
                    ejes, cita_ejes, motivo_ejes = _ejes_de_visita(conn, proyecto_id, f["id_elemento"], rotulo)
                    if ejes:
                        elemento["ejes"] = ejes
                prop_loc = visor._proponer_localizacion(doc, plano["vectorial_archivo"], indice, elemento)
                if not prop_loc.get("rect"):
                    extra = f" Ejes de la visita: {motivo_ejes}." if motivo_ejes else ""
                    no(f["id_elemento"], f["nivel_rango"], "localizacion", (prop_loc.get("motivo") or "sin propuesta") + extra)
                    continue
                if cita_ejes:
                    prop_loc["fuente"] = {**prop_loc["fuente"], "ejes_de_visita": cita_ejes, "ejes": elemento["ejes"]}
                propuestos.append({
                    "uid": f["uid"], "id_elemento": f["id_elemento"], "nivel_rango": f["nivel_rango"], "recuadro": "localizacion",
                    "valor": {"plano_id": plano_id, "pagina": prop_loc["pagina"], "rect": prop_loc["rect"], "estado": PENDIENTE,
                              "origen": ORIGEN_PLANTA, "fuente": {**prop_loc["fuente"], "rotulo_planta": rotulo},
                              "propuesto_en": _ahora()}})

        # ---- Filtrar lo protegido y escribir ----
        a_escribir = []
        for p in propuestos:
            fila = conn.execute(f"SELECT {COLUMNAS[p['recuadro']]} AS actual FROM elementos_diseno WHERE uid = ?",
                                (p["uid"],)).fetchone()
            try:
                actual = json.loads(fila["actual"] or "{}")
            except ValueError:
                actual = {"rect": "ilegible"}
            motivo = _protegido(actual)
            if motivo:
                no(p["id_elemento"], p["nivel_rango"], p["recuadro"], motivo)
            else:
                a_escribir.append(p)
        respaldo = None
        if escribir and a_escribir:
            respaldo = str(_respaldar_bd(conn, Path(config.obtener_db_path())))
            _transaccion(conn)
            try:
                for p in a_escribir:
                    columna = COLUMNAS[p["recuadro"]]
                    anterior = conn.execute(f"SELECT {columna} AS v FROM elementos_diseno WHERE uid = ?", (p["uid"],)).fetchone()["v"]
                    conn.execute(f"UPDATE elementos_diseno SET {columna} = ?, actualizado = ? WHERE uid = ?",
                                 (json.dumps(p["valor"], ensure_ascii=False), _ahora(), p["uid"]))
                    _auditar(conn, "PROPONER_RECUADRO", p["uid"],
                             {"proyecto_id": proyecto_id, "recuadro": p["recuadro"], "estado": PENDIENTE,
                              "anterior": json.loads(anterior or "{}"), "nuevo": p["valor"]}, usuario)
                conn.execute("COMMIT")
            except Exception:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise
    finally:
        conn.close()
    return {"escrito": bool(escribir and a_escribir), "respaldo": respaldo,
            "propuestos": [{k: v for k, v in p.items() if k != "valor"} | {"pagina": p["valor"]["pagina"], "rect": p["valor"]["rect"]}
                           for p in a_escribir],
            "no_propuestos": no_propuestos}
