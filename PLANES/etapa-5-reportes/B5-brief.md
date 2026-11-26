# B5 — Prueba de rotura y cierre de la Fase B — encargo del Líder al Ejecutor

Fecha: 23/11/2026. B4 está aprobada (reauditoría del Director sobre `83d827d`). El Director lanzó B5 el 23/11: «break-ui, teclado, contraste, paridad y cierre, con los 4 abiertos de B4», sin push.

**En B5 no se retira `/clasico`**: Steven no lo autorizó («Conserva el tablero clásico. Su eliminación no queda autorizada», 20/11). B3h sigue sin autorizar.

Va en **dos turnos del mismo Ejecutor**:
- **B5a:** rotura y abiertos.
- **B5b:** teclado, contraste, paridad y cierre.

Al terminar B5a devuelves el informe y paras. El Líder revisa y te manda seguir con B5b.

## Dónde se trabaja (igual que en B4)
- **Worktree y rama:** `C:\Users\Steve\OneDrive\Desktop\CATDIC-WEB\.claude\worktrees\etapa2-t7n-confirmacion-8210cf`, rama `claude/etapa5-fase-b-0020e1`.
  - No crees ni cambies de rama. Nada de push, merge, stash, checkout ni reset. No toques el checkout principal.
  - Trabajas por turnos con el Líder.
- **Zona:** `FRONTEND/**` (menos `maquetas/`, `clasico/` y `vendor/`), `FRONTEND/DESIGN.md`, `PLANES/etapa-5-inventario-ui.md` (solo para marcar el checklist §9 en B5b) y `PLANES/etapa-5-reportes/B5a.md` / `B5b.md`.
  - **Sin excepción de backend: no se toca nada de `BACKEND/`.** Puedes leerlo.
  - Si una rotura solo se arregla en el backend, no la arregles: anótala en el informe como «pide backend» y sigue.
- **Tablero clásico:** no se borra ni se edita `FRONTEND/clasico/` ni `BACKEND/tests/test_frontend_servido.py`. Ninguna mención ni enlace al clásico en el tablero nuevo.
- **Sin red:**
  - nada de librerías nuevas;
  - no ejecutes los scripts de `impeccable` ni nada que descargue o llame a internet;
  - el contraste se mide con tu propio cálculo (fórmula WCAG 2.x), no con una herramienta en línea.
- **Regla de Oro:**
  - los datos extremos son **sintéticos**, solo en tu copia de la BD o en respuestas interceptadas con `page.route`, y rotulados como tales en el script;
  - nunca se añade al tablero un interruptor de «datos de prueba»;
  - lo que falta sigue siendo «pendiente de verificar», y nunca «0 %».
- **Python:** `C:\Users\Steve\AppData\Local\Python\pythoncore-3.14-64\python.exe`.

## B5a — Rotura y abiertos

### 1. Prueba de rotura (`break-ui`)
- Lee `C:\Users\Steve\.claude\skills\break-ui\SKILL.md` y `CATALOG.md` (o cárgala con la herramienta Skill).
- Su «Demo data / Worst case toggle» **no** se construye en el tablero: los datos extremos van en la BD copia o con `page.route`.

Casos mínimos (del plan madre), en todas las pantallas donde aplique (Inicio, Mis obras, la obra con sus 6 pestañas, la Bandeja, la Mesa de Dudas, las Órdenes, Informes, Crear informe, Confirmar datos del plano, el visor y el editor):
- nombres de obra larguísimos (200 caracteres, con y sin espacios), y de una letra;
- obra con **0 visitas**, 0 planos, 0 informes y 0 órdenes;
- **500 dudas** abiertas en una obra (Mesa por obra y Bandeja);
- IDs y ejes con prima: `A'`, `2'`, `EJE A'-1`, y la prima tipográfica `’`;
- todos los campos en «pendiente de verificar» (null o vacío);
- textos no latinos y emoji en notas y respuestas;
- cifras extremas (visita n.º 9999, 10 000 elementos);
- fechas no legibles;
- el peor caso de órdenes de B3f (300 órdenes, 150 en un estado), para ver si hace falta virtualizar o basta con lo que hay. Decide y justifica: si la pantalla responde en menos de ~1 s y no se cuelga, no se virtualiza.

Cada rotura encontrada:
- se arregla en `FRONTEND/`, en un commit propio o agrupado por pantalla;
- va al informe con su captura antes y después (las capturas quedan en el scratch, nunca en git).

### 2. Abiertos de B4 (los 4 obligatorios)
1. **Salida de los diálogos.**
   - Hoy es instantánea, porque el padre los desmonta al emitir `cerrar`.
   - Decide con `emil-design-eng`: una salida corta (~150 ms, fundido y `scale(0.97)`) que no retrase el foco ni deje el diálogo «a medias» si se vuelve a abrir enseguida, o dejarla instantánea.
   - Justifícalo en el informe. Con movimiento reducido, la salida es instantánea.
2. **Avisos que empujan lo de debajo.**
   - Reserva su sitio o colócalos de forma que no desplacen el contenido que el usuario está mirando.
   - Mide con `getBoundingClientRect` que lo de debajo no salta.
3. **Escape en Confirmar plano.** Devuelve el foco al elemento que abrió el diálogo, no al `<h1>`, y en las demás entradas del diálogo lo mismo (abrir desde «Planos y ficha», desde la Mesa y al recargar con `?confirmar=1`). Al recargar no hay disparador: el foco va al `<h1>`, como ahora.
4. **Motivo de «Ir al recuadro» deshabilitado.** Hoy solo lo tienen los lectores de pantalla y el `title`. Hazlo visible: una ayuda corta junto al botón o debajo, **sin** que la barra vuelva a pasar a dos líneas a 800 px (lo que corrigió la nota 8 de B4).

