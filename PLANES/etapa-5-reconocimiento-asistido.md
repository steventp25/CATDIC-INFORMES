# Etapa 5 · A1 — Reconocimiento de la lectura asistida (solo lectura)

- Fecha: 16/11/2026 · Lector: Líder de la Fase A (Claude Code, Opus 5.5, suscripción de Steven, sin llave) · Rama `claude/etapa5-fase-a-3da668`.
- Plano: `SUPERVISION\EN CURSO\TERRA LIVING\ARCHIVOS DEL CLIENTE\PLANOS ESTRUCTURALES\PLANOS ESTRUCTURALES TERRALIVING.pdf` (41 hojas, el mismo de T3n), sha256 `59c6be81…6eda21`, **igual antes y después**. La BD real no tiene la tabla `planos` (esquema de antes de la Etapa 2) y no existe `~\CATDIC-DATOS`, así que no hay "vectorial vigente" registrado: se usó el archivo de Dropbox en solo lectura.
- Método: para cada hoja, imagen completa a 36, 72 y 150 ppp + lista numerada de textos (`lector_plano._lineas`, bbox en el marco visual) en el scratchpad de la sesión; lectura de la imagen y la lista; comprobación con recortes a 150 ppp. **Nada se escribió en la BD, en Dropbox ni en el repositorio** (ni imágenes ni datos del cliente; licencias y nombres se omiten).
- "Acierto" = el valor que propongo coincide con el plano al mirarlo de cerca (recorte a 150 ppp). "Sin ancla" = un valor que necesitaría y que no es un texto del vectorial.

## Resumen para quien decide

| Pregunta | Respuesta |
|---|---|
| ¿Claude puede leer las hojas que hoy no se leen? | **Sí** el cuadro de columnas, los detalles de muro, las etiquetas de losa en planta y los pórticos (estos con recortes por nivel). Las fundaciones (platea y *drops*) solo a medias. |
| ¿Los valores tienen ancla? | **Sí, todos los que leí son texto del vectorial** (0 valores sin ancla en columnas, muros, losas y pórtico). Lo que no es texto (cuántas barras se dibujan, a qué *drop* pertenece una sección) solo sirve de comprobación, nunca de valor. |
| ¿Hubo errores? | En la muestra comprobada, 0 valores mal asociados. Sí hay **trampas** que la skill debe nombrar (abajo): cotas del estribo junto a cotas de la sección, rótulos repetidos por sección, notas "plano anterior". |
| Resolución | **72 ppp para la hoja completa** (orientación) + **recortes a 150 ppp por zona** para leer de cerca. 36 ppp no deja leer nada; 150 ppp en hoja completa no aporta (la imagen se reduce al mostrarla). |
| Cupo | La cuenta es **Pro** (límite de 5 h y semanal). Es la restricción que manda: ver "Cupo". |
| Orden de tipos por fiabilidad | columnas → losas (etiqueta en planta) → muros → pórticos por tramo → fundaciones (platea/drops). **Distinto de D9**: losas sube y zapatas baja. |

## 1. Resultados por hoja

