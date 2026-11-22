# B3d — Visitas y trabajos: cola, Procesar cola, Sincronizar, subir visita y avance en vivo (encargo del Líder al Ejecutor)

Fecha: 19/11/2026. Va después de B3a: el orden de B3 está en `PLANES/etapa-5-fase-B.md`. Estilo **Plano sellado**: ver `FRONTEND/DESIGN.md`.

**Por qué es urgente.** Steven no quiere volver a ver el tablero clásico. Esta tarea trae al tablero nuevo lo que hoy solo hace el clásico con las visitas. Al terminar, nada de esto puede faltar.

## Novedades del 22/11/2026 (reanudación; mandan sobre lo de abajo)
- **Se reanuda la fase.** Steven, 22/11: «Sí, reanúdala».
- **Tablero clásico.** Steven, 20/11: «Conserva el tablero clásico. Su eliminación no queda autorizada».
  - No borres ni edites `FRONTEND/clasico/` ni su prueba (`BACKEND/tests/test_frontend_servido.py`).
  - Lo que hizo `ddca35f` (quitar los enlaces al clásico) queda como está: no lo reviertas ni lo amplíes.
  - Sigue sin haber enlaces ni menciones al clásico en el tablero nuevo.
- **Paquete de CATDIC Campo** (PR #35, rama `claude/paquete-visita-campo`, aún sin fusionar).
  - Añade `*.catdic-visita.json`: cuando la carpeta de una visita lo trae, Procesar cola lo carga en vez del PDF. El contrato está en `PLANES/paquete-visita-v1.md` de esa rama.
  - **En B3d no construyas nada para el paquete.** No lo detectes, no lo simules y no lo leas desde el frontend.
  - En el informe, anota **dónde iría en la cola el aviso «esta visita trae paquete de Campo»**: qué componente, qué columna o línea y qué dato del backend haría falta. Es para una tarea posterior.
- **Puerto.** El 8765 está ocupado por otro proceso que no es tuyo (puede ser la demo de B3a): **no lo cierres**. Usa el **8766**. Donde abajo dice 8765, léelo como 8766, también en el filtro de peticiones de Playwright.

## Dónde se trabaja (igual que en B2 y B3a)
- **Worktree y rama:** `C:\Users\Steve\OneDrive\Desktop\CATDIC-WEB\.claude\worktrees\etapa2-t7n-confirmacion-8210cf`, rama `claude/etapa5-fase-b-0020e1`.
  - No crees ni cambies de rama. Nada de push, merge ni stash.
  - Trabajas por turnos con el Líder.
- **Zona:** `FRONTEND/**` y `PLANES/etapa-5-reportes/B3d.md`.
  - No toques `FRONTEND/maquetas/`, `FRONTEND/clasico/`, `FRONTEND/vendor/` ni `BACKEND/**`. El backend se lee, no se edita.
  - **Ningún enlace ni mención al tablero clásico** (decisión de Steven, 19/11). `clasico/index.html` solo se lee como referencia de paridad.
- **Python:** `C:\Users\Steve\AppData\Local\Python\pythoncore-3.14-64\python.exe`.

## Reglas (las de B2 y B3a siguen vigentes)
- Sin internet ni librerías nuevas. Sin compilación, con scripts clásicos y `window.CATDIC`.
- Usa lo que ya hay en `js/componentes.js` (`Bloque`, `Pendiente`, `FaseD`, `Icono`, `Cajetin`), `C.formato`, `C.api` y el módulo de datos de B3a, si existe.
- Lo que falte es «pendiente de verificar». Nunca se inventan cifras ni datos de ingeniería. Lo que pide backend nuevo se rotula «Fase D».
- Fechas `DD/MM/AAAA`, textos en español.
- Commits atómicos en español, terminados en `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Nunca capturas, PDFs ni `*.db`.

## Qué hay que construir
Lugar decidido por el Director (19/11):
- **Inicio:** un bloque «Cola de visitas» con Procesar cola y Sincronizar desde Dropbox.
- **Bandeja de trabajo:** la cola de todas las obras.
- **Cada obra:** su cola, en la pestaña «Visitas y trabajos».
- **Condición:** el bloque de Inicio enlaza a la vista completa de la Bandeja. **Una sola lista**: Inicio solo muestra el resumen y los botones, sin una segunda tabla que pueda desincronizarse.

Paridad que tiene que quedar cubierta, todo en `PLANES/etapa-5-inventario-ui.md`:

| Pieza | Referencia en el inventario |
|---|---|
| Procesar cola y su seguimiento | A3, A5, A9, Z3 |
| Sincronizar desde Dropbox y su resultado | A2, A7, A8, Z5, Z8 |
| Cola de visitas | Z15, con su tabla de columnas, el orden `visitasOrdenadas` y los textos de vacío de §4 |
| Subir visita y conectar Dropbox | M3, A31–A33, Z4, A6, A19 |
| Lista de paridad | §9, ítems de «Cabecera y avisos» y de «Tarjetas y tablas» que tocan la cola y la sincronización |

1. **Componente de cola** (Z15), uno solo y reutilizable. En la Bandeja muestra todas las obras; en «Visitas y trabajos», una sola obra.
   - Contador «N visitas · M con dudas».
   - Columnas Obra, N.º, Carpeta, Fecha, Clase y Estado, más el detalle de Clase «Mixta».
   - Las líneas de dudas bloqueantes y abiertas, y la de «Pendiente: …».
   - La fila con dudas resaltada, sin depender solo del color.
   - En pantallas estrechas, las filas se acomodan a su `.caja` con container queries.
   - **Clic en una visita con dudas:** hoy abre la Mesa de Dudas, que construye B3e. En B3d deja un enlace estable a `#/obra/<id>/visitas?visita=<vid>` (o el mecanismo que dejó B3a) para que B3e lo conecte. Mientras tanto, no simules la Mesa: muestra «Mesa de Dudas: la construye B3e».
   - En la Bandeja, una cabecera clara «Cola de visitas (todas las obras)». El resto de la Bandeja, que es la ruta común, sigue siendo Fase D-a y conserva su aviso.
2. **Procesar cola** (A3/A9), en Inicio y también por obra en «Visitas y trabajos». Por obra se llama `POST /api/visitas/procesar-cola?proyecto_id=<id>`; lee `BACKEND/main.py`.
   - Botón deshabilitado y «Procesando…» mientras corre.
   - Si la respuesta no trae `trabajo`, se muestra `mensaje`.
   - Con trabajo, se sigue cada 2 s con `GET /api/trabajos/{id}` hasta que termina. Al salir de la pantalla se cancela con `AbortController`/`clearTimeout`, sin fugas.
   - Al terminar se recargan el tablero y las dudas.
   - Los errores 409 (trabajo en curso, visita no procesable) se muestran con el `detail` del servidor.
3. **Avance en vivo del procesador** (cubre la parte que se puede de T10b, Etapa 3).
   - Lee `GET /api/trabajos/{id}/eventos?desde=<n>` (`BACKEND/main.py` y `BACKEND/procesador_cola.py`, `listar_eventos` y los `_evento(...)`). Muestra el avance elemento por elemento: `visita_inicio`, `elemento_inicio`, `elemento_listo`, `duda`, `aviso`, `pdf_generado`, `visita_fin` y `fin`.
   - Cada duda aparece cuando surge, con un enlace a su visita.
   - Se puede cerrar y volver a abrir sin perder el trabajo; la ruta lleva el id del trabajo.
   - **Fuera de B3d, y así se anota en el informe:** responder la duda dentro de la pantalla en vivo llega con la Mesa de B3e; el visor del plano junto a cada duda llega con B3b. No lo simules.
4. **Sincronizar desde Dropbox** (A2), en Inicio.
   - Estado «Sincronizando…» y botón deshabilitado.
   - El resultado completo de Z8: hora `DD/MM/AAAA HH:MM`; por obra, el layout, los 7 contadores, los avisos, las carpetas desaparecidas, las omitidas y las dudas creadas; los planos sellados en `title`.
   - El error Z5 se puede cerrar.
5. **Subir visita y Conectar con Dropbox** (M3), en «Visitas y trabajos», solo en obras de Supervisión.
   - Diálogo accesible: foco atrapado, Escape y foco de vuelta. Reutiliza el patrón del diálogo de Nueva obra de B3a.
   - Los campos, validaciones y mensajes exactos de A31–A33.
   - Al terminar, el resultado Z4 y un enlace a las dudas de la visita para B3e.
   - Con `C.api.enviarFormulario` y `C.api.post`. Ningún POST se reintenta solo.

## Cómo se prueba (obligatorio, con cuidado especial)
- **El backend corre desde este worktree con una copia de la BD**, nunca la real.
  - `CATDIC_DB_PATH` apunta a la copia; el puerto es el 8765, nunca el 8000.
  - Apaga el servidor al terminar.
- **Procesar, sincronizar y subir escriben en disco.** Antes de lanzarlos, lee `BACKEND/config.py`: `CATDIC_DROPBOX_RAIZ`, `CATDIC_DATOS_RAIZ`, `CATDIC_CACHE_RAIZ` y `CATDIC_SALIDA_PRUEBAS`.
  - Las cuatro apuntan al scratch.
  - Para Dropbox, prepara en el scratch una carpeta de prueba pequeña con la estructura que espera el escáner. Mira cómo lo hacen las pruebas de `BACKEND/tests/`.
  - **Nunca** se ejecuta contra `C:\Users\Steve\CATDIC Dropbox\`: el procesador escribe informes en `INFORMES\2.DATA PROCESADA`.
  - Si no puedes aislar un paso, no lo ejecutes: pruébalo con `page.route` (respuestas simuladas solo en la prueba) y anótalo.
- **Playwright** (Chromium) a 375, 768, 1024, 1280 y 1920 px, en claro y oscuro, en Inicio, la Bandeja y `#/obra/<id>/visitas`. Comprueba:
  - 0 peticiones fuera de `127.0.0.1:8765`;
  - 0 errores de consola;
  - sin desplazamiento horizontal;
  - el foco en los diálogos;
  - el polling que se detiene al terminar y al salir de la pantalla (cuenta las peticiones);
  - los estados cargando, vacío (con sus dos textos), error, 409 y trabajo fallido.
- **Peor caso:** 300 visitas, carpetas de 150 caracteres, campos nulos y 40 dudas en una visita. Nada se sale ni se aplasta.
- **Suite del backend** desde `BACKEND/`: solo las 2 fallas de Dropbox. Anota el resultado real.
- **Búsqueda final** de «clasico» y «clásico» en `FRONTEND/` (sin `clasico/`, `maquetas/` ni `vendor/`): 0 resultados.

## Informe
`PLANES/etapa-5-reportes/B3d.md` con:
- archivos tocados;
- decisiones;
- qué ítems de §9 quedan cubiertos (y cuáles no, y por qué);
- qué partes de T10b se cumplen y cuáles esperan a B3e o B3b;
- cómo aislaste las escrituras;
- la tabla de Playwright;
- los estados;
- el peor caso;
- la suite;
- las limitaciones;
- los hashes;
- la carpeta del scratch con las capturas.
