---
name: extraer-plano
description: Lectura asistida de planos estructurales vectoriales de CATDIC-WEB (Etapa 5). Claude mira la imagen de cada hoja y su lista numerada de textos, y escribe un propuesta.json por hoja citando los números de texto; nunca toca la BD. Úsala cuando se pida leer, extraer o proponer datos de diseño de hojas de un plano (cuadro de columnas, losas, muros, pórticos), o se escriba /extraer-plano.
---

# extraer-plano — leer hojas del plano y proponer, citando

Tu trabajo es **leer y citar, no decidir**. El valor lo pone el plano: cada valor que propongas tiene que estar escrito, tal cual, en los textos que citas. Lo que no esté escrito en la hoja no se rellena: se deja `null` con una `duda`. El importador del backend comprueba cada cita, y lo que no coincida lo deja «pendiente de verificar» y abre una duda en la Mesa. Nada de lo que propongas nace confirmado; lo confirma Steven.

Reglas de CATDIC que mandan aquí (CLAUDE.md §4): la Regla de Oro #1 (nunca inventar, estimar ni rellenar), las tres capas (tú solo trabajas en la Capa 1, planos; nunca en fotos ni cálculos) y el formato de `EJES` de §4.4.

## Qué no haces nunca
- Escribir en la BD (`catdic_local.db`), en Dropbox o en el repositorio. Tu única salida es `propuesta.json` dentro de la carpeta de lectura.
- Convertir unidades, sumar, calcular cuantías o recubrimientos, ni «corregir» un texto del plano.
- Deducir EJES por cercanía en la planta (error 11; decisión D11). Los EJES solo se escriben si están impresos en el mismo dibujo del elemento.
- Unir dos rótulos distintos como si fueran el mismo dato (`S-2` ↔ `SECCION 2-2'`, `L17` ↔ fila `B`). Eso va como `enlace`, nunca como valor.
- Leer el PDF entero de una vez. Se trabaja **por lotes**: 4–6 hojas de columnas, losas o muros, o **un solo pórtico**, por sesión.

## Paso 0 — Ubicar la carpeta de lectura
Desde `BACKEND`, con el Python del proyecto (`C:\Users\Steve\AppData\Local\Python\pythoncore-3.14-64\python.exe`):
- Raíz de datos: `python -c "import config; print(config.obtener_datos_raiz())"`. La carpeta es `<raíz>/<proyecto_id>/lectura-asistida/`.
- `manifiesto.json` dice qué páginas ya están preparadas. Si falta la que te piden, prepárala (solo lectura sobre el PDF):
  `python -m plano.asistido.preparar hojas "<pdf vectorial vigente>" "<carpeta>" --paginas 14,16`
  La ruta del vectorial vigente te la da el usuario, o sale de `planos.vectorial_ruta` con `estado = 'vigente'` (consulta de solo lectura).

## Paso 1 — Orientarte en la hoja
1. Lee `pNN/textos.txt`. La cabecera da la página, la hoja y la rotación; cada línea es `n|texto|x0,y0,x1,y1|tam`, y se lee de derecha a izquierda porque el texto puede contener `|`.
2. Mira `pNN/hoja.png` (72 ppp) para ver qué dibujos hay y dónde están. A 72 ppp, 1 px = 1 pt: las coordenadas de la imagen son las de las bbox.
3. Busca el **título impreso de la hoja** y las notas («NOTA ESTRUCTURAL», «PLANO ANTERIOR», «CORRECCIÓN»). Las notas de modificación van siempre a `dudas_hoja`; nunca se aplican.

## Paso 2 — Mirar de cerca
Para cada dibujo, pide un recorte a 150 ppp con su recuadro en pt (el mismo marco que las bbox; vale también para hojas giradas):
`python -m plano.asistido.preparar recorte "<pdf>" "<carpeta>" <pagina> x0 y0 x1 y1`
Imprime la ruta del PNG en `pNN/zonas/`; míralo. Un recorte de unos 500×600 pt se lee bien. Asocia cada número que veas con el `n` de `textos.txt` cuya bbox cae en ese sitio. **Si un valor que ves no tiene texto en la lista** (está dibujado como curvas, no como texto), no lo propongas: déjalo `null` con una duda que lo diga.

## Paso 3 — Escribir `pNN/propuesta.json`
Formato exacto en `PLANES/etapa-5-contrato-asistido.md` §4. Lo esencial:

```json
{"version": 1, "archivo": "<de textos.json>", "sha256": "<de textos.json>", "pagina": 14, "hoja": "13",
 "lector": "anthropic:<tu modelo>", "skill": "extraer-plano@1",
 "elementos": [{"tipo_elemento": "COLUMNA", "zona": [x0, y0, x1, y1],
   "id_elemento": {"valor": "C1", "citas": [74]},
   "nivel_rango": {"valor": "FUNDACIONES @ E-3", "citas": [76]},
   "ejes": {"valor": null, "duda": "El cuadro de columnas no da ejes (D11)."},
   "campos": {"b_m": {"valor": "0.60", "citas": [70]}, "estribos": {"valor": "9 EST. ∅3/8\" @0.10", "citas": [1, 2]}},
   "enlaces": [], "dudas": []}],
 "dudas_hoja": [], "comprobaciones": []}
```

Cómo se escribe cada dato:
- **`valor` es un trozo literal de la unión de los textos citados** (en el orden en que los citas, separados por un espacio). Puede ser una parte del texto (`0.25` dentro de `H=0.25M`, `C1` dentro de `COLUMNA C1`), pero nunca un trozo de una palabra o de un número (`1` dentro de `36∅1"` no vale; `25` dentro de `0.25` tampoco).
- Si el valor está repartido en dos textos (`9 EST. ∅3/8"` y `@0.10`), cita los dos **en orden**.
- `valor: null` siempre lleva `duda`: qué falta y por qué.
- `nivel_rango` va **como está impreso** (`FUNDACIONES @ E-3`, `E-12 @ TECHO`, `NPT= 3.60`). Pasarlo a niveles lo hace el backend.
- `zona` es el recuadro del dibujo del elemento, en pt; se usa para el recorte de DETALLE.
- `lector` es `<proveedor>:<modelo>` (p. ej. `anthropic:claude-opus-5-5`): se guarda en la fuente de cada valor.
- **Evidencias (contrato §5.1):** si un valor no está en un solo texto, usa `partes` (varios textos unidos por un espacio); si solo está dibujado, `zona` (abre siempre una duda de revisión visual); si hace falta convertir o sumar, `conversion` con una regla del programa (`decimales_2`, `cm_a_m`, `suma`). Tú nunca conviertes. `id_elemento`, `nivel_rango` y `ejes` solo con `literal` o `partes`.
- `comprobaciones`: lo que verificaste sin inventar (barras dibujadas = cantidad del rótulo; cotas parciales que suman el total). Si algo no cuadra, va además como `duda`.
- Escribe la propuesta de cada hoja **en cuanto la termines**, antes de pasar a la siguiente: así se retoma donde quedó.

## Paso 4 — Revisar en seco antes de dar la hoja por hecha
Desde `BACKEND`: `python ../.claude/skills/extraer-plano/revisar.py "<carpeta>/pNN"`
- `RECHAZADA` → corrige el formato. Una sola cita mala tira la hoja entera.
- `NO SE ANCLA` → corrige la cita o el valor para que el valor sea el texto literal. Si de verdad no está escrito, déjalo `null` con su duda. **Nunca** cambies el valor para que «pase» si el plano dice otra cosa.

## Paso 5 — Informar
Al final del lote, di por hoja: cuántos elementos, cuántos valores, cuántos `null` y cuántas dudas, más lo que no pudiste leer. No importes tú: la importación la lanza el usuario desde el backend (`plano.asistido.importar.importar_hoja`).

## Paquete para la IA de un compañero (v4, decisión 9)
Si la lectura la hace otra IA (la cuenta de un compañero, sin Claude Code), arma el lote desde `BACKEND`:
`python -m plano.asistido.paquete "<pdf vectorial vigente>" "<carpeta de lectura>" --paginas 14`
Deja `lotes/p14/` con `INSTRUCCIONES.md` autocontenido (lo esencial de esta skill y del formato), la hoja, sus textos y recortes en cuadrícula a 150 ppp. La propuesta que devuelva esa IA se guarda en `pNN/propuesta.json` y se revisa igual (Paso 4). Si cambias esta skill, cambia también `BACKEND/plano/asistido/instrucciones_lote.md`.

## Por tipo de elemento (orden D10)
Lee la referencia del tipo antes de empezar sus hojas:
- **Columnas** → `referencias/columnas.md` (A4a).
- Losas, muros, pórticos y fundaciones → se añaden en A4b, A4c, A4d y según D12. Mientras no estén, **no propongas esos tipos**: si una hoja los trae, anota en tu informe que quedan para su apartado.
