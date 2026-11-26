# B3e · Mesa de Dudas con visor de revisión (Fase B, Etapa 5)

Ejecutor: Claude Sonnet 5.5. Rama `claude/etapa5-fase-b-0020e1`. Pedido por Steven el 22/11/2026 (referencia: PlanRadar, lista a un lado, plano al otro).

## Commits (locales, sin push)

| Hash | Qué |
|---|---|
| `e7436b6` | Backend: `GET /api/dudas/{id}/refs` + `BACKEND/tests/test_dudas_refs.py` |
| `233b64a` | Visor de revisión compartido (`js/visor-revision.js`) |
| `6d749b4` | Mesa de Dudas, rutas propias, CSS e `index.html` |
| `233372c` | Dudas abiertas en la Bandeja y enlaces a la Mesa |
| (este informe) | `PLANES/etapa-5-reportes/B3e.md` |

## Archivos tocados

Backend (solo la excepción del encargo): `BACKEND/mesa_dudas.py` (función `leer_refs_duda` y la ruta `/refs`), `BACKEND/tests/test_dudas_refs.py` (nuevo, 9 pruebas).

Frontend: nuevos `js/visor-revision.js`, `js/mesa-dudas.js`, `js/dudas-bandeja.js`. Modificados `js/rutas.js` (`hashVisita(obra, visita, duda)` y `hashMesaObra(obra, duda)`), `js/pestana-visitas.js` (la Mesa sustituye la vista de solo lectura de B3d), `js/pantallas/obra.js` (Mesa en modo obra), `js/pantallas/obras.js`, `js/datos.js` (el enlace de las dudas de obra va a la Mesa), `js/pantallas/bandeja.js`, `js/cola.js`, `js/avance-trabajo.js`, `js/cola-acciones.js`, `css/base.css` (sección B3e al final), `index.html` (3 scripts).

## Contrato de `GET /api/dudas/{id}/refs`

- 200 `{ "duda_id": N, "refs": { "elemento": {…}|null, "plano": {…}|null, "visita_pdf": {…}|null } }`.
- Sale del evento `duda` más reciente de `trabajo_eventos` (`json_extract(datos_json,'$.duda_id')`; más reciente = mayor `creado`, luego mayor `n`).
- Duda sin evento: 200 con `refs: null`. Duda inexistente: 404. Solo lectura. No cambia `GET /api/dudas`.
- `plano` trae `plano_id`, `pagina`, `bbox`, `recuadro`, `uid_diseno`.

## Visor compartido (`js/visor-revision.js`)

`<VisorRevision>` props: `obraId` (obligatoria) · `uid` · `recuadros` ({localizacion, detalle}, alternativa a `uid`) · `etiqueta` · `paginaInicial` · `notaPagina` · `motivoSinElemento` · `hayPlano` (false = no pedir nada al visor). Eventos: `ubicado` (estado de cada pieza: confirmado, propuesta, pendiente, error, cargando), `abrir`, `cerrar`.
`<VisorPlano>` (diálogo a pantalla completa) props: `obraId`, `pagina`, `localizacion`, `detalle`, `etiqueta`, `nota`. Evento `cerrar`. `C.visor.olvidar(obraId?)` vacía la memoria (úsalo tras guardar un recuadro).

Cómo lo usarán B3c y B3b: `<VisorRevision :obra-id="obra.id" :uid="elemento.uid"/>` junto a la revisión del elemento, o con `:recuadros` si ya tienen el recuadro en la mano; tras `PUT …/recuadro` llamar a `C.visor.olvidar(obra.id)` y cambiar la `key` del componente.

Comportamiento:
- Recuadro confirmado con el `plano_id` del plano vigente: se dibuja. De otro plano: «pendiente de verificar» con el motivo y sin llamar a `vista-previa`. Sin confirmar: se pide `…/propuesta` y se rotula «Propuesta, pendiente de verificar» con su fuente. Sin nada: «pendiente de verificar» con el motivo. Nunca se adivina por cercanía.
- Imágenes por `fetch` + `URL.createObjectURL`, se liberan al desmontar; memoria de 60 s (índice, elementos, propuestas) y tope de 40 vistas y 3 hojas.
- Abrir plano: zoom con rueda, botones, pellizco y teclas (+ − 0), desplazamiento con arrastre y flechas, R va al recuadro, selector de hoja, foco atrapado, Escape cierra y el foco vuelve al botón. El trazo rojo (`--rojo-plano`) mide 3 px en pantalla a cualquier zoom (se divide por la escala). El detalle se dibuja azul punteado.
- Hoja muy grande: se rasteriza a menos dpi (el servidor admite 30 como mínimo): una hoja de 14400×10800 pt sale de 6000×4500 px.

## Mesa de Dudas (`js/mesa-dudas.js`)

