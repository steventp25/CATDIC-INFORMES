# B3e — Mesa de Dudas con visor de revisión (Ubicación · Detalle · Abrir plano) y dudas en la Bandeja (encargo del Líder al Ejecutor)

Fecha: 22/11/2026. Va después de B3g. Orden de B3: B3a → B3d → B3g → **B3e** → B3b → B3c → B3f. Estilo **Plano sellado**: ver `FRONTEND/DESIGN.md`.

Lo pidió Steven el 22/11: «CUANDO EL PROGRAMA ME PIDA QUE ESTA EN REVISION, QUIERO QUE LA PANTALLA DE REVISION ME UBIQUE EL ELEMENTO Y ME DE EL DETALLE DEL ELEMENTO O TAMBIEN OTRA OPCION APARTE DE ESOS ES ABRIR EL PLANO». Su referencia es PlanRadar: la lista de pendientes a la izquierda y el plano a la derecha, con marcadores.

## Dónde se trabaja (igual que en B3d y B3g)
- **Worktree y rama:** `C:\Users\Steve\OneDrive\Desktop\CATDIC-WEB\.claude\worktrees\etapa2-t7n-confirmacion-8210cf`, rama `claude/etapa5-fase-b-0020e1`.
  - No crees ni cambies de rama. Nada de push, merge ni stash. No toques el checkout principal.
  - Trabajas por turnos con el Líder.
- **Zona:**
  - `FRONTEND/**`, menos `maquetas/`, `clasico/` y `vendor/`;
  - `PLANES/etapa-5-reportes/B3e.md`;
  - y la **excepción de backend que aprobó el Director el 22/11**, que es solo esto:
    - en `BACKEND/mesa_dudas.py`, la ruta nueva `GET /api/dudas/{id}/refs` y su función de lectura;
    - las pruebas nuevas en `BACKEND/tests/test_dudas_refs.py`.
