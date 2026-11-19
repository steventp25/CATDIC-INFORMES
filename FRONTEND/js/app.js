/* CATDIC-WEB · armazón del tablero nuevo (B2): riel lateral, navegación D6, cabecera móvil y navegación inferior.
   Orden de Tab: Saltar al contenido → marca → Crear informe → navegación → contenido. */
(function () {
  'use strict';
  var C = window.CATDIC;

  var NAV = [
    { id: 'inicio', href: '#/inicio', texto: 'Inicio', corto: 'Inicio', icono: 'inicio' },
    { id: 'obras', href: '#/obras', texto: 'Mis obras', corto: 'Obras', icono: 'obras' },
    { id: 'bandeja', href: '#/bandeja', texto: 'Bandeja de trabajo', corto: 'Bandeja', icono: 'bandeja' },
    { id: 'informes', href: '#/informes', texto: 'Informes', corto: 'Informes', icono: 'informes' },
    { id: 'configuracion', href: '#/configuracion', texto: 'Configuración', corto: 'Configuración', icono: 'config' }
  ];
  var TITULOS = { inicio: 'Inicio', obras: 'Mis obras', bandeja: 'Bandeja de trabajo', informes: 'Informes', configuracion: 'Configuración', 'crear-informe': 'Crear informe', obra: 'Obra' };

  var Raiz = {
    data: function () { return { nav: NAV, primera: true }; },
    computed: {
      ruta: function () { return C.rutas.ruta; },
      // La obra cuelga de «Mis obras»; Crear informe no es una entrada de la navegación.
      activa: function () { return this.ruta.nombre === 'obra' ? 'obras' : this.ruta.nombre; },
      pantalla: function () { return C.pantallas[this.ruta.nombre] || null; }
    },
    watch: {
      'ruta.clave': function () {
        var self = this;
        document.title = 'CATDIC · ' + (TITULOS[this.ruta.nombre] || '');
        // Al cambiar de pantalla el foco pasa al <h1> (no en la carga inicial, para no romper el orden de Tab).
        this.$nextTick(function () {
          var h1 = document.querySelector('main h1');
          if (h1) { h1.focus({ preventScroll: true }); }
          window.scrollTo(0, 0);
        });
      }
    },
    mounted: function () { document.title = 'CATDIC · ' + (TITULOS[this.ruta.nombre] || ''); },
    template:
      '<a class="saltar" href="#contenido" @click.prevent="irAlContenido">Saltar al contenido</a>' +
      '<div class="app">' +
        '<aside class="riel" aria-label="Navegación principal">' +
          '<a class="marca" href="#/inicio"><span class="marca-n">CATDIC</span><span class="marca-s">Control de obras</span></a>' +
          '<a class="btn btn-crear" href="#/crear-informe" :aria-current="activa === \'crear-informe\' ? \'page\' : null"><Icono nombre="mas"/>Crear informe</a>' +
          '<nav aria-label="Secciones"><ul class="nav">' +
            '<li v-for="n in nav" :key="n.id"><a :href="n.href" :aria-current="activa === n.id ? \'page\' : null"><Icono :nombre="n.icono"/>{{ n.texto }}</a></li>' +
          '</ul></nav>' +
          '<p class="riel-pie">Lectura asistida · Fase C</p>' +
        '</aside>' +
        '<header class="cabeza-movil">' +
          '<a class="marca" href="#/inicio"><span class="marca-n">CATDIC</span></a>' +
          '<a class="btn btn-crear" href="#/crear-informe" :aria-current="activa === \'crear-informe\' ? \'page\' : null"><Icono nombre="mas"/>Crear informe</a>' +
        '</header>' +
        '<nav class="nav-inferior" aria-label="Navegación principal (móvil)">' +
          '<a v-for="n in nav" :key="n.id" :href="n.href" :aria-current="activa === n.id ? \'page\' : null"><Icono :nombre="n.icono"/>{{ n.corto }}</a>' +
        '</nav>' +
        '<main id="contenido" tabindex="-1">' +
          '<component :is="pantalla" v-if="pantalla" :key="ruta.clave"/>' +
        '</main>' +
      '</div>',
    methods: {
      irAlContenido: function () {
        var m = document.getElementById('contenido');
        if (m) m.focus();
      }
    }
  };

  var app = Vue.createApp(Raiz);
  Object.keys(C.componentes).forEach(function (k) { app.component(k, C.componentes[k]); });
  C.rutas.iniciar();
  app.mount('#app');
})();