- Rutas: `#/obra/<id>/visitas?visita=<vid>[&duda=<id>]` y `#/obra/<id>/resumen?dudas=obra[&duda=<id>]`. «Cerrar» vuelve a la cola de la obra o al Resumen. Atrás funciona.
- Lista a un lado y duda con visor y respuesta al otro (≥ 860 px de la propia caja); en estrecho se apilan, con «Volver a la lista».
- Todos los controles de M1 por prioridad (revisado, campo confirmable, texto, fecha, clase, estado con STP, archivos, otro), los avisos `data-aviso-plano` / `data-aviso-etiqueta`, el error por duda, el bloqueo del doble envío, el 409 con « Se recargaron las dudas.», el aviso de éxito (A26) y el de «Procesada con bloqueantes». Tras responder se recargan dudas, visita y tablero. Ningún PATCH se reintenta solo.
- Atado de la duda a su elemento: duda de visita por `refs.plano.uid_diseno`; duda de obra T6n por `campo_confirmable.uid`; nunca por `id_elemento`. Sin atado: solo «Abrir plano» (en la hoja citada, o la primera del índice) y Ubicación/Detalle «pendiente de verificar».
- Desde el avance en vivo cada duda enlaza a `&duda=<id>`; en cola.js el texto «clic para responder» es ahora el enlace «Abrir la Mesa de Dudas».
- Apertura automática (A2/A31): no se abre nada por sorpresa. Tras sincronizar o subir una visita, el resultado muestra «N dudas nuevas · Abrir la Mesa de Dudas». Paridad cubierta con otro patrón.
- Bandeja: «Dudas abiertas (todas las obras)» agrupa por obra y visita, con las de obra aparte, contadores de bloqueantes y hallazgos y enlace a cada Mesa. Una sola lectura `GET /api/dudas?resuelta=false`. El resto de la Bandeja sigue como Fase D-a con su aviso.

## Paridad del inventario

§9 «Mesa de Dudas»: cubiertos todos los ítems salvo dos. Panel lateral con cierre por X y fondo: sustituido por D6 (pantalla con ruta propia y botón «Cerrar»). Apertura automática: cubierta con otro patrón (enlace). T10b: queda cubierto el responder dudas desde el avance (enlace a la Mesa).

## Decisiones y preguntas abiertas

1. «Fotos p. X–Y»: se calcula de `refs.visita_pdf` (`pagina`, y `paginas` si es lista). Si `paginas` es un número, solo se muestra «Foto p. N»: no se infiere un rango.
2. `refs.plano.recuadro` no se usa para dibujar (no se conoce su sistema de coordenadas); solo `uid_diseno` ata la duda.
3. Una hoja muy grande se limita por el dpi mínimo del servidor (30), así que puede pasar de 5000 px de lado (6000 en la prueba).
4. «Guardar estado» con «corresponde» en la obra sintética devuelve 422 «El proyecto no tiene carpeta_dropbox»: es la regla del servidor, mostrada por duda.
5. Los 409/422 de las pruebas aparecen en la consola del navegador como «Failed to load resource»; son los códigos de la API, no errores de la pantalla.

## Cómo aislé las escrituras

Servidor en el puerto 8766 con una COPIA de la BD y las cinco `CATDIC_*` en el scratch; nada contra `C:\Users\Steve\CATDIC Dropbox\`. Obra, planos (PDF vectorial generado con PyMuPDF, uno con una hoja de 14400×10800 pt), elementos, visitas y dudas, todo rotulado SINTÉTICO. Servidor detenido al terminar.

## Playwright (Chromium, 5 anchos × claro y oscuro)

Resultado: 128 comprobaciones de matriz, 0 fallas; 25 de casos del visor, 0 fallas; 24 de controles, 0 fallas.

| Comprobación | Resultado |
|---|---|
| 375, 768, 1024, 1280, 1920 px, claro y oscuro | Mesa visita, Mesa obra, Bandeja y Abrir plano sin desborde horizontal |
| Peticiones fuera de 127.0.0.1:8766 | 0 |
| Errores de consola | 0 (salvo el registro del navegador de los 409/422 buscados) |
| Foco, Tab atrapado, Escape y retorno del foco | correcto en todos los anchos |
| Zoom y desplazamiento (teclado, rueda, arrastre, botones) | correcto |
| Recuadro rojo | 375 px: 187×187 px en pantalla, trazo 3 px; 1920 px: 396×396 px, trazo 3 px |
| Atrás | vuelve a la lista (estrecho) |
| Casos del visor | confirmado, solo propuesta, sin nada, de otro plano, sin plano vigente, `refs` null, sin `uid_diseno`, T6n de obra, duda de obra sin campo: todos con su texto |
| Controles | revisado, campo (422 y valor), texto, fecha (422 y valor), clase, estado (con STP, sin STP), archivos, otro, 409, doble envío, error de conexión, aviso «Procesada» |

## Peor caso

40 dudas de 600 caracteres con campos vacíos en una visita y 376 dudas abiertas en la Bandeja (48 grupos): sin desborde a 375, 1280 y 1920 px; la Mesa abre en unos 2 s y la Bandeja en 1 s.

## Suite

Corrida 1 (todo en el scratch): 962 passed, 7 skipped, 0 fallas (1:51). Corrida 2 (sin `CATDIC_DROPBOX_RAIZ`): 964 passed, 2 failed, 3 skipped (2:02); las 2 fallas son solo las de Dropbox real: `test_escaner_dropbox.py::test_terra_living_real` y `test_parser_visitas.py::test_lista_coincide_con_dropbox_si_esta_disponible`.

## Limitaciones

- No se probó contra los planos reales ni contra Dropbox (por orden del encargo).
- La rueda del ratón y el pellizco se probaron con ratón; el pellizco táctil no se ejercitó en un dispositivo.
- La búsqueda de «clasico»/«clásico» en `FRONTEND/` (sin `clasico/`, `maquetas/`, `vendor/`) da 0 resultados.

Carpeta de pruebas y capturas: `C:\WINDOWS\TEMP\claude\5241ace622d5cd23\bde6ad2c-34d6-42aa-bdc5-6b0fd7ef0f32\scratchpad\b3e\` (capturas en `capturas\`).
