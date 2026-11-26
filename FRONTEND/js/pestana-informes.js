/* CATDIC-WEB · pestaña «Informes» de la obra (B3g).
   props: obra (fila de `proyectos` del tablero) · datos (respuesta de GET /api/dashboard)
   emite `actualizar` cuando hay datos nuevos (se lanzó un trabajo o terminó): la pantalla de la obra relee el tablero.
   Lee GET /api/proyectos/{id}/informes (los PDF que dejó el procesador, del más nuevo al más viejo; un archivo que ya no
   está en la carpeta se marca y no se oculta). «Abrir PDF» abre /api/informes/archivo?ruta=… en una pestaña nueva.
   «Hacer informe» abre FormularioInforme; al lanzar, el avance en vivo (AvanceTrabajo, el mismo de B3d) queda en esta
   pestaña y, al terminar, la lista se vuelve a leer. Con ?hacer=1 en la ruta (botón «Crear informe») el diálogo se abre solo. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};

  // Tamaño legible: 640 B · 57 KB · 1,4 MB
  function tamano(b) {
    if (typeof b !== 'number' || !isFinite(b) || b < 0) return null;
    if (b < 1024) return b.toLocaleString('es') + ' B';
    if (b < 1048576) return Math.round(b / 1024).toLocaleString('es') + ' KB';
    return (b / 1048576).toLocaleString('es', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' MB';
  }

  C.componentes.PestanaInformes = {
    props: {
      obra: { type: Object, required: true },
      datos: { type: Object, required: true }
    },
    emits: ['actualizar'],
    data: function () {
      return { estado: 'cargando', mensaje: '', informes: [], n: 0, dialogo: false, trabajoId: '', trabajoCerrado: false };
    },
    computed: {
      supervision: function () { return this.obra.tipo === 'Supervisión'; },
      visitas: function () {
        var id = this.obra.id;
        return (this.datos.visitas || []).filter(function (v) { return v.proyecto_id === id; });
      },
      estadoBloque: function () { return this.estado === 'listo' && !this.informes.length ? 'vacio' : this.estado; },
      cuenta: function () {
        var n = this.informes.length, falta = this.informes.filter(function (i) { return !i.existe; }).length;
        return C.cola.plural(n, 'informe', 'informes') + (falta ? ' · ' + falta + ' sin archivo' : '');
      },
      conTrabajo: function () { return !!this.trabajoId; }
    },
    created: function () {
      var t = C.cola.tienda.trabajo, q = C.rutas.ruta.consulta || {};
      // Un trabajo de esta obra que sigue corriendo (p. ej. tras recargar la página) se retoma aquí.
      if (t && t.id && t.estado === 'corriendo' && (!t.proyecto || t.proyecto === this.obra.id)) this.trabajoId = t.id;
      if (q.hacer && this.supervision) {
        this.dialogo = true;
        // La URL queda limpia: recargar no vuelve a abrir el diálogo.
        try { history.replaceState(null, '', location.pathname + location.search + C.rutas.hashObra(this.obra.id, 'informes')); } catch (e) { /* sin historial */ }
      }
      this.leer();
    },
    methods: {
      leer: function () {
        var self = this, n = ++this.n;
        this.estado = 'cargando'; this.mensaje = '';
        return C.api.get('/api/proyectos/' + encodeURIComponent(this.obra.id) + '/informes').then(function (d) {
          if (n !== self.n) return;
          self.informes = d && Array.isArray(d.informes) ? d.informes : [];
          self.estado = d && Array.isArray(d.informes) ? 'listo' : 'error';
          if (self.estado === 'error') self.mensaje = 'El servidor respondió algo que no se pudo leer.';
        }, function (e) {
          if (n !== self.n) return;
          self.mensaje = (e && e.mensaje) || 'No se pudo leer la lista de informes.'; self.estado = 'error';
        });
      },
      abrirDialogo: function () { this.dialogo = true; },
      cerrarDialogo: function () { this.dialogo = false; },
      lanzado: function (r) {
        this.dialogo = false; this.trabajoId = r.trabajoId; this.trabajoCerrado = false;
        this.$emit('actualizar');   // la visita pasa a «En proceso»
      },
      alTerminar: function () {
        this.trabajoCerrado = true;
        this.$emit('actualizar');
        this.leer();
      },
      cerrarAvance: function () {
        this.trabajoId = ''; this.trabajoCerrado = false;
        if (C.cola.tienda.trabajo && C.cola.tienda.trabajo.estado !== 'corriendo') C.cola.cerrarTrabajo();
      },
      href: function (i) { return '/api/informes/archivo?ruta=' + encodeURIComponent(i.ruta || ''); },
      hrefVisita: function (i) { return C.rutas.hashVisita(this.obra.id, i.visita.id); },
      fecha: function (i) { return C.formato.fechaHora(i.fecha); },
      tamano: tamano,
      pend: function (x) { return C.cola.esPendiente(x); },
      claseFila: function (i) { return { 'con-dudas': i.con_dudas, 'sin-archivo': !i.existe }; }
    },
    template: `
      <div class="pestana-informes">
        <section class="caja" aria-labelledby="pi-acc">
          <div class="caja-cabeza">
            <h2 id="pi-acc">Informes de la obra</h2>
            <p v-if="estado === 'listo' && informes.length" class="cola-cuenta num" data-informes-cuenta>{{ cuenta }}</p>
          </div>
          <div class="acc-botones pv-botones">
            <button v-if="supervision" type="button" class="btn btn-pri" data-hacer-informe :disabled="conTrabajo && !trabajoCerrado" @click="abrirDialogo"><Icono nombre="mas"/>Hacer informe</button>
            <button type="button" class="btn btn-sec" data-recargar-informes :disabled="estado === 'cargando'" @click="leer"><Icono nombre="sync"/>Actualizar la lista</button>
          </div>
          <p v-if="supervision && conTrabajo && !trabajoCerrado" class="ayuda" data-hay-trabajo>Hay un trabajo procesando; cuando termine podrás hacer otro informe.</p>
          <p v-if="!supervision" class="ayuda" data-no-supervision>Esta obra no es de Supervisión: «Hacer informe» solo existe para las visitas de las obras de Supervisión. Los formatos de Levantamiento (HV-LEV, HV-LEVEVAL, HV-LEVEST, HV-INFTEC) están disponibles más adelante.</p>
        </section>

        <section v-if="conTrabajo" class="caja" aria-labelledby="pi-trabajo" data-avance-informe>
          <div class="caja-cabeza">
            <h2 id="pi-trabajo">Avance del informe</h2>
            <button v-if="trabajoCerrado" type="button" class="btn btn-sec" data-cerrar-avance @click="cerrarAvance"><Icono nombre="cerrar"/>Cerrar el avance</button>
            <a v-else class="enlace" :href="'#/trabajo/' + encodeURIComponent(trabajoId)">Abrir en pantalla completa<Icono nombre="flecha"/></a>
          </div>
          <AvanceTrabajo :trabajo-id="trabajoId" :key="trabajoId" @terminado="alTerminar"/>
        </section>

        <section class="caja inf-caja" aria-labelledby="pi-lista" data-informes>
          <div class="caja-cabeza"><h2 id="pi-lista">PDF generados</h2></div>
          <Bloque :estado="estadoBloque" :huesos="4" vacio-titulo="Esta obra todavía no tiene informes generados"
            vacio-texto="Cuando el sistema procese una visita de esta obra, sus PDF aparecerán aquí."
            error-titulo="No se pudo leer la lista de informes." :error-mensaje="mensaje" @reintentar="leer">
            <div class="inf" role="table" aria-label="Informes de la obra" :aria-rowcount="informes.length + 1">
              <div class="inf-enc" role="row">
                <span role="columnheader">Formato</span><span role="columnheader">Visita</span><span role="columnheader">Fecha</span>
                <span role="columnheader">Archivo</span><span role="columnheader">Estado</span>
              </div>
              <div v-for="(i, k) in informes" :key="(i.trabajo_id || '') + '-' + k" class="inf-f" :class="claseFila(i)" role="row" data-informe>
                <div class="inf-c inf-formato" role="cell"><span class="cola-r" aria-hidden="true">Formato</span><b class="num" v-if="!pend(i.formato)">{{ i.formato }}</b><Pendiente v-else/></div>
                <div class="inf-c inf-visita" role="cell">
                  <span class="cola-r" aria-hidden="true">Visita</span>
                  <a class="cola-enlace" :href="hrefVisita(i)">
                    <b class="num" v-if="!pend(i.visita.numero)">N.º {{ i.visita.numero }}</b><Pendiente v-else>N.º pendiente de verificar</Pendiente>
                    <span class="inf-carpeta"><template v-if="pend(i.visita.nombre_carpeta)"> <Pendiente>carpeta pendiente de verificar</Pendiente></template><template v-else> · {{ i.visita.nombre_carpeta }}</template></span>
                    <span class="sr"> · ver la visita</span>
                  </a>
                </div>
                <div class="inf-c inf-fecha" role="cell"><span class="cola-r" aria-hidden="true">Fecha</span><span v-if="fecha(i)" class="num">{{ fecha(i) }}</span><Pendiente v-else/></div>
                <div class="inf-c inf-archivo" role="cell">
                  <span class="cola-r" aria-hidden="true">Archivo</span>
                  <span class="inf-archivo-c">
                    <span v-if="i.nombre" class="inf-nombre" :title="i.nombre">{{ i.nombre }}</span><Pendiente v-else>nombre pendiente de verificar</Pendiente>
                    <span class="inf-meta"><span class="num">Versión {{ i.version }}</span> · <span v-if="tamano(i.bytes)" class="num">{{ tamano(i.bytes) }}</span><Pendiente v-else>tamaño pendiente de verificar</Pendiente></span>
                  </span>
                </div>
                <div class="inf-c inf-estado" role="cell">
                  <span v-if="i.con_dudas" class="est est-dudas" data-con-dudas><Icono nombre="pregunta"/>Con dudas</span>
                  <p v-if="!i.existe" class="inf-falta" data-archivo-falta><Icono nombre="alerta"/>El archivo ya no está en la carpeta</p>
                  <a v-else class="btn btn-sec inf-abrir" :href="href(i)" target="_blank" rel="noopener" data-abrir-pdf><Icono nombre="externo"/>Abrir PDF<span class="sr"> {{ i.nombre }} (se abre en una pestaña nueva)</span></a>
                </div>
              </div>
            </div>
          </Bloque>
        </section>

        <FormularioInforme v-if="dialogo" :obra="obra" :visitas="visitas" @lanzado="lanzado" @cancelar="cerrarDialogo"/>
      </div>`
  };
})();
