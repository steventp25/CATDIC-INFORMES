# B3c — Revisión de planos: Confirmar datos del plano (M6) — encargo del Líder al Ejecutor

Fecha: 23/11/2026. Va 7.ª en el orden de B3: B3a ✔ → B3d ✔ → B3g ✔ → B3e ✔ → B3g-2 ✔ → B3b ✔ → **B3c** → B3f. La lanzó el Director el 23/11 («Adelante con B3c», sin push). Estilo **Plano sellado** (`FRONTEND/DESIGN.md`).

## Dónde se trabaja (igual que en B3b)
- **Worktree y rama:** `C:\Users\Steve\OneDrive\Desktop\CATDIC-WEB\.claude\worktrees\etapa2-t7n-confirmacion-8210cf`, rama `claude/etapa5-fase-b-0020e1`.
  - No crees ni cambies de rama. Nada de push, merge, stash, checkout ni reset. No toques el checkout principal.
  - Trabajas por turnos con el Líder.
- **Zona:** `FRONTEND/**` (menos `maquetas/`, `clasico/` y `vendor/`) y `PLANES/etapa-5-reportes/B3c.md`.
  - **B3c no tiene excepción de backend: no se toca nada de `BACKEND/`.** Las rutas de M6 ya existen (`BACKEND/plano/extractor.py` y `BACKEND/plano/confirmacion.py`). Léelas para saber qué devuelven, sin modificarlas.
  - Si algo necesita backend nuevo, se rotula «Fase D» o «pendiente de verificar», se anota en el informe y no se simula.
- **Tablero clásico.** Steven, 20/11: «Conserva el tablero clásico. Su eliminación no queda autorizada».
  - No borres ni edites `FRONTEND/clasico/` ni `BACKEND/tests/test_frontend_servido.py`.
  - Ninguna mención ni enlace al clásico en el tablero nuevo.
  - El clásico (`FRONTEND/clasico/index.html`, líneas 604–708 y las funciones 1270–1350 que cita B0) se puede **leer** como referencia de comportamiento.
- **Python:** `C:\Users\Steve\AppData\Local\Python\pythoncore-3.14-64\python.exe`.

## Reglas (siguen todas las de B2–B3b)
- **Sin red ni compilación:** scripts clásicos sobre `window.CATDIC`, Vue local, sin librerías nuevas.
- **Reutiliza, no copies:**
  - `js/componentes.js` (`Bloque`, `Pendiente`, `FaseD`, `Icono`, `Cajetin`), `C.api` (incluido `C.api.pedir` con `respuesta: 'blob'`), `C.formato`;
  - `VisorPlano` y `VisorRevision` (`js/visor-revision.js`), con `C.visor.olvidar`;
  - la Mesa de Dudas (`js/mesa-dudas.js`), en modo obra con `#/obra/<id>/resumen?dudas=obra`;
  - `pestana-planos.js` de B3b, que tiene el sitio reservado de B3c.
  - Si un componente necesita crecer, extiéndelo con props sin romper a sus usuarios y dilo en el informe.
- **Regla de Oro:**
  - Nada se confirma solo.
  - Lo dudoso no se confirma (N19). Un valor sin fuente o que contradice la tabla se muestra como «pendiente de verificar», con salida a la Mesa de Dudas.
  - No se inventan valores, nombres de tabla ni comprobaciones: se muestra lo que trae el servidor, y lo que falte es «pendiente de verificar».
  - Atar por `id_elemento` está prohibido. Si hay que identificar un elemento, se usa el `uid` que traiga el servidor.
  - Confirmar y certificar son acciones de Steven: cada una pide su casilla explícita («Revisé…», «Certifico…»), y el botón queda deshabilitado sin ella, como en el clásico.
- **Diseño:**
  - sin franjas laterales de color: el estado se muestra con un borde completo, un icono y texto («verde» y «rojo» con su palabra, nunca solo con el color);
  - container queries;
  - objetivos táctiles de 44 px o más en móvil;
  - foco visible.
