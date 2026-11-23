# B3b — Obra: Resumen, Planos y ficha, Avance y Cierre (encargo del Líder al Ejecutor)

Fecha: 23/11/2026. Va 6.ª en el orden de B3: B3a ✔ → B3d ✔ → B3g ✔ → B3e → B3g-2 → **B3b** → B3c → B3f. La lanzó el Director el 23/11. Estilo **Plano sellado** (`FRONTEND/DESIGN.md`).

## Dónde se trabaja (igual que en B3e y B3g-2)
- **Worktree y rama:** `C:\Users\Steve\OneDrive\Desktop\CATDIC-WEB\.claude\worktrees\etapa2-t7n-confirmacion-8210cf`, rama `claude/etapa5-fase-b-0020e1`.
  - No crees ni cambies de rama. Nada de push, merge, stash, checkout ni reset. No toques el checkout principal.
  - Trabajas por turnos con el Líder.
- **Zona:** `FRONTEND/**` (menos `maquetas/`, `clasico/` y `vendor/`) y `PLANES/etapa-5-reportes/B3b.md`.
  - **B3b no tiene excepción de backend: no se toca nada de `BACKEND/`.** Todo lo de abajo se hace con las rutas que ya existen.
  - Si algo necesita backend nuevo, se rotula «Fase D» o «pendiente de verificar», se anota en el informe y no se simula.
- **Tablero clásico.** Steven, 20/11: «Conserva el tablero clásico. Su eliminación no queda autorizada».
  - No borres ni edites `FRONTEND/clasico/` ni `BACKEND/tests/test_frontend_servido.py`.
  - Ninguna mención ni enlace al clásico en el tablero nuevo.
- **Python:** `C:\Users\Steve\AppData\Local\Python\pythoncore-3.14-64\python.exe`.

## Reglas (siguen todas las de B2–B3g-2)
- **Sin red ni compilación:** scripts clásicos sobre `window.CATDIC`, Vue local, sin librerías nuevas.
- **Reutiliza, no copies:**
  - `js/componentes.js` (`Bloque`, `Pendiente`, `FaseD`, `Icono`, `Cajetin`), `C.api`, `C.formato` y `js/datos.js`;
  - `FormularioPlanos` de B3a, en `js/formulario-planos.js`, con `modo="cambiar"`;
  - `VisorPlano` y `VisorRevision`, con `C.visor.olvidar`, de B3e en `js/visor-revision.js`;
  - `FormularioVisita`, `ColaVisitas`, `AvanceTrabajo`, `FormularioInforme` y `MesaDudas`.
  - Si un componente necesita crecer, extiéndelo con props sin romper a sus usuarios y dilo en el informe.
- **Regla de Oro:**
  - Lo que falte es «pendiente de verificar». Nunca se inventan cifras ni datos de ingeniería.
  - **Los 3 indicadores (N8, N9 y N10) nunca se muestran como 0 % ni como barra vacía.** Se ven con su fórmula, el motivo (falta la decisión D15) y el rótulo «Fase D-b».
  - **N11:** ningún indicador se calcula con el número de archivos, versiones o visitas.
  - Atar por `id_elemento` está prohibido: el mismo ID se repite en varios niveles. Un elemento de diseño se identifica por su `uid`.
- **Diseño:**
  - sin franjas laterales de color: el estado se muestra con un borde completo, un icono y texto;
  - nada que dependa solo del color;
  - container queries en las filas;
  - objetivos táctiles de 44 px o más en móvil;
  - diálogos con el patrón de B3a: `<dialog>`, `showModal`, Escape, foco atrapado y foco de vuelta.
- **Formato:** fechas `DD/MM/AAAA`; textos en español.
- **Commits:** atómicos, en español, terminados en `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Nunca capturas, PDFs ni `*.db`.

## Qué hay que construir

### 1. Pestaña «Planos y ficha» (`#/obra/<id>/planos`)
Lee B0 (`PLANES/etapa-5-inventario-ui.md`): §1 Z14a, §2 M2, M4 y M5, §3 A11–A13, A15 y A34–A44, §4 y §9 «Modal Nueva obra / Cambiar plano», «Visor» y «Datos de la obra». **Todo lo de esas secciones tiene que estar**, con sus textos.

1. **Plano vigente** (Z14a), de `planos_vigentes[id]` en `/api/dashboard`:
   - muestra «Rev. N · etiqueta», la fecha del plano (o «sin fecha de plano»), «certificado por X» y los sha256 cortos del vectorial y del sellado;
   - sin plano vigente: «Sin plano vigente» y el botón «Subir planos».
2. **Historial de planos:** `GET /api/proyectos/{id}/planos`.
   - Cada fila lleva la revisión, la etiqueta, la fecha, el estado (vigente o histórico) y quién lo certificó.
   - Estados: cargando, vacío y error con «Reintentar».
