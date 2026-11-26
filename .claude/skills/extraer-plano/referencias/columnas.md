# Columnas (A4a) — cuadro de columnas por tramo de rango

Caso de referencia: Terra Living, pág. 14 (hoja 13/36), «COLUMNA C1, C2, C3»: 12 tramos, 60 valores. En el reconocimiento A1 todos estaban anclados y se comprobaron con recortes.

## Cómo es la hoja
- Cada columna (C1, C2…) tiene un **dibujo por tramo de rango**. Cada dibujo es una sección con las barras, el despiece del estribo al lado y, debajo, el rango impreso (`FUNDACIONES @ E-3`, `E-3 @ E-8`, `E-8 @ E-12`, `E-12 @ TECHO`).
- El ID (`C1`) suele estar una sola vez, como título del grupo de tramos (`COLUMNA C1`). Se cita ese mismo texto en todos los tramos de esa columna.
- **No hay ejes.** El cuadro vale para todos los cruces donde la planta pone `C1`.

## Un elemento por tramo
`tipo_elemento: "COLUMNA"`. La clave es `id_elemento` + `nivel_rango`: los 4 tramos de C1 son 4 elementos. Nunca juntes tramos ni copies valores de un tramo a otro, aunque se repitan: cada tramo cita sus propios textos.

| Dato | Qué es | Ejemplo (valor ← texto citado) |
|---|---|---|
| `id_elemento` | el ID impreso | `C1` ← `COLUMNA C1` |
| `nivel_rango` | el rango impreso debajo del dibujo, tal cual | `FUNDACIONES @ E-3` |
| `ejes` | siempre `null` | duda: `El cuadro de columnas no da ejes (D11).` |
| `campos.b_m` | la cota del lado **horizontal** de la sección, tal como está dibujada | `0.60` |
| `campos.h_m` | la cota del lado **vertical** de la sección dibujada | `1.50` |
| `campos.acero_longitudinal` | el rótulo de las barras | `36∅1"` |
| `campos.estribos` | el rótulo del estribo, con su separación | `9 EST. ∅3/8" @0.10` ← `9 EST. ∅3/8"` + `@0.10` |

- No ordenes b y h por tamaño: van según el dibujo. Si no se ve qué cota es de qué lado, deja los dos `null` con una duda.
- Si la sección solo viene en un texto del tipo `0.60X1.50`, propón `campos.seccion` con ese texto literal y deja `b_m` y `h_m` en `null`, con la duda «sección impresa como b X h en un solo texto».
- Los estribos se escriben como estén impresos, con lo que traigan (`4 EST.+GAN.`, `9 EST.+GANCHO`). Si la separación está en otro texto, cítalo también.

## Trampas que ya aparecieron
1. **Cotas del estribo junto a las de la sección.** El despiece del estribo trae sus propias medidas (`1.42`, `0.52`, `0.14`) al lado de las de la sección (`1.50`, `0.60`). Las de la sección acotan el **contorno de concreto**; las del estribo, el estribo, que es más pequeño. Mira el recorte antes de elegir. Si dudas, `null` con duda.
2. **Rango con espacios variables** (`E-3 @ E-8` frente a `E-3@E-8`): copia los espacios tal como estén. El anclaje solo colapsa espacios repetidos, no los inventa.
3. **Notas de modificación**, por ejemplo una nota en C3 que dice que la dimensión «pasa de 1.20 M a 1.50 M atendiendo a plano anterior». Van a `dudas_hoja` citando todos sus textos. El valor del dibujo **se propone igual**, porque es lo impreso; la nota hace que Steven lo revise.
4. **Tramos de distinto rango en la misma columna.** C2 empieza en `FUNDACIONES @ E-2`, no en `E-3`. No supongas que todas las columnas tienen los mismos rangos.

## Comprobaciones que sí puedes hacer (sin inventar)
- Contar las barras dibujadas en la sección del recorte y compararlas con la cantidad del rótulo (`36∅1"` → 36 puntos). Va como `comprobaciones` con `resultado: "cuadra"` o `"no cuadra"`. Si no cuadra, abre además una duda en el elemento.
- Que cada tramo tenga sus 5 datos. Lo que falte va en `null`, con una duda que diga qué falta.
