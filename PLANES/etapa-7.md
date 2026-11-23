# Etapa 7 — De CATDIC Campo al informe de visita automático (prueba con la visita 24 de Terra Living)
Estado: APROBADO (Steven, 23/11/2026: «Sí, planifícalo» y «continúa trabajando según lo establecido; prepara todo para la prueba»). Sin push ni fusión hasta que Steven vuelva.

## Objetivo
Dejar lista la **prueba de punta a punta** con la visita real `24. VERTICALES S-2 COMPLETIVO 06-11-2026` de Terra Living:
paquete de Campo → elementos de la visita → datos del plano (leídos por la IA) → Procesar Cola → STP-MIVED en la
carpeta de pruebas. Al volver Steven, solo faltan sus confirmaciones (datos del plano, recuadros, mapeo de filas).

## Decisiones de Steven que aplican
- 23/11: si una medición de obra va **vacía**, el elemento es **conforme** (OBRA = valor del plano, §4.5). Si el elemento
  está **Pendiente** en la visita, pasa a **En revisión** (no entra como conforme; abre duda).
- 23/11: la IA lee y extrae **todos** los elementos estructurales del plano a las tablas; el código usa esas tablas.
- La IA propone, el código ancla y valida, y Steven confirma (Regla de Oro). Nada se inventa: lo no leído queda
  `pendiente de verificar`.

## Discrepancias CLAUDE.md vs repositorio
- `elementos_diseno` de Terra Living está **vacía** en la BD real (comprobado 23/11 sobre una copia).
- `MAPEO_DISENO_A_STP` en `BACKEND/procesador_cola.py:87` está **vacío**: el programa no sabe qué dato del plano va
  en cada fila del STP-MIVED. Hoy toda ficha se detiene con la duda «decisión pendiente de Steven».
- `medidas_acero_campo_json` no la llena ningún módulo; Campo solo manda `mediciones` como texto libre.
- La BD real no tiene la visita 24 (el sincronizador la crea al correr).
- CATDIC Campo (`G:\My Drive\VISITA A OBRA CATDIC`) no está en git.

## Tareas

### T1 — La IA lee del plano los elementos de la visita 24 (Fase A, tramo acotado)
- Ejecutor: Líder de la Fase A (sesión `fase-a`) con sus Ejecutores; rama `claude/etapa5-fase-a-3da668`.
- Archivos: los de la Fase A (`BACKEND/plano/asistido/…`, skill `extraer-plano`, `PLANES/etapa-5-fase-A.md`); datos solo en scratch y en una **copia** de la BD.
- Depende de: —
- Qué hacer: retomar la Fase A (sale de la pausa por F0) **solo para lo que pide la prueba**: C1, C3, MH2, MH3 y el muro de
  contención del eje 4' (A–D) en el nivel S-2. Hojas: cuadro de columnas, detalles de muros y el detalle del muro de
  contención, y la planta de S-2 para la localización. Hacer A4c (muros) lo justo para estos elementos. Generar
  `propuesta.json` con citas e importarla con el importador con anclaje (A3d) a la copia de la BD, sin confirmar.
- Criterios de aceptación:
  - [ ] Cada valor importado cita un texto del vectorial; lo que no, queda `pendiente de verificar` con su duda `IA:`.
  - [ ] EJES de columnas y muros: del detalle no salen; quedan `pendiente de verificar` y se cruzan por ID + nivel (decisión A1 §6.2).
  - [ ] Informe corto en `PLANES/etapa-5-reportes/` con lo leído, las dudas y el cupo gastado.
  - [ ] Nada escrito en Dropbox ni en la BD real.
- Cupo: la cuenta es Pro y lleva 48 % de la semana (reinicia 28/11). Este tramo cuesta ≈ 10–15 % de una ventana de 5 h. No leer el resto de Terra Living en esta etapa.
- Reglas: Regla de Oro, §4.2, §4.4, errores 11 y 12.

