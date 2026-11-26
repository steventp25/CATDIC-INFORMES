# B5b · Teclado, contraste, paridad y cierre (Etapa 5 · Fase B)

Ejecutor: Claude Sonnet 5.5 · 23/11/2026 · rama `claude/etapa5-fase-b-0020e1`.
Commits de B5b (sobre `09d213e`): `e2ef8e3` contraste, foco y trampa del visor; `78f9776` paridad §9 y §10; `a743dc7` búsquedas de cierre; más el commit de este informe.
No se tocó `BACKEND/`, `clasico/` ni `maquetas/`. Puerto 8766 solo; apagado al terminar.

## 1. Teclado

| Pantalla | A 1280 | A 375 | Resultado |
|---|---|---|---|
| Inicio | Tab recorre 60 paradas en orden de lectura (saltar, marca, Crear informe, navegación, cifras, cola, dudas); foco visible en todas; ninguna tapada | Igual; 15 paradas quedaban tras la barra inferior fija | 375 arreglado |
| Mis obras | 53 paradas, sin problemas | 1 parada («Planos y ficha») tras la barra | 375 arreglado |
| Obra · Resumen | 31 paradas; las pestañas de la obra son enlaces con `aria-current` | 1 parada tras la barra | 375 arreglado |
| Obra · Visitas y trabajos | 31 paradas | 6 paradas tras la barra | 375 arreglado |
| Obra · Planos y ficha | 12 paradas | 1 parada tras la barra | 375 arreglado |
| Obra · Avance | 33 paradas | 5 paradas tras la barra | 375 arreglado |
| Obra · Informes | 21 paradas | 1 parada tras la barra | 375 arreglado |
| Obra · Cierre | 22 paradas | 1 parada tras la barra | 375 arreglado |
| Bandeja de trabajo | 70 paradas (tope de la prueba) | 9 paradas tras la barra | 375 arreglado |
| Órdenes | 70 paradas (tope) | 2 paradas tras la barra; las pestañas de estado se mueven con las flechas (Derecha e Izquierda cambian y vuelven) | 375 arreglado |
| Informes | 17 paradas | 1 parada tras la barra | 375 arreglado |
| Crear informe | 31 paradas | 10 paradas tras la barra | 375 arreglado |
| Configuración | 12 paradas, sin problemas | 12 paradas, sin problemas | OK |

Causa y arreglo de la barra: el navegador deja el elemento enfocado en el borde de la ventana, justo bajo la barra inferior fija. Se añadió `scroll-padding` a `html` en móvil (arriba 4.75 rem por la cabecera pegada, abajo 5.5 rem más el área segura). Repetida la prueba: 0 paradas tapadas en las 13 pantallas a 375.

| Diálogo (abierto con Enter desde su botón) | 1280 | 375 | Resultado |
|---|---|---|---|
| Subir visita | Tab (30 pasos) y Mayús+Tab (12) no salen; foco visible; Escape cierra y devuelve el foco al botón | Igual | OK |
| Subir planos / Cambiar plano | Igual | Igual | OK |
| Datos de la obra | Igual | Igual | OK |
| Hacer informe | Igual | Igual | OK |
| Confirmar datos del plano | Igual; Escape cierra y el foco va al título (se abrió por dirección, sin botón) | Igual | OK |
| Visor / editor de recuadros | Tab escapaba del diálogo una vez por vuelta (4 de 42 pasos) | Igual | Arreglado |

Visor: la trampa de foco tomaba como último elemento el cuarto radio del grupo, que no es parada de Tab (un grupo de radios es una sola parada), así que el foco salía a la página. Ahora `atrapar` cuenta un solo radio por grupo y los dos radios de herramienta llevan `name="ed-herr"`. Repetida: 0 salidas.

| Otras comprobaciones | Resultado |
|---|---|
| «Saltar al contenido» (primer Tab tras cargar, Enter) en Inicio, Mis obras, Resumen y Órdenes, a 1280 y a 375 | OK: el foco pasa a `main` |
| Enter y Espacio activan botones y enlaces (Espacio sobre «Hacer informe» abre el diálogo) a 1280 y a 375 | OK |
| Flechas en pestañas de Órdenes (375, donde son `role="tab"`) | OK; a 1280 el tablero es de columnas, sin pestañas |
| Flechas en las pestañas de la obra | No aplica: son enlaces de una navegación con `aria-current`, se recorren con Tab (patrón correcto para enlaces). Lo anoto por si Steven las quiere como pestañas con flechas |
| Orden de lectura | Riel y barra primero (así lo dice DESIGN.md); en móvil la barra inferior va antes del contenido en el DOM aunque se vea abajo |

