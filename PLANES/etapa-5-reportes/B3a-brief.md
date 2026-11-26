# B3a — Inicio y Mis obras (encargo del Líder de la Fase B al Ejecutor)

Fecha: 19/11/2026. B2 está aprobada por el Director. Estilo: **Plano sellado**.
- Cómo se ve: `FRONTEND/DESIGN.md` y los archivos `FRONTEND/css/tokens.css` y `FRONTEND/css/base.css`.
- Referencia visual de estas dos pantallas: `FRONTEND/maquetas/v2/plano.html` (funciones `inicio()` y `obras()` de `maquetas/v2/app.js`). Está hecha con datos sintéticos: se toma la forma, nunca los datos.

## Dónde se trabaja (igual que en B2)
- **Lugar:** worktree `C:\Users\Steve\OneDrive\Desktop\CATDIC-WEB\.claude\worktrees\etapa2-t7n-confirmacion-8210cf`, rama **`claude/etapa5-fase-b-0020e1`**.
  - No crees ramas ni cambies de rama.
  - Nada de push, merge ni stash.
  - No toques el checkout principal.
- **Turnos:** trabajas por turnos con el Líder. Mientras trabajas, nadie más edita el worktree.
- **Zona permitida:** `FRONTEND/**` y `PLANES/etapa-5-reportes/B3a.md`.
- **Prohibido tocar:**
  - `BACKEND/**`: se lee para entender las respuestas, nunca se edita.
  - `FRONTEND/maquetas/**`
  - `FRONTEND/clasico/**`
  - `FRONTEND/vendor/**`
- **Python:** `C:\Users\Steve\AppData\Local\Python\pythoncore-3.14-64\python.exe`.

## Reglas que no se discuten (las de B2 siguen vigentes)
- **Sin internet:**
  - No se añade ninguna librería, fuente ni descarga.
  - No ejecutes nada que contacte servicios externos (ni `impeccable concept-seed`, ni `curl`, `pip` o `npm` hacia internet).
  - En las pruebas, bloquea con `page.route` cualquier petición que no vaya a `127.0.0.1:<puerto>`.
- **Técnica:** sin compilación, con scripts clásicos y el espacio `window.CATDIC`. Usa los componentes de `js/componentes.js` (`Bloque`, `Pendiente`, `FaseD`, `Icono`, `Cajetin`) y `C.formato`, y el cliente `C.api`.
- **Regla de Oro:**
  - Lo que falta se muestra como «pendiente de verificar».
  - Nunca se inventan cifras ni datos de ingeniería.
  - Los contadores que el backend devuelve siempre en 0 (`stats.bloqueadas`, `stats.vencen_7_dias`) **no se muestran como 0**: van como «pendiente de verificar» con la etiqueta `FaseD` «D-a».
  - Lo que necesita backend nuevo se rotula «Fase D» y no se simula.
- **Formato:** fechas `DD/MM/AAAA` y textos en español.
- **Commits:** atómicos, en español, y cada uno termina con `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Nunca se commitean capturas, PDFs ni `*.db`.

## Qué hay que construir

### 1. Datos compartidos
Inicio y Mis obras leen las mismas rutas:
- `GET /api/dashboard` (`stats`, `proyectos`, `visitas`, `ordenes`, `planos_vigentes`);
- `GET /api/dudas?resuelta=false`.

Si te ayuda, crea un módulo pequeño (por ejemplo `js/datos.js`) que pida las dos y deje que cada pantalla vuelva a pedirlas con «Reintentar».
- Cada lectura tiene su propio estado.
- Si falla `/api/dudas`, Inicio sigue mostrando lo del tablero, y el bloque de dudas muestra su error («No se pudo leer la Mesa de Dudas»), como hoy Z7.
- Nada de recargas automáticas por tiempo.

### 2. Inicio (`js/pantallas/inicio.js`) — necesidades N6 y N7 de `PLANES/etapa-5-inventario-ui.md` §10.2
- **Cabecera:** `<h1>Inicio</h1>` y la fecha de hoy en `DD/MM/AAAA`. Conserva el aviso de «ruta desconocida» que ya existe.
- **Cifras** (paridad Z9–Z13), en cajetín de cifras:
  - Obras activas (`stats.proyectos_activos`), Visitas en cola (`stats.visitas_en_cola`) y Órdenes abiertas (`stats.ordenes_abiertas`): número real.
  - Bloqueadas y Vencen en ≤ 7 días: «pendiente de verificar» con FaseD «D-a».
  - Cada cifra enlaza a donde vive. Las obras, a `#/obras`. Las visitas y las órdenes, a la pantalla de la tarea que las construirá (las rutas existen aunque estén vacías).
