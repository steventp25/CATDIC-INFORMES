# Etapa 5 — Claude razona los planos (sin llave) + rediseño total del tablero
Estado: **APROBADO** (Steven, 16/11/2026: "Apruebo con propuestas"). Sin llave de API, con su suscripción de Claude y sin ningún pago adicional. Fase 0 en curso.

Base del plan: `origin/main` en `b5f7d26` (no el checkout local, que está atrasado; ver "Puesta al día de git").
Método: skill `gestion-proyectos` (Director → Líderes de fase → Ejecutores), integrada con este sistema de `PLANES/` y con `COLABORACION.md`. No se crea `.proyecto/`: el estado vive aquí.

| Qué | Dónde |
|---|---|
| Plan y decisiones (lo que la skill llama `PLAN.md`) | este archivo |
| Estado de cada fase (lo escribe su Líder) | `PLANES/etapa-5-fase-A.md`, `PLANES/etapa-5-fase-B.md` |
| Reporte de cada tarea (máx. 15 líneas) | `PLANES/etapa-5-reportes/<tarea>.md` |
| Auditorías | `PLANES/etapa-5-evaluacion.md` (skill `auditar-catdic`) |

### Respuestas de Steven
- 16/11/2026, sobre el gasto (D3): "CLAUDE COBRA POR CLAVE API. SI ES ASI USAMOS UNA CLAVE DE GEMINI QUE VEO QUE NO ME COBRA" → se le explicó que la llave gratuita de Gemini permite a Google usar las hojas para mejorar sus productos y que su suscripción Gemini Pro no incluye la API.
- 16/11/2026: "SIN LLAVE, USA MI SUSCRIPCION DE CLAUDE. […] NO QUIERO PAGAR ADICIONAL. YA PAGO CLAUDE Y GEMINI."
  - **D3 resuelta:** no hay llave de API (ni de Claude ni de Gemini), no hay `.env`, no se agrega el SDK `anthropic`. La lectura de planos la hace una sesión de Claude Code con la suscripción.
  - **D2 resuelta:** los planos los lee Claude Code igual que hoy; no salen a ningún servicio nuevo.
  - Regla nueva de la etapa: **ninguna tarea puede introducir un servicio de pago**. El único consumo es el cupo de uso de la suscripción.
- 16/11/2026: "Apruebo con propuestas" → plan APROBADO con las propuestas del Director:
  - **D1:** puesta al día de git (respaldo → comparar → `main` al día). Hecha el 16/11; ver Bitácora.
  - **D4:** los planos escaneados quedan fuera de esta etapa.
  - **D5:** frontend sin compilación, con Vue y Tailwind copiados localmente.
  - **D6:** sin referencia dada; B1 trae 2–3 maquetas.
  - **D7:** nadie más toca `FRONTEND/` durante la Fase B; T10b pasa a ser B3d. Falta que Steven diga si Codex sigue revisando los PR.
  - **D8:** ejecutores "fresh" en esta etapa.
  - **D9:** orden columnas → muros y zapatas → pórticos → losas.

## Objetivo (palabras de Steven)
1. Que **Claude razone los planos y extraiga toda la información** — ahora sin llave: con su suscripción.
2. **Cambiar totalmente cómo se presenta la página**, aplicando las skills de diseño instaladas (`impeccable`, `ui-ux-pro-max`, `emil-design-eng`, `apple-design`, `animate`, `break-ui`, etc.).

**Criterio de terminado:**
- Para una obra con plano vigente, Steven pide la lectura (desde el tablero se preparan las hojas; una sesión de Claude Code las lee) y al importar aparecen propuestas para columnas, muros, zapatas, pórticos por tramo y losas, cada valor con su hoja y recuadro de origen y **todas en `pendiente_de_verificar`**; lo que Claude no pudo anclar o dudó llega a la Mesa de Dudas. La app sigue funcionando sin internet y sin Claude igual que hoy.
- El tablero nuevo cubre el 100 % del inventario funcional del actual (B0), funciona sin internet, pasa `break-ui` y la suite `py -3.14 -m pytest -q` sigue en verde.

