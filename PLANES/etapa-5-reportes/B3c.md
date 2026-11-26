# B3c · Confirmar datos del plano (M6) — informe del Ejecutor

Rama `claude/etapa5-fase-b-0020e1`, partiendo de `b37b475`. Solo `FRONTEND/` (nada de `BACKEND/`, nada de `clasico/`, `maquetas/`, `vendor/`).

## Qué se hizo

Pantalla completa nueva en el tablero «Plano sellado»: `#/obra/<id>/planos?confirmar=1[&tabla=<tabla_id>]`.

- Botón «Confirmar datos del plano» en «Planos y ficha»: habilitado solo con plano vigente; sin plano queda deshabilitado con el motivo escrito (`aria-describedby`). La ruta `?confirmar=1` sin plano muestra una pantalla con ese motivo.
- Barra superior: «Extraer del plano vigente» (A45, mensaje literal, «Extrayendo…», un solo POST), «Mesa de Dudas de la obra» con contador de dudas abiertas (A49, abre la Mesa en su propia vista; Atrás vuelve a la tabla) y Cerrar.
- Lista de tablas (R22): nombre amable, página, hoja, nivel, resultado con icono + texto + borde completo, causa de la falla en rojo, «No vigente» con borde punteado y su motivo, estados vacío/cargando/error con Reintentar.
- Detalle de tabla (R23): cabecera, comprobaciones (con detalle), certificación de notas con casilla (A47), recorte del plano con la celda resaltada (A46/A50/A51) por ratón y por teclado (roving tabindex, flechas, Inicio/Fin), tabla de valores con diferencia «tabla: X» cuando el valor propuesto no coincide, confirmar por lote con casilla (A48), bloque de tabla roja («No se puede confirmar» + «Ir a la Mesa de Dudas»), y los `detail` 409/422 del servidor mostrados tal cual.
- Móvil (<1024 px de la propia pantalla): pasos lista → tabla con «Volver a las tablas» (la elección se conserva); objetivos de 44 px.
- Regla de Oro: nada se confirma ni se certifica sin la casilla; lo vacío o sin fuente se muestra «pendiente de verificar»; las filas se identifican por `uid|campo`, nunca por `id_elemento`.

## Archivos tocados

- Nuevo `FRONTEND/js/confirmar-plano.js` (componente `ConfirmarPlano`).
- `FRONTEND/js/rutas.js` (ruta con `confirmar`/`tabla`, `hashConfirmarPlano`, `vinoDeDentroConfirmar` para que Cerrar/Atrás no apile historial).
- `FRONTEND/js/pestana-planos.js` (botón de entrada, pantalla sin plano, montaje del componente).
- `FRONTEND/index.html` (script).
- `FRONTEND/css/base.css` (bloque `.conf-*`, container queries `conf` y `det`).

## Componentes reutilizados / extendidos

- Reutilizado sin cambios: `VisorPlano` (con `detalle` = página + rect del recorte, para «Abrir plano»), `Pendiente`, `C.api` (blob para el recorte), `C.formato`, `C.visor.olvidar`, tokens «Plano sellado», `--rojo-plano` solo para la celda resaltada.
- Extendido: `rutas.js` (ver arriba). No se tocaron `Bloque` ni `VisorRevision`.

## Paridad con B0 §9 «Confirmar datos del plano»

| B0 | Estado |
|---|---|
| Botón solo con plano vigente (A14) | Hecho (deshabilitado + motivo sin plano) |
| Extraer (A45) con mensaje y «Extrayendo…» | Hecho |
| Mesa de Dudas de la obra (A49) | Hecho; ahora es una vista (Atrás vuelve a la tabla) en vez de un modal apilado |
| Lista de tablas con nombres, resultado, falla | Hecho; añade «No vigente» y motivo |
| Comprobaciones con detalle y certificada | Hecho |
| Certificar notas (A47) | Hecho, con casilla |
| Recorte con resaltado por celda (A46/A50/A51) | Hecho (ratón, foco, teclado) |
| Confirmar por lote (A48) | Hecho, con casilla |
| Errores 409/422 tal cual | Hecho |
| X cierra y libera el recorte | Cerrar/Escape/Atrás; libera la URL del recorte |

## Fase D / pendientes

- Edición manual de un valor propuesto no existe en B0 ni aquí (no se inventó).
- Mesa de Dudas de la obra: se abre la vista de B3g ya existente; sin cambios en ella.
- Revisión visual de impresión del recorte a 1920 px con planos reales de varios MB: no probada (solo planos sintéticos).

