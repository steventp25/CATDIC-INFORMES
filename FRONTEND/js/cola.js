/* CATDIC-WEB · cola de visitas (B3d). Un solo componente reutilizable, `ColaVisitas` (Z15 de PLANES/etapa-5-inventario-ui.md):
   en la Bandeja muestra las visitas de todas las obras y en «Visitas y trabajos» las de una sola.
   Aquí también viven lo que comparten las pantallas de la cola: las utilidades de presentación, el trabajo en curso
   (`C.cola.tienda`, para que sobreviva al cambio de pantalla) y el seguimiento cada 2 s con cancelación. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};

  var INTERVALO = 2000;                 // A9: el trabajo se lee cada 2 s mientras corre
  var CLAVE_TRABAJO = 'catdic.trabajo'; // sessionStorage: solo para retomar el seguimiento tras recargar la página
  var ETIQUETAS_CAMPO = { fecha_visita: 'fecha', clase: 'clase', numero: 'número', estado: 'estado', archivos_json: 'archivos (PDF)', lector_visita: 'lectura del PDF' };
  var CLASES_ESTADO = { 'Sin procesar': 'est-sin', 'En cola': 'est-cola', 'En proceso': 'est-proc', 'Con dudas': 'est-dudas', 'En revisión': 'est-rev', 'Procesada': 'est-ok' };

  function esPendiente(v) { return v === null || v === undefined || v === '' || String(v).trim().toLowerCase() === 'pendiente de verificar'; }
  function parsear(txt, porDefecto) {
    if (txt === null || txt === undefined || txt === '') return porDefecto;
    if (typeof txt !== 'string') return txt;
    try { return JSON.parse(txt); } catch (e) { return porDefecto; }
  }
  function lista(txt) { var l = parsear(txt, []); return Array.isArray(l) ? l : []; }
  function plural(n, uno, varios) { return n + ' ' + (n === 1 ? uno : varios); }

  /* Orden de la cola (`visitasOrdenadas` del tablero anterior): obra, número ascendente (sin número válido al final), carpeta. */
  function ordenar(visitas, nombreDe) {
    return visitas.slice().sort(function (a, b) {
      var pa = nombreDe(a.proyecto_id), pb = nombreDe(b.proyecto_id);
      if (pa !== pb) return pa.localeCompare(pb, 'es');
      var na = Number(a.numero), nb = Number(b.numero);
      var va = isFinite(na) && !esPendiente(a.numero), vb = isFinite(nb) && !esPendiente(b.numero);
      if (va && vb && na !== nb) return na - nb;
      if (va !== vb) return va ? -1 : 1;
      return String(a.nombre_carpeta || '').localeCompare(String(b.nombre_carpeta || ''), 'es');
    });
  }

  /* Contadores de la cola. «Con dudas» = visitas con ese estado (como el tablero anterior). */
  function resumen(visitas) {
    var r = { total: visitas.length, conDudas: 0, enCola: 0 };
    visitas.forEach(function (v) {
      if (v.estado === 'Con dudas') r.conDudas++;
      if (v.estado === 'Sin procesar' || v.estado === 'En cola') r.enCola++;
    });
    return r;
  }

  /* «N visitas · P procesadas · X con dudas o con error · K PDF» (A9). */
  function resumirTrabajo(t) {
    var r = t.resumen || {}, vs = Array.isArray(r.visitas) ? r.visitas : [];
    var procesadas = vs.filter(function (v) { return v.estado === 'Procesada'; }).length;
    return vs.length + ' visitas · ' + procesadas + ' procesadas · ' + (vs.length - procesadas) + ' con dudas o con error · ' + (Array.isArray(r.pdf) ? r.pdf.length : 0) + ' PDF';
  }

  /* ---- el trabajo en curso, compartido por las pantallas ---- */
  var tienda = Vue.reactive({ trabajo: null });
  function guardarTrabajo() {
    try {
      var t = tienda.trabajo;
      if (t && t.id) sessionStorage.setItem(CLAVE_TRABAJO, JSON.stringify({ id: t.id, proyecto: t.proyecto || '' }));
      else sessionStorage.removeItem(CLAVE_TRABAJO);
    } catch (e) { /* sin almacenamiento: el trabajo se retoma desde su ruta #/trabajo/<id> */ }
  }
  function fijarTrabajo(t) { tienda.trabajo = t; guardarTrabajo(); }
  function cerrarTrabajo() { tienda.trabajo = null; guardarTrabajo(); }
  (function recuperar() {
    try {
      var g = JSON.parse(sessionStorage.getItem(CLAVE_TRABAJO) || 'null');
      if (g && g.id) tienda.trabajo = { id: g.id, estado: 'corriendo', mensaje: 'Retomando el seguimiento del trabajo…', proyecto: g.proyecto || '', retomado: true };
    } catch (e) { /* nada que retomar */ }
  })();

  /* Lee el trabajo cada 2 s hasta que deja de estar «corriendo». Devuelve { cancelar }: corta la petición en vuelo
     (AbortController) y el siguiente turno (clearTimeout), así que al salir de la pantalla no queda nada colgado. */
  function seguir(id, cb) {
    var control = new AbortController(), reloj = null, vivo = true;
    function turno() {
      reloj = null;
      C.api.get('/api/trabajos/' + encodeURIComponent(id), { senal: control.signal }).then(function (t) {
        if (!vivo) return;
        if (t && t.estado === 'corriendo') {
          if (cb.alLeer) cb.alLeer(t);
          reloj = setTimeout(turno, INTERVALO);
        } else { vivo = false; cb.alTerminar(t || {}); }
      }, function (e) {
        if (!vivo || (e && e.cancelada)) return;
        vivo = false; cb.alFallar(e);
      });
    }
    turno();
    return { cancelar: function () { vivo = false; if (reloj) clearTimeout(reloj); reloj = null; control.abort(); } };
  }

  /* ---- ColaVisitas (Z15) ---- */
  var contador = 0;
  C.componentes.ColaVisitas = {
    props: {
      titulo: { type: String, default: 'Cola de visitas' },
      estado: { type: String, default: 'listo' },            // cargando | error | listo (vacío lo decide el componente)
      mensaje: { type: String, default: '' },
      visitas: { type: Array, default: function () { return []; } },
      proyectos: { type: Array, default: function () { return []; } },
      dudas: { default: null },                                // lista de dudas abiertas, o null si no se pudieron leer
      mostrarObra: { type: Boolean, default: false },
      seleccionada: { type: String, default: '' },
      vacioTexto: { type: String, default: 'Pulsa "Sincronizar desde Dropbox".' }
    },
    emits: ['reintentar'],
    data: function () { contador++; return { uid: 'cola' + contador }; },
    computed: {
      nombres: function () { var m = {}; this.proyectos.forEach(function (p) { m[p.id] = p.nombre; }); return m; },
      ordenadas: function () { var n = this.nombres; return ordenar(this.visitas, function (id) { return String(n[id] || id || ''); }); },
      cuenta: function () { return resumen(this.visitas); },
      estadoBloque: function () { return this.estado !== 'listo' ? this.estado : (this.visitas.length ? 'listo' : 'vacio'); },
      conteo: function () {
        var m = {};
        (this.dudas || []).forEach(function (d) {
          if (!d.visita_id) return;
          var c = m[d.visita_id] = m[d.visita_id] || { bq: 0, abiertas: 0 };
          c.abiertas++; if (d.categoria === 'DUDA_BLOQUEANTE') c.bq++;
        });
        return m;
      }
    },
    watch: { seleccionada: function () { this.mostrarSeleccionada(); } },
    mounted: function () { this.mostrarSeleccionada(); },
    methods: {
      c: function (v) { return this.conteo[v.id] || { bq: 0, abiertas: 0 }; },
      conDudas: function (v) { return v.estado === 'Con dudas' || this.c(v).bq > 0; },
      claseFila: function (v) {
        return { 'con-dudas': this.conDudas(v), 'es-sel': !!this.seleccionada && v.id === this.seleccionada };
      },
      claseEstado: function (e) { return CLASES_ESTADO[e] || 'est-sin'; },
      nombreObra: function (id) { return this.nombres[id] || id; },
      pendientes: function (v) { return lista(v.campos_pendientes_json).map(function (c) { return ETIQUETAS_CAMPO[c] || c; }); },
      detalleMixta: function (v) { return lista(v.clase_detalle_json).filter(function (d) { return d && typeof d === 'object'; }); },
      esPend: esPendiente,
      fecha: function (v) { return C.formato.fecha(v.fecha_visita); },
      hrefVisita: function (v) { return C.rutas.hashVisita(v.proyecto_id, v.id); },
      hrefObra: function (id) { return C.rutas.hashObra(id, 'visitas'); },
      textoBloq: function (n) { return n === 1 ? 'duda bloqueante abierta' : 'dudas bloqueantes abiertas'; },
      textoAbiertas: function (n) { return n === 1 ? 'duda abierta' : 'dudas abiertas'; },
      cuentaTexto: function () { return plural(this.cuenta.total, 'visita', 'visitas') + ' · ' + this.cuenta.conDudas + ' con dudas'; },
      mostrarSeleccionada: function () {
        var self = this;
        if (!this.seleccionada) return;
        this.$nextTick(function () {
          var el = document.getElementById('visita-' + self.seleccionada);
          if (el && el.scrollIntoView) el.scrollIntoView({ block: 'center' });
        });
      }
    },
    template: `
      <section class="caja cola-caja" :aria-labelledby="uid + '-t'" data-cola>
        <div class="caja-cabeza">
          <h2 :id="uid + '-t'">{{ titulo }}</h2>
          <p v-if="estado === 'listo'" class="cola-cuenta num" data-cola-cuenta>{{ cuentaTexto() }}</p>
        </div>
        <slot></slot>
        <p v-if="estado === 'listo' && dudas === null && visitas.length" class="ayuda cola-sin-dudas" role="status">No se pudieron leer las dudas abiertas: la cola no muestra su conteo por visita.</p>
        <Bloque :estado="estadoBloque" :huesos="4" vacio-titulo="No hay visitas registradas." :vacio-texto="vacioTexto"
          error-titulo="Sin datos: no se pudo leer la cola de visitas del backend." :error-mensaje="mensaje" @reintentar="$emit('reintentar')">
          <div class="cola" :class="mostrarObra ? 'con-obra' : 'sin-obra'" role="table" :aria-label="titulo" :aria-rowcount="ordenadas.length + 1">
            <div class="cola-enc" role="row">
              <span v-if="mostrarObra" role="columnheader">Obra</span><span role="columnheader">N.º</span><span role="columnheader">Carpeta de visita</span>
              <span role="columnheader">Fecha</span><span role="columnheader">Clase</span><span role="columnheader">Estado</span>
            </div>
            <div v-for="v in ordenadas" :key="v.id" :id="'visita-' + v.id" class="cola-f" :class="claseFila(v)" role="row" :aria-current="v.id === seleccionada ? 'true' : null" :data-visita="v.id">
              <div v-if="mostrarObra" class="cola-c cola-obra" role="cell"><a :href="hrefObra(v.proyecto_id)">{{ nombreObra(v.proyecto_id) }}</a></div>
              <div class="cola-c cola-num" role="cell"><span class="cola-r" aria-hidden="true">N.º</span><b class="num" v-if="!esPend(v.numero)">{{ v.numero }}</b><Pendiente v-else/></div>
              <div class="cola-c cola-carpeta" role="cell">
                <a v-if="c(v).abiertas > 0" class="cola-enlace" :href="hrefVisita(v)" :title="v.ruta_carpeta || ''"><template v-if="esPend(v.nombre_carpeta)"><Pendiente/></template><template v-else>{{ v.nombre_carpeta }}</template><span class="sr"> · ver las dudas de esta visita</span></a>
                <span v-else :title="v.ruta_carpeta || ''"><template v-if="esPend(v.nombre_carpeta)"><Pendiente/></template><template v-else>{{ v.nombre_carpeta }}</template></span>
              </div>
              <div class="cola-c cola-fecha" role="cell"><span class="cola-r" aria-hidden="true">Fecha</span><span v-if="fecha(v)" class="num">{{ fecha(v) }}</span><Pendiente v-else/></div>
              <div class="cola-c cola-clase" role="cell">
                <span class="cola-r" aria-hidden="true">Clase</span><Pendiente v-if="esPend(v.clase)"/><template v-else>{{ v.clase }}</template>
                <ul v-if="v.clase === 'Mixta'" class="cola-mixta">
                  <li v-for="(d, i) in detalleMixta(v)" :key="i">{{ d.elementos }}: <b>{{ d.clase }}</b></li>
                  <li v-if="!detalleMixta(v).length"><Pendiente>detalle pendiente de verificar</Pendiente></li>
                </ul>
              </div>
              <div class="cola-c cola-estado" role="cell">
                <span v-if="esPend(v.estado)"><Pendiente/></span>
                <span v-else class="est" :class="claseEstado(v.estado)"><Icono v-if="v.estado === 'Con dudas'" nombre="pregunta"/>{{ v.estado }}</span>
                <p v-if="c(v).bq > 0 && v.estado !== 'Con dudas'" class="cola-linea bloq" data-aviso-dudas><Icono nombre="alerta"/>{{ v.estado }} con {{ c(v).bq }} {{ textoBloq(c(v).bq) }}</p>
                <p v-if="c(v).abiertas > 0" class="cola-linea abiertas"><Icono nombre="pregunta"/>{{ c(v).abiertas }} {{ textoAbiertas(c(v).abiertas) }} · <a class="enlace" :href="hrefVisita(v)">Abrir la Mesa de Dudas</a></p>
                <p v-if="pendientes(v).length" class="cola-linea pend">Pendiente: {{ pendientes(v).join(', ') }}</p>
              </div>
            </div>
          </div>
        </Bloque>
      </section>`
  };

  C.cola = {
    INTERVALO: INTERVALO, tienda: tienda, fijarTrabajo: fijarTrabajo, cerrarTrabajo: cerrarTrabajo, seguir: seguir,
    resumen: resumen, ordenar: ordenar, resumirTrabajo: resumirTrabajo, esPendiente: esPendiente, plural: plural, claseEstado: function (e) { return CLASES_ESTADO[e] || 'est-sin'; }
  };
})();
