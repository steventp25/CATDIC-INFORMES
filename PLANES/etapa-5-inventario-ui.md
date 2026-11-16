# Etapa 5 · B0 — Inventario funcional de `FRONTEND/index.html`

Lista de paridad del tablero actual (1.461 líneas, Vue 3 + Tailwind + Font Awesome por CDN, tema oscuro). El tablero nuevo (Fase B) se prueba contra este documento fila por fila. Todas las referencias `index.html:NNN` son números de línea del archivo actual.

Convenciones: `API = http://localhost:8000` (`index.html:714`). `leerError(res)` (`:810`) devuelve `detail` de la respuesta (texto o JSON) o, si no hay JSON, `El servidor respondió <status> <statusText>`. «Texto literal» va entre comillas. Los modales y paneles se muestran con `v-if` sobre una variable `ref`.

Resumen de la página: 1 cabecera, 1 `<main>` con 6 bloques de aviso/resultado, 5 tarjetas, 3 tablas/paneles de datos, y **6 modales/paneles superpuestos** (Mesa de Dudas, Obra, Visita, Visor, Datos de la obra, Confirmar datos del plano). No hay más.

---

## 1. Pantallas y zonas de la página principal

| # | Zona | Qué muestra | Origen del dato | Línea |
|---|---|---|---|---|
| Z1 | Cabecera | Logo `CATDIC`, título «Control Taller», insignia «Web Local v2.0», 3 botones (Nueva obra, Sincronizar, Procesar Cola) | texto fijo; estado de botones de `cargando` y `trabajoCola.estado` | 17-36 |
| Z2 | Aviso de obra creada (verde) | `avisoObra` con icono de check y botón cerrar | texto armado en `enviarObra` con `plano.revision`, `plano.elementos_marcados`, `plano.aviso_paginas` de `POST /api/proyectos/{id}/planos` | 40-43 |
| Z3 | Trabajo de la cola | Mensaje, id del trabajo, estado, resumen y error; borde verde (terminado), amarillo (corriendo), rojo (otro) | `trabajoCola` ← `POST /api/visitas/procesar-cola` (`trabajo.id`, `mensaje`) y `GET /api/trabajos/{id}` (`estado`, `resumen.visitas[].estado`, `resumen.pdf[]`, `error`) | 46-53 |
| Z4 | Resultado de subir visita / conectar Dropbox | Título, resumen, lista de visitas nuevas (`#número`, carpeta, estado coloreado, lector, botón «Mesa de Dudas: N»), mensaje «No hay visitas nuevas.», `<details>` «N avisos del sincronizador» | `resultadoVisitas` ← respuesta de `POST /api/proyectos/{id}/visitas` (`visita.ruta_carpeta`, `visita.archivos`, `dudas`, `lector`) o `POST /api/proyectos/{id}/dropbox` (`carpeta_visitas`, `sync.*`, `visitas_nuevas[]`) | 56-74 |
| Z5 | Error de sincronización (rojo) | Título «No se pudo sincronizar con Dropbox» + `errorSync` + botón cerrar | excepción de `sincronizarDropbox` | 77-86 |
| Z6 | Error del tablero (rojo) | Título «No se pudo cargar el tablero» + `errorDashboard` (sin botón cerrar) | excepción de `cargarDatos` | 87-93 |
| Z7 | Error de dudas (rojo) | Título «No se pudo leer la Mesa de Dudas» + `errorDudas` (sin botón cerrar) | excepción de `cargarDudasAbiertas` | 95-101 |
| Z8 | Resultado de la sincronización | Hora `DD/MM/AAAA HH:MM`; por proyecto: nombre, insignia de layout, contadores (Nuevas, Actualizadas, Sin cambios, Con dudas, Procesadas, Planos sellados, Dudas nuevas), avisos, carpetas desaparecidas, omitidas, dudas creadas | `resumenSync.proyectos[]` ← `POST /api/dropbox/sync`: `id, nombre, layout, visitas_nuevas, actualizadas, sin_cambios, con_dudas, procesadas, planos_sellados[], dudas_creadas[{visita_id,campo_afectado,descripcion_pregunta}], avisos[], desaparecidas[{id,nombre_carpeta,estado}], omitidas[{nombre_carpeta,motivo}]` | 104-143 |
| Z9 | Tarjeta «Proyectos Activos» | número | `stats.proyectos_activos` (`/api/dashboard`) | 147-150 |
| Z10 | Tarjeta «Órdenes Abiertas» | número | `stats.ordenes_abiertas` | 151-154 |
| Z11 | Tarjeta «Bloqueadas» | número | `stats.bloqueadas` (el backend devuelve siempre 0) | 155-158 |
| Z12 | Tarjeta «Vencen en ≤ 7 Días» | número | `stats.vencen_7_dias` (backend: siempre 0) | 159-162 |
| Z13 | Tarjeta «Visitas en Cola» (número amarillo) | número | `stats.visitas_en_cola` | 163-166 |
| Z14 | Tabla «Matriz General de Proyectos» | Encabezado «Matriz General de Proyectos» + «Sincronizado con base de datos local SQLite»; columnas Proyecto, Tipo / Formato, Cliente, Supervisor, Estado Informe, Plano vigente, Próxima Acción | `proyectos[]` (`nombre, tipo, formato_defecto, cliente, supervisor, estado_informe, observaciones, carpeta_dropbox, id`) y `planos_vigentes[id]` | 170-227 |
| Z14a | …celda Plano vigente | «Rev. N · etiqueta», fecha del plano o «sin fecha de plano», «certificado por X», `title` con sha256 vectorial y sellado; o insignia «sin plano»; 3 filas de botones | `planosVigentes[p.id]`: `revision, etiqueta_revision, fecha_plano, certificado_por, vectorial_sha256, sellado_sha256` | 201-220 |
| Z15 | Tabla «Cola de Visitas a Obra» | Contador «N visitas · M con dudas»; columnas Proyecto, N.º, Carpeta de visita, Fecha, Clase, Estado; fila resaltada naranja si «Con dudas» o con bloqueantes; clic abre la Mesa si hay dudas | `visitas[]` (`proyecto_id, numero, nombre_carpeta, ruta_carpeta, fecha_visita, clase, clase_detalle_json, estado, campos_pendientes_json, id`), `dudasAbiertasLista` | 230-288 |
| Z16 | Kanban «Órdenes de Trabajo Activas (OT)» | 6 columnas fijas (Pendiente, Asignada, En proceso, Bloqueada, En revisión, Entregada) con contador y tarjetas `doc_id`, `seccion`, `nota` | `ordenes[]` (`estado, doc_id, seccion, nota`) | 291-308 |

Detalle de la tabla de visitas (Z15), columna por columna:

| Columna | Muestra | Línea |
|---|---|---|
| Proyecto | `nombreProyecto(v.proyecto_id)` (si no se encuentra, el id) | 252 |
| N.º | `v.numero` en negrita, o insignia «pendiente de verificar» si vacío/nulo/«pendiente de verificar» | 253-256 |
| Carpeta de visita | `v.nombre_carpeta`, tooltip `v.ruta_carpeta` | 257 |
| Fecha | `formatearFecha(v.fecha_visita)` o insignia «pendiente de verificar» | 258-261 |
| Clase | `v.clase` o insignia «pendiente de verificar»; si `clase === 'Mixta'`, lista `elementos: clase` desde `clase_detalle_json` o «detalle pendiente de verificar» | 262-269 |
| Estado | insignia coloreada (con icono de pregunta si «Con dudas»); línea `<estado> con N duda bloqueante abierta / dudas bloqueantes abiertas`; línea `N duda abierta / dudas abiertas · clic para responder`; línea `Pendiente: <campos>` desde `campos_pendientes_json` | 270-283 |

Orden de las visitas: `visitasOrdenadas` (`:781`): por nombre de proyecto (`localeCompare 'es'`), luego número numérico ascendente (los que no tienen número válido van al final), luego `nombre_carpeta`.

Botones de la celda «Plano vigente» (fila de cada proyecto): ver acciones A4-A11 en la sección 3.

---

## 2. Modales y paneles

Los 6 modales encontrados. No hay otros (`grep -c "v-if=\"modal\|v-if=\"visor\|v-if=\"confirmar\|v-if=\"mesa"` → 6 bloques raíz: `mesa`, `modalObra`, `modalVisita`, `visor`, `modalDatos`, `confirmar`).

