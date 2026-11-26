# Etapa 7 — De CATDIC Campo al informe de visita automático (prueba con la visita 24 de Terra Living)
Estado: APROBADO (Steven, 23/11/2026: «Sí, planifícalo» y «continúa trabajando según lo establecido; prepara todo para la prueba»). Sin push ni fusión hasta que Steven vuelva.

## Objetivo
Dejar lista la **prueba de punta a punta** con la visita real `24. VERTICALES S-2 COMPLETIVO 06-11-2026` de Terra Living:
paquete de Campo → elementos de la visita → datos del plano (leídos por la IA) → Procesar Cola → STP-MIVED en la
carpeta de pruebas. Al volver Steven, solo faltan sus confirmaciones (datos del plano, recuadros, mapeo de filas).

## Decisiones de Steven que aplican
- 23/11: si una medición de obra va **vacía**, el elemento es **conforme** (OBRA = valor del plano, §4.5). Si el elemento
  está **Pendiente** en la visita, pasa a **En revisión** (no entra como conforme; abre duda).
- 23/11: la IA lee y extrae **todos** los elementos estructurales del plano a las tablas; el código usa esas tablas.
- La IA propone, el código ancla y valida, y Steven confirma (Regla de Oro). Nada se inventa: lo no leído queda
  `pendiente de verificar`.

## Discrepancias CLAUDE.md vs repositorio
- `elementos_diseno` de Terra Living está **vacía** en la BD real (comprobado 23/11 sobre una copia).
- `MAPEO_DISENO_A_STP` en `BACKEND/procesador_cola.py:87` está **vacío**: el programa no sabe qué dato del plano va
  en cada fila del STP-MIVED. Hoy toda ficha se detiene con la duda «decisión pendiente de Steven».
- `medidas_acero_campo_json` no la llena ningún módulo; Campo solo manda `mediciones` como texto libre.
- La BD real no tiene la visita 24 (el sincronizador la crea al correr).
- CATDIC Campo (`G:\My Drive\VISITA A OBRA CATDIC`) no está en git.

## Tareas

### T1 — La IA lee del plano los elementos de la visita 24 (Fase A, tramo acotado)
- Ejecutor: Líder de la Fase A (sesión `fase-a`) con sus Ejecutores; rama `claude/etapa5-fase-a-3da668`.
- Archivos: los de la Fase A (`BACKEND/plano/asistido/…`, skill `extraer-plano`, `PLANES/etapa-5-fase-A.md`); datos solo en scratch y en una **copia** de la BD.
- Depende de: —
- Qué hacer: retomar la Fase A (sale de la pausa por F0) **solo para lo que pide la prueba**: C1, C3, MH2, MH3 y el muro de
  contención del eje 4' (A–D) en el nivel S-2. Hojas: cuadro de columnas, detalles de muros y el detalle del muro de
  contención, y la planta de S-2 para la localización. Hacer A4c (muros) lo justo para estos elementos. Generar
  `propuesta.json` con citas e importarla con el importador con anclaje (A3d) a la copia de la BD, sin confirmar.
- Criterios de aceptación:
  - [ ] Cada valor importado cita un texto del vectorial; lo que no, queda `pendiente de verificar` con su duda `IA:`.
  - [ ] EJES de columnas y muros: del detalle no salen; quedan `pendiente de verificar` y se cruzan por ID + nivel (decisión A1 §6.2).
  - [ ] Informe corto en `PLANES/etapa-5-reportes/` con lo leído, las dudas y el cupo gastado.
  - [ ] Nada escrito en Dropbox ni en la BD real.
- Cupo: la cuenta es Pro y lleva 48 % de la semana (reinicia 28/11). Este tramo cuesta ≈ 10–15 % de una ventana de 5 h. No leer el resto de Terra Living en esta etapa.
- Reglas: Regla de Oro, §4.2, §4.4, errores 11 y 12.

