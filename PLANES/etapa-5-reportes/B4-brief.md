# B4 — Movimiento y pulido — encargo del Líder al Ejecutor

Fecha: 23/11/2026. B3 está completa y aprobada (B3a, B3b, B3c, B3d, B3e, B3f, B3g y B3g-2). B3h **no** está autorizada. El Director lanzó B4 el 23/11 («Adelante con B4», sin push). Estilo **Plano sellado** (`FRONTEND/DESIGN.md`), modo *Operate*: es una herramienta de trabajo, así que el movimiento es poco, rápido y con un motivo.

## Dónde se trabaja (igual que en B3f)
- **Worktree y rama:** `C:\Users\Steve\OneDrive\Desktop\CATDIC-WEB\.claude\worktrees\etapa2-t7n-confirmacion-8210cf`, rama `claude/etapa5-fase-b-0020e1`.
  - No crees ni cambies de rama. Nada de push, merge, stash, checkout ni reset. No toques el checkout principal.
  - Trabajas por turnos con el Líder.
- **Zona:** `FRONTEND/**` (menos `maquetas/`, `clasico/` y `vendor/`), `FRONTEND/DESIGN.md` y `PLANES/etapa-5-reportes/B4.md`.
  - **B4 no tiene excepción de backend: no se toca nada de `BACKEND/`.** Puedes leerlo.
- **Tablero clásico.** No se borra ni se edita `FRONTEND/clasico/` ni `BACKEND/tests/test_frontend_servido.py`. Ninguna mención ni enlace al clásico en el tablero nuevo.
- **Sin red.**
  - Nada de librerías nuevas (ni Motion ni GSAP): CSS y, solo si hace falta, la Web Animations API del navegador.
  - **No ejecutes los scripts de `impeccable`** ni nada que pueda descargar o llamar a internet. La revisión de `impeccable` la hace el Líder.
- **Python:** `C:\Users\Steve\AppData\Local\Python\pythoncore-3.14-64\python.exe`.

## Skills que debes leer antes de tocar nada
Cárgalas con la herramienta Skill si la tienes; si no, lee `C:\Users\Steve\.claude\skills\<nombre>\SKILL.md`:
- `animate`;
- `choreograph`;
- `emil-design-eng`;
- `animation-performance`;
- `apple-design`.

En el informe, di **qué decisión concreta tomaste por cada una**. No basta con nombrarlas (regla 8 del plan madre).

## Parte 1 — Movimiento con propósito
Primero haz un inventario: recorre el tablero (`js/`, `js/pantallas/`, `css/base.css`) y apunta en el informe cada sitio donde algo aparece, desaparece o cambia de golpe.

Para cada sitio, decide con el marco de `emil-design-eng`:
- ¿cuántas veces al día lo ve Steven?
- ¿qué propósito tendría animarlo?
- si se anima: qué curva y qué duración.

Lo que **no** se anima también va al informe, con su motivo.

### Reglas fijas
- **No se anima:**
  - nada que dispare el teclado;
  - el cambio de pantalla ni el de pestaña (se usan decenas de veces al día);
  - la Mesa ni la Bandeja al filtrar.
- **Propiedades:** solo `transform` y `opacity`, y color o fondo de hasta 150 ms. Nada de `height`, `width`, `top`, `margin` ni `transition: all`.
- **Duraciones:** 300 ms o menos. Al presionar, 100–160 ms. Diálogos, 180–240 ms.
- **Curvas:** las de `tokens.css` (`--ease-out`; crea `--ease-in-out` si la necesitas). Nunca `ease-in` para la interfaz. La salida es más rápida que la entrada.
- **Cómo se anima:**
  - Nada aparece desde `scale(0)`: desde `scale(0.97)` con `opacity: 0`.
  - Los diálogos (`<dialog>` con `showModal`) quedan centrados.
  - Un desplegable o menú crece desde su disparador.
  - Entradas con `@starting-style` o con transiciones de CSS, que se pueden interrumpir. `@keyframes` solo para lo que se repite (el latido de los huesos ya existe).
- **`prefers-reduced-motion: reduce`:**
  - quita todo desplazamiento y escala;
  - deja como mucho un fundido corto de opacidad o el cambio de color;
  - la regla global de `base.css` ya existe: comprueba que sigue cubriendo lo nuevo.
- **Sin saltos de diseño:** nada empuja el contenido al aparecer. Si algo se inserta, su sitio está reservado.

