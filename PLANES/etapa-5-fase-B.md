# Etapa 5 · Fase B — Rediseño del tablero (estado de la fase)

Líder: sesión Opus (Líder de la Fase B) · rama `claude/etapa5-fase-b-0020e1` (sale de `claude/etapa5-plan`, `dab9cf0`).
Plan madre: `PLANES/etapa-5.md` (decisiones D5–D8, tareas B0–B5). Este archivo es lo que sobrevive a la compactación: se actualiza en cada paso.

## Reglas que mandan en esta fase
- Zona: `FRONTEND/**`, `DESIGN.md`, `PLANES/etapa-5-fase-B.md`, `PLANES/etapa-5-inventario-ui.md`, `PLANES/etapa-5-reportes/B*.md`. **No tocar `BACKEND/**`** (ni rutas, ni respuestas, ni `main.py`): lo que haga falta se pide al Director.
- Sin compilación (D5): varios archivos, Vue y Tailwind locales en `FRONTEND/vendor/`, funciona **sin internet**. El tablero viejo queda en `FRONTEND/clasico/index.html` (abre en `/clasico/`) hasta el cierre.
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
| B1 v3 | 3 estilos sobre la organización D6, 5 pantallas, en `FRONTEND/maquetas/v2/` + `NOTAS.md`; B0 §10 «Necesidades nuevas»; `PRODUCT.md` al día | Líder | esta rama | **hecha, esperando auditoría del Director** |
| — | **Puerta de Steven:** elige estilo (vía Director) | Steven | — | **resuelta 19/11: «Plano sellado»** |
| B2 | Base: estructura de `FRONTEND/`, `vendor/` local, tokens del estilo B, armazón con navegación D6, cliente API, `/clasico/` (encargo `PLANES/etapa-5-reportes/B2-brief.md`) | Ejecutor Sonnet (subagente, en este worktree) + revisión del Líder | esta rama (`d254519`…`485b3ea`, Líder `a7a1f3f`, `078d4f3`, prueba de backend) | **aprobada por el Director (19/11)** |
| B3a | Inicio y Mis obras, con Nueva obra (encargo `PLANES/etapa-5-reportes/B3a-brief.md`) | Ejecutor Sonnet (subagente, en este worktree) | esta rama | **en curso** |
| B3b | Obra: Resumen, Avance, Cierre, Planos y ficha, visor y recuadros | Ejecutor | — | pendiente |
| B3c | Revisión de planos (confirmar datos del plano) | Ejecutor | — | pendiente |
| B3d | Visitas y trabajos: cola, subir visita/Dropbox, avance del procesador (cubre T10b) | Ejecutor | — | pendiente |
| B3e | Bandeja de trabajo y Mesa de Dudas (la ruta común es Fase D-a) | Ejecutor | — | pendiente |
| B3f | Órdenes de trabajo | Ejecutor | — | pendiente |
| B3g | Informes y Crear informe (solo lo que ya genera el sistema; lo demás «disponible más adelante»; guardar trabajos es Fase D-c) | Ejecutor | — | pendiente |
| B4 | Movimiento y pulido (`animate`, `choreograph`, `emil-design-eng`), `prefers-reduced-motion` | Ejecutor + Líder | — | pendiente |
| B5 | `break-ui`, teclado, contraste, 1280/1920, paridad con B0, cierre | Líder + Ejecutor | — | pendiente |

Las pestañas **Avance** y **Cierre** de la obra entran en **B3b** con Resumen (Director, 19/11). Sus indicadores muestran «pendiente de verificar» hasta D15, sin números inventados.

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
- **19/11/2026 · Estilo visual:** «Plano sellado» (respuesta textual de Steven, relayada por el Director). Se construye con el estilo B de `FRONTEND/maquetas/v2/` (`plano.html`, `estilo-plano.css`). Hormigón y Tablero quedan como antecedente, sin borrarlos. Telemetría del sorteo de `impeccable` enviada (`--kind pick`: «choice recorded»).

## Bitácora (lo más nuevo arriba)
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
