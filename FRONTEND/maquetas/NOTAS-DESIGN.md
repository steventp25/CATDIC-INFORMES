# Etapa 5 · B1 — Notas de diseño de las 3 direcciones

Borrador para escribir `DESIGN.md` cuando Steven elija una dirección (se escribe al terminar B2 con lo construido, no antes). Las tres usan los mismos datos reales: obras, visitas y dudas de la copia de la BD; la tabla de zapata de muro lindero (pág. 6) del vectorial de Terra Living, documentada en `PLANES/etapa-2-reconocimiento-plano.md`. Lo que no se sabe sale como «pendiente de verificar».

Abrir cada una con doble clic (funcionan sin servidor y sin internet). La píldora de abajo cambia entre «Pantalla principal» y «Confirmar datos del plano».

Origen de las direcciones: `impeccable` (sorteo `seed:1803131c2ceb753a`; la A es la asignada por el sorteo, la B es la que el skill elige como más fuerte, la C sigue al tablero actual). `PRODUCT.md` se escribió inferido del brief porque la fase no permite entrevistar a Steven (ver `FRONTEND/PRODUCT.md`).

Común a las tres: navegación con Obras, Cola de visitas, Mesa de Dudas, Planos y datos de diseño, Órdenes de trabajo y el hueco «Lectura asistida · Fase C» desactivado. Fuentes del sistema de Windows (Segoe UI Variable, Bahnschrift, Consolas): no se descarga nada. Rojo de los informes `RGB(220,0,0)` reservado para marcar la celda del plano de donde sale un valor. Fechas `DD/MM/AAAA`.

---

## A · Expediente — `FRONTEND/maquetas/expediente/index.html`
**Idea:** la app como el formulario STP que Steven ya llena: suelo gris `#efefef` de la hoja de inspección, bandas numeradas («1. Lo que bloquea hoy», «2. Obras»…), columnas agrupadas «Plano | Obra» (capa 1 / capa 2).
- **Organización:** riel lateral fijo azul tinta `#14304d` con las secciones y contadores; la principal es una sola página en bandas numeradas, de lo bloqueante a lo informativo.
- **Tipos:** Segoe UI Variable para el texto, Bahnschrift en mayúsculas para los rótulos de banda, Consolas para números.
- **Firma:** «pendiente de verificar» dibujado como el blanco de un formulario (subrayado discontinuo), nunca como hueco; banda partida «1. Tabla en el plano | 2. Valores propuestos» en Confirmar.
- **Riesgo honesto:** es la más sobria; puede sentirse «de oficina» y densa en tablas.

## B · Plano — `FRONTEND/maquetas/plano/index.html`
**Idea:** la app como un plano estructural: papel blanco con retícula, tinta negra, cajetín, ejes con globos.
- **Organización:** todo gira alrededor de la obra elegida (selector arriba) y pestañas Resumen · Visitas · Plano y datos de diseño · Mesa de Dudas · Órdenes; contador global de dudas siempre visible.
- **Tipos:** Bahnschrift en todo (letra de rotulación técnica), Consolas para direcciones de celda.
- **Firma:** las 24 visitas dibujadas como globos de eje sobre una línea (las repetidas, #1, #17, #21, se apilan), con el estado por relleno y las bloqueantes por un cuadro con su número (forma, no solo color). En Confirmar, la hoja con cajetín y una cota roja con guía que dice de qué celda sale el valor («pág. 6 · fila 6" · col Df»).
- **Riesgo honesto:** la línea de visitas es vistosa pero ocupa alto; con 60+ visitas habrá que comprimirla o paginarla.

## C · Obra — `FRONTEND/maquetas/obra/index.html`
**Idea:** continuidad con el tablero actual (oscuro y amarillo CATDIC), pero ordenado por triaje y pensado para teclado.
- **Organización:** riel de iconos estrecho + barra de comandos `Ctrl K` (obras, visitas y acciones); tarjetas de obra con un «semáforo» de 24 segmentos (uno por visita); la cola como tablero por estado (Con dudas · Sin procesar · Procesada) con lo bloqueado arriba.
- **Tipos:** Segoe UI Variable, Bahnschrift para cifras, Consolas para valores.
- **Firma:** una visita «Procesada» que aún tiene bloqueantes lleva cinta de peligro rayada (y su segmento del semáforo va rayado), no solo color. Confirmar en 3 columnas con `J`/`K` para recorrer valores y `Ctrl Enter` para confirmar.
- **Riesgo honesto:** es la más parecida a lo de hoy; el modo oscuro y los atajos le sirven a quien trabaja muchas horas, pero el plano blanco dentro del oscuro contrasta fuerte.

---

## Para cuando Steven elija
1. Confirmar o corregir `FRONTEND/PRODUCT.md` (nombre «Control Taller», amarillo D6, quién más usará la app).
2. Fijar los tokens de la elegida en `FRONTEND/css/tokens.css` (B2) y escribir `DESIGN.md` en la raíz con lo construido.
3. Se puede tomar un detalle de otra dirección (por ejemplo, el «pendiente» como blanco de formulario de A, o la paleta de comandos de C) sin mezclar los lenguajes.