- **Prioridades:** filas al estilo de la maqueta (tipo · obra · dónde · motivo · siguiente paso), con datos reales:
  - visitas con estado «Con dudas» o con dudas bloqueantes abiertas (cuenta dudas abiertas y bloqueantes, como hoy Z15);
  - dudas de obra sin visita;
  - visitas en cola pendientes de procesar.
  - Ordénalas por bloqueante, después «Con dudas», después cola.
  - Cada fila enlaza a la pestaña de su obra: `#/obra/<id>/visitas` para visitas y dudas de visita, `#/obra/<id>/resumen` para dudas de obra. Si `rutas.js` admite parámetros, añade `?visita=<id>` para que B3d y B3e puedan abrir el registro exacto. Si no, deja el enlace a la pestaña y anótalo.
  - **Antigüedad:** solo si sale de un dato real (`fecha_visita`). Sin fecha, «pendiente de verificar». No uses otra fecha.
- **Revisiones de planos:**
  - Lee (sin editar) `BACKEND/plano/confirmacion.py` y la ruta `GET /api/proyectos/{id}/tablas-extraidas`.
  - Si la respuesta trae un estado explícito de «sin confirmar», muestra por obra cuántas tablas faltan por confirmar, con enlace a `#/obra/<id>/planos`.
  - Si no hay un campo inequívoco, no lo deduzcas: muestra «pendiente de verificar» y explica en el informe qué falta.
  - Solo para obras con plano vigente.
- **Entregas y vencimientos:** bloque con FaseD «D-a» y «pendiente de verificar». Sin filas inventadas.
- **Próximas acciones:** por obra, `proyectos[].observaciones` (en el tablero clásico es la columna «Próxima Acción»). Si está vacía, «pendiente de verificar».
- **Mis obras (mini):** lista corta con enlace a `#/obra/<id>/resumen`.
- **Estados:** cada bloque usa `Bloque`, con estos 4 estados distintos:
  - cargando;
  - vacío (texto honesto y acción; por ejemplo «No hay pendientes.»);
  - error con «Reintentar»;
  - pendiente.

### 3. Mis obras (`js/pantallas/obras.js`) — paridad Z14 y Z14a
- **Lista de obras,** ordenada por nombre (`localeCompare` en `es`). Cada obra es una fila o tarjeta que se acomoda a su `.caja` con container queries, como en B2. Muestra:
  - nombre;
  - tipo y formato;
  - cliente;
  - supervisor;
  - estado del informe;
  - plano vigente: «Rev. N · etiqueta», fecha `DD/MM/AAAA` y «certificado por X», con el sha256 vectorial y el sellado en `title`; si no hay plano, la insignia «sin plano vigente», que es un estado real y no un dato que falte;
  - número de visitas;
  - dudas abiertas;
  - próxima acción.

  Un campo que falta es «pendiente de verificar». No uses «—» ni «Pendiente» como relleno; así se corrige el tablero clásico según la Regla de Oro.
- **Toda la fila** abre `#/obra/<id>/resumen`.
- **Accesos directos por obra** (paridad A11–A17). Son enlaces a la pestaña que los construirá, sin simular la acción:
  - «Planos y ficha» → `#/obra/<id>/planos`;
  - «Visitas» → `#/obra/<id>/visitas`, solo en obras de Supervisión;
  - «Dudas de la obra: N» → `#/obra/<id>/resumen`, solo si N > 0.
