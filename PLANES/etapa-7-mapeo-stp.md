# Etapa 7 · T4 — Mapeo de filas del STP-MIVED (propuesta para Steven)

Estado: **PROPUESTA, sin confirmar** (`BACKEND/generators/mapeo_stp.json`, `"confirmado": false`).
Mientras no se confirme, el STP solo se genera como **BORRADOR** (portada con la marca `BORRADOR — mapeo sin confirmar`),
solo en la carpeta de pruebas (`CATDIC_SALIDA_PRUEBAS`); si esa variable no está definida, no se genera y queda una duda.
Nunca escribe en `INFORMES\2.DATA PROCESADA`.

Evidencia: los STP entregados de la visita 24 (S2 completivo 06/11/2026, «S2C») y S3 completivo («S3C»), donde la columna OBRA
repite el valor del plano (conforme, §4.5). Campos de datos de la Fase A: `columnas.md`, `muros.md` y la copia de prueba de T1
(valores leídos de los planos, todos aún `pendiente_de_verificar`). Los valores citados son los impresos en esos informes.

Estados: **mapeada** (correspondencia directa, ya en el JSON) · **sin mapear** (no hay campo o no es directo) ·
**derivación propuesta** (se podría derivar de un campo, pendiente de que Steven la apruebe) · **Capa 3** (la calcula el programa) ·
**§4.5** (sale de la tabla de recubrimientos, no del plano).

## Columna (`fila_stp: col`)

Ejemplos: C1 EJE D-4 (S2C pág. 5) y C3 EJE B-4 (S2C pág. 9). Campos del plano: tramo `FUNDACIONES @ E-3` de C1 y C3.

