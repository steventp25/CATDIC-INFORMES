# Etapa 5 · B1 v3: tres estilos sobre la organización aprobada

Para que Steven elija un estilo antes de B2. `DESIGN.md` se escribe después, con lo que se construya en B2. Abrir `index.html` con doble clic: funciona sin servidor y sin internet.

| Estilo | Archivo | Origen |
|---|---|---|
| A · Hormigón | `hormigon.html` + `estilo-hormigon.css` | La dirección asignada por el sorteo de `impeccable` (`seed:b9414461f55ae1b3`) |
| B · Plano sellado | `plano.html` + `estilo-plano.css` | La que `impeccable` clasifica primera («elección del skill»); riesgo: es la lectura literal |
| C · Tablero de obra | `tablero.html` + `estilo-tablero.css` | Retador del sorteo (pase de abordar + tablero de salidas), fundido con CATDIC; veredicto «competitivo» |

Las tres comparten la estructura (`base.css`), el comportamiento (`app.js`) y los datos sintéticos (`datos.js`). Solo cambian la paleta, la tipografía, la densidad y una firma. Así lo que Steven compara es el estilo, no la organización.

## Lo común a las tres (organización D6)

- **Navegación:** Inicio · Mis obras · Bandeja de trabajo · Informes · Configuración, con «Crear informe» siempre visible.
  - En escritorio va en un riel lateral, con el botón arriba.
  - En móvil va en una barra inferior de 5 entradas, con el botón en la cabecera.
  - En el riel queda el hueco «Lectura asistida · Fase C».
- **Dentro de la obra:** Resumen · Visitas y trabajos · Planos y ficha · Avance · Informes · Cierre.
  - El nombre de la obra y su cajetín quedan a la vista en todas las pestañas.
  - La URL lleva la obra (`#/obra/norte/...`).
  - Al ir de la obra a la Bandeja aparece «Volver a … · Resumen» (N4).
- **Las 5 pantallas de B1:**
  1. **Inicio:** prioridades por vencimiento, dudas, revisiones, entregas y próximas acciones.
  2. **Resumen de obra:** los 3 indicadores y los pendientes.
  3. **Bandeja:** obras y trabajos independientes, con filtros. Si los filtros no dejan resultados, la pantalla lo dice y ofrece «Quitar filtros».
  4. **Revisión de planos:** lista, plano y datos con su fuente. Incluye la vista «De la visita» con la foto y la etiqueta tal cual o su lectura.
  5. **Crear informe:** 4 pasos (servicios, datos y fuentes, revisar pedido, preparar). No crea obra.
- **Estados:** la barra oscura de la maqueta cambia entre «con datos», «vacío», «cargando» y «error».
  - El vacío explica y ofrece una acción.
  - El error dice qué falló y ofrece «Reintentar» (`role="alert"`).
  - Cargando usa huesos con `aria-busy`.
  - «Pendiente de verificar» es un estado propio en cada estilo.
- **Indicadores:** siempre «pendiente de verificar» (D15). Cada uno lleva su fórmula, qué falta decidir y la regla «Sin datos no es 0 %». Nunca se dibujan como 0 %.
- **Honestidad con la Fase D:** lo que pide backend nuevo lleva una etiqueta discontinua:
  - «Vencimientos: Fase D-a»
  - «Ruta común: Fase D-a»
  - «Cálculo: Fase D-b, tras D15»
  - «Guardar trabajos independientes: Fase D-c»

  Nada se simula como guardado. Al preparar un trabajo, la maqueta dice que no guardó nada.
- **Servicios de Crear informe:**
  - Supervisión STP figura como «generador existente, hoy solo dentro de una obra».
  - Los demás figuran como «Desarrollo futuro».
  - La pantalla aclara que no declara implementados los formatos HV.
- **Lo dudoso no se confirma:** si un elemento tiene valores en conflicto o sin fuente, «Confirmar valores con fuente» queda deshabilitado y explica por qué. La salida es «Enviar a la Mesa de Dudas».
  - C4 es el caso de planta contra detalle.
  - C6 es una etiqueta «L5» que no se interpreta.

  El recuadro del plano usa el rojo de los informes, `RGB(220,0,0)`.
- **Datos:** todos sintéticos y rotulados («(sintético)», «PLANO SINTÉTICO · NO ES REAL», «Foto sintética»). La cuantía de C1 se calcula: 8 #6 en 0.40 × 0.40 m da 0.0142.

## Skills aplicadas y qué decidió cada una

