# Etapa 7 · T1 — La IA lee del plano los elementos de la visita 24 (Fase A, tramo acotado)
Líder de la Fase A, 23/11/2026. Rama `claude/etapa5-fase-a-3da668`, sin push.

## Qué se hizo
- **Plano:** `PLANOS ESTRUCTURALES TERRALIVING.pdf` (Dropbox, solo lectura), sha256 `59c6be81…6eda21`.
- **Hojas leídas:** solo 4.

  | Página (hoja) | Qué tiene | Qué se leyó |
  |---|---|---|
  | p14 (13) | cuadro de columnas | C1 y C3 |
  | p16 (15) | detalle de muros | MH3 |
  | p17 (16) | detalle de muros | MH2 |
  | p8 | detalle típico del muro de contención perimetral | ese detalle |

- **Planta de S-2:** es la p24 («PLANTA ESTRUCTURAL DE SOTANO S2»). Allí aparecen C1, C3 (2 veces), MH2 y MH3. No se leyó con IA:
  - la localización es trabajo del visor (T5);
  - EJES no se deducen de la planta (D11).
- **Cómo se leyó:**
  - Se prepararon las hojas con `plano.asistido.preparar`.
  - Se miraron recortes de cada dibujo.
  - Se escribió un `propuesta.json` por hoja, con citas, todo con evidencia `literal`.
  - `revisar.py` dio 0 valores sin ancla en las 4 hojas.
- **Importación:** con el importador A3d, a una **copia** de la BD.
  - Resultado: 16 elementos nuevos y 28 dudas `IA:`.
  - Reimportar no cambia nada: 16 sin cambios y 0 dudas nuevas.
  - Nada nace `confirmado`: todos los campos están `pendiente_de_verificar` y EJES vale «pendiente de verificar».
- **A4c (muros), lo justo para estos elementos:**
  - nueva referencia `.claude/skills/extraer-plano/referencias/muros.md`;
  - contrato §7 ampliado: numeración de bordes, muro en L y `MURO DE CONTENCION`.

## Niveles
Steven aún no ha dado la equivalencia S-2 ↔ E-n (dato del usuario). Por eso se cargaron **todos los tramos** de cada elemento, con el rango tal como está impreso. El backend elige el tramo de S-2 cuando exista la equivalencia.

## Elementos cargados (copia de la BD)

| Elemento | Tipo | Tramos (`nivel_rango`) | Hoja |
|---|---|---|---|
| C1 | COLUMNA | `FUNDACIONES @ E-3`, `E-3 @ E-8`, `E-8 @ E-12`, `E-12 @ TECHO` | p14 |
| C3 | COLUMNA | los mismos 4 | p14 |
| MH2 | MURO H.A. (en L, 3 bordes) | `FUNDACIONES @ E-1`, `E-1 @ E-2`, `E-2 @ E-8`, `E-8 @ TECHO` | p17 |
| MH3 | MURO H.A. (recto, 2 bordes) | `FUNDACIONES @ E-2`, `E-2 @ E-9`, `E-9 @ TECHO` | p16 |
| MURO DE CONTENCION PERIMETRAL | MURO DE CONTENCION | `SOTANO S - 2` | p8 |

Ejemplos de valores leídos:
- **C1, `FUNDACIONES @ E-3`:** 0.60 × 1.50, `36∅1"`, `9 EST. ∅3/8" @0.10`.
- **C3, `E-3 @ E-8`:** 0.60 × 1.20, `28∅1"`.
- **MH2, `E-1 @ E-2`:** espesor 0.40, bordes de `38Ø1"` y `44Ø1"`, alma `Ø1/2"@0.10` / `Ø3/8"@0.10`.
- **MH3:** espesor 0.40, longitud 1.80, bordes de 0.50 con `14∅1"` (`14∅3/4"` en `E-9 @ TECHO`).
- **Muro de contención:** espesor 0.25.

## Campos de `datos_diseno_json` (para T4)
- **COLUMNA:** `b_m`, `h_m`, `acero_longitudinal`, `estribos`.
- **MURO H.A.:**
  - `espesor`, `longitud`;
  - `borde_<k>.longitud`, `borde_<k>.acero`, `borde_<k>.estribos`, con k = 1..2 (MH3) o 1..3 (MH2);
  - `alma.ASV`, `alma.ASH`, `alma.ganchos`.
- **MURO DE CONTENCION:** `espesor`, `longitud`, `alma.ASV`, `alma.ASH`.
- Los valores van **tal como están impresos**, como texto: `0.60`, `36∅1"`, `7EST. Ø3/8"@0.10`. Un dato no leído vale `"pendiente de verificar"`.
- **Bordes:**
  - MH3: 1 es el extremo de arriba del dibujo y 2 el de abajo.
  - MH2: 1 es el extremo del ala horizontal, 2 la esquina y 3 el extremo del ala vertical.

## Dudas abiertas (28, todas `IA:` y bloqueantes)
- **EJES de los 16 elementos** (D11, A1 §6.2): se cruzan por ID + nivel.
- **C3:** nota «pasa de 1.20 M a 1.50 M atendiendo a plano anterior con licencia» (duda de hoja). El 1.50 del dibujo se propuso igual.
- **MH2:**
  - `longitud` en los 4 tramos: el muro está en L, con alas de 3.85 y 3.80;
  - borde 2 de `FUNDACIONES @ E-1`: la esquina mide 1.00 en un lado y 0.99 en el otro;
  - en `E-1 @ E-2`, nota «8Ø1" COMPREDIDAS ENTRE E1/E2»: ¿esas 8 barras van dentro de las 38 o se suman?
- **Muro de contención:**
  - el ID: es un detalle típico; confirmar que es el «muro del eje 4' (A–D)» de la visita;
  - `longitud`: el detalle no la da;
  - `alma.ASV` y `alma.ASH`: hay dos rótulos `∅1/2"@0.10` sin dirección;
  - nota de hoja «ajuste de indicación espesor de muro de contención… plano anterior».

## Huecos encontrados (no se arreglaron: fuera del tramo)
1. **El importador no guarda la `zona`** (recuadro del DETALLE): `recorte_detalle_json` queda `{}`.
   - Las zonas están en cada `propuesta.json` (en pt) y le sirven a T5 para el visor.
   - Guardarlas es tarea de A5 o F0.
2. **La copia de la BD no tenía plano vigente.** Se registró una fila de prueba en `planos`:
   - `etiqueta_revision = "PRUEBA T1 (copia)"`, `certificado_por = "lider-fase-a (prueba)"`, texto «SIN CERTIFICAR»;
   - sin sellado.
   - Steven no ha certificado nada. En la BD real hay que subir el vectorial y el sellado por la pantalla de obras.
3. **Las secciones de fundaciones** «próximas a eje 4 / A / 1 / D» (p11–p13) también dibujan el muro de contención. No se leyeron, para cuidar el cupo.

## Dónde están los datos
- **Carpeta compartida (durable):** `C:\Users\Steve\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_d03e8098-a6a7-4ac9-a8d0-1a6ecc5cc64f\t1-visita24\`.
  - `pNN/` contiene `textos.*`, `propuesta.json` e `importacion.json`.
  - Scripts: `armar_propuestas.py` y `importar_copia.py`.
- **Copia de la BD:** `…\t1-visita24\bd\catdic_copia_t1.db`.
- **BD real sin cambios:** sha256 `eba26967…34f00d` antes y después.
- **Dropbox:** solo se leyó.

## Cupo
- Semanal (todos los modelos): de 48 % a 52 %, unos 4 puntos.
- Ventana de 5 h: 48 % al terminar (compartida con las demás sesiones).
