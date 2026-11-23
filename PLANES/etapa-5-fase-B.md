# Etapa 5 · Fase B — Rediseño del tablero (estado de la fase)

Líder: sesión Opus (Líder de la Fase B) · rama `claude/etapa5-fase-b-0020e1` (sale de `claude/etapa5-plan`, `dab9cf0`).
Plan madre: `PLANES/etapa-5.md` (decisiones D5–D8, tareas B0–B5). Este archivo es lo que sobrevive a la compactación: se actualiza en cada paso.

## Reglas que mandan en esta fase
- Zona: `FRONTEND/**`, `DESIGN.md`, `PLANES/etapa-5-fase-B.md`, `PLANES/etapa-5-inventario-ui.md`, `PLANES/etapa-5-reportes/B*.md`. **No tocar `BACKEND/**`** (ni rutas, ni respuestas, ni `main.py`): lo que haga falta se pide al Director.
- Sin compilación (D5): varios archivos, Vue y Tailwind locales en `FRONTEND/vendor/`, funciona **sin internet**. El tablero viejo queda en `FRONTEND/clasico/index.html` **sin ningún enlace ni mención desde el tablero nuevo** (decisión de Steven, 19/11). **No se borra:** Steven, 20/11, «Conserva el tablero clásico. Su eliminación no queda autorizada» (B3h sin autorización).
- Nada de lo que hace hoy el tablero puede perderse (paridad con B0). Textos en español. Lo que falta se muestra como "pendiente de verificar"; nunca datos de ingeniería inventados.
- **1 Ejecutor a la vez** en esta fase (plan v3); máximo **3 sesiones de CATDIC-WEB trabajando a la vez** entre las fases A y B. Ejecutores `fresh`, Sonnet medio (Haiku bajo para lo mecánico).
- **Ramas (Director, 19/11, a pedido de Steven):** solo quedan `main`, `etapa5-plan`, `etapa5-fase-a` y `etapa5-fase-b`. Todo el trabajo de la Fase B va en `claude/etapa5-fase-b-0020e1`. Un Ejecutor trabaja **en el worktree del Líder, sobre esa misma rama, por turnos** (nunca a la vez que el Líder edita) y **no crea ramas nuevas**.
- Lo que necesite backend nuevo es la **Fase D** (D-a bandeja común, D-b indicadores tras D15, D-c trabajos independientes): se pide al Director, no se simula. En pantalla se rotula y queda «pendiente de verificar».
- Git: solo commits locales en `claude/etapa5-fase-b-0020e1`. Ningún push ni cambio en el checkout principal.
- Para ver el tablero: backend desde el worktree con una **copia** de la BD (`CATDIC_DB_PATH` en el scratch), puerto ≠ 8000. Nunca se commitean PDFs, capturas ni `*.db`.
- **Sin contacto con servicios externos sin el sí de Steven (Director, 19/11).** Incluye los comandos de `impeccable` que llaman a la red (`concept-seed`) y cualquier descarga. La única librería externa autorizada es Vue 3.5.13 (`FRONTEND/vendor/vue/`, SHA-256 en su README).
- Hecho de la fase: paridad completa con B0 en el navegador, sin peticiones a internet, `break-ui` sin roturas abiertas, suite del backend igual (943 pasan; 2 fallan por Dropbox).