- **Formato:** fechas `DD/MM/AAAA` y `DD/MM/AAAA HH:MM`; textos en español.
- **Commits:** atómicos, en español, terminados en `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Nunca capturas, PDFs ni `*.db`.

## Qué hay que construir
Lee B0 (`PLANES/etapa-5-inventario-ui.md`): §2 M6, §3.8 (A45–A51), §4 (fila «M6 Confirmar»), §5 (R22–R26 y R21), §9 «Confirmar datos del plano» y §10.5 (N16–N19). **Todo lo de M6 y §9 tiene que estar**, con sus textos y mensajes literales (A45, A47 y A48).

Como referencia de organización, mira la pantalla «Revisión de planos» de la maqueta aprobada (`FRONTEND/maquetas/v2/`, estilo `plano`): lista a la izquierda, plano en el centro y datos a la derecha. Es solo para **leer**; no se toca.

### 1. Entrada y ruta
- **Ruta:** `#/obra/<id>/planos?confirmar=1[&tabla=<tabla_id>]`. Recargar deja la misma tabla elegida; el Atrás del navegador funciona; «Cerrar» vuelve a «Planos y ficha».
- **Entrada:** en «Planos y ficha», el sitio reservado de B3b pasa a ser el botón **«Confirmar datos del plano»** (A14).
  - Solo funciona con plano vigente.
  - Sin plano vigente, el botón queda deshabilitado y dice el motivo; no se esconde.
- **Pantalla:** a pantalla completa, como el editor de recuadros de B3b. La barra superior dice «Confirmar datos del plano · <nombre de la obra>».

### 2. Barra superior
- **«Extraer del plano vigente»** (A45, `POST …/extraer-diseno`):
  - mientras espera, «Extrayendo…», sin doble envío; usa un `tiempo` largo, porque la extracción tarda;
  - al terminar, el mensaje literal de A45;
  - después recarga las tablas y las dudas.
- **«Mesa de Dudas de la obra»** (A49): abre la Mesa en modo obra.
  - Al volver con el Atrás, regresa a la misma tabla.
  - La Mesa sigue poniéndose a la vista y enfocando su encabezado, como se corrigió en B3e.
  - Junto al botón va el número de dudas abiertas de la obra (`GET /api/dudas?sin_visita=true&proyecto_id=`).
- Los mensajes de error y de éxito se anuncian con `aria-live`.

