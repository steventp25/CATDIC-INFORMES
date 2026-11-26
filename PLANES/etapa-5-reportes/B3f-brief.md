# B3f — Órdenes de trabajo (kanban Z16) — encargo del Líder al Ejecutor

Fecha: 23/11/2026. Va 8.ª y última de B3: B3a ✔ → B3d ✔ → B3g ✔ → B3e ✔ → B3g-2 ✔ → B3b ✔ → B3c ✔ → **B3f**. B3h no está autorizada. La lanzó el Director el 23/11 («Adelante con B3f», sin push). Estilo **Plano sellado** (`FRONTEND/DESIGN.md`).

## Dónde se trabaja (igual que en B3c)
- **Worktree y rama:** `C:\Users\Steve\OneDrive\Desktop\CATDIC-WEB\.claude\worktrees\etapa2-t7n-confirmacion-8210cf`, rama `claude/etapa5-fase-b-0020e1`.
  - No crees ni cambies de rama. Nada de push, merge, stash, checkout ni reset. No toques el checkout principal.
  - Trabajas por turnos con el Líder.
- **Zona:** `FRONTEND/**` (menos `maquetas/`, `clasico/` y `vendor/`) y `PLANES/etapa-5-reportes/B3f.md`.
  - **B3f no tiene excepción de backend: no se toca nada de `BACKEND/`.**
  - Las órdenes solo llegan hoy en `GET /api/dashboard` (`ordenes[]`, con todas las columnas de la tabla `ordenes_trabajo`: `doc_id`, `tipo`, `proyecto_id`, `seccion`, `formato`, `entregable`, `estado`, `depende_de`, `prioridad`, `fecha_comprometida`, `nota`, `version`…). Léelo en `BACKEND/main.py` y `BACKEND/database.py`, sin modificarlos.
  - **No existe ninguna ruta para crear, editar ni mover órdenes.** Esas acciones son **Fase D**: se rotulan, no se simulan, y no se arrastran tarjetas.
- **Tablero clásico.** No se borra ni se edita `FRONTEND/clasico/` ni `BACKEND/tests/test_frontend_servido.py`. Ninguna mención ni enlace al clásico en el tablero nuevo. Se puede **leer** (`FRONTEND/clasico/index.html`, líneas 291–308) como referencia.
- **Python:** `C:\Users\Steve\AppData\Local\Python\pythoncore-3.14-64\python.exe`.

## Reglas (siguen todas las de B2–B3c)
- **Sin red ni compilación:** scripts clásicos sobre `window.CATDIC`, Vue local, sin librerías nuevas.
- **Reutiliza:** `js/componentes.js` (`Bloque`, `Pendiente`, `FaseD`, `Icono`), `C.api`, `C.formato`, `js/datos.js` (si ya lee `/api/dashboard`, úsalo en vez de pedirlo otra vez) y `C.rutas`.
- **Regla de Oro:**
  - Se muestra lo que trae el servidor. Lo que falte o venga vacío (`fecha_comprometida`, `nota`, `depende_de`…) es «pendiente de verificar» o «sin nota», según sea un dato que debería existir o un texto opcional. Dilo en el informe.
  - Nada se calcula como si fuera avance: nada de porcentajes ni barras de progreso de las órdenes.
  - «Bloqueadas» y «Vencen en ≤ 7 días» de Inicio siguen como están («pendiente de verificar · Fase D-a»). B3f **no** los recalcula: es decisión del Director.
- **Diseño:**
  - sin franjas laterales de color: cada estado se muestra con su palabra, un icono y un borde completo;
  - container queries;
  - objetivos táctiles de 44 px o más en móvil;
  - foco visible.
- **Formato:** fechas `DD/MM/AAAA`. Si `fecha_comprometida` no se puede leer como fecha, se muestra tal cual con «pendiente de verificar». Textos en español.
- **Commits:** atómicos, en español, terminados en `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Nunca capturas, PDFs ni `*.db`.

## Qué hay que construir
Lee B0 (`PLANES/etapa-5-inventario-ui.md`): §1 Z10 y Z16, §4 (fila del kanban), §7 (estados del kanban y diseño), §9 (la línea del kanban y las 5 tarjetas) y §10 (N5 y N13).

### 1. Pantalla «Órdenes de trabajo» (`#/ordenes`)
- **Ruta y navegación:**
  - es una ruta general nueva en `rutas.js`, **sin añadir un elemento a la navegación principal**: la organización D6 es fija;
  - en la navegación se marca como activa «Bandeja de trabajo», porque las órdenes son trabajo pendiente;
  - el título de la pantalla es «Órdenes de trabajo».
  - Filtros opcionales en la ruta: `?obra=<proyecto_id>` y `?tipo=Supervisión|Levantamiento`. Se ven aplicados, se pueden quitar y sobreviven a la recarga y al Atrás.