### T2 — Campo v11: mediciones guiadas por tipo
- Ejecutor: ejecutor-frontend (Campo es HTML/JS sin build).
- Archivos: una **copia** de trabajo de Campo `G:\My Drive\VISITA A OBRA CATDIC (v11 prueba)\` (`app.js`, `index.html`, `styles.css`, `sw.js`). La carpeta en uso **no se toca**: Steven la reemplaza al volver.
- Depende de: —
- Qué hacer: en cada elemento, además del cuadro de texto libre, casillas de OBRA con las mismas filas que la columna
  `2. IMFORMACION ARMADO EN OBRA` del STP-MIVED (`BACKEND/generators/stp_mived.py:45-66`), según el tipo (col, muro,
  viga/pórtico, losa). Vacío = conforme (decisión de Steven); se muestra como «conforme (igual al plano)». Las medidas
  dimensionales (`DIMENSIONALES`) se piden **sobre el acero** y la ayuda lo dice. Estado `Pendiente` visible y exportado.
  Exportar el paquete con `version: 2` y un campo `obra` por elemento: `{letra: texto}` y `medidas_acero: {letra: metros}`.
- Criterios de aceptación:
  - [ ] Un paquete v2 exportado desde la copia (en el navegador del PC) valida contra `PLANES/paquete-visita-v2.md`.
  - [ ] Las visitas viejas y el paquete v1 siguen funcionando (cargar una visita guardada no pierde datos).
  - [ ] `sw.js` sube la versión de caché a `campo-v11`.
- Reglas: §4.4, §4.5, error 9 (sin «CORRIDO»), §5.2 (fotos ≤ 1000 px).

### T3 — Informes: lector del paquete v2 y regla «vacío = conforme»
- Ejecutor: ejecutor-backend.
- Archivos: `BACKEND/sync/paquete_visita.py`, `BACKEND/tests/test_paquete_visita.py`, `PLANES/paquete-visita-v2.md` (nuevo).
- Depende de: — (el contrato v2 lo escriben T2 y T3 juntos: lo redacta T3 primero y T2 lo sigue).
- Qué hacer: aceptar `version` 1 y 2. En v2, llenar `medidas_acero_campo_json` con el contrato que ya lee
  `procesador_cola.py:720` (`{letra: metros, "obra": {letra: texto}}`). Vacío = conforme: no se escribe nada en `obra`
  y se marca `conforme_por_omision: true` para esa letra, para que el generador ponga el valor del plano. Estado
  `Pendiente` → el elemento queda `En revisión` con una duda. Validar números (metros con punto o coma; nada de unidades
  raras: eso va a duda, nunca se adivina).
- Criterios de aceptación:
  - [ ] Pruebas nuevas: v2 completo, v2 con vacíos, v2 con estado Pendiente, v2 con medida ilegible, v1 sin cambios.
  - [ ] Suite completa: 977+ pasan; solo fallan las 2 conocidas de Dropbox.
- Reglas: Regla de Oro, §4.5, error 12.

### T4 — Mapeo de filas del STP-MIVED (propuesta para Steven)
- Ejecutor: ejecutor-generadores.
- Archivos: `BACKEND/procesador_cola.py` (solo `MAPEO_DISENO_A_STP` y su carga), `BACKEND/generators/mapeo_stp.json` (nuevo), `BACKEND/tests/test_procesar_cola.py`, `PLANES/etapa-7-mapeo-stp.md` (nuevo).
- Depende de: T1 (nombres de los campos de `datos_diseno_json` que produce la Fase A).
- Qué hacer: proponer, para col y muro (los tipos de la visita 24), de qué campo del plano sale cada fila. La evidencia
  son los STP-MIVED ya entregados de Terra Living en `INFORMES\2.DATA PROCESADA\` (solo lectura): en el informe sale
  la fila y el valor, y en el plano el texto de donde sale. El mapeo va en el JSON con `"confirmado": false`. Mientras no
  esté confirmado, el STP solo se genera en la carpeta de pruebas (`CATDIC_SALIDA_PRUEBAS`) y la portada lleva una marca
  `BORRADOR — mapeo sin confirmar`.
- Criterios de aceptación:
  - [ ] `PLANES/etapa-7-mapeo-stp.md` tiene una tabla fila → campo → ejemplo real (informe, página).
  - [ ] Una fila sin evidencia queda sin mapear (la ficha sigue pidiendo el dato con su duda).
  - [ ] Pruebas de que con `confirmado: false` nunca se escribe en `INFORMES\2.DATA PROCESADA\`.
- Reglas: Regla de Oro, error 12, error 13, §5.2.

### T5 — Prueba preparada de punta a punta
- Ejecutor: Director (yo), con el skill auditar-catdic.
- Archivos: `PLANES/etapa-7-prueba.md` (guion y resultado); todo lo demás en scratch.
- Depende de: T1, T3, T4 (T2 solo para el paquete exportado de verdad; mientras, paquete v2 simulado como el del 23/11).
- Qué hacer: sobre una copia de la BD, correr sincronizador → paquete → diseño de T1 → recuadros propuestos (visor) →
  Procesar Cola. Anotar dónde se detiene y por qué. Dejar a Steven la lista corta de lo que le toca confirmar.
- Criterios de aceptación:
  - [ ] `etapa-7-prueba.md` dice paso a paso qué salió y qué falta, con capturas o rutas de salida en la carpeta de pruebas.
  - [ ] La BD real y Dropbox sin cambios (sha256 antes y después).

### T6 — Cruce por ID + nivel cuando el diseño no trae EJES (equivalencia de niveles)
- Ejecutor: ejecutor-backend. Pedido por el Director el 23/11, después de la corrida 1 de T5 (`PLANES/etapa-7-prueba.md`, punto 3).
- Archivos: `BACKEND/database.py` (tabla nueva), `BACKEND/procesador_cola.py` (`_candidatos` y su duda), `BACKEND/main.py` (endpoints), `BACKEND/tests/test_equivalencias_nivel.py` (nuevo), `PLANES/etapa-7-niveles.md` (nuevo).
- Depende de: —
- Qué hacer:
  - Tabla `equivalencias_nivel` por obra: `proyecto_id`, `nivel_visita` (`S-2`) y `rango_impreso` (`E-1 @ E-2`, tal cual está impreso). El usuario la llena; nunca se deduce. Un nivel admite varios rangos, decisión del Líder del 23/11 por la corrida 1 de T5.
  - Endpoints `GET/PUT /api/proyectos/{id}/equivalencias-nivel`, con auditoría y respaldo de la BD antes de escribir.
  - En el cruce: cuando el diseño no trae EJES (los tiene `pendiente de verificar`), se cruza por ID + nivel (decisión D11 de la Fase A, A1 §6.2). El nivel de la visita se traduce con la tabla, y los EJES del informe son los de la visita.
  - Con la tabla vacía o sin la fila del nivel, se abre una duda clara («falta la equivalencia S-2 → rango impreso»).
  - Normalización exacta del nivel para comparar: mayúsculas, espacios repetidos colapsados y sin espacios alrededor del guion (`SOTANO S - 2` → `SOTANO S-2`). Nada más.
  - Buscar en el plano vectorial, solo lectura, una tabla o corte impreso que relacione sótanos con E-n. Si existe, va en `PLANES/etapa-7-niveles.md` como propuesta citada (página y textos), **sin aplicarla**.
- Criterios de aceptación:
  - [ ] Pruebas de equivalencia presente, ausente y ambigua (dos candidatos), de diseño con EJES (no cambia nada) y de la normalización.
  - [ ] Un elemento de diseño con EJES reales sigue exigiendo los mismos EJES (§4.2).
  - [ ] Suite verde (solo las 2 fallas conocidas de Dropbox).
- Reglas: Regla de Oro, §4.2, §4.4, error 11.

### T7 — Cabecera del proyecto propuesta desde un STP-MIVED entregado
- Ejecutor: ejecutor-backend, después de T6 (los dos tocan `database.py` y `main.py`).
- Archivos: `BACKEND/sync/cabecera_propuesta.py` (nuevo), `BACKEND/main.py`, `BACKEND/tests/test_cabecera_propuesta.py`.
- Depende de: T6 (por los archivos compartidos).
- Qué hacer:
  - Leer, solo lectura, la portada y la cabecera de un STP-MIVED entregado de Terra Living (`INFORMES\2.DATA PROCESADA\`).
  - Proponer `no_solicitud`, `no_licencia`, `direccion_obra`, `provincia`, `sector` y `residente_obra`. Cada valor cita el archivo y la página.
  - Lo que el informe no trae queda `pendiente de verificar`.
  - Se guarda como propuesta pendiente, con una duda para que Steven la confirme. Nada se escribe como confirmado en `proyectos`.
- Criterios de aceptación:
  - [ ] Cada valor propuesto lleva su cita.
  - [ ] Si dos informes dicen cosas distintas, el campo queda en duda y no se elige uno.
  - [ ] La BD real y Dropbox no cambian.
- Reglas: Regla de Oro, §3.1 (la dirección de CATDIC no es la de la obra).

### T8 — Recuadros propuestos: DETALLE desde la `zona` de T1 y LOCALIZACIÓN con el visor
- Ejecutor: ejecutor-backend.
- Archivos: `BACKEND/plano/recuadros_propuestos.py` (nuevo), `BACKEND/tests/test_recuadros_propuestos.py`. `visor.py` solo si hace falta exponer algo.
- Depende de: — (los datos de T1 están en las notas del Director, `t1-visita24\`).
- Coordinación con la Fase A: el importador (`BACKEND/plano/asistido/importar.py`) vive en la rama `claude/etapa5-fase-a-3da668` y **no se toca desde aquí**.
  - T8 es un paso aparte, en esta rama, que lee las `propuesta.json` ya importadas.
  - Engancharlo al importador después es una línea en la rama de la Fase A, y queda anotado para su Líder.
- Qué hacer:
  - DETALLE: la `zona` de cada elemento de `propuesta.json` se guarda en `recorte_detalle_json` con estado pendiente.
  - LOCALIZACIÓN: con `visor._proponer_localizacion` sobre la planta de S-2 (p24), también pendiente.
  - Nunca se escriben como confirmados. Un recuadro que ya estaba confirmado no se pisa.
- Criterios de aceptación:
  - [ ] Pruebas de zona presente, ausente e inválida, de recuadro confirmado que no se pisa y de ID ambiguo en la planta (no se propone).
  - [ ] Suite verde.
- Reglas: Regla de Oro, M3 y M4 (§4.7), errores 1, 2 y 4.

### T9 — Derivación de las filas f, g, h, m y n de COLUMNA (propuesta)
- Ejecutor: ejecutor-generadores. Pedido por el Director el 24/11 tras la corrida 3 de T5: C1 y C3 quedan «listo», pero el STP no sale porque falta la fila `f`.
- Archivos:
  - `BACKEND/generators/mapeo_stp.json`, que sigue con `confirmado: false`;
  - `BACKEND/procesador_cola.py` (aplicar la derivación);
  - `BACKEND/tests/test_procesar_cola.py`;
  - `PLANES/etapa-7-mapeo-stp.md`.
- Incluye dos arreglos menores pedidos en la evaluación 3:
  - `equivalencias_nivel` en una BD sin `inicializar_bd()` no rompe el procesador;
  - la tabla `propuestas_proyecto` se crea en `database.inicializar_bd`.
- Depende de: T4 y T7.
- Qué hacer:
  - Derivaciones, solo con una regex exacta sobre los textos reales del plano (`9 EST. ∅3/8" @0.10`, `10 EST. ∅3/8"@0.10`, `36∅1"`) y copiando las partes tal como están impresas:
    - de `estribos` salen `h` (número + `EST.` + diámetro) y el espaciamiento para `f` y `g`;
    - de `acero_longitudinal` salen el diámetro para `m` y `n`.
  - Un texto que no cuadra abre una duda con el texto impreso.
  - El plano trae un solo espaciamiento y un solo diámetro. Que `f = g` y `m = n` lo decide Steven: va como nota en el MD y como duda que no bloquea en cada ficha. No se copia en silencio.