| Skill | Decisión que aportó |
|---|---|
| `ui-ux-pro-max` (`--design-system`, densidad 8, y dominio `ux`) | Estilo base suizo/minimal para herramienta profesional, con alta densidad. Paleta de partida «gris industrial + naranja de seguridad», que llevó al Hormigón. Navegación fija sin tapar contenido, enlaces profundos e historial con `hashchange`. Errores con `role="alert"`, vacíos con mensaje y acción, carga con `aria-busy`. Barra inferior de 5 entradas como máximo y objetivos de 44 px en móvil. **Descartado:** su pareja de fuentes Inter + Playfair, porque pide internet. |
| `impeccable` (contexto, `concept-seed --scope direction --mode operate`, `craft-floor`, `detect`) | Modo *Operate*: el mundo solo presta tipo, paleta, densidad y una firma; la navegación y los controles son los estándar. El sorteo asignó el candidato 6 de mi lista (Hormigón). B es «la elección del skill». C sale de los retadores. Del `craft-floor` salió: sin eyebrows, tarjetas de icono ni bordes laterales de color; selección, foco, scrollbar y cifras tabulares tematizados. `detect` hizo cambiar el suelo crema del Hormigón a gris concreto y quitar las rayas decorativas del Tablero. |
| `emil-design-eng` | Botones con `scale(0.97)` al presionar (140 ms, ease-out fuerte). Ninguna animación en acciones de teclado ni en navegación frecuente. Transiciones solo de color/fondo, de 150 ms. El reordenamiento de la Bandeja en C usa WAAPI con `transform` (240 ms) y se interrumpe sin saltos. Hover solo donde hay puntero fino. |
| `apple-design` | Respuesta inmediata al presionar. Consistencia espacial: la fila reordenada se desliza desde donde estaba, no aparece de golpe. Tracking por tamaño: títulos apenas negativos, rótulos en mayúsculas con +0.04–0.18 em. Jerarquía por peso y caja antes que por tamaño. `prefers-reduced-motion` quita el movimiento y deja los cambios de color. Orientación en cada pantalla: dónde estoy (riel y pestaña activos), adónde puedo ir y cómo salgo (migas «Mis obras», «Volver a …»). |
| `animate` / `choreograph` / `animation-performance` | No se cargaron todavía. El único movimiento de B1 es el reordenamiento de C, que solo anima `transform` y `opacity`. El movimiento de verdad es B4. |
| `break-ui` | Pendiente para B5, sobre la interfaz real. En B1 ya se probaron filtros sin resultado, el elemento sin ejes (C6) y valores sin fuente. |

## Patrones tomados de las referencias

| Referencia | Patrón adaptado | Dónde |
|---|---|---|
| Procore · Project Overview | Cifra por categoría que abre la lista ya filtrada; acciones rápidas; actividad reciente | Conteos de Inicio y de Resumen de obra; «Acciones rápidas» y «Actividad reciente» del Resumen |
| Autodesk · Project Home | «Asignado a mí» agrupado por vencimiento (vencido, próximos 7 días, más adelante, sin fecha); cada fila lleva directo al pendiente | Bloque «Prioridades» de Inicio (los vencimientos reales son Fase D-a) |
| PlanRadar · plan view | Lista de pendientes junto al plano; elegir una fila resalta su sitio en el plano y abre el detalle | Revisión de planos: lista ↔ recuadro rojo ↔ datos con fuente |
| PlanRadar · plans | Plano por nivel con su versión y estado (vigente / no vigente) | Selector «E-3 · Rev. 3 (vigente)» y «Planos» del cajetín |
| Fieldwire · Tasks | Expediente del trabajo: fuentes, fotos, respuestas, estado y documentos vinculados | Paso «Revisar pedido» de Crear informe. **La página dio 403 al leerla**: el patrón sale de la descripción de Steven en el PR 31, no de la página. |

## Los tres estilos

### A · Hormigón (asignado por el sorteo)
- **Mundo:** la obra en curso. Suelo gris concreto con poro muy leve, riel de encofrado fenólico `#4a2a20` y crayón de marcar naranja (`#f76b15` para «Crear informe», `#c2410c` para la acción principal).
- **Tipos:** Bahnschrift (DIN, letra de señalización de obra) en títulos, rótulos y cifras; Segoe UI Variable en el texto.
- **Firma:** lo que no tiene dato va **rayado**, como una sección sin definir en un plano. Los indicadores muestran el rayado y la etiqueta «pendiente de verificar»; nunca una barra vacía.
- **Mejoras tomadas de los retadores descartados:**
  - Del horario de bolsillo: el rango se marca por peso y caja, no por tamaño.
  - Del léxico: la Bandeja dice qué tramo se ve («de «Duda bloqueante» a «Visita en cola»»).
  - De datamatics: en el plano, el elemento elegido queda nítido y los demás bajan.
  - Del espécimen bitmap: la etiqueta se ve «tal cual» o «leída».
