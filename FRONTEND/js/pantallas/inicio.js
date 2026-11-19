/* CATDIC-WEB · pantalla «Inicio» (armazón de B2). La construye la tarea B3a.
   Muestra el aviso de «ruta desconocida» que deja el enrutador. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.pantallas = C.pantallas || {};
  C.pantallas['inicio'] = {
    computed: { ruta: function () { return C.rutas.ruta; } },
    methods: { cerrarAviso: function () { C.rutas.ruta.aviso = ''; } },
    template:
      '<div class="pagina">' +
        '<div v-if="ruta.aviso" class="aviso" role="status">' +
          '<p>{{ ruta.aviso }}</p>' +
          '<button type="button" class="btn btn-sec" @click="cerrarAviso">Entendido</button>' +
        '</div>' +
        '<PantallaB3 titulo="Inicio" tarea="B3a" descripcion="Aquí irán las prioridades, las dudas y las próximas acciones. Los vencimientos y las entregas necesitan backend nuevo (Fase D-a) y hoy no se calculan."/>' +
      '</div>'
  };
})();
