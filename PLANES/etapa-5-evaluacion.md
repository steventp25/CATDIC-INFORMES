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

## Evaluación 4 · 23/11/2026 · Planificador (auditoría) · Fase B · Reauditoría de B3e y B3g-2 Regenerar informe (rama `claude/etapa5-fase-b-0020e1`, `b0ba715`)
**Veredicto: APROBADO** (las dos; falta que Steven las vea)

### Bloqueantes
- Ninguno. El bloqueante de la Evaluación 3 está corregido (`f67b3ff`).
  - **Comprobación:** en una copia de `b0ba715`, desde la cola desplazada, clic en «Abrir la Mesa de Dudas» de la visita 4.
  - **Resultado:** `scrollY` pasa de 1054 a 573, `#mesa-t` queda en `top = 29` y `activeElement` es `mesa-t`.

### Observaciones (no bloquean)
- **B3g-2 hereda de `ProcesoVisita`** sin cambiar `procesador_cola.py` ni `database.py`. Copia unas 40 líneas de `lanzar_trabajo` y `ejecutar_trabajo`. Queda pendiente el parámetro `clase_proceso` cuando se fusione el PR #35 (decisión del Director).
- **Regenerar recorre `_elemento` de cada elemento.** Por eso puede abrir dudas nuevas, que es lo que se aceptó. No cambia el estado de la visita ni su `salida_json`.
- **STP con dudas:** se publica con « - CON DUDAS» y la visita sigue «Procesada» (decisión del Director).
- **Falta un caso real.** No se regeneró un PDF real en la copia de la BD de Steven, porque no tiene plano vigente. El Ejecutor sí probó v1 → v2 sobre una obra sintética, con Playwright.
- **El visor con un plano real** sigue sin verse (observación de la Evaluación 3).

### Criterios de aceptación
- [x] **Ruta aparte.** `POST /api/visitas/{id}/regenerar` solo acepta visitas «Procesada»; da 409 si la visita está en otro estado o si ya corre otro trabajo. Usa el mismo cerrojo y la misma tabla `trabajos`.
- [x] **Sin lector.** Solo genera el STP-MIVED (`_generar` con `formatos_solicitados = [STP]`) y nunca llama a `_generar_fi`. Publica con `_publicar`, sin sobrescribir.
- [x] **Sin P3.** Se salta la comprobación P3 y lo audita (`REGENERAR_SIN_P3`).
- [x] **El estado no cambia** (`_cerrar` propio), y la regeneración queda auditada (`REGENERAR_VISITA`, con `fi: "sin tocar"`).
- [x] **Pantalla:**
  - las 24 visitas se pueden lanzar, y las «Procesada» dicen «se puede regenerar su informe como versión nueva»;
  - los FI dicen «No se tocan al regenerar»;
  - la confirmación explica: versión nueva, no se borra nada, solo el STP-MIVED, los FI no se tocan y qué pasa si hay bloqueos;
  - el diálogo se cierra con Escape.
- [x] **Mesa de Dudas:** queda a la vista y con el foco al abrirla (bloqueante corregido).
- [?] **Matriz Playwright** de los Ejecutores y del Líder (48 y 130 comprobaciones): la reportan ellos; no la repetí.

### Pruebas ejecutadas
- **Suite completa** sobre una copia exacta de `b0ba715`: 977 pasan, 3 se omiten y 2 fallan. Son las 2 conocidas de Dropbox.
- **En el navegador** (BD copiada, puerto 8767): desplazamiento y foco de la Mesa medidos arriba, y el diálogo «Hacer informe» con la visita 20 «Procesada» seleccionada.

## Evaluación 5 · 23/11/2026 · Planificador (auditoría) · Fase B · B3b Obra: Resumen, Planos y ficha, Avance y Cierre (rama `claude/etapa5-fase-b-0020e1`, `905ec52`)
**Veredicto: APROBADO** (falta que Steven la vea)

### Bloqueantes
- Ninguno.

### Observaciones (no bloquean)
- **El panel se mueve al dibujar.** Al crearse el primer borrador aparece «Ir al recuadro» en la barra del visor. A 800 px de ancho, eso hace que la barra pase a dos líneas y el panel baje unos 38 px, así que un clic que iba a «Confirmar y guardar» cayó sobre la insignia. Conviene reservar el sitio del botón o dejarlo siempre visible y deshabilitado. Se puede arreglar en B4 (pulido).
- **Texto de la tarjeta del plano:** «las huellas sha256 *de abajo*». Las huellas están arriba del texto. Es un cambio de una palabra.
- **El dibujo no tiene equivalente de teclado.** Lo cubren «Proponer» y «Usar propuesta»; es lo acordado en el encargo.
- **Falta un caso real.** No se probó con un plano real, solo con la obra sintética de B3e. Queda para la Fase C.

