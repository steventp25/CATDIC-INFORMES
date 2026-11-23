## Evaluación 1 · 22/11/2026 · Planificador (auditoría) · Fase B · B3a y B3d (rama `claude/etapa5-fase-b-0020e1`, `4422678`)
**Veredicto: APROBADO**

Steven vio las dos pantallas en una copia de la rama (puerto 8767, BD de prueba copiada) y respondió: «Sí, sigue así» (22/11/2026).

### Bloqueantes
- Ninguno.

### Observaciones (no bloquean)
- **Paridad con el tablero clásico.** `FRONTEND/clasico/` y `test_clasico_entrega_el_tablero_anterior` siguen intactos, como pidió Steven el 20/11 («Conserva el tablero clásico»). El tablero nuevo no enlaza al clásico (`ddca35f`, decisión del 19/11). Si el clásico debe volver a tener enlace es una decisión pendiente de Steven; no bloquea.
- **`BACKEND/tests/test_frontend_servido.py`.** Es el único archivo de `BACKEND/` que cambia respecto a `main` (B2, +19/−4). Es una prueba del servidor y no toca código de ejecución.
- **Trabajos tras recargar.** Sin una ruta que liste trabajos, al recargar la página solo se retoma el trabajo de la misma pestaña o el que se abre por su enlace. Queda anotado como Fase D.
- **Aviso de paquete de Campo.** Necesita `paquete_campo` por visita en `/api/dashboard` y `origen` en `visita_inicio`. Es para una tarea posterior, después de que se fusione el PR #35.

### Criterios de aceptación
- [x] **Zona respetada.** El rango `e65efdb..4422678` toca solo `FRONTEND/js`, `FRONTEND/css`, `FRONTEND/index.html` y `PLANES/`. No toca `clasico/`, `vendor/`, `maquetas/` ni código del backend.
- [x] **Sin menciones al clásico.** `git grep -i 'clásico|clasico'` en `FRONTEND`, excluidas `clasico/`, `maquetas/` y `vendor/`, da 0 resultados.
- [x] **Sin URL externas.** Solo hay rutas a `127.0.0.1`, `localhost` y `w3.org`. En el navegador: 0 errores de consola en Inicio, Bandeja y `#/obra/terra-living/visitas`.
- [x] **Sin archivos prohibidos.** El diff no contiene `*.db`, PDF, imágenes ni `.env`.
- [x] **Regla de Oro.** `js/datos.js` solo usa datos de `/api/dashboard` y `/api/dudas`. Los días salen de `fecha_visita` real, o quedan en `null` y se muestran como «pendiente de verificar». Los indicadores sin dato dicen «pendiente de verificar» o «Fase D», nunca 0.
- [x] **Ningún POST se reintenta solo** (`api.js`, `cola-acciones.js`). El polling se cancela al salir de la pantalla (`trabajo.js`: `clearTimeout` y `AbortController.abort()`).
- [x] **Una sola cola.** Inicio muestra el resumen y los botones y enlaza a la Bandeja, sin una segunda tabla.
- [x] **Steven las vio y las aprobó.**
- [?] **Matriz Playwright de 5 anchos × 2 temas y peor caso de 300 visitas.** No la repetí; la reportan el Ejecutor y el Líder. Yo solo vi el ancho del panel (unos 800 px) en tema claro.

### Pruebas ejecutadas
- **Suite completa sobre una copia exacta de `4422678`** (`git archive` al scratch), `python -m pytest -q`: 944 pasan, 3 se omiten y 2 fallan. Las 2 fallas son las conocidas de Dropbox y no vienen de este diff:
  - `test_escaner_dropbox.py::test_terra_living_real`: el PDF real pesa distinto de lo esperado.
  - `test_parser_visitas.py::test_lista_coincide_con_dropbox_si_esta_disponible`: hay carpetas nuevas en Dropbox, por ejemplo «COLUMNAS  S-5 PARCIALES Y PORTICOS» sin número.
- **En el navegador:** el servidor arrancó con una BD copiada y las salidas en el scratch. Inicio, Bandeja y Visitas y trabajos cargan con datos reales de la copia.

### Pendientes de verificar
- **Push:** no se hace. La regla de la fase dice «sin push» hasta cerrarla, y Steven pidió que se le pregunte antes de cualquier push.