## Estado de partida (verificado el 16/11/2026 en `origin/main`)
- **Extracción actual, sin IA:** `BACKEND/plano/lector_plano.py` (módulo puro: texto visible del vectorial + bbox, con PyMuPDF) y `BACKEND/plano/extractor.py` (regex por posición). Solo cubre tablas de aplicación: acero en losa, zapata de muro de lindero, f'c por rango y losa aligerada de P16. Cada valor lleva fuente (archivo, revisión, página, hoja, bbox), queda `pendiente_de_verificar`, pasa por `importadores/validador_diseno.py` y se confirma por lote (`plano/confirmacion.py`, tabla `tablas_extraidas`) o uno por uno en la Mesa de Dudas.
- **Lo que no cubre:** columnas, muros, zapatas aisladas, pórticos por tramo (§4.3), detalles, y obras sin vectorial (decisión 3 de la Etapa 2: "se agrega el ocr o se procesa en el chat", tarea futura).
- **Frontend:** un solo `FRONTEND/index.html` (1.461 líneas, 125 KB), Vue 3 + Tailwind + Font Awesome **desde CDN**, tema oscuro, sin compilación; 86 ganchos `data-*`; 6 modales (Nueva obra, Subir visita/Dropbox, Visor y recuadros, Datos de la obra, Confirmar datos del plano, Mesa de Dudas). Habla con 29 rutas `/api/...`.
- **Trabajos en segundo plano:** ya existen `trabajos` y `trabajo_eventos` (Etapa 3 · T10a); la pantalla en vivo (T10b) está pendiente.

## Decisiones de diseño (propuestas del Director; se vuelven firmes al aprobar)

### Fase A — cómo entra Claude sin llave y sin romper la Regla de Oro
El trabajo se parte en tres piezas. Solo la del medio es Claude; las otras dos son código del backend que funciona sin internet.

| Paso | Quién | Qué hace |
|---|---|---|
| 1. Preparar | Backend (botón del tablero) | Por cada hoja del vectorial vigente guarda en la carpeta local de la obra una imagen de la hoja y la lista de textos visibles, cada uno con un número y su recuadro (los da `lector_plano`). |
| 2. Leer | Sesión de Claude Code (suscripción), con la skill `extraer-plano` | Mira la imagen y la lista, y escribe un archivo `propuesta.json` por hoja: qué texto corresponde a qué campo de qué elemento, **citando el número del texto**. No toca la BD. |
| 3. Importar | Backend (botón del tablero) | Comprueba cada valor contra el texto citado y carga las propuestas por el mismo camino que el extractor actual. |

1. **Claude razona; el valor lo pone el plano.** Al importar, el backend comprueba que el valor propuesto coincide con el texto citado del plano:
   - coincide → propuesta `pendiente_de_verificar` con su fuente (hoja + bbox del texto citado) y `extraido_por = "IA:claude-code"`;
   - no coincide, no cita, o Claude marca duda → el campo queda `"pendiente de verificar"` sin valor y se abre una duda con prefijo `IA:`.
2. **Nada de lo que proponga Claude nace `confirmado`.** Entra por el validador de T2, con clave UNIQUE idempotente, nunca toca un campo ya confirmado, se confirma por lote o por la Mesa de Dudas y deja auditoría por campo.
3. **Doble lectura donde ya hay extractor:** si el extractor por posición y Claude leen el mismo campo y difieren, se abre una duda; si coinciden, se anota como comprobación en verde (el campo sigue pendiente hasta que Steven confirme).
4. **Capas (§4.1):** Claude solo trabaja en la Capa 1 (planos). Nunca recibe fotos de campo como fuente de datos de diseño y no calcula cuantías ni recubrimientos (eso es `reglas_ingenieria.py`).
5. **Offline (§1.5):** la app no llama a ningún servicio. Preparar e importar funcionan sin internet; solo el paso 2 necesita una sesión de Claude Code. Generar informes sigue 100 % offline.
6. **Sin costo adicional:** no hay llave, ni `.env`, ni SDK de pago. El paso 2 consume cupo de la suscripción; A1 mide cuánto por hoja para que Steven sepa cuántas hojas caben en un día de trabajo. Se lee por lotes de hojas, nunca el PDF entero, y se puede retomar donde quedó.
7. **El plano no se modifica:** se comprueba el sha256 del vectorial al preparar y al importar; si el plano cambió, la propuesta no se importa.