| Fila | Rótulo | Campo de `datos_diseno_json` | Ejemplo C1 / C3 (informe) | Estado |
|---|---|---|---|---|
| a | Tipo de Pórtico | — | vacío / vacío | sin mapear (no se pide) |
| b | Resist. esperada | — (f'c está en notas generales, no en el cuadro) | 350 / 350 | sin mapear |
| c | Dim LX | `b_m` | 0.60 / 0.60 (plano: 0.60 / 0.60) | **mapeada** (medida) |
| d | Dim LY | `h_m` | 1.50 / 1.20 (plano: 1.50 / 1.50) | **mapeada** (medida); ver pregunta 1 |
| e | Altura col. H | — (no sale del cuadro) | 2.95 / 2.95 | sin mapear |
| f | Espac. estribos nodos | de `estribos` | ∅3/8"@0.10 | derivación propuesta, pendiente de Steven |
| g | Espac. estribos paño central | de `estribos` | ∅3/8"@0.10 | derivación propuesta, pendiente de Steven |
| h | Diám. Est. | de `estribos` | 9 EST. ∅3/8" / 10 EST. ∅3/8" | derivación propuesta, pendiente de Steven |
| i | Eje x-x | — (conteo por cara del dibujo) | 6-∅1" | sin mapear |
| j | Eje y-y | — | 14-∅1" / 16-∅1" | sin mapear |
| k | Total barras | de `acero_longitudinal` | 36 / 40 | derivación propuesta; el generador la comprueba contra la suma de `barras`, no se copia |
| m | Diám. barras nudos | de `acero_longitudinal` | ∅1" | derivación propuesta, pendiente de Steven |
| n | Diám. barras internas | de `acero_longitudinal` | ∅1" | derivación propuesta, pendiente de Steven |
| o | Solape | — | ZONA CENTRAL / 1.08 | sin mapear |
| p | Cuantía | — | 0.0203 / 0.0282 | **Capa 3** (calculada, error 12: nunca se copia) |
| barras | lista [[n, diámetro]] para la cuantía | `acero_longitudinal` | `36∅1"` → [[36, '1"']] | **mapeada** con conversión exacta (abajo) |

Conversión de `barras` (en el programa, `convertir_barras`): solo si el texto ENTERO es `<n>∅<diámetro>"` (acepta `∅ Ø ø` y las
comillas `" ″ ” “`); `36∅1"` → `[[36, '1"']]`. Cualquier otra cosa (varios grupos, texto extra, `pendiente de verificar`) no se
convierte y abre una duda `diseno:pNNN:barras` con el texto impreso. Los tramos de la copia T1 cuadran (`36∅1"`, `28∅1"`, `18∅1"`, `14∅1"`, `40∅1"`).

## Muro (`fila_stp: muro`; sirve a MURO H.A. y a MURO DE CONTENCION)

Ejemplos: MH2 (S2C pág. 3), muro perimetral eje 4 A-D (S2C pág. 7), MH3 (S2C pág. 11). Plano: `muros.md` y copia T1.
Los dos tipos comparten fila y entrada de mapeo (el procesador no los distingue); los campos comunes son `espesor`, `longitud`,
`alma.ASV` y `alma.ASH`. Las claves del plano llevan el punto en el nombre (`alma.ASV`).

| Fila | Rótulo | Campo | Ejemplo en el informe | Valor en el plano (T1) | Estado |
|---|---|---|---|---|---|
| a | Resistencia esperada | — | 350 (MH2, MH3) / 240 (perimetral) | — | sin mapear |
| b | Espesor muro | `espesor` | MH2 0.50 / perimetral 0.25 / MH3 0.40 | MH2 `FUNDACIONES @ E-1` 0.50; contención 0.25; MH3 0.40 | **mapeada** (medida); coincide en los tres |
| c | Longitud X | `longitud` | MH2 `3.80 + 3.85` / perimetral 18.45 / MH3 1.80 | MH2 y contención: `pendiente de verificar`; MH3 1.80 | **mapeada**: coincide solo en MH3 (1.80); en MH2 el plano trae dos alas y el campo queda pendiente (no se rellena); el perimetral no tiene longitud en el detalle típico |
| d | Altura | — (el detalle no la da; S3C la deja vacía) | 2.95 | — | sin mapear |
| e | Calzos | — (comprobación de obra) | SI | — | sin mapear |
| f, g | Recub. Min / Max | — | 0.04 (MH2, MH3) / 0.075 (perimetral) | — | §4.5 (no sale del plano) |
| h | As Vert. Interno | `alma.ASV` | MH2 `∅1/2"@0.10` | `Ø1/2"@0.10` | **mapeada** (propuesta); ver pregunta 2 |
| i | As Vert. Externo | `alma.ASV` | MH2 `∅1/2"@0.10` | `Ø1/2"@0.10` | **mapeada** (propuesta); ver pregunta 2 |
| j | As Hor. Interno | `alma.ASH` | MH2 y MH3 `∅3/8"@0.10`; perimetral `∅1/2"@0.10` | `Ø3/8"@0.10` (MH2, MH3); contención: pendiente | **mapeada** (propuesta); ver pregunta 2 |
| k | As Hor. Externo | `alma.ASH` | ídem | ídem | **mapeada** (propuesta); ver pregunta 2 |
| — | `borde_<k>.longitud/acero/estribos`, `alma.ganchos` | — | — | MH2 y MH3 | sin mapear: el STP-MIVED no tiene fila para bordes ni ganchos |

Notas de la comparación (sin transformar nada):
- En los 5 muros de S2C y S3C el valor Interno es igual al Externo (h = i y j = k). **El plano no distingue cara**: la propuesta de
  mapear las dos filas al mismo campo se apoya solo en que los STP entregados llevan lo mismo en ambas.
- El símbolo del diámetro: el plano da `Ø` (U+00D8) y el texto extraído de los STP muestra un carácter no legible en `∅1/2"`; el texto
  se copia tal como lo trae el plano, sin convertir. Si Steven quiere `∅`, es una decisión de formato suya.
- Muro de contención en la copia T1: `longitud`, `alma.ASV` y `alma.ASH` están en `pendiente de verificar` (dos rótulos `∅1/2"@0.10`
  sin dirección); el programa no los rellena y el generador pide cada fila con su duda. El STP entregado puso `∅1/2"@0.10` en las cuatro.
- Tramo: el plano trae varios tramos de nivel (`FUNDACIONES @ E-1`, `E-1 @ E-2`…); los valores del ejemplo son del tramo citado. S-2 ↔ E-n sigue sin definir.

## Viga y losa

Fuera de alcance de T4: sin entrada en el JSON, sigue la duda `diseno:pNNN:mapeo`.

## Qué tiene que confirmar Steven

1. **C3, dimensión LY (S2C pág. 9):** el informe lleva 1.20 y la nota de modificación del plano (C3, `columnas.md`) dice «pasa de 1.20 M
   a 1.50 M atendiendo a plano anterior»; el dibujo de C3 `FUNDACIONES @ E-3` trae 1.50. ¿Qué vale para C3 en ese tramo: 1.20 o 1.50?
   El mapeo toma lo impreso en el dibujo (`h_m`); esta duda decide cuál se compara con la medida de obra.
2. **Muro, caras:** ¿se aprueba que `alma.ASV` llene a la vez As Vert. Interno y Externo, y `alma.ASH` As Hor. Interno y Externo?
3. **Columna, derivaciones:** ¿se aprueba derivar f, g, h de `estribos` y m, n de `acero_longitudinal` (hoy sin mapear y pidiendo su dato con duda)?
   El total de barras (k) no se copia: lo comprueba el generador contra la suma de `barras`.
4. **Barras de columna:** ¿se aprueba la conversión exacta `36∅1"` → [[36, '1"']] y que cualquier otro texto vaya a duda?
5. **Longitud de muro (c):** ¿solo cuando el plano da un único valor (como MH3)? En muros en L (MH2) el informe suma las dos alas (`3.80 + 3.85`).
6. **Filas sin campo** (b, e, i, j, o de columna; a, d, e de muro): ¿de dónde salen (notas generales, otra hoja, la visita)?
7. **Confirmar el mapeo** (poner `"confirmado": true`) para que el STP deje de salir como BORRADOR y pueda ir a su carpeta definitiva.
