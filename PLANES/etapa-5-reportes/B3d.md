# B3d — Visitas y trabajos: informe del Ejecutor

Fecha: 22/11/2026. Rama `claude/etapa5-fase-b-0020e1`. Estilo Plano sellado, scripts clásicos con `window.CATDIC`, sin compilación ni librerías nuevas.

## Commits
| Hash | Qué |
|---|---|
| `30a1ef0` | Base: cancelación de peticiones (`senal` en `C.api`), ruta `#/trabajo/<id>`, iconos, `fechaHora`, tokens de color de estado |
| `534e9a8` | `ColaVisitas` (Z15), `AccionesCola` (Procesar cola, Sincronizar), `ResultadoSync` (Z8), `ResultadoVisitas` (Z4) |
| `f7115a3` | `FormularioVisita` (Subir visita y Conectar con Dropbox), `PestanaVisitas`, pantalla `trabajo` (avance en vivo) |
| `d134d01` | Cola en Inicio, Bandeja y pestaña de la obra; estilos; carga de scripts |
| `e3c64c4` | Dudas de la visita seleccionada, hora legible, título del diálogo |
| (este informe) | `PLANES/etapa-5-reportes/B3d.md` |

## Archivos tocados (todo en `FRONTEND/`)
- Nuevos: `js/cola.js`, `js/cola-acciones.js`, `js/formulario-visita.js`, `js/pestana-visitas.js`, `js/pantallas/trabajo.js`.
- Editados: `index.html` (scripts), `css/base.css` (sección B3d al final), `css/tokens.css`, `js/api.js`, `js/rutas.js`, `js/iconos.js`, `js/componentes.js` (`fechaHora`, `ahoraTexto`), `js/app.js` (título y menú de la ruta del trabajo), `js/pantallas/inicio.js`, `bandeja.js`, `obra.js`.
- No se tocó `BACKEND/**`, `FRONTEND/clasico/`, `maquetas/`, `vendor/` ni la prueba `test_frontend_servido.py`. `ddca35f` queda como está.

## Decisiones
1. **Una sola lista.** `ColaVisitas` es el único lugar donde hay tabla de visitas. Inicio solo muestra «N visitas · N en cola · N con dudas», los botones y el enlace «Ver la cola completa» a la Bandeja. La Bandeja muestra todas las obras (columna Obra); la pestaña de la obra, una sola.
2. **Trabajo compartido** (`C.cola.tienda`): un trabajo en marcha se ve en cualquier pantalla (el cerrojo del servidor es uno solo); uno terminado solo donde le toca. Se guarda en `sessionStorage` para retomarlo tras recargar.
3. **Polling** (`C.cola.seguir`): `GET /api/trabajos/{id}` cada 2 s con `AbortController` + `clearTimeout`; se cancela al desmontar. La pantalla de avance usa `GET /eventos?desde=<último>` cada 2 s y, al terminar, lee el trabajo una vez más. No se reintenta ningún POST.
4. **Errores 409:** se muestra el `detail` del servidor y, si trae un id `trab-…`, un enlace a ese trabajo.
5. **Fila con dudas:** borde izquierdo grueso, icono y texto («N dudas abiertas · clic para responder», «con N dudas bloqueantes abiertas»); no depende solo del color. Filas responsivas con container queries (`@container caja`): 760 px sin columna Obra, 900 px con ella; por debajo, cada fila es una tarjeta con rótulos.
6. **Clic en visita con dudas** → `#/obra/<id>/visitas?visita=<vid>`: la fila queda resaltada y arriba aparece un panel con las dudas abiertas de esa visita en solo lectura y el texto «Mesa de Dudas: la construye B3e». No se simula la Mesa.
7. **Diálogo** `FormularioVisita` copia el patrón de `FormularioPlanos`: `<dialog>` modal, Tab atrapado, Escape, foco de vuelta al botón que lo abrió. Mensajes y etiquetas literales de A31–A33. Mixta no se acepta (nota en el diálogo).
8. **En obras de Levantamiento** la pestaña no muestra Procesar ni Subir ni Conectar (el backend solo lee visitas de Supervisión) y lo dice.
9. **Sincronizar** solo en Inicio (como pidió el Director). La pestaña de la obra tiene Procesar cola de la obra y «Conectar con Dropbox», que ya sincroniza esa obra.

## §9 del inventario
Cubierto: Procesar cola y su seguimiento (A3, A5, A9, Z3); Sincronizar y su resultado (A2, A7, A8, Z5, Z8); cola Z15 con columnas, orden `visitasOrdenadas` y los dos textos de vacío; Subir visita y Conectar Dropbox (M3, A31–A33, Z4, A6, A19); contador «N visitas · M con dudas»; líneas de dudas bloqueantes/abiertas y «Pendiente: …»; detalle de Mixta.
No cubierto: abrir la Mesa de Dudas desde la fila (B3e); visor del plano (B3b).

## T10b (avance en vivo, parte de la Etapa 3)
- **Se cumple:** avance visita por visita y elemento por elemento (`visita_inicio`, `elemento_inicio`, `elemento_listo`, `duda`, `aviso`, `pdf_generado`, `visita_fin`, `fin`); cada duda aparece cuando surge, con enlace a su visita; la ruta lleva el id del trabajo y se puede cerrar y volver a abrir.
- **Espera a B3e:** responder la duda dentro de la pantalla en vivo.
- **Espera a B3b:** el visor del plano junto a cada duda.

