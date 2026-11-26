# B5a · Prueba de rotura y abiertos (Etapa 5 · Fase B)

Ejecutor: Sonnet 5.5. Rama `claude/etapa5-fase-b-0020e1`. Solo `FRONTEND/` y este informe. Nada en `BACKEND/`, `clasico/`, `maquetas/` ni `vendor/`.

## Cómo se probó
- Servidor 8766 desde este worktree, con una copia de la BD en el scratch (`b5\copia.db`, salida de `b4\copia.db`). Todo apagado al terminar.
- Los datos extremos son **sintéticos** y están solo en esa copia (`b5\sembrar.py`, rotulado como tal) o en respuestas interceptadas con `page.route` (`fechas.py`, `editor10k.py`). El tablero no tiene ningún interruptor de datos de prueba.
- Obras sintéticas (`x-…`): nombre de 200 caracteres sin espacios y con espacios, nombre de una letra (`Q`), obra vacía (0 visitas, planos, informes y órdenes), obra con 500 dudas abiertas (250 con visita, 250 sin visita), obra con la visita n.º 9999 y 10 000 elementos de diseño, obra con todo «pendiente de verificar» (incluida una duda sin texto, sin campo y sin elemento), obra con primas (`A'`, `2'`, `EJE A'-1`, `A’`), obra con texto chino, árabe, cirílico y emoji, obra con «uno de cada» (plurales). Además 300 órdenes (150 en «Pendiente»), con textos largos, fechas `mañana`, `31/02/2026` y emoji. Las obras sintéticas de B3c y B3e se renombraron con los nombres largos para probar Confirmar plano, el visor y el editor.

## Casos probados por pantalla (375 y 1280 px, claro)
| Pantalla | Casos | Resultado |
|---|---|---|
| Inicio | 9 obras extremas, 500 dudas, 285 órdenes abiertas | OK. Prioridades limitadas; el nombre largo parte en líneas, sin desborde |
| Mis obras | nombres de 200 y de 1 carácter, unicode | OK |
| Obra, 6 pestañas | las 9 obras extremas × 6 pestañas (54 rutas × 2 anchos) | OK: sin desborde horizontal, sin errores de consola, sin `NaN`/`undefined`/`null`/«0 %» en el texto |
| Bandeja | 500 dudas, visita 9999, visitas «pendiente de verificar» | OK |
| Mesa de Dudas | 500 dudas (modo visita y modo obra), primas, unicode, todo pendiente | **1 rotura** (tarjeta en blanco), arreglada |
| Órdenes | 312 órdenes, filtros, fechas imposibles | OK; ver decisión de virtualización |
| Informes / Crear informe | obras de nombre largo | OK |
| Diálogos (Nueva obra, Subir visita, Hacer informe, Datos de la obra) | nombre de 200 caracteres | **1 rotura** (título de 9 líneas), arreglada |
| Confirmar datos del plano | nombre largo; `&tabla=` 999, `abc`, `0`, `-1`, `2x` | **1 rotura** (título), arreglada; el aviso de tabla desconocida ya existía y se afinó |
| Visor y editor de recuadros | nombre largo; 10 000 elementos y ids con prima, emoji y 80 caracteres por `page.route` | OK: abre en unos 0,6 s y elegir un elemento tarda ≈ 0,5 s |
| Fechas ilegibles | `2026-13-45`, `mañana`, `31/02/2026`, `2026-02-30T10:00`, null y vacío en visitas, órdenes, obras, informes y planos (`page.route`) | **1 rotura** (fecha imposible mostrada como fecha), arreglada |
| Plurales y cifras | 1 visita, 1 duda, 1 orden; 0; 9999; 10 000 | OK: «1 visita», sin «1 visitas» |

## Roturas encontradas y arregladas
| # | Qué | Dónde | Causa | Arreglo | Hash |
|---|---|---|---|---|---|
| 1 | `2026-13-45` se mostraba como «45/13/2026» y `31/02/2026` pasaba tal cual | todas las fechas (`C.formato.fecha` y `fechaHora`) | solo validaban la forma, no que el día exista | se valida contra el calendario; si no existe, no es fecha y la pantalla muestra «pendiente de verificar» (con el texto crudo al lado en Órdenes) | `fa7a8a6` |
| 2 | Un nombre de obra de 200 caracteres ocupaba 9 líneas en el título de los diálogos y empujaba el formulario | Subir visita, Conectar, Hacer informe, Planos, Confirmar plano, visor | título sin límite de líneas | clase `.nombre-largo`: tres líneas y el resto en `title`; el nombre entero sigue en la pantalla de la obra | `7747dff` |
| 3 | Una duda con texto, campo y elemento vacíos salía como una tarjeta en blanco | Mesa de Dudas (lista y detalle) | la plantilla pintaba el campo vacío tal cual | «pendiente de verificar» (componente `Pendiente`) en pregunta y en campo | `8950114` |

