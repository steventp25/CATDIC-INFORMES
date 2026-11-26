# B3g-2 — Regenerar el informe de una visita ya procesada (encargo del Líder al Ejecutor)

Fecha: 22/11/2026. Va justo después de B3e. La decidió el Director a pedido de Steven, que el 22/11 respondió «Sí, lo necesito» a la pregunta «¿Quieres poder regenerar el informe de una visita ya procesada?». Estilo **Plano sellado** (`FRONTEND/DESIGN.md`).

## Dónde se trabaja (igual que en B3g y B3e)
- **Worktree y rama:** `C:\Users\Steve\OneDrive\Desktop\CATDIC-WEB\.claude\worktrees\etapa2-t7n-confirmacion-8210cf`, rama `claude/etapa5-fase-b-0020e1`.
  - No crees ni cambies de rama. Nada de push, merge ni stash. No toques el checkout principal.
  - Trabajas por turnos con el Líder.
- **Zona:**
  - `FRONTEND/**`, menos `maquetas/`, `clasico/` y `vendor/`;
  - `PLANES/etapa-5-reportes/B3g2.md`;
  - y la **excepción de backend del Director**, que es solo esto:
    - el módulo nuevo `BACKEND/regenerar_visita.py`;
    - en `BACKEND/main.py`, solo la ruta nueva y su import;
    - las pruebas nuevas `BACKEND/tests/test_regenerar_visita.py`.
- **`procesador_cola.py`:** evítalo, porque el PR #35 lo cambia y el Director quiere el menor choque posible.
  - Reutiliza el procesador **componiéndolo o heredando** de `ProcesoVisita` desde tu módulo. Importar sus funciones y constantes (también las privadas: `_evento`, `_cerrojo`, `_hilos`, `_respaldar_bd`, `_auditar`, `_con_conexion`…) está permitido; editarlas no.
  - Si de verdad hace falta un gancho mínimo, que sea de pocas líneas, sin cambiar el comportamiento de `/procesar` ni de `procesar-cola`, y justificado en el informe. Antes de tocarlo, pregúntalo en el informe como decisión abierta y sigue sin él si puedes.
- **Prohibido:**
  - cambiar `database.py` o el esquema;
  - cambiar `/api/visitas/{id}/procesar` y `ESTADOS_PROCESABLES`;
  - tocar cualquier otro archivo de `BACKEND/`;
  - borrar o editar `FRONTEND/clasico/` o `test_frontend_servido.py`;
  - cualquier mención al clásico.
- **Python:** `C:\Users\Steve\AppData\Local\Python\pythoncore-3.14-64\python.exe`.

