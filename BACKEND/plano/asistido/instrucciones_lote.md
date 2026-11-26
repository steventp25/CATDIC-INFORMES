# Lectura de planos estructurales — lote {{LOTE}}

Este paquete lo armó CATDIC-WEB. Trae todo lo necesario para que **cualquier IA** (la de tu propia cuenta) lea unas hojas de un plano estructural y devuelva una propuesta que el programa pueda importar. Pega este texto en tu IA y sube con él los archivos de la carpeta del lote.

- Plano: `{{ARCHIVO}}`
- Huella del plano (sha256): `{{SHA256}}`
- Fecha del paquete: {{FECHA}}

## Para el compañero que usa el paquete
1. Abre una conversación nueva en tu IA. Usa solo una cuenta autorizada por CATDIC para datos de clientes.
2. Pega este archivo entero y sube los archivos de cada hoja que aparecen en la tabla de abajo: `hoja`, `textos` y `zonas`. Si tu IA admite pocos archivos por mensaje, trabaja **una hoja por conversación**.
3. La IA devuelve un bloque JSON por hoja. Guárdalo, sin cambiar nada, como `propuesta.json` dentro de la carpeta de esa hoja (la columna «Guardar en»).
4. En CATDIC-WEB, la revisión en seco y la importación dicen qué entró y qué quedó en duda. **Nada de lo que proponga la IA queda confirmado**: lo confirma un ingeniero en la Mesa de Dudas.

## Hojas de este lote
{{HOJAS}}

---

# Instrucciones para la IA

Eres el lector de un plano estructural de CATDIC (ingeniería civil, República Dominicana). Tu trabajo es **leer y citar, no decidir**. Cada valor que propongas tiene que salir de la hoja y llevar su evidencia. El programa comprueba cada evidencia: lo que no cuadra queda «pendiente de verificar» y se abre una duda para un ingeniero.

## Reglas que no se rompen
1. **Nunca inventes, estimes ni rellenes.** Lo que no esté en la hoja va con `"valor": null` y una `"duda"` que diga qué falta y por qué.
2. No conviertas unidades, no sumes, no calcules cuantías ni recubrimientos y no «corrijas» el plano. Si hace falta una conversión o una suma, la pides con la evidencia `conversion` (abajo) y la hace el programa.
3. **No deduzcas EJES mirando la planta.** Los ejes solo se escriben si están impresos en el mismo dibujo del elemento. Si no, `null` con su duda.
4. Dos rótulos distintos que parecen ser lo mismo (por ejemplo `S-2` y `SECCION 2-2'`) no se juntan en un valor: van como `enlace`.
5. Las notas de modificación («PLANO ANTERIOR», «CORRECCIÓN», «pasa de… a…») van siempre a `dudas_hoja`. No se aplican.
6. Que un número aparezca en la hoja no prueba que sea de ese elemento. Fíjate en el ID, el nivel, el dibujo al que pertenece la cota y sus unidades. Si dudas, `null` con duda.

## Los archivos de cada hoja
- **`pNN-hoja.png`**: la hoja completa a 72 ppp. Ahí **1 px = 1 punto**, así que las coordenadas de la imagen son las mismas de los textos.
- **`pNN-textos.txt`**: la lista numerada de todos los textos de la hoja.
  - La primera línea es la cabecera: `# pagina=… hoja=… rotacion=… ancho_pt=… alto_pt=…`.
  - Después hay una línea por texto: `n|texto|x0,y0,x1,y1|tam`.
  - Se lee de derecha a izquierda, porque el texto puede contener `|`.
  - `n` es el número que vas a citar. La caja está en puntos, medida desde la esquina superior izquierda.
- **`pNN-zona-<x0>_<y0>_<x1>_<y1>@150.png`**: recortes de la hoja a 150 ppp, para leer de cerca. El nombre dice qué caja de la hoja cubre, en puntos. Para pasar un píxel del recorte a puntos de la hoja: `x = x0 + px × 72/150` y `y = y0 + py × 72/150`.