- **Las 6 columnas fijas, en este orden:** Pendiente, Asignada, En proceso, Bloqueada, En revisión y Entregada.
  - Cada una lleva su contador y su estado vacío («Sin órdenes en este estado»). Las 6 se ven aunque estén vacías, como en el clásico.
  - Un `estado` desconocido no se pierde: va en un grupo aparte, «Otro estado: <valor>», y se anota.
- **Tarjeta:**
  - `doc_id` (en tipografía de cifras), `seccion` y `nota`, como en el clásico;
  - además: la obra (nombre, con enlace a `#/obra/<id>/visitas`), el tipo, el formato, el entregable, la prioridad, la fecha comprometida, «depende de <doc_id>» (si la otra orden existe, enlaza a ella dentro de la pantalla) y la versión.
  - Textos largos sin desbordar.
- **Escritorio** (1280 px o más): las 6 columnas lado a lado, con desplazamiento horizontal **dentro del tablero** si no caben, nunca de la página.
- **Móvil y tableta:** el estado se elige con un control accesible (pestañas o lista de estados con su contador) y se muestra una columna cada vez. El estado elegido sobrevive a la recarga y al Atrás.
- **Estados de la pantalla:** cargando, vacío («No hay órdenes de trabajo registradas.») y error con «Reintentar».
- **Fase D, solo rotulado:** «Crear orden» y «Cambiar estado» van deshabilitados con su motivo y la etiqueta «Fase D». No hay arrastrar ni soltar.

### 2. Enlaces de entrada
- **Inicio:** «Órdenes abiertas» pasa a ser un enlace a `#/ordenes`. Se quita «Se verán en la pantalla de órdenes (B3f).».
- **Bandeja de trabajo:** un acceso «Órdenes de trabajo: N abiertas» a `#/ordenes`. N es `stats.ordenes_abiertas`, el mismo dato que Inicio, sin recalcularlo.
- **Obra, pestaña «Visitas y trabajos»:** un bloque «Órdenes de trabajo de esta obra» con las órdenes de esa obra (`proyecto_id`) agrupadas por estado, con su número y la lista corta. Lleva «Ver en Órdenes de trabajo» a `#/ordenes?obra=<id>`. Sin órdenes: «Esta obra no tiene órdenes de trabajo.».

## Cómo se prueba (las reglas de B3c)
- **Servidor:** backend desde este worktree, con una **copia** de la BD en el scratch; las 5 variables `CATDIC_*` apuntan al scratch; puerto **8766**. No cierres el 8765 ni el 8767, nunca uses el 8000 y apágalo al terminar.
- **Dropbox:** nada contra `C:\Users\Steve\CATDIC Dropbox\`.
- **Datos:**
  - la siembra de la BD trae `OT-LEV-001`;
  - añade, **solo en tu copia** y con un script del scratch rotulado como sintético, órdenes en los 6 estados de varias obras y de los 2 tipos;
  - incluye una con `depende_de` y otra con `fecha_comprometida` vacía y no legible;
  - si la restricción `CHECK` de `estado` lo permite en tu copia, incluye una con estado desconocido; si no, pruébalo con una respuesta interceptada en Playwright (`page.route`).
- **Playwright** (Chromium) a 375, 768, 1024, 1280 y 1920 px, en claro y oscuro, sobre `#/ordenes`, con filtros, Inicio, la Bandeja y la pestaña de la obra. Comprueba:
  - 0 peticiones fuera de `127.0.0.1:8766`;
  - 0 errores de consola;
  - sin desplazamiento horizontal de la página;
  - el Atrás y la recarga con filtros y con el estado elegido en móvil;
  - el teclado en el selector de estado;
  - los estados: cargando (GET lento), vacío (0 órdenes), error (500) y estado desconocido.
- **Peor caso:** 300 órdenes, 150 en un solo estado, `doc_id`, `seccion` y `nota` de 200 caracteres, campos nulos y 40 obras en el filtro.
- **Suite del backend** desde `BACKEND/`, dos veces: todo en el scratch, y sin `CATDIC_DROPBOX_RAIZ`. Solo pueden fallar las 2 de Dropbox.
- **Búsqueda final** de «clasico» y «clásico» en `FRONTEND/` (sin `clasico/`, `maquetas/` ni `vendor/`): 0 resultados.

## Informe
`PLANES/etapa-5-reportes/B3f.md` con:
- archivos tocados;
- componentes reutilizados;
- la paridad marcada contra B0 (Z10, Z16 y §9);
- qué queda como Fase D o «pendiente de verificar»;
- qué se sembró;
- la tabla de Playwright;
- los estados;
- el peor caso;
- la suite;
- las limitaciones;
- los hashes;
- la carpeta del scratch con las capturas.