### Candidatos a valorar
No es obligatorio animarlos todos; decide y justifica:
1. **Diálogos y confirmaciones:**
   - Nueva obra, Subir visita, Regenerar informe y Confirmar datos del plano;
   - entrada con fundido y `scale(0.97 → 1)`, y el fondo (`::backdrop`) con fundido;
   - salida más corta;
   - no rompas el foco ni el `Escape`.
2. **Avisos de resultado** (Sincronizar, Procesar cola, guardar recuadro, responder duda, confirmar tabla):
   - entrada corta para que se note que algo cambió, sin desplazar nada;
   - la región `aria-live` sigue igual.
3. **Avance del procesador en vivo (B3d):** cuando cambia el paso o el estado de la visita, un cambio de color o fondo breve. Nada de barras de progreso inventadas.
4. **Al presionar:**
   - que `scale(0.97)` llegue a todo lo que se presiona: botones, pestañas de órdenes y filas que son enlaces, si no rompe el diseño;
   - el hover solo con `@media (hover: hover) and (pointer: fine)`.
5. **Visor de revisión y editor de recuadros (B3b y B3e):**
   - el zoom y el «Ir al recuadro» del visor pueden moverse suavemente, solo con `transform`, siempre que se puedan interrumpir;
   - al arrastrar, el seguimiento es 1:1 (no animes lo que sigue al puntero).
6. **Tarjeta de orden enlazada por «depende de» (B3f):** al saltar a ella, una señal breve en la tarjeta de destino (contorno o fondo de ~600 ms como máximo) para que se vea adónde se fue el foco.

## Parte 2 — Pulido: las notas acumuladas (todas obligatorias)
1. **Órdenes (B3f):** sin `?estado=`, el modo pestañas abre la **primera pestaña que tenga órdenes**, en el orden de las columnas. Si no hay ninguna, abre «Pendiente». Con `?estado=` se respeta lo que diga la dirección.
2. **Inicio (B3f):**
   - el enlace de «Órdenes abiertas» solo contiene la cifra;
   - dale un nombre accesible completo («1 orden abierta: ver órdenes de trabajo», con singular o plural según la cifra);
   - el texto visible puede seguir siendo la cifra.
3. **Órdenes a 1280 px (B3f):**
   - las columnas 5 y 6 quedan tras un desplazamiento dentro del tablero;
   - que se note que hay más (por ejemplo un sombreado en el borde o el rótulo «6 columnas · desliza»), sin franjas laterales de color de estado;
   - que el contenedor se pueda desplazar con el teclado (`tabindex="0"` y un nombre accesible).

   Si consigues que las 6 quepan a 1280 sin bajar de unos 170 px por columna ni partir los `doc_id`, también vale. Dilo en el informe.
