# Etapa 5 · Fase A — Claude razona los planos (estado de la fase)

Líder: sesión Opus (`claude/etapa5-fase-a-3da668`). Director: la sesión que la lanzó. Plan y decisiones: `PLANES/etapa-5.md` (manda sobre este archivo).
Reglas de la fase: sin llave de API ni servicios de pago; **máximo 1 Ejecutor trabajando a la vez**; commits locales en ramas `claude/etapa5-*`, ningún push ni fusión; BD real y Dropbox en solo lectura; nunca se commitean PDFs, imágenes, `*.db` ni hojas preparadas.

## Tareas

| Tarea | Qué | Quién | Rama | Estado |
|---|---|---|---|---|
| A1 | Reconocimiento con el vectorial de Terra Living (6 hojas, 3 resoluciones) → `etapa-5-reconocimiento-asistido.md` | Líder | `claude/etapa5-fase-a-3da668` | **hecha** (16/11) |
| A2 | Preparar hojas: `plano/asistido/preparar.py` (+ `__init__.py`, pruebas) | Ejecutor Sonnet (a2-preparar) | `claude/etapa5-a2-preparar-3d8018` | **hecha** (`41396f8`, 8 pruebas pasan); ajustes pendientes tras la puerta: ppp 72, `textos.txt`, recortes `zonas/`, manifiesto que acumule lotes |
| — | **Puerta de Steven:** ve el informe de A1 antes de A3 y A4 | Director | — | **resuelta 19/11** (plan v3, D10–D13) |
| A2-aj | Ajustes de A2: 72 ppp, `textos.txt`, recortes en `zonas/`, manifiesto acumulativo, CLI | Ejecutor Sonnet (a2-preparar) | unida a la rama de fase | **hecha** (`5d2c64e`, 17 pruebas; unida en `df7cb9a`, suite 960 + 2 fallas conocidas) |
| A3a | `extractor.py`: parámetro `origen` opcional (commit aparte) + `asistido/esquema.py` (esquema y anclaje) | Ejecutor Sonnet | rama de fase (worktree del Líder, por turnos) | en curso |
| A3b | `asistido/importar.py`: escribir con anclaje, doble lectura con T6n, idempotencia | Ejecutor Sonnet (el mismo) | rama de fase | pendiente (tras A3a) |
| A4 | Skill `extraer-plano` (D10: A4a columnas · A4b losas · A4c muros · A4d pórticos · fundaciones según D12) | Líder | — | pendiente (A4a tras A3) |
| A5 | Rutas `plano/asistido/rutas.py` + 1 línea `include_router` en `main.py` | Ejecutor Sonnet | rama de fase | pendiente |
| A6 | Prueba real (Terra Living completo + P16 Losa E-9) y cierre | Líder + sesión lectora | — | pendiente |
| A7 | (Opcional) lanzar Claude desde el tablero sin costo | Líder (investigación) | — | al final, si da tiempo |

Contrato de archivos (`textos.json`, `propuesta.json`): se fija en `PLANES/etapa-5-contrato-asistido.md` después de A1. A2 arranca con el formato provisional de `textos.json` de su brief.

## Bitácora (lo más nuevo arriba)
- 19/11/2026 · Líder: A2-aj revisada contra código y pruebas (17 pasan) y unida a la rama de fase (`df7cb9a`); suite en la rama de fase: 960 pasan, 2 fallas conocidas de Dropbox. Director aprobó el parámetro `origen` en `_abrir_duda` / `_escribir_elemento` (condiciones en el contrato §6). A3 partida en A3a y A3b.
- 19/11/2026 · Director (pedido de Steven): solo 3 ramas además de `main` (`etapa5-plan`, `etapa5-fase-a`, `etapa5-fase-b`). Cuando A2-aj esté commiteada, se une `claude/etapa5-a2-preparar-3d8018` a `claude/etapa5-fase-a-3da668` y el Director borra esa rama y su worktree. **Desde ahí toda tarea de la Fase A (A3, A4…) trabaja en la rama de fase**: el ejecutor usa un worktree sobre la rama de fase o trabaja por turnos en el worktree del Líder; nunca una rama nueva.
- 19/11/2026 · Líder: plan v3 traído a la rama (merge de `origin/claude/etapa5-plan`, `e853215`). Puerta de A1 resuelta: **D10** orden columnas → losas → muros → pórticos → fundaciones; **D11** diseño por ID + rango con EJES «pendiente de verificar», Claude nunca deduce el cruce en la planta; **D12** de fundaciones solo espesor de platea y f'c, los *drops* a la Mesa; **D13** A6 por lotes en varios días. Límite: máximo 3 sesiones de CATDIC-WEB trabajando a la vez entre las fases. Lanzados los ajustes de A2 con el mismo ejecutor.
- 16/11/2026 · Líder: **A1 hecha** (`PLANES/etapa-5-reconocimiento-asistido.md`). Columnas, losas por etiqueta, muros y pórticos (con recortes) se leen con todo anclado; fundaciones con *drops*, baja. Recomendación: hoja a 72 ppp + recortes a 150 ppp. Propone reordenar A4 (columnas → losas → muros → pórticos → fundaciones). Cuenta Pro: sesiones lectoras cortas y nuevas, 1 pórtico por sesión. A2 revisada contra código y pruebas (8 pasan): aceptada; ejecutor sin archivar para los ajustes. Parada en la puerta de Steven.
- 16/11/2026 · Líder: fase arrancada. Vectorial usado en A1: `SUPERVISION\EN CURSO\TERRA LIVING\ARCHIVOS DEL CLIENTE\PLANOS ESTRUCTURALES\PLANOS ESTRUCTURALES TERRALIVING.pdf` (el mismo de T3n). La BD real no tiene la tabla `planos` (su esquema es de antes de la Etapa 2) y no existe `~\CATDIC-DATOS`: no hay vectorial "vigente" registrado; se usa el archivo de Dropbox en solo lectura.
