# Etapa 5 · Fase B — Rediseño del tablero (estado de la fase)

Líder: sesión Opus (Líder de la Fase B) · rama `claude/etapa5-fase-b-0020e1` (sale de `claude/etapa5-plan`, `dab9cf0`).
Plan madre: `PLANES/etapa-5.md` (decisiones D5–D8, tareas B0–B5). Este archivo es lo que sobrevive a la compactación: se actualiza en cada paso.

## Reglas que mandan en esta fase
- Zona: `FRONTEND/**`, `DESIGN.md`, `PLANES/etapa-5-fase-B.md`, `PLANES/etapa-5-inventario-ui.md`, `PLANES/etapa-5-reportes/B*.md`. **No tocar `BACKEND/**`** (ni rutas, ni respuestas, ni `main.py`): lo que haga falta se pide al Director.
- Sin compilación (D5): varios archivos, Vue y Tailwind locales en `FRONTEND/vendor/`, funciona **sin internet**. El tablero viejo queda en `FRONTEND/clasico/index.html` (abre en `/clasico/`) hasta el cierre.
- Nada de lo que hace hoy el tablero puede perderse (paridad con B0). Textos en español. Lo que falta se muestra como "pendiente de verificar"; nunca datos de ingeniería inventados.
- Máximo **2 Ejecutores trabajando a la vez** en esta fase. Ejecutores `fresh`, en worktree propio, Sonnet medio (Haiku bajo para lo mecánico).
- Git: solo commits locales en ramas `claude/etapa5-*`. Ningún push ni cambio en el checkout principal. Una tarea que depende de otra sale de la rama de la anterior.
- Para ver el tablero: backend desde el worktree con una **copia** de la BD (`CATDIC_DB_PATH` en el scratch), puerto ≠ 8000. Nunca se commitean PDFs, capturas ni `*.db`.
- Hecho de la fase: paridad completa con B0 en el navegador, sin peticiones a internet, `break-ui` sin roturas abiertas, suite del backend igual (943 pasan; 2 fallan por Dropbox).

## Tareas
| Tarea | Qué | Quién | Rama | Estado |
|---|---|---|---|---|
| B0 | Inventario funcional del tablero actual → `PLANES/etapa-5-inventario-ui.md` | Ejecutor Sonnet `b0-inventario` (archivado) | `claude/etapa5-b0-inventario-fb8728` (`effa03a`, traído aquí con cherry-pick) | **aceptada** |
| B1 | Navegación + 3 maquetas (principal y "Confirmar datos del plano") en `FRONTEND/maquetas/{expediente,plano,obra}/` + `FRONTEND/maquetas/NOTAS-DESIGN.md` | Líder | esta rama | **hecha** |
| — | **Puerta de Steven:** elige dirección (vía Director) | Steven | — | esperando |
| B2 | Base: estructura de `FRONTEND/`, `vendor/` local, tokens, armazón con navegación, cliente API, `/clasico/` | Ejecutor | — | bloqueada por la puerta |
| B3a | Obras y tablero | Ejecutor | — | pendiente |
| B3b | Obra: planos, datos de la obra, visor y recuadros | Ejecutor | — | pendiente |
| B3c | Confirmar datos del plano | Ejecutor | — | pendiente |
| B3d | Cola de visitas, subir visita/Dropbox, avance del procesador (cubre T10b) | Ejecutor | — | pendiente |
| B3e | Mesa de Dudas | Ejecutor | — | pendiente |
| B3f | Órdenes de trabajo | Ejecutor | — | pendiente |
| B4 | Movimiento y pulido (`animate`, `choreograph`, `emil-design-eng`), `prefers-reduced-motion` | Ejecutor + Líder | — | pendiente |
| B5 | `break-ui`, teclado, contraste, 1280/1920, paridad con B0, cierre | Líder + Ejecutor | — | pendiente |

Hueco reservado en la navegación: "Lectura asistida" (Fase C, no es de esta fase).

## Bitácora (lo más nuevo arriba)
- 16/11/2026 · Líder: **B1 hecha, parada en la puerta de Steven.** 3 maquetas: A Expediente (sorteo de `impeccable`), B Plano (la que el skill elige), C Obra (continuidad oscuro + amarillo). Revisadas con Playwright a 1280 y 1920: sin desbordes, 0 peticiones externas. Sustituciones declaradas: `FRONTEND/PRODUCT.md` inferido sin entrevista (la fase no permite hablar con Steven) y la página de decisión de `impeccable` sustituida por el reporte al Director. Pendiente al elegir: aviso de telemetría del sorteo (`--from 373b84e9ba2a0560b6dd64bec7b5e4cd`), contrato de dirección y `DESIGN.md`.
- 16/11/2026 · Líder: B0 revisado contra `FRONTEND/index.html`: 93 apariciones / 86 nombres `data-*` (los 86 en la sección 6), 23 `fetch(`, 46 botones, 6 modales; líneas de muestra correctas. Aceptado y Ejecutor archivado. Para B2: el tablero usa `API = 'http://localhost:8000'` fijo; el nuevo debe usar rutas relativas.
- 16/11/2026 · Líder: fase arrancada. Leídos `etapa-5.md`, `CLAUDE.md`, `COLABORACION.md`. B0 lanzado; B1 en curso.