Capturas (en el scratch, nunca en git):
- Roturas 2: antes `capturas\d-375-dlg-Subirvisita.png`, después `capturas\e-375-dlg-Subirvisita.png`; también `d-` y `e-375-confirmar.png`.
- Rotura 3: antes `capturas\e-375-mesa-pend.png`, después `capturas\h-375-obra_x-pend_visitas_visitax-pend-v1.png`.
- Rotura 1: se comprobó con `fechas.py` (texto de las pantallas) y no tiene captura propia: el «antes» es el comportamiento de la función, visible en el código.

## Lo que «pide backend»
Nada nuevo. Observaciones (no bloquean):
- La BD solo admite `AAAA-MM-DD` o «pendiente de verificar» en `fecha_visita` (CHECK), así que una fecha de visita ilegible solo puede llegar por `fecha_comprometida` u otros campos libres; el tablero ya las trata.
- No hay límite de longitud en `proyectos.nombre`: el tablero lo soporta, pero el backend podría fijar uno si Steven quiere.

## Los 4 abiertos de B4
1. **Salida de los diálogos: se queda instantánea (decisión).**
   - Motivo con `emil-design-eng`: una salida de ~150 ms obligaría a retrasar el desmontaje del componente o el foco. Un clic rápido en el disparador durante ese tiempo dejaría un diálogo a medias, justo lo que se quiere evitar.
   - Son controles que se abren y cierran muchas veces al día: lo inmediato se siente más rápido que la salida más fina. La entrada de 200 ms ya explica de dónde viene el diálogo.
   - Comprobado: Escape cierra y el foco vuelve en el mismo cuadro; abrir y cerrar enseguida deja 0 diálogos a medias (`b_mov.py`). Con movimiento reducido no hay diferencia.
   - Va a `DESIGN.md` («Qué no se anima»).
2. **Avisos que empujan: arreglado en los de una línea** (`c1a1058`). Mesa de Dudas, Confirmar plano y Datos de la obra tienen sitio reservado (`.sitio-aviso`, `.conf-msgs`).
   Empuje medido con `getBoundingClientRect` (se oculta el aviso y se compara la posición del siguiente bloque):
   | Aviso | Antes (1280) | Después |
   |---|---|---|
   | Mesa de Dudas (guardar respuesta) | 72,5 px | 0,5 px |
   | Datos de la obra (guardar) | 47 px | 0,6 px |
   | Confirmar plano (extraer) | 48,5 px | 0,5 px |
   - Si el texto ocupa varias líneas (a 800 px, 2; a 375 px, 3) empuja solo el exceso: 23 px y 68 px en Confirmar plano.
   - **Sin cambio:** los paneles de resultado de varias líneas de la cola (error al procesar, resultado de sincronizar, trabajo, regeneración) y el aviso tras subir planos. Empujan unos 100 px lo que está debajo (en Inicio, la rejilla). Reservarles sitio dejaría un hueco de ~100 px permanente en Inicio, y superponerlos taparía contenido. Los botones que los disparan no se mueven (`b_mov.py`). Queda a decisión del Líder.
   - El aviso del editor de recuadros es el último hijo del panel: no empuja nada.
3. **Escape en Confirmar plano: arreglado** (`44718fc`).
   | Entrada | Escape deja el foco en |
   |---|---|
   | Enlace de «Planos y ficha», con clic | el enlace (ya era así) |
   | El mismo enlace, con Enter | el enlace (ya era así) |
   | Botón «Cerrar» | el enlace (ya era así) |
   | Volver con Atrás desde la Mesa | antes: `<body>`; ahora: el enlace |
   | Recargar con `?confirmar=1` | antes: `<body>`; ahora: el `<h1>` |
   - Nota: lo de B4 («Escape lleva el foco al `<h1>`») no se reprodujo en las dos primeras entradas; lo que fallaba de verdad eran las dos últimas, donde el foco caía en el `<body>`.