### Fase B — cómo se rehace el tablero
1. **Primero inventario, luego diseño, luego código.** Nada del tablero actual se pierde: B0 lista cada pantalla, acción, ruta y gancho `data-*`, y esa lista es la prueba de paridad al final.
2. **Steven elige la dirección visual** entre 2–3 maquetas antes de escribir la interfaz real (B1). El resultado se fija en `DESIGN.md`.
3. **Se parte el archivo único** en módulos y componentes para que varias sesiones puedan trabajar sin pisarse, y **todo queda local** (sin CDN), que ya era un pendiente del traspaso.
4. **Backend intacto:** la Fase B no cambia rutas ni respuestas de la API. Lo que necesite del backend lo pide al Director.
5. La pantalla en vivo del procesador (Etapa 3 · T10b) y la pantalla de lectura asistida se construyen dentro del tablero nuevo, no en el viejo.

## Fases

| Fase | Alcance | Zona de archivos | Depende de | Modo | Estado |
|---|---|---|---|---|---|
| **0 · Cimientos** | git al día, ajuste de la especificación | `PLANES/`, `CLAUDE.md` + `AGENTS.md` | Aprobación de Steven | **directo** | T0.1 hecha · T0.2 no hace falta · T0.3 pendiente (no bloquea A ni B) |
| **A · Claude razona los planos** | reconocimiento, preparar hojas, importar con anclaje, skill `extraer-plano`, rutas, prueba real | `BACKEND/plano/asistido/**` (nuevo), `.claude/skills/extraer-plano/` (nuevo), `BACKEND/tests/test_asistido_*.py` | Fase 0 | **líder** (Opus) | pendiente |
| **B · Rediseño del tablero** | inventario, dirección visual, base, pantallas, movimiento, prueba de rotura | `FRONTEND/**`, `DESIGN.md` | Fase 0 | **líder** (Opus) | pendiente |
| **C · Integración** | pantalla "Lectura asistida" contra las rutas reales, auditoría de integración, prueba completa en el navegador | `FRONTEND/**` (solo esa pantalla), `PLANES/` | A5 y B3 | **directo** | pendiente |

**Paralelismo:** la Fase 0 va sola y primero. Después **A y B corren a la vez**: no comparten ningún archivo (`main.py` se toca solo en la Fase 0; si A o B necesitan otro cambio ahí, lo piden al Director). La Fase C va al final. Para cuidar el cupo de la suscripción: **máximo 3 sesiones trabajando a la vez en total**, no 4 por nivel.

**Nadie más toca `FRONTEND/` mientras dure la Fase B** (ni Codex ni tareas de las Etapas 2–4); ver D7.

## Tareas

### Fase 0 — Cimientos (directo)

#### T0.1 — Puesta al día de git (Steven decide; ver D1)
- Ejecutor: Director, con permiso expreso de Steven para cada paso.
- Hecho cuando: existe una rama `claude/etapa5-plan` salida de `origin/main` con este plan; el checkout principal queda como Steven decida.

#### T0.2 — Estáticos y contrato — NO HACE FALTA (16/11/2026)
- Comprobado en `main`: `BACKEND/main.py:196` ya monta toda la carpeta `FRONTEND/` en `/` (`StaticFiles(..., html=True)`). El tablero nuevo puede repartirse en archivos sin tocar el backend, y el viejo puede vivir en `FRONTEND/clasico/index.html` (se abre en `/clasico/`).
- El contrato de rutas es el de A5 (abajo). El formato de `textos.json` y `propuesta.json` lo fija el Líder de la Fase A en `PLANES/etapa-5-contrato-asistido.md` después de A1.
- Única excepción a "nadie toca `main.py`": A5 agrega **una línea** `app.include_router(...)` para sus rutas.

#### T0.3 — Especificación
- Ejecutor: Director (texto) · rama `claude/etapa5-spec`
- Qué hacer: proponer a Steven el texto nuevo de `CLAUDE.md` y `AGENTS.md` (los dos iguales): sección "Lectura de planos asistida por Claude" con las decisiones A1–A7 y la regla de que no se usan servicios de pago. Se aplica solo con su visto bueno.