### 3. Lista de tablas (izquierda; R22 `GET …/tablas-extraidas`)
- Cada tabla es un botón:
  - con su nombre amigable (`acero_en_losa` «Acero en losa», `zapata_muro_lindero` «Zapata de muro lindero», `fc_por_rango` «f'c por rango», `losa_aligerada` «Losa aligerada»; cualquier otro, tal cual);
  - su insignia «verde» o «rojo», con texto e icono;
  - «pág. X · hoja Y · nivel_rango»;
  - «Falla: …» si es roja, y «No vigente: <motivo>» si no es vigente (atenuada, pero legible: contraste de 4,5:1 o más).
- Estados:
  - «Cargando tablas…»;
  - vacío: «Aún no hay tablas extraídas del plano vigente. Pulsa «Extraer del plano vigente».»;
  - error con «Reintentar».
- La tabla elegida se marca con algo más que el color: borde completo, `aria-current` y texto.

### 4. Detalle de la tabla (derecha; R23 `GET …/tablas-extraidas/{tabla_id}`)
- Sin tabla elegida: «Elige una tabla para ver sus filas propuestas junto al recorte del plano.». Mientras carga: «Cargando la tabla…».
- **Cabecera:** título, clave, página, hoja, nivel, «extraída DD/MM/AAAA HH:MM» y la insignia del resultado.
- **Comprobaciones:**
  - cada una con su icono y texto («cumple» o «falla»), no solo un check verde o una X roja, y con su detalle;
  - si está certificada, el texto «(certificada por X el … para el vectorial <sha12>…)».
- **Certificación de notas de modificación** (A47): solo si el detalle dice que es certificable.
  - Lleva la casilla «Certifico…» y el botón «Certificar que vale para el plano vigente» (mientras espera, «Certificando…»). Envía `{certifico:true, extraido_en}`.
  - Al terminar, el mensaje literal de A47, y se recargan la lista, las dudas y la tabla.
- **Recorte del plano** (A46: `POST …/visor/vista-previa` con `{tipo:'detalle', pagina, rect: recorte}` y respuesta blob):
  - sobre él, la caja roja de la celda resaltada;
  - al pasar el ratón **o el foco del teclado** por una fila de valores, se resalta su celda (A50);
  - sin recorte: «Sin recorte: la tabla no tiene celdas con posición.»;
  - si la imagen falla, se dice el error en su sitio;
  - la URL del objeto se revoca al cambiar de tabla y al cerrar (A51).
  - Si ayuda, añade «Abrir plano» con `VisorPlano`, en la página de la tabla.
- **Valores propuestos:**
  - una tabla semántica con las columnas Elemento, Campo («fila N»), Valor y Estado («confirmado» o «pendiente»);
  - si el valor difiere de la tabla, se muestra con su icono y el texto «tabla: …», no solo en rojo;
  - si no hay filas: «Ningún elemento toma valores de esta tabla.»;
  - en móvil, la tabla no puede desbordar la página: usa su propio contenedor con desplazamiento, o pasa a tarjetas.
- **Confirmación por lote** (A48): solo si el detalle dice que se puede confirmar.
  - Lleva la casilla «Revisé…», con el texto de identidad pendiente si lo trae, y el botón «Confirmar tabla completa» (mientras espera, «Confirmando…»). Envía `{confirmo:true, extraido_en}`.
  - Al terminar, el mensaje literal de A48, con los conflictos y las dudas cerradas, y se recargan la lista y la tabla.
- **Si la tabla es roja:** el bloque de tabla roja con «Ir a la Mesa de Dudas». **Si no se puede confirmar:** «No se puede confirmar: …» con el motivo del servidor.
- Un 409 o un 422 del servidor muestra su `detail` tal cual. Ningún POST se reintenta solo.

### 5. Adaptación (N17)
- **Escritorio** (1024 px o más): lista a la izquierda y detalle a la derecha, con el recorte en el detalle.
- **Móvil:** pasos. Lista → tabla (comprobaciones, recorte, valores, confirmar), con un botón «Volver a las tablas» que no pierde la selección.
- En ningún ancho hay desplazamiento horizontal de la página.

## Cómo se prueba (las reglas de B3b)
- **Servidor:** backend desde este worktree, con una **copia** de la BD en el scratch; las 5 variables `CATDIC_*` apuntan al scratch; puerto **8766**. No cierres el 8765 ni el 8767, nunca uses el 8000 y apágalo al terminar.
- **Dropbox:** nada contra `C:\Users\Steve\CATDIC Dropbox\`.
- **Datos:**
  - la obra sintética de B3e y B3b tiene plano vigente y elementos, pero **0 filas en `tablas_extraidas`**;
  - prueba primero «Extraer del plano vigente» sobre ella y anota lo que sale;
  - si no salen tablas, **siembra en la copia de la BD**, con un script del scratch, filas sintéticas de `tablas_extraidas` (y `certificaciones_tabla` si hace falta), con la forma que esperan `extractor.py` y `confirmacion.py`;
  - casos mínimos: una verde confirmable; una roja con «Falla»; una no vigente; una certificable; una sin recorte; y una con un valor que difiere de la tabla;
  - todo rotulado como sintético en el script; nada se siembra en una BD real.
- **Playwright** (Chromium) a 375, 768, 1024, 1280 y 1920 px, en claro y oscuro. Comprueba:
  - 0 peticiones fuera de `127.0.0.1:8766`;
  - 0 errores de consola (salvo los 4xx esperados, anotados);
  - sin desplazamiento horizontal;
  - el Atrás del navegador;
  - la recarga con `&tabla=`;
  - el resaltado de la celda con ratón y con teclado;
  - las casillas que bloquean los botones;
  - confirmar y certificar de verdad sobre la copia, con sus mensajes;
  - que la Mesa se abra a la vista y que el Atrás vuelva a la tabla;
  - los estados: cargando, vacío, error de la lista, error del detalle, error del recorte, 409 o 422 con su `detail`, y sin plano vigente.
- **Peor caso:** 60 tablas, 400 filas de valores, nombres y valores de 120 caracteres, campos nulos y un GET lento.
- **Suite del backend** desde `BACKEND/`, dos veces: todo en el scratch, y sin `CATDIC_DROPBOX_RAIZ`. Solo pueden fallar las 2 de Dropbox.
- **Búsqueda final** de «clasico» y «clásico» en `FRONTEND/` (sin `clasico/`, `maquetas/` ni `vendor/`): 0 resultados.

## Informe
`PLANES/etapa-5-reportes/B3c.md` con:
- archivos tocados;
- componentes reutilizados y cómo se ampliaron;
- la paridad marcada contra B0 §9 «Confirmar datos del plano»;
- qué queda como Fase D o «pendiente de verificar»;
- el resultado de la extracción sobre la obra sintética y lo que se sembró;
- la tabla de Playwright;
- los estados;
- el peor caso;
- la suite;
- las limitaciones;
- los hashes;
- la carpeta del scratch con las capturas.