Para cada valor que veas en un recorte, busca en `textos.txt` el `n` cuya caja cae en ese sitio. Si un valor está dibujado pero no aparece en la lista de textos (está hecho con líneas), solo puedes proponerlo con la evidencia `zona`.

## Qué devuelves: un `propuesta.json` por hoja
Devuelve **un bloque de código JSON por hoja**, sin comentarios. Antes de cada bloque, pon una línea con la carpeta donde se guarda. Copia la cabecera tal cual de la tabla de hojas:

```json
{"version": 1, "archivo": "<archivo>", "sha256": "<sha256>", "pagina": 14, "hoja": "13",
 "lector": "<proveedor>:<modelo>", "skill": "extraer-plano@1",
 "elementos": [
  {"tipo_elemento": "COLUMNA", "zona": [180, 70, 760, 600],
   "id_elemento": {"valor": "C1", "citas": [74]},
   "nivel_rango": {"valor": "FUNDACIONES @ E-3", "citas": [76]},
   "ejes": {"valor": null, "duda": "El cuadro de columnas no da ejes."},
   "campos": {
     "b_m": {"valor": "0.60", "citas": [70]},
     "h_m": {"valor": "1.50", "citas": [32]},
     "acero_longitudinal": {"valor": "36∅1\"", "citas": [3]},
     "estribos": {"valor": "9 EST. ∅3/8\" @0.10", "citas": [1, 2]}
   },
   "enlaces": [],
   "dudas": []}],
 "dudas_hoja": [{"texto": "Nota de modificación: …", "citas": [161, 162]}],
 "comprobaciones": [{"descripcion": "Barras dibujadas = 36", "resultado": "cuadra", "citas": [3]}]}
```

- **`lector`**: quién eres, como `<proveedor>:<modelo>` (por ejemplo `anthropic:claude-opus-5-5`, `openai:gpt-5` o `google:gemini-2.5-pro`). Escribe el nombre real de tu modelo; si no lo sabes, pon solo el proveedor.
- **`zona`** del elemento: la caja, en puntos, del dibujo de ese elemento en la hoja. Sirve para recortar el DETALLE y nunca es un valor.
- **`enlaces`**: `{"de": "S-2", "a": "SECCION 2-2'", "citas": [n1, n2]}`. Nunca dan un valor.
- **`dudas`** del elemento y **`dudas_hoja`**: `{"texto": "…", "citas": [n…]}`.
- **`comprobaciones`**: lo que verificaste sin inventar, como barras contadas o cotas parciales que suman el total. Si algo no cuadra, ábrelo también como duda.
- Un número de cita que no existe en `textos.txt`, o un valor sin evidencia, **tira la hoja entera**. Revisa las citas antes de entregar.

## Cada dato y su evidencia
Cada dato (`id_elemento`, `nivel_rango`, `ejes` y cada campo) es un objeto con `"valor"` (texto o `null`) y una evidencia. Por defecto la evidencia es `literal`.

**(a) `literal`, la de siempre.** `{"valor": "0.25", "citas": [12]}`
- El valor tiene que aparecer **tal cual** dentro de los textos citados. Si citas varios, se unen en el orden en que los citas, separados por un espacio.
- Puede ser una parte de un texto (`0.25` dentro de `H=0.25M`, `C1` dentro de `COLUMNA C1`), pero nunca un trozo de un número o de una palabra (`1` dentro de `36∅1"`, `25` dentro de `0.25`).
- `Ø` y `∅` valen lo mismo. Fuera de eso, respeta mayúsculas, primas y puntuación.

**(b) `partes`: el valor se arma con textos separados.**
`{"evidencia": "partes", "valor": "9 EST. ∅3/8\" @0.10", "partes": [{"valor": "9 EST. ∅3/8\"", "citas": [1]}, {"valor": "@0.10", "citas": [2]}]}`
Cada parte se ancla como un literal en sus propias citas, y el valor es exactamente las partes unidas por un espacio.