4. **Confirmar datos del plano (B3c): dos tablas iguales.**
   - Dos tablas se ven idénticas en la lista («f'c por rango · pág. 1 · hoja 20 · NIVEL 2»).
   - Muestra lo que las distingue: el número de tabla o la clave que ya trae el servidor (`GET .../tablas-extraidas`; mira `BACKEND/plano/extractor.py`, sin tocarlo).
   - No inventes un nombre.
5. **Confirmar datos del plano (B3c): el diálogo es más alto que la ventana.**
   - A 1024×768, `dialog.conf` mide 1064 px de alto.
   - Un `scrollIntoView` hecho por código lo desplazó 96 px, se perdió la cabecera y se vio la página de detrás.
   - Encuentra qué elemento se sale. El diálogo debe caber en la ventana (`max-height` con `dvh`) y desplazarse solo por dentro (`conf-det`), con la cabecera siempre visible.
6. **Confirmar datos del plano (B3c): barra fija en móvil.**
   - A 375 px, la barra superior fija (Extraer, Mesa y Cerrar, uno por línea) ocupa unos 210 px; compáctala, por ejemplo en una sola fila con iconos y texto corto.
   - Los objetivos siguen en 44 px o más, y nada se queda sin nombre accesible.
7. **Confirmar datos del plano (B3c): «Falla:» muestra claves en bruto** (`sin_notas_de_modificacion`).
   - Muestra un texto legible en español.
   - Para las claves que conozcas leyendo el backend, usa un diccionario con su texto exacto.
   - Para las demás, cambia los `_` por espacios y pon la primera en mayúscula. No inventes el significado.
   - La clave original queda en `title` o en un `data-` para quien la necesite.
8. **Editor de recuadros (B3b):**
   - al aparecer «Ir al recuadro», la barra del visor pasa a dos líneas y el panel baja unos 38 px;
   - reserva su sitio: siempre visible y deshabilitado (con motivo) hasta que haya recuadro o borrador;
   - comprueba a 800 px de ancho que el panel ya no se mueve.
9. **Tarjeta del plano (B3b):** dice «huellas sha256 de abajo», pero están arriba. Corrige el texto para que diga dónde están de verdad.

## Diseño (siguen todas las reglas de B2–B3f)
- Sin franjas laterales de color: el estado se muestra con su palabra, un icono y un borde completo.
- Container queries.
- Objetivos táctiles de 44 px o más en móvil.
- Foco visible.
- Fechas `DD/MM/AAAA`.
- «pendiente de verificar» para lo que falta; nunca «0 %».
- Textos en español.
- Actualiza la sección **Movimiento** de `FRONTEND/DESIGN.md` con lo que de verdad quede: qué se anima, con qué curva y duración, qué no se anima y por qué, y `prefers-reduced-motion`.

## Commits
- Atómicos, en español, terminados en `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Al menos uno para el movimiento y uno para el pulido. Mejor si cada nota que toque varios archivos va en su propio commit.
- Nunca capturas, PDFs ni `*.db`.

## Cómo se prueba (las reglas de B3f)
- **Servidor:**
  - backend desde este worktree, con una **copia** de la BD en el scratch `C:\WINDOWS\TEMP\claude\5241ace622d5cd23\bde6ad2c-34d6-42aa-bdc5-6b0fd7ef0f32\scratchpad\b4\` (puedes copiar la de `scratchpad\b3f\copia.db`, que ya tiene órdenes sintéticas, y la obra sintética de B3c de `scratchpad\b3c\`);
  - las 5 variables `CATDIC_*` apuntan al scratch;
  - puerto **8766**;
  - no cierres el 8765 ni el 8767, nunca uses el 8000, y apaga tu servidor al terminar.
- **Dropbox:** nada contra `C:\Users\Steve\CATDIC Dropbox\`.
- **Playwright** (Chromium) a 375, 768, 1024, 1280 y 1920 px, en claro y oscuro, y además con `reduced_motion='reduce'`. Comprueba:
  - 0 peticiones fuera de `127.0.0.1:8766`;
  - 0 errores de consola;
  - sin desplazamiento horizontal de la página;
  - **cada animación nueva:**
    - con `document.getAnimations()` (o los estilos calculados), que solo toca `transform`, `opacity` o color, y dura 300 ms o menos;
    - con `reduced_motion='reduce'`, que no hay escala ni desplazamiento;
  - **sin saltos:** la posición de los botones vecinos no cambia al aparecer un aviso o «Ir al recuadro» (mide `getBoundingClientRect` antes y después);
  - **diálogos:**
    - el foco entra y vuelve;
    - `Escape` cierra;
    - interrumpir (abrir y cerrar enseguida) no deja el diálogo a medias;
  - **cada una de las 9 notas** del pulido, con su prueba (la 5 a 1024×768; la 6 a 375; la 8 a 800 px).
- **Que nada se rompa:** repite las comprobaciones principales de B3 en Inicio, Mis obras, la obra (6 pestañas), la Bandeja, la Mesa, las Órdenes, Confirmar datos del plano y el editor. Puedes reutilizar los scripts del scratch de B3b, B3c y B3f.
- **Suite del backend** desde `BACKEND/`, dos veces: todo en el scratch, y sin `CATDIC_DROPBOX_RAIZ`. Solo pueden fallar las 2 de Dropbox.
- **Búsqueda final:**
  - «clasico» y «clásico» en `FRONTEND/` (sin `clasico/`, `maquetas/` ni `vendor/`): 0 resultados;
  - `transition: all` y `ease-in` (sin `-out`): 0 resultados.

## Informe
`PLANES/etapa-5-reportes/B4.md` con:
- archivos tocados;
- el inventario de movimiento (qué se anima y qué no, con su motivo);
- la decisión de cada skill;
- las 9 notas, una por una, con cómo se comprobó;
- la tabla de Playwright, incluida la de movimiento reducido;
- la suite;
- las limitaciones;
- los hashes;
- la carpeta del scratch con las capturas.
