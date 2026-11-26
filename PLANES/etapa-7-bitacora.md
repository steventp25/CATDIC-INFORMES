# Etapa 7 — Bitácora del Líder (T2, T3, T4)

Rama `claude/etapa7-campo-informe-02d16d`. Commits locales, sin push ni PR (los hace Steven al volver).

## Estado
| Tarea | Estado | Dónde |
|---|---|---|
| Contrato v2 | hecho | `PLANES/paquete-visita-v2.md` (`2bc4bae`, ajuste `a5e5386`) |
| T3 lector v2 | hecho | `e84c14a`. Suite: 1018 pasan, 3 omitidas, solo las 2 fallas conocidas de Dropbox |
| T2 Campo v11 | hecho (fuera de git) | `G:\My Drive\VISITA A OBRA CATDIC (v11 prueba)\` |
| T4 mapeo STP | hecho | `430bcf5`. `mapeo_stp.json` con `confirmado: false`. Columna: c←`b_m`, d←`h_m` y barras←`acero_longitudinal` con conversión exacta. Muro: b←`espesor`, c←`longitud`, h/i←`alma.ASV`, j/k←`alma.ASH`. Sin confirmar, el STP solo sale como BORRADOR en `CATDIC_SALIDA_PRUEBAS`. Suite comprobada por el Líder: 1028 pasan, 3 omitidas y solo las 2 fallas conocidas |

| T6 a T9 | hecho | Equivalencias de nivel, cabecera propuesta, recuadros propuestos y derivaciones f, g, h, m y n (`e810cc7`, `b1b0f82`, `2f973b5`, `cb859e5` y anteriores) |
| T11 / T11b / T11c | hecho, aprobadas por el Director (Evaluación 8) | `d6a953d` (b, e, i, j), `2987705` (k y una sola duda de generación por elemento), `7d5914a` (la duda de OBRA se actualiza). Suite: 1262 pasan, 3 omitidas y solo las 2 fallas conocidas de Dropbox |

| T12 (zona de planta para LOCALIZACIÓN) | hecha, aprobada por el Director (Evaluación 9) | `8165cd5` (plan y contrato), `6eee060` (código). Suite: 1286 pasan, 3 omitidas y solo las 2 fallas conocidas de Dropbox. Imágenes de la prueba en seco en la carpeta de notas del Director, `t12-localizacion\` |

| T13 + T14 (muros únicos, MC y equivalencia S-2 confirmada) | hecha, falta la auditoría del Director | `9b81694`. Un muro único en el nivel cruza con los ejes del plano; «MC» cruza con cualquier muro de contención del nivel; S-2 = FUNDACIONES @ E-1 en `BACKEND/equivalencias_confirmadas.json` |
| T15 (cabecera editable) | hecha, falta la auditoría del Director | `fed15a9` (GET/PUT `/api/proyectos/{id}/cabecera` y el modal «Cabecera» del tablero) y `1da55da` (`codia_residente` migrada al arrancar, con respaldo y auditoría) |
| T16 (área de 1" = 5.07) | hecha, falta la auditoría del Director | `2b17ccb`. C1 36∅1" en 0.60 × 1.50 da 0.0203 |

Suite tras T13–T16: 1323 pasan, 3 omitidas y solo las 2 fallas conocidas de Dropbox.

T13 a T16: aprobadas por el Director en la Evaluación 10.

| T17 (valores del proyecto con cita) | hecha, aprobada por el Director (Evaluación 13) | `4905c4c`. `valores_proyecto_confirmados.json` y `valores_proyecto.py`; el origen queda en `ficha.origen_filas` |
| T18 (C14, C16, regla 11, mapeo confirmado) | hecha, aprobada por el Director (Evaluación 13) | `07ad64c`, corregida en `4e18603` (Evaluación 11) y `37bb78c` (Evaluación 12: C14 exige el mismo acero en OBRA que en el plano). `mapeo_stp.json` con `confirmado: true` |

Evaluación 11 (Director): T17 y T18 quedaron BLOQUEADAS por C14. En obra, la fila «o» es una descripción del empalme y nunca coincide con el plano, así que 2.p salía vacía y sin duda. Corrección del Líder:
- C14 usa el mismo criterio que las discrepancias del generador: solo cuentan las filas dimensionales y que no falte ninguna fila de OBRA obligatoria.
- Cuando no aplica y no hay barras medidas en obra, se abre `obra.p` sin bloquear, con las filas que lo impiden.
- Consecuencia: una fila de texto distinta (incluida la h) ya no rompe la conformidad, porque el generador no compara filas de texto.

Desvíos de T17 y T18 (los hizo el Ejecutor; el Líder está de acuerdo):
- La derivación de la altura (e) sale de `mapeo_stp.json`: así la única fuente es el archivo de valores, y si este falla no se toma el 3.00 del plano en silencio.
- En C16, un dato vacío deja la duda sin bloquear y una forma que no cuadra la bloquea.
- Preguntas nuevas para Steven: al final de `PLANES/etapa-7-mapeo-stp.md` (altura 3.00 de C1 y C3 en E-3, qué es el perimetral, alas de MH2).

**Observaciones de T13–T16 (no bloquean):**
- MH2 y MH3 cruzan como muros únicos, pero sus ejes de diseño siguen «pendiente de verificar». Por eso abren `diseno:pNNN:ejes`.
- El MC real de la visita no trae ID escrito: su duda del importador sigue abierta hasta que el técnico escriba «MC».
- La prueba en seco confirmó C3 LY = 1.50 en el STP borrador (hoja 5).
- T15 usa un modal en el tablero porque no existe una vista de detalle del proyecto.
- Dato previo, sin tocar: una duda `elemento_visita:pNNN` resuelta en blanco la lee `_respuesta_vigente` como respuesta de Steven.
- Reglas C14 (cuantía de OBRA = la del plano cuando hay conformidad) y C16 (el muro en L suma sus alas): Steven las aprobó, pero aún no están programadas.
- El Ejecutor de T15 dejó un uvicorn de prueba en el puerto 8000 (PID 46264, BD temporal). No pude detenerlo (permiso denegado).

**Observaciones de T12 que no bloquean** (Director, Evaluación 9):
- El recuadro de LOCALIZACIÓN de C1 que propuso T8 queda corrido: la columna cae en su esquina de arriba a la izquierda. Steven lo ajusta en el visor.
- `proponer_zona` escribe en la BD sin hacer antes un respaldo. Hay que hacerlo antes de usarlo sobre la BD real.
- Falta probar el visor (la tarjeta «Zona de planta») contra el servidor real; solo se comprobó con respuestas simuladas.
- La zona de la hoja 24 solo se confirmó en la copia de prueba, como simulación. Steven confirma la zona de cada hoja de planta.

**En espera (24/11/2026):** no queda código pendiente para C1 y C3. Con una altura de prueba, la corrida 6 del Director ya da el primer STP borrador. Lo que falta depende de Steven:
- las preguntas 9a–9f de `PLANES/etapa-7-mapeo-stp.md`;
- la equivalencia S-2 (`PLANES/etapa-7-niveles.md`);
- la cabecera;
- las dudas de obra;
- las confirmaciones en el visor.

## T2: copia de Campo v11 (no está en git)
- La carpeta original `G:\My Drive\VISITA A OBRA CATDIC\` no se tocó (app.js sha256 `f9a67c28…`, sw.js `d2c6874e…`).
- sha256 de la copia v11: app.js `c34cbf9c6313221be37328105dffd1d8ebddbbf5a49a1bb16539806181e039a4`,
  index.html `20778d37aad34ce13bafa081dcce576b9581d486999e0e753a1e0b64848ac5fb`,
  styles.css `91f1f9f2b25d5322ea0eacca18d6fb003b1f54137adcf922419ad45cb3a05dbb`,
  sw.js `d16410ab14f3e49de88c94360bd6fe56c1252217a733b4a2abb8fab881632600` (caché `catdic-campo-v11`).
- Bloque plegable «Armado en obra» por tipo (col, muro, viga o pórtico, losa), con los rótulos de `ROTULOS`. Las medidas se toman sobre el acero, en metros. Vacío = «conforme (igual al plano)». Marca roja «PENDIENTE: queda en revisión».
- El paquete exportado sale como v2 y trae `obra: {fila_stp, textos, medidas_acero}`. Las visitas viejas cargan sin perder datos (probado con una visita v1 sembrada y con un elemento antiguo sin `ident`).
- Paquete de ejemplo (datos inventados): `C:\WINDOWS\TEMP\claude\cf008b8b80cb5786\a3a1fe19-9412-4d29-a4e7-b5eb4358eccb\scratchpad\paquete-v2-ejemplo.catdic-visita.json`. El Líder lo pasó por `leer_paquete` y `obra_de_elemento` del lector v2:
  - C1 entra con c=0.32 y d=0.42 (la coma se acepta) y 11 letras conformes por omisión;
  - el muro entra con todo conforme;
  - la viga Pendiente entra sin ninguna letra conforme y queda en revisión.
- En el IndexedDB de `localhost:8765` del navegador integrado quedó una obra de prueba («OBRA DE PRUEBA»). No afecta a la app real.

## Decisiones del Líder (para que Steven las revise)
1. Un elemento v2 sin `obra` va a duda; no se toma como conforme.
2. Un estado desconocido se trata como Pendiente; un estado vacío, como Observación.
3. Una duda `…:pendiente` resuelta por Steven deja procesar el elemento. Sus filas de OBRA no entran como conformes por omisión.

## Pendiente para Steven
Ver la lista al final de `PLANES/etapa-7-mapeo-stp.md`. Incluye:
- la columna C3, que en el informe da LY 1.20 y en el plano tiene una nota que la cambia de 1.20 a 1.50;
- las caras del muro (h=i, j=k);
- las derivaciones de columna;
- la conversión de las barras;
- la longitud de los muros en L (MH2).

Además quedan las 3 decisiones del Líder de arriba y reemplazar Campo en uso por la copia v11.

**En espera (25/11/2026, Evaluación 13):**
- T17 y T18 están aprobadas. Suite: 1405 pasan, 3 omitidas y solo las 2 fallas conocidas de Dropbox.
- En la corrida en seco t5n del Director, el STP sale sin «CON DUDAS», sin «BORRADOR» y sin dudas abiertas. C1 tiene 2.p = 0.0203 y C3 tiene 2.p = 0.0225.
- No hay tareas abiertas. Queda esperando a Steven:
  - las preguntas 29 a 31: el 2.95 en la torre, si todo MC es perimetral y si las filas de texto cuentan como discrepancia;
  - su confirmación en el visor.
- Nada de push: Steven lo hace al volver.