- **«Nueva obra»** (paridad M2 en modo nueva y A28):
  - Un formulario en un diálogo accesible (`<dialog>` o equivalente con foco atrapado, Escape, y foco que vuelve al botón al cerrar), con los campos, validaciones y mensajes de `PLANES/etapa-5-inventario-ui.md` §2 M2 y §3.5 A28. Lee `FRONTEND/clasico/index.html` (líneas 413-471 y `enviarObra`, 1026-1070).
  - Hazlo como un componente reutilizable (`FormularioPlanos` o similar), porque B3b lo usará en modo «cambiar plano».
  - Flujo: `POST /api/proyectos` y después `POST /api/proyectos/{id}/planos` multipart. Si la subida falla después de crear la obra, el diálogo sigue abierto y reintenta solo la subida, con el mensaje de A28.
  - Al terminar, aviso verde con el texto de A28 y enlace a la obra nueva.
  - Usa `C.api.post` y `C.api.enviarFormulario`. Ningún POST se reintenta solo.

## Cómo se prueba (obligatorio)
- **Backend desde este worktree con una copia de la BD**, nunca la real:
  - copia `C:\Users\Steve\OneDrive\Desktop\CATDIC-WEB\BACKEND\catdic_local.db` al scratch;
  - `CATDIC_DB_PATH` apuntando a la copia;
  - desde `BACKEND/`, `uvicorn main:app --port 8765`, en segundo plano;
  - nunca el puerto 8000. Al terminar, apaga el servidor.
- **Antes de cualquier POST,** lee en `BACKEND/` (`obras.py`, `config.py`) dónde escribe `POST /api/proyectos/{id}/planos`.
  - Pon las variables de `config.py` (BD, raíz de Dropbox y carpeta de datos) apuntando al scratch.
  - Si algo escribiría fuera del scratch o en Dropbox, **no lo ejecutes**: prueba ese paso con `page.route` (respuesta simulada solo en la prueba) y anótalo en el informe.
  - Los PDF de prueba se generan en el scratch y no se commitean. Nunca pulses «Sincronizar» ni conectes Dropbox.
- **Playwright** (Chromium) a 375, 768, 1024, 1280 y 1920 px, en claro y oscuro, en `#/inicio` y `#/obras`.
  - **Comprueba:**
    - 0 peticiones fuera de `127.0.0.1:8765`;
    - 0 errores de consola;
    - sin desplazamiento horizontal;
    - foco y Tab correctos en el diálogo de Nueva obra;
    - el botón Atrás.
  - **Estados, con `page.route` solo en la prueba:**
    - cargando (respuesta retrasada);
    - vacío (`proyectos: []`, `visitas: []`, dudas `[]`);
    - error del tablero y error de dudas por separado;
    - datos reales de la copia.
  - **Peor caso** (como `break-ui`): nombres de obra de 120 caracteres, cliente con una palabra larga sin espacios, 40 obras, 0 obras y campos nulos. Nada se sale de su caja ni se aplasta.
- **Suite del backend** desde `BACKEND/`: debe dar solo las 2 fallas de Dropbox. Anota el resultado real.

## Informe
Escribe `PLANES/etapa-5-reportes/B3a.md` con:
- archivos tocados;
- decisiones y por qué;
- qué ítems de la checklist de paridad (§9 «Tarjetas y tablas» y la parte «Nueva obra» de «Cabecera y avisos») quedan cubiertos y cuáles no (y qué tarea los cubre);
- qué necesidades N6 y N7 se cumplen;
- lo que quedó como «pendiente de verificar» o Fase D, y por qué;
- la tabla de Playwright por tamaño y tema;
- los estados probados;
- el peor caso;
- la suite;
- las limitaciones;
- los hashes de los commits;
- la carpeta del scratch con las capturas.