| Pág. | Hoja | Qué tiene | Textos | Valores leídos | Aciertos comprobados | Sin ancla | Dudas que abriría | Tiempo aprox. | Fiabilidad |
|---|---|---|---|---|---|---|---|---|---|
| 21 | 20/36 | **Control**: TABLA DE ACERO EN LOSA (A/B/C) + planta S5 con L1–L20 | 459 | 22 de la tabla + 20 etiquetas de losa (L#, H, tipo) | **22/22 iguales al extractor por posición** (T6n) · 20/20 etiquetas | 0 | 2 celdas AS. ADIC. vacías (regla de Steven T7n-b) | 4 min | alta |
| 14 | 13/36 | COLUMNA C1, C2, C3: 4 tramos cada una (FUND.@E-n, E-n@E-8, E-8@E-12, E-12@TECHO) | 251 | 12 tramos × 5 campos (b, h, acero long., estribos, rango) = 60 | 60/60 (2 recortes) | 0 | 1 nota de modificación (C3: "pasa de 1.20 m a 1.50 m atendiendo a plano anterior") | 5 min | alta |
| 16 | 15/36 | MURO MH1 (en L), MH3, MH4: 3 tramos cada uno + viga de acople + detalle de hueco | 301 | ≈110 (espesor, largo, elementos de borde 1/2/3 con barras y estribos, alma ASV/ASH/GAN) | 24/24 en MH4 (2 tramos, recorte); MH1 y MH3 sin recorte | 0 | 1 comprobación que no cuadra: MH4 FUND.@E-2 suma 0.04+0.50+1.13+0.50+0.60+1.00+0.04 = 3.81 ≠ 3.80 (en E-2@E-8 es 1.12 y cuadra) | 7 min | media-alta |
| 34 | 33/36 | PORTICO ESTRUCTURAL EJE 1 (hoja girada 270°): ~23 niveles × 2–3 tramos + DETALLE SECCIONES DE VIGAS | 774 | 1 nivel completo (NPT 3.60): 2 tramos × 8 campos | 16/16 (recorte) | 0 | nivel impreso como NPT (no "NIVEL n"); a qué niveles aplica la banda de estribos inferior; `S-2` ↔ `SECCION 2-2'` | 6 min el nivel; ≈ 25–30 min la hoja | media |
| 7 | 06/36 | PLANTA DE FUNDACIONES y REPLANTEO: platea e=0.50, drops D1/D2/D3 con H1/H2 | 312 | platea (espesor) + 12 drops (ID, H1, H2) | espesor y H1/H2 sí; dimensiones de drop no | 0 | ID repetido con distinto H1 (D1 = 0.80 y 1.00 según dónde); ejes solo por cercanía; nota "planta ajustada… plano anterior" | 6 min | baja |
| 12 | 11/36 | SECCION DE FUNDACIONES PROXIMA A EJE 1 / EJE A | 186 | acero de drops (∅1"@0.15 A.D.), platea (∅1/2"@0.10), muros de cisterna/séptico (ASV/ASH) | textos sí; a qué elemento pertenece, no | 0 | casi todo: la sección no nombra el *drop* | 5 min | baja |

Notas por tipo (son las que la skill `extraer-plano` debe convertir en reglas):

- **Columnas (p. 14).** Cada tramo es un dibujo: sección con barras + despiece de estribos al lado, y el rango impreso debajo (`FUNDACIONES @ E-3`). Trampa: la cota de la sección (`1.50`, `0.60`) está junto a las del despiece (`1.42`, `0.52`, `0.14`); se distinguen porque la de la sección acota el contorno de concreto. El estribo llega en **dos textos** (`9 EST. ∅3/8"` + `@0.10`): la propuesta debe poder citar varios números para un valor. Comprobación posible sin inventar: el número de barras dibujadas coincide con `36∅1"` (36 puntos contados en el recorte). El cuadro **no da ejes**: el ID C1 vale para todos los cruces donde aparece en planta.
- **Muros (p. 16).** Cada tramo tiene 2–3 zonas confinadas (elementos de borde) con su propio acero y estribos, y el alma con `ASV`/`ASH`/`GAN.`. Los rótulos se repiten idénticos en cada tramo: se asignan por la zona del dibujo. Barras en dos textos (`4∅1"(ESQUINAS)` + `+16Ø3/4"`). En el muro en L (MH1) hay que numerar los elementos de borde (`1`, `2`, `3`, regla M4 de CLAUDE.md) para no confundirlos. Las cotas parciales permiten un control cruzado (suma = largo total) que encontró una diferencia de 1 cm.
- **Losas (p. 21).** Hallazgo que corrige T3n: **el tipo de cada losa sí está en texto**. Cada etiqueta de losa en planta es una pila `L17` / `H=0.25M` / `B` (letra dentro de un círculo) y la letra remite a la TABLA DE ACERO EN LOSA. L11 la trae en una fila (`L11 B H=0.25M`). Es una asociación por etiqueta, no por cercanía a ejes; aun así propongo que Steven confirme por lote el cruce L# → tipo. EJES de losa: siempre `—`.
- **Pórticos (p. 34).** La hoja completa no se lee (774 textos en 6 pt); con un recorte a 150 ppp por nivel se lee bien: por tramo, acero superior e inferior, adicionales con su largo (`ADIC. 3∅1"` + `2.35`), zonas de estribos (`EST. Ø3/8"@0.10` / `1.40`) y llamada de sección `S-2`. Problemas: (a) el nivel está impreso como `NPT= 3.60`, no como nombre de planta: hace falta una equivalencia NPT ↔ nivel que dé el usuario, como hoy E-n ↔ nivel; (b) la banda de estribos de abajo (sobre los ejes A–D) no dice a qué niveles aplica; (c) la llamada `S-2` se rotula `SECCION 2-2'` en el detalle (`V40X70`): unirlas es una inferencia y debe quedar como duda o con confirmación; (d) sobre el nivel 0 no hay columna en C, así que el tramo es B–D aunque haya globo C. EJES: `EJE 1 ENTRE A-B` (formato aceptado por `formatear_campo_ejes`).
- **Fundaciones (pp. 7 y 12).** No hay zapatas aisladas: es platea (e = 0.50) con *drops* D1/D2/D3. El mismo ID tiene distinto `H1` según su posición, así que el ID no identifica un diseño; ubicarlo exige el cruce de ejes por cercanía (prohibido) y las secciones de la p. 12 no nombran el *drop*. Recomendación: en esta etapa solo el espesor de platea y la tabla de f'c; los *drops* a la Mesa de Dudas.
- **Notas de modificación.** Tres hojas de seis traen una nota "…atendiendo a plano anterior con licencia [LICENCIA]". Nunca se aplican: van a la Mesa como duda (igual que hace hoy `notas_de_modificacion`).
- **Hoja girada (pórticos).** `get_pixmap(clip=…)` recibe el recuadro en el marco visual (el mismo de las bbox de `_lineas`); aplicarle `derotation_matrix` da un recorte equivocado. Lo comprobé al recortar la p. 34. A2 ya prueba que la bbox cae en su sitio en la imagen completa girada.

## 2. Resolución recomendada

| Opción | Tamaño (hoja 36×24 in) | Tokens de imagen aprox. | Resultado |
|---|---|---|---|
| 36 ppp | 1296×864 px, 140–200 KB | ≈ 1.500 | se ve el esquema, no se lee ningún rótulo; con la lista de textos se podría asociar por coordenadas, pero sin poder mirar |
| **72 ppp** | 2592×1728 px, 350–540 KB | ≈ 5.000 (se muestra a 2353×1568) | **recomendada para la hoja completa**: se leen rótulos de 7,5 pt, cotas y títulos; no los de 6 pt de los pórticos |
| 150 ppp | 5400×3600 px, 0,9–1,4 MB | igual que 72 ppp (se reduce al mostrarla) | no aporta en hoja completa |
| **recorte 150 ppp** | zona de 500×600 pt ≈ 1000×1250 px | ≈ 1.500–2.500 | **recomendado para leer de cerca**: estribos, rótulos de 6 pt, conteo de barras |

Propuesta para A2 (ajuste, mismos archivos): `ppp` por defecto 72; una función/CLI `recortar(pagina, bbox_pt, ppp=150)` que guarde `pNN/zonas/<x0>_<y0>_<x1>_<y1>.png` para que la sesión lectora pida recortes sin abrir el PDF; y `pNN/textos.txt` compacto (`n|texto|x0,y0,x1,y1|tam`, una línea por texto), porque el JSON con sangría cuesta el doble de tokens. `textos.json` sigue siendo la referencia que usa el importador.

## 3. Cupo y hojas por sesión

Medido con el uso de la cuenta (`get_usage`): plan **Pro**, límite de 5 h y semanal. El coste lo marca sobre todo **el largo del contexto × el número de llamadas** (cada llamada reenvía la conversación): al retomar esta sesión con ~280.000 tokens de contexto, unas 8 llamadas gastaron ≈ 17 % de la ventana de 5 h. Por eso las sesiones lectoras deben ser **cortas y nuevas**, y escribir la propuesta de cada hoja en disco antes de pasar a la siguiente (se retoma donde quedó).

Estimación por hoja en una sesión nueva (contexto pequeño), en % de la ventana de 5 h del plan Pro (orden de magnitud, no medida exacta):

| Tipo de hoja | Llamadas | Tokens de entrada por hoja | % de ventana 5 h aprox. |
|---|---|---|---|
| tabla / planta de losas | 4–6 | 15–20 mil | 2–3 % |
| cuadro de columnas | 5–7 | 15–25 mil | 2–4 % |
| muros | 6–9 | 25–35 mil | 3–5 % |
| pórtico (≈ 12 recortes) | 15–25 | 60–90 mil | 10–15 % |

- **Hojas por sesión:** un lote de **4–6 hojas de columnas, muros o losas**, o **1 pórtico** por sesión. Más que eso alarga el contexto y encarece cada llamada.
- **Terra Living completo** (≈ 15 plantas, 2 de columnas, 2 de muros, 8 pórticos, 5 de fundaciones): del orden de **1,5–2 ventanas de 5 h** y una parte apreciable del cupo semanal (hoy al 30 %, compartido con la Fase B). A6 debe ir por lotes y en días distintos si hace falta.

## 4. Tipos por fiabilidad (propuesta para A4)

1. **Columnas** (cuadro por tramo de rango): todo anclado; un dibujo por tramo.
2. **Losas** (etiqueta en planta + tabla de aplicación): todo anclado, barato; se cruza con el extractor actual (doble lectura, decisión 3).
3. **Muros H.A.** (detalle por tramo): anclado, pero con más campos y elementos de borde que numerar.
4. **Pórticos por tramo**: anclado, pero caro y con dos equivalencias que da el usuario (NPT ↔ nivel, `S-n` ↔ sección) y la banda de estribos sin nivel.
5. **Fundaciones (platea y drops)**: solo espesor de platea y f'c; los *drops* a la Mesa.

Esto cambia D9 (columnas → muros y zapatas → pórticos → losas): **propongo A4a columnas · A4b losas · A4c muros · A4d pórticos · fundaciones al final**. Lo decide Steven en la puerta.

## 5. Formato propuesto de los archivos

### `textos.json` (lo escribe A2; ya hecho así en `preparar.py`)
```json
{"version": 1, "archivo": "PLANOS ….pdf", "sha256": "…", "pagina": 14, "hoja": "13", "rotacion": 0,
 "ancho_pt": 2592.0, "alto_pt": 1728.0, "ppp": 72, "imagen": "hoja.png", "ancho_px": 2592, "alto_px": 1728,
 "px_por_pt": 1.0,
 "textos": [{"n": 1, "texto": "9 EST. ∅3/8\"", "bbox": [279.4, 80.2, 324.1, 87.6], "tam": 7.5}]}
```
Más `textos.txt` (compacto, para leer) y `zonas/` (recortes pedidos). Números `n` estables: orden por `round(y0)` y `x0`.

### `propuesta.json` (lo escribe la sesión lectora, una por hoja, en `pNN/`)
```json
{"version": 1, "archivo": "…", "sha256": "…", "pagina": 14, "hoja": "13", "lector": "claude-code", "skill": "extraer-plano@1",
 "elementos": [
  {"tipo_elemento": "COLUMNA", "zona": [180, 70, 760, 600],
   "id_elemento": {"valor": "C1", "citas": [74]},
   "nivel_rango": {"valor": "FUNDACIONES @ E-3", "citas": [76]},
   "ejes": {"valor": null, "duda": "El cuadro de columnas no da ejes."},
   "campos": {
     "b": {"valor": "0.60", "citas": [70]},
     "h": {"valor": "1.50", "citas": [32]},
     "acero_longitudinal": {"valor": "36∅1\"", "citas": [3]},
     "estribos": {"valor": "9 EST. ∅3/8\" @0.10", "citas": [1, 2]}
   }}],
 "dudas_hoja": [{"texto": "Nota de modificación: corrección de dimensión de C3 respecto de plano anterior.", "citas": [161, 162, 164, 167]}],
 "comprobaciones": [{"descripcion": "Barras dibujadas en C1 FUND.@E-3 = 36", "resultado": "cuadra", "citas": [3]}]}
```
Reglas que propongo para el importador (A3):
- **Anclaje estricto:** `valor` debe aparecer **tal cual** dentro del texto citado (o de la unión con un espacio de los textos citados, en el orden dado), con límites de palabra: `0.25` vale contra `H=0.25M`; `1` no vale contra `36∅1"`. Se guarda también el texto citado literal y la unión de sus bbox como fuente.
- `valor: null` + `duda` → el campo queda `"pendiente de verificar"` y se abre una duda `IA:` con el texto de la duda.
- Una cita a un número que no existe, un `sha256` distinto del vigente o un JSON que no cumple el esquema → no se carga **nada** de esa hoja.
- `nivel_rango` se guarda **como está impreso** (`FUNDACIONES @ E-3`, `NPT= 3.60`); la expansión a niveles la hace el backend con las equivalencias del usuario, nunca Claude.
- Unir dos rótulos distintos (`S-2` ↔ `SECCION 2-2'`, `L17` ↔ fila `B` de la tabla) se declara como `"enlace"` con las dos citas y entra siempre como duda o como confirmación por lote; nunca como valor directo.
- `dudas_hoja` (notas de modificación, contradicciones planta/detalle) → `DUDA_BLOQUEANTE` con prefijo `IA:`; las `comprobaciones` se guardan como información, no cambian valores.

## 6. Preguntas para la puerta (Director / Steven)
1. **Orden de A4**: ¿columnas → losas → muros → pórticos → fundaciones (propuesta) en vez de D9?
2. **Ejes de columnas y muros**: los detalles no los dan. ¿Se guarda el diseño por ID + rango con EJES `"pendiente de verificar"` (y se cruza con la visita por ID + nivel), o se pide a Claude que proponga el cruce leyendo la planta (sería cercanía visual: va contra el error 11 y la Regla de Oro)? Propuesta: lo primero.
3. **Fundaciones con drops**: ¿quedan fuera de esta etapa salvo espesor de platea y f'c?
4. **Cupo**: con el plan Pro, ¿A6 se hace por lotes a lo largo de varios días para no frenar la Fase B?
