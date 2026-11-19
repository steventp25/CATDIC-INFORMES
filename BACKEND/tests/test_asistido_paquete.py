# BACKEND/tests/test_asistido_paquete.py
# Etapa 5 · A4-paquete — paquete de lectura para cualquier IA. Todo # SINTÉTICO: PDF creados aquí con PyMuPDF.
import hashlib
import json
from pathlib import Path

import pymupdf
import pytest

from plano.asistido import paquete as pq


def _pdf(ruta: Path, ancho=1700, alto=900) -> Path:
    doc = pymupdf.open()
    for i in range(2):
        p = doc.new_page(width=ancho, height=alto)
        p.insert_text((100, 100), f"COLUMNA C{i + 1}", fontsize=10)
        p.insert_text((ancho - 80, alto - 20), f"0{i + 1}", fontsize=10)
        p.insert_text((ancho - 66, alto - 20), "/36", fontsize=10)
    doc.save(str(ruta))
    return ruta


def _sha(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def test_cuadricula_cubre_la_hoja_sin_pasar_del_lado():  # SINTÉTICO
    cajas = pq.cuadricula(1700, 900, lado=800, solape=40)
    assert len(cajas) == 3 * 2
    assert min(c[0] for c in cajas) == 0 and min(c[1] for c in cajas) == 0
    assert max(c[2] for c in cajas) == 1700 and max(c[3] for c in cajas) == 900
    assert all(c[2] - c[0] <= 800 + 2 * 40 and c[3] - c[1] <= 800 + 2 * 40 for c in cajas)
    # vecinas se solapan: ningún hueco entre columnas ni entre filas
    assert cajas[0][2] > cajas[1][0] and cajas[0][3] > cajas[3][1]


def test_cuadricula_hoja_pequena_es_un_solo_recorte():  # SINTÉTICO
    assert pq.cuadricula(600, 400) == [[0.0, 0.0, 600.0, 400.0]]


def test_paquete_arma_la_carpeta_plana_e_instrucciones(tmp_path):  # SINTÉTICO
    pdf = _pdf(tmp_path / "vec.pdf")
    antes = _sha(pdf)
    carpeta = pq.armar_paquete(pdf, tmp_path / "out", [2, 1], lado_pt=800)
    assert carpeta == (tmp_path / "out" / "lotes" / "p01-p02").resolve()
    nombres = sorted(x.name for x in carpeta.iterdir())
    for p in ("p01", "p02"):
        assert f"{p}-hoja.png" in nombres and f"{p}-textos.txt" in nombres
        assert len([n for n in nombres if n.startswith(f"{p}-zona-") and n.endswith("@150.png")]) == 6
    ins = (carpeta / "INSTRUCCIONES.md").read_text(encoding="utf-8")
    assert "{{" not in ins
    assert antes in ins and "vec.pdf" in ins and '"pagina": 2, "hoja": "02"' in ins
    assert "p02-zona-" in ins and "propuesta.json" in ins
    lote = json.loads((carpeta / "lote.json").read_text(encoding="utf-8"))
    assert [h["pagina"] for h in lote["hojas"]] == [1, 2] and lote["sha256"] == antes
    assert (tmp_path / "out" / "p01" / "textos.json").exists()  # las hojas quedan preparadas para revisar/importar
    assert _sha(pdf) == antes  # el plano no se toca


def test_rehacer_el_lote_no_deja_restos(tmp_path):  # SINTÉTICO
    pdf = _pdf(tmp_path / "vec.pdf")
    carpeta = pq.armar_paquete(pdf, tmp_path / "out", [1], lado_pt=800)
    (carpeta / "sobra.txt").write_text("x", encoding="utf-8")
    carpeta = pq.armar_paquete(pdf, tmp_path / "out", [1], lado_pt=2000)
    nombres = [x.name for x in carpeta.iterdir()]
    assert "sobra.txt" not in nombres
    assert len([n for n in nombres if "-zona-" in n]) == 1


def test_sin_paginas_o_destino_en_el_repo_falla(tmp_path):  # SINTÉTICO
    pdf = _pdf(tmp_path / "vec.pdf")
    with pytest.raises(ValueError):
        pq.armar_paquete(pdf, tmp_path / "out", [])
    with pytest.raises(ValueError):
        pq.armar_paquete(pdf, Path(pq.__file__).parent / "no-aqui", [1])


def test_la_plantilla_trae_las_cuatro_evidencias_y_las_reglas():  # SINTÉTICO
    t = pq.PLANTILLA.read_text(encoding="utf-8")
    for clave in ('"evidencia": "partes"', '"evidencia": "zona"', '"evidencia": "conversion"',
                  "decimales_2", "cm_a_m", "`suma`", '"lector"', "Nunca inventes"):
        assert clave in t
