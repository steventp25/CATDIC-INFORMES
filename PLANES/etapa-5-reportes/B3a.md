# B3a — Inicio y Mis obras (informe del Ejecutor)

Fecha: 19/11/2026. Rama `claude/etapa5-fase-b-0020e1`. Estilo «Plano sellado». Sin push, merge ni stash; `BACKEND/**`, `maquetas/`, `clasico/` y `vendor/` sin tocar.

## Archivos tocados (todo en `FRONTEND/`)
- Nuevos: `js/datos.js` (lecturas compartidas y cálculo de prioridades), `js/formulario-planos.js` (componente `FormularioPlanos`).
- Reescritos: `js/pantallas/inicio.js`, `js/pantallas/obras.js`.
- Editados: `index.html` (dos `<script>` nuevos; `noscript` sin enlace), `css/base.css` (sección «B3a»), `css/tokens.css` (`--ok-fondo`, aviso verde, claro y oscuro), `js/iconos.js` (icono `cerrar`), `js/componentes.js` y `js/pantallas/obra.js` (solo se quitó el enlace al tablero clásico).

## Cambio del Líder (Steven: no quiere volver a ver el tablero clásico)
Commit aparte `ddca35f`: se quitaron los 3 enlaces (`PantallaB3`, estado vacío de las pestañas de obra, `noscript`, ahora «CATDIC necesita JavaScript para funcionar.»). Los avisos «todavía no está construida» y la tarea que las construye se quedan. **Comprobado al final:** `grep -rniE "cl[aá]sico"` en `FRONTEND/` sin `clasico/`, `maquetas/` ni `vendor/` da 0 resultados (tampoco en `DESIGN.md` ni `PRODUCT.md`). `FRONTEND/clasico/` no se tocó.

