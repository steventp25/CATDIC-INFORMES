# Etapa 5 · Fase A — Contrato de archivos de la lectura asistida (v1)

Fija lo que se pasan las tres piezas: **preparar** (A2, backend) → **leer** (sesión de Claude Code con la skill `extraer-plano`, A4) → **importar** (A3, backend). Sale del informe de A1 (`etapa-5-reconocimiento-asistido.md` §5) y de D10–D13. Si el código y este contrato no coinciden, manda este contrato y se corrige el código (o se cambia el contrato con aviso al Director).

## 1. Carpeta de trabajo

`carpeta_lectura(proyecto_id)` = `<datos>/<proyecto_id>/lectura-asistida/` (fuera del repo y de Dropbox; `preparar._validar_destino` lo impone).

```
lectura-asistida/
  manifiesto.json          # A2: un solo sha256 por carpeta; acumula lotes
  p14/
    hoja.png               # A2: hoja completa, 72 ppp por defecto
    textos.json            # A2: referencia que usa el importador
    textos.txt             # A2: la misma lista, compacta, para leer
    zonas/<x0>_<y0>_<x1>_<y1>@150.png   # A2: recortes pedidos por la sesión lectora
    propuesta.json         # A4 (sesión lectora): una por hoja
    importacion.json       # A3: resultado de la última importación de esta hoja
```

## 2. `manifiesto.json` (A2)
`{"version": 1, "archivo", "sha256", "paginas_total", "hojas": [{"pagina", "hoja", "carpeta", "textos", "ppp"}]}`. Cada lote nuevo se fusiona por página. Si llega otro sha256, se rechaza sin escribir nada.

## 3. `textos.json` y `textos.txt` (A2)
- `textos.json`: `{"version": 1, "archivo", "sha256", "pagina", "hoja", "rotacion", "ancho_pt", "alto_pt", "ppp", "imagen", "ancho_px", "alto_px", "px_por_pt", "textos": [{"n", "texto", "bbox": [x0,y0,x1,y1], "tam"}]}`.
- Las bbox están en puntos, en el **marco visual** de la página: el mismo que ve la imagen y el que recibe `get_pixmap(clip=)`. Los números `n` empiezan en 1, en orden `(round(y0), x0)`, y son estables para un mismo sha256.
- `textos.txt`: una cabecera `# pagina=… hoja=… rotacion=… ancho_pt=… alto_pt=…` y una línea por texto `n|texto|x0,y0,x1,y1|tam` (bbox en enteros). Se lee de derecha a izquierda, porque el texto puede contener `|`.

## 4. `propuesta.json` (sesión lectora, una por hoja)

