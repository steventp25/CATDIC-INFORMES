/* CATDIC-WEB · FormularioVisita (B3d): diálogo «Subir visita» y «Conectar con Dropbox» (M3, A31–A33, Z4).
   Props:  modo = 'subir' | 'dropbox'   ·   proyecto = { id, nombre, carpeta_dropbox }
   Emite:  hecho({ modo, proyecto, resultado })  ·  cancelar()
   resultado = { titulo, resumen, avisos[], visitas[{ id, proyectoId, numero, nombre_carpeta, estado, dudas, lector }] } (lo que pinta Z4).
   Subir: POST /api/proyectos/{id}/visitas (multipart). Conectar: POST /api/proyectos/{id}/dropbox (JSON). Ningún POST se reintenta solo.
   Accesible como FormularioPlanos: <dialog> modal (foco atrapado), Escape cierra, el foco vuelve a quien lo abrió. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};
  var contador = 0;
  var SUBRUTA_VISITAS = '\\LEVANTAMIENTO\\VISITA A OBRA';
  var TIEMPO_LARGO = 180000;   // el servidor guarda, lee el PDF y corre el lector antes de responder

  function textoLector(l) {
    if (!l) return '';
    if (l.ok) return 'lector: ' + l.grupos + ' elementos en ' + l.paginas + ' páginas';
    if (l.omitida) return 'lector: no se abre (' + l.error + ')';
    return 'lector: ' + l.error;
  }
  function fila(v, dudas, lector, proyectoId) {
    return { id: v.id, proyectoId: proyectoId, numero: v.numero, nombre_carpeta: v.nombre_carpeta, estado: v.estado,
             dudas: Array.isArray(dudas) ? dudas.length : 0, lector: textoLector(lector) };
  }

  C.componentes.FormularioVisita = {
    props: {
      modo: { type: String, default: 'subir' },
      proyecto: { type: Object, required: true }
    },
    emits: ['hecho', 'cancelar'],
    data: function () {
      contador++;
      var p = this.proyecto;
      return {
        uid: 'fv' + contador, pdf: null, fotos: [], numero: '', fecha: '', elementos: '', nivel: '', clase: '',
        carpeta: p.carpeta_dropbox ? p.carpeta_dropbox + SUBRUTA_VISITAS : '',
        enviando: false, error: '', cerrado: false, apertura: null
      };
    },
    computed: {
      subir: function () { return this.modo === 'subir'; },
      titulo: function () { return (this.subir ? 'Subir visita' : 'Conectar con Dropbox') + ' · ' + this.proyecto.nombre; },
      textoEnviar: function () {
        if (this.enviando) return this.subir ? 'Subiendo y leyendo la visita…' : 'Sincronizando y leyendo las visitas…';
        return this.subir ? 'Subir visita' : 'Conectar y sincronizar';
      }
    },
    mounted: function () {
      this.apertura = document.activeElement;
      var dlg = this.$refs.dlg;
      if (dlg && dlg.showModal) dlg.showModal(); else if (dlg) dlg.setAttribute('open', '');
      var primero = this.$refs[this.subir ? 'pdf' : 'carpeta'];
      if (primero) primero.focus();
    },
    beforeUnmount: function () { this.devolverFoco(); },
    methods: {
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
        if (this.enviando) return;
        this.cerrarDialogo();
        this.$emit('cancelar');
      },
      alCerrar: function () { if (this.cerrado) return; this.cerrado = true; this.$emit('cancelar'); },
      fallo: function (mensaje, ref) {
        var self = this;
        this.error = mensaje;
        this.$nextTick(function () { var el = self.$refs[ref]; if (el && el.focus) el.focus(); });
      },
      elegirPdf: function (ev) { this.pdf = (ev.target.files && ev.target.files[0]) || null; },
      elegirFotos: function (ev) { this.fotos = [].slice.call(ev.target.files || []); },
      enviar: function () {
        var self = this, p = this.proyecto, ruta;
        if (this.enviando) return;
        this.error = '';
        var peticion;
        if (this.subir) {
          if (!this.pdf) { this.fallo('Elige el PDF de la visita.', 'pdf'); return; }
          if (!/^\d{1,3}$/.test(String(this.numero).trim())) { this.fallo('El número de visita debe ser un entero (p. ej. 17).', 'numero'); return; }
          if (!this.elementos.trim() || !this.nivel.trim()) { this.fallo('Escribe los elementos y el nivel de la visita.', this.elementos.trim() ? 'nivel' : 'elementos'); return; }
          if (this.fecha.trim() && !/^\d{2}\/\d{2}\/\d{4}$/.test(this.fecha.trim())) { this.fallo('La fecha debe ser DD/MM/AAAA (p. ej. 28/09/2026).', 'fecha'); return; }
          var f = new FormData();
          f.append('pdf', this.pdf);
          this.fotos.forEach(function (foto) { f.append('fotos', foto); });
          ['numero', 'elementos', 'nivel', 'fecha', 'clase'].forEach(function (c) { f.append(c, String(self[c]).trim()); });
          ruta = '/api/proyectos/' + encodeURIComponent(p.id) + '/visitas';
          peticion = C.api.enviarFormulario(ruta, f, { tiempo: TIEMPO_LARGO });
        } else {
          if (!this.carpeta.trim()) { this.fallo('Escribe la ruta de la carpeta LEVANTAMIENTO\\VISITA A OBRA.', 'carpeta'); return; }
          ruta = '/api/proyectos/' + encodeURIComponent(p.id) + '/dropbox';
          peticion = C.api.post(ruta, { carpeta_visitas: this.carpeta.trim() }, { tiempo: TIEMPO_LARGO });
        }
        this.enviando = true;
        peticion.then(function (d) {
          var resultado;
          if (self.subir) {
            var v = d.visita;
            resultado = { titulo: p.nombre + ': visita subida', avisos: [],
              resumen: 'Guardada en ' + v.ruta_carpeta + ' (' + (v.archivos || []).length + ' archivo(s) con sha256).',
              visitas: [fila(v, d.dudas, d.lector, p.id)] };
          } else {
            var s = d.sync || {}, omitidas = s.omitidas || [], desaparecidas = s.desaparecidas || [];
            resultado = { titulo: p.nombre + ': conectada con ' + d.carpeta_visitas, avisos: s.avisos || [],
              resumen: s.visitas_nuevas + ' visitas nuevas · ' + s.actualizadas + ' actualizadas · ' + s.sin_cambios + ' sin cambios · ' +
                s.con_dudas + ' con dudas · ' + s.procesadas + ' procesadas' +
                (omitidas.length ? ' · ' + omitidas.length + ' omitidas (sin número legible)' : '') +
                (desaparecidas.length ? ' · ' + desaparecidas.length + ' que ya no están en la carpeta' : ''),
              visitas: (d.visitas_nuevas || []).map(function (x) { return fila(x, x.dudas, x.lector, p.id); }) };
          }
          self.enviando = false;
          self.cerrarDialogo();
          self.$emit('hecho', { modo: self.modo, proyecto: p, resultado: resultado });
        }, function (e) {
          self.enviando = false;
          self.fallo((e && e.mensaje) || 'No se pudo completar la operación.', 'error');
        });
      }
    },
    template: `
      <dialog ref="dlg" class="dlg" :aria-labelledby="uid + '-t'" data-modal-visita @cancel.prevent="cancelar" @close="alCerrar" @keydown.tab="atrapar">
        <form class="dlg-form" @submit.prevent="enviar" novalidate>
          <header class="dlg-cab">
            <h2 :id="uid + '-t'" class="dlg-titulo"><Icono :nombre="subir ? 'subir' : 'carpeta'"/><span class="nombre-largo" :title="titulo">{{ titulo }}</span></h2>
            <button type="button" class="btn btn-sec dlg-x" aria-label="Cerrar" :disabled="enviando" @click="cancelar"><Icono nombre="cerrar"/></button>
          </header>

          <template v-if="subir">
            <p class="ayuda">La visita se guarda en la carpeta local de la obra (nunca en Dropbox), sin sobrescribir nada. Si no das la fecha o la clase, se leen del nombre del PDF; si tampoco están, quedan «pendiente de verificar» en la Mesa de Dudas.</p>
            <div class="campos">
              <label class="campo ancho"><span>PDF de la visita *</span>
                <input ref="pdf" type="file" accept="application/pdf,.pdf" data-visita-pdf @change="elegirPdf"></label>
              <label class="campo ancho"><span>Fotos sueltas (opcional, JPG o PNG)</span>
                <input type="file" accept="image/jpeg,image/png,.jpg,.jpeg,.png" multiple data-visita-fotos @change="elegirFotos"></label>
              <label class="campo"><span>Número de visita *</span>
                <input ref="numero" v-model="numero" type="text" inputmode="numeric" placeholder="17" autocomplete="off" data-visita-campo="numero"></label>
              <label class="campo"><span>Fecha (DD/MM/AAAA)</span>
                <input ref="fecha" v-model="fecha" type="text" placeholder="28/09/2026" autocomplete="off" data-visita-campo="fecha"></label>
              <label class="campo"><span>Elementos *</span>
                <input ref="elementos" v-model="elementos" type="text" placeholder="VERTICALES" autocomplete="off" data-visita-campo="elementos"></label>
              <label class="campo"><span>Nivel *</span>
                <input ref="nivel" v-model="nivel" type="text" placeholder="S-4" autocomplete="off" data-visita-campo="nivel"></label>
              <label class="campo ancho"><span>Clase</span>
                <select v-model="clase" data-visita-campo="clase">
                  <option value="">No la indico (se lee del PDF o queda pendiente)</option><option>Parcial</option><option>Completivo</option>
                </select>
                <span class="ayuda">Mixta no se acepta: si la visita tiene partes Parcial y Completivo, súbela como dos visitas.</span></label>
            </div>
          </template>
          <template v-else>
            <p class="ayuda">Indica la carpeta <b>LEVANTAMIENTO\\VISITA A OBRA</b> de esta obra dentro de Dropbox. Se valida, se guarda en la obra y se sincronizan sus visitas. Dropbox solo se lee: no se escribe ni se mueve nada ahí.</p>
            <label class="campo ancho"><span>Carpeta de visitas *</span>
              <input ref="carpeta" v-model="carpeta" type="text" class="mono" autocomplete="off" data-visita-carpeta placeholder="C:\\Users\\…\\CATDIC Dropbox\\SUPERVISION\\EN CURSO\\<OBRA>\\LEVANTAMIENTO\\VISITA A OBRA"></label>
          </template>

          <p v-if="error" ref="error" class="dlg-error" role="alert" tabindex="-1" data-error-visita><Icono nombre="alerta"/>{{ error }}</p>

          <footer class="dlg-pie">
            <button type="button" class="btn btn-sec" :disabled="enviando" @click="cancelar">Cancelar</button>
            <button type="submit" class="btn btn-pri" :disabled="enviando" :aria-busy="enviando ? 'true' : null" data-enviar-visita>{{ textoEnviar }}</button>
          </footer>
        </form>
      </dialog>`
  };
})();
