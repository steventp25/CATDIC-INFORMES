# B3f · Órdenes de trabajo (kanban Z16) — informe del Ejecutor

Rama `claude/etapa5-fase-b-0020e1`, partiendo de `94dfcaf`. Solo `FRONTEND/` y este informe (nada de `BACKEND/`, `clasico/`, `maquetas/` ni `vendor/`).

## Qué se hizo

Pantalla nueva `#/ordenes`, de **solo lectura**: no existe ruta para crear ni mover órdenes (Fase D), así que se rotula y no se simula.

- **Ruta y navegación:** `ordenes` es una ruta general nueva; no se añadió ningún elemento a la navegación (D6 fija) y se marca «Bandeja de trabajo» como activa (rail y barra inferior). Título «Órdenes de trabajo».
- **Filtros en la dirección:** `?obra=<proyecto_id>`, `?tipo=Supervisión|Levantamiento` (y `&estado=` en pantallas estrechas). Dos listas desplegables, filtros aplicados visibles como etiquetas y «Quitar filtros». Cada cambio de filtro es una entrada del historial (Atrás vuelve al filtro anterior); recargar los conserva. Una obra que no figura en el tablero se muestra con «(no figura en el tablero)»; un tipo inexistente se ignora y se avisa. Filtros sin coincidencias: aviso con «Quitar filtros» (las 6 columnas siguen visibles, vacías).
- **6 columnas fijas** (Pendiente, Asignada, En proceso, Bloqueada, En revisión, Entregada), siempre visibles aunque estén vacías, con contador y «Sin órdenes en este estado». Cada estado: palabra + icono + borde completo (sin franjas laterales). Un estado desconocido (o nulo) va en un grupo aparte, «Otro estado: <valor>» («pendiente de verificar» si es nulo), con una nota que lo explica.
- **Tarjeta:** `doc_id` en tipografía de cifras, tipo, `seccion`, `nota` («sin nota» si no hay), obra (enlace a `#/obra/<id>/visitas`; sin nombre conocido: el id + «obra no registrada»), formato, entregable, prioridad, fecha comprometida (`DD/MM/AAAA`; no legible se muestra tal cual con «pendiente de verificar»; vacía, solo «pendiente de verificar»), «Depende de» (si esa orden está en pantalla es un botón que lleva a ella, cambia al estado correcto y le da el foco; si los filtros la ocultan lo dice; si no existe lo dice) y versión. Textos largos con `overflow-wrap`.
- **Escritorio (contenedor ≥ 880 px, es decir desde 1280 px de ventana):** 6 columnas lado a lado; el desplazamiento horizontal ocurre dentro del tablero (a 1280: 1356 px de contenido en 963 de caja; a 1920 caben sin desplazar) y la lista de cada columna tiene altura máxima con desplazamiento propio.
- **Móvil y tableta:** `tablist` accesible (6 pestañas de 44 px con palabra, icono y contador) y una columna cada vez. Flechas, Inicio y Fin cambian de estado (activación automática, foco rodante). El estado elegido va en la dirección con reemplazo de historial: sobrevive a la recarga y al Atrás.
- **Estados de la pantalla:** cargando (huesos), vacío («No hay órdenes de trabajo registradas.»), error 500 con «Reintentar».
- **Fase D:** «Crear orden» y «Cambiar estado» deshabilitados con su motivo escrito (`aria-describedby`) y la etiqueta «Fase D». No hay arrastrar ni soltar.
- **Enlaces de entrada:**
  - Inicio: «Órdenes abiertas» es un enlace a `#/ordenes` (se quitó «Se verán en la pantalla de órdenes (B3f).»). «Bloqueadas» y «Vencen en ≤ 7 días» siguen «pendiente de verificar · Fase D-a», sin tocar.
  - Bandeja: caja «Órdenes de trabajo» con «Órdenes de trabajo: N abiertas» (`stats.ordenes_abiertas`, sin recalcular).
  - Obra, pestaña «Visitas y trabajos»: bloque «Órdenes de trabajo de esta obra» agrupado por estado, con número y lista corta (3 + «y N más»), «Ver en Órdenes de trabajo» a `#/ordenes?obra=<id>`. Sin órdenes: «Esta obra no tiene órdenes de trabajo.».

