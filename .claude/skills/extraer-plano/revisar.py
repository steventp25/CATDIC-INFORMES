# Revisión en seco de una propuesta.json (sin BD, sin escribir nada): ¿está bien formada y cada valor se ancla en
# el texto que cita? Uso, desde BACKEND:
#   python ../.claude/skills/extraer-plano/revisar.py <carpeta pNN>
# Sale con código 1 si la hoja sería rechazada; lista los datos que quedarían "pendiente de verificar".
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from plano.asistido import esquema as es  # noqa: E402


def main(carpeta: str) -> int:
    c = Path(carpeta)
    textos = json.loads((c / "textos.json").read_text(encoding="utf-8"))
    propuesta = json.loads((c / "propuesta.json").read_text(encoding="utf-8"))
    try:
        p = es.validar_propuesta(propuesta, textos)
    except es.PropuestaInvalida as e:
        print(f"RECHAZADA (la hoja no se cargaría): {e}")
        return 1
    por_n = es.textos_por_n(textos)
    malos = 0
    for i, el in enumerate(p["elementos"]):
        datos = {k: el[k] for k in es.DATOS_FIJOS} | {f"campos.{k}": v for k, v in el["campos"].items()}
        for nombre, d in datos.items():
            r = es.revisar_dato(d, por_n)
            if r["valor"] is None and d["valor"] is not None:
                malos += 1
                print(f"elementos[{i}].{nombre}: NO SE ANCLA -> {r['duda']}")
    print(f"{len(p['elementos'])} elementos, {malos} valores sin ancla, {len(p['dudas_hoja'])} dudas de hoja.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
