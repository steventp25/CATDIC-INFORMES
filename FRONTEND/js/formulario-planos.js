/* CATDIC-WEB · FormularioPlanos (B3a): diálogo para «Nueva obra» (M2 modo nueva, A28) y, desde B3b, «Cambiar plano».
   Props:  modo = 'nueva' | 'cambiar'   ·   proyecto = { id, nombre } (modo cambiar)   ·   titulo (opcional)
   Emite:  hecho({ modo, proyecto: {id, nombre}, plano })   ·   cancelar({ proyectoCreado })
   Flujo (modo nueva): POST /api/proyectos y después POST /api/proyectos/{id}/planos (multipart). Si la subida falla
   tras crear la obra, el diálogo sigue abierto, los campos de la obra quedan fijos y «reintentar» solo repite la subida.
   Ningún POST se reintenta solo. Accesible: <dialog> modal (foco atrapado), Escape cierra, el foco vuelve a quien lo abrió. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};
  var contador = 0;

  // [clave, etiqueta, ancho completo, marcador]
  var CAMPOS = [
    ['nombre', 'Nombre de la obra *', true, ''],
    ['tipo', 'Tipo', false, ''],
    ['cliente', 'Cliente', false, ''],
    ['no_solicitud', 'N.º de solicitud', false, ''],
    ['no_licencia', 'N.º de licencia', false, ''],
    ['residente_obra', 'Residente de obra (nombre y colegiatura)', false, ''],
    ['supervisor', 'Supervisor', false, ''],
    ['direccion_obra', 'Dirección de la obra', true, ''],
    ['provincia', 'Provincia', false, ''],
    ['sector', 'Sector', false, ''],
    ['inicio_obra', 'Inicio de obra (DD/MM/AAAA)', false, '01/03/2026']
  ];

  C.componentes.FormularioPlanos = {
    props: {
      modo: { type: String, default: 'nueva' },
      proyecto: { type: Object, default: null },
      titulo: { type: String, default: '' }
    },
    emits: ['hecho', 'cancelar'],
    data: function () {
      contador++;
      return {
        uid: 'fp' + contador, campos: CAMPOS,
        datos: { nombre: '', tipo: 'Supervisión', cliente: '', no_solicitud: '', no_licencia: '', residente_obra: '', supervisor: '',
                 direccion_obra: '', provincia: '', sector: '', inicio_obra: '' },
        etiqueta_revision: '', fecha_plano: '', vectorial: null, sellado: null, certifico: false,
        proyectoId: this.proyecto ? this.proyecto.id : null, nombreObra: this.proyecto ? this.proyecto.nombre : '',
        enviando: false, error: '', cerrado: false, apertura: null
      };
    },
    computed: {
      nueva: function () { return this.modo === 'nueva'; },
      tituloDialogo: function () { return this.titulo || (this.nueva ? 'Nueva obra' : 'Cambiar plano'); },
      textoEnviar: function () {
        if (this.enviando) return 'Subiendo…';
        if (!this.nueva) return 'Subir plano nuevo';
        return this.proyectoId ? 'Reintentar la subida de planos' : 'Crear obra y subir planos';
      },
      obraFija: function () { return !!this.proyectoId && this.nueva; }
    },
    mounted: function () {
      this.apertura = document.activeElement;
      var dlg = this.$refs.dlg;
      if (dlg && dlg.showModal) dlg.showModal(); else if (dlg) dlg.setAttribute('open', '');
      var primero = this.ref(this.nueva ? 'nombre' : 'vectorial');
      if (primero) primero.focus();
    },
    beforeUnmount: function () { this.devolverFoco(); },
    methods: {
      // El <dialog> modal deja inerte el resto de la página; además el Tab da la vuelta dentro del diálogo en vez de salir al navegador.
      atrapar: function (ev) {
        var dlg = this.$refs.dlg; if (!dlg) return;
        var f = [].slice.call(dlg.querySelectorAll("a[href], button, input, select, textarea, [tabindex]")).filter(function (e) { return !e.disabled && e.tabIndex >= 0 && e.offsetParent !== null; });
        if (!f.length) return;
        var primero = f[0], ultimo = f[f.length - 1];
        if (ev.shiftKey && document.activeElement === primero) { ev.preventDefault(); ultimo.focus(); }
        else if (!ev.shiftKey && document.activeElement === ultimo) { ev.preventDefault(); primero.focus(); }
      },
      // Los ref dentro de v-for llegan como lista.
      ref: function (n) { var r = this.$refs[n]; return Array.isArray(r) ? r[0] : r; },
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
        this.$emit('cancelar', { proyectoCreado: this.nueva && this.proyectoId ? { id: this.proyectoId, nombre: this.nombreObra } : null });
      },
      // El diálogo se cerró por su cuenta (Escape forzado): se avisa igual.
      alCerrar: function () {
        if (this.cerrado) return;
        this.cerrado = true;
        this.$emit('cancelar', { proyectoCreado: this.nueva && this.proyectoId ? { id: this.proyectoId, nombre: this.nombreObra } : null });
      },
      fallo: function (mensaje, ref) {
        this.error = mensaje;
        var self = this;
        this.$nextTick(function () { var el = self.ref(ref); if (el && el.focus) el.focus(); });
      },
      elegir: function (cual, ev) { this[cual] = (ev.target.files && ev.target.files[0]) || null; },
      enviar: function () {
        var self = this;
        if (this.enviando) return;
        this.error = '';
        if (this.nueva && !this.proyectoId && !this.datos.nombre.trim()) { this.fallo('Escribe el nombre de la obra.', 'nombre'); return; }
        if (!this.vectorial || !this.sellado) { this.fallo('Elige los dos archivos: el vectorial y el sellado.', this.vectorial ? 'sellado' : 'vectorial'); return; }
        if (!this.certifico) { this.fallo('Marca la casilla: certifico que el vectorial corresponde a la versión sellada.', 'certifico'); return; }
        this.enviando = true;

        var paso1 = Promise.resolve();
        if (this.nueva && !this.proyectoId) {
          var cuerpo = {};
          Object.keys(this.datos).forEach(function (k) { var v = String(self.datos[k]).trim(); if (v !== '') cuerpo[k] = v; });
          paso1 = C.api.post('/api/proyectos', cuerpo).then(function (r) {
            var creada = r && r.proyecto;
            if (!creada || !creada.id) throw { estado: 0, mensaje: 'El servidor no devolvió la obra creada.' };
            self.proyectoId = creada.id;   // si la subida falla, la obra ya existe: se reintenta solo la subida
            self.nombreObra = creada.nombre;
          });
        }
        paso1.then(function () {
          var f = new FormData();
          f.append('vectorial', self.vectorial);
          f.append('sellado', self.sellado);
          f.append('certifico', 'true');
          f.append('etiqueta_revision', self.etiqueta_revision || '');
          f.append('fecha_plano', self.fecha_plano || '');
          return C.api.enviarFormulario('/api/proyectos/' + encodeURIComponent(self.proyectoId) + '/planos', f).then(function (r) {
            return r && r.plano;
          }, function (e) {
            e.enSubida = true; throw e;
          });
        }).then(function (plano) {
          self.enviando = false;
          self.cerrarDialogo();
          self.$emit('hecho', { modo: self.modo, proyecto: { id: self.proyectoId, nombre: self.nombreObra }, plano: plano || {} });
        }, function (e) {
          self.enviando = false;
          var msg = (e && e.mensaje) || 'No se pudo completar la operación.';
          if (self.nueva && e && e.enSubida) msg = 'La obra se creó, pero los planos no se subieron: ' + msg;
          self.fallo(msg, 'error');
        });
      }
    },
    template: `
      <dialog ref="dlg" class="dlg" :aria-labelledby="uid + '-t'" @cancel.prevent="cancelar" @close="alCerrar" @keydown.tab="atrapar">
        <form class="dlg-form" @submit.prevent="enviar" novalidate>
          <header class="dlg-cab">
            <h2 :id="uid + '-t'">{{ tituloDialogo }}</h2>
            <button type="button" class="btn btn-sec dlg-x" aria-label="Cerrar" :disabled="enviando" @click="cancelar"><Icono nombre="cerrar"/></button>
          </header>

          <div v-if="nueva" class="campos">
            <label v-for="c in campos" :key="c[0]" class="campo" :class="{ ancho: c[2] }">
              <span>{{ c[1] }}</span>
              <select v-if="c[0] === 'tipo'" v-model="datos.tipo" :disabled="obraFija">
                <option>Supervisión</option><option>Levantamiento</option>
              </select>
              <input v-else :ref="c[0] === 'nombre' ? 'nombre' : null" type="text" v-model="datos[c[0]]" :placeholder="c[3]" :disabled="obraFija" autocomplete="off">
            </label>
          </div>
          <p v-else class="dlg-obra">Obra: <strong>{{ nombreObra }}</strong>. El plano nuevo queda vigente; el anterior pasa al histórico y los elementos ya extraídos de él se marcan «plano cambiado: revisar».</p>

          <div class="campos campos-planos">
            <label class="campo"><span>Plano VECTORIAL (PDF, fuente de lectura) *</span>
              <input ref="vectorial" type="file" accept="application/pdf,.pdf" @change="elegir('vectorial', $event)"></label>
            <label class="campo"><span>Plano SELLADO (PDF, referencia legal) *</span>
              <input ref="sellado" type="file" accept="application/pdf,.pdf" @change="elegir('sellado', $event)"></label>
            <label class="campo"><span>Revisión (texto libre)</span>
              <input type="text" v-model="etiqueta_revision" autocomplete="off"></label>
            <label class="campo"><span>Fecha del plano (DD/MM/AAAA)</span>
              <input type="text" v-model="fecha_plano" placeholder="10/03/2026" autocomplete="off"></label>
          </div>

          <label class="certifico">
            <input ref="certifico" type="checkbox" v-model="certifico">
            <span>Certifico que el vectorial corresponde a la versión sellada <span class="ayuda">(queda registrado con tu usuario y la fecha)</span></span>
          </label>

          <p v-if="error" ref="error" class="dlg-error" role="alert" tabindex="-1"><Icono nombre="alerta"/>{{ error }}</p>

          <footer class="dlg-pie">
            <button type="button" class="btn btn-sec" :disabled="enviando" @click="cancelar">Cancelar</button>
            <button type="submit" class="btn btn-pri" :disabled="enviando" :aria-busy="enviando ? 'true' : null">{{ textoEnviar }}</button>
          </footer>
        </form>
      </dialog>`
  };
})();
