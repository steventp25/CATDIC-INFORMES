## Evaluación 1 · 22/11/2026 · Planificador (auditoría) · Fase B · B3a y B3d (rama `claude/etapa5-fase-b-0020e1`, `4422678`)
**Veredicto: APROBADO**

Steven vio las dos pantallas en una copia de la rama (puerto 8767, BD de prueba copiada) y respondió: «Sí, sigue así» (22/11/2026).

### Bloqueantes
- Ninguno.

### Observaciones (no bloquean)
- **Paridad con el tablero clásico.** `FRONTEND/clasico/` y `test_clasico_entrega_el_tablero_anterior` siguen intactos, como pidió Steven el 20/11 («Conserva el tablero clásico»). El tablero nuevo no enlaza al clásico (`ddca35f`, decisión del 19/11). Si el clásico debe volver a tener enlace es una decisión pendiente de Steven; no bloquea.
- **`BACKEND/tests/test_frontend_servido.py`.** Es el único archivo de `BACKEND/` que cambia respecto a `main` (B2, +19/−4). Es una prueba del servidor y no toca código de ejecución.
- **Trabajos tras recargar.** Sin una ruta que liste trabajos, al recargar la página solo se retoma el trabajo de la misma pestaña o el que se abre por su enlace. Queda anotado como Fase D.
- **Aviso de paquete de Campo.** Necesita `paquete_campo` por visita en `/api/dashboard` y `origen` en `visita_inicio`. Es para una tarea posterior, después de que se fusione el PR #35.

### Criterios de aceptación
- [x] **Zona respetada.** El rango `e65efdb..4422678` toca solo `FRONTEND/js`, `FRONTEND/css`, `FRONTEND/index.html` y `PLANES/`. No toca `clasico/`, `vendor/`, `maquetas/` ni código del backend.
- [x] **Sin menciones al clásico.** `git grep -i 'clásico|clasico'` en `FRONTEND`, excluidas `clasico/`, `maquetas/` y `vendor/`, da 0 resultados.
- [x] **Sin URL externas.** Solo hay rutas a `127.0.0.1`, `localhost` y `w3.org`. En el navegador: 0 errores de consola en Inicio, Bandeja y `#/obra/terra-living/visitas`.
- [x] **Sin archivos prohibidos.** El diff no contiene `*.db`, PDF, imágenes ni `.env`.
- [x] **Regla de Oro.** `js/datos.js` solo usa datos de `/api/dashboard` y `/api/dudas`. Los días salen de `fecha_visita` real, o quedan en `null` y se muestran como «pendiente de verificar». Los indicadores sin dato dicen «pendiente de verificar» o «Fase D», nunca 0.
- [x] **Ningún POST se reintenta solo** (`api.js`, `cola-acciones.js`). El polling se cancela al salir de la pantalla (`trabajo.js`: `clearTimeout` y `AbortController.abort()`).
- [x] **Una sola cola.** Inicio muestra el resumen y los botones y enlaza a la Bandeja, sin una segunda tabla.
- [x] **Steven las vio y las aprobó.**
- [?] **Matriz Playwright de 5 anchos × 2 temas y peor caso de 300 visitas.** No la repetí; la reportan el Ejecutor y el Líder. Yo solo vi el ancho del panel (unos 800 px) en tema claro.

### Pruebas ejecutadas
- **Suite completa sobre una copia exacta de `4422678`** (`git archive` al scratch), `python -m pytest -q`: 944 pasan, 3 se omiten y 2 fallan. Las 2 fallas son las conocidas de Dropbox y no vienen de este diff:
  - `test_escaner_dropbox.py::test_terra_living_real`: el PDF real pesa distinto de lo esperado.
  - `test_parser_visitas.py::test_lista_coincide_con_dropbox_si_esta_disponible`: hay carpetas nuevas en Dropbox, por ejemplo «COLUMNAS  S-5 PARCIALES Y PORTICOS» sin número.
- **En el navegador:** el servidor arrancó con una BD copiada y las salidas en el scratch. Inicio, Bandeja y Visitas y trabajos cargan con datos reales de la copia.

### Pendientes de verificar
- **Push:** no se hace. La regla de la fase dice «sin push» hasta cerrarla, y Steven pidió que se le pregunte antes de cualquier push.

## Evaluación 2 · 22/11/2026 · Planificador (auditoría) · Fase B · B3g Informes dentro de la obra (rama `claude/etapa5-fase-b-0020e1`, `e5a1c62`)
**Veredicto: APROBADO** (falta que Steven la vea)

### Bloqueantes
- Ninguno.

### Observaciones (no bloquean)
- **Una visita «Procesada» no se puede volver a lanzar**, así que no hay forma de regenerar su informe desde la pantalla. Es lo que permite hoy el procesador (`/api/visitas/{id}/procesar` solo acepta Sin procesar, En cola o Con dudas). Si Steven quiere regenerar informes de visitas ya procesadas, es una decisión de producto con backend nuevo (Fase D).
- **`ruta_registrada` lee todos los eventos `pdf_generado` en cada apertura.** Con el volumen actual no importa; si crece, conviene un índice o filtrar en SQL.
- **Dónde quedan los PDF.** Hoy el procesador publica en la salida de pruebas (`CATDIC_SALIDA_PRUEBAS`), no en `INFORMES\2.DATA PROCESADA`. La lista muestra lo que se generó ahí.
- **No se generó un PDF real de punta a punta.** La copia de la BD no tiene datos de diseño suficientes. La lista se probó con eventos y PDF sintéticos.

