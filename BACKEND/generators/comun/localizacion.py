# BACKEND/generators/comun/localizacion.py
# Etapa 3 · T6 — M3 (CLAUDE.md §4.7): LOCALIZACION.
# Etapa 7 · T12: planta estructural ENTERA del nivel recortada a su dibujo (la «zona de planta» de la hoja,
# confirmada en el visor): sin cajetín, tablas, notas ni otros dibujos de la hoja, y nunca un zoom a una parte
# de la planta (error #1). Recuadro rojo RGB(220,0,0) cuyo grosor, calculado sobre la imagen YA recortada,
# compensa la reducción (error #4). Las coordenadas del recuadro y de la zona llegan como parámetro: este módulo
# nunca las deduce. Sin zona no hay vuelta a la hoja entera: ValueError «pendiente de verificar».
import math
from pathlib import Path
from typing import Optional, Tuple, Union

import pymupdf
from PIL import Image, ImageDraw

from reglas_ingenieria import PENDIENTE, calcular_grosor_recuadro_rojo

DPI_PLANTA = 200
ROJO = (220, 0, 0)
Caja = Tuple[float, float, float, float]  # x0, y0, x1, y1 en píxeles de la imagen rasterizada


def rasterizar_pagina_completa(ruta_pdf: Union[str, Path], pagina: int, dpi: int = DPI_PLANTA) -> Image.Image:
    """Rasteriza la página ENTERA del plano (pagina es 0-based), sin recorte."""
    if dpi <= 0:
        raise ValueError(f"{PENDIENTE}: dpi inválido.")
    with pymupdf.open(str(ruta_pdf)) as doc:
        if not 0 <= pagina < doc.page_count:
            raise ValueError(f"{PENDIENTE}: la hoja {pagina} no existe en el plano ({doc.page_count} hojas).")
        pix = doc[pagina].get_pixmap(dpi=dpi, alpha=False)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def dibujar_recuadro_rojo(planta: Image.Image, caja: Caja, ancho_celda_px: int, alto_celda_px: int
                          ) -> Tuple[Image.Image, int]:
    """
    Dibuja el recuadro rojo en una copia de la planta. `caja` viene dada (px de la planta);
    si no cabe en la imagen o es degenerada -> ValueError 'pendiente de verificar'.
    Devuelve (imagen, grosor_en_px_de_la_fuente).
    """
    x0, y0, x1, y1 = caja
    if not (0 <= x0 < x1 <= planta.width and 0 <= y0 < y1 <= planta.height):
        raise ValueError(f"{PENDIENTE}: el recuadro {caja} no cabe en la planta de "
                         f"{planta.width}×{planta.height} px; las coordenadas no se deducen.")
    grosor = calcular_grosor_recuadro_rojo(planta.width, planta.height, ancho_celda_px, alto_celda_px)
    salida = planta.convert("RGB").copy()
    ImageDraw.Draw(salida).rectangle([x0, y0, x1, y1], outline=ROJO, width=grosor)
    return salida, grosor


def recortar_a_zona(planta: Image.Image, zona: Caja) -> Image.Image:
    """Recorta la planta rasterizada a la zona (px de la misma imagen). Una zona degenerada o fuera de la hoja es un error."""
    try:
        x0, y0, x1, y1 = [float(v) for v in zona]
    except (TypeError, ValueError):
        raise ValueError(f"{PENDIENTE}: la zona de planta debe ser [x0, y0, x1, y1] en píxeles.") from None
    if not (-0.5 <= x0 < x1 <= planta.width + 0.5 and -0.5 <= y0 < y1 <= planta.height + 0.5):
        raise ValueError(f"{PENDIENTE}: la zona de planta {zona} no cabe en la hoja de {planta.width}×{planta.height} px.")
    caja = (max(0, math.floor(x0)), max(0, math.floor(y0)), min(planta.width, math.ceil(x1)), min(planta.height, math.ceil(y1)))
    return planta.crop(caja)


def generar_localizacion(ruta_pdf: Union[str, Path], pagina: int, caja: Caja, ancho_celda_px: int,
                         alto_celda_px: int, dpi: int = DPI_PLANTA, zona: Optional[Caja] = None) -> Image.Image:
    """
    Planta recortada a su zona (px a `dpi`) + recuadro rojo con grosor compensado sobre la imagen ya recortada.
    `caja` y `zona` van en píxeles de la hoja rasterizada a `dpi`. La caja se traslada al origen de la zona y debe
    caer ENTERA dentro: el recuadro nunca se recorta. Sin zona (None) no hay vuelta a la hoja entera.
    """
    if zona is None:
        raise ValueError(f"{PENDIENTE}: no hay zona de planta confirmada para esta hoja; LOCALIZACION no sale de la "
                         "hoja entera (con cajetín) ni de un zoom.")
    planta = rasterizar_pagina_completa(ruta_pdf, pagina, dpi)
    recortada = recortar_a_zona(planta, zona)
    ox, oy = max(0, math.floor(zona[0])), max(0, math.floor(zona[1]))
    cx0, cy0, cx1, cy1 = caja
    trasladada = (cx0 - ox, cy0 - oy, cx1 - ox, cy1 - oy)
    if not (0 <= trasladada[0] < trasladada[2] <= recortada.width and 0 <= trasladada[1] < trasladada[3] <= recortada.height):
        raise ValueError(f"{PENDIENTE}: el recuadro {caja} no cae entero dentro de la zona de planta {tuple(zona)}; "
                         "no se recorta el recuadro: ajusta la zona o el recuadro en el visor.")
    imagen, _ = dibujar_recuadro_rojo(recortada, trasladada, ancho_celda_px, alto_celda_px)
    return imagen
