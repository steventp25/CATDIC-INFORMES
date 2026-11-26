/* CATDIC-WEB · «Dudas abiertas (todas las obras)» de la Bandeja (B3e).
   props: dudas (Array de GET /api/dudas?resuelta=false) · estado ('cargando' | 'listo' | 'error') · mensaje · proyectos (Array)
   evento: reintentar. Agrupa por obra y visita; las dudas de la obra (sin visita) van aparte. Cada grupo enlaza a su Mesa de Dudas. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};

  C.componentes.DudasBandeja = {
    props: {
      dudas: { type: Array, default: function () { return []; } },
      estado: { type: String, default: 'cargando' },
      mensaje: { type: String, default: '' },
      proyectos: { type: Array, default: function () { return []; } }
    },
    emits: ['reintentar'],
    computed: {
      nombres: function () {
        var m = {}; this.proyectos.forEach(function (p) { m[p.id] = p.nombre; }); return m;
      },
      estadoBloque: function () {
        if (this.estado !== 'listo') return this.estado;
        return this.dudas.length ? 'listo' : 'vacio';
      },
      grupos: function () {
        var self = this, vis = {}, obra = {};
        this.dudas.forEach(function (d) {
          if (d.visita_id) {
            var k = d.visita_id;
            vis[k] = vis[k] || { clave: 'v:' + k, pid: d.proyecto_id, vid: k, numero: d.visita_numero, carpeta: d.visita_carpeta, ds: [] };
            vis[k].ds.push(d);
          } else {
            obra[d.proyecto_id] = obra[d.proyecto_id] || { clave: 'o:' + d.proyecto_id, pid: d.proyecto_id, vid: '', ds: [] };
            obra[d.proyecto_id].ds.push(d);
          }
        });
        function dec(g) {
          g.bq = g.ds.filter(function (d) { return d.categoria === 'DUDA_BLOQUEANTE'; }).length;
          g.otras = g.ds.length - g.bq;
          g.obra = self.nombres[g.pid] || ('Obra ' + g.pid);
          g.href = g.vid ? C.rutas.hashVisita(g.pid, g.vid, g.ds[0].id) : C.rutas.hashMesaObra(g.pid, g.ds[0].id);
          g.donde = g.vid ? ((g.numero !== null && g.numero !== undefined && g.numero !== '' ? 'Visita ' + g.numero : 'Visita') + (g.carpeta ? ' · ' + g.carpeta : '')) : 'Dudas de la obra (sin visita)';
          return g;
        }
        function ord(a, b) { return (b.bq - a.bq) || a.obra.localeCompare(b.obra, 'es') || a.donde.localeCompare(b.donde, 'es', { numeric: true }); }
        return {
          visitas: Object.keys(vis).map(function (k) { return dec(vis[k]); }).sort(ord),
          obras: Object.keys(obra).map(function (k) { return dec(obra[k]); }).sort(ord)
        };
      },
      totales: function () {
        var bq = this.dudas.filter(function (d) { return d.categoria === 'DUDA_BLOQUEANTE'; }).length;
        return { n: this.dudas.length, bq: bq, otras: this.dudas.length - bq };
      }
    },
    methods: {
      pl: function (n, s, p) { return n + ' ' + (n === 1 ? s : p); }
    },
    template: `
      <section class="caja" aria-labelledby="t-dudas-ab" data-dudas-bandeja>
        <div class="caja-cabeza"><h2 id="t-dudas-ab">Dudas abiertas (todas las obras)</h2></div>
        <Bloque :estado="estadoBloque" :huesos="3" vacio-titulo="No hay dudas abiertas." vacio-texto="Ninguna obra tiene dudas por responder."
          error-titulo="No se pudieron leer las dudas." :error-mensaje="mensaje" @reintentar="$emit('reintentar')">
          <p class="db-res" data-dudas-resumen>{{ pl(totales.n, 'duda abierta', 'dudas abiertas') }} · {{ pl(totales.bq, 'bloqueante', 'bloqueantes') }} · {{ pl(totales.otras, 'hallazgo interno', 'hallazgos internos') }}</p>
          <template v-if="grupos.visitas.length">
            <h3 class="db-sub">Dudas de visitas</h3>
            <ul class="db-lista">
              <li v-for="g in grupos.visitas" :key="g.clave" class="db-grupo" :data-grupo-dudas="g.clave">
                <span class="db-obra">{{ g.obra }}</span>
                <span class="db-dest"><a class="enlace" :href="g.href">{{ g.donde }}<Icono nombre="flecha"/><span class="sr"> · abrir la Mesa de Dudas</span></a></span>
                <span class="db-cuentas">
                  <span v-if="g.bq" class="etq etq-acento"><Icono nombre="alerta"/>{{ pl(g.bq, 'bloqueante', 'bloqueantes') }}</span>
                  <span v-if="g.otras" class="etq"><Icono nombre="info"/>{{ pl(g.otras, 'hallazgo interno', 'hallazgos internos') }}</span>
                </span>
              </li>
            </ul>
          </template>
          <template v-if="grupos.obras.length">
            <h3 class="db-sub">Dudas de la obra (plano y datos)</h3>
            <ul class="db-lista">
              <li v-for="g in grupos.obras" :key="g.clave" class="db-grupo" :data-grupo-dudas="g.clave">
                <span class="db-obra">{{ g.obra }}</span>
                <span class="db-dest"><a class="enlace" :href="g.href">{{ g.donde }}<Icono nombre="flecha"/><span class="sr"> · abrir la Mesa de Dudas</span></a></span>
                <span class="db-cuentas">
                  <span v-if="g.bq" class="etq etq-acento"><Icono nombre="alerta"/>{{ pl(g.bq, 'bloqueante', 'bloqueantes') }}</span>
                  <span v-if="g.otras" class="etq"><Icono nombre="info"/>{{ pl(g.otras, 'hallazgo interno', 'hallazgos internos') }}</span>
                </span>
              </li>
            </ul>
          </template>
        </Bloque>
      </section>`
  };
})();