### Fase A — Claude razona los planos (líder)

#### A1 — Reconocimiento (solo lectura)
- Ejecutor: una sesión de Sonnet prepara las hojas a mano; el Líder (Opus) hace la lectura · informe `PLANES/etapa-5-reconocimiento-asistido.md`
- Qué hacer: con el vectorial vigente de Terra Living, probar 4–6 hojas elegidas con Steven: una tabla que el extractor actual ya lee y Steven ya confirmó (sirve de control) y hojas que hoy no se leen (cuadro de columnas, detalle de muro, elevación de un pórtico con su banda de estribos, zapatas). Probar 2–3 resoluciones de imagen. Medir por hoja: aciertos contra el plano, valores sin ancla, tiempo y consumo de cupo.
- Hecho cuando: el informe trae la tabla de resultados por hoja, la resolución recomendada, cuántas hojas caben razonablemente por sesión y la lista de tipos de elemento ordenada por fiabilidad. El Director lo contrasta con el plano real. Nada se escribe en la BD ni en Dropbox.
- **Puerta:** Steven ve el informe antes de A3 y A4.

#### A2 — Preparar hojas
- Ejecutor: ejecutor-backend (Sonnet) · Archivos: `BACKEND/plano/asistido/__init__.py`, `preparar.py`, `BACKEND/tests/test_asistido_preparar.py`.
- Qué hacer: para una obra y una lista de páginas, escribir en la carpeta local de la obra (`CATDIC_DATOS_RAIZ`, nunca en Dropbox ni en el repositorio) `pNN/hoja.png` y `pNN/textos.json` (número, texto, bbox, hoja), más un `manifiesto.json` con el sha256 del vectorial. Reutiliza `lector_plano` sin modificarlo. Solo lee capas visibles.
- Hecho cuando: pruebas `# SINTÉTICO` con un PDF pequeño; preparar dos veces da el mismo resultado; el plano no cambia (sha256 antes y después).
- Puede ir en paralelo con A1.

#### A3 — Importar con anclaje
- Ejecutor: ejecutor-backend (Sonnet) · Archivos: `BACKEND/plano/asistido/esquema.py`, `importar.py`, pruebas.
- Qué hacer: validar `propuesta.json` contra el esquema; aplicar las decisiones A1–A3 y A7; reutilizar `validador_diseno` y las funciones de escritura y de dudas de `plano/extractor.py` **sin modificarlas** (si hace falta abrir una función, se pide al Director).
- Reglas que se prueban: formato de `EJES` de §4.4 (losas siempre `—`; nada deducido por cercanía); planta contra detalle en contradicción → `DUDA_BLOQUEANTE` (§4.2); un valor sin texto citado nunca se guarda como valor; un archivo mal formado no carga nada.
- Hecho cuando: pruebas `# SINTÉTICO` con propuestas buenas, sin ancla, con valor distinto al texto, con plano cambiado y repetidas (idempotencia); 0 campos `confirmado`.

#### A4 — Skill `extraer-plano` (el procedimiento que sigue Claude al leer)
- Ejecutor: Líder de la fase (Opus) · Archivos: `.claude/skills/extraer-plano/SKILL.md` y sus referencias por tipo de elemento.
- Qué hacer: el procedimiento paso a paso para la sesión lectora: qué archivos abrir, cómo citar, qué hacer ante duda (marcarla, nunca rellenar), las reglas de §4.2–§4.4 y el formato exacto de salida. Un apartado por tipo, en el orden que salga de A1 (propuesta): **A4a** columnas · **A4b** muros y zapatas · **A4c** pórticos por tramo (§4.3, con el control cruzado `S + losa = Hv`) · **A4d** losas y lo que falte.
- Hecho cuando (cada apartado): una sesión nueva, solo con la skill, lee las hojas de A1 de ese tipo y al importar quedan 0 valores sin ancla guardados; el Director contrasta una muestra contra el plano.