Limitación: Mayús+Tab se probó 12 pasos seguidos dentro de cada diálogo y un paso por pantalla; no se recorrió cada pantalla entera hacia atrás.

## 2. Contraste

Método: razón WCAG 2.x calculada por mí sobre `css/tokens.css` en sus dos temas (el bloque `:root`, `[data-tema="oscuro"]` y el `@media (prefers-color-scheme: dark)`), y además medida con Playwright sobre los colores calculados de **15.246 elementos de texto reales** en 15 pantallas a 1280, en claro y en oscuro (fondo efectivo = capas de fondo apiladas). Texto normal 4.5:1, texto grande y bordes de controles 3:1.

Resultado de la medición real: 0 textos por debajo de su umbral. Mínimo 5.92:1 en claro y 6.88:1 en oscuro. Los fondos con trama (el patrón de «pendiente de verificar») no se miden en bloque: su texto va sobre `--superficie-2` y el par está en la tabla.

Corregido (solo en tokens, misma dirección «Plano sellado»; aplicado en los tres bloques de tema):

| Token | Antes (claro / oscuro) | Ahora |
|---|---|---|
| `--borde-fuerte` | `#9aa5b1` (2.46 sobre superficie, 2.23 sobre fondo) / `#46586e` (2.31 / 2.52) | `#7a8693` / `#62768d` (3.3 a 3.9) |
| `--est-cola-borde` | `#b89a2e` (2.32) / `#8a7a2e` (2.98) | `#9a7f1c` / `#a8963a` |
| `--est-rev-borde` (solo oscuro) | `#6f5a99` (2.56) | `#9a82cc` |

Tabla completa (68 pares):

