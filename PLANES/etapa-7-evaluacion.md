## Evaluación 1 · 23/11/2026 · Director (auditoría) · Etapa 7 · T2, T3 y T4 (rama `claude/etapa7-campo-informe-02d16d`, `db08f7e`)
**Veredicto: APROBADO.** El mapeo queda como propuesta sin confirmar; lo confirma Steven.

### Bloqueantes
- Ninguno.

### Regla de Oro y decisiones de Steven (revisado en el diff)
- **«Vacío = conforme».**
  - `obra_de_elemento` (`sync/paquete_visita.py`) solo da por conformes las letras del juego de la fila STP que no se escribieron y no están mal. Un elemento Pendiente no recibe ninguna conforme.
  - En el generador, OBRA copia el valor del plano solo si la letra está en `conforme_por_omision` y el plano trae valor. Si el plano no lo trae, OBRA sigue vacía y abre duda.
- **«Pendiente → En revisión».**
  - Se abre la duda `elemento_visita:pNNN:pendiente`.
  - `procesador_cola._ficha` no arma la ficha mientras esa duda siga abierta.
  - Un estado desconocido se trata como Pendiente.
- **Medidas.**
  - Solo se aceptan números positivos en metros, de 30 m o menos, con punto o coma.
  - Cualquier otro valor va a duda con el valor literal y nunca se da por conforme.
  - Si el juego de filas no corresponde al tipo, la obra entera no se usa.
- **Barras.**
  - `convertir_barras` acepta solo el texto entero, con un único grupo (`36∅1"` → `[[36, '1"']]`).
  - Cualquier otro texto abre una duda con el texto impreso.
- **Mapeo.**
  - `mapeo_stp.json` tiene `confirmado: false`. Viga y losa siguen sin entrada y con su duda.
  - En muro, h = i (ASV) y j = k (ASH) es una propuesta con evidencia de 5 muros de STP entregados. Lo confirma Steven.
- **Salida.**
  - Sin confirmar, el STP lleva la marca «BORRADOR — mapeo sin confirmar».
  - Solo se genera si `CATDIC_SALIDA_PRUEBAS` está definida; si no, abre duda.
  - La carpeta sale siempre de `obtener_salida_pruebas()`. Nunca de `INFORMES\2.DATA PROCESADA`.
- **Retrocompatibilidad.** Un paquete v1 no escribe `medidas_acero_campo_json`.

### Pruebas ejecutadas
- **Suite completa** sobre una copia exacta de `db08f7e`, con BD, salida y caché temporales: **1028 pasan**, 3 se omiten y fallan las 2 conocidas de Dropbox.
- **BD real sin cambios:** sha256 `eba26967…` antes y después.

### Campo v11 (T2)
- La copia está en `G:\My Drive\VISITA A OBRA CATDIC (v11 prueba)\`. Lleva la caché `campo-v11`, `VERSION_PAQUETE = 2` y exporta `fila_stp`, `textos` y `medidas_acero`.
- El `app.js`, `index.html`, `styles.css` y `sw.js` de la carpeta original **no cambiaron** (fechas del 22/11).
- **Observación:** la carpeta original tiene una subcarpeta oculta `.impeccable` modificada hoy a las 19:38. Es de la herramienta de diseño, no de la app, pero el plan decía no tocar la carpeta original. Que el Líder confirme qué escribió ahí.
- **[?] En el navegador:** no probé la copia de Campo. El Líder reporta un paquete exportado con el botón real y leído por el lector v2.

### Observaciones (no bloquean)
- Si un elemento de la visita tiene una falta, el procesador no genera ninguna ficha de esa visita. Es el comportamiento de antes. En la prueba T5 se verá si conviene cambiarlo (decisión de Steven).
- En la visita 24, la longitud del muro (fila c) solo está en el plano para MH3. MH2 y el muro de contención la tienen pendiente (T1).

## Evaluación 2 · 23/11/2026 · Director (auditoría) · Etapa 7 · T1 (rama `claude/etapa5-fase-a-3da668`, `ea7b0b1`)
**Veredicto: APROBADO.**

- **Lectura.** Se leyeron 4 hojas y salieron 16 elementos en la copia de la BD, con 28 dudas `IA:`. No se confirmó nada. EJES queda «pendiente de verificar», según la decisión D11.
- **Revisión.** `revisar.py` da 0 valores sin ancla, según el Líder.
- **Comprobación cruzada.** C1 `FUNDACIONES @ E-3` da 0.60 × 1.50 y `36∅1"`, igual que en el reconocimiento A1 del 16/11.
- **Dudas bien abiertas:**
  - la nota de C3 sobre un «plano anterior»;
  - las alas de MH2;
  - las 8 barras «comprendidas» entre E1 y E2;
  - el ID y las caras del muro de contención.
