/* CATDIC-WEB · pantalla «Configuración» (B2). Dos cosas reales:
   - «Servidor local»: lee GET /api/dashboard y muestra conectado, cargando o error con «Reintentar».
   - Tema: claro, oscuro o del sistema, guardado en localStorage. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.pantallas = C.pantallas || {};
  C.pantallas['configuracion'] = {
    data: function () {
      return { estado: 'cargando', mensaje: '', obras: null, tema: C.tema.leer(), solicitud: 0 };
    },
    created: function () { this.leer(); },
    methods: {
      leer: function () {
        var self = this, n = ++this.solicitud;
        this.estado = 'cargando'; this.mensaje = '';
        C.api.get('/api/dashboard').then(function (d) {
          if (n !== self.solicitud) return;
          self.obras = d && Array.isArray(d.proyectos) ? d.proyectos.length : null;
          self.estado = 'listo';
        }, function (e) {
          if (n !== self.solicitud) return;
          self.mensaje = e.mensaje; self.estado = 'error';
        });
      },
      elegirTema: function (v) { this.tema = v; C.tema.guardar(v); }
    },
    computed: { servidor: function () { return location.host; } },
    template:
      '<div class="pagina">' +
        '<header class="pagina-cabeza"><h1 tabindex="-1">Configuración</h1></header>' +
        '<div class="rejilla-cfg">' +
          '<section class="caja" aria-labelledby="t-srv">' +
            '<div class="caja-cabeza"><h2 id="t-srv">Servidor local</h2></div>' +
            '<Bloque :estado="estado" :huesos="2" error-titulo="El servidor local no responde." :error-mensaje="mensaje" @reintentar="leer">' +
              '<p class="ok"><Icono nombre="check"/> Conectado</p>' +
              '<dl class="datos">' +
                '<div><dt>Dirección</dt><dd class="num">{{ servidor }}</dd></div>' +
                '<div><dt>Obras registradas</dt><dd class="num"><Pendiente v-if="obras === null"/><template v-else>{{ obras }}</template></dd></div>' +
              '</dl>' +
            '</Bloque>' +
          '</section>' +
          '<section class="caja" aria-labelledby="t-tema">' +
            '<div class="caja-cabeza"><h2 id="t-tema">Apariencia</h2></div>' +
            '<fieldset class="opciones"><legend>Tema</legend>' +
              '<label class="opcion"><input type="radio" name="tema" value="claro" :checked="tema === \'claro\'" @change="elegirTema(\'claro\')"> Claro</label>' +
              '<label class="opcion"><input type="radio" name="tema" value="oscuro" :checked="tema === \'oscuro\'" @change="elegirTema(\'oscuro\')"> Oscuro</label>' +
              '<label class="opcion"><input type="radio" name="tema" value="sistema" :checked="tema === \'sistema\'" @change="elegirTema(\'sistema\')"> Del sistema</label>' +
            '</fieldset>' +
            '<p class="ayuda">«Del sistema» sigue el tema de Windows. La elección se guarda solo en este navegador.</p>' +
          '</section>' +
        '</div>' +
      '</div>'
  };
})();