## Reglas
Son las de B3d, B3g y B3e, más estas:
- **CLAUDE.md §5.2:** jamás sobrescribir. La versión nueva sale con `v2`, `v3`… mediante `obtener_ruta_salida_sin_sobrescribir`.
- **Errores 15 y 18:** PDF de menos de 30 MB y sin sobrescribir; un FI MIVED existente nunca se rehace.
- **Regla de Oro:** no se inventa nada. Si hoy faltan datos, no se genera.
- **Commits:** atómicos, en español, terminados en `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Nunca capturas, PDFs ni `*.db`.

## Qué hay que construir (decisiones del Director)
1. **`POST /api/visitas/{id}/regenerar`** devuelve 202 y el trabajo.
   - Solo acepta visitas **«Procesada»**. Cualquier otro estado da 409 con el motivo y remite a «Procesar».
   - Visita inexistente: 404.
   - Otro trabajo corriendo: 409, con el **mismo cerrojo** (`_cerrojo`) y la misma tabla `trabajos`. Ojo: la columna `trabajos.tipo` solo admite `'visita'` o `'cola'` y el esquema no se cambia, así que usa `'visita'` y distingue la regeneración en la auditoría y en los eventos (por ejemplo, `"regenerar": true` en `visita_inicio`).
2. **Solo vuelve a generar el PDF,** con los datos que ya están en la BD: elementos de la visita, respuestas de la Mesa y plano vigente.
   - **No** relee el PDF ni el paquete de la visita: nada de lector.
   - **No** borra elementos ni dudas.
   - Lee `ProcesoVisita._procesar`, `_correr_lector`, `_elemento`, `_fichas_en_orden`, `_bloqueos_de_visita`, `_p3`, `_generar`, `_generar_fi`, `_publicar` y `_cerrar` (`procesador_cola.py`, líneas 369–1020) para decidir qué pasos reutilizas y cuáles sustituyes.
3. **Solo STP-MIVED,** como versión nueva y sin sobrescribir.
   - Se **salta P3** («ya hay un STP de su fecha»), porque aquí la versión nueva es justo lo que se pide.
   - Ese salto queda en `auditoria`, con una acción propia, por ejemplo `REGENERAR_SIN_P3`, y su motivo.
4. **Los FI-01/02/03 no se tocan.** No se llama a `_generar_fi`.
   - La pantalla dice: «Los formularios MIVED ya incluyen esta visita; no se vuelven a modificar».
5. **Si hoy hay bloqueos** (dudas abiertas, elementos en espera o plano cambiado):
   - no se genera nada y el motivo se informa como evento `aviso`;
   - se pueden abrir dudas nuevas si las hay;
   - **el estado de la visita no cambia:** sigue «Procesada», genere o no. No reutilices el `_cerrar` que cambia el estado.
6. **El mismo seguimiento de hoy:**
   - los eventos van a `trabajo_eventos`: `visita_inicio`, `elemento_*`, `duda`, `aviso`, `pdf_generado` con la ruta nueva, `visita_fin` y `fin`;
   - así la versión nueva sale en la lista de Informes de B3g, se abre con `/api/informes/archivo` y se sigue con `AvanceTrabajo`;
   - el trabajo se respalda y se cierra igual que `ejecutar_trabajo`.
7. **Pantalla** (`js/formulario-informe.js` de B3g, y la lista de Informes):
   - en «Hacer informe», las visitas «Procesada» dejan de estar deshabilitadas y ofrecen **«Regenerar informe»**, que llama a `/regenerar`; las demás siguen con `/procesar`;
   - antes de lanzarlo, una **confirmación** accesible que diga: sale como versión nueva (v2, v3…), no se borra nada, solo es el STP-MIVED y los formularios MIVED no se tocan (con el texto exacto de arriba). Sin una casilla marcada o un botón explícito no se lanza;
   - se sigue con el avance en vivo y, al terminar, se recarga la lista, donde la versión nueva aparece arriba;
   - los 409 y 404 se muestran con el `detail` del servidor, y ningún POST se reintenta solo;
   - si no se generó nada por los bloqueos, se dice claro, con el motivo y enlaces a la Mesa.

## Pruebas del backend (`tests/test_regenerar_visita.py`, BD de prueba y archivos en `tmp_path`)
Sigue el modelo de `tests/test_procesar_cola.py`, con material SINTÉTICO.
- Una visita «Procesada» genera la v2, y el original queda intacto (mismo sha256).
- Una segunda regeneración genera la v3.
- Una visita que no está «Procesada» da 409, y una visita inexistente da 404.
- Con una duda abierta, no genera, y el estado sigue «Procesada».
- Los FI quedan intactos (mismo sha256 antes y después).
- Con un trabajo en curso, da 409.
- La auditoría registra el salto de P3.
- El evento `pdf_generado` lleva la ruta nueva, y `informes_de_obra` la lista primero.
- Las pruebas que generan el STP necesitan Chromium de Playwright: haz como `test_procesar_cola.py`, que las salta con un mensaje si no está.

## Cómo se prueba en el navegador
- Las mismas reglas de B3e:
  - una copia de la BD en el scratch, con las 5 variables `CATDIC_*` al scratch;
  - el puerto **8766**: no cierres el 8765 ni el 8767, y nunca uses el 8000;
  - nada contra `C:\Users\Steve\CATDIC Dropbox\`.
- La copia de la BD no tiene una obra con plano vigente ni datos que den PDF. Prepara una obra SINTÉTICA en el scratch (como en B3e) con una visita «Procesada» que pueda regenerarse. Si no se puede, prueba el flujo de pantalla con `page.route` y anótalo.
- Playwright a 5 anchos × 2 temas sobre «Hacer informe» con una visita Procesada, la confirmación, el avance y la lista con la v2 arriba. Estados: 409, 404, sin generar por bloqueos. Sin peticiones fuera de `127.0.0.1:8766`, sin errores de consola y sin desplazamiento horizontal.
- La suite se corre dos veces (con todo en el scratch y sin `CATDIC_DROPBOX_RAIZ`). Solo pueden fallar las 2 de Dropbox.

## Informe
`PLANES/etapa-5-reportes/B3g2.md` con:
- archivos tocados, con los del backend aparte;
- qué reutilizaste de `ProcesoVisita` y qué sustituiste;
- el contrato de la ruta;
- cómo se distingue una regeneración en los trabajos y la auditoría;
- las pruebas;
- la tabla de Playwright;
- la suite;
- las limitaciones;
- los hashes;
- la carpeta del scratch.
