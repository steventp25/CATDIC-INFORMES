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
