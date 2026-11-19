# B2 — Base del tablero nuevo (encargo del Líder de la Fase B al Ejecutor)

Fecha: 19/11/2026. Estilo elegido por Steven: **«Plano sellado»** (estilo B de `FRONTEND/maquetas/v2/`).

## Dónde se trabaja
- Worktree `C:\Users\Steve\OneDrive\Desktop\CATDIC-WEB\.claude\worktrees\etapa2-t7n-confirmacion-8210cf`, rama **`claude/etapa5-fase-b-0020e1`**.
  - No crees ramas, no cambies de rama.
  - No hagas push, merge ni stash.
  - No toques el checkout principal (`C:\Users\Steve\OneDrive\Desktop\CATDIC-WEB`).
- Trabajas por turnos con el Líder. Mientras trabajas, nadie más edita este worktree.
- **Zona permitida:** `FRONTEND/**` y `PLANES/etapa-5-reportes/B2.md`.
  - **No toques `BACKEND/**`**: ni rutas, ni respuestas, ni `main.py`.
  - No toques `FRONTEND/maquetas/**`. Es antecedente: se lee, no se edita.
- Python: `C:\Users\Steve\AppData\Local\Python\pythoncore-3.14-64\python.exe`.

## Reglas que no se discuten
- **Sin internet.** No se agrega ninguna librería, fuente, icono ni archivo descargado.
  - La única librería externa es Vue 3.5.13, ya en `FRONTEND/vendor/vue/vue.global.prod.min.js`. Lee su README.
  - Sin Tailwind, sin Font Awesome, sin CDN.
  - No ejecutes nada que contacte servicios externos. Eso incluye los comandos `impeccable concept-seed` y cualquier `curl`/`pip`/`npm` hacia internet.
- **Sin compilación** (D5): archivos `.html`, `.css` y `.js` que el servidor entrega tal cual.
- **Scripts clásicos, no módulos ES.** Usa `<script defer src=…>` con un espacio de nombres `window.CATDIC`.
  - Motivo: en Windows, `StaticFiles` puede servir `.js` como `text/plain` según el registro, y los módulos ES exigen el tipo correcto.
  - Comprueba el `Content-Type` que entrega el servidor de prueba y anótalo en el informe.
- **Textos en español.**
  - Lo que falta se muestra como «pendiente de verificar», como estado visible y nunca como hueco.
  - Nunca se inventan datos de ingeniería. Nunca se muestran indicadores como 0 %.
  - Lo que pide backend nuevo se rotula «Fase D» y no se simula.
- **Fechas** `DD/MM/AAAA`.
- **Commits locales** atómicos en la rama, en español. Cada mensaje termina con:
  `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`
  - Nunca se commitean capturas, PDFs ni `*.db`. Las capturas van al scratch.

## Qué hay que entregar
1. **`/clasico/`:** `git mv FRONTEND/index.html FRONTEND/clasico/index.html`, sin cambiar ni un byte.
   - Comprueba que abre en `http://127.0.0.1:<puerto>/clasico/` y sigue funcionando. Usa `API = 'http://localhost:8000'` fijo, así que al probar en otro puerto sus llamadas irán al 8000. Anótalo como limitación conocida y **no lo edites**: se retira al cierre de la fase.
   - El backend ya sirve `FRONTEND/` en `/` con `html=True`, así que `/clasico/` no pide cambios de backend.
2. **`FRONTEND/index.html` nuevo:** el armazón. Carga, en este orden:
   1. `vendor/vue/vue.global.prod.min.js`
   2. `css/tokens.css` y `css/base.css`
   3. `js/iconos.js`, `js/api.js`, `js/rutas.js` y `js/componentes.js`
   4. `js/pantallas/*.js`
   5. `js/app.js`

   Todas las rutas son relativas (`vendor/...`, nunca `http://localhost:8000/...`).
3. **`css/tokens.css`:** los tokens del estilo Plano sellado.
   - Salen de `FRONTEND/maquetas/v2/estilo-plano.css` y de las variables de `FRONTEND/maquetas/v2/base.css`.
   - Tema claro y oscuro con `:root[data-tema="oscuro"]`. Sin preferencia guardada, sigue a `prefers-color-scheme`.
   - Fuentes del sistema: Segoe UI Variable y Consolas, sin archivos.
   - El rojo de localización `RGB(220,0,0)` queda reservado para recuadros.
4. **`css/base.css`:** la estructura de la maqueta v2 adaptada al tablero real.
   - Riel lateral de 15 rem. Por debajo de 899 px, cabecera móvil y navegación inferior de 5 entradas.
   - `.caja` como contenedor (`container: caja / inline-size`) y filas que se acomodan a su caja: apiladas por debajo de 640 px, 4 columnas desde ahí.
   - Cajetín, pestañas de obra, `.pendiente`, `.fase-d`, botones con `scale(0.97)` al presionar, foco visible, objetivos táctiles de 44 px en móvil.
   - Bloque `prefers-reduced-motion`.
   - **No copies la barra de la maqueta** (selector de estado, «Otros estilos», «Datos sintéticos»): era solo de la maqueta.