### M1. Mesa de Dudas (panel lateral derecho) — `index.html:312-411`
- **Se abre:** (a) clic en una fila de visita con dudas abiertas (`:251` → `abrirMesa(v)`); (b) botón «Mesa de Dudas: N» de la lista de resultado (`:69` → `abrirMesaDeVisita`); (c) botón «Dudas de la obra: N» de la matriz (`:214` → `abrirMesaObra(p)`); (d) botones «Mesa de Dudas de la obra» (`:609`) e «Ir a la Mesa de Dudas» (`:700`) desde Confirmar datos del plano; (e) automáticamente tras sincronizar o tras subir/conectar visita si hay dudas nuevas y la Mesa no estaba abierta (`abrirMesaSiHayDudasNuevas :851`, `enviarVisita :1429`).
- **Se cierra:** clic en el fondo oscuro (`@click.self="cerrarMesa"` `:312`) o botón X (`:323`).
- **Cabecera:** título «Mesa de Dudas». Modo visita: «Visita <numero> · <nombre_carpeta>» + insignia de estado. Modo obra: «Obra <nombre> · dudas sin visita (plano y datos de la obra)» (`data-mesa-obra`).
- **Cuerpo:** error `mesa.error`; conflicto `mesa.conflicto + " Se recargaron las dudas."`; «Cargando dudas…»; mensaje vacío; aviso si la visita está «Procesada» pero tiene bloqueantes («Esta visita figura como Procesada pero tiene dudas bloqueantes abiertas.»); lista de dudas (tarjetas); aviso de éxito `mesa.aviso`.
- **Tarjeta de duda** (`:338`): insignia «Bloqueante» (`DUDA_BLOQUEANTE`) o «Hallazgo interno»; si es de etiqueta de foto: «Etiqueta en la visita: <id_elemento o "(sin etiqueta)"> · <Fotos p. X–Y>»; si no: «Campo: <etiquetaCampo>» y «Elemento: <id_elemento>»; insignia «Resuelta»; `pregunta`; «Creada: DD/MM/AAAA HH:MM» (+ « · Resuelta: …»); si resuelta, «Respuesta: <respuesta o —>».
- **Control según tipo de duda abierta** (cadena de `v-if`, `:356-404`), en este orden de prioridad:

| Condición | Control | Botón | Línea |
|---|---|---|---|
| `categoria === 'HALLAZGO_INTERNO'` | ninguno | «Marcar revisado» → envía `revisado` | 356-358 |
| `d.campo_confirmable` | texto «Campo del plano: … propuesto: …», input `Valor leído en el plano` (`data-valor-campo`), nota de auditoría | «Confirmar valor» (`data-confirmar-campo`), deshabilitado si vacío o guardando | 359-364 |
| `d.id_elemento` (resto) | textarea `Respuesta (texto libre)` (2 filas); avisos `data-aviso-plano` (si `esDudaPlano`: campo empieza por `T6n:`/`T7n:`) y `data-aviso-etiqueta` (si de visita) | «Guardar respuesta» | 365-370 |
| `campo_afectado === 'fecha_visita'` | input `DD/MM/AAAA` (max 10, numérico) | «Guardar fecha» | 371-374 |
| `campo_afectado === 'clase'` | select «Elige la clase…» con Parcial / Completivo | «Guardar clase» | 375-382 |
| `campo_afectado === 'estado'` | radios «Corresponde» / «No corresponde»; si «corresponde»: select de STP candidatos (`candidatosStp`, opciones `g.join(' | ')`) o aviso «La visita no tiene STP candidatos guardados: no se puede citar ninguno.» | «Guardar estado» | 383-398 |
| `campo_afectado === 'archivos_json'` | solo texto «Se cierra sola al sincronizar cuando el PDF esté en la carpeta de la visita. No se responde con texto.» | ninguno | 399-401 |
| otro | «Esta duda (<campo>) no se responde desde la Mesa de Dudas.» | ninguno | 402-404 |

  Error por duda: `d._error` (`data-error-duda`) `:405`. Orden de la lista: abiertas primero, luego por id ascendente (`:947`).

### M2. Nueva obra / Cambiar plano / Subir planos — `index.html:413-471` (`data-modal-obra`)
- **Se abre:** «Nueva obra» (`:23`, `abrirNuevaObra`, modo `nueva`, título «Nueva obra»); «Cambiar plano» o «Subir planos» (`:208`, `abrirCambiarPlano`, modo `cambiar`; el título es «Cambiar plano» si ya hay plano vigente, si no «Subir planos»).
- **Se cierra:** X (`:417`) o «Cancelar» (`:464`) → `cerrarModalObra`. Se cierra solo al éxito. No se cierra al hacer clic en el fondo.
- **Campos (solo modo `nueva`, `:420-444`):** Nombre de la obra * (`data-campo="nombre"`), Tipo (select Supervisión / Levantamiento), Cliente, No. de solicitud, No. de licencia, Residente de obra (nombre y colegiatura), Supervisor, Dirección de la obra, Provincia, Sector, Inicio de obra (DD/MM/AAAA) con placeholder `01/03/2026`. Todos se deshabilitan si ya se creó la obra (`proyecto_id` fijo, reintento de solo la subida).
- **Modo `cambiar`:** texto «Obra: <nombre>. El plano nuevo queda vigente; el anterior pasa al histórico y los elementos ya extraídos de él se marcan «plano cambiado: revisar».» (`:445-446`).
- **Campos comunes (`:448-457`):** archivo Plano VECTORIAL (PDF) * (`data-archivo="vectorial"`), Plano SELLADO (PDF) * (`data-archivo="sellado"`), Revisión (texto libre), Fecha del plano (DD/MM/AAAA) placeholder `10/03/2026`.
- **Casilla** `data-certifico` (`:459`): «Certifico que el vectorial corresponde a la versión sellada (queda registrado con tu usuario y la fecha)».
- **Error:** `modalObra.error` (`data-error-obra`) `:462`.
- **Botones:** «Cancelar»; enviar (`data-enviar-obra`): «Crear obra y subir planos» (modo nueva), «Subir plano nuevo» (modo cambiar), «Subiendo…» mientras envía.

### M3. Subir visita / Conectar con Dropbox — `index.html:474-516` (`data-modal-visita`)
- **Se abre:** «Subir visita» (`:217`, `abrirSubirVisita`) o «Conectar con Dropbox» / «Dropbox conectado» (`:218`, `abrirConectarDropbox`); ambos solo para proyectos de tipo `Supervisión`.
- **Se cierra:** X (`:478`) o «Cancelar» (`:509`); al éxito.
- **Título:** icono + «Subir visita» o «Conectar con Dropbox» + « · <nombre>».
- **Modo subir (`:481-501`):** texto explicativo («La visita se guarda en la carpeta local de la obra (nunca en Dropbox)…»); PDF de la visita * (`data-visita-pdf`); Fotos sueltas, opcional JPG/PNG, múltiple (`data-visita-fotos`); Número de visita * (`data-visita-campo="numero"`, placeholder `17`); Fecha (DD/MM/AAAA) (`fecha`, placeholder `28/09/2026`); Elementos * (`elementos`, placeholder `VERTICALES`); Nivel * (`nivel`, placeholder `S-4`); Clase (`clase`, select: «No la indico (se lee del PDF o queda pendiente)», Parcial, Completivo) con nota «Mixta no se acepta: si la visita tiene partes Parcial y Completivo, súbela como dos visitas.».
- **Modo dropbox (`:502-506`):** texto explicativo («Indica la carpeta LEVANTAMIENTO\VISITA A OBRA…»); Carpeta de visitas * (`data-visita-carpeta`, fuente mono). Valor inicial: `carpeta_dropbox + "\LEVANTAMIENTO\VISITA A OBRA"` si el proyecto ya tiene carpeta, si no vacío.
- **Error:** `modalVisita.error` (`data-error-visita`) `:507`.
- **Botón enviar** (`data-enviar-visita`): subir → «Subir visita» / «Subiendo y leyendo la visita…»; dropbox → «Conectar y sincronizar» / «Sincronizando y leyendo las visitas…».

### M4. Visor del vectorial y recuadros — `index.html:519-577` (`data-visor`, pantalla completa, fondo negro 80 %)
- **Se abre:** botón «Ver plano» (`:209`, `abrirVisor`), solo si hay plano vigente. **Se cierra:** X (`:532`, `visor = null`). Sin tecla de cierre.
- **Barra superior:** «Visor · <nombre> (plano vectorial vigente)»; select de hoja (`data-visor-hoja`) con opciones `p<pagina> · hoja <hoja> · <primer título cortado a 40>`; «Zoom», botón `−` (`data-zoom-menos`, ×0.8), porcentaje (`data-zoom`), botón `+` (`data-zoom-mas`, ×1.25), botón «Ajustar» (ancho del lienzo); límite de zoom 0.1-8.
- **Lienzo** (`data-lienzo` `:535`, `data-hoja-lienzo` `:537`, `data-hoja-img` `:538`): imagen PNG de la hoja con cajas superpuestas `data-caja` (verde sólido «LOC/DET confirmado», amarillo discontinuo «LOC/DET propuesto (pendiente)», azul «LOC/DET sin guardar»). Dibujo del recuadro arrastrando (mousedown/mousemove/mouseup/mouseleave); un arrastre menor de 5 pt se descarta. Coordenadas en puntos PDF.
- **Panel derecho (ancho 96):** select Elemento (`data-visor-elemento`, opciones `<id_elemento> · <ejes> · <nivel_rango>`, primera «— elige un elemento —»); avisos «Esta obra aún no tiene elementos de diseño: los recuadros se guardan por elemento.» y `elementoVisor.revisar_motivo`; botón «Proponer recuadros» (`data-proponer`); por cada tipo (`LOCALIZACION`, `DETALLE`; `data-recuadro`): radio de tipo activo, insignia de estado, texto de detalle (`data-detalle-recuadro`), botones «Usar propuesta» (`data-usar`), «Confirmar y guardar» (`data-guardar-recuadro`), «Vista previa» (`data-previa`), imagen de vista previa (`data-previa-img`); texto de ayuda «Dibuja un recuadro arrastrando sobre la hoja; se aplica al tipo marcado. Las coordenadas se guardan en puntos del PDF vectorial.»; error (`data-visor-error`) y mensaje (`data-visor-mensaje`).