4. **Motivo de «Ir al recuadro» deshabilitado: ahora es visible** (`c834471`).
   - Texto corto «Dibuja uno primero» bajo el botón; el motivo completo sigue para lectores de pantalla.
   - El sitio se reserva siempre (con o sin recuadro). La barra mide lo mismo en las dos situaciones: 289 / 130 / 126 / 77 px a 375 / 800 / 1024 / 1280. A 800 px la barra sigue en 130, como en B4.

## Los 2 abiertos de B3
- **B3c, `&tabla=` desconocida:** el aviso ya existía y no se había perdido. Se cambió el texto a «La tabla 999 no existe en esta extracción. Se muestra la lista de tablas.» (para un valor no numérico, «La tabla «abc» …»). Probado con 999, `abc`, 0, -1 y `2x`: la dirección vuelve a `?confirmar=1` y se ve la lista (`012a79e`).
- **B3b, dibujo sin teclado:** no se construye. Comprobado con Tab: elegir elemento con las flechas, Tab llega a «Proponer recuadros», Enter, y Tab llega a «Usar propuesta» (con dos botones, uno por tipo). Los dos se alcanzan y cubren la función.

## Decisión sobre la virtualización de Órdenes: no se virtualiza
312 órdenes, 150 en «Pendiente»: 9 641 nodos en el DOM.
| Medida | Normal | CPU ×4 más lenta |
|---|---|---|
| Entrar a la pantalla | 0,15–0,20 s | 0,93–1,04 s |
| Filtrar por una obra | 0,05–0,08 s | 0,34–0,36 s |
| Quitar el filtro | 0,11–0,14 s | 0,64–0,74 s |
Responde en menos de ~1 s incluso con la CPU frenada 4 veces y no se cuelga. Virtualizar añadiría accesibilidad y búsqueda del navegador rotas para un caso 25 veces mayor al real (12 órdenes).

## Playwright
| Prueba | Resultado |
|---|---|
| Exploración: 67 rutas con obras extremas × 375 y 1280 (134 visitas) | 0 desbordes, 0 errores de consola, 0 `NaN`/`undefined`/`null`/«0 %»; se repitió tras el último arreglo |
| Diálogos y pantallas completas con nombre largo a 375 y 1280 (`dlg.py`) | OK, sin desborde de página |
| Fechas ilegibles por `page.route` en 10 rutas × 2 anchos | OK |
| Editor con 10 000 elementos sintéticos | OK, 0 errores |
| Matriz B4 (14 rutas × 5 anchos × claro/oscuro × normal/reducido = 280) | 0 fallos; 0 errores de consola; 0 peticiones externas; sin scroll horizontal |
| Movimiento normal y reducido (`b_mov.py`) | 0 fallos (el 500 de procesar-cola es el simulado) |
| Notas 1–9 de B4 (`c_notas.py`) | 0 fallos |
| Visor (`d_visor.py`) | 1 «fallo» conocido del script (bordes desglosados de la orden destino), ya explicado en B4; no es del producto |
| Salto de avisos, Escape, barra del visor, tabla desconocida, Tab en B3b | OK (tablas de arriba) |

## Suite del backend
Desde `BACKEND/`, todo en el scratch:
- Con `CATDIC_DROPBOX_RAIZ` apuntando al scratch: 975 pasan, 7 omitidas, 0 fallos.
- Sin `CATDIC_DROPBOX_RAIZ`: 977 pasan, 3 omitidas, 2 fallos, los 2 de Dropbox (`test_terra_living_real` y `test_lista_coincide_con_dropbox_si_esta_disponible`). Igual que en B4.

## Limitaciones y dudas
- Los paneles de resultado de varias líneas de la cola siguen empujando lo de debajo (ver abierto 2).
- Con 3 líneas de aviso a 375 px, Confirmar plano se corre el exceso (68 px).
- `DESIGN.md` recoge la decisión de la salida de los diálogos y los sitios de aviso (ya en la rama). La sección Accesibilidad sigue «Se mide en B5»: se cierra en B5b.
- No se probó nada contra Dropbox ni contra el puerto 8000.

## Hashes
`fa7a8a6` fechas · `7747dff` títulos de diálogos · `c1a1058` sitios de aviso · `44718fc` foco de Confirmar plano · `c834471` motivo de «Ir al recuadro» · `012a79e` tabla desconocida · `8950114` Mesa con campos vacíos (incluye los cambios de `DESIGN.md`) · y el commit de este informe.

## Scratch
`C:\WINDOWS\TEMP\claude\5241ace622d5cd23\bde6ad2c-34d6-42aa-bdc5-6b0fd7ef0f32\scratchpad\b5\` (scripts, `capturas\`, `copia.db`, suites).
