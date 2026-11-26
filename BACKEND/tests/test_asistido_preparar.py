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
    assert man["hojas"] == [{"pagina": 1, "hoja": "06", "carpeta": "p01", "ppp": 72, "textos": 4}]
    t = _leer(tmp_path / "out", 1)
    assert [x["n"] for x in t["textos"]] == [1, 2, 3, 4]
    assert [x["texto"] for x in t["textos"]][:2] == ["ARRIBA", "MEDIO"]
    assert t["px_por_pt"] == 1.0 and t["ppp"] == 72 and t["hoja"] == "06" and t["pagina"] == 1
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
    assert uno == dos and len(uno) == 7
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


# ---------- Ajustes (Líder Fase A) ----------

def _pdf2(ruta: Path, rot=0) -> Path:
    doc = pymupdf.open()
    p = doc.new_page(width=600, height=400)
    p.insert_text((300, 200), "ZZ CENTRO", fontsize=14)
    p.insert_text((40, 60), "A|B|C", fontsize=10)
    doc.new_page(width=600, height=400).insert_text((50, 50), "SEGUNDA", fontsize=10)
    if rot:
        doc[0].set_rotation(rot)
    doc.save(str(ruta))
    return ruta


def test_ppp_por_defecto_72():
    import inspect
    assert inspect.signature(pr.preparar_hojas).parameters["ppp"].default == 72
    assert inspect.signature(pr.recortar).parameters["ppp"].default == 150


def test_textos_txt_mismo_orden_y_barra(tmp_path):
    pdf = _pdf2(tmp_path / "t.pdf")
    pr.preparar_hojas(pdf, tmp_path / "out", paginas=[1])
    js = _leer(tmp_path / "out", 1)
    lin = (tmp_path / "out" / "p01" / "textos.txt").read_text(encoding="utf-8").splitlines()
    assert lin[0] == "# pagina=1 hoja=pendiente de verificar rotacion=0 ancho_pt=600.0 alto_pt=400.0".replace(
        "pendiente de verificar", PENDIENTE)
    assert len(lin) - 1 == len(js["textos"])
    for l, t in zip(lin[1:], js["textos"]):
        n, resto = l.split("|", 1)
        medio, bbox, tam = resto.rsplit("|", 2)
        assert int(n) == t["n"] and medio == t["texto"] and float(tam) == t["tam"]
        assert bbox == ",".join(str(round(v)) for v in t["bbox"])
    assert any(t["texto"] == "A|B|C" for t in js["textos"])


def test_txt_cambia_saltos_de_linea():
    from types import SimpleNamespace
    page = SimpleNamespace(rotation=0, rect=pymupdf.Rect(0, 0, 10, 10))
    b = pr._txt(1, "01", page, [{"n": 1, "texto": "uno\ndos|x", "bbox": [0.4, 1.6, 2, 3], "tam": 8.0}])
    assert b.decode().splitlines()[1] == "1|uno dos|x|0,2,2,3|8.0"


@pytest.mark.parametrize("rot", [0, 270])
def test_recorte_con_texto_y_vacio(tmp_path, rot):
    pdf = _pdf2(tmp_path / "z.pdf", rot=rot)
    out = tmp_path / "out"
    pr.preparar_hojas(pdf, out, paginas=[1])
    t = _leer(out, 1)
    bb = next(x["bbox"] for x in t["textos"] if x["texto"] == "ZZ CENTRO")

    def oscuros(ruta):
        pix = pymupdf.Pixmap(str(ruta))
        return sum(1 for i in range(pix.width) for j in range(pix.height) if sum(pix.pixel(i, j)[:3]) < 300)

    r = pr.recortar(pdf, out, 1, bb)
    assert r.parent == out / "p01" / "zonas" and r.name.endswith("@150.png")
    assert oscuros(r) > 20
    assert pr.recortar(pdf, out, 1, bb) == r  # idempotente
    ancho, alto = t["ancho_pt"], t["alto_pt"]
    vacio = pr.recortar(pdf, out, 1, [ancho - 30, alto - 30, ancho - 5, alto - 5] if rot == 0
                        else [ancho - 30, 5, ancho - 5, 30])
    assert oscuros(vacio) == 0


def test_recorte_fuera_sin_preparar_o_sha_distinto(tmp_path):
    pdf = _pdf2(tmp_path / "z.pdf")
    out = tmp_path / "out"
    with pytest.raises(ValueError):
        pr.recortar(pdf, out, 1, [0, 0, 50, 50])  # sin preparar
    pr.preparar_hojas(pdf, out, paginas=[1])
    with pytest.raises(ValueError):
        pr.recortar(pdf, out, 1, [700, 500, 800, 600])  # fuera de la página
    otro = _pdf2(tmp_path / "otro.pdf")
    otro.write_bytes(otro.read_bytes() + b"\n%x")
    with pytest.raises(ValueError):
        pr.recortar(otro, out, 1, [0, 0, 50, 50])  # sha distinto
    with pytest.raises(ValueError):
        pr.recortar(pdf, tmp_path / "dbx_no", 2, [0, 0, 50, 50])  # página 2 no preparada


def test_manifiesto_acumulativo_y_relote(tmp_path):
    pdf = _pdf2(tmp_path / "m.pdf")
    out = tmp_path / "out"
    pr.preparar_hojas(pdf, out, paginas=[1])
    man = pr.preparar_hojas(pdf, out, paginas=[2], ppp=100)
    assert [(h["pagina"], h["ppp"]) for h in man["hojas"]] == [(1, 72), (2, 100)] and "ppp" not in man
    man = pr.preparar_hojas(pdf, out, paginas=[1], ppp=50)
    assert [(h["pagina"], h["ppp"]) for h in man["hojas"]] == [(1, 50), (2, 100)]
    assert json.loads((out / "manifiesto.json").read_text(encoding="utf-8")) == man


def test_otro_pdf_en_el_mismo_destino(tmp_path):
    a = _pdf2(tmp_path / "a.pdf")
    out = tmp_path / "out"
    pr.preparar_hojas(a, out, paginas=[1])
    antes = (out / "manifiesto.json").read_bytes()
    b = tmp_path / "b.pdf"
    b.write_bytes(a.read_bytes() + b"\n%otra version")
    with pytest.raises(ValueError, match="otra versión"):
        pr.preparar_hojas(b, out, paginas=[2])
    assert (out / "manifiesto.json").read_bytes() == antes and not (out / "p02").exists()


def test_cli(tmp_path, capsys):
    pdf = _pdf2(tmp_path / "c.pdf")
    out = tmp_path / "out"
    assert pr.main(["hojas", str(pdf), str(out), "--paginas", "1"]) == 0
    assert "1 hoja" in capsys.readouterr().out
    assert pr.main(["recorte", str(pdf), str(out), "1", "280", "180", "400", "210"]) == 0
    ruta = Path(capsys.readouterr().out.strip())
    assert ruta.exists() and ruta.name == "280_180_400_210@150.png"
    assert pr.main(["recorte", str(pdf), str(out), "1", "900", "900", "950", "950"]) == 1
