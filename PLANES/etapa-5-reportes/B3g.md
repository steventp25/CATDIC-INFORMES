# B3g — Informes dentro de la obra: informe del Ejecutor (22/11/2026)

Rama `claude/etapa5-fase-b-0020e1`. Encargo: `B3g-brief.md`.

## Commits
- `a87738d` backend: rutas de solo lectura para listar y abrir los informes.
- `5d03273` el avance en vivo pasa a un componente común (`AvanceTrabajo`).
- `30ad788` pestaña Informes, diálogo «Hacer informe», «Crear informe» e «Informes».
(El hash del commit del informe va en la respuesta al Líder.)

## Archivos tocados
**Backend (excepción del Director)**
- `BACKEND/informes_obra.py` (nuevo, solo lectura).
- `BACKEND/main.py`: solo el import de `informes_obra` y `FileResponse`, y las 2 rutas nuevas.
- `BACKEND/tests/test_informes_obra.py` (nuevo, 11 pruebas).

**Frontend**
- Nuevos: `js/avance-trabajo.js`, `js/pestana-informes.js`, `js/formulario-informe.js`, `js/elegir-obra.js`.
- Modificados: `js/pantallas/trabajo.js` (ahora solo cabecera + `AvanceTrabajo`), `js/pantallas/obra.js`, `js/pantallas/informes.js`, `js/pantallas/crear-informe.js`, `js/iconos.js` (icono `externo`), `index.html`, `css/base.css`.
- `procesador_cola.py`, `database.py` y el resto de `BACKEND/` no se tocaron. No se tocó `clasico/` ni `test_frontend_servido.py`.

## Rutas nuevas
- `GET /api/proyectos/{id}/informes` → `{"informes": [...]}`, del más nuevo al más viejo (por `creado` del evento). Obra inexistente: 404 «Proyecto no encontrado.». Cada informe:
  `formato`, `visita {id, numero, nombre_carpeta}`, `trabajo_id`, `fecha` (el `creado` del evento), `nombre`, `version` (N del sufijo final ` vN`, 1 si no hay), `bytes`, `con_dudas`, `existe` (el archivo sigue en disco; si no, se marca y no se oculta), `ruta` (la registrada en el evento).
  Solo entran eventos `pdf_generado` cuya visita pertenece a la obra.
- `GET /api/informes/archivo?ruta=...` → el PDF en línea (`Content-Disposition: inline`, `application/pdf`). Solo sirve rutas idénticas, carácter por carácter, a la de un evento `pdf_generado`; cualquier otra (exista o no el archivo, con `..`, otra mayúscula, vacía, la BD) da 404. Ruta registrada pero archivo ausente: 404 «El archivo de este informe ya no está en la carpeta.».
- Nada escribe, mueve ni borra (hay una prueba que compara BD y carpeta antes y después).

## Decisiones
- **Avance en vivo:** se extrajo `AvanceTrabajo` (prop `trabajoId`, emite `terminado`). La pantalla `#/trabajo/<id>` lo usa igual que antes y la pestaña Informes lo muestra en línea, sin diálogo abierto, para poder seguir leyendo la lista. Cada PDF del avance gana «Abrir PDF».
- **Flujo:** el diálogo solo elige visita y formatos y lanza; al lanzar se cierra y el avance queda en la pestaña. Un trabajo corriendo de esta obra se retoma al recargar. Mientras corre, «Hacer informe» está deshabilitado con el motivo escrito. Al terminar se relee la lista y el tablero.
- **Crear informe:** `#/crear-informe` lista las obras; «Hacer informe» lleva a `#/obra/<id>/informes?hacer=1`, que abre el diálogo y deja la URL limpia. «Informes» de la barra principal lista las obras con acceso a su pestaña.
- **Estado y énfasis:** «Con dudas» y «archivo ya no está» van con icono, texto y borde completo (sin franjas laterales).
- Lo que falta (nombre, tamaño, fecha, número, carpeta, formatos) se muestra «pendiente de verificar».