### Criterios de aceptación
- [x] **Solo frontend.** `git diff --stat b0ba715 905ec52` toca solo `FRONTEND/` y `PLANES/`; `BACKEND/` queda igual.
- [x] **Elementos atados por `uid`.** El selector usa `uid` como valor, y el PUT y el POST van a `/elementos/{uid}/…`. En la obra sintética, dos «C1 · EJE A-1» de niveles distintos (S-1 y S-2) salen como opciones separadas.
- [x] **Guardar llama a `C.visor.olvidar(obra.id)`** (`editor-plano.js:190`). También se llama al cambiar el plano (`pestana-planos.js:101`).
- [x] **El valor de `origen` coincide con lo que acepta el backend** (`visor.py:304`): `dibujado` al dibujar y `confirmado` con «Usar propuesta», igual que el clásico.
- [x] **Arrastres pequeños y redondeo.** Un arrastre de menos de 5 pt se descarta y las coordenadas se redondean a 2 decimales (`visor-revision.js:394-396`).
- [x] **Sin doble envío.** Proponer, Guardar, Vista previa y Datos de la obra se deshabilitan mientras esperan respuesta.
- [x] **Indicadores N8, N9 y N10 sin cifras.** Muestran la fórmula, «pendiente de verificar», D15 y «Fase D-b». No hay ninguna cifra en %, ni `progress`, `meter` o `progressbar`, en Resumen ni en Cierre. Cierre aclara que no hay un «listo para cerrar» calculado.
- [x] **Datos de la obra.** Si el GET falla, se muestra el estado de error con su mensaje; ya no se abre vacío en silencio.
- [x] **En el navegador** (copia de `905ec52`, obra sintética copiada, puerto 8768):
  - Planos y ficha muestra el plano vigente (Rev. 2, los sha256 y quién lo certificó), el historial con 2 revisiones, «Dudas de la obra: 5» y el sitio reservado para B3c sin simularlo.
  - En el visor, elegí C9, dibujé con el ratón y guardé. Salió el mensaje «LOCALIZACION guardado (confirmado por steven).», el recuadro pasó a «LOC confirmado» con trazo continuo y apareció la vista previa.
  - El Atrás del navegador vuelve a `#/obra/…/planos`.
  - Resumen muestra los pendientes reales: dudas por visita, dudas de obra, el plano, el elemento con «plano cambiado: revisar» con su enlace al visor, los informes vacíos y las acciones rápidas. Actividad reciente aparece como «Fase D-a».
  - Datos de la obra trae sus 4 grupos. Se abre con Enter, el foco pasa al primer textarea, Escape lo cierra y el foco vuelve a su botón.
  - 0 errores de consola.
- [?] **Matriz de Playwright** (136 comprobaciones del Líder, más 5 anchos × 2 temas, el toque y el peor caso del Ejecutor): la reportan ellos; no la repetí.

### Pruebas ejecutadas
- **Suite completa** sobre una copia exacta de `905ec52`, sin `CATDIC_DROPBOX_RAIZ`: 977 pasan, 3 se omiten y 2 fallan. Son las 2 conocidas de Dropbox.

## Evaluación 6 · 23/11/2026 · Planificador (auditoría) · Fase B · B3c Confirmar datos del plano (rama `claude/etapa5-fase-b-0020e1`, `25fe9a5`)
**Veredicto: APROBADO** (falta que Steven la vea)

### Bloqueantes
- Ninguno.

### Observaciones (no bloquean)
- **Dos tablas de la lista se ven idénticas.** Ambas dicen «f'c por rango · pág. 1 · hoja 20 · NIVEL 2». Una de ellas es probablemente la tabla «sin recorte» que se sembró en la copia. Si dos tablas reales coinciden en tipo, página y nivel, Steven no puede distinguirlas sin abrirlas. Conviene mostrar la clave (`p1:…`) o el número de tabla. Va a B4.
- **El diálogo tiene más contenido del que cabe.** A 1024×768, `dialog.conf` mide 1064 px de alto en un espacio de 768. Con un `scrollIntoView` hecho por código, el diálogo se desplazó 96 px: la cabecera desapareció y abajo se vio la página de detrás. Con Tab de verdad no pasa: el diálogo se queda en 0 y solo se desplaza `conf-det`. Hay que buscar qué elemento se sale del diálogo. Va a B4.
- **Abierto del Líder:** una `&tabla=` desconocida vuelve a la lista sin aviso. Además, la barra fija ocupa unos 210 px a 375 px de ancho, y «Falla:» muestra las claves tal cual.
- **Falta un caso real.** No se probó con un plano real, solo con la obra sintética `obra-sintetica-b3c`. Queda para la Fase C.

