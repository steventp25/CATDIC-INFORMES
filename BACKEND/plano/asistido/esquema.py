# BACKEND/plano/asistido/esquema.py
# Etapa 5 · A3a — Esquema de propuesta.json y regla de anclaje (contrato §4 y §5).
# Módulo puro: sin BD y sin escribir archivos. Nada se infiere: lo que no cumple queda sin valor y con una duda `IA:`.
import re
from decimal import Decimal
from typing import Callable, Dict, List, Optional

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


EVIDENCIAS = ("literal", "partes", "zona", "conversion")


def _numeros4(z) -> bool:
    return isinstance(z, list) and len(z) == 4 and all(
        isinstance(x, (int, float)) and not isinstance(x, bool) for x in z)


def _con_citas(o, donde: str, existentes) -> Dict:
    """{"valor": str, "citas": [n…]} con valor no vacío y al menos una cita que exista."""
    if not isinstance(o, dict) or not isinstance(o.get("valor"), str) or not o["valor"].strip():
        raise PropuestaInvalida(f"{donde}: debe traer 'valor' (cadena).")
    if not o.get("citas"):
        raise PropuestaInvalida(f"{donde}: falta 'citas'.")
    return {"valor": o["valor"], "citas": _citas(o["citas"], donde, existentes)}


def _dato(dato, donde: str, existentes, fijo: bool = False) -> Dict:
    """Un dato con su evidencia (§5.1). `fijo`: id_elemento, nivel_rango y ejes (solo literal o partes)."""
    if not isinstance(dato, dict):
        raise PropuestaInvalida(f"{donde}: debe ser un objeto.")
    evidencia = dato.get("evidencia", "literal")
    valor = dato.get("valor")
    if evidencia not in EVIDENCIAS:  # contrato §5.1: desconocida → hoja rechazada, también con valor null
        raise PropuestaInvalida(f"{donde}: evidencia {evidencia!r} desconocida.")
    if valor is None and isinstance(dato.get("duda"), str) and dato["duda"].strip():
        # valor null + duda: igual que siempre, con cualquiera de las evidencias conocidas
        return {"valor": None, "citas": _citas(dato.get("citas", []), donde, existentes), "duda": dato["duda"],
                "evidencia": "literal"}
    if fijo and (evidencia in ("zona", "conversion") or "zona" in dato or "conversion" in dato):
        raise PropuestaInvalida(f"{donde}: la identidad del elemento solo admite 'literal' o 'partes'.")
    if evidencia == "conversion" and valor is None and "conversion" in dato:
        pass  # el valor lo calcula el programa
    elif "valor" not in dato:
        raise PropuestaInvalida(f"{donde}: falta 'valor'.")
    elif valor is None:
        raise PropuestaInvalida(f"{donde}: 'valor' es null y falta 'duda'.")
    elif not isinstance(valor, str) or not valor.strip():
        raise PropuestaInvalida(f"{donde}: 'valor' debe ser una cadena o null.")
    out = {"valor": valor, "evidencia": evidencia, "citas": []}
    if isinstance(dato.get("duda"), str):
        out["duda"] = dato["duda"]
    if evidencia == "literal":
        if not dato.get("citas"):
            raise PropuestaInvalida(f"{donde}: tiene valor pero no 'citas'.")
        out["citas"] = _citas(dato["citas"], donde, existentes)
    elif evidencia == "partes":
        partes = dato.get("partes")
        if not isinstance(partes, list) or len(partes) < 2:
            raise PropuestaInvalida(f"{donde}: 'partes' debe ser una lista de 2 o más.")
        out["partes"] = [_con_citas(p, f"{donde}.partes[{k}]", existentes) for k, p in enumerate(partes)]
        out["citas"] = _citas(dato.get("citas", []), donde, existentes)
    elif evidencia == "zona":
        if not _numeros4(dato.get("zona")):
            raise PropuestaInvalida(f"{donde}: 'zona' debe ser 4 números.")
        out["zona"] = list(dato["zona"])
        out["citas"] = _citas(dato.get("citas", []), donde, existentes)
    else:
        conv = dato.get("conversion")
        if not isinstance(conv, dict) or not isinstance(conv.get("regla"), str):
            raise PropuestaInvalida(f"{donde}: 'conversion.regla' debe ser una cadena.")
        entradas = conv.get("entradas")
        if not isinstance(entradas, list) or not entradas:
            raise PropuestaInvalida(f"{donde}: 'conversion.entradas' debe ser una lista no vacía.")
        out["conversion"] = {"regla": conv["regla"],
                             "entradas": [_con_citas(e, f"{donde}.conversion.entradas[{k}]", existentes)
                                          for k, e in enumerate(entradas)]}
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
            nuevo[k] = _dato(el[k], f"{d}.{k}", existentes, fijo=True)
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