- **Prohibido:**
  - cambiar la respuesta de `GET /api/dudas`, porque la usa también el tablero clásico;
  - tocar `procesador_cola.py` (lo cambia el PR #35), `database.py`, el esquema, `visor.py` y cualquier otro archivo de `BACKEND/`;
  - borrar o editar `FRONTEND/clasico/` o `BACKEND/tests/test_frontend_servido.py`;
  - revertir o ampliar `ddca35f`;
  - cualquier mención o enlace al clásico.
- **Python:** `C:\Users\Steve\AppData\Local\Python\pythoncore-3.14-64\python.exe`.

## Reglas (las de las tareas anteriores siguen vigentes)
- **Sin red:** nada de internet, librerías nuevas ni descargas.
- **Frontend:** sin compilación, con scripts clásicos y `window.CATDIC`. Reutiliza `componentes.js`, `C.api`, `C.formato`, `datos.js`, `cola.js` y el patrón de diálogo de `formulario-planos.js`.
- **Regla de Oro:**
  - lo que falte es «pendiente de verificar»;
  - nunca se inventan cifras ni datos de ingeniería;
  - nunca se adivina una ubicación;
  - lo que pide backend nuevo se rotula «Fase D».
- **Estilo:**
  - sin franjas laterales gruesas de color: el estado se dice con un borde completo, un icono y texto;
  - el rojo `--rojo-plano` (RGB 220,0,0) es solo para el recuadro de localización.
- **Formato:** fechas `DD/MM/AAAA` (con `HH:MM` donde haya hora) y textos en español.
- **Commits:** atómicos, en español, terminados en `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Nunca capturas, PDFs ni `*.db`.

## Qué hay que construir

### 1. Backend: `GET /api/dudas/{id}/refs` (excepción del Director)
- **Qué devuelve:** `{duda_id, refs}`. `refs` es `{elemento, plano, visita_pdf}`, sacado del `datos_json` del evento `duda` más reciente de esa duda en `trabajo_eventos`, buscando por `json_extract(datos_json, '$.duda_id')`.
  - El más reciente es el de mayor `creado` y, si empatan, el de mayor `n`.
  - Mira `procesador_cola.py`: `duda(...)`, cerca de la línea 387, y `_refs(...)`, cerca de la 532.
- **Respuestas:**
  - la duda no existe en `dudas_y_hallazgos`: **404**;
  - existe pero no tiene evento: **200** con `refs: null`.
- **Solo lectura:** sin cambio de esquema.
- **Pruebas** (`tests/test_dudas_refs.py`, con una BD de prueba en `tmp_path` y eventos insertados a mano):
  - una duda con evento;
  - una duda sin evento (`refs: null`);
  - dos eventos de la misma duda: gana el último;
  - las dudas de otra obra no se mezclan;
  - una duda inexistente da 404.

### 2. Visor de revisión: un componente compartido (`js/visor-revision.js` o similar)
Se construye **una sola vez**. Lo usan B3e (cada duda), B3c (cada elemento en revisión) y B3b (Planos y ficha). Recibe la obra y el `uid` del elemento, o directamente un recuadro, y muestra tres piezas:
1. **Ubicación (M3):**
   - pide `POST /api/proyectos/{id}/visor/vista-previa` con `{tipo:'localizacion', pagina, rect}` de `recorte_planta`;
   - el resultado es la planta completa del nivel con el recuadro rojo, igual que en los informes;
   - nunca un zoom irreconocible.
2. **Detalle (M4):**
   - la misma ruta con `tipo:'detalle'` y `recorte_detalle`;
   - nunca una foto de campo.
3. **Abrir plano:**
   - la hoja completa (`GET …/visor/hojas/{n}.png`, con `…/hojas/{n}/info` para pasar de puntos a píxeles; lee `rect_pt_a_px` en `BACKEND/visor.py`);
   - con zoom y desplazamiento (rueda, botones +/−, arrastre o dedo, y teclado);
   - centrado en el recuadro, que se dibuja encima en SVG con `--rojo-plano` y un grosor que se vea a tamaño de pantalla;
   - con selector de hoja desde `…/visor/indice` para ir a otras hojas;
   - en un diálogo a pantalla completa, con foco atrapado, Escape y foco de vuelta.

**De dónde sale el recuadro:**
- **Confirmado:** `GET /api/proyectos/{id}/elementos` → `recorte_planta` o `recorte_detalle` con `estado:'confirmado'` y el `plano_id` del plano vigente. Lee `listar_elementos` y `guardar_recuadro` en `visor.py`.
- **Sin confirmar:** `POST …/elementos/{uid}/propuesta`, que no guarda nada. La propuesta se rotula **«propuesta, pendiente de verificar»**, con su `fuente` y su `motivo`.
- **Recuadro de un plano que ya no es el vigente**, o sin plano vigente: «pendiente de verificar» con el motivo.
- **Sin recuadro, ni propuesta, ni hoja:** «pendiente de verificar». **Nunca se adivina la ubicación por cercanía.**
- **Las imágenes:** con `fetch` y `URL.createObjectURL`. Libera las URL al desmontar y guarda en memoria lo ya pedido. Cada pieza tiene sus estados: cargando, error con «Reintentar» y pendiente.

**Cómo se ata cada cosa a su elemento:**
- **Duda de visita:** `GET /api/dudas/{id}/refs` → `refs.plano.uid_diseno`, `pagina` y `recuadro`.
  - Con `refs: null`, sin `uid_diseno` o sin plano: **solo «Abrir plano»**, y Ubicación y Detalle quedan «pendiente de verificar».
- **Duda de obra T6n:** por `campo_confirmable.uid` de `/api/dudas`.
- **Prohibido atar por `id_elemento`:** el mismo ID se repite en varios niveles (Director, 22/11).
- **Duda que no se puede atar a ningún elemento:** solo «Abrir plano», sobre la primera hoja del índice. Si no hay plano vigente, «pendiente de verificar».

### 3. Mesa de Dudas (M1, paridad completa con `PLANES/etapa-5-inventario-ui.md` §2 M1, §3.4 A20–A27, §4 y §9 «Mesa de Dudas»)
**Disposición, como en PlanRadar:**
- a un lado, la lista de dudas: abiertas primero, después por id;
- al otro, la duda elegida con el visor de revisión y su respuesta;
- en móvil, apilado: primero la lista y, al elegir una duda, su detalle con «Volver a la lista»;
- todo con container queries.

**Lugar (decisión del Líder):** la Mesa es una vista con dirección propia, no un panel superpuesto. Así funcionan Atrás y los enlaces.
- **Modo visita:** en «Visitas y trabajos», con `#/obra/<id>/visitas?visita=<vid>`. Es la ruta que ya dejó B3d; sustituye su vista de solo lectura y el texto «Mesa de Dudas: la construye B3e».
- **Modo obra (dudas sin visita):** `#/obra/<id>/resumen?dudas=obra`. Actualiza a esa ruta el enlace «Dudas de la obra: N» de Mis obras (B3a).
- Puedes añadir `&duda=<id>` para abrir una duda concreta.
- En el informe, marca el ítem de §9 «Panel lateral, se cierra con X y clic en el fondo» como **sustituido por D6 (vista con dirección propia)**. «Cerrar» vuelve a la cola de la obra o al Resumen.

**Cabeceras, estados y avisos:**
- las cabeceras de modo visita y modo obra, con el texto de M1;
- cargando, los dos textos de vacío, el error de conexión, el conflicto 409 con « Se recargaron las dudas.» y el aviso de éxito con el texto de A26;
- el aviso «Esta visita figura como Procesada pero tiene dudas bloqueantes abiertas.».

**Tarjeta y controles:** exactamente los de la tabla de M1, en el mismo orden de prioridad:
- hallazgo interno;
- campo confirmable;
- duda con elemento;
- fecha;
- clase;
- estado con los STP candidatos;
- archivos;
- otro campo.

Llevan los mismos textos, el `PATCH /api/dudas/{id}` con el cuerpo de A21–A25, el error por duda y el bloqueo del envío doble. Ningún PATCH se reintenta solo.

**Al responder:**
- se recargan las dudas, la visita y el tablero (`datos.js`);
- la lista y los contadores de Inicio, la cola y Mis obras quedan al día.

**Desde el avance en vivo (`AvanceTrabajo`):**
- cada duda enlaza a su duda en la Mesa (`&duda=<id>`);
- responder dentro de la pantalla en vivo puede ser ese enlace: no hace falta duplicar la Mesa dentro del avance.
- Corrige en `cola.js` el texto de la fila «clic para responder», para que lleve a la Mesa.

**Apertura automática (A2 y A31, `abrirMesaSiHayDudasNuevas`), decisión del Líder:**
- no se abre nada por sorpresa;
- tras sincronizar o subir una visita con dudas nuevas, el resultado muestra un enlace claro: «N dudas nuevas · Abrir la Mesa de Dudas»;
- anótalo como paridad cubierta con otro patrón.

### 4. Dudas en la Bandeja de trabajo
- Bajo la cola de B3d, un bloque **«Dudas abiertas (todas las obras)»**:
  - agrupadas por obra y visita, con las dudas de obra aparte;
  - contadores de bloqueantes y hallazgos;
  - cada grupo enlaza a su Mesa.
- Es una sola lectura de `GET /api/dudas?resuelta=false` (usa `datos.js`), sin una segunda fuente.
- El resto de la Bandeja (ruta común, vencimientos y actividad) sigue como Fase D-a, con su aviso.

## Cómo se prueba (las reglas de B3d y B3g)
- **Backend:**
  - corre desde este worktree con una **copia** de la BD en el scratch;
  - las 5 variables `CATDIC_*` apuntan al scratch;
  - usa el **puerto 8766**: el 8765 y el 8767 son de otros procesos, no los cierres; nunca el 8000;
  - apágalo al terminar;
  - nada contra `C:\Users\Steve\CATDIC Dropbox\`.
- **Plano para probar el visor:** la copia de la BD **no tiene ninguna obra con plano vigente**. Prepara en el scratch una obra de prueba con un plano vectorial sintético:
  - mira cómo lo hacen `BACKEND/tests/test_visor.py` y `test_obras.py`, y súbelo con `POST /api/proyectos` y `POST /api/proyectos/{id}/planos`, que escriben en `CATDIC_DATOS_RAIZ` (scratch);
  - prepara elementos con recuadro confirmado (`PUT …/recuadro`), elementos solo con propuesta y elementos sin nada;
  - inserta en la copia de la BD dudas con eventos `duda` cuyas refs apunten a esos elementos, más dudas sin evento;
  - todo rotulado SINTÉTICO.
  - Si un paso no se puede aislar, simúlalo con `page.route` y anótalo.
- **Playwright** (Chromium) a 375, 768, 1024, 1280 y 1920 px, en claro y oscuro. En la Mesa en modo visita y en modo obra, en la Bandeja y en el visor «Abrir plano». Comprueba:
  - 0 peticiones fuera de `127.0.0.1:8766`;
  - 0 errores de consola;
  - sin desplazamiento horizontal;
  - el foco en el diálogo del plano;
  - el zoom y el desplazamiento con teclado y con el ratón;
  - que el recuadro rojo se ve a 375 y a 1920 (mídelo: grosor y tamaño en pantalla);
  - que Atrás funciona;
  - cada tipo de control de M1, con su PATCH, su 409, su 422 y su error por duda.
- **Casos del visor:**
  - recuadro confirmado;
  - solo propuesta;
  - sin propuesta;
  - recuadro de otro plano;
  - sin plano vigente;
  - duda con `refs: null`;
  - duda de obra T6n.
- **Peor caso:** 40 dudas en una visita, preguntas de 600 caracteres, campos nulos, 300 dudas en la Bandeja y una hoja de plano muy grande. Nada se sale ni se aplasta.
- **Suite del backend**, corrida dos veces:
  - con todo en el scratch;
  - sin `CATDIC_DROPBOX_RAIZ`: solo pueden fallar las 2 pruebas del Dropbox real.
  - Anota el resultado real.
- **Búsqueda final** de «clasico» y «clásico» en `FRONTEND/` (sin `clasico/`, `maquetas/` ni `vendor/`): 0 resultados.

## Informe
`PLANES/etapa-5-reportes/B3e.md` con:
- archivos tocados, con los del backend aparte;
- el contrato de `/api/dudas/{id}/refs`;
- el componente del visor y cómo lo usarán B3c y B3b (sus props y eventos);
- decisiones;
- los ítems de §9 «Mesa de Dudas» cubiertos (y los sustituidos por D6);
- la parte de T10b que queda cubierta;
- cómo aislaste las escrituras;
- la tabla de Playwright;
- los estados;
- el peor caso;
- la suite;
- las limitaciones;
- los hashes;
- la carpeta del scratch con las capturas.