## Tareas
| Tarea | Qué | Quién | Rama | Estado |
|---|---|---|---|---|
| B0 | Inventario funcional del tablero actual → `PLANES/etapa-5-inventario-ui.md` | Ejecutor Sonnet `b0-inventario` (archivado) | `claude/etapa5-b0-inventario-fb8728` (`effa03a`, traído aquí con cherry-pick) | **aceptada** |
| B1 (16/11) | Navegación + 3 maquetas en `FRONTEND/maquetas/{expediente,plano,obra}/` + `NOTAS-DESIGN.md` | Líder | esta rama | antecedente (sustituida por B1 v3) |
| B1 v3 | 3 estilos sobre la organización D6, 5 pantallas, en `FRONTEND/maquetas/v2/` + `NOTAS.md`; B0 §10 «Necesidades nuevas»; `PRODUCT.md` al día | Líder | esta rama | **auditada y aprobada (19/11)** |
| — | **Puerta de Steven:** elige estilo (vía Director) | Steven | — | **resuelta 19/11: «Plano sellado»** |
| B2 | Base: estructura de `FRONTEND/`, `vendor/` local, tokens del estilo B, armazón con navegación D6, cliente API, `/clasico/` (encargo `PLANES/etapa-5-reportes/B2-brief.md`) | Ejecutor Sonnet (subagente, en este worktree) + revisión del Líder | esta rama (`d254519`…`485b3ea`, Líder `a7a1f3f`, `078d4f3`, prueba de backend) | **aprobada por el Director (19/11)** |
| B3a | Inicio y Mis obras, con Nueva obra (encargo `PLANES/etapa-5-reportes/B3a-brief.md`) | Ejecutor Sonnet (subagente, en este worktree) + revisión del Líder | esta rama (`ddca35f`, `30bea9a`, `6f6d73a`, `69ed72f`, Líder: corrección móvil) | **aprobada (Director, 22/11; Steven: «Sí, sigue así»)** |
| B3d | **(2.º; encargo `PLANES/etapa-5-reportes/B3d-brief.md`; informe `B3d.md`)** Visitas y trabajos: **Procesar cola** con el seguimiento del trabajo (polling cada 2 s), **Sincronizar desde Dropbox** con su resultado (Z8), cola de visitas de todas las obras (Z15) y de cada obra, subir visita / conectar Dropbox (M3), avance del procesador (cubre T10b) | Ejecutor Sonnet (subagente, en este worktree) + revisión del Líder | esta rama (`30a1ef0`, `534e9a8`, `f7115a3`, `d134d01`, `e3c64c4`, `452a33b`, `28f44b7`; Líder `65f0916`) | **aprobada (Director, 22/11; Steven: «Sí, sigue así»)** |
| B3g | **(3.º; Director a pedido de Steven, 22/11; encargo `PLANES/etapa-5-reportes/B3g-brief.md`)** Informes dentro de la obra: lista de informes generados con «Abrir PDF», «Hacer informe» (elegir visita, procesar y avance en vivo de B3d) y «Crear informe» lleva a elegir obra. **Excepción de backend:** `BACKEND/informes_obra.py`, `GET /api/proyectos/{id}/informes`, `GET /api/informes/archivo` (solo rutas registradas en `pdf_generado`) y `tests/test_informes_obra.py` | Ejecutor Sonnet (subagente, en este worktree) + revisión del Líder | esta rama (`a87738d`, `5d03273`, `30ad788`, `051b816`; informe `B3g.md`) | **aprobada (Director, 22/11; evaluación en `etapa-5-evaluacion.md`); falta que Steven la vea** |
| B3e | **(4.º; encargo `PLANES/etapa-5-reportes/B3e-brief.md`)** **Mesa de Dudas** completa (M1: por visita y por obra, responder, conflictos) y Bandeja de trabajo con lo que hay hoy (la ruta común es Fase D-a). Construye el **visor de revisión compartido** (Ubicación · Detalle · Abrir plano, ver abajo). **Excepción de backend:** `GET /api/dudas/{id}/refs` | Ejecutor Sonnet (subagente, en este worktree) + revisión del Líder | esta rama (`e7436b6`, `233b64a`, `6d749b4`, `233372c`, `31c36ec`, `76eb9e8`; corrección de la auditoría `f67b3ff`; informe `B3e.md`) | **APROBADA** (reauditoría del Director, 23/11, sobre `b0ba715`; bloqueo previo corregido en `f67b3ff`); falta que Steven la vea |
| B3g-2 | **(5.º; Director a pedido de Steven, 22/11: «Sí, lo necesito»; encargo `PLANES/etapa-5-reportes/B3g2-brief.md`)** Regenerar el informe de una visita «Procesada»: solo STP-MIVED, como versión nueva (`v2`, `v3`…), sin P3, sin tocar los FI ni el estado de la visita; «Regenerar informe» con confirmación en «Hacer informe». **Excepción de backend:** `BACKEND/regenerar_visita.py`, `POST /api/visitas/{id}/regenerar` y `tests/test_regenerar_visita.py`; `procesador_cola.py` sin tocar | Ejecutor Sonnet (subagente, en este worktree) + revisión del Líder | esta rama (`5b135d0`, `39f1346`, `bc1f6da`, `d82824c`; informe `B3g2.md`) | **APROBADA** (auditoría del Director, 23/11, sobre `b0ba715`); falta que Steven la vea |
| B3b | **(6.º)** Obra: Resumen, Avance, Cierre, Planos y ficha (cambiar plano con el formulario de B3a, datos de la obra M5), visor y recuadros (M4) | Ejecutor Sonnet (subagente, en este worktree) + revisión del Líder | esta rama (`eeebe2b`, `5f6a46a`, `c3def42`, `4568959`; encargo `B3b-brief.md`, informe `B3b.md`) | **APROBADA** (auditoría del Director, 23/11, sobre `905ec52`); falta que Steven la vea |
| B3c | **(7.º)** Revisión de planos: confirmar datos del plano (M6) | Ejecutor Sonnet (subagente, en este worktree) + revisión del Líder | esta rama (`9dd4aee`, `71d4bd1`; corrección del Líder `ede37af`; encargo `B3c-brief.md`, informe `B3c.md`) | **hecha y revisada por el Líder, esperando auditoría** |
| B3f | **(8.º)** Órdenes de trabajo (kanban Z16) | Ejecutor | — | pendiente |
| B3h | **(SIN AUTORIZACIÓN: Steven, 20/11, «Conserva el tablero clásico»)** Retiro del clásico: checklist de paridad de B0 §9 completa en el tablero nuevo; se borran `FRONTEND/clasico/` y `test_clasico_entrega_el_tablero_anterior` (esta prueba es de `BACKEND/`: pide excepción al Director) | Líder + Ejecutor | — | pendiente |
| B4 | Movimiento y pulido (`animate`, `choreograph`, `emil-design-eng`), `prefers-reduced-motion` | Ejecutor + Líder | — | pendiente |
| B5 | `break-ui`, teclado, contraste, 1280/1920, paridad con B0, cierre | Líder + Ejecutor | — | pendiente |