| Tipo | Par (primer plano sobre fondo) | Claro | Oscuro | Umbral | Corregido |
|---|---|---|---|---|---|
| texto | `--tinta` / `--fondo` | 14.64 | 15.41 | 4.5 | No hizo falta |
| texto | `--tinta` / `--superficie` | 16.16 | 14.12 | 4.5 | No hizo falta |
| texto | `--tinta` / `--superficie-2` | 14.67 | 12.68 | 4.5 | No hizo falta |
| texto | `--tinta-2` / `--fondo` | 6.47 | 8.88 | 4.5 | No hizo falta |
| texto | `--tinta-2` / `--superficie` | 7.14 | 8.14 | 4.5 | No hizo falta |
| texto | `--tinta-2` / `--superficie-2` | 6.48 | 7.31 | 4.5 | No hizo falta |
| texto | `--riel-tinta` / `--riel-fondo` | 13.98 | 17.32 | 4.5 | No hizo falta |
| texto | `--riel-tinta-2` / `--riel-fondo` | 8.64 | 10.7 | 4.5 | No hizo falta |
| texto | `--riel-tinta` / `--riel-hover` | 11.23 | 14.72 | 4.5 | No hizo falta |
| texto | `--riel-tinta-2` / `--riel-hover` | 6.94 | 9.09 | 4.5 | No hizo falta |
| texto | `--riel-tinta` / `--riel-activo` | 8.94 | 11.57 | 4.5 | No hizo falta |
| texto | `--sobre-acento` / `--acento` | 7.66 | 7.83 | 4.5 | No hizo falta |
| texto | `--sobre-acento` / `--acento-hover` | 9.97 | 9.95 | 4.5 | No hizo falta |
| texto | `--acento` / `--superficie` | 7.52 | 6.94 | 4.5 | No hizo falta |
| texto | `--acento` / `--fondo` | 6.81 | 7.57 | 4.5 | No hizo falta |
| texto | `--enlace` / `--superficie` | 7.52 | 8.82 | 4.5 | No hizo falta |
| texto | `--enlace` / `--fondo` | 6.81 | 9.63 | 4.5 | No hizo falta |
| texto | `--enlace` / `--aviso-fondo` | 6.55 | 7.09 | 4.5 | No hizo falta |
| texto | `--enlace` / `--sel-fondo` | 6.55 | 7.09 | 4.5 | No hizo falta |
| texto | `--crear-tinta` / `--crear-fondo` | 13.98 | 15.93 | 4.5 | No hizo falta |
| texto | `--crear-tinta` / `--crear-hover` | 15.3 | 18.95 | 4.5 | No hizo falta |
| texto | `--alerta` / `--superficie` | 6.35 | 6.61 | 4.5 | No hizo falta |
| texto | `--alerta` / `--error-fondo` | 5.26 | 5.91 | 4.5 | No hizo falta |
| texto | `--alerta-tinta` / `--error-fondo` | 6.39 | 7.1 | 4.5 | No hizo falta |
| texto | `--alerta-tinta` / `--superficie` | 7.71 | 7.94 | 4.5 | No hizo falta |
| texto | `--alerta` / `--fondo` | 5.75 | 7.21 | 4.5 | No hizo falta |
| texto | `--ok-tinta` / `--superficie` | 6.8 | 9.45 | 4.5 | No hizo falta |
| texto | `--ok-tinta` / `--ok-fondo` | 5.94 | 7.99 | 4.5 | No hizo falta |
| texto | `--ok-tinta` / `--fondo` | 6.16 | 10.31 | 4.5 | No hizo falta |
| texto | `--pend-tinta` / `--superficie` | 16.16 | 14.12 | 4.5 | No hizo falta |
| texto | `--pend-tinta` / `--fondo` | 14.64 | 15.41 | 4.5 | No hizo falta |
| texto | `--fased-tinta` / `--superficie` | 7.14 | 8.14 | 4.5 | No hizo falta |
| texto | `--fased-tinta` / `--fondo` | 6.47 | 8.88 | 4.5 | No hizo falta |
| texto | `--fased-tinta` / `--aviso-fondo` | 6.22 | 6.54 | 4.5 | No hizo falta |
| texto | `--nuevo-tinta` / `--nuevo-fondo` | 7.66 | 7.83 | 4.5 | No hizo falta |
| texto | `--deshab-tinta` / `--deshab-fondo` | 6.3 | 7.31 | 4.5 | No hizo falta |
| texto | `--seg-activo-tinta` / `--seg-activo` | 13.98 | 15.93 | 4.5 | No hizo falta |
| texto | `--tinta` / `--sel-fondo` | 14.08 | 11.35 | 4.5 | No hizo falta |
| texto | `--tinta` / `--aviso-fondo` | 14.08 | 11.35 | 4.5 | No hizo falta |
| texto | `--tinta` / `--seleccion` | 11.9 | 8.22 | 4.5 | No hizo falta |
| texto | `--tinta` / `--error-fondo` | 13.39 | 12.63 | 4.5 | No hizo falta |
| texto | `--tinta` / `--ok-fondo` | 14.11 | 11.93 | 4.5 | No hizo falta |
| texto | `--est-cola-tinta` / `--est-cola-fondo` | 7.65 | 9.11 | 4.5 | No hizo falta |
| texto | `--dudas-tinta` / `--dudas-fondo` | 6.27 | 8.25 | 4.5 | No hizo falta |
| texto | `--dudas-tinta` / `--dudas-suave` | 6.98 | 9.86 | 4.5 | No hizo falta |
| texto | `--est-rev-tinta` / `--est-rev-fondo` | 8.89 | 8.22 | 4.5 | No hizo falta |
| texto | `--pl-tinta` / `--papel` | 16.16 | 14.05 | 4.5 | No hizo falta |
| texto | `--pl-tinta-2` / `--papel` | 7.14 | 8.66 | 4.5 | No hizo falta |
| borde / foco | `--foco` / `--superficie` | 7.52 | 8.82 | 3.0 | No hizo falta |
| borde / foco | `--foco` / `--fondo` | 6.81 | 9.63 | 3.0 | No hizo falta |
| borde / foco | `--foco` / `--riel-fondo` | 2.0 | 9.95 | 3.0 | No aplica: No se usa: en el riel y las barras móviles el foco es `--riel-tinta` (13.98 / 17.32) |
| borde / foco | `--foco` / `--sel-fondo` | 6.55 | 7.09 | 3.0 | No hizo falta |
| borde / foco | `--borde-fuerte` / `--superficie` | 3.64 | 3.6 | 3.0 | Sí (antes 2.46 / 2.31) |
| borde / foco | `--borde-fuerte` / `--fondo` | 3.3 | 3.93 | 3.0 | Sí (antes 2.23 / 2.52) |
| borde / foco | `--sel-borde` / `--sel-fondo` | 6.55 | 5.58 | 3.0 | No hizo falta |
| borde / foco | `--pend-borde` / `--superficie` | 7.14 | 8.14 | 3.0 | No hizo falta |
| borde / foco | `--pend-borde` / `--fondo` | 6.47 | 8.88 | 3.0 | No hizo falta |
| borde / foco | `--fased-borde` / `--superficie` | 3.46 | 4.09 | 3.0 | No hizo falta |
| borde / foco | `--fased-borde` / `--fondo` | 3.13 | 4.47 | 3.0 | No hizo falta |
| borde / foco | `--est-cola-borde` / `--est-cola-fondo` | 3.29 | 4.31 | 3.0 | Sí (antes 2.32 / 2.98) |
| borde / foco | `--dudas-borde` / `--dudas-fondo` | 3.64 | 4.81 | 3.0 | No hizo falta |
| borde / foco | `--est-rev-borde` / `--est-rev-fondo` | 3.49 | 4.57 | 3.0 | Sí (antes 3.49 / 2.56) |
| borde / foco | `--alerta` / `--error-fondo` | 5.26 | 5.91 | 3.0 | No hizo falta |
| borde / foco | `--ok-tinta` / `--ok-fondo` | 5.94 | 7.99 | 3.0 | No hizo falta |
| borde / foco | `--pl-linea` / `--papel` | 3.46 | 3.52 | 3.0 | No hizo falta |
| borde / foco | `--tinta` / `--superficie` | 16.16 | 14.12 | 3.0 | No hizo falta |
| borde / foco | `--acento` / `--superficie` | 7.52 | 6.94 | 3.0 | No hizo falta |
| borde / foco | `--seleccion` / `--superficie` | 1.36 | 1.72 | 3.0 | No aplica: Es un relleno de selección, no un borde ni un texto; la selección lleva además borde `--sel-borde` (6.55 / 5.58) y marca |

