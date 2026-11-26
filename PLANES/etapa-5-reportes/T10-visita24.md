# Etapa 7 · T10 — f'c, altura y barras por cara de C1 y C3 `FUNDACIONES @ E-3`
Líder de la Fase A, 24/11/2026. Rama `claude/etapa5-fase-a-3da668`, sin push. Plano vigente sha256 `59c6be81…6eda21` (solo lectura).

## Resultado

| Campo (`datos_diseno_json`) | Fila STP | C1 | C3 | Evidencia | Estado |
|---|---|---|---|---|---|
| `fc` | b | pendiente de verificar | pendiente de verificar | — (duda con las dos fuentes) | pendiente + duda `IA:` |
| `altura_m` | e | pendiente de verificar | pendiente de verificar | — | pendiente + duda `IA:` |
| `barras_cara_x` | i | `6` | `6` | `zona` (conteo en el vectorial) | pendiente + duda de revisión visual |
| `barras_cara_y` | j | `14` | `16` | `zona` (conteo en el vectorial) | pendiente + duda de revisión visual |

Se usaron los nombres que propuso el Director; la Fase A no tenía otros. Nada se confirmó.

## f'c (fila b)
Las dos fuentes coinciden para este tramo:
- **p2, «TABLA DE RESISTENCIAS UTILIZADAS»:** fila «A) COLUMNAS Y MUROS DE HORMIGON», «FUND@E10» → «350» (columna «CONCRETO F'C(Kg/cm2)»).
- **p24, «CALIDAD DE MATERIALES»:** «FUND.@ E3» → «350 Kg/cm2».

No se cargó como valor, por dos motivos:
1. Las dos citas están en otras hojas (p2 y p24), no en la p14 del elemento. Un enlace entre hojas nunca da valor (contrato §4), y el importador solo ancla a textos de la misma hoja.
2. Las tablas no cortan los tramos de arriba igual: la p2 usa FUND@E10 y E11@TECHO; la p24 usa E3 @ E10, E10 @ E16 y E16 @ TECHO. Además, en la p24 la fila «COLUMNAS» queda a la altura de «E10 @ E16» → 280.

La duda propone **350 Kg/cm2** para que Steven lo confirme en un clic.

## Altura H (fila e)
- El plano no imprime la altura de la columna ni la del entrepiso de S-2.
- La planta de S-2 (p24) solo trae niveles NPT (`NPT= -5.45`, `NPT= -4.30`…), y la p5 solo dice «H = ALTURA DE LA COLUMNA».
- No se restaron cotas: queda pendiente, con una duda, hasta que Steven decida si se calcula.

## Barras por cara (filas i y j)
**Cómo se contó:** sobre los objetos del vectorial, en la sección dibujada del cuadro de columnas (p14), no mirando la imagen.
- **C1:** 36 círculos rellenos del mismo diámetro (4.9 pt), todos en el perímetro. Hay 6 en cada cara horizontal (lado b = 0.60) y 14 en cada cara vertical (lado h = 1.50).
- **C3:** 40 círculos, con 6 y 16 por cara.
- **Comprobación:** las esquinas cuentan en las dos caras, así que el total es 2·(i+j)−4. Para C1 da 2·(6+14)−4 = 36, igual al rótulo `36∅1"` (texto 3). Para C3 da 2·(6+16)−4 = 40, igual a `40∅1"` (texto 166). La suma i + j sola (20 y 22) no es el total.

**Por qué evidencia `zona`:** el importador solo ancla a textos, no a círculos.
- El valor entra, pero queda pendiente con la duda «revisión visual» y la zona del recorte: C1 `[215, 105, 392, 540]`, C3 `[135, 1205, 310, 1640]`.
- El conteo y su comprobación quedan en `comprobaciones` de la propuesta.

**Convención:**
- `barras_cara_x` = barras de una cara paralela al lado b (horizontal en el dibujo);
- `barras_cara_y` = las de una cara paralela al lado h;
- con esquinas incluidas.

Si el STP pide otra cosa en x-x / y-y (por ejemplo, sin esquinas), T4 lo dirá.

## Importación
- **Propuesta:** la p14 de T1 con los 4 campos nuevos en los 2 elementos `FUNDACIONES @ E-3`.
- **BD:** copia nueva de la BD de T1.
- **Resultado:** 2 actualizados, 6 sin cambios y 8 dudas `IA:` nuevas (2 de f'c, 2 de altura, 4 de revisión visual). Reimportar no cambia nada (8 sin cambios).
- **Sin cambios:**

  | BD | sha256 |
  |---|---|
  | copia de T1 | `835e04b2…` |
  | real | `eba26967…` |

- **Dropbox:** solo se leyó.

## Dónde están los datos
`C:\Users\Steve\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_d03e8098-a6a7-4ac9-a8d0-1a6ecc5cc64f\t10-visita24\`:
- la copia de la BD: `bd\catdic_copia_t10.db`;
- la hoja: `p14\` (`propuesta.json`, `importacion.json`, textos);
- el script: `t10.py`.

## Cupo
- Semanal: de 59 % a 63 % (compartido con las demás sesiones).
- Ventana de 5 h: 27 %.
