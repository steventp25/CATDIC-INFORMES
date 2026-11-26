# B3g — Informes dentro de la obra: lista, abrir PDF y «Hacer informe» (encargo del Líder al Ejecutor)

Fecha: 22/11/2026. Va después de B3d. Orden nuevo de B3, decidido por el Director a pedido de Steven: B3a → B3d → **B3g** → B3e → B3b → B3c → B3f.
- Steven, 22/11: «PREPARA CATDIC INFORMES PARA QUE YO PUEDA HACER LOS INFORMES DENTRO DEL PROYECTO».
- Estilo **Plano sellado**: ver `FRONTEND/DESIGN.md`.

## Dónde se trabaja (igual que en B3a y B3d)
- **Worktree y rama:** `C:\Users\Steve\OneDrive\Desktop\CATDIC-WEB\.claude\worktrees\etapa2-t7n-confirmacion-8210cf`, rama `claude/etapa5-fase-b-0020e1`.
  - No crees ni cambies de rama. Nada de push, merge ni stash. No toques el checkout principal.
  - Trabajas por turnos con el Líder.
- **Zona:**
  - `FRONTEND/**` (menos `maquetas/`, `clasico/` y `vendor/`).
  - `PLANES/etapa-5-reportes/B3g.md`.
  - **Excepción de backend que concede el Director, y solo esto:**
    - el módulo nuevo `BACKEND/informes_obra.py`;
    - en `BACKEND/main.py`, solo las dos rutas nuevas de abajo y su `import`;
    - las pruebas nuevas `BACKEND/tests/test_informes_obra.py`.
  - **Prohibido:**
    - tocar `BACKEND/procesador_cola.py`, porque el PR #35 lo cambia;
    - cambiar el esquema de la BD (`database.py`);
    - tocar cualquier otro archivo de `BACKEND/`.
- **Tablero clásico.** Steven, 20/11: «Conserva el tablero clásico. Su eliminación no queda autorizada».
  - No borres ni edites `FRONTEND/clasico/` ni `BACKEND/tests/test_frontend_servido.py`.
  - No reviertas ni amplíes `ddca35f`.
  - Ninguna mención ni enlace al clásico en el tablero nuevo.
- **Python:** `C:\Users\Steve\AppData\Local\Python\pythoncore-3.14-64\python.exe`.

## Reglas (las de B2, B3a y B3d siguen vigentes)
- **Sin red:** sin internet, sin librerías nuevas y sin descargas.
- **Frontend:** sin compilación, con scripts clásicos y `window.CATDIC`. Reutiliza `js/componentes.js`, `C.api`, `C.formato` y `js/datos.js`.
- **Reutiliza el avance en vivo de B3d:** el componente y la ruta del trabajo que describe `PLANES/etapa-5-reportes/B3d.md`. No copies código: si hace falta, extráelo a un componente común y cambia B3d para que lo use.
- **Regla de Oro:**
  - Lo que falte es «pendiente de verificar».
  - Nunca se inventan cifras ni datos de ingeniería.
  - Lo que pide backend nuevo se rotula «Fase D».
- **Formato:** fechas `DD/MM/AAAA`; textos en español.
- **Commits:** atómicos, en español, terminados en `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Nunca capturas, PDFs ni `*.db`.

## Qué hay hoy en el backend (comprobado por el Director en `main`)
- **De dónde salen los informes:** solo del procesador, con `POST /api/visitas/{id}/procesar` (una visita) y `POST /api/visitas/procesar-cola`.
- **Qué genera:** STP-MIVED y FI-01/02/03, según `visitas.formatos_solicitados`. CATDIC-STP está aplazado y los formatos HV no existen.
- **Dónde queda cada PDF:**
  - No hay una tabla de informes.
  - Cada PDF queda en un evento `pdf_generado` de `trabajo_eventos`. Su `datos_json` trae `{visita_id, formato, ruta, con_dudas, bytes}`, y `creado` es la fecha del evento. Mira `procesador_cola.py`, alrededor de la línea 976.
  - También queda en `auditoria`, como `PUBLICAR_PDF`.
- **Qué falta:** no hay ninguna ruta para listar los PDF ni para abrirlos.

## Qué hay que construir

### 1. Backend (excepción del Director)
1. **`BACKEND/informes_obra.py`**, de solo lectura, con `informes_de_obra(proyecto_id)`.
   - Lee los eventos `pdf_generado` y los une a `visitas` por `visita_id`. Solo entran las visitas de esa obra (`visitas.proyecto_id`).
   - Cada informe lleva:
     - `formato`;
     - la visita: `id`, `numero` y `nombre_carpeta`;
     - la fecha del trabajo (el `creado` del evento);
     - `nombre` (el nombre del archivo);
     - `version`: la N del sufijo final ` vN` del nombre (§5.2). Si no hay sufijo, es la primera versión;
     - `bytes`;
     - `con_dudas`;
     - `existe`: si el archivo sigue en disco. **Un archivo que ya no está se marca y no se oculta.**
   - Van ordenados del más nuevo al más viejo.
   - Nunca mueve, borra ni escribe nada.
2. **`GET /api/proyectos/{id}/informes`** en `main.py`. Si la obra no existe, da 404, como las demás rutas de obra.
3. **`GET /api/informes/archivo?ruta=...`**, que abre el PDF en el navegador con `FileResponse`, en línea (`Content-Disposition: inline`).
   - **Solo sirve rutas que aparezcan tal cual en un evento `pdf_generado`.** Cualquier otra ruta da 404, aunque el archivo exista. Así no se pueden pedir rutas libres ni usar `..`.
   - Si la ruta está registrada pero el archivo ya no existe, también da 404, con un `detail` claro.
   - Es de solo lectura.
4. **`BACKEND/tests/test_informes_obra.py`**, con una BD de prueba (`CATDIC_DB_PATH` en `tmp_path`) y PDF sintéticos en `tmp_path`. Toma como modelo la preparación de `tests/test_procesar_cola.py`, pero inserta los eventos directamente, sin lanzar el procesador. Cubre:
   - la lista vacía;
   - el orden del más nuevo al más viejo;
   - la versión leída del nombre;
   - un archivo que ya no existe (`existe: false`, sigue en la lista);
   - una ruta no registrada, que da 404 aunque exista;
   - la ruta registrada cuyo archivo falta, que da 404;
   - la obra ajena, que no se mezcla;
   - la obra inexistente, que da 404.

### 2. Pestaña «Informes» de la obra (`#/obra/<id>/informes`)
- **Lista de informes:**
  - formato, visita (N.º y carpeta), fecha `DD/MM/AAAA HH:MM`, nombre, versión, tamaño legible y «Abrir PDF», que abre `/api/informes/archivo?ruta=…` en una pestaña nueva.
  - **«Con dudas»** con texto e icono, no solo color.
  - **«El archivo ya no está en la carpeta»** cuando `existe` es falso, sin el botón Abrir.
  - Las filas se acomodan a su `.caja` con container queries.
