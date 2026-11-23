/* CATDIC-WEB · órdenes de trabajo (B3f): ayudas compartidas (C.ordenes) y el bloque «Órdenes de trabajo de esta obra» (OrdenesObra).
   Las órdenes solo llegan en GET /api/dashboard (`ordenes[]`). No existe ninguna ruta para crearlas ni moverlas: eso es Fase D.
   Aquí no se calcula nada como avance: solo se agrupan y se cuentan las órdenes que trae el servidor. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};

  var ESTADOS = ['Pendiente', 'Asignada', 'En proceso', 'Bloqueada', 'En revisión', 'Entregada'];
  // Cada estado se dice con su palabra, un icono y un borde completo (nunca solo con color).
  var ICONOS = { 'Pendiente': 'reloj', 'Asignada': 'informes', 'En proceso': 'sync', 'Bloqueada': 'alerta', 'En revisión': 'pregunta', 'Entregada': 'check' };

  function lista(datos) { return datos && Array.isArray(datos.ordenes) ? datos.ordenes.filter(function (o) { return o && typeof o === 'object'; }) : []; }

  /* Agrupa por estado: { porEstado: { 'Pendiente': [...], ... }, otros: [{ valor, texto, items }] }.
     Un estado que no es de los 6 no se pierde: va en `otros`, tal cual lo dice el servidor. */
  function agrupar(ordenes) {
    var porEstado = {}, otrosMapa = {}, otros = [];
    ESTADOS.forEach(function (e) { porEstado[e] = []; });
    ordenes.forEach(function (o) {
      if (ESTADOS.indexOf(o.estado) !== -1) { porEstado[o.estado].push(o); return; }
      var k = o.estado === null || o.estado === undefined ? '' : String(o.estado);
      if (!otrosMapa[k]) { otrosMapa[k] = { valor: k, texto: C.formato.texto(k), items: [] }; otros.push(otrosMapa[k]); }
      otrosMapa[k].items.push(o);
    });
    return { porEstado: porEstado, otros: otros };
  }

  /* Dirección de la pantalla de órdenes. q = { obra, tipo, estado }; lo vacío no se escribe. */
  function hash(q) {
    q = q || {};
    var partes = [];
    ['obra', 'tipo', 'estado'].forEach(function (k) {
      if (q[k]) partes.push(k + '=' + encodeURIComponent(q[k]));
    });
    return '#/ordenes' + (partes.length ? '?' + partes.join('&') : '');
  }

  C.ordenes = { ESTADOS: ESTADOS, ICONOS: ICONOS, lista: lista, agrupar: agrupar, hash: hash };

  var MAX_CORTA = 3;

  C.componentes.OrdenesObra = {
    props: {
      obra: { type: Object, required: true },
      ordenes: { type: Array, default: function () { return []; } }
    },
    computed: {
      propias: function () {
        var id = this.obra.id;
        return this.ordenes.filter(function (o) { return o.proyecto_id === id; });
      },
      grupos: function () {
        var g = C.ordenes.agrupar(this.propias), salida = [];
        C.ordenes.ESTADOS.forEach(function (e) {
          if (g.porEstado[e].length) salida.push({ clave: e, etiqueta: e, icono: C.ordenes.ICONOS[e], items: g.porEstado[e] });
        });
        g.otros.forEach(function (o) {
          salida.push({ clave: 'otro:' + o.valor, etiqueta: 'Otro estado: ' + (o.texto || 'pendiente de verificar'), icono: 'info', items: o.items });
        });
        return salida;
      },
      enlace: function () { return C.ordenes.hash({ obra: this.obra.id }); },
      corta: function () { return MAX_CORTA; }
    },
    methods: {
      visibles: function (g) { return g.items.slice(0, MAX_CORTA); },
      texto: function (v) { return C.formato.texto(v); }
    },
    template: `
      <section class="caja" aria-labelledby="oo-t" data-ordenes-obra>
        <div class="caja-cabeza"><h2 id="oo-t">Órdenes de trabajo de esta obra</h2>
          <a v-if="propias.length" class="enlace" :href="enlace">Ver en Órdenes de trabajo<Icono nombre="flecha"/></a></div>
        <p v-if="!propias.length" class="ayuda" data-ordenes-obra-vacio>Esta obra no tiene órdenes de trabajo.</p>
        <ul v-else class="oo-lista">
          <li v-for="g in grupos" :key="g.clave" class="oo-grupo" :data-oo-estado="g.clave">
            <p class="oo-cab"><span class="etq oo-etq"><Icono :nombre="g.icono"/>{{ g.etiqueta }}</span><span class="num oo-n">{{ g.items.length }}</span></p>
            <ul class="oo-corta">
              <li v-for="o in visibles(g)" :key="o.doc_id"><span class="num">{{ o.doc_id }}</span> · <template v-if="texto(o.seccion)">{{ o.seccion }}</template><Pendiente v-else/></li>
              <li v-if="g.items.length > corta" class="ayuda">y {{ g.items.length - corta }} más</li>
            </ul>
          </li>
        </ul>
      </section>`
  };
})();