## Decisiones y por qué
- **Datos compartidos (`datos.js`).** Un *mixin* con dos lecturas independientes (`/api/dashboard`, `/api/dudas?resuelta=false`), cada una con su estado, su contador anti-respuesta-vieja y su «Reintentar». Sin recargas por tiempo. Si fallan las dudas, Inicio sigue con el tablero y muestra «No se pudo leer la Mesa de Dudas» aparte; en Mis obras la celda «Dudas abiertas» pasa a «pendiente de verificar» (nunca 0).
- **Prioridades.** Visita con estado «Con dudas» o con dudas bloqueantes abiertas; dudas de obra (sin visita, una fila por obra); visitas «Sin procesar» / «En cola» sin dudas. Orden: bloqueante → «Con dudas» → cola; dentro de cada grupo, la más antigua primero. Se muestran 10 y «Y N más» remite a la Bandeja (la lista completa es de B3e).
- **Antigüedad.** Solo desde `fecha_visita` (días hasta hoy). Sin fecha válida, «pendiente de verificar». Las dudas de obra no traen fecha de visita y se dejan en pendiente (no se usa `creado`).
- **Enlaces.** Visitas y dudas de visita: `#/obra/<id>/visitas?visita=<id de la visita>`. `rutas.js` ya lee la consulta (`ruta.consulta.visita`), así que B3d y B3e pueden abrir el registro exacto sin cambiar el enrutador. Dudas de obra: `#/obra/<id>/resumen`.
- **Cifras (Z9–Z13).** Cajetín con celda completa clicable: Obras activas → `#/obras`; Visitas en cola → `#/bandeja` (la cola global la construye B3d/B3e, la ruta existe vacía); Bloqueadas y Vencen en ≤ 7 días → «pendiente de verificar» + «Fase D-a». **Órdenes abiertas:** número real, pero **no hay ruta** para el kanban (no existe en `GENERALES` y lo construye B3f), así que no enlaza; lleva una nota «Se verán en la pantalla de órdenes (B3f)». El Líder debe decidir dónde vive.
- **Revisiones de planos (N6).** Leí `BACKEND/plano/confirmacion.py` y `GET /api/proyectos/{id}/tablas-extraidas` (`plano/extractor.py:listar_tablas`). La lista trae `resultado` (verde/rojo), `vigente` y `motivos_no_vigente`, pero **ningún campo que diga si la tabla está confirmada**: `confirmable` y `campos[].estado` solo salen del detalle por tabla (`GET …/tablas-extraidas/{id}`), y deducirlo sería adivinar. Por eso, por cada obra con plano vigente se muestra una fila con enlace a `#/obra/<id>/planos` y «Tablas por confirmar: pendiente de verificar · Fase D-a». No se hace ninguna petición por obra. Lo que falta: un campo (o un conteo) de tablas sin confirmar en la lista o en el tablero.
- **Entregas y vencimientos:** bloque «pendiente de verificar» + «Fase D-a», sin filas.
- **Próximas acciones:** `proyectos[].observaciones` por obra (la columna «Próxima Acción» del clásico); vacío = «pendiente de verificar». Nota: hoy esos textos son los de siembra («Completa supervisor, estado y fechas.»).
- **Mis obras.** Filas ordenadas por nombre (`localeCompare` en `es`), acomodadas a su `.caja` (container query). Toda la fila abre la obra con un enlace extendido (`::after`); los accesos directos van por encima. Plano vigente: «Rev. N · etiqueta», fecha, «certificado por X», sha256 vectorial y sellado en el `title`; sin plano, la insignia «sin plano vigente». «Visitas» solo en Supervisión; «Dudas de la obra: N» solo con N > 0.
- **Nueva obra / `FormularioPlanos`.** `<dialog>` modal con `showModal()` (el resto queda inerte), Escape y Cancelar/X cierran, el Tab da la vuelta dentro del diálogo (manejador propio además del nativo), el foco entra en el primer campo y vuelve al botón al cerrar. 11 campos, 2 archivos, revisión, fecha y casilla, con los 3 mensajes locales del clásico (el foco pasa al campo que falla). Flujo `POST /api/proyectos` → `POST /api/proyectos/{id}/planos` (multipart) con `C.api.post` y `C.api.enviarFormulario`; ningún POST se reintenta solo. Si la subida falla, la obra ya existe: el diálogo sigue abierto, los campos de la obra quedan deshabilitados, el mensaje es «La obra se creó, pero los planos no se subieron: …» y el botón pasa a «Reintentar la subida de planos» (solo repite la subida). Reutilizable: `modo="cambiar"` con `:proyecto="{id, nombre}"` para B3b; emite `hecho` y `cancelar`. Si se cancela tras crear la obra, la lista se recarga.
- **Aviso verde (A28).** Mismo texto que el clásico, con un cambio: «(botón «Datos de la obra»)» se sustituyó por «(se responden en la pestaña «Planos y ficha» de la obra)» porque ese botón ya no existe; más el enlace «Abrir la obra nueva» a `#/obra/<id>/planos`.
- **Ortografía de «—» y «Pendiente»:** no se usan como relleno; siempre «pendiente de verificar».

## Checklist de paridad (B0 §9)
Cubierto:
- Tarjetas: Proyectos Activos, Órdenes Abiertas, Bloqueadas, Vencen en ≤ 7 días, Visitas en Cola (las dos que el backend no calcula, como pendiente/D-a).
- Matriz de proyectos: las 7 columnas (proyecto, tipo/formato, cliente, supervisor, estado informe, plano vigente, próxima acción), con «pendiente de verificar» en vez de «—», «Pendiente» y «Sin iniciar».
- Celda de plano vigente: revisión, etiqueta, fecha, certificado por, tooltip sha256, insignia «sin plano vigente».
- Botón «Dudas de la obra: N» (solo con dudas) y «Subir visita» solo en Supervisión: ambos como **enlaces** a la pestaña, sin acción.
- Cabecera y avisos: botón «Nueva obra»; aviso verde de obra creada con botón cerrar; error «No se pudo cargar el tablero» y «No se pudo leer la Mesa de Dudas» (esta con «Reintentar»; el clásico no lo tenía); carga inicial de dudas abiertas y tablero.
- Modal Nueva obra: 11 campos y deshabilitado tras crearla; 2 PDF, revisión, fecha y certificación; 3 validaciones; crear en 2 pasos con reintento solo de la subida; aviso final.

