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
