/* CATDIC-WEB · ElegirObra (B3g): la lista de obras con el acceso a sus informes.
   Lo usan «Informes» (modo 'informes': abre la pestaña Informes de la obra) y «Crear informe» (modo 'hacer': abre esa
   pestaña con el diálogo «Hacer informe» ya abierto). Lee GET /api/dashboard. Solo las obras de Supervisión pueden hacer informe
   hoy (se procesan sus visitas); las de Levantamiento muestran «disponible más adelante» y conservan el acceso a su lista. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};
  var contador = 0;

  C.componentes.ElegirObra = {
    props: { modo: { type: String, default: 'informes' } },   // 'informes' | 'hacer'
    data: function () { contador++; return { uid: 'eo' + contador, estado: 'cargando', mensaje: '', datos: null, n: 0 }; },
    computed: {
      obras: function () {
        var d = this.datos || {}, visitas = d.visitas || [];
        return (d.proyectos || []).map(function (p) {
          var propias = visitas.filter(function (v) { return v.proyecto_id === p.id; });
          return {
            id: p.id, nombre: p.nombre, tipo: C.formato.texto(p.tipo), supervision: p.tipo === 'Supervisión',
            visitas: propias.length,
            lanzables: propias.filter(function (v) { return ['Sin procesar', 'En cola', 'Con dudas'].indexOf(v.estado) !== -1; }).length
          };
        }).sort(function (a, b) { return String(a.nombre || '').localeCompare(String(b.nombre || ''), 'es'); });
      },
      estadoBloque: function () { return this.estado === 'listo' && !this.obras.length ? 'vacio' : this.estado; },
      hacer: function () { return this.modo === 'hacer'; }
    },
    created: function () { this.leer(); },
    methods: {
      leer: function () {
        var self = this, n = ++this.n;
        this.estado = 'cargando'; this.mensaje = '';
        C.api.get('/api/dashboard').then(function (d) {
          if (n !== self.n) return;
          self.datos = d || {}; self.estado = 'listo';
        }, function (e) {
          if (n !== self.n) return;
          self.mensaje = (e && e.mensaje) || 'No se pudo leer la lista de obras.'; self.estado = 'error';
        });
      },
      hrefInformes: function (o) { return C.rutas.hashObra(o.id, 'informes'); },
      hrefHacer: function (o) { return C.rutas.hashObra(o.id, 'informes') + '?hacer=1'; },
      plural: C.cola.plural
    },
    template: `
      <section class="caja" :aria-labelledby="uid + '-t'" data-elegir-obra>
        <div class="caja-cabeza"><h2 :id="uid + '-t'">{{ hacer ? '1. Elige la obra' : 'Informes por obra' }}</h2></div>
        <Bloque :estado="estadoBloque" :huesos="3" vacio-titulo="Todavía no hay obras." vacio-texto="Crea una obra en «Mis obras» para hacer informes de sus visitas."
          accion-texto="Ir a Mis obras" accion-href="#/obras" error-titulo="No se pudo leer la lista de obras." :error-mensaje="mensaje" @reintentar="leer">
          <ul class="eo-lista">
            <li v-for="o in obras" :key="o.id" class="eo-f" :data-obra-informe="o.id">
              <div class="eo-n">
                <b class="eo-nombre">{{ o.nombre }}</b>
                <span class="eo-m"><span v-if="o.tipo">{{ o.tipo }}</span><Pendiente v-else>servicio pendiente de verificar</Pendiente> · <span class="num">{{ plural(o.visitas, 'visita', 'visitas') }}</span><template v-if="o.supervision"> · <span class="num">{{ o.lanzables }}</span> {{ o.lanzables === 1 ? 'se puede lanzar' : 'se pueden lanzar' }}</template></span>
              </div>
              <div class="eo-a">
                <a v-if="hacer && o.supervision" class="btn btn-pri" :href="hrefHacer(o)" data-hacer-en-obra><Icono nombre="mas"/>Hacer informe<span class="sr"> de {{ o.nombre }}</span></a>
                <span v-else-if="hacer" class="eo-no"><Icono nombre="info"/>Los formatos de Levantamiento: disponible más adelante</span>
                <a :class="hacer && o.supervision ? 'enlace' : 'btn btn-sec'" :href="hrefInformes(o)" data-ver-informes><Icono v-if="!(hacer && o.supervision)" nombre="informes"/>Ver informes<span class="sr"> de {{ o.nombre }}</span><Icono v-if="hacer && o.supervision" nombre="flecha"/></a>
              </div>
            </li>
          </ul>
        </Bloque>
      </section>`
  };
})();