- Criterios de aceptación:
  - [ ] Pruebas de los textos reales, de texto que no cuadra y de la duda de `f = g`.
  - [ ] Pruebas de los dos arreglos menores.
  - [ ] Suite verde.
- Reglas: Regla de Oro, error 12 (la cuantía nunca se copia).

### T11 — Mapeo de las filas b, e, i y j de COLUMNA (propuesta)
- Ejecutor: ejecutor-generadores. Pedido por el Director el 24/11 tras la corrida 4 de T5: la ficha ya llena f, g, h, m y n, y se detiene en la fila `e`. También faltan `b`, `i` y `j` (pregunta 6 de `etapa-7-mapeo-stp.md`).
- Archivos:
  - `BACKEND/generators/mapeo_stp.json` (sigue con `confirmado: false`);
  - `BACKEND/procesador_cola.py` (reglas de conversión);
  - `BACKEND/tests/test_procesar_cola.py`;
  - `PLANES/etapa-7-mapeo-stp.md`.
- Depende de **T10 de la Fase A**: lectura con citas, sin confirmar, de `fc`, `barras_cara_x`, `barras_cara_y` y `altura_m` (esta última solo si está impresa) para C1 y C3. **No se empieza hasta el aviso del Director.**
- Qué hacer:
  - **b ← `fc`:** solo el número en kg/cm² cuando el texto lo trae así (p. ej. `f'c = 350 kg/cm²` → `350`). Si viene en MPa o psi, o con otra unidad, va a duda con el texto impreso. No se convierte sin la aprobación de Steven.
  - **i ← `barras_cara_x` y j ← `barras_cara_y`:** con el formato del informe entregado, `6-∅1"` (S-2 Completivo, pág. 5). La conversión es exacta desde el texto que lea T10. Si no cuadra, va a duda.
  - **e ← `altura_m`:** solo si es un número en metros impreso en el plano. Sin el dato, la fila sigue pidiéndolo con su duda.
  - En las tres conversiones, el símbolo y la comilla se copian tal como vienen.
  - La evidencia por fila se compara contra el STP de la visita 24: C1 tiene b 350, e 2.95, i `6-∅1"` y j `14-∅1"`; C3 tiene j `16-∅1"`.