Las pestañas **Avance** y **Cierre** de la obra entran en **B3b** con Resumen (Director, 19/11). Sus indicadores muestran «pendiente de verificar» hasta D15, sin números inventados.

**Visor de revisión (Steven, 22/11):** «CUANDO EL PROGRAMA ME PIDA QUE ESTA EN REVISION, QUIERO QUE LA PANTALLA DE REVISION ME UBIQUE EL ELEMENTO Y ME DE EL DETALLE DEL ELEMENTO O TAMBIEN OTRA OPCION APARTE DE ESOS ES ABRIR EL PLANO». Referencia: PlanRadar, con la lista a un lado y el plano al otro.
- Un solo componente, construido en **B3e** y reutilizado en B3c y B3b.
- Muestra junto a cada pregunta:
  - **Ubicación** (M3, `visor/vista-previa` con `localizacion`);
  - **Detalle** (M4, `detalle`);
  - **Abrir plano**: la hoja completa con zoom, centrada en el recuadro.
- **Si falta el recuadro:**
  - sin recuadro confirmado se muestra la propuesta, rotulada «propuesta, pendiente de verificar», con su fuente;
  - sin propuesta ni hoja, «pendiente de verificar»;
  - si la duda no se puede atar a un elemento, solo «Abrir plano».
- **Prohibido** atar una duda por `id_elemento`.
- Las dudas de visita se atan con `GET /api/dudas/{id}/refs`, excepción de backend de B3e aprobada por el Director el 22/11:
  - devuelve el evento `duda` más reciente;
  - si la duda no existe, 404; si no tiene evento, `refs: null`;
  - no cambia `/api/dudas`.
- Está detallado en el encargo de B3e.

Hueco reservado en la navegación: "Lectura asistida" (Fase C, no es de esta fase).

## B1 v3 (plan aprobado el 19/11) — hecha, esperando auditoría y puerta
- Organización fija (D6): Inicio · Mis obras · Bandeja de trabajo · Informes · Configuración + «Crear informe»; en la obra: Resumen · Visitas y trabajos · Planos y ficha · Avance · Informes · Cierre.
- Entregable: 2–3 estilos visuales sobre esa misma organización, 5 pantallas (Inicio, Resumen de obra, Bandeja, Revisión de planos, Crear informe independiente), datos sintéticos rotulados, estados vacío/cargando/error/pendiente, escritorio y móvil. Indicadores siempre «pendiente de verificar» (D15), nunca 0 %. Cada estilo dice qué skill aportó qué decisión y qué patrón toma de Procore/Autodesk/PlanRadar/Fieldwire.
- Lugar: `FRONTEND/maquetas/v2/` (un HTML por estilo + `datos.js`, `app.js`, `base.css`, `estilo-*.css`). Las maquetas del 16/11 quedan como antecedente.
- B0 se amplía con la sección 10 «Necesidades nuevas» (criterios propios; lo que pide backend va a la Fase D, no se simula).
- Reglas nuevas: 1 ejecutor a la vez; máx. 3 sesiones de CATDIC-WEB a la vez entre fases A y B.
- Resultado: A **Hormigón** (asignado por el sorteo de `impeccable`, `seed:b9414461f55ae1b3`), B **Plano sellado** (elección del skill), C **Tablero de obra** (retador competitivo). Detalle en `FRONTEND/maquetas/v2/NOTAS.md`.
- Pendiente al elegir: telemetría del sorteo (`--from b429ec8dc7555d53ac6ca00d75b3dc17 --scope direction --mode operate --kind <assigned|pick|challenger>`), contrato de dirección y `DESIGN.md` (se escribe en B2).
- Necesidades de Fase D que salen de B1 (B0 §10): D-a ruta común de la Bandeja, vencimientos y actividad reciente; D-b indicadores (tras D15); D-c guardar trabajos independientes.

## Decisiones de Steven
- **19/11/2026 · Tablero clásico:** «EL TABLERO CLASICO NO LO QUIERO VOLVER A VER» (cita relayada por el Director). Consecuencias:
  - Desde B3a, ningún enlace ni mención al clásico en el tablero nuevo.
  - `FRONTEND/clasico/` sigue en el repo sin enlazar hasta B3h, donde se borra con su prueba.
  - B3 se reordena para que lleguen primero las funciones que hoy solo tiene el clásico: Procesar cola, Sincronizar, la cola de visitas y la Mesa de Dudas.