No cubierto (y quién lo cubre):
- «Cambiar plano»/«Subir planos», «Ver plano», «Datos de la obra», «Confirmar datos del plano»: B3b / B3c (el componente ya está listo para «cambiar»). Aquí solo hay un enlace «Planos y ficha».
- «Subir visita» y «Conectar con Dropbox» como acciones, la cola de visitas (Z15) y su contador, Sincronizar, Procesar cola, trabajo de la cola: B3d.
- Mesa de Dudas y «Dudas de la obra» como panel: B3e.
- Kanban de órdenes (Z16): B3f.
- Aviso «Z4/Z5/Z8» de sincronización: B3d.

## Necesidades
- **N6 (prioridades, dudas, revisiones, entregas, próximas acciones):** cumplida con lo que el backend da hoy. Cada fila enlaza al registro (visita o pestaña de la obra), cada bloque tiene cargando, vacío, error con «Reintentar» y pendiente. Revisiones y entregas, en «pendiente de verificar» por falta de backend (ver arriba).
- **N7 (sin cifras falsas):** cumplida: `bloqueadas` y `vencen_7_dias` nunca se muestran como 0.

## Pendiente de verificar / Fase D
- Bloqueadas, Vencen en ≤ 7 días, Entregas y vencimientos, y «Tablas por confirmar» por obra: **D-a**.
- Antigüedad de las dudas de obra y de una visita sin fecha válida.
- Cliente, supervisor y estado del informe vacíos (hoy casi todos), fecha o certificado del plano vacíos, próxima acción vacía.

## Playwright (Chromium, `#/inicio` y `#/obras`, backend en 127.0.0.1:8765 con copia de la BD)
| Ancho | Claro | Oscuro |
|---|---|---|
| 375 | 0 externas · 0 errores de consola · sin desplazamiento horizontal · nada fuera de su caja · 0 objetivos < 44 px | igual |
| 768 | igual (sin la prueba de 44 px) | igual |
| 1024 | igual | igual |
| 1280 | igual | igual |
| 1920 | igual | igual |

En una primera pasada a 375 px había 6 objetivos de 22–41 px (cifras, enlaces de «Próximas acciones» y nombre de obra); se corrigieron con `min-height: 44px` en móvil y la repetición dio 0.

Otras comprobaciones:
- **Diálogo (1280):** abre con el foco en «Nombre de la obra»; 40 Tab y 40 Mayús+Tab sin salir del diálogo (0 veces fuera; antes del manejador propio el foco pasaba al `body` del navegador 2 veces); Escape, Cancelar y X cierran y el foco vuelve a «Nueva obra»; las 3 validaciones con su texto y el foco en el campo correcto; a 375 px no desborda; oscuro revisado en captura.
- **Creación real** (copia de la BD y carpeta de datos en el scratch): `POST /api/proyectos` → plano simulado con 500 (solo la respuesta, con `page.route`) → mensaje «La obra se creó, pero los planos no se subieron: …», campos deshabilitados, botón «Reintentar la subida de planos» → reintento real: **3 POST en total (1 obra, 1 subida fallida, 1 subida buena)**, o sea que no se recreó la obra. Aviso verde con enlace `#/obra/obra-de-prueba-b3a/planos`; la obra aparece en la lista con «Rev. 1 · Rev. prueba · 10/03/2026 · certificado por steven» y los sha256 en el `title`; Inicio muestra su fila en «Revisiones de planos». Los PDF eran de 3 hojas hechos en el scratch.
- **Navegación:** clic en cualquier punto de la fila de Terra Living → `#/obra/terra-living/resumen`, Atrás → `#/obras`; «Visitas» → `…/visitas`; la primera prioridad → `#/obra/terra-living/visitas?visita=terra-living-17-completivo-verticales-s-4-28-09-2026`, Atrás → `#/inicio`; la cifra de obras → `#/obras`.