### 3. Otros abiertos de B3 que entran aquí
- **B3c:** una `&tabla=` desconocida vuelve a la lista sin avisar. Muestra un aviso corto («La tabla N no existe en esta extracción») y la lista.
- **B3b:** el dibujo de recuadros no tiene equivalente de teclado. No lo construyas: confirma que «Proponer» y «Usar propuesta» se alcanzan con Tab y lo cubren, y anótalo.

### Informe B5a
`PLANES/etapa-5-reportes/B5a.md` con:
- los casos probados por pantalla;
- cada rotura (qué, dónde, causa, arreglo, hash);
- lo que «pide backend»;
- los 4 abiertos de B4 y los 2 de B3, uno por uno, con su comprobación;
- la decisión sobre la virtualización;
- la tabla de Playwright;
- la suite;
- los hashes;
- la carpeta del scratch.

## B5b — Teclado, contraste, paridad y cierre (solo cuando el Líder lo diga)

### 1. Teclado
- Recorre con Tab y Mayús+Tab **todas** las pantallas y diálogos, a 1280 y a 375:
  - el orden sigue la lectura;
  - el foco siempre es visible y nunca queda detrás de la barra fija móvil ni de un diálogo;
  - en un diálogo abierto, Tab no sale de él;
  - Escape cierra y devuelve el foco;
  - Enter y Espacio activan;
  - las pestañas (de la obra y de las órdenes) se mueven con las flechas;
  - «Saltar al contenido» funciona.
- Haz una tabla por pantalla: qué se probó, OK o arreglado.

### 2. Contraste
- Calcula la razón de contraste WCAG de cada par de tokens de `css/tokens.css` que se usa como texto sobre fondo, y de los estados (`--alerta`, `--ok-tinta`, `--pend-*`, `--fased-*`, `--nuevo-*`, enlaces, foco) en claro y en oscuro:
  - texto normal: 4.5:1 o más;
  - texto grande y bordes de controles: 3:1 o más.
- Además, con Playwright, mide los colores **calculados** de una muestra de elementos reales en cada pantalla, en los dos temas.
- Lo que no llegue se corrige en los tokens, sin cambiar la dirección «Plano sellado», y va a una tabla del informe.
- Actualiza la sección **Accesibilidad** de `DESIGN.md` («Se mide en B5» pasa a las cifras medidas).

### 3. Paridad con B0 y criterios nuevos
- Marca el checklist **§9** de `PLANES/etapa-5-inventario-ui.md`, ítem por ítem: `[x]` con dónde está en el tablero nuevo (pantalla y gancho), o `[ ]` con el motivo.
- Revisa también los criterios nuevos de **§10**: las necesidades que piden backend se marcan «Fase D», no se simulan.
- **Lo que no se marca:** cualquier cosa que solo exista en el clásico y falte en el tablero nuevo se anota como hueco y no se marca. El clásico no se borra.

### 4. Matriz final
Playwright a 375, 768, 1024, 1280 y 1920 px, en claro y oscuro, en todas las rutas del tablero, con y sin movimiento reducido. Comprueba:
- 0 peticiones fuera de `127.0.0.1:8766`;
- 0 errores de consola;
- sin desplazamiento horizontal de la página;
- ningún «0 %»;
- ninguna mención al clásico.

Haz además una pasada de los scripts de revisión del Líder de B3b, B3c, B3f y B4 del scratch, que deben seguir en 0 fallas.

### 5. Suite y búsquedas
- **Suite del backend** desde `BACKEND/`, dos veces: todo en el scratch, y sin `CATDIC_DROPBOX_RAIZ`. Solo pueden fallar las 2 de Dropbox.
- **Búsquedas** en `FRONTEND/` (sin `clasico/`, `maquetas/` ni `vendor/`), todas con 0 resultados:
  - «clasico» y «clásico»;
  - `transition: all`;
  - `ease-in` (sin `-out`);
  - URL `http(s)://` que no sean del propio servidor;
  - «0 %».

### Informe B5b
`PLANES/etapa-5-reportes/B5b.md` con:
- la tabla de teclado;
- la tabla de contraste (par, razón, claro y oscuro, corregido sí o no);
- el resumen del checklist §9 (marcados, huecos con motivo) y §10;
- la matriz final;
- la suite;
- las búsquedas;
- las limitaciones;
- los hashes;
- la carpeta del scratch.

## Cómo se prueba (las reglas de B4)
- **Servidor:**
  - backend desde este worktree, con una **copia** de la BD en `C:\WINDOWS\TEMP\claude\5241ace622d5cd23\bde6ad2c-34d6-42aa-bdc5-6b0fd7ef0f32\scratchpad\b5\`;
  - parte de `scratchpad\b4\copia.db`, que ya tiene órdenes sintéticas y la obra sintética de B3c;
  - las 5 variables `CATDIC_*` apuntan al scratch;
  - puerto **8766**: no cierres el 8765 ni el 8767, nunca uses el 8000, y apaga tu servidor al terminar cada turno.
- **Dropbox:** nada contra `C:\Users\Steve\CATDIC Dropbox\`.

## Commits
- Atómicos, en español, terminados en `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Nunca capturas, PDFs ni `*.db`.
- Al terminar cada turno, el árbol queda limpio, todo commiteado y sin procesos tuyos vivos.