- **19/11/2026 · Estilo visual:** «Plano sellado» (respuesta textual de Steven, relayada por el Director). Se construye con el estilo B de `FRONTEND/maquetas/v2/` (`plano.html`, `estilo-plano.css`). Hormigón y Tablero quedan como antecedente, sin borrarlos. Telemetría del sorteo de `impeccable` enviada (`--kind pick`: «choice recorded»).

## Bitácora (lo más nuevo arriba)
- 23/11/2026 · Líder: **B3c hecha y revisada** (informe `PLANES/etapa-5-reportes/B3c.md`).
  - Revisión: solo `FRONTEND/` y el informe, sin `BACKEND/`. «Confirmar tabla completa» y «Certificar…» quedan deshabilitados sin su casilla y envían `extraido_en`. `id_elemento` solo se muestra y va en `data-campo` por paridad con B0; la clave de la fila es el `uid`. La URL del recorte se revoca. El único borde lateral nuevo es el divisor entre la lista y el detalle.
  - Datos: la obra de B3e da 0 tablas. Sobre una obra sintética nueva (`obra-sintetica-b3c`, vectorial de 5 páginas), la extracción real dio 6 tablas, 9 elementos, 128 campos y 8 dudas. Se añadieron por SQL, solo en la copia, una tabla no vigente, una sin recorte y un valor distinto.
  - Playwright del Líder (375 y 1280, claro y oscuro: entrada desde «Planos y ficha», lista, detalle, casilla que habilita el botón, `&tabla=` tras recargar y Atrás): 56 comprobaciones, 0 fallas.
  - Corregido por el Líder: a 375 px, la tabla de valores pedía desplazamiento lateral y escondía «tabla: …» y el Estado (ahora cabe); el aviso de valores dudosos partía su enlace en una columna estrecha y no concordaba en singular.
  - Ejecutor: suite 975/7/0 en el scratch y 977 pasan / 2 fallan (Dropbox) sin `CATDIC_DROPBOX_RAIZ`. Playwright a 5 anchos × 2 temas, confirmar y certificar de verdad en la copia, peor caso (60 tablas, 400 filas).
  - **Para B4:** a 375 px la barra superior (Extraer, Mesa y Cerrar, uno por línea) queda fija y ocupa unos 210 px; conviene compactarla. «Falla:» muestra las claves tal cual (`sin_notas_de_modificacion`), igual que el clásico.
  - Abierto: nada probado con un plano real; una `&tabla=` desconocida vuelve a la lista sin aviso.
- 23/11/2026 · Director: **B3b APROBADA** sobre `905ec52` (Evaluación 5 copiada en `etapa-5-evaluacion.md`). Suite: 977 pasan, 3 se omiten y solo fallan las 2 de Dropbox. «Adelante con B3c», sin push. Líder: encargo `PLANES/etapa-5-reportes/B3c-brief.md` y Ejecutor lanzado.
  - **Para B4 (no bloquean):** (1) al aparecer «Ir al recuadro», la barra del visor pasa a dos líneas y el panel baja unos 38 px: reservar su sitio; (2) la tarjeta del plano dice «huellas sha256 de abajo», pero están arriba.
- 23/11/2026 · Líder: **B3b hecha y revisada** (informe `PLANES/etapa-5-reportes/B3b.md`).
  - Revisión: solo `FRONTEND/` y el informe, sin `BACKEND/`. Los elementos se atan por `uid` (`id_elemento` solo se muestra) y se llama a `C.visor.olvidar` al guardar un recuadro y al cambiar de plano. Las rutas usadas existen (`/api/dudas` con `sin_visita`, `elementos`, `propuesta`, `recuadro`, `vista-previa`, `datos-obra`, `planos`, `informes`). Ni `progress` ni `meter`, 0 menciones al clásico y 0 URL externas; el único borde lateral nuevo es el divisor de 1,5 px entre la hoja y el panel del editor, no una franja de estado.
  - Playwright del Líder (375 y 1280, claro y oscuro; Resumen, Planos y ficha, Avance, Cierre y editor; Atrás desde el editor): 136 comprobaciones, 0 fallas.
  - Corregido por el Líder: la nota de los indicadores decía literalmente «0 %» («No se muestran como 0 %…»); ahora dice «no se muestra ninguna cifra ni barra».
  - Ejecutor: suite 975/7/0 en el scratch y 977 pasan / 2 fallan (Dropbox) sin `CATDIC_DROPBOX_RAIZ`. Playwright a 5 anchos × 2 temas, dibujo con ratón y con toque, peor caso (300 elementos, 120 caracteres, 30 revisiones).
  - Abierto: el dibujo no tiene equivalente de teclado (lo cubren «Proponer» y «Usar propuesta»); con «Dibujar» activo hay que pasar a «Mover la hoja» para arrastrar; nada probado con un plano real.