5. **`js/api.js`:** cliente de la API.
   - Rutas relativas (`/api/...`). Funciones `get`, `post`, `put`, `patch` y `del` con JSON, y `enviarFormulario` para multipart.
   - Cada petición tiene un tiempo límite con `AbortController`. Ningún POST se reintenta solo.
   - Los errores se devuelven como un objeto `{estado, mensaje, detalle}`. El `mensaje` es un texto en español legible y sale del `detail` de FastAPI cuando existe.
   - «No se pudo conectar con el servidor local» si `fetch` falla.
   - Debe poder cubrir las 26 combinaciones de método y ruta de `PLANES/etapa-5-inventario-ui.md` §5. No hace falta escribir una función por ruta: B3 las agrega.
6. **`js/rutas.js`:** enrutador por hash; el botón Atrás del navegador funciona.
   - Rutas generales: `#/inicio`, `#/obras`, `#/bandeja`, `#/informes`, `#/configuracion` y `#/crear-informe`.
   - Rutas de obra: `#/obra/<id>/<pestaña>`, con pestaña `resumen | visitas | planos | avance | informes | cierre`.
   - Una ruta desconocida lleva a Inicio con un aviso.
   - Al cambiar de pantalla, el foco pasa al `<h1>`.
7. **`js/componentes.js`:** componentes Vue compartidos, como objetos con `template` en texto.
   - `Bloque`: estados cargando con huesos y `aria-busy`, vacío con mensaje y acción, error con `role="alert"` y botón «Reintentar», y contenido.
   - `Pendiente` («pendiente de verificar»), `FaseD` (etiqueta discontinua «… · Fase D-a/b/c») e `Icono` (SVG en línea, en `js/iconos.js`; toma los de `maquetas/v2/app.js`).
   - `Cajetin` y `PestanasObra`.
8. **`js/app.js`:** el armazón.
   - Riel con la marca CATDIC y «Crear informe» siempre visible.
   - Navegación D6: Inicio · Mis obras · Bandeja de trabajo · Informes · Configuración, con `aria-current`.
   - Hueco «Lectura asistida · Fase C». Enlace «Saltar al contenido».
   - Cabecera móvil con Crear informe y navegación inferior.
9. **`js/pantallas/*.js`:** una pantalla por futura tarea de B3. Cada una con su `<h1>` y un estado vacío honesto: qué tarea la construye (B3a…B3g) y un enlace «Mientras tanto: tablero clásico» a `/clasico/`. **Dos lecturas reales** para probar el cliente:
   - **Configuración:** «Servidor local» lee `GET /api/dashboard` y muestra conectado, cargando o error con Reintentar. Incluye el selector de tema (claro, oscuro o del sistema), guardado en `localStorage` con try/catch.
   - **Obra (`#/obra/<id>/…`):** la cabecera lee la obra de `GET /api/dashboard`, que trae `proyectos`, y muestra su nombre y su cajetín. Cada campo que la respuesta no trae dice «pendiente de verificar». Si la obra no existe, aparece el estado vacío «No se encontró la obra» con un enlace a Mis obras. Las 6 pestañas navegan; el contenido de cada pestaña es el estado vacío de B3.

## Cómo se prueba (obligatorio)
- **Backend desde este worktree con una copia de la BD**, nunca con la real.
  - Copia `C:\Users\Steve\OneDrive\Desktop\CATDIC-WEB\BACKEND\catdic_local.db` al scratch.
  - Ponle `CATDIC_DB_PATH` apuntando a esa copia.
  - Arranca `uvicorn main:app --port 8765` desde `BACKEND/`, en segundo plano. Nunca uses el puerto 8000.
  - Dropbox es de solo lectura: no pulses «Sincronizar» ni subas nada.
- **Playwright** (`python -m playwright`, Chromium) a 375, 768, 1024, 1280 y 1920 px, en claro y oscuro, en todas las rutas. Comprueba:
  - 0 peticiones fuera de `127.0.0.1:8765`;
  - 0 errores de consola;
  - sin desplazamiento horizontal;
  - orden de Tab correcto: Saltar → marca → Crear informe → navegación → contenido;
  - el botón Atrás funciona;
  - el estado de error de Configuración con el servidor apagado.
- **Suite del backend sin cambios:** `pytest` desde la raíz da 943 pasan y 2 fallan por Dropbox. Corre el comando y anota el resultado real.

## Informe
Escribe `PLANES/etapa-5-reportes/B2.md` con:
- archivos creados;
- decisiones y por qué;
- `Content-Type` observado;
- resultados de Playwright (tabla por tamaño y tema);
- resultado de la suite;
- limitaciones conocidas;
- hashes de los commits.

Termina con los commits hechos y la carpeta del scratch donde dejaste las capturas.