3. **«Cambiar plano» o «Subir planos»** (A11, A28): usa `FormularioPlanos` con `modo="cambiar"` y `:proyecto`.
   - El texto de la obra es el de M2: el plano nuevo queda vigente y los elementos se marcan «plano cambiado: revisar».
   - Al terminar sale el aviso final de A28: revisión, elementos marcados, `aviso_paginas` y los datos pendientes con su acceso a «Datos de la obra». Se recargan la obra y el historial.
4. **Visor del plano con recuadros (M4, A34–A44).** Es el editor completo, no solo la vista de B3e.
   - **Ruta propia:** `#/obra/<id>/planos?visor=1[&elemento=<uid>]`. «Cerrar» vuelve a la pestaña; el botón Atrás funciona; recargar deja el mismo elemento elegido.
   - **Reutiliza `VisorPlano` de B3e** para la hoja, el zoom (0.1–8; `−`, `+`, «Ajustar»), el desplazamiento y el selector de hoja (`/visor/indice`, `/hojas/{n}/info`, `/hojas/{n}.png`). Amplíalo con props para lo que falta.
   - **Selector de elemento** (`GET /api/proyectos/{id}/elementos`):
     - cada opción muestra `id_elemento · ejes · nivel_rango` y su valor es el `uid`;
     - se muestran los avisos «Esta obra aún no tiene elementos de diseño: los recuadros se guardan por elemento.» y `revisar_motivo`;
     - al elegir un elemento se salta a la página de su recuadro guardado.
   - **Cajas sobre la hoja:** confirmado, propuesto (pendiente) y sin guardar. Cada una lleva una etiqueta de texto («LOC confirmado», «DET propuesto · pendiente de verificar», «LOC sin guardar») y un trazo distinto (continuo, discontinuo o punteado), no solo un color.
     - El recuadro de localización del informe sigue siendo RGB(220,0,0), como en B3e.
   - **«Proponer recuadros»** (`POST …/elementos/{uid}/propuesta`) y **«Usar propuesta»**.
   - **Dibujar** arrastrando, con ratón y con el dedo (Pointer Events con `setPointerCapture`):
     - un arrastre de menos de 5 pt se descarta;
     - las coordenadas van en puntos PDF, redondeadas a 2 decimales;
     - el dibujo se aplica al tipo marcado (LOCALIZACION o DETALLE).
   - **Teclado:** el dibujo no tiene equivalente de teclado razonable. Por eso «Proponer» y «Usar propuesta» deben poder hacerse con teclado. Anótalo.
   - **«Confirmar y guardar»** (`PUT …/elementos/{uid}/recuadro` con `{tipo, pagina, rect, origen}`):
     - muestra el mensaje «LOCALIZACION guardado (confirmado por <quien>).» y pide la vista previa;
     - después **llama a `C.visor.olvidar(obraId)`**, para que la Mesa y el visor de revisión no muestren un recuadro viejo.
   - **«Vista previa»** (`POST …/visor/vista-previa`), con la imagen y la URL del objeto revocada al cambiar.
   - Los textos de estado y detalle de cada recuadro son los de A44 (`estadoRecuadro`).
   - Hay mensajes de error y de éxito, y «Cargando la hoja…».
   - Ningún PUT o POST se reintenta solo, y se bloquea el doble envío.
5. **«Datos de la obra» (M5, A13, A29).** Puede ser un diálogo o una sección de la pestaña.
   - Hay 4 grupos: `equivalencia_nivel`, `losa_tipo`, `hoja_par` y `techo`. Cada uno lleva su título, su ayuda, su ejemplo como *placeholder*, un textarea y «Guardar».
   - Los 3 primeros llevan la casilla «Ya escribí todos los de esta lista». `techo` lleva el texto de B0.
   - Los datos guardados se cargan antes con `GET …/datos-obra`. **Si ese GET falla, se dice**: no se abre vacío en silencio, como hacía el clásico.
   - `PUT …/datos-obra`: cada línea se parte en el primer `=` o `:`. El mensaje es verde o rojo por grupo, con el texto de A29.
6. **Dudas de la obra** (A15): el enlace «Dudas de la obra: N» abre la Mesa en modo obra (`#/obra/<id>/resumen?dudas=obra`).
7. **«Confirmar datos del plano»** (M6): es de **B3c**. Aquí va solo el sitio reservado, con un rótulo de la tarea, sin simularlo.

### 2. Pestaña «Resumen» (`#/obra/<id>/resumen`)
- **Los 3 indicadores** (N8 Avance por entrepisos, N9 Expediente completo, N10 Documentación al día):
  - cada uno con su fórmula tal cual la dice B0 §10.3, «pendiente de verificar», el motivo («falta la decisión D15») y el rótulo «Fase D-b»;
  - nunca 0 % ni una barra.