- Criterios de aceptación:
  - [ ] Pruebas de los textos reales de T10, de las unidades que no son kg/cm² (van a duda) y del texto que no cuadra.
  - [ ] La tabla del MD está actualizada con su ejemplo real.
  - [ ] Suite verde.
- Reglas: Regla de Oro, error 12. No se convierte ninguna unidad sin la aprobación de Steven.

### T11b — Fila k de COLUMNA y todas las filas faltantes en una sola duda
- Ejecutor: ejecutor-generadores. Pedido por el Director el 24/11 tras la corrida 5 de T5 (`PLANES/etapa-7-prueba.md`, hallazgos H1 y H2).
- Archivos: `BACKEND/generators/mapeo_stp.json` (sigue `confirmado: false`), `BACKEND/procesador_cola.py`, `BACKEND/tests/test_procesar_cola.py`, `PLANES/etapa-7-mapeo-stp.md`.
- **H1:** k ← total de un único grupo de `acero_longitudinal` (`36∅1"` → `36`), con la misma regex exacta `_RE_BARRAS_UNICO`. Si no cuadra, abre la duda `derivacion.k`. Se anota en la nota del JSON y en las preguntas para Steven.
- **H2:** las filas que faltan del plano salen en **una sola duda por elemento**, que las lista todas en orden alfabético fijo (como la duda de OBRA). Hoy queda solo la primera y, como `OBLIGATORIAS` es un `set`, la letra cambia entre corridas.
- Criterios de aceptación:
  - [ ] Una columna sin b, e ni k muestra las tres, en el mismo orden, en dos corridas.
  - [ ] C1 y C3 llenan k (36 y 40) con los textos reales de T10.
  - [ ] Suite verde y prueba en seco sobre una copia de la BD de T10.