```json
{"version": 1, "archivo": "…pdf", "sha256": "…", "pagina": 14, "hoja": "13",
 "lector": "anthropic:claude-opus-5-5", "skill": "extraer-plano@1",
 "elementos": [
  {"tipo_elemento": "COLUMNA", "zona": [180, 70, 760, 600],
   "id_elemento": {"valor": "C1", "citas": [74]},
   "nivel_rango": {"valor": "FUNDACIONES @ E-3", "citas": [76]},
   "ejes": {"valor": null, "duda": "El cuadro de columnas no da ejes (D11)."},
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

`lector` es `<proveedor>:<modelo>` de la IA que hizo la propuesta (v4, decisión 9; sin formato forzado: si no se sabe el modelo, solo el proveedor). El paquete para la IA de un compañero lo arma `python -m plano.asistido.paquete` (A4-paquete).

Cada **dato** (`id_elemento`, `nivel_rango`, `ejes` y cada campo) es `{"valor": str|null, "citas": [n…], "duda": str?}`:
- `valor` es una cadena tal como sale del plano. Claude no hace conversiones, unidades ni cálculos.
- `valor: null` obliga a escribir `duda`. El campo queda `"pendiente de verificar"` y se abre una duda `IA:` con ese texto.
- `valor` sin `citas`, o con una cita a un `n` que no existe → **la hoja entera no se carga**: es un archivo mal formado.

Otras claves:
- `zona`: el recuadro (marco visual, en pt) del dibujo del elemento. Se guarda como recorte de DETALLE (M4) y nunca es un valor.
- `enlaces`: unen dos rótulos distintos. Por ejemplo `{"de": "S-2", "a": "SECCION 2-2'", "citas": [n1, n2]}`, o el `L17` de la planta con la fila `B` de la tabla. Un enlace **nunca** da un valor directo: entra como duda o va a confirmación por lote.
- `dudas` (del elemento) y `dudas_hoja`: notas de modificación ("plano anterior"), contradicción entre planta y detalle (§4.2), cotas que no suman. Cada una se abre como `DUDA_BLOQUEANTE` con prefijo `IA:`.
- `comprobaciones`: solo informan (sumas de cotas, barras contadas). No cambian ningún valor.

## 5. Regla de anclaje (la aplica el importador)
1. Se unen los textos citados en el orden dado, separados por un espacio, y se normalizan los espacios (varios → uno; sin espacios al principio ni al final). El `valor` se normaliza igual.
2. El `valor` tiene que aparecer **tal cual** dentro de esa unión. Si va pegado a otros caracteres, estos no pueden ser letras ni dígitos: `0.25` vale dentro de `H=0.25M`, porque la `M` de metros se admite como sufijo de unidad (ver 3); `1` no vale dentro de `36∅1"`.
3. Excepción de límite: admite como sufijo de unidad pegado solo `M` o `m`, y solo detrás de un número (`H=0.25M`, `e=0.50m`).
4. `∅` y `Ø` se consideran el mismo carácter, tanto al comparar como al guardar el valor tal como lo citó Claude. Fuera de eso, ni mayúsculas, ni prima, ni puntuación se normalizan.
5. Un dato que no cumple la regla → se guarda sin valor (`"pendiente de verificar"`) y se abre una duda `IA:` que dice qué propuso Claude y qué dice el texto citado.
6. La fuente de cada valor guarda: página, hoja, `n` citados, texto literal de cada cita y la unión de sus bbox.

### 5.1 Evidencias (v4, decisión 8; A3d)
Un dato puede traer la clave opcional `evidencia`. Si no la trae, es `"literal"` y todo lo de arriba sigue igual. Para cualquier evidencia:
- Sin evidencia válida, el dato no tiene valor.
- Nada nace `confirmado`.
- Un dato con `evidencia` desconocida, o que no trae las claves de su evidencia, deja **la hoja rechazada**, como una cita mala.
- `id_elemento`, `nivel_rango` y `ejes` solo admiten `literal` o `partes`: la identidad del elemento no sale de una lectura visual ni de una conversión. Si traen `zona` o `conversion`, la hoja se rechaza.

| `evidencia` | Claves del dato | Qué comprueba el importador | Qué guarda |
|---|---|---|---|
| `"literal"` (a) | `valor`, `citas` | La regla 1–4 de arriba. | El trozo literal y la fuente del punto 6. |
| `"partes"` (b) | `valor`, `partes: [{"valor", "citas"}…]` (2 o más), sin `citas` propias | Cada parte se ancla por la regla literal en **sus** citas. El `valor` del dato, con los espacios colapsados, es igual a los literales de las partes unidos por un espacio. | Esa unión. La fuente lleva cada parte con sus citas, textos y bbox, y la unión de todas las bbox. |
| `"zona"` (c) | `valor` (la lectura), `zona: [x0,y0,x1,y1]` en pt del marco visual, `citas` opcionales | `x0<x1`, `y0<y1` y la caja cabe en la hoja (`ancho_pt`, `alto_pt` de `textos.json`). | El valor leído con la fuente `{"zona", "lectura", "citas"}`. Además abre **siempre** una duda `IA: revisión visual: …` con la zona y la lectura. |
| `"conversion"` (d) | `conversion: {"regla", "entradas": [{"valor", "citas"}…]}` y `valor` opcional | Cada entrada se ancla por la regla literal. El **programa** aplica la regla a los literales anclados. Si la IA puso `valor` y no es igual al resultado, no hay valor y se abre una duda. | El resultado del programa. La fuente lleva la regla, las entradas (literal, citas, textos, bbox) y la unión de las bbox. |