- **Estados con `Bloque`:**
  - cargando;
  - vacío, con el texto exacto «Esta obra todavía no tiene informes generados»;
  - error con «Reintentar».

### 3. «Hacer informe» dentro de la obra
- Un botón en la pestaña Informes abre el flujo, en un diálogo accesible o en la misma pestaña. Usa el patrón de diálogo de B3a.
- **Elegir la visita:**
  - se elige una visita de esa obra y se ven su N.º, carpeta, fecha, estado y los formatos que pide (`formatos_solicitados`);
  - solo se pueden lanzar las visitas que el backend acepta: «Sin procesar», «En cola» y «Con dudas». Las demás se ven, deshabilitadas, con el motivo.
- **Formatos:**
  - los que el sistema genera hoy (STP-MIVED y MIVED FI-01/02/03) se muestran como los que saldrán;
  - CATDIC-STP, HV-LEV, HV-LEVEVAL, HV-LEVEST y HV-INFTEC se muestran como «disponible más adelante», sin simularlos;
  - cambiar los formatos que pide una visita no tiene ruta: se rotula «Fase D».
- **Lanzar:**
  - `POST /api/visitas/{id}/procesar` y, con el trabajo, el avance en vivo de B3d;
  - al terminar, se recarga la lista de informes;
  - los 409 y 404 se muestran con el `detail` del servidor;
  - ningún POST se reintenta solo.

### 4. «Crear informe» (el botón global del riel)
- Lleva a elegir la obra y, después, al mismo flujo «Hacer informe» de esa obra.
- El trabajo independiente, sin obra, sigue siendo Fase D-c y conserva su rótulo.
- En la sección «Informes» de la barra principal basta con un acceso a los informes de cada obra. La vista de todas las obras juntas puede esperar: rotúlala como pendiente.

## Cómo se prueba (las reglas de B3d)
- **Backend:**
  - corre desde este worktree con una **copia** de la BD en el scratch;
  - `CATDIC_DB_PATH`, `CATDIC_DROPBOX_RAIZ`, `CATDIC_DATOS_RAIZ`, `CATDIC_CACHE_RAIZ` y `CATDIC_SALIDA_PRUEBAS` apuntan al scratch;
  - usa el puerto **8766**, nunca el 8765 ni el 8000;
  - apágalo al terminar.
- **Dropbox:**
  - nada contra `C:\Users\Steve\CATDIC Dropbox\`;
  - el procesador escribe en `INFORMES\2.DATA PROCESADA`, así que lanza solo visitas de la carpeta de prueba del scratch (como en B3d) o simula la respuesta con `page.route`, y anótalo.
- **Playwright** (Chromium) a 375, 768, 1024, 1280 y 1920 px, en claro y oscuro, en `#/obra/<id>/informes`, en el flujo «Hacer informe» y en «Crear informe». Comprueba:
  - 0 peticiones fuera de `127.0.0.1:8766`;
  - 0 errores de consola;
  - sin desplazamiento horizontal;
  - el foco en los diálogos;
  - los estados: cargando, vacío, error, 409, archivo que falta y con dudas.
- **Peor caso:** 200 informes, nombres de 150 caracteres y campos nulos. Nada se sale ni se aplasta.
- **Suite del backend** desde `BACKEND/`:
  - solo las 2 fallas de Dropbox;
  - las pruebas nuevas pasan;
  - anota el resultado real.
- **Búsqueda final** de «clasico» y «clásico» en `FRONTEND/` (sin `clasico/`, `maquetas/` ni `vendor/`): 0 resultados.

## Informe
`PLANES/etapa-5-reportes/B3g.md` con:
- archivos tocados, con los del backend aparte;
- las rutas nuevas y su contrato;
- decisiones;
- qué queda como «disponible más adelante» o Fase D;
- cómo aislaste las escrituras;
- la tabla de Playwright;
- los estados;
- el peor caso;
- la suite;
- las limitaciones;
- los hashes;
- la carpeta del scratch con las capturas.