## «Disponible más adelante» y Fase D
- Disponible más adelante: CATDIC-STP, HV-LEV, HV-LEVEVAL, HV-LEVEST, HV-INFTEC (en el diálogo, y en las obras de Levantamiento, que no tienen «Hacer informe»).
- Fase D: cambiar los formatos que pide una visita (no hay ruta). Fase D-c: informe independiente sin obra. Pendiente (rotulado): vista de todos los informes de todas las obras juntas.

## Aislamiento de escrituras
- Servidor en el puerto 8766 desde el worktree, con copia de la BD en el scratch y las 5 variables `CATDIC_*` apuntando al scratch. Nada contra `C:\Users\Steve\CATDIC Dropbox\`.
- Los PDF de la lista son sintéticos, sembrados en el scratch con eventos escritos directamente en la copia de la BD. El lanzamiento real fue sobre la visita 9 de Terra Living de la copia: el procesador terminó con 3 dudas (cabecera incompleta, dos PDF en la carpeta, sin elementos) y 0 PDF, y todo se escribió en el scratch. Los 409 y 404 se simularon con `page.route` (el 409 real depende de otro trabajo corriendo).
- Playwright bloquea con `page.route` todo lo que no va a `127.0.0.1:8766`.

## Playwright (Chromium, claro y oscuro)
Vistas: pestaña Informes, diálogo Hacer informe (con una visita Con dudas elegida), Crear informe, Informes, pestaña vacía (Torre P16).
| Ancho | Desborde horizontal | Cajas desbordadas | Peticiones externas | Errores de consola | Foco en el diálogo |
|---|---|---|---|---|---|
| 375, 768, 1024, 1280, 1920 (×2 temas ×5 vistas = 50) | 0 | 0 | 0 | 0 | sí |

Flujos: cargando (aria-busy), vacío con el texto exacto, error con «Reintentar» que recupera, con dudas (texto e icono), archivo ausente sin botón Abrir, Abrir PDF en pestaña nueva y PDF servido en línea, ruta libre 404, foco al abrir el diálogo en la primera visita lanzable, foco atrapado, Escape cierra y devuelve el foco, visita Procesada deshabilitada con su motivo, 409 y 404 con el `detail` del servidor (el 409 con enlace «Ver ese trabajo»), un solo POST real, avance en la pestaña, Crear informe → diálogo, obra de Levantamiento sin «Hacer informe», `#/trabajo/<id>` y su 404 sin cambios.
En el barrido de flujos la consola solo registra los «Failed to load resource» del navegador por los 500, 409 y 404 que yo mismo simulé; la aplicación no lanzó errores.

## Peor caso (simulado con `page.route`)
200 informes; nombres de 150 caracteres; fecha, nombre, tamaño, formato, número y carpeta nulos; 30 visitas con estados nulos, carpetas de 150 caracteres y formatos nulos o desconocidos. 5 anchos × 2 temas × 2 vistas (lista y diálogo): sin desborde, sin cajas desbordadas y sin errores.

## Suite del backend (desde `BACKEND/`)
- Con las 5 variables al scratch: **953 passed, 7 skipped** (incluye las 11 nuevas).
- Sin `CATDIC_DROPBOX_RAIZ` (las otras 4 al scratch; el Dropbox real solo se lee): **955 passed, 3 skipped, 2 failed**; las 2 fallas son `test_escaner_dropbox.py::test_terra_living_real` y `test_parser_visitas.py::test_lista_coincide_con_dropbox_si_esta_disponible`, las del Dropbox real.
- Búsqueda de «clasico» y «clásico» en `FRONTEND/` (sin `clasico/`, `maquetas/` ni `vendor/`): 0 resultados.

## Limitaciones
- No se generó un PDF real de punta a punta: la copia de la BD no tiene datos de diseño que den PDF; la lista se probó con PDF y eventos sintéticos.
- La lista no pagina (200 filas se pintan bien); filtros por formato o fecha quedan fuera.
- La ruta registrada se expone en la lista (necesaria para armar el enlace); es una ruta local.
- Contraste medido solo a ojo (B5 lo mide).

## Scratch con capturas
`C:\WINDOWS\TEMP\claude\5241ace622d5cd23\bde6ad2c-34d6-42aa-bdc5-6b0fd7ef0f32\scratchpad\b3g\capturas\`
