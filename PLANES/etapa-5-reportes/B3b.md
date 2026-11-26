# B3b · Informe del Ejecutor: Resumen, Planos y ficha, Avance y Cierre

Rama `claude/etapa5-fase-b-0020e1`, HEAD de partida `b008dda`. Sin cambios en `BACKEND/`.

## Archivos

Nuevos (`FRONTEND/js/`): `pestana-resumen.js`, `pestana-planos.js`, `pestana-avance-cierre.js` (Avance y Cierre), `indicadores.js` (componente `Indicador` y mixin de lecturas `C.obraHechos`), `editor-plano.js`, `datos-obra.js`.
Modificados: `js/visor-revision.js`, `js/rutas.js`, `js/pantallas/obra.js` (monta las 4 pestañas y retira el texto de «pestaña no construida»), `index.html` (scripts), `css/base.css` (bloque B3b al final).

## Componentes reutilizados y extendidos

- `VisorPlano`: props nuevas `editor`, `cajas`, `herramienta` (mover|dibujar), `salto`, `leyendaPropia`; eventos `hoja` y `dibujado`; slot `panel`. Dibujo con Pointer Events + `setPointerCapture`; trazos menores de 5 pt se descartan; se redondea a 2 decimales; el pellizco de dos dedos cancela un trazo en curso. Etiqueta y halo en tamaño constante en pantalla (`12/e`, `3/e`).
- `rutas.js`: `hashVisorPlano(obraId, uid)`, `reemplazar(hash)`, `vinoDeDentro` (decide entre `history.back()` y reemplazar al cerrar el visor).
- Se reutilizan `FormularioPlanos modo="cambiar"`, `ColaVisitas`, `AccionesCola`, `FormularioVisita`, `ResultadoVisitas`, `Bloque`, `Cajetin`, `Pendiente`, `FaseD`, `C.datos.prioridades`.

## Qué hace cada pestaña

- Planos y ficha: plano vigente (Rev., etiqueta, fecha o «sin fecha de plano», certificado por, sha256 cortos); sin plano: «Sin plano vigente» + «Subir planos»; historial con cargando, vacío y error + Reintentar; Cambiar plano con aviso A28; «Datos de la obra» (4 grupos, GET previo y, si falla, lo dice y no abre el formulario; PUT con mensaje A29); enlace «Dudas de la obra: N» (`?dudas=obra`); hueco reservado a M6 (B3c) sin simular. `?subir=1` abre el diálogo.
- Editor de recuadros (`?visor=1[&elemento=uid]`): selector por `uid`; cajas confirmado (continuo) / propuesto (discontinuo) / sin guardar (punteado) con etiqueta; «Proponer recuadros», «Usar propuesta», «Confirmar y guardar» (PUT y luego `C.visor.olvidar`), «Vista previa» (URL de objeto revocada); textos A44; sin reintentos automáticos ni doble envío. Los recuadros de un plano anterior no se tratan como confirmados.
- Resumen: N8, N9 y N10 siempre «pendiente de verificar» con fórmula, motivo D15 y «Fase D-b» (nunca 0 % ni barra); pendientes N12 con datos reales y enlaces; elementos «plano cambiado: revisar»; últimos informes; acciones rápidas; actividad reciente «Fase D-a».
- Avance: N8 y las visitas como hechos (no como porcentaje).
- Cierre: N9 y N10, y hechos con enlace (dudas abiertas, visitas sin procesar o con dudas, plano vigente, informes). No hay «listo para cerrar» calculado.

## Queda como Fase D / pendiente de verificar

Los tres indicadores (D15, Fase D-b); actividad reciente (Fase D-a, no hay registro por obra en el servidor); el nombre de carpeta de cada visita (elementos y nivel) no se interpreta; la revisión de tablas del plano es B3c.

## Pruebas (Playwright, Chromium, servidor propio en 8766)

- Barrido 375/768/1024/1280/1920, claro y oscuro, en Resumen, Planos, Avance, Cierre y visor: sin scroll horizontal, 0 errores de consola, 0 peticiones fuera de 127.0.0.1:8766.
- Editor con ratón: dibujo, trazo de 2 px descartado, guardado (PUT recuadro) y vista previa; Escape cierra y vuelve a la URL de planos. Con toque (CDP, 375 px): el dibujo funciona.
- Datos de la obra: guardar (mensaje A29), Escape devuelve el foco al botón, GET con 500 muestra error + Reintentar sin abrir el formulario. Historial de planos con 500: error + Reintentar.
- Cambiar plano / Subir planos con PDF sintéticos: sin archivos da el error del formulario; con archivos queda vigente y el Resumen y el Cierre lo reflejan.
- Peor caso (respuestas simuladas): 300 elementos con id y ejes de 120 caracteres, 30 revisiones con campos nulos: sin desbordes.
- Correcciones hechas durante la prueba: CSS que anulaba el tamaño de la etiqueta del recuadro; en móvil el editor deja la hoja a 45–55 % de la altura y el panel desplaza.

Suite del backend (desde `BACKEND/`, todo en la carpeta temporal): con `CATDIC_DROPBOX_RAIZ` 975 pasan, 7 omitidas, 0 fallos. Sin esa variable 977 pasan, 3 omitidas y fallan solo los 2 que leen el Dropbox real (`test_terra_living_real` y `test_lista_coincide_con_dropbox_si_esta_disponible`).

## Commits

`eeebe2b` (visor y rutas), `5f6a46a` (Planos y ficha, editor, Datos de la obra), `c3def42` (Resumen, Avance, Cierre, estilos), más el commit de este informe. Búsqueda de «clásico» en `FRONTEND/` (sin `clasico/`, `maquetas/`, `vendor/`): 0 resultados.

## Limitaciones

- Dibujar un recuadro requiere ratón o dedo; no hay equivalente de teclado. «Proponer recuadros» y «Usar propuesta» cubren a quien usa teclado.
- Con la herramienta «Dibujar» activa (por defecto), mover la hoja exige cambiar a «Mover la hoja» (zoom y flechas por teclado siguen funcionando).
- No se probó contra Dropbox real.

Capturas y datos sintéticos en `...\scratchpad\b3b\capturas\` (no se versionan).