def _colapsar(s: str) -> str:
    return " ".join(s.split())


def _norm(s: str) -> str:
    return _colapsar(s).replace("Ø", "∅")


def _pegajoso(c: str) -> bool:
    """Letra, dígito o el símbolo ∅ (que va pegado a la cantidad y al diámetro)."""
    return c.isalnum() or c == "∅"


def _limites_ok(union: str, i: int, j: int) -> bool:
    v_ini, v_fin = union[i], union[j - 1]
    antes = union[i - 1] if i > 0 else ""
    despues = union[j] if j < len(union) else ""
    # Un '-' o un '.' con letra o dígito a los dos lados (E-3, 0.25, A-B) deja el valor pegado al otro trozo.
    if antes:
        if _pegajoso(antes):
            return False
        if antes in ".-" and i > 1 and _pegajoso(union[i - 2]) and _pegajoso(v_ini):
            return False
    if not despues:
        return True
    if despues in "Mm" and v_fin.isdigit():  # sufijo de unidad: H=0.25M
        resto = union[j + 1:j + 2]
        return resto == "" or not _pegajoso(resto)
    if _pegajoso(despues):
        return False
    return not (despues in ".-" and _pegajoso(v_fin) and _pegajoso(union[j + 1:j + 2] or " "))


def encontrar(valor: str, citados: List[str]) -> Optional[str]:
    """El trozo LITERAL del plano (espacios colapsados, sin cambiar Ø/∅) donde `valor` se ancla, o None."""
    v = _norm(valor or "")
    union = _colapsar(" ".join(citados))
    comparable = union.replace("Ø", "∅")  # mismo largo: los índices coinciden
    if not v:
        return None
    i = comparable.find(v)
    while i != -1:
        if _limites_ok(comparable, i, i + len(v)):
            return union[i:i + len(v)]
        i = comparable.find(v, i + 1)
    return None


def anclar(valor: str, citados: List[str]) -> bool:
    """¿Aparece `valor` tal cual dentro de la unión de los textos citados, con límites válidos?"""
    return encontrar(valor, citados) is not None


def _union_bbox(bboxes: List[List[float]]) -> Optional[List[float]]:
    if not bboxes:
        return None
    return [min(b[0] for b in bboxes), min(b[1] for b in bboxes),
            max(b[2] for b in bboxes), max(b[3] for b in bboxes)]


# ---------- Reglas de conversión (§5.1): las únicas; aritmética decimal exacta, sin redondeo ----------

def _decimal(texto: str, patron: str, que: str) -> Decimal:
    t = texto.strip()
    if not re.fullmatch(patron, t):
        raise ValueError(f"'{texto}' no es {que}")
    return Decimal(t)


def _decimales(d: Decimal) -> int:
    return max(0, -d.as_tuple().exponent)