### T2 — Campo v11: mediciones guiadas por tipo
- Ejecutor: ejecutor-frontend (Campo es HTML/JS sin build).
- Archivos: una **copia** de trabajo de Campo `G:\My Drive\VISITA A OBRA CATDIC (v11 prueba)\` (`app.js`, `index.html`, `styles.css`, `sw.js`). La carpeta en uso **no se toca**: Steven la reemplaza al volver.
- Depende de: —
- Qué hacer: en cada elemento, además del cuadro de texto libre, casillas de OBRA con las mismas filas que la columna
  `2. IMFORMACION ARMADO EN OBRA` del STP-MIVED (`BACKEND/generators/stp_mived.py:45-66`), según el tipo (col, muro,
  viga/pórtico, losa). Vacío = conforme (decisión de Steven); se muestra como «conforme (igual al plano)». Las medidas
  dimensionales (`DIMENSIONALES`) se piden **sobre el acero** y la ayuda lo dice. Estado `Pendiente` visible y exportado.
  Exportar el paquete con `version: 2` y un campo `obra` por elemento: `{letra: texto}` y `medidas_acero: {letra: metros}`.
- Criterios de aceptación:
  - [ ] Un paquete v2 exportado desde la copia (en el navegador del PC) valida contra `PLANES/paquete-visita-v2.md`.
  - [ ] Las visitas viejas y el paquete v1 siguen funcionando (cargar una visita guardada no pierde datos).
  - [ ] `sw.js` sube la versión de caché a `campo-v11`.
- Reglas: §4.4, §4.5, error 9 (sin «CORRIDO»), §5.2 (fotos ≤ 1000 px).

### T3 — Informes: lector del paquete v2 y regla «vacío = conforme»
- Ejecutor: ejecutor-backend.
- Archivos: `BACKEND/sync/paquete_visita.py`, `BACKEND/tests/test_paquete_visita.py`, `PLANES/paquete-visita-v2.md` (nuevo).
- Depende de: — (el contrato v2 lo escriben T2 y T3 juntos: lo redacta T3 primero y T2 lo sigue).
- Qué hacer: aceptar `version` 1 y 2. En v2, llenar `medidas_acero_campo_json` con el contrato que ya lee
  `procesador_cola.py:720` (`{letra: metros, "obra": {letra: texto}}`). Vacío = conforme: no se escribe nada en `obra`
  y se marca `conforme_por_omision: true` para esa letra, para que el generador ponga el valor del plano. Estado
  `Pendiente` → el elemento queda `En revisión` con una duda. Validar números (metros con punto o coma; nada de unidades
  raras: eso va a duda, nunca se adivina).
- Criterios de aceptación:
  - [ ] Pruebas nuevas: v2 completo, v2 con vacíos, v2 con estado Pendiente, v2 con medida ilegible, v1 sin cambios.
  - [ ] Suite completa: 977+ pasan; solo fallan las 2 conocidas de Dropbox.
- Reglas: Regla de Oro, §4.5, error 12.

### T4 — Mapeo de filas del STP-MIVED (propuesta para Steven)
- Ejecutor: ejecutor-generadores.
- Archivos: `BACKEND/procesador_cola.py` (solo `MAPEO_DISENO_A_STP` y su carga), `BACKEND/generators/mapeo_stp.json` (nuevo), `BACKEND/tests/test_procesar_cola.py`, `PLANES/etapa-7-mapeo-stp.md` (nuevo).
- Depende de: T1 (nombres de los campos de `datos_diseno_json` que produce la Fase A).
- Qué hacer: proponer, para col y muro (los tipos de la visita 24), de qué campo del plano sale cada fila. La evidencia
  son los STP-MIVED ya entregados de Terra Living en `INFORMES\2.DATA PROCESADA\` (solo lectura): en el informe sale
  la fila y el valor, y en el plano el texto de donde sale. El mapeo va en el JSON con `"confirmado": false`. Mientras no
  esté confirmado, el STP solo se genera en la carpeta de pruebas (`CATDIC_SALIDA_PRUEBAS`) y la portada lleva una marca
  `BORRADOR — mapeo sin confirmar`.
- Criterios de aceptación:
  - [ ] `PLANES/etapa-7-mapeo-stp.md` tiene una tabla fila → campo → ejemplo real (informe, página).
  - [ ] Una fila sin evidencia queda sin mapear (la ficha sigue pidiendo el dato con su duda).
  - [ ] Pruebas de que con `confirmado: false` nunca se escribe en `INFORMES\2.DATA PROCESADA\`.
- Reglas: Regla de Oro, error 12, error 13, §5.2.

### T5 — Prueba preparada de punta a punta
- Ejecutor: Director (yo), con el skill auditar-catdic.
- Archivos: `PLANES/etapa-7-prueba.md` (guion y resultado); todo lo demás en scratch.
- Depende de: T1, T3, T4 (T2 solo para el paquete exportado de verdad; mientras, paquete v2 simulado como el del 23/11).
- Qué hacer: sobre una copia de la BD, correr sincronizador → paquete → diseño de T1 → recuadros propuestos (visor) →
  Procesar Cola. Anotar dónde se detiene y por qué. Dejar a Steven la lista corta de lo que le toca confirmar.
- Criterios de aceptación:
  - [ ] `etapa-7-prueba.md` dice paso a paso qué salió y qué falta, con capturas o rutas de salida en la carpeta de pruebas.
  - [ ] La BD real y Dropbox sin cambios (sha256 antes y después).

## Paralelismo
- T1, T2 y T3 a la vez (no comparten archivos). T4 espera a T1. T5 al final.
- La Fase B (B5b) sigue en su sesión; no comparte archivos con esta etapa.

## Pendientes de verificar / preguntas para Steven (al volver)
1. Confirmar el mapeo de filas de T4.
2. Confirmar los datos del plano que importe T1 (pantalla «Confirmar plano») y los recuadros de LOCALIZACIÓN y DETALLE (visor).
3. Reemplazar Campo en uso por la copia v11 cuando esté aprobada.
4. Las 3 dudas reales de la visita 24: ejes de MH2 y MH3, e ID del muro de contención del eje 4'.

## Fuera de alcance
- Leer el resto de Terra Living con IA (se hace después, por lotes, cuidando el cupo semanal).
- CATDIC-STP, MIVED FI y los formatos HV.
- Push, PR y fusiones (las hace Steven).
