# Paquete de visita v2 (CATDIC Campo v11 → CATDIC Informes)

Etapa 7 (T2 + T3). Amplía el v1 (`PLANES/paquete-visita-v1.md`): **todo lo del v1 sigue igual**; el v2 solo agrega
las mediciones guiadas de OBRA por elemento. Decisión de Steven del 23/11/2026:

- una casilla de OBRA **vacía** significa que esa fila es **conforme** (en OBRA va el valor del plano, §4.5);
- un elemento con estado **Pendiente** no entra como conforme: queda **en revisión** con una duda.

Informes carga v1 y v2. Campo v11 exporta siempre v2.

## Cambios en la estructura

```json
{
  "formato": "catdic-paquete-visita",
  "version": 2,
  "generado_por": "CATDIC Campo (campo-v11)",
  "...": "lo demás igual que v1",
  "elementos": [
    {
      "orden": 1,
      "tipo": "COLUMNA",
      "id": "C1",
      "...": "nivel, ejes, ejes_texto, texto_libre, mediciones, estado, descripcion y fotos igual que v1",
      "estado": "Conforme",
      "obra": {
        "fila_stp": "col",
        "textos": { "k": "12", "h": "3/8\"" },
        "medidas_acero": { "c": "0.32", "d": "0,42" }
      }
    }
  ]
}
```

### `elementos[].obra`

| Clave | Tipo | Qué es |
|---|---|---|
| `fila_stp` | `"col"`, `"muro"`, `"viga"`, `"losa"` o `""` | Juego de filas que Campo mostró, según el tipo (tabla de abajo). `""` para tipos sin STP-MIVED (zapata, platea, escalera, otro): entonces `textos` y `medidas_acero` van vacíos. |
| `textos` | `{letra: texto}` | Lo que el técnico escribió en las filas de texto de la columna `2. IMFORMACION ARMADO EN OBRA`. Solo las casillas con texto; **una casilla vacía no se exporta** (vacío = conforme). |
| `medidas_acero` | `{letra: texto}` | Medidas dimensionales tomadas **sobre el acero**, en metros, tal como se escribieron (`"0.32"` o `"0,32"`). Solo las casillas con texto. Informes suma el recubrimiento (§4.5); Campo no calcula nada. |

- Las letras son las de `ROTULOS` en `BACKEND/generators/stp_mived.py`. Una letra que no es del juego de `fila_stp`
  es un error del paquete (va a duda, no se usa).
- Un elemento v2 **sin** la clave `obra` no se toma como conforme: Campo v11 siempre la exporta, así que falta por un
  error; se trata como `fila_stp` que no coincide (duda `elemento_visita:pNNN:obra`, nada conforme por omisión).
- `mediciones` (texto libre) sigue existiendo y sigue siendo solo una nota: nunca llena OBRA.
- `estado` es `Pendiente`, `Observación` o `Conforme` (los del selector de Campo). Vacío se trata como `Observación`;
  cualquier otro valor se trata como `Pendiente` (con su duda que lo explica).

### Filas por tipo (las mismas del STP-MIVED)

`fila_stp` sale del tipo con la misma regla que `stp_mived._tipo_de_fila`:
COLUMNA → `col`; MURO H.A. y MURO DE CONTENCION → `muro`; VIGA y PORTICO → `viga`; LOSA → `losa`; el resto → `""`.

| `fila_stp` | `medidas_acero` (metros, sobre el acero) | `textos` |
|---|---|---|
| `col` | `c` Dim LX, `d` Dim LY | `a b e f g h i j k m n o q` |
| `muro` | `b` Espesor muro | `a c d e f g h i j k` |
| `viga` | `c` Ancho, `d` Altura | `a b e f g h i j k m n o q` |
| `losa` | `b` Espesor losa | `c d e f g h i j k m n o p` |

- Las letras dimensionales son las de `DIMENSIONALES` del generador; esas no se piden como texto.
- La cuantía (`p` en col y viga) **no se pide**: la calcula el programa (§4.6, error 12).
- Los rótulos que muestra Campo son los de `ROTULOS`. Prohibido «CORRIDO» (error 9).

## Lo que hace CATDIC Informes al cargar un v2

Además de los 10 pasos del v1:

1. `fila_stp` se recalcula desde el tipo validado; si no coincide con la del paquete, `obra` no se usa y se abre una
   duda `elemento_visita:pNNN:obra`.
2. Cada medida se valida: número positivo en metros, con punto o coma decimal (`0.32`, `0,32`, `.32`). Cualquier otra
   cosa (unidades, `32 cm`, `3/8`, texto, negativo, > 30 m) **no se adivina**: esa letra no se escribe y se abre una
   duda `elemento_visita:pNNN:obra` con el valor literal.
3. Se llena `elementos_visita.medidas_acero_campo_json` con el contrato que ya lee `procesador_cola.py`:

```json
{
  "c": 0.32, "d": 0.42,
  "obra": { "k": "12", "h": "3/8\"" },
  "conforme_por_omision": ["a", "b", "e", "f", "g", "i", "j", "m", "n", "o", "q"],
  "estado_campo": "Conforme",
  "origen": "paquete_v2"
}
```

   - `conforme_por_omision`: las letras del juego que llegaron vacías (texto y medidas). El generador pone en OBRA
     el valor del plano para esas letras. Una letra con medida ilegible **no** va aquí (va a duda).
   - Estado `Pendiente`: `conforme_por_omision` va **vacío** (nada entra como conforme), `estado_campo` es
     `"Pendiente"` y se abre la duda `elemento_visita:pNNN:pendiente` («elemento en revisión: el técnico lo dejó
     Pendiente»). El elemento no se procesa hasta resolverla.
4. Un v1 no toca `medidas_acero_campo_json` (igual que hoy).
5. Recarga idempotente: el mismo paquete no cambia nada; si cambió `obra`, la fila se actualiza y se audita.
