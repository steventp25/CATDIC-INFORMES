# Etapa 7 · T5 — Prueba de punta a punta, corrida 1 (23/11/2026, Director)

## Montaje
- **Código:** copia exacta de `claude/etapa7-campo-informe-02d16d` en `db08f7e` (T2, T3 y T4).
- **BD:** copia de la BD de T1 (`catdic_copia_t1.db`). Tiene los 16 elementos de diseño de C1, C3, MH2, MH3 y el muro de contención, sin confirmar. Está en el scratch del Director, `…\scratchpad\t5\copia.db`.
- **Visita:** real, `24. VERTICALES S-2 COMPLETIVO 06-11-2026`. Se leyó de Dropbox sin escribir nada.
- **Paquete v2 simulado** a partir del PDF real.
  - Las casillas de identidad se llenaron como lo haría el técnico.
  - En OBRA, C1 y C3 llevan solo la fila «o» (solape), con el texto del PDF.
  - El resto de las filas va vacío, es decir, conforme.
- **Salida:** `CATDIC_SALIDA_PRUEBAS` en el scratch. El mapeo está sin confirmar, así que el STP sale como borrador.
- **BD real y Dropbox:** no se tocaron.

## Resultado: el procesador se detiene antes de generar (0 de 5 fichas, 6 dudas)

| # | Dónde se detiene | Elemento | Por qué | Quién lo resuelve |
|---|---|---|---|---|
| 1 | Paquete | MH2, MH3 | La visita no trae ejes | Steven o el técnico (dato de obra) |
| 2 | Paquete | Muro de contención | La visita no trae ID | Steven o el técnico |
| 3 | Cruce visita ↔ diseño | C1, C3 | No hay un elemento de diseño con ID + nivel S-2 + ejes. El diseño (T1) está guardado por **rango impreso** (`FUNDACIONES @ E-3`, `E-3 @ E-8`…) y con **EJES pendientes** (el cuadro de columnas no da ejes). El procesador compara el nivel literal (`S-2`) y exige los mismos ejes. | **Código (T6)** y un dato de Steven (S-2 ↔ E-n) |
| 4 | Cabecera del proyecto | (visita) | Faltan `no_solicitud`, `no_licencia`, `direccion_obra`, `provincia`, `sector` y `residente_obra` | Steven. **T7** puede proponerlos desde un STP ya entregado |
| 5 | (todavía no se llega) | todos | Recuadros de LOCALIZACIÓN y DETALLE confirmados en el visor | **T8** los propone y Steven los confirma |
| 6 | (todavía no se llega) | todos | Datos del plano confirmados por Steven («Confirmar plano») | Steven |

## Lo que hace falta desarrollar para que la prueba llegue al PDF
- **T6 — Cruce por ID + nivel y equivalencia de niveles** (backend).
  - Si el diseño no trae EJES (cuadro de columnas, detalles de muro), la regla aprobada es cruzar por **ID + nivel** (decisión D11 de la Fase A, A1 §6.2) y tomar los EJES de la visita.
  - Hace falta una tabla de equivalencias por obra, que da el usuario: `S-2` → el rango impreso que le toca (p. ej. `E-1 @ E-2`).
  - Mientras falte la equivalencia, se abre una duda y nunca se adivina.
  - El rango del muro de contención viene impreso `SOTANO S - 2`. Normalizar los espacios para que cuadre con `SOTANO S-2` es una regla exacta.
- **T7 — Cabecera propuesta** desde la portada de un STP-MIVED ya entregado de Terra Living, en solo lectura.
  - Cada valor cita el informe y la página.
  - Va sin confirmar; Steven la confirma.
- **T8 — Recuadros propuestos.**
  - **LOCALIZACIÓN:** con `visor._proponer_localizacion` sobre la planta de S-2 (p24). El ID aparece una vez o se cruzan los ejes.
  - **DETALLE:** con la `zona` que la IA ya escribió en cada `propuesta.json` de T1. Hoy el importador no la guarda.
  - Todo queda «pendiente» para que Steven lo confirme en el visor.

## Lista de Steven (al volver, en este orden)
1. Las 3 dudas de la visita: ejes de MH2 y MH3, e ID del muro de contención del eje 4'.
2. La equivalencia S-2 ↔ E-n de Terra Living.
3. Confirmar la cabecera propuesta (T7).
4. Confirmar los datos del plano (28 dudas `IA:` de T1) y los recuadros (T8).
5. Confirmar el mapeo de filas del STP (`PLANES/etapa-7-mapeo-stp.md`).
6. Reemplazar Campo por la copia v11.

# Corrida 2 (24/11/2026, Director)