## Archivos tocados

- Nuevos: `FRONTEND/js/ordenes.js` (`C.ordenes` y componente `OrdenesObra`), `FRONTEND/js/pantallas/ordenes.js`.
- `FRONTEND/js/rutas.js` (ruta `ordenes`), `FRONTEND/js/app.js` (título y «Bandeja de trabajo» activa), `FRONTEND/index.html` (2 scripts), `FRONTEND/js/pantallas/inicio.js`, `FRONTEND/js/pantallas/bandeja.js`, `FRONTEND/js/pestana-visitas.js`, `FRONTEND/css/base.css` (bloque `.ord-*` / `.oo-*`, container query `ordenes`).

## Componentes reutilizados

`Bloque` (cargando/vacío/error), `Pendiente`, `FaseD`, `Icono` (iconos existentes), `C.api.get('/api/dashboard')`, `C.formato.fecha/texto`, `C.rutas` (`hashObra`, `irA`, `reemplazar`), clases `caja`, `campo`, `etq`, `aviso`, `btn`, `enlace`. La pantalla lee `/api/dashboard` por sí sola en vez de usar el mixin de `datos.js`, porque ese mixin también pide las dudas, que aquí no hacen falta; la pestaña de la obra usa los datos que ya recibe.

## Paridad con B0

| B0 | Estado |
|---|---|
| Z10 «Órdenes abiertas» (`stats.ordenes_abiertas`) | Hecho; ahora enlaza a `#/ordenes` |
| Z16 kanban, 6 columnas fijas con contador | Hecho (siempre las 6, también vacías) |
| Z16 tarjeta `doc_id`, `seccion`, `nota` | Hecho (y más campos) |
| §4 fila del kanban: contador 0 y sin tarjetas mientras no llega la respuesta | Sustituido por el estado «cargando» y, si falla, error con «Reintentar» (el clásico no tenía error) |
| §9 línea del kanban y las 5 tarjetas de B3f | Hechas: pantalla, columnas, tarjeta, Inicio, Bandeja, bloque de obra y Fase D rotulada |
| §10 N5 «Órdenes sigue existiendo» | Hecho |
| §10 N13 «abre el registro original (… Órdenes)» | Parcial: la pantalla existe y las tres entradas enlazan; la lista común de pendientes con filas de órdenes es Fase D-a |

## Fase D o «pendiente de verificar»

- Crear orden y cambiar estado (sin ruta): Fase D.
- «Bloqueadas» y «Vencen en ≤ 7 días» en Inicio: sin tocar, «pendiente de verificar · Fase D-a».
- Pendientes de órdenes en la lista común de la Bandeja: Fase D-a.
- Campos vacíos o ilegibles de una orden: «pendiente de verificar» (fecha, prioridad, versión, sección, formato, entregable, tipo) o «sin nota» (nota, que es opcional). `depende_de` vacío no muestra la línea.
- Nada de porcentajes ni barras de avance.

## Qué se sembró (solo en la copia de la BD del scratch; script `sembrar_ordenes.py`, rotulado sintético)

11 órdenes además de `OT-LEV-001`: 2 por estado, de 3 obras reales y 2 sintéticas, de los 2 tipos. Incluye `OT-SUP-003`, `OT-LEV-002` y `OT-LEV-005` con `depende_de` (existente), `OT-SUP-006` con `depende_de` inexistente (`OT-SUP-099`), `OT-SUP-003` y `OT-LEV-005` con fecha vacía, `OT-SUP-004` con fecha «próximo mes» (no legible) y varias notas vacías. La restricción `CHECK` de `estado` impide un estado desconocido en la BD (se comprobó); se probó con una respuesta interceptada (`page.route`).

## Playwright (Chromium, 127.0.0.1:8766)

