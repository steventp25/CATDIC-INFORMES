# BACKEND/plano/asistido/esquema.py
# Etapa 5 · A3a — Esquema de propuesta.json y regla de anclaje (contrato §4 y §5).
# Módulo puro: sin BD y sin escribir archivos. Nada se infiere: lo que no cumple queda sin valor y con una duda `IA:`.
from typing import Dict, List, Optional

import reglas_ingenieria as ri

VERSION = 1
CLAVES_PROPUESTA = {"version": int, "archivo": str, "sha256": str, "pagina": int, "hoja": str,
                    "lector": str, "skill": str, "elementos": list}
DATOS_FIJOS = ("id_elemento", "nivel_rango", "ejes")


class PropuestaInvalida(ValueError):
    """La propuesta está mal formada: la hoja entera no se carga."""


def _raise(msg: str):
    raise PropuestaInvalida(msg)


def _int(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def textos_por_n(textos: Dict) -> Dict[int, Dict]:
    """textos.json → {n: {"texto", "bbox", ...}}."""
    return {t["n"]: t for t in textos.get("textos", [])}


def _citas(citas, donde: str, existentes) -> List[int]:
    if not isinstance(citas, list) or not all(_int(c) for c in citas):
        raise PropuestaInvalida(f"{donde}: 'citas' debe ser una lista de enteros.")
    for c in citas:
        if c not in existentes:
            raise PropuestaInvalida(f"{donde}: la cita {c} no existe en textos.json.")
    return list(citas)


def _dato(dato, donde: str, existentes) -> Dict:
    if not isinstance(dato, dict) or "valor" not in dato:
        raise PropuestaInvalida(f"{donde}: falta 'valor'.")
    valor = dato["valor"]
    if valor is None:
        duda = dato.get("duda")
        if not isinstance(duda, str) or not duda.strip():
            raise PropuestaInvalida(f"{donde}: 'valor' es null y falta 'duda'.")
        return {"valor": None, "citas": _citas(dato.get("citas", []), donde, existentes), "duda": duda}
    if not isinstance(valor, str) or not valor.strip():
        raise PropuestaInvalida(f"{donde}: 'valor' debe ser una cadena o null.")
    if not dato.get("citas"):
        raise PropuestaInvalida(f"{donde}: tiene valor pero no 'citas'.")
    out = {"valor": valor, "citas": _citas(dato["citas"], donde, existentes)}
    if isinstance(dato.get("duda"), str):
        out["duda"] = dato["duda"]
    return out


def _tipo_conocido(tipo: str) -> bool:
    """Los tipos que conoce validador_diseno (los mismos de reglas_ingenieria.CATEGORIA_POR_TIPO)."""
    try:
        ri.obtener_categoria_elemento(tipo)
        return True
    except ValueError:
        return False


def _nota(n, donde: str, existentes) -> Dict:
    if isinstance(n, str):
        return {"texto": n, "citas": []}
    if not isinstance(n, dict) or not isinstance(n.get("texto"), str):
        raise PropuestaInvalida(f"{donde}: debe traer 'texto'.")
    return {**n, "citas": _citas(n.get("citas", []), donde, existentes)}


def _objeto_con_citas(o, donde: str, existentes) -> Dict:
    if not isinstance(o, dict):
        raise PropuestaInvalida(f"{donde}: debe ser un objeto.")
    return {**o, "citas": _citas(o.get("citas", []), donde, existentes)}


def validar_propuesta(propuesta: Dict, textos: Dict) -> Dict:
    """Valida contra §4 y contra el textos.json de la hoja. Devuelve la propuesta normalizada (citas = list[int])."""
    if not isinstance(propuesta, dict):
        raise PropuestaInvalida("La propuesta debe ser un objeto.")
    for clave, tipo in CLAVES_PROPUESTA.items():
        if clave not in propuesta:
            raise PropuestaInvalida(f"Falta la clave '{clave}'.")
        v = propuesta[clave]
        if not isinstance(v, tipo) or (tipo is int and isinstance(v, bool)):
            raise PropuestaInvalida(f"La clave '{clave}' tiene un tipo equivocado.")
    if propuesta["version"] != VERSION:
        raise PropuestaInvalida(f"version {propuesta['version']} no soportada (se espera {VERSION}).")
    if propuesta["sha256"] != textos.get("sha256"):
        raise PropuestaInvalida("El sha256 de la propuesta no es el de textos.json.")
    if propuesta["pagina"] != textos.get("pagina"):
        raise PropuestaInvalida("La página de la propuesta no es la de textos.json.")
    existentes = textos_por_n(textos)
    out = dict(propuesta)
    out["elementos"] = []
    for i, el in enumerate(propuesta["elementos"]):
        d = f"elementos[{i}]"
        if not isinstance(el, dict):
            raise PropuestaInvalida(f"{d}: debe ser un objeto.")
        tipo = el.get("tipo_elemento")
        if not isinstance(tipo, str) or not _tipo_conocido(tipo):
            raise PropuestaInvalida(f"{d}: tipo_elemento {tipo!r} no es un tipo conocido.")
        zona = el.get("zona")
        if not isinstance(zona, list) or len(zona) != 4 or not all(
                isinstance(z, (int, float)) and not isinstance(z, bool) for z in zona):
            raise PropuestaInvalida(f"{d}: 'zona' debe ser 4 números.")
        nuevo = {**el, "zona": list(zona)}
        for k in DATOS_FIJOS:
            if k not in el:
                raise PropuestaInvalida(f"{d}: falta '{k}'.")
            nuevo[k] = _dato(el[k], f"{d}.{k}", existentes)
        campos = el.get("campos")
        if not isinstance(campos, dict):
            raise PropuestaInvalida(f"{d}: 'campos' debe ser un objeto.")
        nuevo["campos"] = {c: _dato(v, f"{d}.campos.{c}", existentes) for c, v in campos.items()}
        enlaces, dudas = el.get("enlaces", []), el.get("dudas", [])
        if not isinstance(enlaces, list) or not isinstance(dudas, list):
            raise PropuestaInvalida(f"{d}: 'enlaces' y 'dudas' deben ser listas.")
        nuevo["enlaces"] = [_objeto_con_citas(e, f"{d}.enlaces[{j}]", existentes) for j, e in enumerate(enlaces)]
        nuevo["dudas"] = [_nota(n, f"{d}.dudas[{j}]", existentes) for j, n in enumerate(dudas)]
        out["elementos"].append(nuevo)
    dudas_hoja, comps = propuesta.get("dudas_hoja", []), propuesta.get("comprobaciones", [])
    if not isinstance(dudas_hoja, list) or not isinstance(comps, list):
        raise PropuestaInvalida("'dudas_hoja' y 'comprobaciones' deben ser listas.")
    out["dudas_hoja"] = [_nota(n, f"dudas_hoja[{j}]", existentes) for j, n in enumerate(dudas_hoja)]
    out["comprobaciones"] = [_objeto_con_citas(c, f"comprobaciones[{j}]", existentes) for j, c in enumerate(comps)]
    return out


# ---------- Anclaje (contrato §5) ----------

def _norm(s: str) -> str:
    return " ".join(s.replace("Ø", "∅").split())


def _pegajoso(c: str) -> bool:
    """Letra, dígito o el símbolo ∅ (que va pegado a la cantidad y al diámetro)."""
    return c.isalnum() or c == "∅"


def _limites_ok(union: str, i: int, j: int) -> bool:
    v_ini, v_fin = union[i], union[j - 1]
    antes = union[i - 1] if i > 0 else ""
    despues = union[j] if j < len(union) else ""
    if antes and (_pegajoso(antes) or (antes == "." and v_ini.isdigit())):
        return False
    if not despues:
        return True
    if despues in "Mm" and v_fin.isdigit():  # sufijo de unidad: H=0.25M
        resto = union[j + 1:j + 2]
        return resto == "" or not _pegajoso(resto)
    if _pegajoso(despues):
        return False
    return not (despues == "." and v_fin.isdigit() and union[j + 1:j + 2].isdigit())


def anclar(valor: str, citados: List[str]) -> bool:
    """¿Aparece `valor` tal cual dentro de la unión de los textos citados, con límites válidos?"""
    v = _norm(valor or "")
    union = _norm(" ".join(citados))
    if not v:
        return False
    i = union.find(v)
    while i != -1:
        if _limites_ok(union, i, i + len(v)):
            return True
        i = union.find(v, i + 1)
    return False


def _union_bbox(bboxes: List[List[float]]) -> Optional[List[float]]:
    if not bboxes:
        return None
    return [min(b[0] for b in bboxes), min(b[1] for b in bboxes),
            max(b[2] for b in bboxes), max(b[3] for b in bboxes)]


def revisar_dato(dato: Dict, textos_por_n: Dict[int, Dict]) -> Dict:
    """→ {"valor", "fuente", "duda"}: valor anclado con su fuente, o sin valor y con la duda `IA:` que corresponda."""
    if dato.get("valor") is None:
        return {"valor": None, "fuente": None, "duda": dato.get("duda")}
    valor = dato["valor"]
    citas = list(dato.get("citas", []))
    textos = [textos_por_n[c]["texto"] for c in citas if c in textos_por_n]
    if citas and len(textos) == len(citas) and anclar(valor, textos):
        return {"valor": _norm(valor),
                "fuente": {"citas": citas, "textos": textos,
                           "bbox": _union_bbox([textos_por_n[c]["bbox"] for c in citas])},
                "duda": None}
    union = _norm(" ".join(textos))
    return {"valor": None, "fuente": None, "duda": f"IA: propuso '{valor}' pero el texto citado dice '{union}'"}