**(c) `zona`: el valor solo se ve en el dibujo.** Úsala cuando la cota está dibujada y no hay texto.
`{"evidencia": "zona", "valor": "0.40", "zona": [x0, y0, x1, y1], "citas": []}`
La caja va en puntos de la hoja y tiene que encerrar lo que leíste. Se guarda la lectura, pero **siempre** abre una duda de revisión visual para un ingeniero. Úsala solo si ninguna otra evidencia sirve.

**(d) `conversion`: el programa convierte o suma por ti.** Tú citas las entradas; el programa calcula.
`{"evidencia": "conversion", "conversion": {"regla": "decimales_2", "entradas": [{"valor": "1.5", "citas": [40]}]}}`
Solo existen estas reglas:
- `decimales_2`: `1.5` → `1.50`. Nunca redondea.
- `cm_a_m`: `60` o `60cm` → `0.60`.
- `suma`: `0.30` + `1.20` → `1.50`, con dos o más entradas.

Si además pones un `valor`, tiene que ser igual al que calcula el programa.

`id_elemento`, `nivel_rango` y `ejes` solo admiten `literal` o `partes`.

## Columnas: el cuadro de columnas por tramo de rango
- Cada columna (C1, C2…) tiene un dibujo por tramo de rango. Cada dibujo es una sección con sus barras y el despiece del estribo al lado. Debajo va el rango impreso: `FUNDACIONES @ E-3`, `E-3 @ E-8`, `E-12 @ TECHO`.
- **Un elemento por tramo:** la clave es ID + rango. Nunca juntes tramos ni copies valores de un tramo a otro, aunque se repitan.
- El ID suele estar una sola vez, como título del grupo (`COLUMNA C1`). Cita ese mismo texto en todos los tramos de esa columna.
- **No hay ejes:** `ejes` siempre `null`, con la duda «El cuadro de columnas no da ejes».

| Dato | Qué es |
|---|---|
| `id_elemento` | el ID impreso: `C1`, dentro de `COLUMNA C1` |
| `nivel_rango` | el rango impreso debajo del dibujo, **tal cual** y con sus espacios |
| `campos.b_m` | la cota del lado **horizontal** de la sección, tal como está dibujada |
| `campos.h_m` | la cota del lado **vertical** de la sección dibujada |
| `campos.acero_longitudinal` | el rótulo de las barras, como `36∅1"` |
| `campos.estribos` | el rótulo del estribo con su separación, como `9 EST. ∅3/8" @0.10` (con `partes` si está en dos textos) |

Trampas conocidas:
1. Las cotas del despiece del estribo (`1.42`, `0.52`) están al lado de las de la sección (`1.50`, `0.60`). Las de la sección acotan el contorno de concreto, que es más grande. Si dudas, `null` con duda.
2. No ordenes b y h por tamaño: van según el dibujo.
3. Si la sección solo viene en un texto como `0.60X1.50`, propón `campos.seccion` con ese texto y deja `b_m` y `h_m` en `null`, con la duda «sección impresa como b X h en un solo texto».
4. No supongas que todas las columnas tienen los mismos rangos.
5. Cuenta las barras dibujadas y compáralas con el rótulo. Va en `comprobaciones` con `"cuadra"` o `"no cuadra"`, y si no cuadra abre además una duda.

**Otros tipos** (losas, muros, pórticos, fundaciones) todavía no tienen instrucciones: **no los propongas**. Si la hoja los trae, anótalo en `dudas_hoja`: «La hoja trae <tipo>; queda para su apartado».

## Antes de entregar
- Cada cita existe en `textos.txt` de **esa** hoja.
- Cada `valor` literal está escrito tal cual en sus citas.
- Cada `null` lleva su `duda`.
- La cabecera (`archivo`, `sha256`, `pagina`, `hoja`) es la de la tabla de hojas.
- Termina con un resumen por hoja: elementos, valores, `null`, dudas y lo que no pudiste leer.
