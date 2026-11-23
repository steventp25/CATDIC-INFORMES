/* CATDIC-WEB · Mesa de Dudas (B3e). Sustituye al panel lateral M1 (decisión D6: ahora es una pantalla con ruta propia).
   Lista de dudas a un lado; la duda elegida, con el visor de revisión (Ubicación · Detalle · Abrir plano) y su respuesta, al otro.
   En pantalla estrecha se apilan: lista, y al elegir una duda, su detalle con «Volver a la lista».
   props
     obra     (Object, obligatoria)  fila de `proyectos` del tablero
     datos    (Object)               respuesta de GET /api/dashboard (para la visita y sus STP candidatos)
     visitaId (String)               '' = modo obra (dudas sin visita); con valor = modo visita
   evento  actualizar  se respondió una duda: la pantalla vuelve a leer el tablero y las dudas (Inicio, cola y Mis obras al día).
   Rutas:  #/obra/<id>/visitas?visita=<vid>[&duda=<id>]   y   #/obra/<id>/resumen?dudas=obra[&duda=<id>]
   Cómo se ata una duda a su elemento del plano (nunca por id_elemento: el mismo ID se repite en varios niveles):
     · duda de visita: GET /api/dudas/{id}/refs → refs.plano.uid_diseno
     · duda de obra T6n: campo_confirmable.uid
     · si no hay, solo «Abrir plano» y Ubicación/Detalle quedan «pendiente de verificar». */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};

  var UMBRAL_ANCHO = 860;
  var CAMPOS = { fecha_visita: 'Fecha de la visita', clase: 'Clase de la visita', estado: 'Estado de la visita', archivos_json: 'Archivos de la visita' };
  var MSG_CONEXION = 'No hay conexión con el backend. Verifica que el servidor FastAPI esté corriendo.';

  function jsonObj(v) {
    if (v && typeof v === 'object') return v;
    if (typeof v !== 'string' || !v) return {};
    try { var o = JSON.parse(v); return o && typeof o === 'object' ? o : {}; } catch (e) { return {}; }
  }
  function esPlano(campo) { return /^(T6n|T7n):/.test(campo || ''); }
  function esEtiqueta(campo) { return /^elemento_visita:/.test(campo || ''); }

  C.componentes.MesaDudas = {
    props: {
      obra: { type: Object, required: true },
      datos: { type: Object, default: null },
      visitaId: { type: String, default: '' }
    },
    emits: ['actualizar'],
    data: function () {
      return { estado: 'cargando', mensaje: '', dudas: [], entradas: {}, refs: {}, aviso: '', conflicto: '', ancho: 1200, n: 0, nRefs: 0 };
    },
    computed: {
      ruta: function () { return C.rutas.ruta; },
      modoVisita: function () { return !!this.visitaId; },
      visita: function () {
        var id = this.visitaId, vs = (this.datos && this.datos.visitas) || [];
        return id ? (vs.filter(function (v) { return v.id === id; })[0] || null) : null;
      },
      ancha: function () { return this.ancho >= UMBRAL_ANCHO; },
      ordenadas: function () {
        return this.dudas.slice().sort(function (a, b) {
          if (!!a.resuelta !== !!b.resuelta) return a.resuelta ? 1 : -1;
          return a.id - b.id;
        });
      },
      abiertas: function () { return this.dudas.filter(function (d) { return !d.resuelta; }); },
      bloqueantes: function () { return this.abiertas.filter(function (d) { return d.categoria === 'DUDA_BLOQUEANTE'; }).length; },
      idSel: function () { var q = this.ruta.consulta; return q && q.duda ? String(q.duda) : ''; },
      sel: function () {
        var id = this.idSel;
        return id ? (this.ordenadas.filter(function (d) { return String(d.id) === id; })[0] || null) : null;
      },
      actual: function () {
        if (this.sel) return this.sel;
        return this.ancha && this.ordenadas.length ? this.ordenadas[0] : null;
      },
      mostrarLista: function () { return this.ancha || !this.sel; },
      mostrarDetalle: function () { return !!this.actual && (this.ancha || !!this.sel); },
      figuraProcesada: function () { return this.modoVisita && this.visita && this.visita.estado === 'Procesada' && this.bloqueantes > 0; },
      titulo: function () {
        if (!this.modoVisita) return 'Obra ' + (this.obra.nombre || '') + ' · dudas sin visita (plano y datos de la obra)';
        var v = this.visita;
        if (!v) return 'Visita ' + this.visitaId;
        return (v.numero !== null && v.numero !== undefined && v.numero !== '' ? 'Visita ' + v.numero : 'Visita') + (v.nombre_carpeta ? ' · ' + v.nombre_carpeta : '');
      },
      hrefCerrar: function () { return C.rutas.hashObra(this.obra.id, this.modoVisita ? 'visitas' : 'resumen'); },
      hrefLista: function () { return this.modoVisita ? C.rutas.hashVisita(this.obra.id, this.visitaId) : C.rutas.hashMesaObra(this.obra.id); },
      vacioTexto: function () { return this.modoVisita ? 'Esta visita no tiene dudas.' : 'Esta obra no tiene dudas abiertas sin visita.'; },
      refsActual: function () { return this.actual ? (this.refs[this.actual.id] || null) : null; },
      vinculo: function () { return this.actual ? this.vincular(this.actual) : null; },
      hayPlano: function () {
        var pv = this.datos && this.datos.planos_vigentes;
        return pv && typeof pv === 'object' ? !!pv[this.obra.id] : null;   // null = no se sabe: el visor lo averigua
      }
    },
    watch: {
      'obra.id': function () { this.cargar(); },
      visitaId: function () { this.cargar(); },
      'actual.id': function (id) { if (id !== undefined) this.leerRefs(this.actual); }
    },
    created: function () { this.cargar(); },
    mounted: function () {
      var self = this, el = this.$refs.raiz;
      if (el) this.ancho = el.clientWidth || this.ancho;
      if (window.ResizeObserver && el) {
        this._ro = new ResizeObserver(function () { self.ancho = el.clientWidth || self.ancho; });
        this._ro.observe(el);
      }
    },
    beforeUnmount: function () { if (this._ro) this._ro.disconnect(); },
    methods: {
      fechaHora: function (v) { return C.formato.fechaHora(v) || '—'; },
      etiquetaCampo: function (c) { return CAMPOS[c] || c; },
      esPlano: esPlano, esEtiqueta: esEtiqueta,
      claseEstado: function (e) { return C.cola.claseEstado(e); },
      hrefDuda: function (d) { return this.modoVisita ? C.rutas.hashVisita(this.obra.id, this.visitaId, d.id) : C.rutas.hashMesaObra(this.obra.id, d.id); },
      categoria: function (d) { return d.categoria === 'DUDA_BLOQUEANTE' ? 'Bloqueante' : 'Hallazgo interno'; },
      cargar: function (silencioso) {
        var self = this, n = ++this.n, consulta = { proyecto_id: this.obra.id };
        if (this.modoVisita) consulta.visita_id = this.visitaId; else consulta.sin_visita = 'true';
        if (silencioso !== true) { this.estado = 'cargando'; this.mensaje = ''; this.aviso = ''; this.conflicto = ''; }
        return C.api.get('/api/dudas', { consulta: consulta }).then(function (d) {
          if (n !== self.n) return;
          self.dudas = Array.isArray(d) ? d : [];
          self.dudas.forEach(function (x) {
            if (!self.entradas[x.id]) self.entradas[x.id] = { texto: '', stp: '', opcion: '', guardando: false, error: '' };
          });
          self.estado = 'listo';
          if (self.actual) self.leerRefs(self.actual);
        }, function (e) {
          if (n !== self.n) return;
          self.mensaje = e && e.estado === 0 ? MSG_CONEXION + (e.detalle ? ' (' + e.detalle + ')' : '') : ((e && e.mensaje) || MSG_CONEXION);
          self.estado = 'error';
        });
      },
      leerRefs: function (d) {
        var self = this;
        if (!d || !d.visita_id) return;                       // duda de obra: se ata por campo_confirmable.uid
        var r = this.refs[d.id];
        if (r && (r.estado === 'listo' || r.estado === 'cargando')) return;
        this.refs[d.id] = { estado: 'cargando', refs: null, error: '' };
        C.api.get('/api/dudas/' + encodeURIComponent(d.id) + '/refs').then(function (x) {
          self.refs[d.id] = { estado: 'listo', refs: (x && x.refs) || null, error: '' };
        }, function (e) {
          self.refs[d.id] = { estado: 'error', refs: null, error: (e && e.mensaje) || 'No se pudieron leer las referencias de la duda.' };
        });
      },
      reintentarRefs: function (d) { delete this.refs[d.id]; this.leerRefs(d); },
      vincular: function (d) {
        // Devuelve { listo, uid, pagina, nota, motivo }. Nunca por id_elemento.
        if (!d.visita_id) {
          var cc = d.campo_confirmable;
          if (cc && cc.uid) return { listo: true, uid: String(cc.uid), pagina: 0, nota: '', motivo: '' };
          return { listo: true, uid: '', pagina: 0, nota: '', motivo: 'Esta duda de la obra no apunta a un elemento concreto del plano: no se adivina su ubicación.' };
        }
        var r = this.refs[d.id];
        if (!r || r.estado === 'cargando') return { listo: false };
        if (r.estado === 'error') return { listo: false, error: r.error };
        var rf = r.refs, pl = rf && rf.plano;
        if (!rf) return { listo: true, uid: '', pagina: 0, nota: '', motivo: 'Esta duda no trae referencias al plano (no se guardó de dónde salió). No se adivina la ubicación.' };
        if (!pl || !pl.uid_diseno) {
          return { listo: true, uid: '', pagina: pl && pl.pagina ? Number(pl.pagina) : 0,
            nota: pl && pl.pagina ? 'Hoja del plano de la que sale el dato de esta duda; no hay recuadro del elemento.' : '',
            motivo: 'La duda no quedó atada a un elemento de diseño del plano: no se adivina la ubicación.' };
        }
        return { listo: true, uid: String(pl.uid_diseno), pagina: pl.pagina ? Number(pl.pagina) : 0,
          nota: pl.pagina ? 'Hoja del plano que cita la duda.' : '', motivo: '' };
      },
      fotos: function (d) {
        var r = this.refs[d.id], rf = r && r.refs, vp = rf && rf.visita_pdf;
        if (!vp || !vp.pagina) return '';
        var p = Number(vp.pagina);
        if (Array.isArray(vp.paginas) && vp.paginas.length > 1) {
          var a = vp.paginas.map(Number).filter(isFinite);
          if (a.length) return 'Fotos p. ' + Math.min.apply(null, a) + '–' + Math.max.apply(null, a);
        }
        return 'Foto p. ' + p;
      },
      etiquetaVisita: function (d) {
        var r = this.refs[d.id], el = r && r.refs && r.refs.elemento;
        return d.id_elemento || (el && el.etiqueta) || '(sin etiqueta)';
      },
      candidatos: function () {
        var v = this.visita, o = jsonObj(v && v.origen_datos_json), g = o.stp_candidatos;
        return Array.isArray(g) ? g.filter(function (x) { return Array.isArray(x) && x.length; }) : [];
      },
      tipoControl: function (d) {
        if (d.categoria === 'HALLAZGO_INTERNO') return 'hallazgo';
        if (d.campo_confirmable) return 'campo';
        if (d.id_elemento) return 'texto';
        var c = d.campo_afectado;
        if (c === 'fecha_visita') return 'fecha';
        if (c === 'clase') return 'clase';
        if (c === 'estado') return 'estado';
        if (c === 'archivos_json') return 'archivos';
        return 'otro';
      },
      puedeEnviar: function (d) {
        var e = this.entradas[d.id]; if (!e || e.guardando) return false;
        var t = this.tipoControl(d);
        if (t === 'hallazgo') return true;
        if (t === 'estado') {
          if (!e.opcion) return false;
          return !(e.opcion === 'corresponde' && this.candidatos().length > 1 && e.stp === '');
        }
        return !!String(e.texto || '').trim();
      },
      enviar: function (d) {
        var e = this.entradas[d.id], t = this.tipoControl(d), cuerpo;
        if (!e || e.guardando || !this.puedeEnviar(d)) return;
        if (t === 'hallazgo') cuerpo = { respuesta: 'revisado' };
        else if (t === 'estado') {
          cuerpo = { respuesta: e.opcion };
          var g = this.candidatos();
          if (e.opcion === 'corresponde' && g.length > 1) cuerpo.stp = g[Number(e.stp)];
        } else cuerpo = { respuesta: String(e.texto).trim() };
        e.guardando = true; e.error = ''; this.aviso = ''; this.conflicto = '';
        var self = this;
        // Un PATCH no se reintenta solo: si falla, se muestra y Steven decide.
        C.api.patch('/api/dudas/' + encodeURIComponent(d.id), cuerpo).then(function (r) {
          e.guardando = false;
          var t2 = 'Duda ' + (r && r.duda_id !== undefined ? r.duda_id : d.id) + ' respondida.';
          if (r && r.valor_aplicado !== null && r.valor_aplicado !== undefined && r.valor_aplicado !== '') t2 += ' Valor aplicado: ' + self.valorTexto(r.valor_aplicado) + '.';
          if (r && r.estado_visita) t2 += ' Estado de la visita: ' + r.estado_visita + '.';
          self.aviso = t2;
          return self.cargar(true).then(function () { self.$emit('actualizar'); });
        }, function (err) {
          e.guardando = false;
          if (err && err.estado === 409) {
            self.conflicto = ((err.mensaje || 'La duda cambió.') + ' Se recargaron las dudas.').replace(/\.\s+Se recargaron/, '. Se recargaron');
            return self.cargar(true).then(function () { self.$emit('actualizar'); });
          }
          e.error = err && err.estado === 0 ? MSG_CONEXION : ((err && err.mensaje) || 'No se pudo guardar la respuesta.');
        });
      },
      valorTexto: function (v) {
        if (v && typeof v === 'object') return v.estado !== undefined ? String(v.estado) : JSON.stringify(v);
        var s = String(v);
        return /^\d{4}-\d{2}-\d{2}/.test(s) ? (C.formato.fecha(s) || s) : s;
      },
      enfocarDetalle: function () {
        var self = this;
        this.$nextTick(function () { var h = self.$refs.tit; if (h && h.focus) h.focus({ preventScroll: false }); });
      }
    },
    template: `
      <section ref="raiz" class="caja mesa" :class="{ 'mesa-ancha': ancha }" aria-labelledby="mesa-t" data-mesa :data-modo="modoVisita ? 'visita' : 'obra'">
        <div class="caja-cabeza mesa-cab">
          <div class="mesa-tit">
            <h2 id="mesa-t">Mesa de Dudas</h2>
            <p class="mesa-sub" :data-mesa-obra="modoVisita ? null : ''">{{ titulo }}<span v-if="visita && modoVisita" class="est" style="margin-inline-start:.5em" :class="claseEstado(visita.estado)">{{ visita.estado }}</span></p>
          </div>
          <a class="btn btn-sec" :href="hrefCerrar" data-cerrar-mesa><Icono nombre="cerrar"/>Cerrar</a>
        </div>

        <p v-if="estado === 'listo' && aviso" class="aviso aviso-ok" role="status" data-aviso-mesa><Icono nombre="check"/>{{ aviso }}</p>
        <p v-if="conflicto" class="aviso aviso-mal" role="alert" data-conflicto-mesa><Icono nombre="alerta"/>{{ conflicto }}</p>
        <p v-if="figuraProcesada" class="aviso aviso-mal" role="alert" data-aviso-procesada><Icono nombre="alerta"/>Esta visita figura como Procesada pero tiene dudas bloqueantes abiertas.</p>

        <div v-if="estado === 'cargando'" class="cargando" aria-busy="true" aria-live="polite"><span class="sr">Cargando dudas…</span><span class="hueso" style="--i:0"></span><span class="hueso" style="--i:1"></span><span class="hueso" style="--i:2"></span></div>
        <div v-else-if="estado === 'error'" class="error" role="alert" data-error-mesa>
          <Icono nombre="alerta"/>
          <div><p class="error-t">No se pudieron leer las dudas.</p><p>{{ mensaje }}</p><button type="button" class="btn btn-sec" @click="cargar()">Reintentar</button></div>
        </div>
        <div v-else-if="!dudas.length" class="vacio" data-mesa-vacia><p class="vacio-t">{{ vacioTexto }}</p></div>

        <div v-else class="mesa-cuerpo">
          <nav v-if="mostrarLista" class="mesa-lista" aria-label="Dudas">
            <p class="mesa-cuenta" data-mesa-cuenta>{{ abiertas.length }} {{ abiertas.length === 1 ? 'duda abierta' : 'dudas abiertas' }}<template v-if="bloqueantes"> · {{ bloqueantes }} {{ bloqueantes === 1 ? 'bloqueante' : 'bloqueantes' }}</template><template v-if="dudas.length > abiertas.length"> · {{ dudas.length - abiertas.length }} {{ dudas.length - abiertas.length === 1 ? 'resuelta' : 'resueltas' }}</template></p>
            <ul class="mesa-ul">
              <li v-for="d in ordenadas" :key="d.id">
                <a class="mesa-item" :class="{ 'es-sel': actual && actual.id === d.id, 'es-resuelta': d.resuelta }" :href="hrefDuda(d)" :data-duda-item="d.id" :aria-current="actual && actual.id === d.id ? 'true' : null">
                  <span class="mesa-item-cab">
                    <span class="num mesa-id">#{{ d.id }}</span>
                    <span class="etq" :class="d.categoria === 'DUDA_BLOQUEANTE' ? 'etq-acento' : ''"><Icono :nombre="d.categoria === 'DUDA_BLOQUEANTE' ? 'alerta' : 'info'"/>{{ categoria(d) }}</span>
                    <span v-if="d.resuelta" class="etq"><Icono nombre="check"/>Resuelta</span>
                  </span>
                  <span class="mesa-item-p">{{ d.pregunta }}</span>
                  <span class="mesa-item-m">{{ etiquetaCampo(d.campo_afectado) }}<template v-if="d.id_elemento"> · {{ d.id_elemento }}</template></span>
                </a>
              </li>
            </ul>
          </nav>

          <article v-if="mostrarDetalle" class="mesa-det" :data-duda="actual.id" :key="actual.id" aria-labelledby="mesa-d-t">
            <header class="mesa-det-cab">
              <a v-if="!ancha" class="enlace mesa-volver" :href="hrefLista" data-volver-lista><Icono nombre="volver"/>Volver a la lista</a>
              <h3 id="mesa-d-t" ref="tit" tabindex="-1">Duda <span class="num">{{ actual.id }}</span></h3>
              <p class="mesa-badges">
                <span class="etq" :class="actual.categoria === 'DUDA_BLOQUEANTE' ? 'etq-acento' : ''"><Icono :nombre="actual.categoria === 'DUDA_BLOQUEANTE' ? 'alerta' : 'info'"/>{{ categoria(actual) }}</span>
                <span v-if="actual.resuelta" class="etq"><Icono nombre="check"/>Resuelta</span>
              </p>
            </header>

            <p class="mesa-pregunta" data-pregunta>{{ actual.pregunta }}</p>
            <p v-if="esEtiqueta(actual.campo_afectado)" class="mesa-meta" data-etiqueta-visita>Etiqueta en la visita: <b class="num">{{ etiquetaVisita(actual) }}</b><template v-if="fotos(actual)"> · {{ fotos(actual) }}</template></p>
            <p v-else class="mesa-meta">Campo: <b>{{ etiquetaCampo(actual.campo_afectado) }}</b><template v-if="actual.id_elemento"> · Elemento: <b class="num">{{ actual.id_elemento }}</b></template></p>
            <p class="mesa-meta">Creada: <span class="num">{{ fechaHora(actual.creado) }}</span><template v-if="actual.resuelta"> · Resuelta: <span class="num">{{ fechaHora(actual.resuelto_en) }}</span></template></p>
            <p v-if="actual.resuelta" class="mesa-respuesta" data-respuesta>Respuesta: {{ actual.respuesta || '—' }}</p>

            <div v-if="vinculo && vinculo.listo" class="mesa-visor">
              <VisorRevision :key="actual.id + '|' + vinculo.uid" :obra-id="obra.id" :uid="vinculo.uid" :pagina-inicial="vinculo.pagina" :nota-pagina="vinculo.nota"
                :motivo-sin-elemento="vinculo.motivo" :hay-plano="hayPlano"/>
            </div>
            <div v-else-if="vinculo && vinculo.error" class="error" role="alert"><Icono nombre="alerta"/><div><p class="error-t">No se pudo saber a qué elemento del plano se refiere la duda.</p><p>{{ vinculo.error }}</p><button type="button" class="btn btn-sec" data-reintentar-refs @click="reintentarRefs(actual)">Reintentar</button></div></div>
            <div v-else-if="vinculo" class="cargando" aria-busy="true" aria-live="polite"><span class="sr">Buscando el elemento del plano…</span><span class="hueso" style="--i:0"></span></div>

            <form v-if="!actual.resuelta && entradas[actual.id]" class="mesa-resp" @submit.prevent="enviar(actual)" :data-control="tipoControl(actual)">
              <template v-if="tipoControl(actual) === 'hallazgo'">
                <p class="ayuda">Es un hallazgo interno: no pide ningún valor. Márcalo como revisado cuando lo hayas visto.</p>
                <button type="submit" class="btn btn-pri" :disabled="entradas[actual.id].guardando" data-marcar-revisado>{{ entradas[actual.id].guardando ? 'Guardando…' : 'Marcar revisado' }}</button>
              </template>
              <template v-else-if="tipoControl(actual) === 'campo'">
                <p class="mesa-campo" data-campo-plano>Campo del plano: <b class="num">{{ actual.campo_confirmable.id_elemento }}</b> · {{ actual.campo_confirmable.campo }}<template v-if="actual.campo_confirmable.nivel_rango"> · {{ actual.campo_confirmable.nivel_rango }}</template> · propuesto: <b class="num">{{ actual.campo_confirmable.valor === null || actual.campo_confirmable.valor === undefined || actual.campo_confirmable.valor === '' ? 'pendiente de verificar' : actual.campo_confirmable.valor }}</b><template v-if="actual.campo_confirmable.estado"> ({{ actual.campo_confirmable.estado }})</template></p>
                <label class="campo"><span class="campo-e">Valor leído en el plano</span>
                  <input type="text" class="campo-i" v-model="entradas[actual.id].texto" autocomplete="off" data-valor-campo></label>
                <p class="ayuda">Se valida y se guarda en el elemento; queda registrado en la auditoría con tu usuario.</p>
                <button type="submit" class="btn btn-pri" :disabled="!puedeEnviar(actual)" data-confirmar-campo>{{ entradas[actual.id].guardando ? 'Guardando…' : 'Confirmar valor' }}</button>
              </template>
              <template v-else-if="tipoControl(actual) === 'texto'">
                <label class="campo"><span class="campo-e">Respuesta (texto libre)</span>
                  <textarea class="campo-i" rows="2" v-model="entradas[actual.id].texto" data-respuesta-texto></textarea></label>
                <p v-if="esPlano(actual.campo_afectado)" class="ayuda" data-aviso-plano>Esta duda sale de la lectura del plano: tu respuesta se guarda, pero no cambia ningún valor del elemento.</p>
                <p v-if="actual.visita_id && esEtiqueta(actual.campo_afectado)" class="ayuda" data-aviso-etiqueta>Esta duda sale de una etiqueta de foto de la visita: tu respuesta se guarda, pero no cambia la etiqueta ni el elemento.</p>
                <button type="submit" class="btn btn-pri" :disabled="!puedeEnviar(actual)" data-guardar-respuesta>{{ entradas[actual.id].guardando ? 'Guardando…' : 'Guardar respuesta' }}</button>
              </template>
              <template v-else-if="tipoControl(actual) === 'fecha'">
                <label class="campo"><span class="campo-e">Fecha de la visita (DD/MM/AAAA)</span>
                  <input type="text" class="campo-i" maxlength="10" inputmode="numeric" placeholder="DD/MM/AAAA" v-model="entradas[actual.id].texto" autocomplete="off" data-valor-fecha></label>
                <button type="submit" class="btn btn-pri" :disabled="!puedeEnviar(actual)" data-guardar-fecha>{{ entradas[actual.id].guardando ? 'Guardando…' : 'Guardar fecha' }}</button>
              </template>
              <template v-else-if="tipoControl(actual) === 'clase'">
                <label class="campo"><span class="campo-e">Clase de la visita</span>
                  <select class="campo-i" v-model="entradas[actual.id].texto" data-valor-clase>
                    <option value="">Elige la clase…</option><option value="Parcial">Parcial</option><option value="Completivo">Completivo</option>
                  </select></label>
                <button type="submit" class="btn btn-pri" :disabled="!puedeEnviar(actual)" data-guardar-clase>{{ entradas[actual.id].guardando ? 'Guardando…' : 'Guardar clase' }}</button>
              </template>
              <template v-else-if="tipoControl(actual) === 'estado'">
                <fieldset class="campo-grupo"><legend class="campo-e">¿La visita corresponde a un informe STP?</legend>
                  <label class="radio"><input type="radio" :name="'est-' + actual.id" value="corresponde" v-model="entradas[actual.id].opcion" data-estado-corresponde> Corresponde</label>
                  <label class="radio"><input type="radio" :name="'est-' + actual.id" value="no corresponde" v-model="entradas[actual.id].opcion" data-estado-no> No corresponde</label>
                </fieldset>
                <template v-if="entradas[actual.id].opcion === 'corresponde'">
                  <label v-if="candidatos().length > 1" class="campo"><span class="campo-e">STP que corresponde</span>
                    <select class="campo-i" v-model="entradas[actual.id].stp" data-stp>
                      <option value="">Elige el STP…</option>
                      <option v-for="(g, i) in candidatos()" :key="i" :value="String(i)">{{ g.join(' | ') }}</option>
                    </select></label>
                  <p v-else-if="candidatos().length === 1" class="ayuda" data-stp-unico>STP candidato: {{ candidatos()[0].join(' | ') }}</p>
                  <p v-else class="ayuda" data-sin-stp>La visita no tiene STP candidatos guardados: no se puede citar ninguno.</p>
                </template>
                <button type="submit" class="btn btn-pri" :disabled="!puedeEnviar(actual)" data-guardar-estado>{{ entradas[actual.id].guardando ? 'Guardando…' : 'Guardar estado' }}</button>
              </template>
              <p v-else-if="tipoControl(actual) === 'archivos'" class="ayuda" data-archivos>Se cierra sola al sincronizar cuando el PDF esté en la carpeta de la visita. No se responde con texto.</p>
              <p v-else class="ayuda" data-otro>Esta duda ({{ actual.campo_afectado }}) no se responde desde la Mesa de Dudas.</p>
              <p v-if="entradas[actual.id].error" class="dlg-error" role="alert" data-error-duda><Icono nombre="alerta"/>{{ entradas[actual.id].error }}</p>
            </form>
          </article>
          <div v-else-if="ancha" class="mesa-det vacio"><p>Elige una duda de la lista.</p></div>
        </div>
      </section>`
  };
})();
