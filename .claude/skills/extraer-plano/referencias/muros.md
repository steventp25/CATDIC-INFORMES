# Muros (A4c) — detalle de muro H.A. por tramo de rango y muro de contención típico

Casos de referencia (Etapa 7 · T1, 23/11/2026; solo lo que pidió la visita 24 de Terra Living):
- pág. 16 (hoja 15/36), «MURO MH3»: muro recto, 3 tramos.
- pág. 17 (hoja 16/36), «MURO MH2»: muro en L, 4 tramos.
- pág. 8, «DETALLE TIPICO DE MURO DE CONTENCION PERIMETRAL».

Todos los valores se anclaron a la primera (0 sin ancla). Se miraron con recortes de 100–120 ppp.

## Cómo es la hoja
- Cada muro (MH2, MH3…) tiene un **dibujo en planta por tramo de rango**, con el rango impreso debajo (`FUNDACIONES @ E-1`, `E-2 @ E-8`). El ID va una vez, como título (`MURO MH2`), y se cita en todos sus tramos.
- En cada dibujo hay:
  - **elementos de borde** (zonas confinadas con estribos) en los extremos y en las esquinas;
  - **el alma** entre ellos, con `ASV`, `ASH` y los ganchos.
- Los rangos de un muro no tienen por qué coincidir con los de otro (MH2: `E-1 @ E-2`, `E-2 @ E-8`; MH3: `E-2 @ E-9`). Cada uno se copia tal cual.
- **No hay ejes.** EJES va siempre `null` con su duda (D11, A1 §6.2).

## Un elemento por tramo
`tipo_elemento: "MURO H.A."`.

| Dato | Qué es | Ejemplo (valor ← texto citado) |
|---|---|---|
| `campos.espesor` | la cota del grueso del muro | `0.40` |
| `campos.longitud` | la cota total del muro | `1.80`. En un muro en L, `null` (ver abajo) |
| `campos.borde_<k>.longitud` | la cota del largo del borde k | `0.50` |
| `campos.borde_<k>.acero` | el rótulo de las barras del borde. Si son varios rótulos, se citan **todos y en orden** | `4Ø1" 22Ø3/4" 2Ø1"(ESQUINA) +2Ø3/4"(CENTRO)` |
| `campos.borde_<k>.estribos` | estribos con su separación | `8EST.+4GAN. Ø3/8"@0.10` ← `8EST.+4GAN.` + `Ø3/8"@0.10` |
| `campos.alma.ASV` | la parte con diámetro y separación del rótulo `ASV:` | `Ø1/2"@0.10` |
| `campos.alma.ASH` | ídem con `ASH:` | `Ø3/8"@0.10` |
| `campos.alma.ganchos` | los tres textos de los ganchos | `GAN. Ø3/8" ASV: @0.20 ASH: @0.20` |

**Numeración de los bordes (k).** El plano no los numera. La numeración la fija la lectura, la misma para todos los tramos del muro, y se anota en `comprobaciones`. Se usó:
- **Muro recto:** borde_1 es el extremo de arriba en el dibujo y borde_2 el de abajo.
- **Muro en L:** borde_1 es el extremo del ala horizontal, borde_2 la esquina y borde_3 el extremo del ala vertical.

## Muro de contención típico
`tipo_elemento: "MURO DE CONTENCION"`. El detalle es **típico**: corta todos los sótanos y no trae ID ni rango.
- `id_elemento`: el título literal, `MURO DE CONTENCION PERIMETRAL` ← `DETALLE TIPICO DE MURO` + `DE CONTENCION PERIMETRAL`. Siempre lleva una duda que pida a Steven confirmar a qué muro de la planta aplica.
- `nivel_rango`: el rótulo del nivel que se pidió (`SOTANO S - 2`), citado.
- `campos.espesor`: la cota del grueso del muro. Es la horizontal pegada al muro, no las verticales de las rampas.
- `campos.longitud`: siempre `null`, porque el detalle no la da.
- `campos.alma.ASV` y `campos.alma.ASH`: `null` si los rótulos no dicen la dirección. En Terra Living hay dos `∅1/2"@0.10` por tramo sin decir cuál es cuál.

## Trampas que ya aparecieron
1. **Muro en L con dos longitudes** (`3.85` el ala horizontal, `3.80` la vertical). `longitud` va `null`, con una duda que cite las dos.
2. **Esquina con dos largos distintos** (`1.00` y `0.99`). `borde_k.longitud` va `null` con duda. Si los dos largos son iguales, se citan los dos textos.
3. **Notas de acero parcial** (`8Ø1" COMPREDIDAS ENTRE E1/E2`). No se mezclan con el rótulo del borde. Van como duda del elemento.
4. **Notas de modificación** («AJUSTE DE INDICACION ESPESOR… PLANO ANTERIOR»): van a `dudas_hoja`. El valor del dibujo se propone igual.
5. **Despieces de estribos dibujados aparte.** Sus cotas (`0.31`, `0.26`, `0.12`) no son del muro y no se citan.
