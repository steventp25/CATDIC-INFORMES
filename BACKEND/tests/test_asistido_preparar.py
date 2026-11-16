# BACKEND/tests/test_asistido_preparar.py
# Etapa 5 · A2 — Preparar hojas del plano vectorial. Todo # SINTÉTICO: PDF creados aquí con PyMuPDF.
import hashlib
import json
from pathlib import Path

import pymupdf
import pytest

import config
from plano.asistido import preparar as pr
from reglas_ingenieria import PENDIENTE


def _pdf(ruta: Path, rot=0, con_hoja=True, capa_apagada=False) -> Path:
    doc = pymupdf.open()
    p = doc.new_page(width=600, height=400)
    p.insert_text((300, 200), "ZZ CENTRO", fontsize=14)
    p.insert_text((40, 60), "ARRIBA", fontsize=10)
    p.insert_text((200, 61), "MEDIO", fontsize=10)
    if capa_apagada:
        oculta = doc.add_ocg("oculta", on=False)
        p.insert_text((40, 300), "TEXTO OCULTO", fontsize=10, oc=oculta)
    if con_hoja:
        p.insert_text((520, 380), "06", fontsize=10)
        p.insert_text((534, 380), "/36", fontsize=10)
    doc.new_page(width=600, height=400).insert_text((50, 50), "SEGUNDA", fontsize=10)
    if rot:
        doc[0].set_rotation(rot)
    doc.save(str(ruta))
    return ruta


def _leer(destino, p):
    return json.loads((destino / f"p{p:02d}" / "textos.json").read_text(encoding="utf-8"))


def _hash(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def test_pagina_normal_y_numeracion(tmp_path):
    pdf = _pdf(tmp_path / "a.pdf")
    man = pr.preparar_hojas(pdf, tmp_path / "out", paginas=[1])
    assert man["hojas"] == [{"pagina": 1, "hoja": "06", "carpeta": "p01", "textos": 4}]
    t = _leer(tmp_path / "out", 1)
    assert [x["n"] for x in t["textos"]] == [1, 2, 3, 4]
    assert [x["texto"] for x in t["textos"]][:2] == ["ARRIBA", "MEDIO"]
    assert t["px_por_pt"] == 1.3889 and t["hoja"] == "06" and t["pagina"] == 1
    assert (tmp_path / "out" / "p01" / "hoja.png").exists()
    assert not (tmp_path / "out" / "p02").exists()


def test_pagina_girada_270_bbox_cae_en_la_imagen(tmp_path):
    pdf = _pdf(tmp_path / "g.pdf", rot=270)
    pr.preparar_hojas(pdf, tmp_path / "out", paginas=[1])
    t = _leer(tmp_path / "out", 1)
    assert t["rotacion"] == 270 and (t["ancho_pt"], t["alto_pt"]) == (400.0, 600.0)
    pix = pymupdf.Pixmap(str(tmp_path / "out" / "p01" / "hoja.png"))
    assert (pix.width, pix.height) == (t["ancho_px"], t["alto_px"])
    k = t["px_por_pt"]
    for x in t["textos"]:
        x0, y0, x1, y1 = (round(v * k) for v in x["bbox"])
        oscuros = sum(1 for i in range(max(x0, 0), min(x1, pix.width))
                      for j in range(max(y0, 0), min(y1, pix.height)) if sum(pix.pixel(i, j)[:3]) < 300)
        assert oscuros > 5, x["texto"]
        # y la zona justo fuera del recuadro, lejos, está en blanco: el recuadro no es "todo oscuro" por azar
    assert t["textos"][0]["bbox"][2] <= 400.0 and t["textos"][0]["bbox"][3] <= 600.0


def test_capa_apagada_no_aparece(tmp_path):
    pdf = _pdf(tmp_path / "c.pdf", capa_apagada=True)
    pr.preparar_hojas(pdf, tmp_path / "out", paginas=[1])
    textos = [x["texto"] for x in _leer(tmp_path / "out", 1)["textos"]]
    assert "TEXTO OCULTO" not in textos and "ARRIBA" in textos


def test_idempotente_y_pdf_intacto(tmp_path):
    pdf = _pdf(tmp_path / "i.pdf")
    antes = _hash(pdf)
    pr.preparar_hojas(pdf, tmp_path / "out")
    uno = {p.relative_to(tmp_path / "out"): p.read_bytes() for p in (tmp_path / "out").rglob("*") if p.is_file()}
    pr.preparar_hojas(pdf, tmp_path / "out")
    dos = {p.relative_to(tmp_path / "out"): p.read_bytes() for p in (tmp_path / "out").rglob("*") if p.is_file()}
    assert uno == dos and len(uno) == 5
    assert _hash(pdf) == antes == json.loads(uno[Path("manifiesto.json")])["sha256"]


def test_destino_en_dropbox_o_repo_rechazado(tmp_path, monkeypatch):
    pdf = _pdf(tmp_path / "d.pdf")
    monkeypatch.setenv(config.ENV_DROPBOX_RAIZ, str(tmp_path / "dbx"))
    with pytest.raises(ValueError):
        pr.preparar_hojas(pdf, tmp_path / "dbx" / "sub")
    with pytest.raises(ValueError):
        pr.preparar_hojas(pdf, Path(pr.__file__).resolve().parents[3] / "salida_x")
    assert not (tmp_path / "dbx").exists()


def test_pagina_fuera_de_rango(tmp_path):
    pdf = _pdf(tmp_path / "r.pdf")
    for malas in ([0], [3], [1, 9]):
        with pytest.raises(ValueError):
            pr.preparar_hojas(pdf, tmp_path / "out", paginas=malas)


def test_sin_numero_de_hoja_queda_pendiente(tmp_path):
    pdf = _pdf(tmp_path / "s.pdf", con_hoja=False)
    man = pr.preparar_hojas(pdf, tmp_path / "out", paginas=[1])
    assert man["hojas"][0]["hoja"] == PENDIENTE == _leer(tmp_path / "out", 1)["hoja"]


def test_carpeta_lectura(monkeypatch, tmp_path):
    monkeypatch.setenv(config.ENV_DATOS_RAIZ, str(tmp_path / "datos"))
    assert pr.carpeta_lectura("terra") == (tmp_path / "datos").resolve() / "terra" / "lectura-asistida"
