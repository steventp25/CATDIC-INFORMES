# Vue 3.5.13 (copia local)

Copia local de la librería Vue. Con ella el tablero funciona sin internet (decisión D5: frontend sin compilación).

| Dato | Valor |
|---|---|
| Archivo | `vue.global.prod.min.js` (build global de producción, con el compilador de plantillas) |
| Versión | 3.5.13 (dentro del archivo: `Bs="3.5.13"`) |
| Origen | https://cdnjs.cloudflare.com/ajax/libs/vue/3.5.13/vue.global.prod.min.js |
| Descargado | 19/11/2026, por el Líder de la Fase B, con autorización de Steven: «Sí, descarga Vue» (relayada por el Director) |
| Tamaño | 154 807 bytes |
| SHA-256 | `220ffd8a70f6161104efbf08802375364d9e4579f2552ba412cf80437f1692fe` |
| Licencia | MIT (© Evan You y colaboradores de Vue) |

- **Uso:** `<script src="/vendor/vue/vue.global.prod.min.js"></script>` expone `window.Vue`.
- **Red:** el archivo no hace peticiones. Las URL que aparecen en el texto son espacios de nombres (SVG/MathML) y el enlace de sus mensajes de error.
- **Reglas:** no se reemplaza ni se actualiza sin un nuevo sí de Steven. No se agrega ninguna otra librería de internet sin ese sí.
- **Comprobación:** `sha256sum FRONTEND/vendor/vue/vue.global.prod.min.js` debe dar el valor de arriba.
