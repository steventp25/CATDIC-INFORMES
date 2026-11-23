# Paquete de visita v1 (CATDIC Campo → CATDIC Informes)

Aprobado por Steven el 22/11/2026: "SI, IMPLEMENTA EL PAQUETE EN CAMPO E INFORMES".

## Para qué

CATDIC Campo exporta, además del PDF, un archivo con los datos de cada elemento ya ordenados
(tipo, ID, ejes y fotos). CATDIC Informes lo carga tal cual, sin leer el PDF ni interpretar texto
libre. **No se usa IA** en ningún paso.

## Archivo

- Nombre: `PAQUETE_VISITA_<OBRA>_<AAAA-MM-DD>.catdic-visita.json`.
- Va en la carpeta de la visita en Dropbox, junto al PDF
  (`LEVANTAMIENTO\VISITA A OBRA\<carpeta de la visita>\`).
- Es un solo archivo JSON con las fotos dentro (base64), sin dependencias nuevas.
- Si la carpeta trae más de un paquete, Informes no elige uno: abre una duda.
- Si la carpeta no trae paquete, Informes sigue leyendo el PDF como antes. Las visitas viejas de
  Report & Run no cambian.

## Estructura

```json
{
  "formato": "catdic-paquete-visita",
  "version": 1,
  "generado_por": "CATDIC Campo (campo-v10)",
  "generado_en": "2026-11-22T15:56:06.719Z",
  "obra": "TERRALIVING",
  "visita": {
    "nombre": "Verticales parcial S-7",
    "fecha": "2026-11-20",
    "clase": "Parcial",
    "nivel": "S-7",
    "supervisores": "…",
    "ing_campo": "…"
  },
  "elementos": [
    {
      "orden": 1,
      "tipo": "COLUMNA",
      "id": "C2",
      "nivel": "",
      "ejes": { "caso": "cruce_puntual", "letra_1": "F", "letra_2": "", "num_1": "11", "num_2": "" },
      "ejes_texto": "EJE F-11",
      "texto_libre": "",
      "mediciones": "L=3.85, E=0.26",
      "estado": "Pendiente",
      "descripcion": "…",
      "fotos": [
        { "numero": 1, "archivo": "foto_001.jpg", "hora": "…", "mime": "image/jpeg", "base64": "…" }
      ]
    }
  ]
}
```

- `visita.fecha` es `AAAA-MM-DD` o vacío. `visita.clase` es `Parcial`, `Completivo` o vacío.
- `elementos[].nivel` vacío significa que se usa el nivel de la visita.
- `fotos[].numero` es el número global de la foto en la visita (1, 2, 3…), único.
- `texto_libre` solo lo llevan los elementos escritos antes de las casillas guiadas.

## Casos de ejes por tipo (los mismos de `formatear_campo_ejes`)

| Tipo | Caso | Ejemplo |
|---|---|---|
| COLUMNA, ZAPATA | `cruce_puntual` | `EJE F-11` |
| MURO H.A., MURO DE CONTENCION | `muro_entre_letras` | `EJE D-E,4` |
| VIGA | `viga_recta_sobre_letra` | `EJE C, ENTRE 2-3` |
| VIGA sin eje-letra | `viga_sin_eje_letra` | `—` |
| PORTICO | `tramo_portico` | `EJE F ENTRE 10-11` |
| LOSA | `losa` | `—` |
| PLATEA | `area` | `(A-B),(1-2)` |
| ESCALERA, OTRO | sin caso | queda `pendiente de verificar` |

## Lo que hace CATDIC Informes al cargarlo

1. Valida `formato` y `version`. Un paquete con otra estructura no carga nada y abre una duda.
2. **No confía en `ejes_texto`:** recalcula los ejes con `formatear_campo_ejes` desde las casillas, y
   exige que el caso sea el del tipo (tabla de arriba).
3. El tipo tiene que estar en `CATEGORIA_POR_TIPO`. `OTRO` o un tipo desconocido queda pendiente.
4. El ID se pasa a mayúsculas. Vacío o con caracteres raros queda pendiente.
5. Nivel:
   - si la carpeta trae un nivel, manda la carpeta;
   - si el paquete trae otro distinto, el nivel queda pendiente y se abre una duda;
   - si la carpeta no trae nivel, se usa el del paquete.
6. Un elemento con tipo, ID, ejes o nivel pendiente abre **una** duda (`elemento_visita:pNNN`), igual
   que el lector del PDF. Los demás entran sin duda.
7. `orden_en_log` es el número de la primera foto del elemento. Las fotos van a la caché local como
   `p<numero>.jpg`, máximo 1000×1000 px, JPG calidad 72, con `exif_transpose` (§5.2). Nunca se
   escriben en Dropbox.
8. `mediciones` y `descripcion` se guardan como nota de la primera foto. **Nunca** llenan
   `medidas_acero_campo_json`: cómo se capturan los valores de OBRA sigue pendiente de Steven.
9. Fecha y clase de la visita:
   - si la visita las tiene pendientes y el paquete trae un valor válido, se llenan y la duda del
     sincronizador se cierra con la respuesta `dato del paquete de Campo`;
   - si la visita ya tiene un valor y el paquete trae otro, no se cambia nada y se abre una duda;
   - si coinciden, no pasa nada.
10. Todo queda en `auditoria` (módulo `PAQUETE_VISITA`). La BD se respalda antes de escribir.