### Criterios de aceptación
- [x] **El backend se queda dentro de la excepción.** Cambian solo `BACKEND/informes_obra.py` (nuevo, de solo lectura), las 2 rutas de `main.py` y `tests/test_informes_obra.py`. No cambian `procesador_cola.py`, `database.py` ni el esquema.
- [x] **Abrir un PDF solo sirve rutas registradas.** `GET /api/informes/archivo` compara la ruta exacta con los eventos `pdf_generado` antes de tocar el disco; cualquier otra ruta da 404, y un archivo ausente también da 404. No hay rutas libres.
- [x] **Los informes se listan** del más nuevo al más viejo, con su versión `vN` y con `existe`. Un archivo ausente se marca, no se oculta.
- [x] **En el navegador** (copia de `e5a1c62`, BD copiada, puerto 8767):
  - la pestaña Informes muestra el vacío «Esta obra todavía no tiene informes generados»;
  - «Hacer informe» lista las 24 visitas, de las que 18 se pueden lanzar;
  - las «Procesada» salen deshabilitadas, con el motivo escrito;
  - el diálogo cabe en la pantalla y se cierra con Escape;
  - 0 errores de consola.
- [x] **Los formatos que no existen** (CATDIC-STP y HV) aparecen como «disponible más adelante», sin simulación.
- [?] **Matriz de 5 anchos × 2 temas y peor caso de 200 informes.** La reportan el Ejecutor y el Líder; no la repetí.

### Pruebas ejecutadas
- **Suite completa sobre una copia exacta de `e5a1c62`:** 955 pasan, 3 se omiten y 2 fallan. Son las 2 conocidas de Dropbox, por el contenido actual de Dropbox y no por este diff.

## Evaluación 3 · 23/11/2026 · Planificador (auditoría) · Fase B · B3e Mesa de Dudas y visor de revisión (rama `claude/etapa5-fase-b-0020e1`, `4405ca2`)
**Veredicto: BLOQUEADO** (1 bloqueante pequeño de uso; el resto está bien)

### Bloqueantes
- **La Mesa se abre fuera de la pantalla** (`FRONTEND/js/pestana-visitas.js` / `mesa-dudas.js`; el enlace sale de `cola.js:186`).
  - **Qué pasa:** desde la cola de «Visitas y trabajos», con la página desplazada hacia abajo, al pulsar «Abrir la Mesa de Dudas» cambia el hash y la Mesa se monta arriba, pero queda fuera de la pantalla y el foco se queda en `BODY`. Para Steven, el enlace parece no hacer nada.
  - **Evidencia** (copia de `4405ca2`, 800 px): clic en el enlace de la visita 4 → `scrollY` pasa de 1959 a 1389, el encabezado «Mesa de Dudas» queda en `top = -787` (no visible) y `document.activeElement` es `BODY`. Lo mismo ocurre al recargar con `?visita=`.
  - **Corrección esperada:**
    - Cuando la ruta trae `?visita=` (o `?dudas=obra`), y también cuando cambia la duda con `&duda=`, la Mesa se desplaza a la vista (`scrollIntoView`) y el foco pasa a su encabezado (`tabindex="-1"`, sin marco de foco visible).
    - Si hay `&duda=`, el desplazamiento va al detalle de esa duda.
    - Hace falta una prueba de Playwright que lo compruebe desde la cola desplazada, en 375 y 1280 px.

### Observaciones (no bloquean)
- **Backend dentro de la excepción.** `leer_refs_duda` y `GET /api/dudas/{id}/refs` son de solo lectura y toman el evento `duda` más reciente (`creado DESC, n DESC`). Responden 404 si la duda no existe y `refs: null` si no hay evento. `/api/dudas` no cambia.
- **Visor sin datos de plano en la copia.** La duda #52 muestra «pendiente de verificar» en Ubicación y Detalle, con el motivo («La obra no tiene plano vigente…»), y «Abrir plano» deshabilitado con el mismo motivo. Es correcto según la Regla de Oro: no se adivina nada.
- **Diseño en pantalla ancha.** A 1440 px la lista queda a la izquierda y Ubicación/Detalle/Respuesta a la derecha, como en la referencia de PlanRadar que mandó Steven. A 800 px se apila.
- **Abiertos del Líder** (siguen sin bloquear):
  - `refs.plano.recuadro` no se dibuja todavía, porque su sistema de coordenadas es desconocido;
  - el zoom con pellizco está sin probar;
  - los 409/422 aparecen en consola como «Failed to load resource». Son errores del navegador por códigos de la API, no de la página.
- **Falta un caso real.** No pude ver el visor con un plano real en la copia: no tiene plano vigente. Hay que verificarlo con una obra con plano cuando Steven lo pruebe.

### Criterios de aceptación
- [x] El backend se queda en `mesa_dudas.py` y `tests/test_dudas_refs.py`, sin cambio de esquema y sin tocar `procesador_cola.py`.
- [x] Las dudas no se atan por `id_elemento`: solo por `refs.plano.uid_diseno` o `campo_confirmable.uid` (revisión del Líder; en la copia, las refs llegan nulas y no se ata nada).
- [x] El visor muestra Ubicación, Detalle y «Abrir plano», y cae a «pendiente de verificar» con su motivo.
- [ ] **Abrir la Mesa desde la cola la pone a la vista.** Bloqueante de arriba.
- [?] Matriz de Playwright y peor caso de 376 dudas: la reporta el Ejecutor, no la repetí.

### Pruebas ejecutadas
- **Suite completa sobre una copia exacta de `4405ca2`:** 964 pasan, 3 se omiten y 2 fallan (las 2 conocidas de Dropbox).
- **En el navegador** (BD copiada, puerto 8767): Mesa de la visita 3, detalle de la duda #52, 1440 px y 800 px, y la medición del desplazamiento y el foco descrita arriba.