### M5. Datos de la obra — `index.html:580-600` (`data-modal-datos`)
- **Se abre:** botón «Datos de la obra» (`:210`, `abrirDatosObra`). **Se cierra:** solo X (`:584`).
- **Cuerpo:** texto de ayuda («El plano no trae estos datos: los escribes tú (una línea por dato, «clave = valor»)…»). 4 grupos (`gruposDatos :1066`), cada uno con `textarea` de 4 filas (`data-datos="<tipo>"`, placeholder = ejemplo), botón «Guardar» (`data-guardar="<tipo>"`) y mensaje por grupo (`data-mensaje="<tipo>"`, verde o rojo):

| tipo | Título | Ayuda | Casilla / texto |
|---|---|---|---|
| `equivalencia_nivel` | Equivalencias E-n ↔ nivel | (el plano rotula entrepisos E-1…E-n) | casilla «Ya escribí todos los de esta lista» |
| `losa_tipo` | Tipo de cada losa (A, B o C) | (la tabla de acero en losa no dice a qué L# corresponde) | casilla «Ya escribí todos los de esta lista» |
| `hoja_par` | Emparejamiento de hojas vectorial → sellado | (número de hoja del vectorial = número de hoja del sellado, o «sin pareja») | casilla «Ya escribí todos los de esta lista» |
| `techo` | Nivel de las plantas repetidas | (página del vectorial = nivel; solo para plantas con el mismo título en varias hojas…) | texto «Las dudas de esas plantas se cierran al volver a extraer.» (sin casilla) |

### M6. Confirmar datos del plano — `index.html:604-708` (`data-confirmar`, pantalla completa, `z-30`; la Mesa es `z-40` y queda por encima)
- **Se abre:** botón «Confirmar datos del plano» (`:213`, `abrirConfirmar`), solo con plano vigente. **Se cierra:** X (`:611`, `cerrarConfirmar`, libera el recorte).
- **Barra superior:** «Confirmar datos del plano · <nombre>»; botón «Extraer del plano vigente» (`data-extraer`; «Extrayendo…»); botón «Mesa de Dudas de la obra»; error `data-confirmar-error`; mensaje `data-confirmar-mensaje`.
- **Columna izquierda (lista de tablas, ancho 80):** «Cargando tablas…» / «Aún no hay tablas extraídas del plano vigente. Pulsa «Extraer del plano vigente».»; cada tabla es un botón (`data-tabla="<clave>"`) con nombre (`NOMBRES_TABLA`: `acero_en_losa` «Acero en losa», `zapata_muro_lindero` «Zapata de muro lindero», `fc_por_rango` «f'c por rango», `losa_aligerada` «Losa aligerada»; otro nombre se muestra tal cual), insignia `verde`/`rojo`, «pág. X · hoja Y · nivel_rango», «Falla: …» si rojo, «No vigente: <motivo>» (opacidad 50 %) si no vigente.
- **Columna derecha:** «Elige una tabla para ver sus filas propuestas junto al recorte del plano.» / «Cargando la tabla…»; con tabla elegida: título, clave, página, hoja, nivel, «extraída DD/MM/AAAA HH:MM», insignia resultado (`data-resultado`); lista de comprobaciones (`data-comprobaciones`; check verde o X roja, con detalle y, si certificada, `data-certificada` «(certificada por X el … para el vectorial <sha12>…)»); bloque de certificación de notas de modificación (`data-certificar`; casilla `data-certifico`; botón `data-certificar-notas` «Certificar que vale para el plano vigente» / «Certificando…»); recorte del plano (`data-recorte`, `data-recorte-img`, caja roja de celda resaltada `data-resaltado`) o texto «Sin recorte: la tabla no tiene celdas con posición.»; tabla de valores propuestos (`data-campos`, filas `data-campo="<id>|<campo>"`: Elemento, Campo (fila N), Valor (rojo con «tabla: …» si difiere), Estado `confirmado`/`pendiente`); «Ningún elemento toma valores de esta tabla.»; sección de confirmación por lote: casilla `data-revisado` (con `data-identidad` si hay identidad pendiente) y botón `data-confirmar-tabla` «Confirmar tabla completa» / «Confirmando…»; o bloque rojo `data-tabla-roja` con botón `data-ir-mesa` «Ir a la Mesa de Dudas»; o texto `data-no-confirmable` «No se puede confirmar: …».
- Al pasar el ratón sobre una fila de valores se resalta su celda en el recorte (`@mouseenter/@mouseleave` `:676`).

---

## 3. Acciones (botón/enlace/evento → función → API → respuesta → mensajes)

`ERR-RED` = `El backend no responde en http://localhost:8000. Verifica que el servidor FastAPI esté corriendo.` (algunas variantes sin la segunda frase, indicadas). Donde dice «error» sin más, el texto es el de `leerError` (ver arriba).

### 3.1 Cabecera y avisos

| ID | Elemento (línea) | Función | Llamada | Qué hace con la respuesta | Mensajes |
|---|---|---|---|---|---|
| A1 | «Nueva obra» `data-nueva-obra` (23) | `abrirNuevaObra` | ninguna | abre M2 modo nueva | — |
| A2 | «Sincronizar desde Dropbox» (26) | `sincronizarDropbox` (859) | `POST /api/dropbox/sync` sin cuerpo | exige `status==='ok'` y `proyectos` array; guarda `resumenSync` con hora local; `cargarDatos()`; `abrirMesaSiHayDudasNuevas` | botón: «Sincronizando…» (con icono girando) / «Sincronizar desde Dropbox»; error de red: `El backend no responde en <API>. Verifica que el servidor FastAPI esté corriendo.`; inesperada: `Respuesta inesperada del servidor de sincronización.`; el error va a Z5 y borra Z8 |
| A3 | «Procesar Cola Visitas» `data-procesar-cola` (31) | `procesarCola` (917) | `POST /api/visitas/procesar-cola` sin cuerpo (backend responde 202) | si no hay `trabajo`: `trabajoCola = {estado:'terminado', mensaje: data.mensaje}`; si hay: estado `corriendo` y `seguirTrabajo(id)` | botón: «Procesando…» (icono latiendo, deshabilitado) / «Procesar Cola Visitas»; fallo: `No se pudo lanzar el procesamiento.` + error; red: texto `ERR-RED` |
| A4 | cerrar Z2 (42) | inline | — | `avisoObra = ''` | — |
| A5 | cerrar Z3 (52) | inline | — | `trabajoCola = null`; solo visible si estado ≠ `corriendo` | — |
| A6 | cerrar Z4 (59) | inline | — | `resultadoVisitas = null` | — |
| A7 | cerrar Z5 (85) | inline | — | `errorSync = ''` | — |
| A8 | cerrar Z8 (109) | inline | — | `resumenSync = null` | — |
| A9 | `seguirTrabajo` (903), polling de A3 | función | `GET /api/trabajos/{id}` cada 2000 ms mientras `estado==='corriendo'` | al terminar: `trabajoCola = {id, estado, mensaje, resumen, error}`; recarga `cargarDatos()` y `cargarDudasAbiertas()` | `Procesamiento terminado.` / `El procesamiento falló.`; resumen `N visitas · P procesadas · X con dudas o con error · K PDF`; si falla la lectura: `No se pudo leer el estado del trabajo.` (estado `desconocido`) |
| A10 | `onMounted` (1438) | `cargarDatos` | `GET /api/dudas?resuelta=false` y `GET /api/dashboard` (en ese orden) | rellena `stats, proyectos, visitas, ordenes, planosVigentes, dudasAbiertasLista` | error del tablero: `No hay conexión con el backend en <API> (<detalle>). Verifica que el servidor FastAPI esté corriendo.`; error de dudas: `No se pudieron leer las dudas (<detalle>). Verifica que el servidor FastAPI esté corriendo.` |

### 3.2 Matriz de proyectos (por cada fila)

| ID | Botón (línea) | Condición de visibilidad | Función | Llamada | Resultado |
|---|---|---|---|---|---|
| A11 | «Cambiar plano» / «Subir planos» `data-cambiar-plano` (208) | siempre | `abrirCambiarPlano` | ninguna | abre M2 modo cambiar |
| A12 | «Ver plano» `data-ver-plano` (209) | hay plano vigente | `abrirVisor` | ver A34 | abre M4 |
| A13 | «Datos de la obra» `data-datos-obra` (210) | siempre | `abrirDatosObra` | `GET /api/proyectos/{id}/datos-obra` | abre M5; rellena textareas con `datos[tipo][].clave = valor`; si falla se abre vacío, sin mensaje |
| A14 | «Confirmar datos del plano» `data-confirmar-plano` (213) | hay plano vigente | `abrirConfirmar` | `GET /api/proyectos/{id}/tablas-extraidas` | abre M6 |
| A15 | «Dudas de la obra: N» `data-dudas-obra` (214) | `dudasObra(p.id) > 0` (dudas abiertas con ese `proyecto_id` y sin `visita_id`) | `abrirMesaObra` | `GET /api/dudas?sin_visita=true&proyecto_id={id}` | abre M1 modo obra |
| A16 | «Subir visita» `data-subir-visita` (217) | `p.tipo === 'Supervisión'` | `abrirSubirVisita` | ninguna | abre M3 modo subir |
| A17 | «Dropbox conectado» / «Conectar con Dropbox» `data-conectar-dropbox` (218) | `p.tipo === 'Supervisión'` | `abrirConectarDropbox` | ninguna | abre M3 modo dropbox |

### 3.3 Cola de visitas y resultado de visitas

| ID | Elemento (línea) | Función | Llamada | Resultado |
|---|---|---|---|---|
| A18 | clic en fila de visita (251), solo si `dudasAbiertas(v.id) > 0`; tooltip «Abrir la Mesa de Dudas de esta visita» | `abrirMesa(v)` (956) | `GET /api/dudas?visita_id={id}` | abre M1 modo visita |
| A19 | botón «Mesa de Dudas: N» `data-abrir-mesa-visita` (69), solo si `v.dudas` | `abrirMesaDeVisita(id)` | igual que A18 | busca la visita en `visitas`; si no está, no hace nada |

### 3.4 Mesa de Dudas (M1)

| ID | Elemento (línea) | Función | Llamada | Cuerpo | Resultado y mensajes |
|---|---|---|---|---|---|
| A20 | X / fondo (323, 312) | `cerrarMesa` | — | — | `mesa = null` |
| A21 | «Marcar revisado» (357) | `responder(d,'revisado')` → `enviarRespuesta` (962) | `PATCH /api/dudas/{id}` | `{"respuesta":"revisado"}` | ver A26 |
| A22 | «Confirmar valor» (362) | `responder(d, d._entrada)` | `PATCH /api/dudas/{id}` | `{"respuesta":"<texto recortado>"}` | ver A26 |
| A23 | «Guardar respuesta» (367) | `responder` | `PATCH /api/dudas/{id}` | `{"respuesta":"<texto>"}` | ver A26 |
| A24 | «Guardar fecha» (373) / «Guardar clase» (381) | `responder` | `PATCH /api/dudas/{id}` | `{"respuesta":"<DD/MM/AAAA | Parcial | Completivo>"}` | ver A26 |
| A25 | «Guardar estado» (397) | `responderEstado` (1005) | `PATCH /api/dudas/{id}` | `{"respuesta":"corresponde"|"no corresponde"}`; con `corresponde` y más de un grupo STP candidato añade `"stp": <grupo elegido>`; con uno solo lo toma el backend | ver A26 |
| A26 | respuesta de `enviarRespuesta` | — | — | — | éxito: `cargarDatos()`, refresca la visita de la Mesa, `cargarDudasVisita()`, aviso verde `Duda <duda_id> respondida.` + ` Valor aplicado: <valor>.` (si `valor_aplicado`; fecha en DD/MM/AAAA; si es objeto usa `.estado`) + ` Estado de la visita: <estado_visita>.`. Error 409: aviso rojo `mesa.conflicto` (texto del servidor) + « Se recargaron las dudas.» y recarga. Otros errores (404/422/red) quedan en `d._error` bajo la duda. Botones con `d._guardando` deshabilitan el envío doble |
| A27 | radios Corresponde / No corresponde (385-386) | v-model | — | — | muestra u oculta el select de STP |

### 3.5 Obra y planos (M2) y datos de la obra (M5)

| ID | Elemento (línea) | Función | Llamada | Cuerpo | Resultado y mensajes |
|---|---|---|---|---|---|
| A28 | enviar `data-enviar-obra` (465) | `enviarObra` (1026) | 1) solo si modo nueva y sin `proyecto_id`: `POST /api/proyectos` JSON con los campos no vacíos de `datos`; 2) `POST /api/proyectos/{id}/planos` multipart (`vectorial`, `sellado`, `certifico='true'`, `etiqueta_revision`, `fecha_plano`) | — | validaciones locales (en `modalObra.error`): `Escribe el nombre de la obra.` / `Elige los dos archivos: el vectorial y el sellado.` / `Marca la casilla: certifico que el vectorial corresponde a la versión sellada.`; si la subida falla tras crear: `La obra se creó, pero los planos no se subieron: <error>` (el modal sigue abierto y reintenta solo la subida); red: `El backend no responde en <API>.`; éxito: `cargarDatos()`, cierra el modal, aviso Z2: `<nombre|id>: plano rev. <revision> vigente` + ` · N elementos marcados «plano cambiado: revisar»` + ` · <aviso_paginas>` + `. Quedan dudas por responder: equivalencias E-n ↔ nivel, tipos de losa y emparejamiento de hojas (botón «Datos de la obra»).` |
| A29 | «Guardar» por grupo `data-guardar` (594) | `guardarDatos(tipo)` (1082) | `PUT /api/proyectos/{id}/datos-obra` | `{"tipo":"...","items":[{"clave","valor"}...],"completo":bool}`; cada línea no vacía se parte en el primer `=` o `:`; sin separador → `valor:""` | verde: `Guardados N datos como confirmados` + ` · duda cerrada.` o `.`; rojo: texto del error, en `data-mensaje` del grupo |
| A30 | cerrar M2 / M3 / M5 (417, 464, 478, 509, 584) | inline | — | — | cierra sin confirmar ni guardar borradores |