### T11c — La duda de OBRA se actualiza cuando cambia la lista
- La hizo el Líder (cambio de una línea). Pedido por el Director el 24/11 tras revisar T11b.
- **Problema:** `obra:pNNN` conservaba el texto de su primera corrida, así que seguía nombrando celdas que el técnico ya había completado.
- **Arreglo:** `duda(..., actualizar=True)` (la de T11b), con las celdas en orden fijo. Si la lista cambia, el texto se actualiza con auditoría `ACTUALIZAR_DUDA`; si no cambia, no se audita nada.
- Prueba: `test_t11c_la_duda_de_obra_se_actualiza_al_completar_una_celda`.

### T12 — LOCALIZACIÓN = solo la planta (sin cajetín) con el elemento destacado
- Decisión de Steven del 24/11, comunicada por el Director: el recuadro rojo está bien; lo que falla es que hoy sale la hoja entera, con el cajetín, los detalles y las notas.
- Ejecutores: **ejecutor-backend + ejecutor-generadores (T12a)** y **ejecutor-frontend (T12b)**, a la vez con el contrato de abajo. No comparten archivos: T12b solo toca `FRONTEND/index.html`.

**Contrato**
- **Tabla `zonas_planta`** (migración no destructiva en `database.py`, creada también en `inicializar_bd`):
  - `id`, `proyecto_id`, `plano_id INTEGER NOT NULL`, `pagina INTEGER NOT NULL` (de 1 en adelante, como `recorte_planta_json.pagina`);
  - `rect_json` en puntos del PDF, `[x0, y0, x1, y1]`, o NULL;
  - `estado`: `vacia`, `pendiente de verificar` o `confirmado`;
  - `origen`: `propuesta_ejes` o `manual`;
  - `fuente_json` (rótulos usados y margen), `motivo`, `actualizado_por`, `actualizado`;
  - `UNIQUE(plano_id, pagina)`: una zona por hoja, que comparten todos los elementos de esa planta.