### Estados probados (1280, `page.route` solo en la prueba)
- **Cargando** (respuestas retenidas): `aria-busy` en 5 bloques en Inicio y 1 en Mis obras, con «Cargando…» para lectores de pantalla.
- **Vacío** (`proyectos: []`, `visitas: []`, dudas `[]`): «No hay pendientes.», «Ninguna obra tiene plano vigente.», «Nada que hacer ahora.», «Aún no hay obras.» (Inicio y Mis obras).
- **Error del tablero** (500): «No se pudo cargar el tablero» con `role="alert"` y «Reintentar» en cada bloque (5 en Inicio, 1 en Mis obras).
- **Error de dudas** (500, tablero bien): un solo aviso «No se pudo leer la Mesa de Dudas»; Inicio sigue mostrando 10 filas del tablero; Mis obras muestra «Dudas abiertas: pendiente de verificar» (no 0). «Reintentar» recupera: 0 alertas y los conteos 0 / 22 / 0.
- **Datos reales** de la copia: 3 obras, 24 visitas de Terra Living, 22 dudas abiertas.
- Los errores de consola de esas pruebas («Failed to load resource» por los 500 y las respuestas abortadas) son los provocados a propósito; en las rutas con datos reales la consola quedó vacía.

### Peor caso (375, 768 y 1280, claro)
40 obras, la primera con nombre de 120 caracteres y cliente de 90 «A» sin espacios; campos nulos y vacíos; etiqueta de revisión de 80 caracteres, «certificado por» de 70 y fecha de plano inválida (sale «pendiente de verificar»); una duda de obra bloqueante. Resultado: 0 desbordes horizontales, 0 elementos fuera de su caja, 40 filas en Mis obras, 0 externas, 0 errores de consola. Con 0 obras, ver «Vacío».

## Suite del backend (desde `BACKEND/`, con la BD, datos, caché y salida de pruebas en el scratch)
Resultado real: **944 pasan, 2 fallan, 3 se omiten** (199 s). Las 2 fallas son las esperadas de Dropbox: `test_escaner_dropbox.py::test_terra_living_real` y `test_parser_visitas.py::test_lista_coincide_con_dropbox_si_esta_disponible`. La falla de B2 (`test_raiz_entrega_el_tablero_local`) ya no aparece: el Líder corrigió la prueba en `d6574ea`.

## Limitaciones
- El contraste no se midió con herramienta (B5). El movimiento con propósito llega en B4.
- No se probó en un navegador distinto de Chromium. Safari no da foco al botón al hacer clic; el retorno de foco usa el elemento activo al abrir, que allí puede ser el `body` (se cae al `<h1>`).
- «Antigüedad» de las visitas usa la fecha local de la PC; una visita con fecha futura muestra esa fecha en vez de «hace −N d».
- No hay ruta para las órdenes (ver Decisiones).
- La fila de cifras puede dejar la quinta celda sola en una línea a ciertos anchos (cajetín `auto-fit`).
- Pruebas: no se pulsó «Sincronizar», no se conectó Dropbox y nada se escribió fuera del scratch. Servidor apagado al terminar.

## Scratch (capturas, scripts y resultados; no se commitean)
`C:\WINDOWS\TEMP\claude\5241ace622d5cd23\bde6ad2c-34d6-42aa-bdc5-6b0fd7ef0f32\scratchpad\b3a\` — capturas en `capturas\` (2 pantallas × 5 anchos × 2 temas, estados cargando/vacío/error, peor caso, diálogo), scripts `prueba_estados.py` y `prueba_dialogo.py`, resultados `res_estados.json` y `res_dialogo.json`.

## Commits
- `ddca35f` quita todo enlace al tablero clásico.
- `30bea9a` Inicio y `js/datos.js`.
- `6f6d73a` Mis obras y `FormularioPlanos` (con CSS, token, icono e `index.html`).
- Informe: ver el commit siguiente.