Los dos pares que no llegan a 3:1 no son bordes de control: `--foco` sobre `--riel-fondo` no se usa (el riel pinta el foco con `--riel-tinta`), y `--seleccion` es un relleno. DESIGN.md · Accesibilidad tiene ahora las cifras medidas.

## 3. Paridad con el tablero anterior

`PLANES/etapa-5-inventario-ui.md` §9 marcada: **76 de 84 cumplen**, 8 huecos con su razón escrita en cada línea:
1. Marca «Control Taller» e insignia «Web Local v2.0»: la marca nueva es «CATDIC · Control de obras». Lo decide Steven.
2. La Mesa de Dudas ya no es un panel lateral con cierre por clic en el fondo, es una vista con dirección propia y botón «Cerrar» (decisión de B3e).
3. La Mesa no se abre sola tras sincronizar o subir una visita; el resultado trae el enlace «Abrir la Mesa de Dudas» (cuenta como dos líneas de la lista).
4. 12 de los 84 ganchos `data-*` de §6 se renombraron (nombres en la lista); los otros 72 existen con el mismo nombre.
5. No se comparó cada texto literal uno por uno (solo una muestra).
6. El mensaje de red «El backend no responde en http://localhost:8000…» ahora es «No se pudo conectar con el servidor local.».
7. Ya no hay capas apiladas (Mesa sobre Confirmar); se pasa por enlace y se vuelve con Atrás.

Comprobado por búsqueda en el código: las 26 rutas de §5 están en uso (la imagen de la hoja por `fetch` con respuesta `blob`).

§10 revisada (subsección 10.8 nueva): N1–N5, N7, N11, N14, N16, N17, N19, N24–N26 hechas; N8–N10 y N21–N23 son Fase D-b y D-c y salen «pendiente de verificar» sin simular; N6, N12, N13 parciales por Fase D-a. Huecos que no necesitan backend:
- **N20**: «Crear informe» no lista los servicios (STP, levantamiento de supervisión, estructural, visual, dimensional, esclerometría) con «disponible hoy» o «desarrollo futuro».
- **N15**: la Bandeja no tiene filtros (dependen de la ruta común, D-a).
- **N18**: la Mesa muestra la etiqueta literal y la página de las fotos, no la foto original.

Nada de lo que solo existía en `/clasico` y falta en el tablero nuevo se marcó como hecho.

## 4. Matriz final

Playwright, 14 rutas (Inicio, Mis obras, las 6 pestañas de la obra, Bandeja, Órdenes, Confirmar plano, Editor de recuadros, Configuración, Informes) × 375/768/1024/1280/1920 × claro/oscuro × movimiento normal y reducido = 20 combinaciones, 280 visitas:
- 20 de 20 OK: 0 peticiones fuera de `127.0.0.1:8766`, 0 errores de consola, sin desplazamiento horizontal, sin «0 %» en el texto, sin mención al tablero anterior.
- Con movimiento reducido: ninguna animación de `transform` ni `opacity` activa.
- Decisión del Líder sobre los paneles de varias líneas de la cola (error de proceso, sincronización, trabajo, regeneración, aviso tras subir planos): se dejan como están, sin reservar sitio (aparecen donde el usuario acaba de pulsar y el botón no se mueve). No se cuenta como rotura.

