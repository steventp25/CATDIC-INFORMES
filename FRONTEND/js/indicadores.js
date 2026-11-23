/* CATDIC-WEB · indicadores de la obra y lecturas compartidas de Resumen, Avance y Cierre (B3b).

   ── Indicador (<Indicador/>) ─────────────────────────────────────────────────────────────────────────────────────
   Los 3 indicadores de la obra (N8, N9 y N10 de B0 §10.3) se muestran SIEMPRE «pendiente de verificar»: con su fórmula, el motivo
   (falta la decisión D15) y el rótulo «Fase D-b». Nunca como 0 % ni como barra, y nunca calculados con el número de archivos,
   versiones o visitas (N11). El hueco lleva una X (el patrón de «pendiente» del estilo Plano sellado).
   props   codigo ('n8' | 'n9' | 'n10')

   ── C.obraHechos.mixin ────────────────────────────────────────────────────────────────────────────────────────────
   Para una pestaña con props `obra` (fila de `proyectos`) y `datos` (GET /api/dashboard). Lee, cada una con su estado
   (cargando | listo | error) y su «Reintentar»:
     · dudas abiertas de la obra     GET /api/dudas?resuelta=false&proyecto_id=…
     · informes generados            GET /api/proyectos/{id}/informes      (del más nuevo al más viejo)
     · elementos de diseño           GET /api/proyectos/{id}/elementos     (solo si hay plano vigente)
   y calcula con lo ya leído: visitas de la obra, plano vigente, filas de pendientes (las mismas reglas que Inicio:
   C.datos.prioridades) y los elementos con `revisar_motivo` («plano cambiado: revisar»). Un elemento se identifica por su `uid`. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};

  var MOTIVO = 'Falta la decisión D15: qué cuenta como entrepiso ejecutado y qué es una unidad documental. Sin esa definición no se calcula, y no se sustituye por el número de archivos, versiones o visitas.';
  var DEFINICION = {
    n8: { titulo: 'Avance por entrepisos', formula: 'entrepisos ejecutados y confirmados / total previsto en planos' },
    n9: { titulo: 'Expediente completo', formula: 'unidades documentales completadas / alcance documental final confirmado' },
    n10: { titulo: 'Documentación al día', formula: 'unidades completadas y exigibles / total exigible hasta el avance actual' }
  };
  var contador = 0;

  C.componentes.Indicador = {
    props: { codigo: { type: String, required: true } },
    data: function () { contador++; return { uid: 'ind' + contador }; },
    computed: {
      def: function () { return DEFINICION[this.codigo] || { titulo: this.codigo, formula: '' }; },
      motivo: function () { return MOTIVO; }
    },
    template: `
      <article class="ind" :aria-labelledby="uid" :data-indicador="codigo">
        <h3 :id="uid" class="ind-t">{{ def.titulo }}</h3>
        <p class="ind-f"><span class="ind-fe">Fórmula</span><span class="ind-ft">{{ def.formula }}</span></p>
        <div class="ind-hueco" data-ind-hueco><Pendiente/></div>
        <p class="ind-m">{{ motivo }}</p>
        <p class="ind-r"><FaseD fase="D-b"/></p>
      </article>`
  };

  var mixin = {
    props: {
      obra: { type: Object, required: true },
      datos: { type: Object, required: true }
    },
    data: function () {
      return {
        dudas: null, estadoDudas: 'cargando', mensajeDudas: '', nD: 0,
        informes: [], estadoInf: 'cargando', mensajeInf: '', nI: 0,
        elementos: [], estadoEl: 'cargando', mensajeEl: '', nE: 0
      };
    },
    computed: {
      supervision: function () { return this.obra.tipo === 'Supervisión'; },
      visitas: function () {
        var id = this.obra.id;
        return (this.datos.visitas || []).filter(function (v) { return v.proyecto_id === id; });
      },
      pv: function () { return (this.datos.planos_vigentes || {})[this.obra.id] || null; },
      hayPlano: function () { return !!this.pv; },
      textoPlano: function () {
        var p = this.pv; if (!p) return '';
        var et = C.formato.texto(p.etiqueta_revision);
        return 'Rev. ' + (p.revision !== null && p.revision !== undefined ? p.revision : '(pendiente de verificar)') + (et ? ' · ' + et : '');
      },
      dudasLista: function () { return this.estadoDudas === 'listo' && Array.isArray(this.dudas) ? this.dudas : []; },
      dudasDeVisita: function () { return this.dudasLista.filter(function (d) { return d.visita_id; }); },
      dudasDeObra: function () { return this.dudasLista.filter(function (d) { return !d.visita_id; }); },
      bloqueantes: function () { return this.dudasLista.filter(function (d) { return d.categoria === 'DUDA_BLOQUEANTE'; }).length; },
      // Las mismas reglas que Inicio: si las dudas no se pudieron leer, solo cuenta el estado de la visita.
      filas: function () {
        return C.datos.prioridades({ proyectos: [this.obra], visitas: this.visitas }, this.estadoDudas === 'listo' ? this.dudas : null);
      },
      filasVisita: function () { return this.filas.filter(function (f) { return f.clave.charAt(0) === 'v'; }); },
      filasObra: function () { return this.filas.filter(function (f) { return f.clave.charAt(0) === 'o'; }); },
      revisar: function () { return this.elementos.filter(function (e) { return e && e.revisar_motivo; }); },
      ultimosInformes: function () { return this.informes.slice(0, 3); }
    },
    created: function () { this.leerDudas(); this.leerInformes(); this.leerElementos(); },
    methods: {
      leerDudas: function () {
        var self = this, n = ++this.nD;
        this.estadoDudas = 'cargando'; this.mensajeDudas = '';
        return C.api.get('/api/dudas', { consulta: { resuelta: 'false', proyecto_id: this.obra.id } }).then(function (d) {
          if (n !== self.nD) return;
          if (!Array.isArray(d)) { self.mensajeDudas = 'El servidor respondió algo que no se pudo leer.'; self.estadoDudas = 'error'; return; }
          var id = self.obra.id;
          self.dudas = d.filter(function (x) { return x.proyecto_id === id; }); self.estadoDudas = 'listo';
        }, function (e) {
          if (n !== self.nD) return;
          self.dudas = null; self.mensajeDudas = (e && e.mensaje) || 'No se pudieron leer las dudas.'; self.estadoDudas = 'error';
        });
      },
      leerInformes: function () {
        var self = this, n = ++this.nI;
        this.estadoInf = 'cargando'; this.mensajeInf = '';
        return C.api.get('/api/proyectos/' + encodeURIComponent(this.obra.id) + '/informes').then(function (d) {
          if (n !== self.nI) return;
          if (!d || !Array.isArray(d.informes)) { self.mensajeInf = 'El servidor respondió algo que no se pudo leer.'; self.estadoInf = 'error'; return; }
          self.informes = d.informes; self.estadoInf = 'listo';
        }, function (e) {
          if (n !== self.nI) return;
          self.mensajeInf = (e && e.mensaje) || 'No se pudo leer la lista de informes.'; self.estadoInf = 'error';
        });
      },
      leerElementos: function () {
        var self = this, n = ++this.nE;
        this.mensajeEl = '';
        if (!this.hayPlano) { this.elementos = []; this.estadoEl = 'listo'; return Promise.resolve(); }
        this.estadoEl = 'cargando';
        return C.api.get('/api/proyectos/' + encodeURIComponent(this.obra.id) + '/elementos').then(function (r) {
          if (n !== self.nE) return;
          self.elementos = r && Array.isArray(r.elementos) ? r.elementos : []; self.estadoEl = 'listo';
        }, function (e) {
          if (n !== self.nE) return;
          self.mensajeEl = (e && e.mensaje) || 'No se pudieron leer los elementos de la obra.'; self.estadoEl = 'error';
        });
      },
      recargarHechos: function () { this.leerDudas(); this.leerInformes(); this.leerElementos(); },
      etiquetaDias: function (f) {
        if (f.dias === null) return null;
        if (f.dias < 0) return f.fecha;
        return f.dias === 0 ? 'hoy' : 'hace ' + f.dias + ' d';
      },
      textoElemento: function (e) { return [e.id_elemento, e.ejes, e.nivel_rango].filter(Boolean).join(' · ') || e.uid; },
      hrefElemento: function (e) { return C.rutas.hashVisorPlano(this.obra.id, e.uid); },
      hrefInforme: function (i) { return '/api/informes/archivo?ruta=' + encodeURIComponent(i.ruta || ''); },
      fechaInforme: function (i) { return C.formato.fechaHora(i.fecha); },
      plural: function (n, a, b) { return C.cola.plural(n, a, b); }
    },
    watch: {
      // El tablero se releyó (se subió un plano nuevo): los elementos pueden haber cambiado.
      'pv.revision': function () { this.leerElementos(); }
    }
  };

  C.obraHechos = { mixin: mixin, MOTIVO: MOTIVO, DEFINICION: DEFINICION };
})();
