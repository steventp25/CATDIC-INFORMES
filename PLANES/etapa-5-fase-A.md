# Etapa 5 · Fase A — Claude razona los planos (estado de la fase)

Líder: sesión Opus (`claude/etapa5-fase-a-3da668`). Director: la sesión que la lanzó. Plan y decisiones: `PLANES/etapa-5.md` (manda sobre este archivo).
Reglas de la fase: sin llave de API ni servicios de pago; **máximo 1 Ejecutor trabajando a la vez**; commits locales en ramas `claude/etapa5-*`, ningún push ni fusión; BD real y Dropbox en solo lectura; nunca se commitean PDFs, imágenes, `*.db` ni hojas preparadas.

## Tareas

| Tarea | Qué | Quién | Rama | Estado |
|---|---|---|---|---|
| A1 | Reconocimiento con el vectorial de Terra Living (4–6 hojas, 2–3 resoluciones) → `etapa-5-reconocimiento-asistido.md` | Líder | `claude/etapa5-fase-a-3da668` | en curso |
| A2 | Preparar hojas: `plano/asistido/preparar.py` (+ `__init__.py`, pruebas) | Ejecutor Sonnet | `claude/etapa5-a2-preparar` | pendiente de lanzar |
| — | **Puerta de Steven:** ve el informe de A1 antes de A3 y A4 | Director | — | esperando A1 |
| A3 | Importar con anclaje: `esquema.py`, `importar.py`, pruebas | Ejecutor Sonnet (partido en ≤ 1 h) | sale de A2 | bloqueada por la puerta |
| A4 | Skill `extraer-plano` (A4a columnas · A4b muros y zapatas · A4c pórticos · A4d losas) | Líder | — | bloqueada por la puerta |
| A5 | Rutas `plano/asistido/rutas.py` + 1 línea `include_router` en `main.py` | Ejecutor Sonnet | sale de A3 | pendiente |
| A6 | Prueba real (Terra Living completo + P16 Losa E-9) y cierre | Líder + sesión lectora | — | pendiente |
| A7 | (Opcional) lanzar Claude desde el tablero sin costo | Líder (investigación) | — | al final, si da tiempo |

Contrato de archivos (`textos.json`, `propuesta.json`): se fija en `PLANES/etapa-5-contrato-asistido.md` después de A1. A2 arranca con el formato provisional de `textos.json` de su brief.

## Bitácora (lo más nuevo arriba)
- 16/11/2026 · Líder: fase arrancada. Vectorial usado en A1: `SUPERVISION\EN CURSO\TERRA LIVING\ARCHIVOS DEL CLIENTE\PLANOS ESTRUCTURALES\PLANOS ESTRUCTURALES TERRALIVING.pdf` (el mismo de T3n). La BD real no tiene la tabla `planos` (su esquema es de antes de la Etapa 2) y no existe `~\CATDIC-DATOS`: no hay vectorial "vigente" registrado; se usa el archivo de Dropbox en solo lectura.