- **Propuesta automática** (`BACKEND/plano/zona_planta.py`):
  - Toma la envolvente de los rótulos de ejes de la hoja en el vectorial, más un margen fijo documentado.
  - Un rótulo de eje es un texto que es solo una letra (`A`, `A'`) o solo un número (`1`, `2'`), que se repite alineado (los globos de los dos extremos de la retícula).
  - Hacen falta al menos 2 letras y 2 números. Si no, la zona queda `vacia`, con su motivo y su duda.
  - La propuesta siempre queda «pendiente de verificar» y nunca pisa una zona confirmada.
  - La duda es de proyecto: `plano:<plano_id>:p<pagina>:zona_planta`.
- **Regla anti-zoom (error 1):**
  - Una zona que no contiene todos los rótulos de ejes detectados en la hoja es un zoom parcial: al guardar se rechaza con un mensaje claro.
  - Si la hoja no tiene ejes detectables, se acepta la zona manual y se audita.
- **API** (router del visor):
  - `GET /api/proyectos/{pid}/visor/hojas/{pagina}/zona-planta` devuelve `{estado, rect, origen, fuente, motivo, ejes_rect}`. `ejes_rect` es la envolvente detectada, o null.
  - `POST …/zona-planta/propuesta` propone; `PUT …/zona-planta` con `{rect}` confirma (origen `manual` si cambió el rect). Todo queda auditado con el usuario del proceso.
  - `POST /api/proyectos/{pid}/visor/vista-previa` acepta además `zona` (pt), opcional.
- **Generador** (`generators/comun/localizacion.py`): `generar_localizacion(..., zona=<px>)`.
  - Recorta la planta a la zona y traslada la caja.
  - El grosor se recalcula sobre el tamaño ya recortado (error 4).
  - Una caja que no cae entera dentro de la zona da ValueError «pendiente de verificar»: nunca se recorta el recuadro.
  - Sin zona no hay vuelta a la hoja entera; el error lo maneja quien lo llama.
- **Procesador:**
  - Sin zona confirmada en el plano vigente, abre la falta `diseno:pNNN:zona_planta` y la ficha no se genera.
  - Si la caja queda fuera de la zona, abre `diseno:pNNN:zona_planta_fuera`.
