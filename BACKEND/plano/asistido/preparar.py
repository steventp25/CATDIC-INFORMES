# BACKEND/plano/asistido/preparar.py
# Etapa 5 · A2 — Paso 1 de la lectura asistida: preparar las hojas del plano vectorial.
# Por cada página escribe una imagen (hoja.png) y la lista numerada de textos visibles con su recuadro (textos.json).
# Solo lectura sobre el PDF (se comprueba con sha256 antes y después). Sin BD ni rutas web.
import argparse
import hashlib
import json
import sys
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


def _hojas_previas(destino: Path, sha: str) -> List[Dict]:
    """Hojas ya preparadas en el destino. Si son de otra versión del plano, error sin escribir nada."""
    ruta = destino / "manifiesto.json"
    if not ruta.exists():
        return []
    previo = json.loads(ruta.read_text(encoding="utf-8"))
    if previo.get("sha256") != sha:
        raise ValueError("El destino tiene hojas de otra versión del plano (sha256 distinto).")
    return list(previo.get("hojas", []))


def _txt(pagina: int, hoja: str, page, textos: List[Dict]) -> bytes:
    """
    textos.txt: cabecera '# pagina=.. hoja=.. rotacion=.. ancho_pt=.. alto_pt=..' y luego una línea por texto
    'n|texto|x0,y0,x1,y1|tam' (bbox en enteros). El texto puede contener '|': se lee de DERECHA a IZQUIERDA
    (los dos últimos campos y el primero son fijos; lo que queda en medio es el texto). textos.json es la referencia.
    """
    lineas = [f"# pagina={pagina} hoja={hoja} rotacion={page.rotation} "
              f"ancho_pt={round(page.rect.width, 1)} alto_pt={round(page.rect.height, 1)}"]
    for t in textos:
        texto = " ".join(t["texto"].replace("\r", "\n").split("\n"))
        bbox = ",".join(str(round(v)) for v in t["bbox"])
        lineas.append(f"{t['n']}|{texto}|{bbox}|{t['tam']}")
    return ("\n".join(lineas) + "\n").encode("utf-8")


def preparar_hojas(ruta_pdf: Path, destino: Path, paginas: Optional[List[int]] = None, ppp: int = 72) -> Dict:
    """Prepara las páginas indicadas (desde 1; None = todas). Devuelve el manifiesto."""
    ruta_pdf = Path(ruta_pdf)
    destino = _validar_destino(destino)
    sha = _sha256(ruta_pdf)
    nombre = ruta_pdf.name
    previas = _hojas_previas(destino, sha)
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
            _escribir(carpeta / "textos.txt", _txt(p, hoja, page, textos))
            hojas.append({"pagina": p, "hoja": hoja, "carpeta": f"p{p:02d}", "ppp": ppp, "textos": len(textos)})
    if _sha256(ruta_pdf) != sha:
        raise RuntimeError(f"El PDF '{nombre}' cambió mientras se leía; no debería ocurrir (se abre solo en lectura).")
    fusion = {h["pagina"]: h for h in previas}
    fusion.update({h["pagina"]: h for h in hojas})
    manifiesto = {"version": VERSION, "archivo": nombre, "sha256": sha, "paginas_total": total,
                  "hojas": [fusion[k] for k in sorted(fusion)]}
    _escribir(destino / "manifiesto.json", _json(manifiesto))
    return manifiesto


def recortar(ruta_pdf: Path, destino: Path, pagina: int, bbox, ppp: int = 150) -> Path:
    """
    Recorte de una zona de una página ya preparada. `bbox` en puntos, en el marco VISUAL (el de textos.json), se pasa
    tal cual a `clip` (sin derotation_matrix). Guarda pNN/zonas/<x0>_<y0>_<x1>_<y1>@<ppp>.png.
    """
    ruta_pdf = Path(ruta_pdf)
    destino = _validar_destino(destino)
    carpeta = destino / f"p{pagina:02d}"
    ficha = carpeta / "textos.json"
    if not ficha.exists():
        raise ValueError(f"La página {pagina} no está preparada en '{destino}'.")
    sha = _sha256(ruta_pdf)
    if json.loads(ficha.read_text(encoding="utf-8")).get("sha256") != sha:
        raise ValueError("El PDF no coincide con el que se preparó en ese destino (sha256 distinto).")
    with pymupdf.open(str(ruta_pdf)) as doc:
        if not isinstance(pagina, int) or pagina < 1 or pagina > doc.page_count:
            raise ValueError(f"Página {pagina} fuera de rango (el PDF tiene {doc.page_count}).")
        page = doc[pagina - 1]
        zona = pymupdf.Rect(*[float(v) for v in bbox]) & page.rect
        if zona.is_empty or zona.width <= 0 or zona.height <= 0:
            raise ValueError(f"El recorte {list(bbox)} queda vacío o fuera de la página.")
        nombre = "_".join(str(round(v)) for v in (zona.x0, zona.y0, zona.x1, zona.y1)) + f"@{ppp}.png"
        salida = carpeta / "zonas" / nombre
        salida.parent.mkdir(parents=True, exist_ok=True)
        page.get_pixmap(dpi=ppp, clip=zona).save(str(salida))
    if _sha256(ruta_pdf) != sha:
        raise RuntimeError("El PDF cambió mientras se leía; no debería ocurrir (se abre solo en lectura).")
    return salida


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m plano.asistido.preparar")
    sub = ap.add_subparsers(dest="orden", required=True)
    h = sub.add_parser("hojas")
    h.add_argument("pdf"), h.add_argument("destino")
    h.add_argument("--paginas", default=None, help="lista separada por comas, p. ej. 3,5")
    h.add_argument("--ppp", type=int, default=72)
    r = sub.add_parser("recorte")
    r.add_argument("pdf"), r.add_argument("destino"), r.add_argument("pagina", type=int)
    for c in ("x0", "y0", "x1", "y1"):
        r.add_argument(c, type=float)
    r.add_argument("--ppp", type=int, default=150)
    a = ap.parse_args(argv)
    try:
        if a.orden == "hojas":
            paginas = [int(x) for x in a.paginas.split(",") if x.strip()] if a.paginas else None
            man = preparar_hojas(Path(a.pdf), Path(a.destino), paginas, a.ppp)
            print(f"{man['archivo']}: {len(man['hojas'])} hoja(s) en el manifiesto de {a.destino}")
        else:
            print(recortar(Path(a.pdf), Path(a.destino), a.pagina, [a.x0, a.y0, a.x1, a.y1], a.ppp))
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