### 3.6 Visita (M3)

| ID | Elemento (línea) | Función | Llamada | Resultado y mensajes |
|---|---|---|---|---|
| A31 | enviar `data-enviar-visita` (510), modo subir | `enviarVisita` (1386) | `POST /api/proyectos/{id}/visitas` multipart: `pdf`, `fotos` (varias), `numero`, `elementos`, `nivel`, `fecha`, `clase` (recortados) | validaciones: `Elige el PDF de la visita.` / `El número de visita debe ser un entero (p. ej. 17).` / `Escribe los elementos y el nivel de la visita.` / `La fecha debe ser DD/MM/AAAA (p. ej. 28/09/2026).`; éxito: Z4 con título `<nombre>: visita subida`, resumen `Guardada en <ruta_carpeta> (<n> archivo(s) con sha256).`, una fila (`filaResultado`); cierra el modal; `cargarDatos()`; abre la Mesa de la primera visita con dudas si la Mesa no estaba abierta |
| A32 | enviar `data-enviar-visita`, modo dropbox | `enviarVisita` | `POST /api/proyectos/{id}/dropbox` JSON `{"carpeta_visitas":"<ruta>"}` | validación: `Escribe la ruta de la carpeta LEVANTAMIENTO\VISITA A OBRA.`; éxito: Z4 con título `<nombre>: conectada con <carpeta_visitas>`, resumen `N visitas nuevas · N actualizadas · N sin cambios · N con dudas · N procesadas` + ` · N omitidas (sin número legible)` + ` · N que ya no están en la carpeta`, avisos `s.avisos`, filas de `d.visitas_nuevas`. Lector: `lector: N elementos en M páginas` / `lector: no se abre (<error>)` / `lector: <error>` |
| A33 | errores de red | — | — | `El backend no responde en <API>. Verifica que el servidor FastAPI esté corriendo.`; otros: texto del servidor en `modalVisita.error` |

### 3.7 Visor (M4)

| ID | Elemento (línea) | Función | Llamada | Resultado y mensajes |
|---|---|---|---|---|
| A34 | apertura (209) | `abrirVisor` (1112) | `GET /api/proyectos/{id}/visor/indice` y `GET /api/proyectos/{id}/elementos` en paralelo | `hojas`, `elementos` (si la 2.ª falla, lista vacía); página inicial = primera hoja; llama a `cargarHoja`; error → `visor.error` |
| A35 | select de hoja `data-visor-hoja` (523) | `cargarHoja` (1125) | `GET /api/proyectos/{id}/visor/hojas/{pagina}/info?dpi=60`; la imagen es `GET .../visor/hojas/{pagina}.png?dpi=<info.dpi>` (por `<img src>`) | `info` (`ancho_pt, alto_pt, ancho_px, dpi`); ajusta el zoom al ancho |
| A36 | `−` / `+` / «Ajustar» (527, 529, 530) | `zoomVisor(0.8 / 1.25)`, `ajustarVisor` | — | zoom entre 0.1 y 8 |
| A37 | select Elemento `data-visor-elemento` (550) | `cambiarElemento` (1148) | — | reinicia propuestas, borradores, vistas previas y mensajes; salta a la página del recuadro guardado si existe |
| A38 | «Proponer recuadros» `data-proponer` (557) | `proponerVisor` (1158) | `POST /api/proyectos/{id}/elementos/{uid}/propuesta` sin cuerpo | `propuestas.{localizacion,detalle}` (`rect, pagina, fuente.metodo, fuente.rotulo, motivo`); salta a la página de la propuesta de LOCALIZACION; deshabilitado sin elemento o mientras `ocupado` |
| A39 | «Usar propuesta» `data-usar` (565) | `usarPropuesta` | — | copia la propuesta al borrador con `origen:'confirmado'`, activa ese tipo, salta de página |
| A40 | dibujar en el lienzo (537) | `empezarDibujo/seguirDibujo/terminarDibujo` | — | borrador con `origen:'dibujado'`, coordenadas redondeadas a 2 decimales; < 5 pt se descarta |
| A41 | «Confirmar y guardar» `data-guardar-recuadro` (566) | `guardarRecuadro` | `PUT /api/proyectos/{id}/elementos/{uid}/recuadro` JSON `{tipo,pagina,rect,origen}` | actualiza `recorte_planta`/`recorte_detalle` del elemento; mensaje `LOCALIZACION guardado (confirmado por <quien>).` o `DETALLE guardado (confirmado por <quien>).`; luego pide vista previa |
| A42 | «Vista previa» `data-previa` (567) | `vistaPrevia` (1212) | `POST /api/proyectos/{id}/visor/vista-previa` JSON `{tipo,pagina,rect}` → imagen (blob) | muestra `<img>` con URL de objeto (revoca la anterior); error → `visor.error` y vista previa vacía |
| A43 | radio de tipo (560) | v-model | — | define a qué tipo se aplica el dibujo |
| A44 | X (532) | inline | — | `visor = null` |

