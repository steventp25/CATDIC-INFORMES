# Design

<!-- Sistema de diseño del tablero CATDIC, escrito a partir de lo construido en B2 (19/11/2026). La fuente de verdad son `FRONTEND/css/tokens.css` y `FRONTEND/css/base.css`; si algo de aquí no coincide con ellos, mandan los archivos. -->

## Dirección
**«Plano sellado»**, elegido por Steven el 19/11/2026 entre tres propuestas (`FRONTEND/maquetas/v2/`). El mundo es la hoja de planos estructurales:
- papel con retícula;
- tinta azul-negra;
- el **cajetín** para leer la obra;
- **globos** para los ejes;
- un **hueco discontinuo** para lo que falta.

Es una herramienta de trabajo (modo *Operate*). El estilo vive en los detalles; los controles y la navegación son los habituales.

## Principios visuales
1. **El plano manda.** Los datos van en Consolas, dentro de celdas de cajetín con líneas de tinta, y siempre con su fuente al lado.
2. **Lo que falta es un estado, no un vacío.**
   - `.pendiente` muestra «pendiente de verificar» en un recuadro discontinuo.
   - En los indicadores, el hueco lleva una X. Nunca se dibuja una barra vacía ni 0 %.
3. **Lo que pide backend nuevo se rotula.** `.fase-d` es una píldora discontinua «… · Fase D-a/b/c», sin simular datos.
4. **El rojo es del plano.** `--rojo-plano` (`RGB(220,0,0)`) se reserva para recuadros de localización. Los errores usan `--alerta`, que es otro rojo.
5. **Sin red.**
   - Fuentes del sistema de Windows.
   - Iconos SVG en línea (`js/iconos.js`).
   - Una sola librería: Vue 3.5.13 local.

## Tokens (`css/tokens.css`)
| Grupo | Claro | Uso |
|---|---|---|
| Fondo / superficie | `--fondo #f1f2ee`, `--superficie #fdfdfb`, retícula `--reticula` | papel con retícula de 24 px; cajas lisas |
| Tinta | `--tinta #14202e`, `--tinta-2 #4a5868` | texto y líneas del cajetín; secundario |
| Riel | `--riel-fondo #16263a` | navegación lateral y barras móviles |
| Acento | `--acento #1f4fa8` (azul de sello) | acción principal, enlaces, foco |
| Crear informe | `--crear-fondo #f2f5f8` sobre el riel | botón siempre visible |
| Estados | `--alerta`, `--ok-tinta`, `--pend-*`, `--fased-*`, `--nuevo-*` | error, bien, pendiente, Fase D, nuevo |

- **Tema oscuro:** con `:root[data-tema="oscuro"]`, o con `prefers-color-scheme` cuando no hay preferencia guardada (`js/tema.js` la aplica antes de pintar).
- **Tipos:**
  - Texto y títulos: `--f-texto` y `--f-titulo` (Segoe UI Variable).
  - Datos: `--f-dato` (Consolas), con cifras tabulares.
  - Rótulos del cajetín: en mayúsculas con +0.1 em.
- **Espacios:** de `--esp-1` (4 px) a `--esp-6` (32 px).
- **Radios:** 2 px en controles y 0 en cajas: la hoja no se redondea.

## Componentes (`js/componentes.js` + `css/base.css`)
| Componente | Qué es |
|---|---|
| Armazón | Riel de 15 rem con la marca, «Crear informe» y la navegación D6. Por debajo de 899 px: cabecera móvil y barra inferior de 5 entradas de 44 px o más. |
| `Bloque` | Resuelve los estados de cada zona: cargando (huesos, `aria-busy`), vacío (mensaje y acción), error (`role="alert"` y «Reintentar») y contenido. |
| `Cajetin` | Rejilla `auto-fit` de celdas con líneas de tinta; rótulo arriba y dato en Consolas debajo. |
| `PestanasObra` | Resumen · Visitas y trabajos · Planos y ficha · Avance · Informes · Cierre, con `aria-current`. |
| `.caja` | Contenedor (`container: caja / inline-size`). Lo de dentro se acomoda al ancho de la caja, no al de la ventana. |
| Filas de pendientes | Apiladas por debajo de 640 px de caja y en 4 columnas desde ahí. En la Bandeja, tabla de 6 desde 880 px (maqueta v2; se construye en B3). |
| `.btn` | `.btn-pri`, `.btn-sec` y `.btn-crear`; al presionar, `scale(0.97)` con `--ease-out`. |
| `Pendiente`, `FaseD`, `Icono` | Los estados honestos y los iconos. |

## Movimiento
Principio: el movimiento solo confirma una acción del puntero o explica de dónde viene algo. Nada decora.