def decimales_2(entradas: List[str]) -> str:
    if len(entradas) != 1:
        raise ValueError("decimales_2 lleva exactamente 1 entrada")
    d = _decimal(entradas[0], r"\d+(\.\d{1,2})?", "un decimal con punto y hasta 2 decimales")
    return f"{d:.2f}"


def cm_a_m(entradas: List[str]) -> str:
    if len(entradas) != 1:
        raise ValueError("cm_a_m lleva exactamente 1 entrada")
    m = re.fullmatch(r"(\d+)(?:cm)?", entradas[0].strip(), re.IGNORECASE)
    if not m:
        raise ValueError(f"'{entradas[0]}' no es un entero de centímetros (con o sin 'cm')")
    return f"{Decimal(m.group(1)) / 100:.2f}"


def suma(entradas: List[str]) -> str:
    if len(entradas) < 2:
        raise ValueError("suma lleva 2 o más entradas")
    ds = [_decimal(e, r"\d+(\.\d+)?", "un decimal con punto") for e in entradas]
    return f"{sum(ds, Decimal(0)):.{max(_decimales(d) for d in ds)}f}"


REGLAS_CONVERSION: Dict[str, Callable[[List[str]], str]] = {
    "decimales_2": decimales_2, "cm_a_m": cm_a_m, "suma": suma}


# ---------- Revisión de un dato ----------

def _sin_valor(duda: str, evidencia: str) -> Dict:
    # `literal` no lleva la clave (conducta de A3a/A3b intacta); quien la lea usa .get("evidencia", "literal")
    r = {"valor": None, "fuente": None, "duda": duda}
    if evidencia != "literal":
        r["evidencia"] = evidencia
    return r


def _anclar_con_citas(valor: str, citas: List[int], por_n: Dict[int, Dict]):
    """→ (literal | None, textos citados, bbox unida)."""
    textos = [por_n[c]["texto"] for c in citas if c in por_n]
    literal = encontrar(valor, textos) if citas and len(textos) == len(citas) else None
    bbox = _union_bbox([por_n[c]["bbox"] for c in citas if c in por_n])
    return literal, textos, bbox


def _revisar_literal(dato: Dict, por_n: Dict[int, Dict]) -> Dict:
    valor = dato["valor"]
    citas = list(dato.get("citas", []))
    literal, textos, bbox = _anclar_con_citas(valor, citas, por_n)
    if literal is not None:  # el valor lo pone el plano, no Claude
        return {"valor": literal, "fuente": {"citas": citas, "textos": textos, "bbox": bbox}, "duda": None}
    union = _colapsar(" ".join(textos))
    return _sin_valor(f"IA: propuso '{valor}' pero el texto citado dice '{union}'", "literal")


def _anclar_trozos(trozos: List[Dict], por_n: Dict[int, Dict], que: str):
    """Ancla cada {"valor","citas"}. → (lista de trozos anclados, None) o (None, duda)."""
    out = []
    for k, t in enumerate(trozos):
        literal, textos, bbox = _anclar_con_citas(t["valor"], t["citas"], por_n)
        if literal is None:
            union = _colapsar(" ".join(textos))
            return None, f"IA: {que} {k + 1}: propuso '{t['valor']}' pero el texto citado dice '{union}'"
        out.append({"literal": literal, "citas": list(t["citas"]), "textos": textos, "bbox": bbox})
    return out, None


def _citas_de(trozos: List[Dict]) -> List[int]:
    return [c for t in trozos for c in t["citas"]]


def _revisar_partes(dato: Dict, por_n: Dict[int, Dict]) -> Dict:
    partes, duda = _anclar_trozos(dato["partes"], por_n, "parte")
    if duda:
        return _sin_valor(duda, "partes")
    unido = " ".join(p["literal"] for p in partes)
    if _norm(dato["valor"]) != _norm(unido):
        return _sin_valor(f"IA: propuso '{_colapsar(dato['valor'])}' pero las partes citadas dicen '{unido}'", "partes")
    return {"valor": unido, "duda": None, "evidencia": "partes",
            "fuente": {"evidencia": "partes", "citas": _citas_de(partes),
                       "textos": [t for p in partes for t in p["textos"]],
                       "partes": [{"valor": p["literal"], "citas": p["citas"], "textos": p["textos"], "bbox": p["bbox"]}
                                  for p in partes],
                       "bbox": _union_bbox([p["bbox"] for p in partes if p["bbox"]])}}