Estado de cada recuadro (`estadoRecuadro :1180`): «sin guardar» (azul) / «confirmado» (verde) / «propuesto · pendiente de verificar» (naranja) / «pendiente de verificar» (naranja). Texto de detalle (`:1188`): `p<pág> · [x0, y0, x1, y1] pt` + `(origen)`, o `· <origen> por <confirmado_por>`, o `· fuente: <metodo> «<rotulo>»`, o el `motivo`; sin nada: «Sin recuadro: elige un elemento y pulsa «Proponer recuadros», o dibújalo.».

### 3.8 Confirmar datos del plano (M6)

| ID | Elemento (línea) | Función | Llamada | Cuerpo | Resultado y mensajes |
|---|---|---|---|---|---|
| A45 | «Extraer del plano vigente» `data-extraer` (608) | `extraerPlano` (1346) | `POST /api/proyectos/{id}/extraer-diseno` | sin cuerpo | mensaje verde `Extracción rev. <revision>: N tablas (V en verde), E elementos propuestos, D dudas nuevas, C cerradas. Todo queda pendiente hasta que lo confirmes.`; recarga tablas y dudas |
| A46 | clic en una tabla `data-tabla` (620) | `abrirTabla` (1284) | `GET /api/proyectos/{id}/tablas-extraidas/{id}`; si trae `recorte`: `POST /api/proyectos/{id}/visor/vista-previa` `{tipo:'detalle',pagina,rect:recorte}` | — | `sel` con comprobaciones y campos; imagen del recorte (error en `errorRecorte`) |
| A47 | «Certificar que vale para el plano vigente» `data-certificar-notas` (658) | `certificarNotas` (1328) | `POST /api/proyectos/{id}/tablas-extraidas/{id}/certificar-notas` | `{"certifico":true,"extraido_en":"<sel.extraido_en>"}` | mensaje `Tabla <tabla> certificada para el vectorial <sha12>…: queda en <resultado>` + ` · N duda cerrada.`; recarga tablas/dudas y reabre la tabla; deshabilitado sin casilla |
| A48 | «Confirmar tabla completa» `data-confirmar-tabla` (695) | `confirmarTabla` (1308) | `POST /api/proyectos/{id}/tablas-extraidas/{id}/confirmar` | `{"confirmo":true,"extraido_en":"<sel.extraido_en>"}` | mensaje `Lote <lote>: N valores confirmados en M elementos` + ` · N ya confirmados con otro valor (duda abierta en la Mesa)` + ` · N dudas cerradas` + `.`; recarga y reabre; deshabilitado sin casilla `data-revisado` |
| A49 | «Mesa de Dudas de la obra» (609) / «Ir a la Mesa de Dudas» `data-ir-mesa` (700) | `abrirMesaObra` | `GET /api/dudas?sin_visita=true&proyecto_id={id}` | — | abre M1 sobre M6 |
| A50 | hover sobre fila de valores (676) | inline | — | — | resalta la celda en el recorte |
| A51 | X (611) | `cerrarConfirmar` | — | — | libera la URL del recorte |

---

## 4. Estados (cargando / vacío / error)

| Pantalla / modal | Cargando | Vacío | Error |
|---|---|---|---|
| Carga inicial del tablero (Z9-Z16) | no existe (las tarjetas muestran vacío hasta que llega la respuesta; `stats` es `{}`) | las tarjetas quedan en blanco | Z6 «No se pudo cargar el tablero» + `No hay conexión con el backend en http://localhost:8000 (<detalle>). Verifica que el servidor FastAPI esté corriendo.` |
| Dudas abiertas (para los contadores) | no existe | lista vacía | Z7 «No se pudo leer la Mesa de Dudas» + `No se pudieron leer las dudas (<detalle>). Verifica que el servidor FastAPI esté corriendo.` |
| Sincronizar (A2) | botón «Sincronizando…» + icono girando, deshabilitado | no existe | Z5 «No se pudo sincronizar con Dropbox» + texto |
| Procesar cola (A3) | botón «Procesando…» + icono latiendo, deshabilitado; Z3 borde amarillo con el mensaje y el id | `data.mensaje` cuando no hay trabajo (por ejemplo, nada que procesar) | Z3 borde rojo con `No se pudo lanzar el procesamiento.` / `El procesamiento falló.` / `No se pudo leer el estado del trabajo.` + error |
| Matriz de proyectos (Z14) | no existe | no existe (tabla sin filas, sin texto) | no existe (comparte Z6) |
| Plano vigente (celda) | no existe | insignia «sin plano»; fecha ausente → «sin fecha de plano»; supervisor ausente → «Pendiente»; cliente ausente → «—»; estado de informe ausente → «Sin iniciar» | no existe |
| Cola de visitas (Z15) | no existe | «No hay visitas registradas. Pulsa "Sincronizar desde Dropbox".», o si hay error del tablero «Sin datos: no se pudo leer la cola de visitas del backend.» | comparte Z6 |
| Kanban de OT (Z16) | no existe | columnas con contador 0 y sin tarjetas | no existe |
| M1 Mesa de Dudas | «Cargando dudas…» | «Esta visita no tiene dudas.» / «Esta obra no tiene dudas abiertas sin visita.» | recuadro rojo `data-error-mesa` con `No hay conexión con el backend en <API> (<detalle>). Verifica que el servidor FastAPI esté corriendo.`; conflicto `data-conflicto-mesa`; error por duda `data-error-duda` |
| M2 Obra | botón «Subiendo…» | no existe | `data-error-obra` con los mensajes de A28 |
| M3 Visita | botón «Subiendo y leyendo la visita…» / «Sincronizando y leyendo las visitas…» | no existe | `data-error-visita` |
| M4 Visor | «Cargando la hoja…» en el lienzo hasta tener `info` | «Esta obra aún no tiene elementos de diseño: los recuadros se guardan por elemento.»; «Sin recuadro: elige un elemento y pulsa «Proponer recuadros», o dibújalo.» | `data-visor-error` (rojo); éxito en `data-visor-mensaje` (verde) |
| M5 Datos de la obra | no existe (se abre vacío mientras llega el GET) | textareas vacías con ejemplo como placeholder | mensaje por grupo en rojo (`data-mensaje`); el error del GET inicial se ignora en silencio |
| M6 Confirmar | «Cargando tablas…» (lista), «Cargando la tabla…» (detalle), «Extrayendo…», «Confirmando…», «Certificando…» | «Aún no hay tablas extraídas del plano vigente. Pulsa «Extraer del plano vigente».»; «Elige una tabla para ver sus filas propuestas junto al recorte del plano.»; «Ningún elemento toma valores de esta tabla.»; «Sin recorte: la tabla no tiene celdas con posición.» | `data-confirmar-error`; `errorRecorte` en el recorte; éxito `data-confirmar-mensaje` |

---

## 5. Rutas de la API

Todas bajo `http://localhost:8000`. Se hacen **23 llamadas `fetch(` en el código (24 peticiones, porque `Promise.all` de `abrirVisor :1117` lanza dos)**, a **25 combinaciones de método y ruta** (R2, R3 y R4 son la misma ruta `/api/dudas` con distinto filtro). La tabla lista 26 filas porque añade R18, la imagen de la hoja, que se pide desde `<img src>` y no desde `fetch`. Verificadas contra el backend (`main.py`, `mesa_dudas.py`, `obras.py`, `visor.py`, `plano/extractor.py`, `plano/confirmacion.py`, `visitas_obra.py`).

