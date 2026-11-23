/* CATDIC-WEB · «Datos de la obra» (B3b, M5 del inventario; acciones A13 y A29).
   Diálogo con los 4 grupos de datos que el plano no trae y que escribe el usuario: equivalencias E-n ↔ nivel, tipo de cada losa,
   emparejamiento de hojas y nivel de las plantas repetidas.
   props   obra (Object, obligatoria: { id, nombre })
   eventos cerrar · guardado({ tipo, guardados, dudas_cerradas })
   Los datos ya guardados se leen antes con GET /api/proyectos/{id}/datos-obra. Si esa lectura falla SE DICE (no se abre vacío en
   silencio, como hacía el tablero anterior): el diálogo muestra el error y «Reintentar», y no deja guardar sobre lo que no se leyó.
   «Guardar» (PUT …/datos-obra): cada línea no vacía se parte en el primer «=» o «:»; sin separador el valor queda vacío.
   Mensaje verde o rojo por grupo. Ningún PUT se reintenta solo y un envío en curso bloquea su botón.
   Accesible: <dialog> modal, foco atrapado, Escape cierra, el foco vuelve a quien lo abrió. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};
  var contador = 0;

  var GRUPOS = [
    { tipo: 'equivalencia_nivel', titulo: 'Equivalencias E-n ↔ nivel', ayuda: '(el plano rotula entrepisos E-1…E-n)', ejemplo: 'E-1 = SOTANO S7\nE-2 = SOTANO S6' },
    { tipo: 'losa_tipo', titulo: 'Tipo de cada losa (A, B o C)', ayuda: '(la tabla de acero en losa no dice a qué L# corresponde)', ejemplo: 'L1 = A\nL2 = B' },
    { tipo: 'hoja_par', titulo: 'Emparejamiento de hojas vectorial → sellado', ayuda: '(número de hoja del vectorial = número de hoja del sellado, o «sin pareja»)', ejemplo: '1 = 1\n9 = sin pareja' },
    { tipo: 'techo', titulo: 'Nivel de las plantas repetidas', ayuda: '(página del vectorial = nivel; solo para plantas con el mismo título en varias hojas, p. ej. dos «DE TECHO»)', ejemplo: '32 = TECHO\n33 = TECHO ASCENSOR', sinDuda: true }
  ];

  function lineas(texto) {
    return String(texto || '').split('\n').map(function (l) { return l.trim(); }).filter(Boolean).map(function (l) {
      var i = l.search(/[=:]/);
      return i < 0 ? { clave: l, valor: '' } : { clave: l.slice(0, i).trim(), valor: l.slice(i + 1).trim() };
    });
  }

  C.datosObra = { grupos: GRUPOS, lineas: lineas };

  C.componentes.DatosObra = {
    props: { obra: { type: Object, required: true } },
    emits: ['cerrar', 'guardado'],
    data: function () {
      contador++;
      var texto = {}, completo = {}, enviando = {}, mensajes = {}, errores = {};
      GRUPOS.forEach(function (g) { texto[g.tipo] = ''; completo[g.tipo] = false; enviando[g.tipo] = false; mensajes[g.tipo] = ''; errores[g.tipo] = false; });
      return { uid: 'do' + contador, grupos: GRUPOS, estado: 'cargando', mensajeLectura: '', texto: texto, completo: completo, enviando: enviando, mensajes: mensajes, errores: errores,
               abiertas: null, n: 0, cerrado: false, apertura: null };
    },
    mounted: function () {
      this.apertura = document.activeElement;
      var dlg = this.$refs.dlg;
      if (dlg && dlg.showModal) dlg.showModal(); else if (dlg) dlg.setAttribute('open', '');
      this.leer();
    },
    beforeUnmount: function () { this.devolverFoco(); },
    methods: {
      leer: function () {
        var self = this, n = ++this.n;
        this.estado = 'cargando'; this.mensajeLectura = '';
        C.api.get('/api/proyectos/' + encodeURIComponent(this.obra.id) + '/datos-obra').then(function (d) {
          if (n !== self.n) return;
          var datos = (d && d.datos) || {};
          self.grupos.forEach(function (g) {
            self.texto[g.tipo] = (Array.isArray(datos[g.tipo]) ? datos[g.tipo] : []).map(function (x) { return x.clave + ' = ' + x.valor; }).join('\n');
          });
          self.abiertas = Array.isArray(d && d.dudas_abiertas) ? d.dudas_abiertas.length : null;
          self.estado = 'listo';
          self.$nextTick(function () { var t = self.$refs.primero; if (t) (Array.isArray(t) ? t[0] : t).focus(); });
        }, function (e) {
          if (n !== self.n) return;
          self.mensajeLectura = (e && e.mensaje) || 'No se pudieron leer los datos guardados.'; self.estado = 'error';
        });
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
      cerrar: function () {
        var dlg = this.$refs.dlg;
        this.cerrado = true;
        if (dlg && dlg.open && dlg.close) dlg.close();
        this.$emit('cerrar');
      },
      alCerrar: function () { if (!this.cerrado) { this.cerrado = true; this.$emit('cerrar'); } },
      guardar: function (tipo) {
        var self = this;
        if (this.enviando[tipo] || this.estado !== 'listo') return;
        this.errores[tipo] = false; this.mensajes[tipo] = '';
        var items = lineas(this.texto[tipo]);
        this.enviando[tipo] = true;
        C.api.put('/api/proyectos/' + encodeURIComponent(this.obra.id) + '/datos-obra', { tipo: tipo, items: items, completo: !!this.completo[tipo] }).then(function (d) {
          self.enviando[tipo] = false;
          var g = d && typeof d.guardados === 'number' ? d.guardados : items.length;
          self.mensajes[tipo] = 'Guardados ' + g + ' datos como confirmados' + (d && d.dudas_cerradas ? ' · duda cerrada.' : '.');
          self.$emit('guardado', { tipo: tipo, guardados: g, dudas_cerradas: (d && d.dudas_cerradas) || 0 });
        }, function (e) {
          self.enviando[tipo] = false;
          self.errores[tipo] = true;
          self.mensajes[tipo] = (e && e.mensaje) || 'No se pudo guardar.';
        });
      }
    },
    template: `
      <dialog ref="dlg" class="dlg dlg-datos" :aria-labelledby="uid + '-t'" @cancel.prevent="cerrar" @close="alCerrar" @keydown.tab="atrapar" data-modal-datos>
        <div class="dlg-form">
          <header class="dlg-cab">
            <h2 :id="uid + '-t'">Datos de la obra · {{ obra.nombre }}</h2>
            <button type="button" class="btn btn-sec dlg-x" aria-label="Cerrar" data-cerrar-datos @click="cerrar"><Icono nombre="cerrar"/></button>
          </header>
          <p class="ayuda">El plano no trae estos datos: los escribes tú (una línea por dato, «clave = valor») y quedan confirmados con auditoría. Lo que no escribas sigue pendiente en la Mesa de Dudas.</p>

          <div v-if="estado === 'cargando'" class="cargando" aria-busy="true" aria-live="polite" data-datos-cargando><span class="sr">Cargando los datos guardados…</span><span class="hueso" style="--i:0"></span><span class="hueso" style="--i:1"></span><span class="hueso" style="--i:2"></span></div>
          <div v-else-if="estado === 'error'" class="error" role="alert" data-error-lectura-datos>
            <Icono nombre="alerta"/>
            <div><p class="error-t">No se pudieron leer los datos guardados de la obra.</p><p>{{ mensajeLectura }}</p><p>No se abre el formulario vacío para no escribir encima de lo que ya hay guardado.</p><button type="button" class="btn btn-sec" data-reintentar-datos @click="leer">Reintentar</button></div>
          </div>
          <template v-else>
            <section v-for="(g, i) in grupos" :key="g.tipo" class="dato-grupo" :aria-labelledby="uid + '-g-' + g.tipo" :data-grupo-datos="g.tipo">
              <h3 :id="uid + '-g-' + g.tipo" class="dato-t">{{ g.titulo }} <span class="ayuda dato-ayuda">{{ g.ayuda }}</span></h3>
              <textarea :ref="i === 0 ? 'primero' : null" class="campo-i dato-ta" rows="4" v-model="texto[g.tipo]" :placeholder="g.ejemplo" :aria-labelledby="uid + '-g-' + g.tipo" :data-datos="g.tipo" spellcheck="false"></textarea>
              <div class="dato-pie">
                <p v-if="g.sinDuda" class="ayuda">Las dudas de esas plantas se cierran al volver a extraer.</p>
                <label v-else class="dato-comp"><input type="checkbox" v-model="completo[g.tipo]" :data-completo="g.tipo">Ya escribí todos los de esta lista</label>
                <button type="button" class="btn btn-pri" :disabled="enviando[g.tipo]" :aria-busy="enviando[g.tipo] ? 'true' : null" :data-guardar="g.tipo" @click="guardar(g.tipo)">{{ enviando[g.tipo] ? 'Guardando…' : 'Guardar' }}</button>
              </div>
              <p v-if="mensajes[g.tipo]" class="dato-msg" :class="errores[g.tipo] ? 'es-mal' : 'es-ok'" :role="errores[g.tipo] ? 'alert' : 'status'" :data-mensaje="g.tipo"><Icono :nombre="errores[g.tipo] ? 'alerta' : 'check'"/>{{ mensajes[g.tipo] }}</p>
            </section>
          </template>
        </div>
      </dialog>`
  };
})();