- 23/11/2026 · Director: **B3e y B3g-2 APROBADAS** en la reauditoría sobre `b0ba715` (Evaluación 4 copiada en `etapa-5-evaluacion.md`). Suite: 977 pasan, 3 se omiten y solo fallan las 2 de Dropbox. La Mesa queda a la vista y con el foco al abrirla. El Director se las enseña a Steven.
- 23/11/2026 · Director: **lanza B3b**; audita B3e y B3g-2 sobre una copia de `b0ba715`. Decisiones de B3g-2: (1) el STP con dudas sale « - CON DUDAS» y la visita queda «Procesada»; (2) `salida_json` sin cambios; (3) `clase_proceso` es tarea posterior, después de fusionar el PR #35; (4) `REGENERAR_SIN_P3` se audita en cada intento. Líder: encargo `PLANES/etapa-5-reportes/B3b-brief.md` (solo frontend, sin excepción de backend) y Ejecutor lanzado.
- 23/11/2026 · Líder: **B3g-2 hecha y revisada** (informe `PLANES/etapa-5-reportes/B3g2.md`).
  - Revisión: el backend queda en la excepción (`regenerar_visita.py`, la ruta y su import en `main.py`, `tests/test_regenerar_visita.py`); `procesador_cola.py` y `database.py` sin cambios. `ProcesoRegeneracion` hereda de `ProcesoVisita` y sustituye `ejecutar`, `_procesar`, `_p3`, `_generar` (solo STP) y `_cerrar` (sin cambio de estado). `lanzar_trabajo`/`ejecutar_trabajo` se copiaron (~40 líneas) porque `ejecutar_trabajo` fija `ProcesoVisita`. 57 pruebas pasan (regenerar + procesar cola + informes).
  - Corregido por el Líder: en «Hacer informe», al regenerar, la fila de los FI decía «Se genera hoy»; ahora «No se tocan al regenerar». Los textos de formatos ya no se parten en columnas a 375 px.
  - Ejecutor: suite 975/7/0 en el scratch y 977 pasan / 2 fallan (Dropbox) sin `CATDIC_DROPBOX_RAIZ`; Playwright 130 comprobaciones sin fallas; v1 y v2 reales sobre obra sintética.
  - Decisiones abiertas para el Director: (1) si el STP se genera pero deja dudas, sale « - CON DUDAS» como en el procesador; (2) `salida_json` no apunta a la versión nueva; (3) un parámetro `clase_proceso` en `ejecutar_trabajo` evitaría la copia cuando se fusione el PR #35; (4) `REGENERAR_SIN_P3` se audita en cada intento.
- 23/11/2026 · Director: **B3e BLOQUEADA** (evaluación en `etapa-5-evaluacion.md`): desde la cola desplazada, «Abrir la Mesa de Dudas» dejaba la Mesa fuera de la vista y el foco en `BODY`. Líder: corregido en `f67b3ff` (scrollIntoView y foco al encabezado con `?visita=`, `?dudas=obra` y `&duda=`, también al recargar). Playwright a 375 y 1280, claro y oscuro, desde la cola desplazada: 48 comprobaciones, 0 fallas.
- 23/11/2026 · Líder: **B3e hecha y revisada** (informe `PLANES/etapa-5-reportes/B3e.md`). El límite de 5 horas cortó al Ejecutor a mitad; se reanudó el mismo, sin descartar nada.
  - Revisión del Líder: el backend queda dentro de la excepción (`mesa_dudas.py` + `tests/test_dudas_refs.py`, 9 pasan); `/api/dudas` no cambia; ninguna duda se ata por `id_elemento` (solo se muestra); 0 menciones al clásico, 0 URL externas y sin bordes laterales. Corregido el espacio entre el título de la visita y su estado en la cabecera de la Mesa.
  - Ejecutor: suite 962/7/0 con todo en el scratch y 964 pasan / 2 fallan (las de Dropbox) sin `CATDIC_DROPBOX_RAIZ`. Playwright: 128 + 25 + 24 comprobaciones sin fallas, peor caso con 376 dudas abiertas.
  - Abierto: «Fotos p. N» si `paginas` es un número; `refs.plano.recuadro` no se dibuja (sistema de coordenadas sin confirmar); pellizco en pantalla táctil sin probar.
- 22/11/2026 · Director: **B3g aprobada** (evaluación copiada en `etapa-5-evaluacion.md`). Nueva tarea **B3g-2, regenerar el informe de una visita ya procesada**, justo después de B3e (Steven: «Sí, lo necesito»). Líder: encargo `B3g2-brief.md`.
- 22/11/2026 · Director: **arranca B3e** mientras audita B3g sobre una copia de `e5a1c62`.
  - Líder: encargo `B3e-brief.md`. La Mesa es una vista con dirección propia (modo visita en `#/obra/<id>/visitas?visita=`, modo obra en `#/obra/<id>/resumen?dudas=obra`), sin panel superpuesto ni apertura automática: es la variante D6 de M1.
  - El visor de revisión se construye como componente compartido.