- **Riesgo honesto:**
  - El rayado es justo el patrón que `detect` marca como decoración. Aquí tiene una sola función («sin dato»), pero si se usa para algo más pierde sentido.
  - El marrón del riel es cálido y fuerte en jornadas largas.

### B · Plano sellado (elección del skill)
- **Mundo:** la hoja de planos. Papel con retícula, tinta azul-negra `#14202e`, azul de sello `#1f4fa8` para acciones y el rojo reservado al recuadro.
- **Tipos:** Segoe UI Variable; Consolas para datos y celdas del cajetín.
- **Firma:**
  - La obra se lee en un **cajetín** dibujado con líneas de tinta.
  - Los ejes van en **globos**.
  - Lo que falta se dibuja como un **hueco en planta**: recuadro discontinuo, y en los indicadores un recuadro con una X.
- **Riesgo honesto:**
  - Es la lectura literal del oficio y la más parecida a la maqueta «Plano» del 16/11.
  - La retícula de fondo es la que `detect` señala como recurso genérico (avisa, no bloquea).
  - Consolas en el cajetín es denso.

### C · Tablero de obra (retador competitivo)
- **Mundo:** tablero de salidas y pase de abordar. Paneles neutros de alto contraste, cifras tabulares grandes (Bahnschrift) y **un solo color de aviso, ámbar**, reservado para lo que cambió.
- **Firma:**
  - Lo nuevo queda **encendido** en ámbar, con la marca «NUEVO» (no solo color), hasta que lo abres.
  - Al filtrar la Bandeja, las filas se **reordenan en su sitio**.
  - El cajetín es un pase segmentado con cortes punteados.
  - Los indicadores no dibujan barra: un riel vacío se leería como 0 %.
- **Por qué es competitivo y no ganador:** gana en claridad para triar pendientes, pero Steven no vive en aeropuertos; su mundo es la obra y el plano.
- **Riesgo honesto:**
  - Es el más genérico de los tres si se quita el ámbar.
  - El negro casi puro del riel en tema oscuro es muy duro.

## Retadores del sorteo y su veredicto

| Retador | Veredicto | Qué se tomó |
|---|---|---|
| Pase de abordar + tablero de salidas | Competitivo (claridad) | Es el estilo C |
| Mapa de metro esmaltado | Competitivo (claridad: niveles como estaciones) | Nada en B1. Idea para «Avance» en B3 si D15 lo permite. |
| Horario de bolsillo en vidrio | Descartado | Rango por peso y caja |
| Léxico con palabras guía | Descartado | El tramo visible en la Bandeja |
| Espécimen bitmap Emigre | Descartado | Ver la etiqueta «tal cual» o «leída» |
| Datamatics (Ikeda) | Descartado | El elemento elegido en foco y el resto atenuado |

## Validación hecha (Playwright, 19/11/2026)
- Tamaños: 1280×800, 1920×1080 y 375×812, en tema claro y oscuro.
- Cobertura: 3 estilos × 5 pantallas = 75 capturas, más estados, pasos de Crear informe y C4 en conflicto.
- Resultado:
  - Sin desplazamiento horizontal en ningún caso.
  - 0 peticiones fuera de `file:`.
  - 0 errores de consola.
- Teclado: el orden de tabulación es «Saltar al contenido», la barra de la maqueta, la marca, «Crear informe» y las 5 entradas. Los elementos del plano SVG se eligen con Enter o Espacio.
- Contraste: el texto secundario de los tres estilos supera 4.5:1 sobre su superficie (calculado al elegir los tokens). El foco es un contorno de 2 px del color de acento.
- `impeccable detect`:
  - Quedan 2 avisos de nivel *advisory*: la retícula de B y el rayado de A. Los dos son firma funcional, declarada arriba.
  - Se corrigieron el suelo crema de A y las rayas sin función de C.

## Sustituciones declaradas
- La página de decisión de `impeccable` se sustituye por esta nota y la puerta de Steven, a través del Director (en esta fase no se le habla directamente).
- El aviso de telemetría del sorteo (`--from b429ec8dc7555d53ac6ca00d75b3dc17 --kind …`) se manda cuando Steven elija: `assigned` (A), `pick` (B) o `challenger --chosen vernacular-ephemera-boarding-pass-and-gate-board` (C).
- Las fuentes son las de Windows (Bahnschrift, Segoe UI Variable, Consolas). `impeccable` prefiere una fuente propia autoalojada, pero no hay archivos de fuente en el proyecto, y la regla «sin internet» prohíbe descargarlas en tiempo de uso. Si Steven quiere otra, hay que añadir el archivo a `FRONTEND/vendor/` en B2.
