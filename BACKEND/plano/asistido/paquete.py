# BACKEND/plano/asistido/paquete.py
# Etapa 5 · A4-paquete (v4, decisión 9) — Paquete de lectura para la IA de cualquier compañero, no solo Claude Code.
# Por lote de hojas arma una carpeta plana lista para subir a un chat: hoja.png y textos.txt de cada hoja, recortes en
# cuadrícula a 150 ppp e INSTRUCCIONES.md autocontenido. Solo lectura sobre el PDF; nada va a la BD ni al repositorio.
import argparse
import json
import math
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from plano.asistido import preparar as pr

PLANTILLA = Path(__file__).with_name("instrucciones_lote.md")
LADO_PT = 800     # lado máximo de cada recorte: a 150 ppp son ~1670 px, lo que una IA de chat lee sin reducir mucho
SOLAPE_PT = 40    # para que un rótulo partido entre dos recortes salga entero en uno de ellos
PPP_RECORTE = 150


def cuadricula(ancho: float, alto: float, lado: float = LADO_PT, solape: float = SOLAPE_PT) -> List[List[float]]:
    """Cajas (marco visual, pt) que cubren toda la hoja con recortes de lado <= `lado` (+ solape), fila a fila."""
    cols, filas = max(1, math.ceil(ancho / lado)), max(1, math.ceil(alto / lado))
    paso_x, paso_y = ancho / cols, alto / filas
    cajas = []
    for f in range(filas):
        for c in range(cols):
            cajas.append([round(max(0.0, c * paso_x - solape), 1), round(max(0.0, f * paso_y - solape), 1),
                          round(min(ancho, (c + 1) * paso_x + solape), 1), round(min(alto, (f + 1) * paso_y + solape), 1)])
    return cajas


def _tabla_hojas(filas: List[Dict]) -> str:
    out = ["| Página | Hoja | Archivos a subir | Guardar en | Cabecera de la propuesta |", "|---|---|---|---|---|"]
    for f in filas:
        archivos = ", ".join(f"`{a}`" for a in f["archivos"])
        cab = (f'`"archivo": {json.dumps(f["archivo"], ensure_ascii=False)}, "sha256": "{f["sha256"]}", '
               f'"pagina": {f["pagina"]}, "hoja": {json.dumps(f["hoja"], ensure_ascii=False)}`')
        out.append(f"| {f['pagina']} | {f['hoja']} | {archivos} | `{f['carpeta']}/propuesta.json` | {cab} |")
    return "\n".join(out)


def armar_paquete(ruta_pdf: Path, destino: Path, paginas: List[int], lado_pt: float = LADO_PT) -> Path:
    """
    Prepara las páginas (A2) y arma `destino/lotes/<lote>/` con los archivos en plano e INSTRUCCIONES.md.
    Devuelve la carpeta del lote. Rehacer el mismo lote la vacía y la vuelve a llenar (todo en ella es derivado).
    """
    if not paginas:
        raise ValueError("Indica al menos una página para el lote.")
    destino = pr._validar_destino(destino)
    man = pr.preparar_hojas(Path(ruta_pdf), destino, paginas)
    paginas = sorted(set(paginas))
    lote = "-".join(f"p{p:02d}" for p in paginas)
    carpeta = destino / "lotes" / lote
    if carpeta.exists():
        shutil.rmtree(carpeta)
    carpeta.mkdir(parents=True)
    filas = []
    for p in paginas:
        hoja_dir = destino / f"p{p:02d}"
        t = json.loads((hoja_dir / "textos.json").read_text(encoding="utf-8"))
        archivos = [f"p{p:02d}-hoja.png", f"p{p:02d}-textos.txt"]
        shutil.copyfile(hoja_dir / "hoja.png", carpeta / archivos[0])
        shutil.copyfile(hoja_dir / "textos.txt", carpeta / archivos[1])
        for caja in cuadricula(t["ancho_pt"], t["alto_pt"], lado_pt):
            rec = pr.recortar(Path(ruta_pdf), destino, p, caja, PPP_RECORTE)
            nombre = f"p{p:02d}-zona-{rec.name}"
            shutil.copyfile(rec, carpeta / nombre)
            archivos.append(nombre)
        filas.append({"pagina": p, "hoja": t["hoja"], "archivo": t["archivo"], "sha256": t["sha256"],
                      "carpeta": str(hoja_dir), "archivos": archivos})
    texto = (PLANTILLA.read_text(encoding="utf-8")
             .replace("{{LOTE}}", lote).replace("{{ARCHIVO}}", man["archivo"]).replace("{{SHA256}}", man["sha256"])
             .replace("{{FECHA}}", datetime.now().strftime("%d/%m/%Y")).replace("{{HOJAS}}", _tabla_hojas(filas)))
    (carpeta / "INSTRUCCIONES.md").write_bytes(texto.encode("utf-8"))
    (carpeta / "lote.json").write_bytes(pr._json({"version": 1, "lote": lote, "archivo": man["archivo"],
                                                  "sha256": man["sha256"], "hojas": filas}))
    return carpeta


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m plano.asistido.paquete")
    ap.add_argument("pdf"), ap.add_argument("destino")
    ap.add_argument("--paginas", required=True, help="lista separada por comas, p. ej. 14,16")
    ap.add_argument("--lado", type=float, default=LADO_PT, help="lado máximo de cada recorte, en pt")
    a = ap.parse_args(argv)
    try:
        carpeta = armar_paquete(Path(a.pdf), Path(a.destino), [int(x) for x in a.paginas.split(",") if x.strip()],
                                a.lado)
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    n = len(list(carpeta.iterdir()))
    print(f"{carpeta}  ({n} archivos; empieza por INSTRUCCIONES.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