### Criterios de aceptación
- [x] **Solo frontend.** `git diff --stat 905ec52 25fe9a5` toca solo `FRONTEND/` y `PLANES/`.
- [x] **Ninguna acción sin su casilla.** «Confirmar tabla completa» está deshabilitado hasta marcar «Revisé los N valores…». La certificación tiene su propia casilla, «Revisé las notas y certifico…». Las dos envían `extraido_en`.
- [x] **Regla de Oro (navegador).** La tabla de la pág. 1 tiene un valor distinto del plano: `L1 / H = 0.26` contra `tabla: 0.25`, en rojo. Al confirmarla, el servidor la rechaza y la pantalla lo dice tal cual: «No se confirma: L1 / H = '0.26' ya no coincide con la tabla ('0.25'). Vuelve a extraer.» El aviso de arriba manda el valor dudoso a la Mesa.
- [x] **Confirmación real en la copia.** La zapata de muro lindero dio «Lote …: 10 valores confirmados en 2 elementos.»
- [x] **Lista de tablas.** Muestra verde/rojo con icono y texto, «Falla: …» y «No vigente: …». El detalle trae sus 9 comprobaciones, el recorte del plano y «Abrir plano».
- [x] **Resaltado con el teclado.** Las filas de valores son enfocables (`tr` con `tabindex=0`) y al enfocarlas aparece la caja `conf-caja` sobre el recorte.
- [x] **Navegación.**
  - «Mesa de Dudas de la obra (9 abiertas)» abre `#/obra/…/resumen?dudas=obra`, y Atrás vuelve a `…?confirmar=1&tabla=1` con el diálogo abierto.
  - Escape vuelve a «Planos y ficha».
  - Recargar con `&tabla=` mantiene la tabla elegida.
- [x] **Consola.** Solo aparece el 409 esperado, como «Failed to load resource».
- [?] **Matriz Playwright** (56 del Líder; anchos, pasos en móvil y peor caso de 60 tablas × 400 filas del Ejecutor): la reportan ellos; no la repetí.

### Pruebas ejecutadas
- **Suite completa** sobre una copia exacta de `25fe9a5`: 977 pasan, 3 se omiten y 2 fallan. Son las 2 conocidas de Dropbox.
- **En el navegador:** copia de `25fe9a5` con la BD sintética del Ejecutor copiada a mi scratch, en el puerto 8768.

## Evaluación 7 · 23/11/2026 · Planificador (auditoría) · Fase B · B3f Órdenes de trabajo (rama `claude/etapa5-fase-b-0020e1`, `d7cec65`)
**Veredicto: APROBADO** (falta que Steven la vea)

### Bloqueantes
- Ninguno.

### Observaciones (no bloquean; van a B4/B5)
- **La pestaña inicial puede salir vacía.** En modo pestañas (1024 px) se abre «Pendiente» aunque esté vacía y la única orden esté en «En proceso». Conviene abrir la primera pestaña que tenga órdenes cuando no hay `?estado=`.
- **El enlace de Inicio no dice adónde lleva.** En «Órdenes abiertas», el enlace solo contiene la cifra («1»), sin `aria-label`. Un lector de pantalla oye «1, enlace». Debe decir, por ejemplo, «1 orden abierta: ver órdenes de trabajo».
- **Abiertos del Líder:**
  - a 1280 px, las columnas 5 y 6 quedan tras un desplazamiento dentro del tablero;
  - no hay virtualización para 300 órdenes.

### Criterios de aceptación
- [x] **Solo frontend.** `git diff --stat 94dfcaf d7cec65 -- BACKEND` sale vacío.
- [x] **Solo se lee `/api/dashboard`.**
  - No se crea ni se mueve nada: «Crear orden» y «Cambiar estado» están deshabilitados, con el motivo y «Fase D».
  - Hay 0 elementos `draggable`.
  - Un estado desconocido no se pierde: va a «Otro estado».
- [x] **Inicio sin cifras inventadas.** «Bloqueadas» y «Vencen en ≤ 7 días» siguen como «pendiente de verificar · Fase D-a».
- [x] **En el navegador** (copia de `d7cec65`, BD sintética, puerto 8768, a 1024 px):
  - `#/ordenes` marca «Bandeja de trabajo» como activa;
  - las 6 pestañas muestran su contador;
  - «En proceso» enseña OT-LEV-001 con su obra, formato, entregable y prioridad; la fecha comprometida dice «pendiente de verificar»;
  - el estado queda en la dirección (`?estado=En%20proceso`) y Atrás funciona;
  - la Bandeja muestra «Órdenes de trabajo: 1 abierta» y lleva a `#/ordenes`;
  - Inicio enlaza a `#/ordenes`;
  - una obra sin órdenes dice «Esta obra no tiene órdenes de trabajo.»;
  - no hay desbordamiento horizontal de la página.
- [x] **Consola sin errores de la página.** Hubo un solo error, que vino de un script inyectado por la herramienta del navegador y no de la app.
- [?] **Matriz Playwright del Líder** (375, 1280 y 1920 px, claro y oscuro, flechas y foco de «depende de») y **peor caso** (300 órdenes): los reportan ellos; no los repetí.

### Pruebas ejecutadas
- **Suite completa** sobre una copia exacta de `d7cec65`: 977 pasan, 3 se omiten y 2 fallan. Son las 2 conocidas de Dropbox.

### Estado de B3
Con B3f, quedan aprobadas **B3a, B3b, B3c, B3d, B3e, B3f, B3g y B3g-2**. B3h (retirar el tablero clásico) sigue **sin autorizar**.