| Prueba | Resultado |
|---|---|
| 375, 768, 1024, 1280, 1920 px × claro y oscuro sobre `#/ordenes`: columnas/pestañas según el ancho, sin desborde de página ni de cajas, 0 peticiones externas, 0 errores de consola, pestañas ≥ 44 px | 66 comprobaciones, 0 fallas |
| 375 y 1280 × claro y oscuro: filtros por obra y tipo, etiquetas, recarga y Atrás con filtros, «Quitar filtros», sin coincidencias, obra/tipo desconocidos | OK |
| 375: teclado (flechas, Inicio, Fin, envolver), una columna visible, `aria-selected`, estado conservado al recargar y tras Atrás desde la obra, «Depende de» lleva a la orden, enlaces ≥ 44 px | OK |
| 1280: 6 columnas, contadores, Fase D deshabilitados con su rótulo | OK |
| Inicio (enlace, sin «B3f», «Bloqueadas» y «Vencen» sin tocar), Bandeja («10 abiertas» = `stats`), bloque de la obra (con y sin órdenes, «Ver en Órdenes» aplica la obra), «Bandeja de trabajo» activa | OK |
| Estados: cargando (GET retenido), vacío (0 órdenes), error 500 + «Reintentar», estado desconocido y nulo | OK |
| Peor caso (375, 1280, 1920) | OK (ver abajo) |

Total de la segunda tanda: 140 comprobaciones, 0 fallas (`t2.py`); primera tanda 66 (`t1.py`).

## Peor caso (respuesta interceptada)

300 órdenes, 175 en «En proceso», `doc_id` / `seccion` / `nota` / `entregable` de 200 caracteres, campos nulos (cada 13), 40 obras añadidas con nombres largos (42 opciones en el filtro). Sin desborde de página ni de tarjetas, 0 errores, carga en menos de 1 s. A 375 px las 175 tarjetas de un estado se apilan sin límite de altura; a 1280/1920 cada columna se desplaza por dentro.

## Suite del backend

- Todo en el scratch (las 5 variables `CATDIC_*`): **975 pasan, 7 se omiten, 0 fallan**.
- Sin `CATDIC_DROPBOX_RAIZ`: **977 pasan, 3 se omiten, 2 fallan**, las 2 de Dropbox (`test_escaner_dropbox.py::test_terra_living_real` y `test_parser_visitas.py::test_lista_coincide_con_dropbox_si_esta_disponible`).
- Las dos pasadas corrieron a la vez por un lanzamiento duplicado (ambas con carpetas de trabajo compartidas) y aun así dieron lo esperado. `BACKEND/` no se tocó.

## Limitaciones

- Sin ordenar dentro de la columna: se respeta el orden del servidor (no se inventa un criterio de prioridad).
- Con 300 órdenes todas las tarjetas se pintan (sin virtualizar); la carga midió menos de 1 s.
- El umbral escritorio/estrecho depende del ancho del tablero (880 px), no del de la ventana: a 1024 px de ventana ya sale en pestañas.
- «Depende de» solo enlaza dentro de la pantalla, no entre filtros.
- Nada probado con órdenes reales de uso: la BD real solo trae `OT-LEV-001`.
- Un error de una ejecución anterior de la suite: se lanzó una vez por equivocación con la ruta del scratch de B3c y se detuvo a los pocos minutos; pudo reescribir `scratchpad\b3c\suite1.txt` y los temporales de `b3c\suite\`. No se tocó nada más del scratch de B3c.

## Hashes

`9c7cc93` (pantalla), `bf8d9b6` (enlaces de entrada) y el commit de este informe. `PLANES/etapa-5-fase-B.md` tenía un cambio sin commit que no es mío y no se incluyó.

## Scratch

`C:\WINDOWS\TEMP\claude\5241ace622d5cd23\bde6ad2c-34d6-42aa-bdc5-6b0fd7ef0f32\scratchpad\b3f\` (capturas en `capturas\`: `ordenes-<ancho><c|o>.png`, `obra-ordenes-*`, `bandeja-*`, `estado-*`, `peor-*`; scripts `t1.py`, `t2.py`, `sembrar_ordenes.py`).
