/* CATDIC-WEB · componentes Vue compartidos (objetos con `template` en texto: sin compilación).
   app.js los registra todos como componentes globales con el nombre de cada clave. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};

  /* Icono: SVG en línea. Decorativo (aria-hidden); el texto vecino dice lo que significa. */
  var Icono = {
    props: { nombre: { type: String, required: true } },
    computed: { cuerpo: function () { return C.iconos[this.nombre] || ''; } },
    template: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true" focusable="false" v-html="cuerpo"></svg>'
  };

  /* Pendiente: lo que falta se ve como un estado, nunca como un hueco ni se rellena. */
  var Pendiente = {
    template: '<span class="pendiente"><slot>pendiente de verificar</slot></span>'
  };

  /* FaseD: etiqueta discontinua para lo que necesita backend nuevo. No se simula. */
  var FaseD = {
    props: { texto: { type: String, default: '' }, fase: { type: String, required: true } },
    template: '<span class="fase-d" title="Necesita backend nuevo; todavía no existe y no se simula">{{ texto ? texto + \' · \' : \'\' }}Fase {{ fase }}</span>'
  };

  /* Bloque: los 4 estados de un bloque de datos.
       estado = 'cargando' | 'error' | 'vacio' | 'listo'
     cargando: huesos con aria-busy · vacío: mensaje y acción · error: role="alert" y «Reintentar» · listo: el contenido. */
  var Bloque = {
    props: {
      estado: { type: String, default: 'listo' },
      huesos: { type: Number, default: 3 },
      vacioTitulo: { type: String, default: 'No hay nada para mostrar.' },
      vacioTexto: { type: String, default: '' },
      accionTexto: { type: String, default: '' },
      accionHref: { type: String, default: '' },
      errorTitulo: { type: String, default: 'No se pudo leer esta información.' },
      errorMensaje: { type: String, default: '' }
    },
    emits: ['reintentar'],
    template:
      '<div v-if="estado === \'cargando\'" class="cargando" aria-busy="true" aria-live="polite">' +
        '<span class="sr">Cargando…</span>' +
        '<span v-for="i in huesos" :key="i" class="hueso" :style="{ \'--i\': i - 1 }"></span>' +
      '</div>' +
      '<div v-else-if="estado === \'error\'" class="error" role="alert">' +
        '<Icono nombre="alerta"/>' +
        '<div><p class="error-t">{{ errorTitulo }}</p>' +
        '<p v-if="errorMensaje">{{ errorMensaje }}</p>' +
        '<button type="button" class="btn btn-sec" @click="$emit(\'reintentar\')">Reintentar</button></div>' +
      '</div>' +
      '<div v-else-if="estado === \'vacio\'" class="vacio">' +
        '<p class="vacio-t">{{ vacioTitulo }}</p>' +
        '<p v-if="vacioTexto">{{ vacioTexto }}</p>' +
        '<a v-if="accionTexto && accionHref" class="btn btn-sec" :href="accionHref">{{ accionTexto }}</a>' +
      '</div>' +
      '<slot v-else></slot>'
  };

  /* Cajetín: rótulo de la hoja con celdas de línea de tinta. Un campo sin valor dice «pendiente de verificar». */
  var Cajetin = {
    props: { campos: { type: Array, required: true } }, // [{ etiqueta, valor }]
    template:
      '<dl class="cajetin">' +
        '<div v-for="c in campos" :key="c.etiqueta"><dt>{{ c.etiqueta }}</dt>' +
        '<dd><Pendiente v-if="c.valor === null || c.valor === undefined || c.valor === \'\'"/><template v-else>{{ c.valor }}</template></dd></div>' +
      '</dl>'
  };

  /* PestanasObra: las 6 secciones de una obra. La URL lleva la obra y la pestaña. */
  var PestanasObra = {
    props: { id: { type: String, required: true }, activa: { type: String, required: true } },
    computed: { pestanas: function () { return C.rutas.PESTANAS; } },
    methods: { href: function (p) { return C.rutas.hashObra(this.id, p); } },
    template:
      '<nav class="pestanas" aria-label="Secciones de la obra">' +
        '<a v-for="p in pestanas" :key="p[0]" :href="href(p[0])" :aria-current="p[0] === activa ? \'page\' : null">{{ p[1] }}</a>' +
      '</nav>'
  };

  /* PantallaB3: estado vacío honesto de una pantalla que construye una tarea de B3. */
  var PantallaB3 = {
    props: {
      titulo: { type: String, required: true },
      tarea: { type: String, required: true },
      descripcion: { type: String, default: '' }
    },
    template:
      '<div class="pagina">' +
        '<header class="pagina-cabeza"><h1 tabindex="-1">{{ titulo }}</h1></header>' +
        '<section class="caja pantalla-b3" :aria-label="titulo">' +
          '<p class="vacio-t">Esta pantalla todavía no está construida.</p>' +
          '<p v-if="descripcion">{{ descripcion }}</p>' +
          '<p>La construye la tarea <span class="num tarea">{{ tarea }}</span> de la Fase B.</p>' +
          '<a class="enlace" href="/clasico/">Mientras tanto: tablero clásico<Icono nombre="flecha"/></a>' +
        '</section>' +
      '</div>'
  };

  C.componentes = { Icono: Icono, Pendiente: Pendiente, FaseD: FaseD, Bloque: Bloque, Cajetin: Cajetin, PestanasObra: PestanasObra, PantallaB3: PantallaB3 };

  /* Utilidades de formato compartidas por las pantallas */
  C.formato = {
    // Fechas siempre DD/MM/AAAA. Acepta AAAA-MM-DD (con o sin hora) y DD/MM/AAAA; cualquier otra cosa no es una fecha → null.
    fecha: function (v) {
      if (typeof v !== 'string') return null;
      var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(v);
      if (m) return m[3] + '/' + m[2] + '/' + m[1];
      if (/^\d{2}\/\d{2}\/\d{4}$/.test(v)) return v;
      return null;
    },
    // Texto de la BD: vacío o «pendiente de verificar» (lo que escribe el backend) → null (la pantalla lo muestra como pendiente).
    texto: function (v) {
      if (v === null || v === undefined) return null;
      var s = String(v).trim();
      return (s === '' || s.toLowerCase() === 'pendiente de verificar') ? null : s;
    }
  };
})();