#### A5 — Rutas
- Ejecutor: ejecutor-backend (Sonnet) · Archivos: `BACKEND/plano/asistido/rutas.py`, pruebas.
- Contrato (se fija en T0.2):
  - `GET /api/proyectos/{id}/lectura-asistida` → estado por hoja: sin preparar / preparada / propuesta lista / importada / plano cambiado
  - `POST /api/proyectos/{id}/lectura-asistida/preparar` `{paginas?: [..]}`
  - `POST /api/proyectos/{id}/lectura-asistida/importar` `{paginas?: [..]}` → propuestas cargadas, dudas abiertas, valores rechazados por falta de ancla
  - los resultados se ven por las rutas actuales de `elementos`, `tablas-extraidas` y `dudas`.
- Hecho cuando: cada importación deja una fila en `auditoria`; importar dos veces no duplica.

#### A6 — Prueba real y cierre de fase
- Terra Living completo y Torre P16 (Losa E-9), por lotes de hojas. Informe: elementos propuestos por tipo, dudas abiertas, cupo consumido. El Director audita contra los planos.

#### A7 — (Opcional, por verificar) Botón que lanza a Claude desde el tablero
- Averiguar si Claude Code puede arrancarse desde el backend con la suscripción, sin llave y sin costo adicional, para que el paso 2 también sea un botón. Si no se puede garantizar que no cobra, **no se hace** y el paso 2 se sigue pidiendo a una sesión.

### Fase B — Rediseño del tablero (líder)

#### B0 — Inventario funcional (solo lectura)
- Ejecutor: ejecutor-frontend (Sonnet) · informe `PLANES/etapa-5-inventario-ui.md`
- Hecho cuando: están listadas todas las pantallas, modales, acciones, estados (cargando, vacío, error), rutas que usa cada una y los 86 `data-*`. El Director lo contrasta con `index.html`.

#### B1 — Dirección de diseño (puerta de Steven)
- Ejecutor: Líder de la fase (Opus) con `impeccable`, `ui-ux-pro-max` y `apple-design`.
- Qué hacer: proponer la navegación (hoy todo es una página con modales; propuesta: barra lateral con Obras, Cola de visitas, Mesa de Dudas, Planos y datos de diseño, Órdenes) y 2–3 maquetas de la pantalla principal y de "Confirmar datos del plano", con datos reales de ejemplo. Escribir `DESIGN.md` (color, tipografía, espaciado, componentes, movimiento).
- **Puerta:** Steven elige. Sin elección no empieza B2.

#### B2 — Base
- Ejecutor: ejecutor-frontend (Sonnet) · Archivos: estructura nueva de `FRONTEND/` (según D5), librerías locales en `FRONTEND/vendor/`, tokens de diseño, armazón con navegación, cliente de la API.
- Hecho cuando: el armazón abre en `http://localhost:8000` **sin internet** y el tablero viejo sigue disponible en `/clasico` hasta el cierre de la fase.

#### B3 — Pantallas (una tarea por pantalla, cada una en sus propios archivos)
- B3a Obras y tablero · B3b Obra: planos, datos de la obra, visor y recuadros · B3c Confirmar datos del plano · B3d Cola de visitas, subir visita/Dropbox y avance del procesador (cubre T10b) · B3e Mesa de Dudas · B3f Órdenes de trabajo.
- Hecho cuando (cada una): todas sus filas del inventario B0 marcadas y probadas en el navegador contra una **copia** de la BD; cero errores en consola.

#### B4 — Movimiento y pulido
- Skills: `animate`, `choreograph`, `emil-design-eng`, `animation-performance`; revisión con `review` de `impeccable`. Respeta `prefers-reduced-motion`.

#### B5 — Prueba de rotura y cierre
- `break-ui` con datos extremos (nombres de obra larguísimos, 0 visitas, 500 dudas, IDs con prima `A'`, campos `"pendiente de verificar"`), teclado y contraste, anchos 1280 y 1920. Paridad completa con B0. Se retira `/clasico` solo con el visto bueno de Steven.

### Fase C — Integración (directo)
- **C1** Pantalla "Lectura asistida": estado por hoja, botón Preparar, la frase exacta que hay que decirle a Claude Code para que lea, botón Importar, y el resultado que lleva a Confirmar datos y a la Mesa de Dudas. Las propuestas de Claude se distinguen a la vista de las del extractor por posición.
- **C2** Auditoría de integración del Director: recorrido completo en el navegador (obra → preparar → leer → importar → confirmar → procesar visita → PDF), suite completa y revisión contra los 18 errores.