## Montaje
- **Código:** copia exacta de `claude/etapa7-campo-informe-02d16d` en `2f973b5` (T6, T7, T8, T8b y T8c).
- **BD:** copia nueva de la BD de T1, en `…\scratchpad\t5b\copia.db`. Se inicializó como lo hace el servidor al arrancar, para crear la tabla `equivalencias_nivel`.
- **Equivalencia S-2:** cargada **solo en la copia y como hipótesis**, con el usuario `prueba-t5-hipotesis`. Lleva los tres rangos de `PLANES/etapa-7-niveles.md`: `FUNDACIONES @ E-3`, `FUNDACIONES @ E-1` y `FUNDACIONES @ E-2`.
- **Paquete:** el mismo paquete v2 simulado de la corrida 1.
- **BD real y Dropbox:** no se tocaron. La BD real tiene sha256 `eba26967…` antes y después; Dropbox solo se leyó.

## Resultado: 0 fichas, pero el cruce ya funciona
| Paso | Corrida 1 | Corrida 2 |
|---|---|---|
| Cruce de C1 y C3 con el diseño | se detenía | **cruza** por ID + nivel con la equivalencia (T6) |
| Recuadros propuestos | ninguno | **DETALLE** de los 16 elementos y **LOCALIZACIÓN** de C1, C3, MH2 y MH3 en la planta de S-2. Todos quedan pendientes de confirmar (T8). El muro de contención no tiene localización: su ID no aparece en la planta y sus ejes no son un cruce puntual. |
| Cabecera | faltaban 6 campos | **propuesta** con 19 de 19 STP entregados, todos coinciden (T7): solicitud (dato del cliente, en la BD), licencia (dato del cliente, en la BD), dirección (dato del cliente, en la BD), provincia (dato del cliente, en la BD), sector (dato del cliente, en la BD), residente (dato del cliente, en la BD). Sigue sin confirmar, así que el procesador todavía la pide. |
| Dudas abiertas | 6 | 6, pero ahora solo las que resuelve Steven (abajo) |

## Dónde se detiene ahora (todas dependen de Steven o del técnico)
1. Ejes de MH2 y MH3, y el ID del muro de contención (dato de obra).
2. Datos del plano de C1 y C3 sin confirmar («Confirmar plano»).
3. La cabecera propuesta sin confirmar. **Ojo:** el número de solicitud y el de licencia salen iguales (dato del cliente, en la BD) en los 19 informes. Steven debe decir si es correcto.
4. Después vendrán los recuadros propuestos (confirmarlos en el visor) y la equivalencia S-2 (hipótesis).

**Ya no falta código para llegar al PDF de C1 y C3.** Falta que Steven confirme. Cuando lo haga, se repite la corrida 3 y debería salir el STP borrador de esas dos columnas.

# Corrida 3: SIMULACIÓN de las confirmaciones (24/11/2026, Director)
**No es un dato de Steven.** El objetivo era ver si el código llega al PDF cuando todo está confirmado. Se usó otra copia de la BD (`…\scratchpad\t5c\copia.db`) con el usuario `prueba-simulada`. En esa copia:
- se dieron por confirmados los datos del plano y los dos recuadros de C1 y C3 (`FUNDACIONES @ E-3`);
- se copió la cabecera propuesta a la obra;
- se quitaron de la visita MH2, MH3 y el muro de contención, que tienen dudas de obra.

**Resultado:** C1 y C3 quedan **«listo»**: el cruce, la ficha y los recuadros están bien. Aun así, el STP no se genera por 2 dudas, una por columna: *«Falta en el plano el valor de la fila 'f' de COLUMNA»* (espaciamiento de estribos en nodos).
- **La causa:** en el mapeo de T4, las filas f, g y h (estribos) y m y n (diámetros) quedaron **sin mapear a propósito**. Son la pregunta 3 de `PLANES/etapa-7-mapeo-stp.md`: *¿se aprueba derivar f, g y h de `estribos` (`9 EST. ∅3/8" @0.10`) y m y n de `acero_longitudinal`?*
- **Lo que significa:** cuando Steven apruebe esa derivación, hay que programar la conversión exacta (tarea corta, con pruebas). Después, la corrida con sus confirmaciones reales debería sacar el STP borrador de C1 y C3.

## Lista corta de Steven (actualizada)
1. Dudas de obra: ejes de MH2 y MH3, e ID del muro de contención.
2. Equivalencia S-2: confirmar o corregir la hipótesis (`PLANES/etapa-7-niveles.md`).
3. Cabecera propuesta: confirmarla. Ojo: la solicitud y la licencia salen iguales, (dato del cliente, en la BD).
4. Datos del plano de C1 y C3 (y de los muros) y sus recuadros, en el visor.
5. Mapeo STP, **sobre todo la pregunta 3** (estribos y diámetros de columna): sin eso no sale el PDF.
6. Reemplazar Campo por la copia v11.
