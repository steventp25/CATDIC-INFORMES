/* CATDIC-WEB · pestaña «Visitas y trabajos» de la obra (B3d).
   props: obra (fila de `proyectos` del tablero) · datos (respuesta de GET /api/dashboard)
   emite `actualizar` cuando hay datos nuevos: la pantalla de la obra vuelve a leer el tablero sin desmontar esta pestaña.
   Aquí viven, solo en obras de Supervisión: Procesar cola de la obra, «Subir visita» y «Conectar con Dropbox» (M3), la cola
   de la obra (ColaVisitas) y, si la ruta trae ?visita=<id>, la Mesa de Dudas de esa visita (MesaDudas, js/mesa-dudas.js). */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};

  C.componentes.PestanaVisitas = {
    props: {
      obra: { type: Object, required: true },
      datos: { type: Object, required: true }
    },
    emits: ['actualizar'],
    data: function () {
      return { dialogo: '', resultado: null, dudas: null, estadoDudas: 'cargando', nDudas: 0 };
    },
    computed: {
      ruta: function () { return C.rutas.ruta; },
      supervision: function () { return this.obra.tipo === 'Supervisión'; },
      visitas: function () {
        var id = this.obra.id;
        return (this.datos.visitas || []).filter(function (v) { return v.proyecto_id === id; });
      },
      dudasObra: function () {
        if (!Array.isArray(this.dudas)) return null;
        var id = this.obra.id;
        return this.dudas.filter(function (d) { return d.proyecto_id === id; });
      },
      seleccionada: function () { return this.ruta.consulta && this.ruta.consulta.visita ? String(this.ruta.consulta.visita) : ''; },
      visitaSel: function () {
        var s = this.seleccionada;
        return s ? (this.visitas.filter(function (v) { return v.id === s; })[0] || null) : null;
      },
      dudasSel: function () {
        var s = this.seleccionada;
        return s && this.dudasObra ? this.dudasObra.filter(function (d) { return d.visita_id === s; }) : [];
      },
      ordenesTodas: function () { return C.ordenes.lista(this.datos); },
      estadoCola: function () { return 'listo'; },
      conectada: function () { return !!this.obra.carpeta_dropbox; },
      vacioTexto: function () {
        return this.supervision
          ? 'Pulsa "Sincronizar desde Dropbox" en Inicio, o conecta la carpeta de visitas de esta obra y sube una visita.'
          : 'Las visitas se leen solo en las obras de Supervisión.';
      }
    },
    created: function () { this.leerDudas(); },
    methods: {
      leerDudas: function () {
        var self = this, n = ++this.nDudas;
        this.estadoDudas = 'cargando';
        return C.api.get('/api/dudas', { consulta: { resuelta: 'false', proyecto_id: this.obra.id } }).then(function (d) {
          if (n !== self.nDudas) return;
          self.dudas = Array.isArray(d) ? d : null; self.estadoDudas = Array.isArray(d) ? 'listo' : 'error';
        }, function () {
          if (n !== self.nDudas) return;
          self.dudas = null; self.estadoDudas = 'error';
        });
      },
      actualizar: function () { this.$emit('actualizar'); this.leerDudas(); },
      abrir: function (modo) { this.resultado = null; this.dialogo = modo; },
      cerrarDialogo: function () { this.dialogo = ''; },
      hecho: function (r) { this.dialogo = ''; this.resultado = r.resultado; this.actualizar(); },
      quitarSeleccion: function () { location.hash = C.rutas.hashObra(this.obra.id, 'visitas'); },
      textoVisita: function (v) {
        var n = v.numero !== null && v.numero !== undefined && v.numero !== '' ? 'Visita ' + v.numero : 'Visita';
        return v.nombre_carpeta ? n + ' · ' + v.nombre_carpeta : n;
      },
      categoria: function (d) { return d.categoria === 'DUDA_BLOQUEANTE' ? 'Bloqueante' : 'Duda o hallazgo'; }
    },
    template: `
      <div class="pestana-visitas">
        <section class="caja" aria-labelledby="pv-acc">
          <div class="caja-cabeza"><h2 id="pv-acc">Visitas y trabajos</h2></div>
          <template v-if="supervision">
            <div class="acc-botones pv-botones">
              <button type="button" class="btn btn-sec" data-abrir-subir @click="abrir('subir')"><Icono nombre="subir"/>Subir visita</button>
              <button type="button" class="btn btn-sec" data-abrir-dropbox @click="abrir('dropbox')"><Icono nombre="carpeta"/>{{ conectada ? 'Dropbox conectado' : 'Conectar con Dropbox' }}</button>
            </div>
            <AccionesCola :proyecto="obra.id" :con-sincronizar="false" @actualizar="actualizar"/>
          </template>
          <p v-else class="ayuda" data-no-supervision>Esta obra no es de Supervisión: Procesar cola, Subir visita y Conectar con Dropbox solo existen en las obras de Supervisión.</p>
          <ResultadoVisitas v-if="resultado" :resultado="resultado" @cerrar="resultado = null"/>
        </section>

        <MesaDudas v-if="seleccionada" :obra="obra" :datos="datos" :visita-id="seleccionada" @actualizar="actualizar"/>

        <ColaVisitas titulo="Cola de visitas de esta obra" estado="listo" :visitas="visitas" :proyectos="[obra]" :dudas="dudasObra"
          :seleccionada="seleccionada" :vacio-texto="vacioTexto">
        </ColaVisitas>

        <OrdenesObra :obra="obra" :ordenes="ordenesTodas"/>

        <FormularioVisita v-if="dialogo" :modo="dialogo" :proyecto="obra" @hecho="hecho" @cancelar="cerrarDialogo"/>
      </div>`
  };
})();
