# BACKEND/plano/asistido/preparar.py
# Etapa 5 · A2 — Paso 1 de la lectura asistida: preparar las hojas del plano vectorial.
# Por cada página escribe una imagen (hoja.png) y la lista numerada de textos visibles con su recuadro (textos.json).
# Solo lectura sobre el PDF (se comprueba con sha256 antes y después). Sin BD ni rutas web.
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional

import pymupdf

import config
from plano import lector_plano as lp
from reglas_ingenieria import PENDIENTE

VERSION = 1
_RAIZ_REPO = Path(__file__).resolve().parent.parent.parent.parent


def carpeta_lectura(proyecto_id: str) -> Path:
    return config.obtener_datos_raiz() / proyecto_id / "lectura-asistida"


def _sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _dentro(ruta: Path, raiz: Path) -> bool:
    return ruta == raiz or raiz in ruta.parents


def _validar_destino(destino: Path) -> Path:
    d = Path(destino).resolve()
    dropbox = config.obtener_dropbox_raiz().resolve()
    for raiz, nombre in ((dropbox, "Dropbox"), (_RAIZ_REPO.resolve(), "el repositorio")):
        if _dentro(d, raiz):
            raise ValueError(f"El destino '{d}' está dentro de {nombre}; las hojas preparadas se guardan fuera.")
    return d


def _json(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def _escribir(ruta: Path, datos: bytes) -> None:
    ruta.write_bytes(datos)


def preparar_hojas(ruta_pdf: Path, destino: Path, paginas: Optional[List[int]] = None, ppp: int = 100) -> Dict:
    """Prepara las páginas indicadas (desde 1; None = todas). Devuelve el manifiesto."""
    ruta_pdf = Path(ruta_pdf)
    destino = _validar_destino(destino)
    sha = _sha256(ruta_pdf)
    nombre = ruta_pdf.name
    hojas = []
    with pymupdf.open(str(ruta_pdf)) as doc:
        total = doc.page_count
        lista = list(range(1, total + 1)) if paginas is None else list(paginas)
        for p in lista:
            if not isinstance(p, int) or isinstance(p, bool) or p < 1 or p > total:
                raise ValueError(f"Página {p} fuera de rango (el PDF tiene {total}).")
        lista = sorted(set(lista))
        destino.mkdir(parents=True, exist_ok=True)
        for p in lista:
            page = doc[p - 1]
            hoja = lp._hoja_de(doc, p) or PENDIENTE
            lineas = sorted(lp._lineas(page), key=lambda l: (round(l["rect"].y0), l["rect"].x0))
            textos = [{"n": i, "texto": l["texto"], "bbox": lp._rect(l["rect"]), "tam": l["tam"]}
                      for i, l in enumerate(lineas, 1)]
            pix = page.get_pixmap(dpi=ppp)
            carpeta = destino / f"p{p:02d}"
            carpeta.mkdir(exist_ok=True)
            pix.save(str(carpeta / "hoja.png"))
            _escribir(carpeta / "textos.json", _json({
                "version": VERSION, "archivo": nombre, "sha256": sha, "pagina": p, "hoja": hoja,
                "rotacion": page.rotation, "ancho_pt": round(page.rect.width, 1), "alto_pt": round(page.rect.height, 1),
                "ppp": ppp, "imagen": "hoja.png", "ancho_px": pix.width, "alto_px": pix.height,
                "px_por_pt": round(ppp / 72, 4), "textos": textos}))
            hojas.append({"pagina": p, "hoja": hoja, "carpeta": f"p{p:02d}", "textos": len(textos)})
    if _sha256(ruta_pdf) != sha:
        raise RuntimeError(f"El PDF '{nombre}' cambió mientras se leía; no debería ocurrir (se abre solo en lectura).")
    manifiesto = {"version": VERSION, "archivo": nombre, "sha256": sha, "paginas_total": total, "ppp": ppp, "hojas": hojas}
    _escribir(destino / "manifiesto.json", _json(manifiesto))
    return manifiesto