## Extracción y semillas (solo copia en scratch)

- Obra de B3e («con plano real sintético»): `POST extraer-diseno` da 0 tablas, 0 elementos, 2 dudas cerradas → estado vacío «Aún no hay tablas extraídas…». Obra sin plano: 409 «La obra no tiene un plano vigente…».
- Se sembró la obra `obra-sintetica-b3c` (todo rotulado SINTETICO) con un PDF vectorial de 5 páginas: p1 acero_en_losa + f'c por rango (verde), p2 acero con notas de modificación (rojo, certificable), p3 acero con datos malos (rojo: unidades, total_de_barras, espesor_total), p4 zapata_muro_lindero (verde), p5 losa_aligerada E9 (verde). La extracción real dio 6 tablas, 9 elementos, 128 campos, 8 dudas.
- Casos extra por SQL en la copia: p5 no vigente (extracción vieja), una fila `p9:fc_por_rango` sin bbox ni elementos («Sin recorte»), y L1/H cambiado a 0.26 contra 0.25 de la tabla para provocar la diferencia y un 409 real.

## Pruebas (Playwright, Chromium, puerto 8766, copia en scratch)

| Ancho | Claro | Oscuro | Notas |
|---|---|---|---|
| 375 | OK | OK | pasos y «Volver a las tablas» con selección conservada; botones ≥44 px |
| 768 | OK | OK | igual (pasos) |
| 1024 | OK | OK | dos columnas |
| 1280 | OK | OK | dos columnas, recorte y valores lado a lado |
| 1920 | OK | OK | idem |

En los 10 casos: sin scroll horizontal, `JS_CAJAS` vacío, 0 peticiones externas, 0 errores de consola, resaltado por teclado (1 caja), Atrás.

Funcional (1280): recarga con `&tabla=`, resaltado por ratón y teclado con texto de la celda, casilla que bloquea el botón, 409 real con `detail`, «Sin recorte», tabla roja con «Ir a la Mesa de Dudas», no vigente, certificar real («Tabla p2:acero_en_losa certificada… queda en verde · 1 duda cerrada.»), confirmar real de p4 («10 valores confirmados en 2 elementos») y p2 («16 valores… en 2 elementos»), Mesa abre en vista y Atrás vuelve a `…confirmar=1&tabla=1`, Extraer con mensaje literal y selección limpia, Cerrar/Escape a «Planos y ficha», fallos simulados de lista/detalle/recorte con Reintentar, 409/422 simulados mostrados tal cual, extracción lenta (un solo POST), `tabla=999` con aviso, cargando, obra sin plano, obra vacía. Solo hubo los 4xx esperados.

Peor caso (375 y 1280, claro y oscuro; GET lento simulado): 60 tablas, 400 filas, nombres/valores de 120 caracteres, `nivel_rango`/`hoja`/valores nulos → sin desborde, sin errores; los nulos se muestran «pendiente de verificar».

Suite del backend desde `BACKEND/`: ver «Suite» abajo.

## Suite

- Todo en scratch (con `CATDIC_DROPBOX_RAIZ` de prueba): **975 passed, 7 skipped, 0 failed**.
- Sin `CATDIC_DROPBOX_RAIZ`: **977 passed, 3 skipped, 2 failed**, solo los 2 esperados de Dropbox: `test_terra_living_real` y `test_lista_coincide_con_dropbox_si_esta_disponible`.
- Búsqueda de «clasico»/«clásico» en `FRONTEND/` (sin `clasico/`, `maquetas/`, `vendor/`): 0 resultados.

## Limitaciones

- Solo planos sintéticos; no se probó contra Dropbox real (prohibido).
- Los textos con acentos se ven rotos solo en la consola de Windows; en pantalla están bien.
- En el aviso de valores dudosos el enlace «Mesa de Dudas de la obra» puede partirse en varias líneas en 375 px (legible, sin desborde).

## Capturas y scratch

`C:\WINDOWS\TEMP\claude\5241ace622d5cd23\bde6ad2c-34d6-42aa-bdc5-6b0fd7ef0f32\scratchpad\b3c\capturas\` (matriz `m-<ancho>-<tema>-*.png`, peor caso `peor-*.png`, funcionales `t*-*.png`). No versionadas.

## Hashes

- Implementación: `9dd4aee`
- Ajuste «pendiente de verificar» en hoja/nivel nulos e informe: ver el commit siguiente.
