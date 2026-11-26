# backend/valores_proyecto.py
# Etapa 7 · T17 — Valores del proyecto CONFIRMADOS por Steven (con su cita), versionados en git junto al código.
# Son filas del STP que el plano no trae (altura de columna, solape, resistencia del muro...). Nada va como constante
# en el generador: el procesador los lee de `valores_proyecto_confirmados.json`. Archivo ausente, roto o con un valor
# incompleto: se ignora con aviso en el log y NUNCA llena nada (Regla de Oro #1).
#
# Forma de cada valor: {"proyecto_id", "fila_stp", "letra", "valor", "aplica_a": [tipos de elemento], "confirmado_por",
# "fecha", "cita", "origen"} y, opcionales:
#   "solo_si": {"campo": "id_elemento" | "tipo_elemento" | "nivel_rango" | "datos_diseno.<clave>", "contiene_palabra": "…"}
#       el valor aplica solo si ese dato del DISEÑO trae esa palabra completa (sin importar mayúsculas); nunca se deduce.
#   "solo_nivel_visita": "sotano"  (T20) el valor aplica solo si el NIVEL DE LA VISITA es un sótano (S-n, «SOTANO -n»);
#       nunca se deduce del rango impreso del plano (E-n).
#   "contraste_campos": ["altura_m"]  datos del diseño que, si traen un número legible en metros distinto del valor,
#       abren una duda en vez de llenar la fila.
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from equivalencias_nivel import clave_nivel_visita

RUTA_CONFIGURACION = Path(__file__).resolve().parent / "valores_proyecto_confirmados.json"
ARCHIVO = RUTA_CONFIGURACION.name
_CAMPOS_TEXTO = ("proyecto_id", "fila_stp", "letra", "valor", "confirmado_por", "fecha", "cita", "origen")
_CAMPOS_DISENO = ("id_elemento", "tipo_elemento", "nivel_rango")
NIVELES_VISITA = ("sotano",)
# Sótano escrito en la visita: lo que clave_nivel_visita ya da como S-n, o «SOTANO -n» / «SÓTANO S-n» (T20)
_RE_SOTANO_VISITA = re.compile(r"^(?:S-\d+|S[OÓ]TANO\s*-?\s*(?:S-?)?\d+)$")
log = logging.getLogger(__name__)


def cargar_valores(ruta: Optional[Path] = None) -> Tuple[List[Dict], List[str]]:
    """(valores válidos, avisos de lo ignorado). Nunca lanza: lo roto o incompleto se descarta."""
    ruta = Path(ruta or RUTA_CONFIGURACION)
    avisos: List[str] = []
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        avisos.append(f"Valores del proyecto ignorados: no se pudo leer {ruta.name} ({exc}).")
        log.warning(avisos[-1])
        return [], avisos
    crudos = datos.get("valores") if isinstance(datos, dict) else None
    if not isinstance(crudos, list):
        avisos.append(f"Valores del proyecto ignorados: {ruta.name} no trae la lista `valores`.")
        log.warning(avisos[-1])
        return [], avisos
    valores = []
    for i, v in enumerate(crudos, 1):
        if not _valido(v):
            avisos.append(f"Valor {i} de {ruta.name} ignorado: faltan datos o tiene otra forma.")
            log.warning(avisos[-1])
            continue
        valores.append(v)
    return valores, avisos


def _valido(v) -> bool:
    if not isinstance(v, dict) or not all(isinstance(v.get(c), str) and v[c].strip() for c in _CAMPOS_TEXTO):
        return False
    aplica = v.get("aplica_a")
    if not isinstance(aplica, list) or not aplica or not all(isinstance(t, str) and t.strip() for t in aplica):
        return False
    solo = v.get("solo_si")
    if solo is not None and not (isinstance(solo, dict) and isinstance(solo.get("contiene_palabra"), str)
                                 and solo["contiene_palabra"].strip() and isinstance(solo.get("campo"), str)
                                 and (solo["campo"] in _CAMPOS_DISENO or (
                                     solo["campo"].startswith("datos_diseno.") and len(solo["campo"]) > 13))):
        return False
    if v.get("solo_nivel_visita") is not None and v["solo_nivel_visita"] not in NIVELES_VISITA:
        return False
    contraste = v.get("contraste_campos")
    return contraste is None or (isinstance(contraste, list) and all(isinstance(c, str) and c for c in contraste))


def valores_de(proyecto_id: str, fila_stp: str, tipo_elemento: str, ruta: Optional[Path] = None) -> List[Dict]:
    """Valores confirmados de ese proyecto, fila del STP y tipo de elemento (sin evaluar `solo_si`)."""
    valores, _ = cargar_valores(ruta)
    return [v for v in valores if v["proyecto_id"] == proyecto_id and v["fila_stp"] == fila_stp
            and tipo_elemento in v["aplica_a"]]


def _palabra(texto, palabra: str) -> bool:
    patron = rf"(?<![A-Z0-9]){re.escape(palabra.strip().upper())}(?![A-Z0-9])"
    return isinstance(texto, str) and re.search(patron, texto.upper()) is not None


def cumple_marca(valor: Dict, elemento: Dict, datos: Dict) -> bool:
    """True si el valor no pide marca, o si el dato de DISEÑO que pide trae la palabra completa."""
    solo = valor.get("solo_si")
    if not solo:
        return True
    campo = solo["campo"]
    if campo.startswith("datos_diseno."):
        return _palabra(datos.get(campo[len("datos_diseno."):]), solo["contiene_palabra"])
    return _palabra(elemento[campo] if campo in elemento.keys() else None, solo["contiene_palabra"])


def origen_de(valor: Dict) -> Dict:
    """Lo que la ficha guarda de dónde salió la fila: archivo, valor, cita, quién lo confirmó, cuándo y su origen."""
    return {"archivo": ARCHIVO, "valor": valor["valor"], "cita": valor["cita"],
            "confirmado_por": valor["confirmado_por"], "fecha": valor["fecha"], "origen": valor["origen"]}


def es_sotano_visita(nivel) -> bool:
    """T20: True si el nivel escrito en la VISITA es un sótano (S-2, S2, «SOTANO -7», «SÓTANO S-3»)."""
    return isinstance(nivel, str) and _RE_SOTANO_VISITA.match(clave_nivel_visita(nivel)) is not None


def cumple_nivel(valor: Dict, nivel_visita) -> bool:
    """True si el valor no pide nivel, o si el nivel de la visita es el que pide (hoy solo «sotano»)."""
    return valor.get("solo_nivel_visita") != "sotano" or es_sotano_visita(nivel_visita)
