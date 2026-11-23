/* CATDIC-WEB · AvanceTrabajo: el avance en vivo de un trabajo del procesador de la cola (B3d, T10b), como componente común.
   Lo usan la pantalla «Avance del trabajo» (#/trabajo/<id>) y la pestaña «Informes» de la obra (B3g), sin copiar código.
   props: trabajoId (el id del trabajo)   ·   emite `terminado(trabajo)` cuando el servidor da el trabajo por cerrado.
   Lee:
     GET /api/trabajos/{id}                      estado, resumen y error del trabajo
     GET /api/trabajos/{id}/eventos?desde=<n>    eventos nuevos (visita_inicio, elemento_inicio, elemento_listo, duda, aviso,
                                                 pdf_generado, visita_fin, fin); se pide cada 2 s mientras el trabajo corre
   Los eventos viven en el servidor: se puede cerrar y volver a abrir sin perder nada.
   Al desmontarse cancela la petición en vuelo (AbortController) y el siguiente turno (clearTimeout).
   Fuera de B3d: responder la duda aquí (Mesa de Dudas, B3e) y el visor del plano junto a la duda (B3b). */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};

  var TXT_ELEMENTO = { procesando: 'Procesando…', listo: 'Listo', anterior: 'Pertenece al anterior', espera: 'En espera de una respuesta' };
  var CLASE_ELEMENTO = { procesando: 'el-corre', listo: 'el-listo', anterior: 'el-ant', espera: 'el-espera' };

  function etiquetaElemento(e) {
    if (!e) return '(sin elemento)';
    var partes = [e.etiqueta || '(sin etiqueta)'];
    if (e.nivel) partes.push(e.nivel);
    if (e.ejes) partes.push(e.ejes);
    return partes.join(' · ');
  }

  C.componentes.AvanceTrabajo = {
    props: { trabajoId: { type: String, required: true } },
    emits: ['terminado'],
    data: function () {
      return {
        estado: 'cargando',          // cargando | listo | vacio (404) | error
        mensaje: '',
        trabajo: null,
        eventos: [],
        ultimo: 0,
        siguiendo: false,
        perdido: '',                 // el seguimiento se cortó (error de red): hay que reintentar
        obraDe: {},                  // visita_id -> proyecto_id (del tablero), para los enlaces
        reloj: null,
        control: null,
        n: 0
      };
    },
    computed: {
      id: function () { return this.trabajoId; },
      corriendo: function () { return !!this.trabajo && this.trabajo.estado === 'corriendo'; },
      claseEstado: function () {
        var e = this.trabajo && this.trabajo.estado;
        return e === 'terminado' ? 'p-ok' : (e === 'corriendo' ? 'p-corre' : 'p-mal');
      },
      iconoEstado: function () {
        var e = this.trabajo && this.trabajo.estado;
        return e === 'terminado' ? 'check' : (e === 'corriendo' ? 'reloj' : 'alerta');
      },
      textoEstado: function () {
        var e = this.trabajo && this.trabajo.estado;
        if (e === 'terminado') return 'El procesamiento terminó.';
        if (e === 'fallido') return 'El procesamiento falló.';
        if (e === 'corriendo') return this.perdido ? 'Se perdió el seguimiento del trabajo.' : 'Procesando la cola…';
        return 'Estado del trabajo: ' + (e || 'desconocido');
      },
      // Las visitas del trabajo, armadas con los eventos (en el orden en que empezaron).
      visitas: function () {
        var orden = [], por = {};
        function de(id) {
          if (!por[id]) { por[id] = { id: id, numero: null, carpeta: '', estado: null, error: '', fin: false, elementos: [], idxEl: {}, dudas: [], avisos: [], pdf: [] }; orden.push(por[id]); }
          return por[id];
        }
        function elemento(v, refs) {
          var e = refs && refs.elemento;
          var uid = e && e.uid != null ? String(e.uid) : '?';
          if (!v.idxEl[uid]) { v.idxEl[uid] = { uid: uid, texto: etiquetaElemento(e), estado: 'procesando', titulo: '', reintento: false, dudas: 0 }; v.elementos.push(v.idxEl[uid]); }
          return v.idxEl[uid];
        }
        this.eventos.forEach(function (ev) {
          if (!ev.visita_id) return;
          var v = de(ev.visita_id);
          switch (ev.tipo) {
            case 'visita_inicio': v.numero = ev.numero; v.carpeta = ev.carpeta || ''; break;
            case 'elemento_inicio': elemento(v, ev).reintento = !!ev.reintento; break;
            case 'elemento_listo': { var e = elemento(v, ev); e.estado = ev.anterior ? 'anterior' : 'listo'; e.titulo = ev.titulo || ''; break; }
            case 'duda': {
              var el = ev.elemento ? elemento(v, ev) : null;
              if (el) el.dudas++;
              v.dudas.push({ n: ev.n, id: ev.duda_id, nueva: ev.nueva, campo: ev.campo, pregunta: ev.pregunta, elemento: el ? el.texto : '' });
              break;
            }
            case 'aviso': v.avisos.push(ev.texto); break;
            case 'pdf_generado': v.pdf.push({ formato: ev.formato, ruta: ev.ruta, conDudas: !!ev.con_dudas, bytes: ev.bytes }); break;
            case 'visita_fin':
              v.fin = true; v.estado = ev.estado || null; v.error = ev.error || '';
              v.elementos.forEach(function (x) { if (x.estado === 'procesando') x.estado = 'espera'; });
              break;
          }
        });
        return orden;
      },
      totalDudas: function () { return this.visitas.reduce(function (s, v) { return s + v.dudas.length; }, 0); },
      resumenFinal: function () {
        var t = this.trabajo;
        return t && t.estado !== 'corriendo' && t.resumen ? C.cola.resumirTrabajo(t) : '';
      }
    },
    created: function () { this.cargar(); },
    beforeUnmount: function () { this.parar(); },
    watch: { id: function () { this.cargar(); } },
    methods: {
      parar: function () {
        if (this.reloj) clearTimeout(this.reloj);
        this.reloj = null;
        if (this.control) this.control.abort();
        this.control = null;
        this.siguiendo = false;
      },
      etiqueta: function (e) { return TXT_ELEMENTO[e] || e; },
      claseEl: function (e) { return CLASE_ELEMENTO[e] || ''; },
      hrefVisita: function (vid) {
        var p = this.obraDe[vid];
        return p ? C.rutas.hashVisita(p, vid) : '';
      },
      textoVisita: function (v) {
        var n = v.numero !== null && v.numero !== undefined && v.numero !== '' ? 'Visita ' + v.numero : 'Visita';
        return v.carpeta ? n + ' · ' + v.carpeta : n;
      },
      estadoVisita: function (v) {
        if (v.error) return 'Con error';
        if (v.fin) return v.estado || 'Terminada';
        return 'Procesando…';
      },
      hrefPdf: function (ruta) { return '/api/informes/archivo?ruta=' + encodeURIComponent(ruta); },
      hora: function (v) { return C.formato.fechaHora(v) || v; },
      claseVisita: function (v) { return v.error ? 'est-mal' : (v.fin ? C.cola.claseEstado(v.estado) : 'est-cola'); },
      kb: function (b) { return typeof b === 'number' ? Math.max(1, Math.round(b / 1024)).toLocaleString('es') + ' KB' : null; },
      cargar: function () {
        var self = this, n = ++this.n;
        this.parar();
        this.estado = 'cargando'; this.mensaje = ''; this.trabajo = null; this.eventos = []; this.ultimo = 0; this.perdido = '';
        this.control = new AbortController();
        var senal = this.control.signal;
        // El tablero solo sirve para enlazar cada visita con su obra: si falla, las dudas salen sin enlace.
        C.api.get('/api/dashboard', { senal: senal }).then(function (d) {
          if (n !== self.n) return;
          var m = {};
          ((d && d.visitas) || []).forEach(function (v) { m[v.id] = v.proyecto_id; });
          self.obraDe = m;
        }, function () { /* sin enlaces */ });
        C.api.get('/api/trabajos/' + encodeURIComponent(this.id), { senal: senal }).then(function (t) {
          if (n !== self.n) return;
          self.trabajo = t || {}; self.estado = 'listo';
          self.turno(n);
        }, function (e) {
          if (n !== self.n || (e && e.cancelada)) return;
          if (e && e.estado === 404) { self.estado = 'vacio'; return; }
          self.mensaje = (e && e.mensaje) || 'No se pudo leer el trabajo.'; self.estado = 'error';
        });
      },
      // Pide los eventos nuevos; mientras el trabajo corre, vuelve a pedir a los 2 s. Al terminar lee el trabajo una vez más.
      turno: function (n) {
        var self = this;
        if (n !== this.n) return;
        this.reloj = null; this.perdido = ''; this.siguiendo = true;
        if (!this.control) this.control = new AbortController();
        var senal = this.control.signal;
        C.api.get('/api/trabajos/' + encodeURIComponent(this.id) + '/eventos', { consulta: { desde: this.ultimo }, senal: senal }).then(function (r) {
          if (n !== self.n) return;
          var nuevos = (r && r.eventos) || [];
          if (nuevos.length) {
            var vistos = {};
            self.eventos.forEach(function (x) { vistos[x.n] = true; });
            self.eventos = self.eventos.concat(nuevos.filter(function (x) { return !vistos[x.n]; }));
          }
          if (r && typeof r.ultimo === 'number') self.ultimo = r.ultimo;
          if (r && r.estado === 'corriendo') {
            if (self.trabajo) self.trabajo.estado = 'corriendo';
            self.reloj = setTimeout(function () { self.turno(n); }, C.cola.INTERVALO);
            return;
          }
          self.siguiendo = false;
          self.cerrarTrabajo(n, senal);
        }, function (e) {
          if (n !== self.n || (e && e.cancelada)) return;
          self.siguiendo = false;
          self.perdido = (e && e.mensaje) || 'No se pudo leer el avance.';
        });
      },
      cerrarTrabajo: function (n, senal) {
        var self = this;
        C.api.get('/api/trabajos/' + encodeURIComponent(this.id), { senal: senal }).then(function (t) {
          if (n !== self.n) return;
          self.trabajo = t || self.trabajo;
          self.$emit('terminado', self.trabajo);
          var g = C.cola.tienda.trabajo;
          if (g && g.id === self.id && g.estado === 'corriendo' && t) {
            C.cola.fijarTrabajo({
              id: self.id, estado: t.estado, proyecto: g.proyecto || '', eventos: t.eventos,
              mensaje: t.estado === 'terminado' ? 'Procesamiento terminado.' : 'El procesamiento falló.',
              resumen: C.cola.resumirTrabajo(t), error: t.error || ''
            });
          }
        }, function (e) {
          if (n !== self.n || (e && e.cancelada)) return;
          self.perdido = (e && e.mensaje) || 'No se pudo leer el trabajo.';
        });
      },
      reintentar: function () { this.perdido = ''; this.turno(this.n); }
    },
    template: `
      <div class="avance-trabajo">
        <Bloque :estado="estado" :huesos="3" vacio-titulo="No se encontró ese trabajo."
          vacio-texto="El servidor no tiene ningún trabajo con ese identificador. Pudo ser de una sesión anterior de la base de datos."
          accion-texto="Ir a la Bandeja" accion-href="#/bandeja"
          error-titulo="No se pudo leer el trabajo." :error-mensaje="mensaje" @reintentar="cargar">
          <section class="panel" :class="claseEstado" role="status" aria-live="polite" data-trabajo-estado>
            <div class="panel-cab"><p class="panel-t"><Icono :nombre="iconoEstado"/>{{ textoEstado }}</p></div>
            <p class="panel-d">Estado: <b>{{ trabajo.estado }}</b><template v-if="trabajo.creado"> · creado {{ hora(trabajo.creado) }}</template><template v-if="trabajo.terminado"> · terminado {{ hora(trabajo.terminado) }}</template> · {{ eventos.length }} eventos · {{ totalDudas }} dudas</p>
            <p v-if="resumenFinal" class="panel-d">{{ resumenFinal }}</p>
            <p v-if="trabajo.error" class="panel-e">{{ trabajo.error }}</p>
            <p v-if="perdido" class="panel-e" role="alert" data-seguimiento-perdido>{{ perdido }} <button type="button" class="btn btn-sec" @click="reintentar">Reintentar el seguimiento</button></p>
          </section>

          <div v-if="!visitas.length" class="vacio" data-sin-eventos>
            <p class="vacio-t"><template v-if="corriendo">Esperando el primer evento del procesador…</template><template v-else>Este trabajo no registró avance por visita.</template></p>
          </div>

          <section v-for="v in visitas" :key="v.id" class="caja tr-visita" :aria-labelledby="'tv-' + v.id" :data-visita-trabajo="v.id">
            <div class="caja-cabeza">
              <h2 :id="'tv-' + v.id">{{ textoVisita(v) }}</h2>
              <span class="est" :class="claseVisita(v)">{{ estadoVisita(v) }}</span>
            </div>
            <p v-if="v.error" class="panel-e" role="alert">{{ v.error }}</p>

            <ul v-if="v.elementos.length" class="tr-elementos">
              <li v-for="e in v.elementos" :key="e.uid" class="tr-el" :class="claseEl(e.estado)">
                <span class="tr-el-t">{{ e.texto }}<span v-if="e.reintento" class="etq"> reintento</span></span>
                <span class="tr-el-e"><Icono :nombre="e.estado === 'listo' ? 'check' : (e.estado === 'espera' ? 'pregunta' : (e.estado === 'procesando' ? 'reloj' : 'info'))"/>{{ etiqueta(e.estado) }}<template v-if="e.dudas"> · {{ e.dudas }} {{ e.dudas === 1 ? 'duda' : 'dudas' }}</template></span>
                <span v-if="e.titulo" class="tr-el-ficha">{{ e.titulo }}</span>
              </li>
            </ul>

            <div v-if="v.dudas.length" class="tr-dudas" data-dudas-trabajo>
              <h3 class="tr-sub">Dudas que surgieron ({{ v.dudas.length }})</h3>
              <ul>
                <li v-for="d in v.dudas" :key="d.n" class="tr-duda">
                  <p class="tr-duda-p"><Icono nombre="pregunta"/>{{ d.pregunta }}</p>
                  <p class="tr-duda-m ayuda"><span v-if="d.elemento">{{ d.elemento }} · </span>Campo <span class="num">{{ d.campo }}</span><span v-if="d.nueva" class="etq"> nueva</span></p>
                  <p class="tr-duda-a"><a v-if="hrefVisita(v.id)" class="enlace" :href="hrefVisita(v.id)">Ver la visita<Icono nombre="flecha"/></a><span v-else class="ayuda">Visita <span class="num">{{ v.id }}</span></span></p>
                </li>
              </ul>
              <p class="ayuda">Mesa de Dudas: la construye B3e. Aquí no se responden las dudas.</p>
            </div>

            <ul v-if="v.avisos.length" class="tr-avisos"><li v-for="(a, i) in v.avisos" :key="i"><Icono nombre="info"/>{{ a }}</li></ul>

            <div v-if="v.pdf.length" class="tr-pdf">
              <h3 class="tr-sub">Informes generados</h3>
              <ul>
                <li v-for="(p, i) in v.pdf" :key="i" :title="p.ruta"><span class="num">{{ p.formato }}</span> · <span class="tr-ruta">{{ p.ruta }}</span><template v-if="kb(p.bytes)"> · {{ kb(p.bytes) }}</template><span v-if="p.conDudas" class="etq etq-acento"> con dudas</span> · <a class="enlace tr-abrir" :href="hrefPdf(p.ruta)" target="_blank" rel="noopener" data-abrir-pdf-trabajo>Abrir PDF<Icono nombre="externo"/><span class="sr"> (se abre en una pestaña nueva)</span></a></li>
              </ul>
            </div>
          </section>
        </Bloque>
      </div>`
  };
})();