| # | Método | Ruta | Dónde se usa (línea del `fetch`) | Cuerpo | Qué devuelve (lo que el tablero lee) |
|---|---|---|---|---|---|
| R1 | GET | `/api/dashboard` | `cargarDatos` (833) | — | `stats`, `proyectos`, `visitas`, `ordenes`, `planos_vigentes` |
| R2 | GET | `/api/dudas?resuelta=false` | `cargarDudasAbiertas` (820) | — | lista de dudas (`id, visita_id, proyecto_id, categoria, campo_afectado, id_elemento, pregunta, resuelta, ...`) |
| R3 | GET | `/api/dudas?visita_id={id}` | `cargarDudasVisita` (943) | — | lista de dudas de la visita (incluye resueltas, `respuesta`, `creado`, `resuelto_en`, `campo_confirmable`) |
| R4 | GET | `/api/dudas?sin_visita=true&proyecto_id={id}` | `cargarDudasVisita` (943) | — | lista de dudas de la obra sin visita |
| R5 | PATCH | `/api/dudas/{id}` | `enviarRespuesta` (971) | JSON `{respuesta[, stp]}` | `duda_id`, `campo`, `valor_aplicado`, `estado_visita`; 404/409/422 con `detail` |
| R6 | POST | `/api/dropbox/sync` | `sincronizarDropbox` (867) | — | `{status:'ok', proyectos:[…]}` |
| R7 | POST | `/api/visitas/procesar-cola` | `procesarCola` (922) | — | `{mensaje, trabajo:{id}}` (202) |
| R8 | GET | `/api/trabajos/{id}` | `seguirTrabajo` (905) | — | `estado, resumen{visitas[], pdf[]}, error` |
| R9 | POST | `/api/proyectos` | `enviarObra` (1037) | JSON con los campos no vacíos | `{proyecto:{id, nombre}}` (201) |
| R10 | POST | `/api/proyectos/{id}/planos` | `enviarObra` (1050) | multipart | `{plano:{revision, elementos_marcados, aviso_paginas}}` (201) |
| R11 | GET | `/api/proyectos/{id}/datos-obra` | `abrirDatosObra` (1076) | — | `{datos:{<tipo>:[{clave,valor}]}}` |
| R12 | PUT | `/api/proyectos/{id}/datos-obra` | `guardarDatos` (1092) | JSON `{tipo, items, completo}` | `{guardados, dudas_cerradas}` |
| R13 | POST | `/api/proyectos/{id}/visitas` | `enviarVisita` (1409) | multipart | `{visita, dudas, lector}` (201) |
| R14 | POST | `/api/proyectos/{id}/dropbox` | `enviarVisita` (1409) | JSON `{carpeta_visitas}` | `{carpeta_visitas, sync, visitas_nuevas[]}` |
| R15 | GET | `/api/proyectos/{id}/visor/indice` | `abrirVisor` (1117) | — | `{hojas:[{pagina, hoja, titulos[]}]}` |
| R16 | GET | `/api/proyectos/{id}/elementos` | `abrirVisor` (1117) | — | `{elementos:[{uid, id_elemento, ejes, nivel_rango, recorte_planta, recorte_detalle, revisar_motivo}]}` |
| R17 | GET | `/api/proyectos/{id}/visor/hojas/{pagina}/info?dpi=60` | `cargarHoja` (1129) | — | `{ancho_pt, alto_pt, ancho_px, dpi}` |
| R18 | GET | `/api/proyectos/{id}/visor/hojas/{pagina}.png?dpi={dpi}` | `<img src>` (538, URL en 1132), **no es `fetch`** | — | PNG |
| R19 | POST | `/api/proyectos/{id}/elementos/{uid}/propuesta` | `proponerVisor` (1162) | — | `{localizacion, detalle}` |
| R20 | PUT | `/api/proyectos/{id}/elementos/{uid}/recuadro` | `guardarRecuadro` (1201) | JSON `{tipo,pagina,rect,origen}` | `{guardado:{pagina,rect,origen,confirmado_por}}` |
| R21 | POST | `/api/proyectos/{id}/visor/vista-previa` | `vistaPrevia` (1217), `abrirTabla` (1295) | JSON `{tipo,pagina,rect}` | imagen (blob) |
| R22 | GET | `/api/proyectos/{id}/tablas-extraidas` | `cargarTablas` (1270) | — | `{tablas:[…]}` |
| R23 | GET | `/api/proyectos/{id}/tablas-extraidas/{tabla_id}` | `abrirTabla` (1290) | — | detalle con `comprobaciones`, `campos`, `recorte`, `confirmable`, `certificable`, … |
| R24 | POST | `/api/proyectos/{id}/tablas-extraidas/{tabla_id}/confirmar` | `confirmarTabla` (1314) | JSON `{confirmo, extraido_en}` | `{lote, confirmados, elementos, conflictos, dudas_cerradas[]}` |
| R25 | POST | `/api/proyectos/{id}/tablas-extraidas/{tabla_id}/certificar-notas` | `certificarNotas` (1334) | JSON `{certifico, extraido_en}` | `{tabla, sha256, resultado, dudas_cerradas[]}` |
| R26 | POST | `/api/proyectos/{id}/extraer-diseno` | `extraerPlano` (1350) | — | `{revision, tablas[], elementos:{propuestos}, dudas_creadas, dudas_cerradas}` |

**Polling e intervalos:** solo uno: `setTimeout(() => seguirTrabajo(id), 2000)` en `:908` (reintenta cada 2 s mientras el trabajo está «corriendo»; no hay límite de intentos ni cancelación; si la lectura falla, se detiene). No hay `setInterval`, recarga periódica, WebSocket ni EventSource. Los datos solo se refrescan al cargar la página y tras cada acción.

**Rutas del backend que el tablero NO usa:** `PATCH /api/proyectos/{id}` (`main.py:97`), `GET /api/proyectos/{id}/planos`, `POST /api/visitas/{id}/procesar`, `GET /api/trabajos/{id}/eventos`. Se anotan por si el rediseño las quiere usar; no son parte de la paridad.

---

## 6. Ganchos `data-*`

**Total: 93 apariciones, 86 nombres distintos.** El número de 86 corresponde a los nombres distintos; las apariciones son 93 porque 7 nombres se repiten (`data-archivo` ×2, `data-campo` ×2, `data-certifico` ×2, `data-visita-campo` ×5). Comprobado con `grep -o 'data-[a-z0-9-]*' FRONTEND/index.html | sort | uniq -c`. Los que tienen `:` (ligados) generan un valor dinámico por elemento.

