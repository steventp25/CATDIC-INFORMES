# Etapa 7 · T6 — Qué dice el plano de Terra Living sobre sótanos (S-n) y entrepisos (E-n)

**Estado: PROPUESTA para Steven. No se cargó nada en la tabla `equivalencias_nivel`.** La equivalencia la escribe el usuario (`PUT /api/proyectos/{id}/equivalencias-nivel`); el código nunca la deduce.

## Fuente (solo lectura)
- Archivo: `PLANOS ESTRUCTURALES TERRALIVING.pdf`, sha256 `59c6be8107d5b01c857659078337983819e87027217d6f82e8ba473ba46eda21`, 41 páginas (el mismo del manifiesto de T1).
- Texto extraído con PyMuPDF a una carpeta temporal; el PDF no se copió al repo. Las páginas son las del PDF (1 = primera).

## Resultado corto
**No hay una tabla ni un corte impreso que diga «S-2 = E-n».** Lo único que relaciona sótanos con entrepisos es un corte del muro de contención que ubica `E-1` en el nivel de calle, con los sótanos por debajo. A partir de eso se puede proponer (como hipótesis, sin evidencia directa) qué rango cubre S-2, pero Steven tiene que confirmarlo.

## Lo que está impreso

### 1. Página 8 (hoja «07»): corte del detalle típico de muro de contención perimetral
Bloque «DETALLE TIPICO DE MURO DE CONTENCION PERIMETRAL, ESC. 1:40, 3, E-7». Rótulos de nivel, con su posición vertical en la hoja (y crece hacia abajo; hoja de 2592 × 1728 pt):

| y (pt) | Texto impreso |
|---|---|
| 337 | `E-1 Ó  NIVEL DE CALLE` |
| 436 | `SOTANO S -S` (así impreso; no se interpreta) |
| 528 | `SOTANO S -1` |
| 616 | `SOTANO S - 2` |
| 714 | `SOTANO S -3` |
| 806 | `SOTANO S -4` |
| 894 | `SOTANO S - 5` |
| 988 | `SOTANO S - 6` |
| 1084 | `PLATEA DE FUNDACION` (con `TERRENO NATURAL` junto a los niveles) |

Lo que dice con certeza: `E-1` es el nivel de calle, los sótanos S-1…S-6 están por debajo, en ese orden, y el rótulo de S-2 se imprime con espacios (`SOTANO S - 2`), igual que el rango del muro de contención guardado por T1.
Lo que **no** dice: a qué rango de columnas o muros pertenece cada sótano.

### 2. Páginas 14 a 17 (hojas «13» a «16»): rangos impresos de columnas y muros H.A.
Los rangos que T1 guardó como `nivel_rango`, tal como están impresos:
- Columnas (C1, C3; pp. 14-15): `FUNDACIONES @ E-3`, `E-3 @ E-8`, `E-8 @ E-12`, `E-12 @ TECHO`.
- Muros H.A. (pp. 16-17): MH3 `FUNDACIONES @ E-2`, `E-2 @ E-9`, `E-9 @ TECHO`; MH2 `FUNDACIONES @ E-1`, `E-1 @ E-2`, `E-2 @ E-8`, `E-8 @ TECHO` (y en la p. 16 también `E-1 @ E-8`, `E-2 @ E-8`).

### 3. Otra numeración de E-n en las mismas hojas (no confundir)
Las plantas (pp. 7-13 y 20-33) traen una leyenda «CALIDAD DE MATERIALES · CONCRETO F'c · ELEMENTO ESTRUCTURAL» (en la p. 24, `PLANTA ESTRUCTURAL DE SOTANO S2`, en torno a x 1710-1880, y 1440-1523) con otros cortes: `FUND.@ E3`, `E3 @ E10`, `E10 @ E16`, `E16 @ TECHO` (sin guiones y con otros números). Son rangos de resistencia del hormigón, no los de los cuadros de columnas; no se usaron para nada.

### 4. Plantas por sótano
Los títulos impresos son `PLANTA ESTRUCTURAL DE SOTANO S6` (p. 20), `S5` (p. 21), `S4` (p. 22), `S3` (p. 23), `S2` (p. 24), `S1` (p. 25), `PLANTA ESTRUCTURAL PRIMER NIVEL` (p. 26), y después `NIVEL 2`, `NIVEL 3`, `NIVEL 4@8`, `NIVEL 9@17`, `NIVEL 18`. Estos títulos usan «NIVEL n», no «E-n».

## Propuesta (hipótesis; Steven decide)
Si `E-1` es el nivel de calle (p. 8) y los sótanos están por debajo, un rango que empieza en `FUNDACIONES` abarca todos los sótanos hasta su `E-n` final. Entonces, para S-2:

| Nivel de la visita | Rango impreso propuesto | Cubre |
|---|---|---|
| S-2 | `FUNDACIONES @ E-3` | C1 y C3 (visita 24) |

**Qué no está probado:** que `FUNDACIONES @ E-3` incluya S-2 es una inferencia de la lectura del corte de la p. 8; el plano no lo dice con esas palabras. Si Steven conoce otra relación (por ejemplo, otra numeración de E-n entre sótanos y torre), la que él escriba manda.

## Limitación del diseño de la tabla (hay que decidirla)
La tabla pedida guarda **un solo rango por nivel de visita**. Pero cada familia de elemento tiene sus propios rangos: en S-2, las columnas C1/C3 caen en `FUNDACIONES @ E-3`, MH2 en `FUNDACIONES @ E-1` y MH3 en `FUNDACIONES @ E-2`. Con una sola fila `S-2 → FUNDACIONES @ E-3`, MH2 y MH3 nunca cruzan por la tabla y el procesador abre la duda «la equivalencia definida no corresponde a ningún rango de MH2». Opciones para una tarea posterior (no se hicieron aquí porque el plan fija «una sola equivalencia por obra»):
1. Equivalencia por familia (columna / muro) además de por nivel.
2. Equivalencia por ID de elemento.
3. Permitir varios rangos por nivel, aceptando el que coincida con el ID.

Mientras tanto, el muro de contención (`SOTANO S - 2`) cruza sin tabla, por la normalización exacta.