### Scripts de revisión del Líder (cada uno contra su copia de BD en su carpeta)

| Script | Resultado |
|---|---|
| `b5/lider.py` | 14 OK, 1 fallo: «aviso de tabla desconocida» (lee demasiado pronto, como avisó el Líder) |
| `b5/lider_tabla.py` | El aviso «La tabla 999 no existe en esta extracción. Se muestra la lista de tablas.» aparece: el fallo anterior es de tiempo del script |
| `b3b/lider.py` | 136 OK, 0 fallos |
| `b3c/lider.py` | 56 OK, 0 fallos (con la BD de b3c; con la mía falla porque faltan sus datos) |
| `b4/lider.py` y `b4/lider_comp.py` | 25 y 38 OK, 0 fallos |
| `b3f/lider.py` | 72 OK, 36 fallos tal cual; 108 OK, 0 fallos con una copia mía que sustituye `time.sleep` por `pg.wait_for_timeout` (con `time.sleep` Python no sirve las peticiones enrutadas y la pantalla se lee en «Cargando…») y compara el nombre del estado sin mayúsculas (las cabeceras de columna salen en mayúsculas por CSS) |
| `b3f/lider2.py` | 1 fallo del script: «depende de enlaza dentro de la pantalla» busca un `<a>`, y «Depende de» es un `<button class="enlace">`; `pantallas/ordenes.js` no cambia desde B4 (`git diff 85f528c HEAD` vacío), así que no lo causa B5 |
| `b3f/lider3.py` | Solo imprime datos, sin comprobaciones |

No edité ningún script del Líder; las copias adaptadas se borraron.

## 5. Suite (desde `BACKEND/`, todo en el scratch)

| Pasada | Resultado |
|---|---|
| Con `CATDIC_DROPBOX_RAIZ` en el scratch | 975 passed, 7 skipped, 0 failed |
| Sin esa variable | 977 passed, 3 skipped, **2 failed**: `test_escaner_dropbox.py::test_terra_living_real` y `test_parser_visitas.py::test_lista_coincide_con_dropbox_si_esta_disponible` (los dos de Dropbox real, los permitidos) |

## 6. Búsquedas en `FRONTEND/` (sin `clasico/`, `maquetas/`, `vendor/`)

`clasico` y `clásico`: 0. `transition: all`: 0. `ease-in` (no `-out`): 0. URLs `http(s)://`: 0. «0 %»: 0.
Para llegar a 0 hubo que reescribir frases que describían la regla (la de `transition: all`, la de `ease-in`, la de «0 %» y una URL de `localhost:8000` en PRODUCT.md) en DESIGN.md, PRODUCT.md, `base.css` e `indicadores.js`. Solo texto y comentarios.

## 7. Cambios de código

- `css/tokens.css`: `--borde-fuerte`, `--est-cola-borde`, `--est-rev-borde` (tres bloques de tema).
- `css/base.css`: `scroll-padding` en `html` en móvil.
- `js/visor-revision.js`: la trampa de Tab cuenta un solo radio por grupo.
- `js/editor-plano.js`: `name="ed-herr"` en los radios de herramienta.
- `FRONTEND/DESIGN.md`, `PRODUCT.md`, `js/indicadores.js` (comentario): texto.
- `PLANES/etapa-5-inventario-ui.md`: §9 y §10.8.

## 8. Limitaciones y para el Líder

- Contraste de textos con trama o imagen de fondo: no medido con Playwright (solo por tokens).
- La matriz usa datos sintéticos; las obras reales de Steven no se tocaron.
- Pregunta: ¿Steven quiere la insignia «Web Local v2.0», la apertura automática de la Mesa y los servicios de N20? Son los únicos huecos de §9 y §10 sin backend.
- `b3f/lider.py` y `lider2.py` necesitan actualizarse (tiempo, mayúsculas, `<button>`) si se van a seguir usando.

Scratch: `C:\WINDOWS\TEMP\claude\5241ace622d5cd23\bde6ad2c-34d6-42aa-bdc5-6b0fd7ef0f32\scratchpad\b5\` (scripts `contraste.py`, `contraste_real.py`, `tec_rutas.py`, `tec_dlg.py`, `tec_otros.py`, `a_matriz2.py`, `suite.ps1`).