| Gancho | Elemento que marca | Línea(s) |
|---|---|---|
| `data-nueva-obra` | botón «Nueva obra» | 23 |
| `data-procesar-cola` | botón «Procesar Cola Visitas» | 31 |
| `data-aviso-obra` | aviso verde de obra creada | 40 |
| `data-trabajo-cola` | recuadro del trabajo de la cola | 46 |
| `data-resultado-visitas` | recuadro de resultado de visitas | 56 |
| `data-visita-nueva` (valor `v.id`) | `<li>` de cada visita nueva | 64 |
| `data-abrir-mesa-visita` (valor `v.id`) | botón «Mesa de Dudas: N» del resultado | 69 |
| `data-error-dudas` | recuadro rojo de error de dudas | 95 |
| `data-plano-de` (valor `p.id`) | celda «Plano vigente» de la fila | 201 |
| `data-cambiar-plano` (`p.id`) | botón Cambiar plano / Subir planos | 208 |
| `data-ver-plano` (`p.id`) | botón Ver plano | 209 |
| `data-datos-obra` (`p.id`) | botón Datos de la obra | 210 |
| `data-confirmar-plano` (`p.id`) | botón Confirmar datos del plano | 213 |
| `data-dudas-obra` (`p.id`) | botón Dudas de la obra: N | 214 |
| `data-subir-visita` (`p.id`) | botón Subir visita | 217 |
| `data-conectar-dropbox` (`p.id`) | botón Conectar / Dropbox conectado | 218 |
| `data-aviso-dudas` | línea «con N duda(s) bloqueante(s)» en la cola | 274 |
| `data-mesa` | raíz del panel Mesa de Dudas | 312 |
| `data-mesa-obra` | subtítulo de la Mesa en modo obra | 321 |
| `data-error-mesa` | error de conexión de la Mesa | 326 |
| `data-conflicto-mesa` | aviso de conflicto 409 | 329 |
| `data-duda` (`d.id`) | tarjeta de una duda | 338 |
| `data-etiqueta-visita` | línea «Etiqueta en la visita» | 341 |
| `data-campo-confirmable` | línea «Campo del plano: …» | 360 |
| `data-valor-campo` | input «Valor leído en el plano» | 361 |
| `data-confirmar-campo` | botón «Confirmar valor» | 362 |
| `data-aviso-plano` | aviso de duda de plano | 368 |
| `data-aviso-etiqueta` | aviso de duda de etiqueta de visita | 369 |
| `data-error-duda` | error de una duda | 405 |
| `data-aviso-mesa` | aviso verde de éxito de la Mesa | 408 |
| `data-modal-obra` | raíz del modal de obra | 413 |
| `data-campo="nombre"` (fijo) | input «Nombre de la obra» | 422 |
| `data-archivo="vectorial"` / `="sellado"` | inputs de archivo del modal de obra | 450, 452 |
| `data-certifico` | casilla de certificación del modal de obra | 459 |
| `data-certifico` | casilla de certificación de notas (M6) | 655 |
| `data-error-obra` | error del modal de obra | 462 |
| `data-enviar-obra` | botón enviar del modal de obra | 465 |
| `data-modal-visita` | raíz del modal de visita | 474 |
| `data-visita-pdf` | input PDF de la visita | 485 |
| `data-visita-fotos` | input de fotos | 487 |
| `data-visita-campo="numero"` / `="fecha"` / `="elementos"` / `="nivel"` / `="clase"` | los 5 campos del modal de visita | 489, 491, 493, 495, 497 |
| `data-visita-carpeta` | input de la carpeta de Dropbox | 505 |
| `data-error-visita` | error del modal de visita | 507 |
| `data-enviar-visita` | botón enviar del modal de visita | 510 |
| `data-visor` | raíz del visor | 519 |
| `data-visor-hoja` | select de hoja | 523 |
| `data-zoom-menos` | botón − | 527 |
| `data-zoom` | porcentaje de zoom | 528 |
| `data-zoom-mas` | botón + | 529 |
| `data-lienzo` | contenedor con scroll del visor | 535 |
| `data-hoja-lienzo` | capa de dibujo de la hoja | 537 |
| `data-hoja-img` | imagen de la hoja | 538 |
| `data-caja` (valor `guardado-/propuesta-/borrador-<tipo>`) | cajas sobre la hoja | 539 |
| `data-visor-elemento` | select de elemento | 550 |
| `data-proponer` | botón «Proponer recuadros» | 557 |
| `data-recuadro` (valor `localizacion`/`detalle`) | tarjeta de cada tipo de recuadro | 558 |
| `data-detalle-recuadro` (valor tipo) | texto de detalle del recuadro | 563 |
| `data-usar` (valor tipo) | botón «Usar propuesta» | 565 |
| `data-guardar-recuadro` (valor tipo) | botón «Confirmar y guardar» | 566 |
| `data-previa` (valor tipo) | botón «Vista previa» | 567 |
| `data-previa-img` (valor tipo) | imagen de vista previa | 569 |
| `data-visor-error` | error del visor | 572 |
| `data-visor-mensaje` | mensaje de éxito del visor | 573 |
| `data-modal-datos` | raíz del modal de datos de la obra | 580 |
| `data-datos` (valor `g.tipo`) | textarea de cada grupo | 590 |
| `data-guardar` (valor `g.tipo`) | botón «Guardar» del grupo | 594 |
| `data-mensaje` (valor `g.tipo`) | mensaje del grupo | 596 |
| `data-confirmar` | raíz del modal Confirmar datos del plano | 604 |
| `data-extraer` | botón «Extraer del plano vigente» | 608 |
| `data-confirmar-error` | error de Confirmar | 613 |
| `data-confirmar-mensaje` | mensaje de éxito de Confirmar | 614 |
| `data-tabla` (valor `t.clave`) | botón de cada tabla extraída | 620 |
| `data-resultado` | insignia verde/rojo de la tabla abierta | 640 |
| `data-comprobaciones` | lista de comprobaciones | 642 |
| `data-certificada` | texto «(certificada por …)» | 645 |
| `data-certificar` | bloque de certificación de notas | 649 |
| `data-certificar-notas` | botón de certificar | 658 |
| `data-recorte` | contenedor del recorte | 663 |
| `data-recorte-img` | imagen del recorte | 664 |
| `data-resaltado` | caja roja de celda resaltada | 665 |
| `data-campos` | tabla de valores propuestos | 673 |
| `data-campo` (valor `<id_elemento>|<campo>`) | fila de la tabla de valores | 677 |
| `data-revisado` | casilla «Revisé los N valores…» | 692 |
| `data-identidad` | texto de identidad de elementos pendiente | 693 |
| `data-confirmar-tabla` | botón «Confirmar tabla completa» | 695 |
| `data-tabla-roja` | bloque de tabla en rojo | 697 |
| `data-ir-mesa` | botón «Ir a la Mesa de Dudas» | 700 |
| `data-no-confirmable` | texto «No se puede confirmar: …» | 702 |

---

## 7. Reglas de presentación que ya aplica

| Regla | Detalle | Línea |
|---|---|---|
| Fechas de visita | solo acepta `AAAA-MM-DD…` y muestra `DD/MM/AAAA`; cualquier otro valor se trata como pendiente | 743-747 |
| Fecha y hora | `AAAA-MM-DDTHH:MM…` → `DD/MM/AAAA HH:MM`; si no coincide, «—» | 795-799 |
| Hora de la sincronización | hora local del navegador en `DD/MM/AAAA HH:MM` | 876-882 |
| Valor «pendiente de verificar» | constante `PENDIENTE`; `esPendiente(v)` es verdadero para nulo, vacío o ese texto (sin distinguir mayúsculas) | 715, 739 |
| Insignia «pendiente de verificar» (naranja `bg-orange-950 text-orange-300 border-orange-600`) | en N.º, Fecha y Clase de la cola; en estados de recuadro; «layout pendiente de verificar» en Z8; «detalle pendiente de verificar» para Mixta | 117, 254, 260, 263, 267, 1185-1186 |
| Campos pendientes de la visita | línea «Pendiente: » + etiquetas separadas por coma, `ETIQUETAS_CAMPO`: `fecha_visita`→fecha, `clase`→clase, `numero`→número, `estado`→estado, `archivos_json`→archivos (PDF), `lector_visita`→lectura del PDF; otro valor se muestra tal cual | 767-768, 280 |
| Colores por estado de visita (`claseEstado`) | `Sin procesar` gris; `En cola` amarillo; `En proceso` azul; `Con dudas` naranja fuerte y negrita; `En revisión` púrpura; `Procesada` verde; cualquier otro, gris | 770-777 |
| Fila de visita con dudas | fondo `bg-orange-950/30` con borde izquierdo naranja 4 px si `estado === 'Con dudas'` o hay bloqueantes abiertas; cursor mano si hay dudas abiertas | 251 |
| Estados de visita que el tablero conoce | Sin procesar, En cola, En proceso, Con dudas, En revisión, Procesada | 770-777 |
| Texto de dudas | singular/plural: «duda bloqueante abierta» / «dudas bloqueantes abiertas»; «duda abierta» / «dudas abiertas · clic para responder» | 275, 278 |
| Categorías de duda | `DUDA_BLOQUEANTE` → «Bloqueante» (naranja); `HALLAZGO_INTERNO` → «Hallazgo interno» (amarillo); resuelta → opacidad 70 % y «Resuelta» verde | 338-346 |
| Texto de fotos de una duda | «Foto p. N» / «Fotos p. N–M» / «Fotos desde p. N» / «Fotos», leído del texto de la pregunta (`página(s) N a M`) o del sufijo `pNNN` del campo | 757-765 |
| Colores de las insignias de la matriz | tipo = azul; estado de informe = amarillo; layout `supervision 5.1` azul, pendiente naranja, otro gris | 116-118, 193, 199 |
| Valores por defecto en la matriz | cliente ausente «—»; supervisor ausente «Pendiente»; estado de informe ausente «Sin iniciar» | 196-199 |
| Colores del visor | confirmado verde `#22c55e`, propuesto amarillo discontinuo `#eab308`, sin guardar azul `#3b82f6`; recuadro de celda resaltada rojo `#dc0000` | 1231-1233, 666 |
| Estados de tabla extraída | `verde` (verde) / `rojo` (rojo); no vigente: opacidad 50 % y texto naranja; valor distinto del de la tabla: texto rojo con «tabla: …» | 625, 622, 680 |
| Estados del kanban | las 6 columnas fijas: Pendiente, Asignada, En proceso, Bloqueada, En revisión, Entregada | 294 |
| Ortografía de campos exactos | la validación de fecha del modal exige `DD/MM/AAAA` (`^\d{2}/\d{2}/\d{4}$`); número de visita entero de 1 a 3 cifras | 1393, 1395 |
| Tema | fondo `#121214`, texto `#e1e1e6`, tarjetas `#1a1a1e`, bordes `#29292e`, acento amarillo (`yellow-500`); fuente `system-ui, -apple-system, sans-serif`; `lang="es"` | 11, 2 |
| Iconos | Font Awesome 6.4.0 (solid y brands) | 9 |
| Atajos de teclado | **no existen** (no hay `@keydown`, `@keyup` ni `addEventListener`; solo se cierra con la X; la Mesa también con clic en el fondo) | — |
| Persistencia en el navegador | **no existe** (no hay `localStorage`, `sessionStorage` ni cookies) | — |
| Capas (z-index) | Mesa `z-40`; modales de obra, visita, visor y datos `z-50`; Confirmar `z-30`. La Mesa queda sobre Confirmar; los demás sobre la Mesa | 312, 413, 474, 519, 580, 604 |
| Diseño de la página | `grid-cols-5` (tarjetas), `grid-cols-6` (kanban): ancho fijo, sin versión móvil | 146, 293 |

Hallazgos que el rediseño debe conocer (no son cambios):
1. `stats.bloqueadas` y `stats.vencen_7_dias` se muestran, pero el backend siempre devuelve 0.
2. `stats.visitas_con_dudas` llega pero no se usa; el tablero cuenta él mismo `contarConDudas` (`:808`).
3. El campo `observaciones` del proyecto se muestra bajo el rótulo «Próxima Acción».
4. Z6 y Z7 (errores de carga) no tienen botón cerrar y desaparecen solos al recargar con éxito.
5. El modal de obra, el de visita y el de datos no se cierran al hacer clic en el fondo (la Mesa sí).
6. El error al leer los datos de la obra (A13) se ignora sin mostrar nada.
7. `resultadoVisitas` solo sustituye al anterior; no se acumulan.