- 22/11/2026 · Líder: **B3g hecha, esperando auditoría y que Steven la vea** (informe `PLANES/etapa-5-reportes/B3g.md`).
  - **Revisión:**
    - el backend se queda dentro de la excepción: `informes_obra.py` y `test_informes_obra.py`, nuevos, y en `main.py` solo las 2 rutas y sus imports;
    - `/api/informes/archivo` solo sirve rutas idénticas a las de un `pdf_generado`;
    - no se tocaron `procesador_cola.py`, `database.py`, `clasico/` ni su prueba;
    - 0 menciones al clásico, 0 URL externas y sin franjas laterales.
  - **Avance en vivo:** se extrajo a `js/avance-trabajo.js` (`AvanceTrabajo`), que ahora usan `#/trabajo/<id>` y la pestaña Informes.
  - **Pruebas:**
    - las de `test_informes_obra.py` y `test_frontend_servido.py` pasan (13);
    - suite del Ejecutor: 953 pasan con todo en el scratch, y 955 pasan con 2 fallas, las de Dropbox, sin `CATDIC_DROPBOX_RAIZ`.
  - **Límite:** no se generó un PDF real de punta a punta, porque la copia de la BD no tiene datos de diseño que den PDF. La lista se probó con eventos y PDF sintéticos.
- 22/11/2026 · Director: **B3a y B3d APROBADAS** sobre `4422678`, sin bloqueantes. La evaluación está en `PLANES/etapa-5-evaluacion.md`.
  - Steven las vio en una copia de la rama (puerto 8767) y respondió: «Sí, sigue así».
  - «Sincronizar desde Dropbox» se queda solo en Inicio; en la obra basta con «Conectar con Dropbox».
- 22/11/2026 · Líder: **B3d hecha, esperando auditoría y que Steven la vea** (informe `PLANES/etapa-5-reportes/B3d.md`).
  - **Revisión:**
    - toda la entrega está en `FRONTEND/**` y el informe, sin tocar `clasico/`, `maquetas/`, `vendor/` ni `BACKEND/`;
    - 0 menciones al clásico y 0 URL externas.
  - **Corrección del Líder (`65f0916`):** franjas laterales gruesas cambiadas por bordes completos (aviso del detector de diseño). Matriz y peor caso repetidos sin fallas.
  - **Suite** (con las rutas al scratch): 942 pasan, 7 se omiten y 0 fallan. Las 2 de Dropbox se omiten en vez de fallar porque la raíz apunta al scratch.
  - **Paquete de Campo:** el informe anota dónde iría el aviso y qué dato haría falta (`paquete_campo` por visita en `/api/dashboard`, `origen` en `visita_inicio`).
  - **Pregunta abierta para el Director:** ¿«Sincronizar desde Dropbox» también en la pestaña de cada obra? Por ahora solo está en Inicio; «Conectar con Dropbox» ya sincroniza la obra.
- 22/11/2026 · Director, a pedido de Steven: **nuevo orden de B3: B3a → B3d → B3g → B3e → B3b → B3c → B3f.**
  - Steven: «PREPARA CATDIC INFORMES PARA QUE YO PUEDA HACER LOS INFORMES DENTRO DEL PROYECTO».
  - B3g lleva una excepción de backend concedida por el Director (ver la tabla).
  - Visor de revisión pedido por Steven: entra en B3e (ver arriba).
- 22/11/2026 · Director: **se reanuda la Fase B.** Steven, textual: «Sí, reanúdala».
  - B3d arranca con su encargo, 1 Ejecutor a la vez, en este worktree y esta rama (ya contiene `main`).
  - El clásico sigue como lo dejó Steven el 20/11: no se borra `FRONTEND/clasico/` ni su prueba; `ddca35f` no se revierte ni se amplía. B3h sigue sin autorización.
  - PR #35 (`claude/paquete-visita-campo`, sin fusionar) añade el paquete de CATDIC Campo `*.catdic-visita.json`. En B3d no se construye nada para él; el informe anota dónde iría el aviso «esta visita trae paquete de Campo» en la cola.
  - B3a sigue esperando que Steven la vea y la auditoría: el Director enseñará B3a y B3d juntas.
  - Líder: el puerto 8765 está ocupado por otro proceso (PID 42292, sin identificar; no se cierra). El Ejecutor de B3d usa el **8766**. Novedades añadidas al encargo.
- 20/11/2026 · Director: **Fase B en pausa.** Steven aprobó empezar F0 del plan «Fundación inicial» (`PLANES/fundacion-inicial.md`, PR 33). Su punto 2: «Pausa la ejecución de A y B mientras haces esa reconciliación».
  - No se arranca B3d ni ningún Ejecutor nuevo.
  - B3a se conserva; F1 evaluará qué sirve.
  - Punto 4 de Steven: «Conserva el tablero clásico. Su eliminación no queda autorizada». **B3h queda sin autorización.** Los enlaces que quitó `ddca35f` se quedan en la rama hasta que se decida en F0/F1.

  Estado al pausar:
  - El Ejecutor de B3d se cortó por el límite de uso antes de escribir nada: no hay trabajo a medias ni WIP.
  - Árbol limpio, sin servidores de prueba encendidos.
  - Última suite (19/11): 944 pasan, 2 fallan (Dropbox), 3 se omiten.