## Aislamiento de las escrituras
Backend desde este worktree en `127.0.0.1:8766`, con una **copia** de la BD en el scratch, neutralizada (todas las `carpeta_dropbox` vacías; rutas de visitas dentro del scratch). `CATDIC_DB_PATH`, `CATDIC_DROPBOX_RAIZ`, `CATDIC_DATOS_RAIZ`, `CATDIC_CACHE_RAIZ` y `CATDIC_SALIDA_PRUEBAS` apuntan al scratch (`dbx` y `datos`/`cache` hermanas, porque `config.py` rechaza raíces cuya ruta contenga «dropbox»). Dropbox de prueba: carpeta sintética `dbx\SUPERVISION\EN CURSO\TORRE P16\LEVANTAMIENTO\VISITA A OBRA\` con 3 PDF hechos con pymupdf. Nada contra `C:\Users\Steve\CATDIC Dropbox\` ni el puerto 8000 ni el 8765. En Playwright, todo lo que no va a `127.0.0.1:8766` se aborta y se cuenta. Servidor apagado al terminar.

## Playwright (Chromium)
Scripts y capturas en el scratch (ver al final).

| Prueba | Resultado |
|---|---|
| Matriz 375/768/1024/1280/1920 × claro/oscuro × Inicio, Bandeja, `#/obra/<id>/visitas` (datos reales de la copia, dos obras) | 60 combinaciones: 0 desbordes horizontales, 0 elementos fuera de su caja, 0 peticiones externas, 0 errores de consola |
| Peor caso (300 visitas, carpetas de 150 caracteres, campos nulos, Mixta con detalle largo, 40 dudas en una visita) × mismas 30 combinaciones | 0 fallas |
| Diálogos a 375 y 768, claro y oscuro | dentro de la ventana, sin desborde |
| Diálogo: foco inicial, validaciones (mensajes exactos), Tab atrapado, Escape, foco de vuelta, error del servidor visible | todo bien |
| Conectar Dropbox real (sintético): Z4, 3 filas, enlace a dudas de la visita | bien |
| Subir visita real: Z4 con «Guardada en … con sha256» | bien |
| Procesar cola real por obra: «Procesando…» deshabilitado, `POST …?proyecto_id=`, terminado, recarga tablero y dudas | bien |
| Polling: se detiene al terminar (2→2 peticiones en 6 s) y al salir de la pantalla (0 peticiones nuevas en 6 s); en curso, ~2 s entre peticiones | bien |
| Avance en vivo con trabajo real (3 visitas, elementos, 9 dudas con enlace) y simulado en curso | bien |
| Sincronizar real: «Sincronizando…» deshabilitado, Z8 con 3 obras; error Z5 simulado y cerrable | bien |
| Estados: cargando, vacío (Bandeja, obra Supervisión, obra Levantamiento), error (3 pantallas), 409, sin trabajo (mensaje), trabajo fallido, trabajo 404 | bien |

Los «errores de consola» de las pruebas de error son los 404, 409 y 500 que la propia prueba provoca; el navegador los registra como `Failed to load resource`. En las pruebas sin errores provocados la consola quedó limpia.
Simulados con `page.route` (solo en la prueba): el 409, el trabajo fallido, el trabajo en curso, el error de sincronización, los estados de carga y error y el peor caso. Todo lo demás corrió contra el backend real del worktree.

## Suite del backend
Desde `BACKEND/`, con las variables al scratch: **942 passed, 7 skipped, 0 failed** (104 s). Las 2 pruebas del Dropbox real quedaron entre las omitidas (no fallaron) porque el Dropbox real no se usa con las rutas aisladas. Resultado en `suite/resultado.txt`.

## Búsqueda de «clasico» / «clásico»
En `FRONTEND/` sin `clasico/`, `maquetas/` ni `vendor/`: **0 resultados**.

## Dónde iría el aviso «esta visita trae paquete de Campo» (no se construyó nada)
- **Componente:** `ColaVisitas` (`js/cola.js`), en la celda Estado de cada fila (`.cola-estado`), como una línea más (`.cola-linea`, con icono `info`) debajo de «Pendiente: …». Alternativa: una `.etq` junto al nombre de la carpeta.
- **Pantalla de avance:** una línea en el bloque de la visita (`js/pantallas/trabajo.js`) con «cargada desde el paquete de Campo», a partir del evento `visita_inicio`.
- **Dato del backend que haría falta:** una marca por visita en `GET /api/dashboard` → `visitas[]`, por ejemplo `paquete_campo` (booleano o nombre del `*.catdic-visita.json` y su versión), que hoy esas filas no traen; y, para la pantalla de avance, un campo `origen` (`pdf` o `paquete`) en el evento `visita_inicio`. El frontend no debe buscar el archivo en disco: es el sincronizador quien lo detecta.

## Limitaciones y preguntas abiertas
- El backend no tiene una ruta que liste trabajos. Tras recargar, un trabajo en curso se retoma solo si está en `sessionStorage` (misma pestaña) o por el enlace del mensaje 409 o de `#/trabajo/<id>`. Una ruta «trabajos recientes» sería Fase D.
- Probado solo en Chromium; no se midió contraste con herramienta (se usan los tokens ya aprobados en B2/B3a y los nuevos de estado, con texto siempre escrito).
- Las dudas de la visita seleccionada se muestran en solo lectura; responderlas es de B3e.
- Pregunta: ¿«Sincronizar desde Dropbox» también debe estar en la pestaña de cada obra? Se dejó solo en Inicio, como pidió el Director, porque «Conectar con Dropbox» ya sincroniza esa obra.

## Carpeta del scratch
`C:\WINDOWS\TEMP\claude\5241ace622d5cd23\bde6ad2c-34d6-42aa-bdc5-6b0fd7ef0f32\scratchpad\b3d\` — capturas en `capturas\`, scripts `matriz.py`, `e2e.py`, `e2e2.py`, `peor.py`, `estados.py`, `dlgmov.py`; resultado de la suite en `suite\resultado.txt`.