def _revisar_zona(dato: Dict, hoja: Optional[Dict]) -> Dict:
    zona = list(dato["zona"])
    ancho, alto = (hoja or {}).get("ancho_pt"), (hoja or {}).get("alto_pt")
    if not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in (ancho, alto)):
        return _sin_valor(f"IA: la zona {zona} no se puede comprobar: faltan ancho_pt y alto_pt de la hoja.", "zona")
    x0, y0, x1, y1 = zona
    if not (x0 < x1 and y0 < y1 and x0 >= 0 and y0 >= 0 and x1 <= ancho and y1 <= alto):
        return _sin_valor(f"IA: la zona {zona} no es una caja válida dentro de la hoja ({ancho} x {alto} pt).", "zona")
    lectura = _colapsar(dato["valor"])
    return {"valor": lectura, "evidencia": "zona",
            "fuente": {"evidencia": "zona", "zona": zona, "lectura": lectura, "citas": list(dato.get("citas", []))},
            "duda": f"IA: revisión visual: la IA leyó '{lectura}' en la zona {zona}; no hay texto vectorial que lo "
                    f"compruebe. Confírmalo mirando el recorte."}


def _revisar_conversion(dato: Dict, por_n: Dict[int, Dict]) -> Dict:
    conv = dato["conversion"]
    regla = REGLAS_CONVERSION.get(conv["regla"])
    if regla is None:
        return _sin_valor(f"IA: la regla de conversión '{conv['regla']}' no existe.", "conversion")
    entradas, duda = _anclar_trozos(conv["entradas"], por_n, "entrada")
    if duda:
        return _sin_valor(duda, "conversion")
    literales = [e["literal"] for e in entradas]
    try:
        resultado = regla(literales)
    except ValueError as err:
        return _sin_valor(f"IA: la regla '{conv['regla']}' falla con {literales}: {err}", "conversion")
    propuesto = dato.get("valor")
    if propuesto is not None and _colapsar(propuesto) != resultado:
        return _sin_valor(f"IA: propuso '{_colapsar(propuesto)}' pero la regla '{conv['regla']}' da '{resultado}'",
                          "conversion")
    return {"valor": resultado, "duda": None, "evidencia": "conversion",
            "fuente": {"evidencia": "conversion", "regla": conv["regla"], "citas": _citas_de(entradas),
                       "entradas": entradas, "bbox": _union_bbox([e["bbox"] for e in entradas if e["bbox"]])}}


def revisar_dato(dato: Dict, textos_por_n: Dict[int, Dict], hoja: Optional[Dict] = None) -> Dict:
    """
    → {"valor", "fuente", "duda"} (+ "evidencia" si no es `literal`): valor anclado con su fuente, o sin valor y con la duda `IA:` que
    corresponda. `hoja` es el textos.json completo (solo la zona lo necesita: ancho_pt y alto_pt). Con la evidencia
    `zona` hay valor Y duda a la vez (revisión visual).
    """
    evidencia = dato.get("evidencia", "literal")
    if dato.get("valor") is None and (evidencia != "conversion" or dato.get("duda")):
        return {"valor": None, "fuente": None, "duda": dato.get("duda")}
    if evidencia == "partes":
        return _revisar_partes(dato, textos_por_n)
    if evidencia == "zona":
        return _revisar_zona(dato, hoja)
    if evidencia == "conversion":
        return _revisar_conversion(dato, textos_por_n)
    return _revisar_literal(dato, textos_por_n)