Reglas
- Solo `transform`, `opacity` y color/fondo/borde (estos, hasta 150 ms). Nada de `height`, `width`, `top`, `margin` ni `transition: all`.
- Curva `--ease-out` de `tokens.css`; nunca `ease-in`. Total ≤ 300 ms.
- Las entradas parten de `scale(0.97)` + `opacity: 0` con `@starting-style`, dentro de `@media (prefers-reduced-motion: no-preference)`.
- Todo `:hover` va dentro de `@media (hover: hover) and (pointer: fine)`.
- Sin movimiento reducido no hay escala ni desplazamiento: queda solo el color. La regla global de `base.css` queda de red de seguridad.

Qué se anima
| Qué | Cómo | Tiempo |
|---|---|---|
| Diálogos (Nueva obra, Subir visita, Hacer informe) | Entrada: opacidad + `scale(0.97→1)`, y el fondo se funde. Siguen centrados. | 200 ms |
| Confirmar plano (pantalla completa) | Solo fundido, sin escala. | 200 ms |
| Avisos de resultado (error al procesar, resultado de sincronizar, regeneración, confirmación del editor). Los de una línea (Mesa, Confirmar plano, Datos de la obra) tienen **sitio reservado** (`.sitio-aviso`, `.conf-msgs`) y no empujan lo de debajo; los paneles de varias líneas se insertan al final de su bloque | Entrada: opacidad + `scale(0.98)`, origen arriba a la izquierda. Los botones de arriba no se mueven. | 160 ms |
| Presionar controles compactos (`.btn`, navegación, pestañas) | `scale(0.97)` | 140 ms |
| Presionar filas anchas (`.fila-a`, `.of`, `.mesa-item`, `.conf-t`) | `scale(0.985)`: a 0.97 una fila de 900 px se correría unos 27 px. | 140 ms |
| Visor: acercar, alejar, Ajustar, Ir al recuadro, Ir a la ubicación, Ir al detalle | Suaviza `transform`, solo si el clic vino del puntero. | 180 ms |
| Paso vivo del procesador, estados de paneles y de filas | Cambio de color/fondo/borde. | 150 ms |
| Orden de destino al llegar desde «depende de» | Fondo y borde de selección, que se quitan solos. | ≈ 450 ms |

Qué no se anima, y por qué
- Cualquier cosa disparada por teclado: el atajo debe sentirse inmediato (visor con `+`, `-`, flechas, rueda y arrastre incluidos; el arrastre va 1:1).
- Cambios de pantalla y de pestaña.
- Filtros de la Mesa de Dudas y de la Bandeja: se filtra con frecuencia y animar estorba.
- La salida de los diálogos (decidido en B5a): cierra al instante.
  - Una salida de ~150 ms exigiría retrasar el desmontaje o el foco, y un clic rápido en el disparador durante ese tiempo dejaría el diálogo a medias.
  - Se abren y cierran muchas veces al día: lo inmediato se siente más rápido que la salida más fina.
  - La entrada (200 ms) ya explica de dónde viene; al salir no hay nada que explicar.
- Desplazamiento del tablero de Órdenes y su sombra de borde: son indicios, no animaciones.

## Accesibilidad
- «Saltar al contenido».
- Foco visible de 2 px en el color de acento. El `<h1>` recibe el foco al cambiar de pantalla, sin marco.
- Orden de Tab: Saltar → marca → Crear informe → navegación → contenido.
- Objetivos táctiles de 44 px en móvil.
- Orden de Tab, medido en B5b a 1280 y a 375: en móvil la barra inferior viene antes del contenido (así está en el DOM); `html` lleva `scroll-padding` arriba y abajo para que el foco nunca quede tras la cabecera pegada ni la barra fija.
- Diálogos: Tab y Mayús+Tab dan la vuelta dentro; un grupo de radios cuenta como una sola parada (el visor lo ignoraba y dejaba escapar el foco). Escape cierra y devuelve el foco a quien abrió. Las pestañas de la obra son enlaces de una navegación (`aria-current`), se recorren con Tab; las de Órdenes en móvil son `role="tab"` y se mueven con las flechas.
- Contraste medido (razón WCAG calculada sobre `tokens.css`, claro / oscuro y, además, sobre los colores calculados de 15.246 elementos de texto reales en las 15 pantallas, ambos temas): texto normal, mínimo 5.26:1 (`--alerta` sobre `--error-fondo`) en claro y 5.91:1 en oscuro; ningún texto real por debajo de 5.9:1 en claro ni de 6.8:1 en oscuro. Bordes de control y de estado, mínimo 3.3:1 (`--borde-fuerte`, `--est-cola-borde`, `--fased-borde`, `--dudas-borde`, `--est-rev-borde`). El anillo de foco mide 6.8:1 o más sobre fondos y superficies, y 13.98:1 sobre el riel (allí usa `--riel-tinta`).
- Excepciones: `--seleccion` es un relleno, no un borde ni un texto; el estado nunca se distingue solo por color, siempre lleva icono y palabra.