- **Visor (T12b):**
  - Una tarjeta «Zona de planta (hoja N)» con los mismos estados que los recuadros: vacía, propuesta (naranja «propuesto · confirma o ajusta») o confirmada.
  - Botones «Proponer zona» y «Confirmar y guardar». Al dibujar con el tipo «zona» marcado, el borrador queda como zona.
  - La zona se dibuja sobre la hoja con otro color que el de los recuadros.
  - La vista previa de LOCALIZACIÓN usa la zona.
  - Se mantiene el tablero clásico.

**Línea propuesta para CLAUDE.md §4.7 M3** (para el PR; el CLAUDE.md no se toca en esta etapa):
> **M3 (Localización):** planta estructural **entera del nivel, recortada a su dibujo** (sin cajetín, tablas, notas ni otros dibujos de la hoja); nunca la hoja completa con el cajetín y nunca un zoom a una parte de la planta. La zona de planta se confirma una vez por hoja. Recuadro(s) rojo(s) `RGB(220,0,0)` con grosor compensado sobre la imagen ya recortada.

- Criterios de aceptación:
  - [ ] Pruebas con un PDF sintético: propuesta por ejes, menos de 2 ejes da vacía con duda, regla anti-zoom, recorte con caja trasladada y grosor recalculado, caja fuera de la zona da duda y sin zona no hay ficha.
  - [ ] Prueba en seco sobre una copia de la BD de la corrida 6 (hoja 24, S-2): imagen de LOCALIZACIÓN de C1 enviada al Director.
  - [ ] Suite verde; la BD real y Dropbox, sin tocar (Dropbox solo se lee).

## Respuestas de Steven del 26/11/2026 (las transmitió el Director, palabras textuales)
- (4) «SEGUN PLANOS, PARECE SER UN ERROR DE CAMPO» → C3 LY = 1.50, porque manda el plano. No requiere código; se comprueba en el STP.
- (5) «S-2 SIGNIFICA SOTANO -2. PERTENECE A FUNDACIONES A @ E-1» → S-2 queda entre FUNDACIONES y E-1, así que cae en todo rango que empiece por FUNDACIONES.
- (6) «QUIERO ARREGLARLO DENTRO DE LA APP… SI, ES ASI MISMO» → la cabecera actual es correcta y debe poder editarse en la app.
- (8) «LOS MUROS SON UNICOS EN EL PLANO, ESTO ES UN PATRON QUE HACEMOS EN CAMPO, SI SOLO HAY 1 MH1, PUES NO TIENES QUE VOLVER A DESCRIBIRLO».
- (9) «TODOS LOS MUROS DE CONTENCION SIMPLEMENTE UNO LO LLAMA MC Y YA».
- Reglas del mapeo 10 a 16 aprobadas (la 15 solo si la malla es simétrica: si el plano trae caras distintas, manda el plano). `confirmado` sigue en false hasta que respondan la 17 y la 18.
- Siguen abiertas: el área de ∅1" (5.10 o 5.07), la altura de columna, la 17 y la 18.

### T13 — Ejes de muros desde el plano y «MC» como ID
- Ejecutor: ejecutor-backend (junto con T14). Archivos: `BACKEND/procesador_cola.py` (`_candidatos` y el cruce), `BACKEND/sync/lector_visita.py` (solo si hace falta para «MC») y sus pruebas.
- **Muro con ID único:** si la visita no trae los ejes de un muro (MURO H.A. o MURO DE CONTENCION) y su ID es único en ese nivel del plano, ya con la equivalencia aplicada, los EJES se toman de `elementos_diseno`. No se abre duda de obra, y la auditoría y la ficha registran que los ejes vienen del plano.
- **Plano sin ejes:** si el diseño tampoco trae ejes, quedan «pendiente de verificar» y la duda es de **diseño** (`diseno:pNNN:ejes`), no de obra.
- **MC:** una etiqueta «MC» (mayúsculas o minúsculas, sin número) es un ID válido de MURO DE CONTENCION.
  - Si hay un solo MC en ese nivel, se toma ese.
  - Si hay varios y la visita no trae ejes que los distingan, hay duda; nunca se elige por cercanía.