---

## 8. Dependencias externas

| Recurso | URL exacta | Uso | Línea |
|---|---|---|---|
| Tailwind CSS (CDN en tiempo de ejecución) | `https://cdn.tailwindcss.com` | todos los estilos (clases utilitarias, incluidos valores arbitrarios como `bg-[#1a1a1e]`) | 7 |
| Vue 3 (build global, versión flotante `@3`) | `https://unpkg.com/vue@3/dist/vue.global.js` | toda la interfaz | 8 |
| Font Awesome 6.4.0 | `https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css` | iconos `fa-solid` y `fa-brands fa-dropbox` | 9 |
| Fuentes | ninguna externa: `system-ui, -apple-system, sans-serif` | texto | 11 |
| Backend | `http://localhost:8000` (constante `API`) | todas las rutas de la sección 5 | 714 |

No hay imágenes, logos, favicon ni archivos CSS/JS propios: todo está en un único archivo con `<style>` mínimo (1 regla en `body`) y un único `<script>` en línea (`:712-1460`). El tablero requiere Internet para cargar sus 3 CDN (no funciona sin conexión si el navegador no los tiene en caché).

---

## 9. Checklist de paridad (para marcar en B5)

### Cabecera y avisos
- [ ] Logo `CATDIC`, título «Control Taller» e insignia «Web Local v2.0»
- [ ] Botón «Nueva obra» abre el modal de obra
- [ ] Botón «Sincronizar desde Dropbox» con estado «Sincronizando…» y deshabilitado mientras corre
- [ ] Botón «Procesar Cola Visitas» con estado «Procesando…» y deshabilitado mientras corre
- [ ] Aviso verde de obra creada, con botón cerrar
- [ ] Recuadro del trabajo de la cola (id, estado, resumen, error; colores por estado; cerrar solo si no corre)
- [ ] Polling cada 2 s del trabajo hasta que termina; al terminar recarga datos y dudas
- [ ] Recuadro de resultado de subir visita / conectar Dropbox (título, resumen, filas, «No hay visitas nuevas.», avisos en `<details>`)
- [ ] Botón «Mesa de Dudas: N» en cada fila del resultado
- [ ] Error «No se pudo sincronizar con Dropbox» con botón cerrar
- [ ] Error «No se pudo cargar el tablero»
- [ ] Error «No se pudo leer la Mesa de Dudas»
- [ ] Resultado de la sincronización: hora, layout, 7 contadores, avisos, carpetas desaparecidas, omitidas, dudas creadas, tooltip de planos sellados
- [ ] Carga inicial: dudas abiertas y dashboard

### Tarjetas y tablas
- [ ] 5 tarjetas: Proyectos Activos, Órdenes Abiertas, Bloqueadas, Vencen en ≤ 7 Días, Visitas en Cola
- [ ] Matriz de proyectos con las 7 columnas y sus valores por defecto («—», «Pendiente», «Sin iniciar»)
- [ ] Celda de plano vigente: revisión, etiqueta, fecha, certificado por, tooltip de sha256, insignia «sin plano»
- [ ] Botón «Cambiar plano» / «Subir planos»
- [ ] Botón «Ver plano» (solo con plano)
- [ ] Botón «Datos de la obra»
- [ ] Botón «Confirmar datos del plano» (solo con plano)
- [ ] Botón «Dudas de la obra: N» (solo si hay)
- [ ] Botones «Subir visita» y «Conectar con Dropbox» / «Dropbox conectado» (solo Supervisión)
- [ ] Cola de visitas: contador «N visitas · M con dudas», 6 columnas, orden por proyecto/número/carpeta
- [ ] Fila resaltada con dudas o bloqueantes; clic abre la Mesa
- [ ] N.º, Fecha y Clase con «pendiente de verificar»; fecha en DD/MM/AAAA; clase Mixta con detalle
- [ ] Insignias de estado con los 6 colores
- [ ] Líneas «con N duda(s) bloqueante(s)», «N duda(s) abierta(s) · clic para responder» y «Pendiente: …»
- [ ] Texto de cola vacía (dos variantes según haya error)
- [ ] Kanban de OT con 6 columnas, contadores y tarjetas

### Mesa de Dudas
- [ ] Panel lateral, se cierra con X y clic en el fondo
- [ ] Modo visita y modo obra, con cabeceras distintas
- [ ] Cargando, vacío (2 textos), error de conexión, conflicto 409, aviso de éxito
- [ ] Aviso «figura como Procesada pero tiene dudas bloqueantes abiertas»
- [ ] Tarjeta con categoría, campo/elemento o etiqueta y fotos, fechas de creación y resolución, respuesta
- [ ] Hallazgo interno: «Marcar revisado»
- [ ] Campo del plano confirmable: input + «Confirmar valor»
- [ ] Duda con elemento: textarea + «Guardar respuesta» y avisos de plano / etiqueta
- [ ] Duda de fecha: input DD/MM/AAAA + «Guardar fecha»
- [ ] Duda de clase: select + «Guardar clase»
- [ ] Duda de estado: radios, select de STP candidatos, aviso sin candidatos, «Guardar estado»
- [ ] Duda de archivos: solo texto informativo
- [ ] Duda de otro campo: texto «no se responde desde la Mesa de Dudas»
- [ ] Error por duda y bloqueo del envío doble
- [ ] Apertura automática de la Mesa si hay dudas nuevas tras sincronizar o subir visita

### Modal Nueva obra / Cambiar plano
- [ ] 11 campos de la obra y deshabilitado tras crearla
- [ ] 2 archivos PDF, revisión, fecha del plano y casilla de certificación
- [ ] 3 validaciones locales con su texto
- [ ] Crear obra y subir planos en 2 pasos; reintento solo de la subida si falla
- [ ] Aviso final con revisión, elementos marcados y aviso de páginas

### Modal Subir visita / Conectar con Dropbox
- [ ] Modo subir: PDF, fotos, número, fecha, elementos, nivel, clase y nota de «Mixta»
- [ ] Modo dropbox: carpeta, con valor inicial desde `carpeta_dropbox`
- [ ] Validaciones locales con su texto
- [ ] Etiquetas del botón en reposo y enviando, en los dos modos
- [ ] Resultado en el recuadro de resultado y apertura de la Mesa si hay dudas

### Visor
- [ ] Selector de hoja y zoom `−`, `+`, «Ajustar» (límites 0.1-8)
- [ ] Imagen de la hoja y cajas verde / amarilla / azul con etiqueta
- [ ] Dibujo por arrastre, descarte de arrastres menores de 5 pt
- [ ] Selector de elemento, avisos sin elementos y `revisar_motivo`
- [ ] «Proponer recuadros»
- [ ] Por tipo: radio, estado, detalle, «Usar propuesta», «Confirmar y guardar», «Vista previa» e imagen de la vista previa
- [ ] Salto automático a la página del recuadro
- [ ] Error y mensaje del visor, «Cargando la hoja…»

### Datos de la obra
- [ ] 4 grupos con título, ayuda, ejemplo, textarea y «Guardar»
- [ ] Casilla «Ya escribí todos los de esta lista» (3 grupos) y texto de `techo`
- [ ] Carga previa de los datos guardados
- [ ] Mensaje verde / rojo por grupo

### Confirmar datos del plano
- [ ] «Extraer del plano vigente» con mensaje de resultado
- [ ] Botón «Mesa de Dudas de la obra»
- [ ] Lista de tablas con nombre, resultado, página/hoja/nivel, «Falla», «No vigente»
- [ ] Detalle: cabecera, comprobaciones, certificadas
- [ ] Certificación de notas de modificación (casilla + botón + mensaje)
- [ ] Recorte del plano con celda resaltada al pasar el ratón por un valor; texto sin recorte
- [ ] Tabla de valores propuestos con estado confirmado/pendiente y diferencia con la tabla
- [ ] Confirmación por lote (casilla, identidad pendiente, botón, mensaje de lote)
- [ ] Tabla roja: texto y botón «Ir a la Mesa de Dudas»; texto «No se puede confirmar»
- [ ] Estados cargando / vacío / error de cada columna

### Generales
- [ ] Las 26 filas (25 rutas con `fetch` y la imagen de la hoja) de la sección 5 con el mismo método y cuerpo
- [ ] Los 86 `data-*` de la sección 6 (93 apariciones) presentes con el mismo valor
- [ ] Formato `DD/MM/AAAA` y `DD/MM/AAAA HH:MM`; «pendiente de verificar»
- [ ] Textos de error y éxito literales de las secciones 3 y 4
- [ ] Mensajes de red: `El backend no responde en http://localhost:8000…`
- [ ] Dependencias externas de la sección 8 (o su sustituto, anotado)
- [ ] Sin pérdida de las capas de apertura (Mesa sobre Confirmar; modales sobre Mesa)