## Modelos y sesiones (skill `gestion-proyectos` §3)
| Rol | Modelo | Esfuerzo |
|---|---|---|
| Director | `claude-fable-5-2` hoy; `claude-opus-5-5` alto desde el 17/11/2026 | alto |
| Líder de fase A y B | `claude-opus-5-5` | alto |
| Ejecutor estándar | `claude-sonnet-5-5` | medio |
| Ejecutor mecánico (mover archivos, librerías locales) | `claude-haiku-5-5` | bajo |

Cada ejecutor trabaja en su propio worktree salido de `origin/main`. Ver D8 sobre "fresh" contra "fork". Todo sale del cupo de la suscripción de Steven: si se agota, el trabajo se detiene hasta que se renueve; **no se activa el uso adicional de pago**.

## Reglas de convivencia (de `COLABORACION.md`, sin cambios)
- Ramas `claude/etapa5-<tarea>`; nadie hace push a `main`; un PR por tarea; **Steven fusiona**.
- Todas las ramas de la etapa salen de `claude/etapa5-plan` (trae este plan y los planes rescatados). Una tarea que depende de otra sale de la rama de la anterior.
- Los Líderes y Ejecutores solo hacen commits locales en su propia rama de tarea. **Ningún push, fusión ni cambio en el checkout principal sin permiso de Steven**; el push va después de la auditoría del Director.
- Suite de referencia en `main` (`b5f7d26`, 16/11/2026): 943 pasan, 3 saltadas y **2 fallan por el contenido actual de Dropbox**, no por el código (`test_escaner_dropbox.py::test_terra_living_real`: el PDF `TERRA LIVING -ESTRUCTURALES.pdf` pesa 57.692.301 bytes y la prueba espera 57.692.938; `test_parser_visitas.py::test_lista_coincide_con_dropbox_si_esta_disponible`: faltan 6 carpetas de visita con el nombre esperado). Pendiente de verificar con Steven; ninguna tarea de la Etapa 5 las toca.
- Antes de cambiar de rama, hacer commit, push o fusionar: se le pregunta a Steven.
- Nunca se suben `*.db`, PDFs, fotos ni las carpetas de hojas preparadas. Dropbox en solo lectura. La BD real se respalda antes de tocarla; las pruebas usan `CATDIC_DB_PATH`.
- Todo con `py -3.14`.

## Puesta al día de git (propuesta; no se ejecuta sin Steven)
Situación: el checkout principal está en `codex/planes-traspaso` (`bd197d0`), **97 commits detrás de `origin/main`**; `main` local está 11 detrás; hay 5 worktrees viejos; y hay cambios sin commitear en 4 archivos de `PLANES/` con unas **400 líneas que una comparación rápida no encontró en `origin/main`** (sobre todo `etapa-2-evaluacion.md`; por confirmar), más `.agents/`, `.claude/skills/` y `PLANES/referencia/` sin trackear.
1. Copiar esos 4 archivos y las 3 carpetas a una carpeta de respaldo fuera del repositorio.
2. Comparar el respaldo con `origin/main` y decirle a Steven qué texto se perdería; lo que valga se rescata en un PR de documentación.
3. `git switch main` y `git pull --ff-only`, para que `INICIAR_CATDIC.bat` arranque la versión actual.
4. Limpiar los worktrees viejos solo con su permiso.

Mientras tanto la Etapa 5 no depende de esto: todas las sesiones trabajan en worktrees salidos de `origin/main`.

## Riesgos que hay que vigilar
- **Claude inventa o lee mal un número.** Mitigación: anclaje al texto del plano, doble lectura, todo pendiente, confirmación humana. Se mide en A1 antes de construir.
- **Hojas donde el dato no es texto** (cotas dibujadas, planos escaneados): no hay ancla. Quedan fuera salvo D4.
- **El cupo de la suscripción se agota** a mitad de una lectura o del proyecto. Mitigación: lotes de hojas retomables, máximo 3 sesiones a la vez, Sonnet para lo mecánico.
- **El paso 2 no es un botón:** hay que pedírselo a una sesión de Claude Code. A7 estudia si puede serlo sin costo.
- **Perder funciones al rediseñar.** Mitigación: inventario B0, paridad en B5, tablero viejo en `/clasico` hasta el final.
- **Choque con Codex o con tareas de las Etapas 2–4** en `FRONTEND/` o `main.py`. Mitigación: congelación de D7 y Fase 0 primero.
- **`CLAUDE.md` y `AGENTS.md` desincronizados.** Se cambian juntos en T0.3.