Reglas de conversión del programa (`esquema.REGLAS_CONVERSION`). Son las únicas, cada una con pruebas, y fuera de ellas no hay conversión:
- **`decimales_2`:** 1 entrada, un número decimal con punto, con 0, 1 o 2 decimales. Lo devuelve con 2 decimales, rellenando ceros (`1.5` → `1.50`). Si trae más de 2 decimales no se redondea: la regla falla.
- **`cm_a_m`:** 1 entrada, un entero de centímetros, con o sin `cm` pegado. Lo devuelve en metros con 2 decimales (`60` → `0.60`, `125cm` → `1.25`).
- **`suma`:** 2 o más entradas, todas números decimales con punto. Las suma con aritmética decimal exacta y las da con el mayor número de decimales de las entradas (`0.30` + `1.20` → `1.50`).

Si la regla no existe, una entrada no se ancla o la regla falla, el dato queda sin valor y se abre una duda `IA:` que dice qué falló.

Además, la fuente de todo valor importado lleva `lector`, copiado de la propuesta (A4-paquete: el modelo o proveedor que la hizo).

## 6. Cómo se guarda (A3)
- Clave: `(proyecto_id, id_elemento, nivel_rango, ejes)`, como hoy. El `nivel_rango` se guarda **como está impreso** (`FUNDACIONES @ E-3`, `NPT= 3.60`). La expansión a niveles la hace el backend con las equivalencias del usuario, nunca Claude.
- **EJES (D11):** en columnas, muros y pórticos que el detalle no ubica, va `"pendiente de verificar"`. En losas va siempre `—`. Claude **nunca** deduce el cruce mirando la planta. Un tramo de pórtico sí lo trae impreso (eje del pórtico + ejes de los extremos) y se escribe con `formatear_campo_ejes('tramo_portico', …)`.
- Todo pasa por `validador_diseno.validar_elemento_diseno` y **todo queda `pendiente_de_verificar`** (0 campos `confirmado`).
- Fuente: `extraido_por = "IA:claude-code"`, sha256, página, hoja y la fuente de cada valor (§5.6).
- **Doble lectura (decisión 3):** en un campo que ya escribió el extractor T6n (tablas de aplicación), A3 no escribe nada. Compara: si difiere, abre una duda `IA:`; si coincide, anota una comprobación «coincide con T6n».
- Antes de importar, el sha256 de `propuesta.json` se compara con el de `textos.json` y con el del vectorial vigente. Si alguno es distinto, la hoja no se carga.
- Importar dos veces la misma propuesta no cambia nada (idempotente). Un campo `confirmado` nunca se toca.
- **Reutilización del extractor (aprobada por el Director el 19/11):** `_escribir_elemento` y `_abrir_duda` reciben un parámetro opcional `origen`.
  - Sin el parámetro, nada cambia: ni el texto, ni la fuente, ni la auditoría.
  - Las pruebas actuales del extractor pasan sin tocarlas.
  - Se mantiene la regla de choque: una fila de otro extractor, o ya confirmada, nunca se sobrescribe, tampoco con origen IA.
  - Va en un commit aparte, «extractor: parámetro origen opcional».
  - A3 lo llama con `origen="IA:claude-code"` (fuente) y `"IA:"` (prefijo de duda).
  - `_cerrar_dudas_viejas` no se toca: en esta versión, las dudas `IA:` se cierran en la Mesa, no al reimportar.

## 7. Campos por tipo (`campos`, en el orden de D10)
Las claves se fijan en cada apartado de la skill (A4a–A4d) y se añaden aquí cuando se escriban.
- **COLUMNA (A4a):** `b_m` (lado horizontal de la sección dibujada), `h_m` (lado vertical), `acero_longitudinal`, `estribos` (puede citar dos textos); `seccion` solo si viene en un único texto `bXh`. Nombres alineados con `test_validador_diseno.py`. Detalle en `.claude/skills/extraer-plano/referencias/columnas.md`.
- **LOSA (A4b):** `H` y `tipo_losa` (como enlace con la tabla de aplicación). Las dimensiones y el acero salen de la tabla que ya lee T6n (doble lectura).
- **MURO H.A. (A4c):** `espesor`, `longitud`, `borde_<k>.longitud`, `borde_<k>.acero`, `borde_<k>.estribos` (k = 1, 2, 3, rotulados en el recorte de DETALLE), `alma.ASV`, `alma.ASH`, `alma.ganchos`.
- **PORTICO, por tramo (A4d):** se fija en A4d (acero superior e inferior, adicionales con su largo, zonas de estribos, llamada de sección como enlace).
- **Fundaciones (D12):** solo `espesor` de la platea y la tabla de f'c. Los *drops* van a `dudas_hoja`.