- 19/11/2026 · Director: B3a delante de Steven; la auditoría formal va después de que la vea. Aprobado:
  1. **Fase D-a suma un campo o conteo de tablas confirmadas** en `/tablas-extraidas`. Mientras tanto, «pendiente de verificar».
  2. Órdenes sin enlace hasta B3f.
  3. El aviso de obra creada remite a «Planos y ficha».

  B3d sigue en curso.
- 19/11/2026 · Líder: **B3a hecha, esperando auditoría.** El Ejecutor Sonnet entregó `ddca35f` (fuera los enlaces al clásico), `30bea9a` (Inicio y `js/datos.js`), `6f6d73a` (Mis obras y `FormularioPlanos`) y `69ed72f` (informe `PLANES/etapa-5-reportes/B3a.md`).

  Pruebas del Ejecutor:
  - Suite: 944 pasan y 2 fallan (Dropbox).
  - Playwright a 5 anchos y 2 temas: 0 peticiones externas, 0 errores y sin desbordes.
  - Diálogo «Nueva obra»: foco atrapado y reintento de solo la subida.
  - Estados y peor caso probados.

  Revisión del Líder:
  - Sin cambios en `BACKEND/`, `clasico/`, `vendor/` ni `maquetas/`. 0 menciones al clásico y 0 URLs externas.
  - Corregido que el tipo de fila se partía a 375 px.

  Abierto:
  1. «Tablas por confirmar» queda «pendiente de verificar · Fase D-a», porque `/tablas-extraidas` no dice cuáles están confirmadas. Hace falta un campo o un conteo en backend.
  2. «Órdenes abiertas» muestra el número real sin enlace hasta B3f.
  3. «Visitas en cola» enlaza a la Bandeja, que llena B3d.
- 19/11/2026 · Director: aprobado el orden B3a → B3d → B3e → B3b → B3c → B3f → B3g → B3h. Es decisión del Director: Steven todavía no la confirmó, y si la cambia se avisa. Lugar de la cola:
  - Inicio: bloque «Cola de visitas» con Procesar cola y Sincronizar desde Dropbox. **Condición:** enlaza a la vista completa de la Bandeja, para no tener dos listas que se desincronicen.
  - Bandeja de trabajo: la cola de todas las obras.
  - Cada obra: su cola, en «Visitas y trabajos».

  Los botones y el enlace los añade B3d en Inicio. El logo y el título «Control Taller» de B0 §9 se marcan «sustituido por D6». Steven quiere ver cada pantalla en cuanto esté: se avisa al Director al cerrar cada tarea de B3.
- 19/11/2026 · Director: Steven no quiere volver a ver el tablero clásico. Hecho:
  - Pedido al Ejecutor de B3a, que trabaja en `FRONTEND/`, un commit aparte que quita las 3 menciones: `componentes.js`, `obra.js` y el `noscript` de `index.html`.
  - B3 reordenado: B3a → B3d → B3e → B3b → B3c → B3f → B3g.
  - Añadida B3h, retiro del clásico. Ver «Decisiones de Steven».
- 19/11/2026 · Director: **B2 aprobada.** Respuestas:
  1. Excepción coordinada: el Líder puede tocar solo `BACKEND/tests/test_frontend_servido.py`. La prueba vieja pasa a `/clasico/` y una nueva comprueba que `/` entrega el tablero nuevo con `vendor/vue/`. Hecho; la suite queda en 944 pasan, 2 fallan (Dropbox) y 3 se omiten.
  2. Avance y Cierre entran en B3b; las pestañas ya lo dicen.
  3. Las CDN de `/clasico/` se retiran en B5.

  El SHA-256 de Vue ya estaba completo en su README. Se abre B3a con su encargo.
- 19/11/2026 · Líder: **B2 hecha, esperando auditoría.** El Ejecutor Sonnet entregó 5 commits (`d254519`…`485b3ea`, informe en `PLANES/etapa-5-reportes/B2.md`). Contenido:
  - `/clasico/` idéntico byte a byte al `index.html` anterior.
  - Armazón nuevo con Vue local, scripts clásicos, tokens de Plano sellado en claro, oscuro y del sistema, cliente API y enrutador por hash.
  - Las 7 pantallas con su estado vacío honesto, más 2 lecturas reales: Configuración y la cabecera de obra.
  - Playwright a 375–1920 px en claro y oscuro: 0 peticiones externas del tablero nuevo, sin desbordes, Tab y Atrás correctos.

  Revisión del Líder:
  - Sin cambios en `BACKEND/`. No hay URLs `http` en los archivos nuevos.
  - Corregido «Ajustes» → «Configuración» en la barra móvil, que cabe a 320 px, y el marco de foco del `<h1>` (`a7a1f3f`).
  - Escrito `FRONTEND/DESIGN.md` (`078d4f3`).

  Abierto:
  1. Suite 942/3/3: falla además `test_frontend_servido.py::test_raiz_entrega_el_tablero_local`, que espera el tablero viejo en `/`. Es backend y se pide al Director.
  2. Avance y Cierre sin tarea B3.
  3. Contraste sin medir con herramienta (va a B5).
  4. Al probar `/clasico/`, el navegador pidió una vez sus 3 CDN (Tailwind, Vue en unpkg, Font Awesome). Lo pide esa página por sí sola; no se descargó nada y el tablero nuevo no hace peticiones externas.