- **Pruebas:** MH2 y MH3 de la visita 24 (ejes desde el plano), el MC del eje 4', un ID repetido en el nivel (duda) y un plano sin ejes (duda de diseño).

### T14 — Equivalencia S-2 confirmada por Steven
- Ejecutor: ejecutor-backend (junto con T13). Archivos: `BACKEND/equivalencias_nivel.py`, un archivo de configuración nuevo con la respuesta de Steven y sus pruebas.
- **Configuración en git:** por proyecto, `S-2` → todo rango impreso del diseño que empiece por `FUNDACIONES @`, con la cita literal de Steven, la fecha 26/11/2026 y «confirmado_por: Steven».
- **Cruce:** `equivalencias_de` suma las filas de la BD y las de la configuración, expandidas contra los rangos del diseño de ese proyecto.
- **Listado:** el endpoint marca cada fila con su origen (`bd` o `configuracion_confirmada`).
- **Escritura:** nada se escribe en la BD real. En una **copia** de la BD de la corrida 6, las filas de hipótesis se reemplazan con auditoría.

### T15 — Cabecera del proyecto editable en la app
- Ejecutor: ejecutor-frontend (backend pequeño más tablero). Archivos: un router nuevo `BACKEND/cabecera_proyecto.py` registrado en `main.py`, `FRONTEND/index.html` y sus pruebas.
- **Campos:** solicitud, licencia, dirección, provincia, sector, residente y CODIA, con las columnas reales de `proyectos`.
- **Endpoints:** `GET` y `PUT /api/proyectos/{id}/cabecera`.
  - Cada campo que cambia queda en `auditoria` con su valor anterior y el nuevo.
  - Sin cambios, no se escribe nada.
  - Solo se aceptan textos (se les quitan los espacios de los extremos); un campo vacío se guarda vacío, también con auditoría.
- **Duda de la cabecera:** guardar resuelve, con auditoría, la duda de proyecto `proyecto.cabecera_propuesta` si estaba abierta.
- **Tablero:** una tarjeta «Cabecera del proyecto» en la vista del proyecto, para ver y editar. Muestra la propuesta de T7 al lado si existe. Se mantiene el tablero clásico.

### T16 — Área de ∅1" = 5.07 cm² (decisión de Steven)
- Steven, 26/11/2026: «5.07 (como mi informe)». Respondió después de que el Director le explicara que ASTM A615 #8 da 5.10.
- La hace el Líder, en cola detrás de T13 y T14 para no compartir `reglas_ingenieria.py`.
- **Cambio:** en `AREA_BARRA_CM2`, `'1"'` y `'#8'` pasan de 5.10 a 5.07, con el comentario «decisión de Steven 26/11/2026, coincide con sus informes entregados». Los demás diámetros no se tocan.
- **Pruebas:**
  - Se ajustan las que dependían del 5.10.
  - Una nueva con C1: 36∅1" en 0.60 × 1.50 da 0.0203 (36 × 5.07 / 9000 = 0.02028).

## Paralelismo
- T1, T2 y T3 a la vez (no comparten archivos). T4 espera a T1. T5 al final.
- T6 y T8 a la vez; T7 después de T6 (comparten `database.py` y `main.py`).
- La Fase B (B5b) sigue en su sesión; no comparte archivos con esta etapa.

## Pendientes de verificar / preguntas para Steven (al volver)
1. Confirmar el mapeo de filas de T4.
2. Confirmar los datos del plano que importe T1 (pantalla «Confirmar plano») y los recuadros de LOCALIZACIÓN y DETALLE (visor).
3. Reemplazar Campo en uso por la copia v11 cuando esté aprobada.
4. Las 3 dudas reales de la visita 24: ejes de MH2 y MH3, e ID del muro de contención del eje 4'.

## Fuera de alcance
- Leer el resto de Terra Living con IA (se hace después, por lotes, cuidando el cupo semanal).
- CATDIC-STP, MIVED FI y los formatos HV.
- Push, PR y fusiones (las hace Steven).