## Decisiones que quedan para Steven
- **D1 · Git:** ¿apruebas la puesta al día de arriba (respaldo → comparar → `main` al día)? ¿O dejo el checkout como está y solo trabajo en worktrees?
- ~~D2 · Privacidad~~ — resuelta (16/11): sin servicios nuevos.
- ~~D3 · Gasto~~ — resuelta (16/11): sin llave y sin pago adicional.
- **D4 · Planos sin vectorial (escaneados):** ¿entran en esta etapa? Si entran, sus valores no tienen ancla y se confirmarían siempre uno por uno, nunca por lote. Propuesta: fuera de esta etapa.
- **D5 · Cómo se arma el frontend:** (a) **sin compilación**: varios archivos, Vue y Tailwind copiados localmente, se sigue abriendo con `INICIAR_CATDIC.bat` — propuesta; o (b) con Vite (Node ya está instalado): mejor para componentes, pero agrega un paso de compilación en cada cambio.
- **D6 · Estilo:** ¿hay alguna referencia que te guste (una app, una web), sigue el tema oscuro, se mantienen el amarillo y el nombre "Control Taller"? Si no dices nada, B1 te trae 2–3 opciones.
- **D7 · Codex:** ¿sigue revisando los PR? ¿Y aceptas que nadie más toque `FRONTEND/` mientras dure la Fase B (T10b pasa a ser B3d)?
- **D8 · Sesiones:** la skill nueva lanza ejecutores "fresh"; tu regla del 09/11 era lanzarlos con "fork". ¿Vale la skill nueva para esta etapa? Propuesta: sí (fresh, gasta menos cupo).
- **D9 · Orden de tipos en A4:** propuesta columnas → muros y zapatas → pórticos → losas. ¿O hay un tipo que te urja más?

## Verificación
- **Fase 0:** suite en verde; ninguna dependencia nueva en `requirements.txt`.
- **Fase A:** informe A1 contrastado con el plano; por apartado de A4, 0 valores sin ancla guardados y 0 `confirmado` sin acción del usuario; volver a importar es idempotente; el sha256 del plano no cambia.
- **Fase B:** paridad con B0 fila por fila en el navegador; sin peticiones a internet (pestaña de red); `break-ui` sin roturas abiertas.
- **Fase C:** recorrido completo y auditoría `auditar-catdic` con veredicto APROBADO antes de cada push.

## Fuera de alcance de esta etapa
- Cualquier llave de API o servicio de pago (Claude, Gemini u otro).
- Etapa 4 (formatos HV) y CATDIC-STP (T9, aplazada).
- Que Claude lea visitas a obra o fotos de campo (Capa 2).
- Usuarios y roles.
- Cambios en los generadores de PDF.

## Bitácora (lo más nuevo arriba)
- 16/11/2026 · Director: T0.1 hecha. Respaldo en `C:\Users\Steve\CATDIC-RESPALDOS\etapa5-2026-11-16` (planes locales, skills, BD) y en `git stash` ("respaldo-etapa5-2026-11-16"). Los 4 archivos locales de `PLANES/` eran superconjuntos de `origin/main` (Evaluaciones 5–13 de la Etapa 2, 23 de la Etapa 3 y decisiones de Steven sin subir): se rescatan en la rama `claude/etapa5-plan`. Checkout principal en `main` = `b5f7d26`.
- 16/11/2026 · Steven aprueba el plan con las propuestas.
- 16/11/2026 · Director: plan v2. Steven decide sin llave y sin pago adicional; la Fase A pasa a preparar → leer con Claude Code → importar con anclaje. Sin sesiones lanzadas.
- 16/11/2026 · Director: plan en BORRADOR; lectura hecha sobre `origin/main` `b5f7d26`.