- **BD real y Dropbox.** La BD real no cambió: sha256 `eba26967…`, igual antes y después. Dropbox solo se leyó.
- **Huecos para T5:**
  - El importador no guarda la `zona` del DETALLE.
  - Falta la equivalencia S-2 ↔ E-n, un dato que da Steven.
  - La copia tiene un plano «PRUEBA T1» sin certificar.

## Evaluación 3 · 24/11/2026 · Director (auditoría) · Etapa 7 · T6, T7, T8, T8b y T8c (rama `claude/etapa7-campo-informe-02d16d`, `db08f7e..2f973b5`)
**Veredicto: APROBADO.**

### Bloqueantes
- Ninguno.

### Regla de Oro (revisado en el diff)
- **T6, equivalencias.**
  - La tabla `equivalencias_nivel` solo la escribe el usuario, con `PUT`, respaldo previo y auditoría.
  - Las equivalencias valen solo para los elementos de diseño sin EJES (D11). Si falta la equivalencia, se abre la duda `cruce:pNNN:equivalencia`. Si dos tramos del mismo ID cumplen, se abre la duda y no se elige ninguno.
  - Los EJES de la ficha salen de la visita. Si no hay, se abre la duda `cruce:pNNN:ejes`.
  - La normalización es exacta: espacios alrededor de `-` y `@`, y mayúsculas.
- **T7, cabecera.**
  - Solo lee los PDF.
  - Guarda en `propuestas_proyecto` con estado `propuesta` y la cita (archivo y página). Nunca escribe en `proyectos`.
  - No pisa lo que Steven resolvió, descarta la dirección de CATDIC y abre una sola duda.
- **T8, T8b y T8c, recuadros.**
  - Siempre quedan `pendiente de verificar` con su origen y su cita. Nunca escriben «confirmado».
  - No pisan un recuadro confirmado y el sha256 debe coincidir con el vectorial.
  - En T8c, los ejes de la visita se usan solo si hay exactamente uno válido, y en una copia del elemento: el diseño no se modifica.
- **Visor (`f43511f`).** Distingue entre vacío, propuesto y confirmado.

### Pruebas ejecutadas
- **Suite completa** sobre una copia exacta de `2f973b5`, con BD, caché y salida temporales: **1117 pasan**, 3 se omiten y fallan las 2 conocidas de Dropbox.
- **T5, corridas 2 y 3:** ver `etapa-7-prueba.md`. El cruce de C1 y C3, la cabecera (19 de 19 informes coinciden) y 4 localizaciones con 16 detalles funcionan.
- **BD real sin cambios:** sha256 `eba26967…`.

### Observaciones (no bloquean)
- **Tabla sin crear.** `procesador_cola` consulta `equivalencias_nivel` sin comprobar que existe. En una BD vieja que no pasó por `inicializar_bd()` falla con `no such table`. El servidor la crea al arrancar, así que solo afecta a scripts. Conviene una prueba o una comprobación.
- **Tabla creada por el módulo.** `propuestas_proyecto` la crea `cabecera_propuesta._asegurar_tabla` y no `database.inicializar_bd`. Es inconsistente con el resto del esquema.
- **Mapeo de columna.** Sin la derivación de las filas f, g, h, m y n (pregunta 3 del mapeo), ninguna columna llega al PDF. Es decisión de Steven.

## Evaluación 4 · 24/11/2026 · Director (auditoría) · Etapa 7 · T9 (rama `claude/etapa7-campo-informe-02d16d`, `3cc0036..cb859e5`)
**Veredicto: APROBADO.**

### Lo revisado
- **Reglas de derivación.** Las tres reglas usan regex exacta sobre el texto entero. El símbolo y la comilla se copian como vienen impresos.
- **Texto que no cuadra.** Abre la duda `diseno:pNNN:derivacion.<letra>` con el texto impreso, y la fila queda vacía.
- **Prioridad.** Una fila directa en `filas` manda sobre la derivación.
- **k y la cuantía.** No se tocan (error 12).
- **Regla desconocida.** Si el JSON trae una regla que no existe, el mapeo se toma por roto y no se adivina.
- **f = g y m = n.** Son una propuesta con una duda que no bloquea por ficha. Lo decide Steven (pregunta 7).
- **Arreglos menores.**
  - `equivalencias_de` devuelve `[]` si la tabla no existe.
  - `inicializar_bd` crea la tabla `propuestas_proyecto`.

### Pruebas ejecutadas
- **Suite completa** sobre una copia exacta de `cb859e5`: **1149 pasan**, 3 se omiten y fallan las 2 conocidas de Dropbox.
- **Simulación de la corrida 4** (abajo).
- **BD real sin cambios:** sha256 `eba26967…`.