- 19/11/2026 · Líder: Steven autorizó, vía Director, la descarga de Vue: «Sí, descarga Vue». Bajado `vue.global.prod.min.js` 3.5.13 de cdnjs a `FRONTEND/vendor/vue/` (154 807 bytes, SHA-256 `220ffd8a…92fe`, con README). También aprobado: solo Vue, sin Tailwind, y `/clasico/` con el `index.html` actual tal cual. Respondido al Director qué envía la telemetría de `impeccable`: una consulta GET a impeccable.style/api/roll con alcance, modo, clave aleatoria y contador, sin archivos del proyecto, según declara el programa.
- 19/11/2026 · Director: Steven eligió «Plano sellado». Se abre la puerta de B2.
- 19/11/2026 · Director: `e07e54a` verificado a 1024 y 800 px; corrección aprobada. B1 v3 auditada. La fase queda parada en la puerta hasta que Steven elija estilo.
- 19/11/2026 · Líder: corregido el defecto de la auditoría de B1 v3. A 768–1279 px, «Prioridades» se aplastaba a una palabra por línea. Ahora las filas se acomodan al ancho de su caja con container queries: apiladas por debajo de 640 px, 4 columnas desde ahí y tabla de 6 en la Bandeja desde 880 px. La obra se ve también en Inicio y el cajetín de A y C tiene celdas más anchas. Validado de 375 a 1920 px, con 1024 y 768, en las 5 pantallas de los 3 estilos: sin texto aplastado, sin desbordes, 0 peticiones externas y 0 errores.
- 19/11/2026 · Director: ramas reducidas a 3 además de `main` (las demás borradas, con respaldo; la de B0 ya estaba copiada aquí). La Fase B trabaja solo en `claude/etapa5-fase-b-0020e1`; los Ejecutores trabajan en este worktree, por turnos, sin ramas nuevas.
- 19/11/2026 · Líder: **B1 v3 hecha.** 3 estilos en `FRONTEND/maquetas/v2/` (un HTML por estilo + `datos.js`, `app.js`, `base.css`, `estilo-*.css`, `index.html` para elegir, `NOTAS.md`). Verificación con Playwright a 1280, 1920 y 375, en claro y oscuro: sin desbordes, 0 peticiones fuera de `file:` y 0 errores de consola. El orden de Tab es correcto. Los estados vacío, cargando y error se probaron, igual que C4 en conflicto y los pasos de Crear informe. `impeccable detect`: quedan 2 avisos *advisory* justificados, la retícula de B y el rayado de A. B0 ampliado con la §10 (N1–N27, columna de backend). `FRONTEND/PRODUCT.md` actualizado con D6. Avisado el Director para la auditoría.
- 19/11/2026 · Líder: plan v3 traído con merge de `origin/claude/etapa5-plan` (`e853215`). Leído el comentario de Steven en el PR 31 (por la API REST: `gh pr view` falla por permisos del token). B1 se rehace.
- 16/11/2026 · Líder: **B1 hecha, parada en la puerta de Steven.** 3 maquetas: A Expediente (sorteo de `impeccable`), B Plano (la que el skill elige), C Obra (continuidad oscuro + amarillo). Revisadas con Playwright a 1280 y 1920: sin desbordes, 0 peticiones externas. Sustituciones declaradas: `FRONTEND/PRODUCT.md` inferido sin entrevista (la fase no permite hablar con Steven) y la página de decisión de `impeccable` sustituida por el reporte al Director. Pendiente al elegir: aviso de telemetría del sorteo (`--from 373b84e9ba2a0560b6dd64bec7b5e4cd`), contrato de dirección y `DESIGN.md`.
- 16/11/2026 · Líder: B0 revisado contra `FRONTEND/index.html`: 93 apariciones / 86 nombres `data-*` (los 86 en la sección 6), 23 `fetch(`, 46 botones, 6 modales; líneas de muestra correctas. Aceptado y Ejecutor archivado. Para B2: el tablero usa `API = 'http://localhost:8000'` fijo; el nuevo debe usar rutas relativas.
- 16/11/2026 · Líder: fase arrancada. Leídos `etapa-5.md`, `CLAUDE.md`, `COLABORACION.md`. B0 lanzado; B1 en curso.