- **Pendientes de la obra** (N12), con datos reales y acceso directo al registro:
  - dudas abiertas de visita y de obra, con enlaces a la Mesa;
  - visitas en cola o con dudas, que llevan a «Visitas y trabajos»;
  - sin plano vigente, que lleva a «Subir planos»;
  - elementos con «plano cambiado: revisar», si `/elementos` lo trae, que llevan al visor con ese `uid`;
  - y los últimos informes generados (`GET /api/proyectos/{id}/informes`, los 3 más nuevos), con «Abrir PDF».
  - Cada bloque tiene sus estados de cargando, vacío y error.
- **Actividad reciente:** «Fase D-a».
- **Acciones rápidas:** «Subir visita», «Procesar cola de esta obra» si ya existe en B3d, «Hacer informe» y «Abrir el plano». Reutilizan los flujos que ya existen.
- La Mesa en modo obra (`?dudas=obra`) sigue funcionando como en B3e.

### 3. Pestaña «Avance» (`#/obra/<id>/avance`)
- El indicador N8 con su fórmula, «pendiente de verificar», D15 y «Fase D-b».
- Lo que sí se sabe hoy, presentado como **hechos y no como porcentaje**: por ejemplo, la lista de visitas de la obra con su fecha, sus elementos, su nivel y su estado.
- Nada que parezca una medida de avance (N11).

### 4. Pestaña «Cierre» (`#/obra/<id>/cierre`)
- Los indicadores N9 y N10 con su fórmula, «pendiente de verificar», D15 y «Fase D-b».
- **Lo que hoy impide cerrar, como hechos con enlaces:**
  - dudas abiertas;
  - visitas sin procesar o con dudas;
  - si hay o no plano vigente;
  - los informes generados.
- Nada de «listo para cerrar» calculado.

## Cómo se prueba (las reglas de B3e)
- **Servidor:** backend desde este worktree con una **copia** de la BD en el scratch; las 5 variables `CATDIC_*` apuntan al scratch; puerto **8766**. No cierres el 8765 ni el 8767, nunca uses el 8000 y apágalo al terminar.
- **Dropbox:** nada contra `C:\Users\Steve\CATDIC Dropbox\`.
- **Obra sintética:** la copia de la BD no tiene ninguna obra con plano vigente. Reutiliza la obra sintética de B3e, que tiene plano y elementos (`scratchpad\b3e\sembrar.py`, `ids.json`, `copia-sembrada.db`), copiándola a tu carpeta del scratch.
  - Ahí se prueban: dibujar, guardar, proponer, la vista previa, Datos de la obra y Cambiar plano, con PDF sintéticos en el scratch.
  - Lo que escriba el servidor va a la copia y al scratch.
- **Playwright** (Chromium) a 375, 768, 1024, 1280 y 1920 px, en claro y oscuro, sobre Resumen, Planos y ficha, el visor, Datos de la obra, Avance y Cierre. Comprueba:
  - 0 peticiones fuera de `127.0.0.1:8766`;
  - 0 errores de consola (salvo los «Failed to load resource» de 4xx esperados, anotados);
  - sin desplazamiento horizontal;
  - el foco en los diálogos y en el visor;
  - el Atrás del navegador;
  - los estados: cargando, vacío, error, sin plano vigente, sin elementos, 409 o 422 del servidor con su `detail`, y el GET de datos-obra que falla.
- **Visor:**
  - dibujar con ratón y con eventos táctiles;
  - descartar un arrastre de menos de 5 pt;
  - guardar y ver que el visor de revisión de la Mesa muestra el recuadro nuevo (después de `olvidar`);
  - zoom y desplazamiento con teclado.
- **Peor caso:** 300 elementos en el selector, IDs y ejes de 120 caracteres, 30 revisiones de plano, campos nulos y un GET lento.
- **Suite del backend** desde `BACKEND/`, dos veces: todo en el scratch, y sin `CATDIC_DROPBOX_RAIZ`. Solo pueden fallar las 2 de Dropbox.
- **Búsqueda final** de «clasico» y «clásico» en `FRONTEND/` (sin `clasico/`, `maquetas/` ni `vendor/`): 0 resultados.

## Informe
`PLANES/etapa-5-reportes/B3b.md` con:
- archivos tocados;
- componentes reutilizados y cómo se ampliaron;
- la paridad marcada contra B0 §9 (Cambiar plano, Visor y Datos de la obra);
- qué queda como Fase D o «pendiente de verificar»;
- la tabla de Playwright;
- los estados;
- el peor caso;
- la suite;
- las limitaciones;
- los hashes;
- la carpeta del scratch con las capturas.
