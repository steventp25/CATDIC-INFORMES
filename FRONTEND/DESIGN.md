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
- Solo hay respuesta al presionar y cambios de color de 150 ms.
- Nada se anima en acciones de teclado.
- `prefers-reduced-motion` lo quita todo.
- El movimiento con propósito llega en B4.

## Accesibilidad
- «Saltar al contenido».
- Foco visible de 2 px en el color de acento. El `<h1>` recibe el foco al cambiar de pantalla, sin marco.
- Orden de Tab: Saltar → marca → Crear informe → navegación → contenido.
- Objetivos táctiles de 44 px en móvil.
- Contraste: elegido para 4.5:1 o más, pero todavía sin medir con herramienta. Se mide en B5.
