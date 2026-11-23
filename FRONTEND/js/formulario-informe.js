/* CATDIC-WEB · FormularioInforme (B3g): diálogo «Hacer informe» dentro de una obra.
   Props:  obra = { id, nombre }  ·  visitas = filas de `visitas` del tablero (solo las de esa obra)  ·  inicial = id de visita (opcional)
   Emite:  lanzado({ trabajoId, visita })  ·  cancelar()
   Elegir la visita → ver qué formatos saldrán → lanzar con POST /api/visitas/{id}/procesar (202, con el trabajo).
   Solo se lanzan las visitas que el backend acepta: «Sin procesar», «En cola» y «Con dudas»; las demás se ven, deshabilitadas, con el motivo.
   Los formatos que el sistema genera hoy son STP-MIVED y MIVED FI-01/02/03; el resto va como «disponible más adelante» y no se simula.
   Cambiar los formatos que pide una visita no tiene ruta en el backend: se rotula «Fase D».
   Los 404 y 409 se muestran con el `detail` del servidor. Ningún POST se reintenta solo.
   Accesible como FormularioVisita: <dialog> modal (foco atrapado), Escape cierra, el foco vuelve a quien lo abrió. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};
  var contador = 0;
  var RE_TRABAJO = /trab-\d{8}-\d{6}-[0-9a-f]{6}/;
  var PROCESABLES = ['Sin procesar', 'En cola', 'Con dudas'];   // los estados que acepta procesador_cola.lanzar_trabajo
  // Los nombres con que `formatos_solicitados` puede traer los formularios MIVED (procesador_cola.FORMATOS_FI).
  var NOMBRES_FI = ['MIVED FI', 'MIVED FI-01/02/03', 'FI-01/02/03', 'FORMULARIOS MIVED', 'FI-01', 'FI-02', 'FI-03'];

  // Los 7 formatos activos (CLAUDE.md §3.2). `hoy`: el procesador los genera hoy.
  var FORMATOS = [
    { id: 'STP-MIVED', nombre: 'STP-MIVED', texto: 'Informe de Supervisión Técnica para el MIVED', hoy: true },
    { id: 'FI', nombre: 'MIVED FI-01/02/03', texto: 'Formularios oficiales del MIVED (cimentación; losas, escaleras y vigas; muros y columnas)', hoy: true },
    { id: 'CATDIC-STP', nombre: 'CATDIC-STP', texto: 'Hojas de la plantilla FORMULARIOS MIVED completadas', hoy: false },
    { id: 'HV-LEV', nombre: 'HV-LEV', texto: 'Ficha de levantamiento del refuerzo', hoy: false },
    { id: 'HV-LEVEVAL', nombre: 'HV-LEVEVAL', texto: 'Levantamiento con Profometer 650 AI', hoy: false },
    { id: 'HV-LEVEST', nombre: 'HV-LEVEST', texto: 'Levantamiento con radar GPR Proceq GP8000', hoy: false },
    { id: 'HV-INFTEC', nombre: 'HV-INFTEC', texto: 'Informe técnico completo (Word)', hoy: false }
  ];

  function clave(f) {
    var s = String(f).trim();
    if (NOMBRES_FI.indexOf(s) !== -1) return 'FI';
    return s;
  }
  function formatosDe(v) {
    var l = v && v.formatos_solicitados;
    if (typeof l === 'string') { try { l = JSON.parse(l); } catch (e) { l = null; } }
    return Array.isArray(l) ? l.filter(function (x) { return typeof x === 'string' && x.trim(); }) : null;
  }
  function numeroDe(v) { var n = Number(v && v.numero); return isFinite(n) && v.numero !== null && v.numero !== '' ? n : null; }

  C.informes = { FORMATOS: FORMATOS, PROCESABLES: PROCESABLES, formatosDe: formatosDe, claveFormato: clave };

  C.componentes.FormularioInforme = {
    props: {
      obra: { type: Object, required: true },
      visitas: { type: Array, default: function () { return []; } },
      inicial: { type: String, default: '' }
    },
    emits: ['lanzado', 'cancelar'],
    data: function () {
      contador++;
      return { uid: 'fi' + contador, elegida: this.inicial || '', lanzando: false, error: '', trabajoOtro: '', cerrado: false, apertura: null };
    },
    computed: {
      formatos: function () { return FORMATOS; },
      ordenadas: function () {
        return this.visitas.slice().sort(function (a, b) {
          var na = numeroDe(a), nb = numeroDe(b);
          if (na !== null && nb !== null && na !== nb) return nb - na;
          if ((na === null) !== (nb === null)) return na === null ? 1 : -1;
          return String(b.fecha_visita || '').localeCompare(String(a.fecha_visita || ''));
        });
      },
      lanzables: function () { var self = this; return this.visitas.filter(function (v) { return self.puede(v); }); },
      visita: function () {
        var id = this.elegida;
        return id ? (this.visitas.filter(function (v) { return v.id === id; })[0] || null) : null;
      },
      pedidos: function () {
        var v = this.visita;
        if (!v) return [];
        var l = formatosDe(v);
        if (!l) return null;
        var visto = {}, hechos = [];
        l.forEach(function (f) {
          var k = clave(f);
          if (visto[k]) return;
          visto[k] = true;
          var cat = FORMATOS.filter(function (x) { return x.id === k; })[0];
          hechos.push({ id: k, nombre: cat ? cat.nombre : f, hoy: !!(cat && cat.hoy), conocido: !!cat });
        });
        return hechos;
      },
      saldran: function () { return (this.pedidos || []).filter(function (p) { return p.hoy; }); },
      despues: function () { return (this.pedidos || []).filter(function (p) { return !p.hoy; }); },
      textoSaldran: function () { return this.saldran.map(function (s) { return s.nombre; }).join(', '); },
      textoDespues: function () { return this.despues.map(function (s) { return s.nombre; }).join(', '); },
      titulo: function () { return 'Hacer informe · ' + this.obra.nombre; },
      hrefOtro: function () { return this.trabajoOtro ? C.rutas.hashTrabajo(this.trabajoOtro) : ''; }
    },
    mounted: function () {
      this.apertura = document.activeElement;
      var dlg = this.$refs.dlg;
      if (dlg && dlg.showModal) dlg.showModal(); else if (dlg) dlg.setAttribute('open', '');
      var sel = dlg && dlg.querySelector('input[type="radio"]:checked');
      var primero = sel || (dlg && dlg.querySelector('input[type="radio"]:not(:disabled)'));
      if (primero) primero.focus(); else if (this.$refs.cancelar) this.$refs.cancelar.focus();
    },
    beforeUnmount: function () { this.devolverFoco(); },
    methods: {
      puede: function (v) { return PROCESABLES.indexOf(v.estado) !== -1; },
      motivo: function (v) {
        if (v.estado === 'En proceso') return 'Ya la está procesando un trabajo: espera a que termine.';
        return 'Está «' + (v.estado || 'sin estado') + '»: el procesador solo acepta visitas Sin procesar, En cola o Con dudas.';
      },
      claseEstado: function (e) { return C.cola.claseEstado(e); },
      fecha: function (v) { return C.formato.fecha(v.fecha_visita); },
      pend: function (x) { return C.cola.esPendiente(x); },
      nombresPedidos: function (v) {
        var l = formatosDe(v);
        return l ? l.join(', ') : null;
      },
      atrapar: function (ev) {
        var dlg = this.$refs.dlg; if (!dlg) return;
        var f = [].slice.call(dlg.querySelectorAll('a[href], button, input, select, textarea, [tabindex]')).filter(function (e) { return !e.disabled && e.tabIndex >= 0 && e.offsetParent !== null; });
        if (!f.length) return;
        var primero = f[0], ultimo = f[f.length - 1];
        if (ev.shiftKey && document.activeElement === primero) { ev.preventDefault(); ultimo.focus(); }
        else if (!ev.shiftKey && document.activeElement === ultimo) { ev.preventDefault(); primero.focus(); }
      },
      devolverFoco: function () {
        var a = this.apertura; this.apertura = null;
        if (a && a.isConnected && a.focus) { a.focus({ preventScroll: true }); return; }
        var h1 = document.querySelector('main h1'); if (h1) h1.focus({ preventScroll: true });
      },
      cerrarDialogo: function () {
        var dlg = this.$refs.dlg;
        this.cerrado = true;
        if (dlg && dlg.open && dlg.close) dlg.close();
      },
      cancelar: function () {
        if (this.lanzando) return;
        this.cerrarDialogo();
        this.$emit('cancelar');
      },
      alCerrar: function () { if (this.cerrado) return; this.cerrado = true; this.$emit('cancelar'); },
      fallo: function (mensaje, ref) {
        var self = this;
        this.error = mensaje;
        this.$nextTick(function () { var el = self.$refs[ref]; if (el && el.focus) el.focus(); });
      },
      elegir: function () { this.error = ''; this.trabajoOtro = ''; },
      lanzar: function () {
        var self = this, v = this.visita;
        if (this.lanzando) return;
        this.error = ''; this.trabajoOtro = '';
        if (!v) { this.fallo('Elige la visita de la que quieres hacer el informe.', 'error'); return; }
        if (!this.puede(v)) { this.fallo(this.motivo(v), 'error'); return; }
        this.lanzando = true;
        C.api.post('/api/visitas/' + encodeURIComponent(v.id) + '/procesar').then(function (d) {
          var t = d && d.trabajo;
          self.lanzando = false;
          if (!t || !t.id) { self.fallo('El servidor aceptó la petición pero no devolvió el trabajo. Mira la Bandeja de trabajo antes de volver a intentarlo.', 'error'); return; }
          C.cola.fijarTrabajo({ id: t.id, estado: 'corriendo', mensaje: (d && d.mensaje) || 'Trabajo lanzado.', proyecto: self.obra.id });
          self.cerrarDialogo();
          self.$emit('lanzado', { trabajoId: t.id, visita: v });
        }, function (e) {
          self.lanzando = false;
          var m = RE_TRABAJO.exec((e && e.mensaje) || '');
          self.trabajoOtro = m ? m[0] : '';
          self.fallo((e && e.mensaje) || 'No se pudo lanzar el procesamiento.', 'error');
        });
      }
    },
    template: `
      <dialog ref="dlg" class="dlg" :aria-labelledby="uid + '-t'" data-modal-informe @cancel.prevent="cancelar" @close="alCerrar" @keydown.tab="atrapar">
        <form class="dlg-form" @submit.prevent="lanzar" novalidate>
          <header class="dlg-cab">
            <h2 :id="uid + '-t'" class="dlg-titulo"><Icono nombre="informes"/>{{ titulo }}</h2>
            <button type="button" class="btn btn-sec dlg-x" aria-label="Cerrar" :disabled="lanzando" @click="cancelar"><Icono nombre="cerrar"/></button>
          </header>

          <p class="ayuda">El informe sale de una visita de la obra: el sistema la procesa y deja los PDF en la carpeta de salida. Solo se lanzan las visitas Sin procesar, En cola o Con dudas.</p>

          <fieldset class="opciones inf-visitas" :aria-describedby="uid + '-ayuda'" data-elegir-visita>
            <legend>1. Elige la visita</legend>
            <p :id="uid + '-ayuda'" class="ayuda"><template v-if="!visitas.length">Esta obra no tiene visitas registradas. Sincroniza o sube una visita en «Visitas y trabajos».</template><template v-else-if="!lanzables.length">Ninguna visita de esta obra se puede lanzar ahora; se ven con el motivo.</template><template v-else>{{ lanzables.length }} de {{ visitas.length }} visitas se pueden lanzar.</template></p>
            <ul v-if="visitas.length" class="inf-op-lista">
              <li v-for="v in ordenadas" :key="v.id">
                <label class="vis-op" :class="{ 'es-sel': elegida === v.id, 'no-puede': !puede(v) }" :data-visita-op="v.id">
                  <input type="radio" :name="uid + '-v'" :value="v.id" v-model="elegida" :disabled="!puede(v) || lanzando" :aria-describedby="puede(v) ? null : uid + '-m-' + v.id" @change="elegir">
                  <span class="vis-op-c">
                    <span class="vis-op-t">
                      <b class="num" v-if="!pend(v.numero)">N.º {{ v.numero }}</b><Pendiente v-else>N.º pendiente de verificar</Pendiente>
                      <span class="vis-op-carpeta"><template v-if="pend(v.nombre_carpeta)"><Pendiente>carpeta pendiente de verificar</Pendiente></template><template v-else>{{ v.nombre_carpeta }}</template></span>
                    </span>
                    <span class="vis-op-m">
                      <span v-if="fecha(v)" class="num">{{ fecha(v) }}</span><Pendiente v-else>fecha pendiente de verificar</Pendiente>
                      <span v-if="pend(v.estado)"><Pendiente>estado pendiente de verificar</Pendiente></span>
                      <span v-else class="est" :class="claseEstado(v.estado)"><Icono v-if="v.estado === 'Con dudas'" nombre="pregunta"/>{{ v.estado }}</span>
                      <span class="vis-op-f">Pide: <span v-if="nombresPedidos(v) !== null" class="num">{{ nombresPedidos(v) || 'ningún formato' }}</span><Pendiente v-else>formatos pendientes de verificar</Pendiente></span>
                    </span>
                    <span v-if="!puede(v)" :id="uid + '-m-' + v.id" class="vis-op-no"><Icono nombre="info"/>{{ motivo(v) }}</span>
                  </span>
                </label>
              </li>
            </ul>
          </fieldset>

          <section class="inf-formatos" aria-labelledby="inf-f-t" data-formatos>
            <h3 id="inf-f-t" class="tr-sub">2. Formatos</h3>
            <div v-if="visita" class="inf-sale" role="status" aria-live="polite" data-formatos-visita>
              <p v-if="pedidos === null" class="ayuda"><Pendiente>formatos de la visita pendientes de verificar</Pendiente> El servidor no trae la lista de formatos que pide esta visita.</p>
              <template v-else>
                <p v-if="saldran.length" class="inf-sale-t"><Icono nombre="check"/>Saldrán de esta visita: <b class="num">{{ textoSaldran }}</b></p>
                <p v-else class="inf-sale-t inf-sale-no"><Icono nombre="alerta"/>Esta visita no pide ningún formato que el sistema genere hoy.</p>
                <p v-if="despues.length" class="ayuda"><Icono nombre="info"/>Los pide la visita, pero todavía no se generan: <span class="num">{{ textoDespues }}</span> · disponible más adelante.</p>
              </template>
              <p v-if="visita.estado === 'Con dudas'" class="ayuda"><Icono nombre="pregunta"/>Esta visita está Con dudas: se vuelve a procesar, y si quedan dudas abiertas los PDF salen marcados «CON DUDAS».</p>
            </div>
            <p v-else class="ayuda">Elige una visita para ver qué formatos saldrán.</p>

            <ul class="inf-catalogo" aria-label="Formatos del sistema">
              <li v-for="f in formatos" :key="f.id" class="inf-cat" :class="{ 'es-hoy': f.hoy }">
                <span class="inf-cat-n num">{{ f.nombre }}</span>
                <span class="inf-cat-t">{{ f.texto }}</span>
                <span class="inf-cat-e"><template v-if="f.hoy"><Icono nombre="check"/>Se genera hoy</template><template v-else>Disponible más adelante</template></span>
              </li>
            </ul>
            <p class="ayuda inf-cambiar">Cambiar los formatos que pide una visita: <FaseD fase="D" texto="Sin ruta en el backend"/></p>
          </section>

          <p v-if="error" ref="error" class="dlg-error" role="alert" tabindex="-1" data-error-informe><Icono nombre="alerta"/><span>{{ error }}<template v-if="hrefOtro"> <a class="enlace" :href="hrefOtro" data-ver-otro-trabajo>Ver ese trabajo<Icono nombre="flecha"/></a></template></span></p>

          <footer class="dlg-pie">
            <button ref="cancelar" type="button" class="btn btn-sec" :disabled="lanzando" @click="cancelar">Cancelar</button>
            <button type="submit" class="btn btn-pri" :disabled="lanzando || !lanzables.length" :aria-busy="lanzando ? 'true' : null" data-lanzar-informe><Icono nombre="rayo"/>{{ lanzando ? 'Lanzando…' : 'Procesar esta visita' }}</button>
          </footer>
        </form>
      </dialog>`
  };
})();
