/* CATDIC-WEB · acciones sobre la cola (B3d): «Procesar cola» con su seguimiento (A3, A5, A9, Z3), «Sincronizar desde Dropbox»
   (A2, A7, A8, Z5, Z8) y el resultado de subir una visita o conectar Dropbox (Z4, A6).
   `AccionesCola` se usa en Inicio, en la Bandeja y en «Visitas y trabajos» de cada obra (con `proyecto`, solo esa obra).
   Ningún POST se reintenta solo. El seguimiento se cancela al salir de la pantalla y se retoma al volver (C.cola.tienda). */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};
  var RE_TRABAJO = /trab-\d{8}-\d{6}-[0-9a-f]{6}/;
  var TIEMPO_SYNC = 180000;   // leer Dropbox y las visitas puede tardar más que los 60 s de una escritura normal

  /* Z8: resultado de la sincronización. */
  C.componentes.ResultadoSync = {
    props: { resultado: { type: Object, required: true } },
    emits: ['cerrar'],
    methods: {
      lista: function (x) { return Array.isArray(x) ? x : []; },
      hrefVisita: function (p, d) { return d && d.visita_id ? C.rutas.hashVisita(p.id, d.visita_id) : ''; },
      hrefMesa: function (p) { return this.hrefVisita(p, this.lista(p.dudas_creadas)[0]); },
      contadores: function (p) {
        var n = function (v) { return typeof v === 'number' ? v : null; };
        var sellados = this.lista(p.planos_sellados);
        return [
          { e: 'Nuevas', v: n(p.visitas_nuevas) }, { e: 'Actualizadas', v: n(p.actualizadas) }, { e: 'Sin cambios', v: n(p.sin_cambios) },
          { e: 'Con dudas', v: n(p.con_dudas), alerta: p.con_dudas > 0 }, { e: 'Procesadas', v: n(p.procesadas) },
          { e: 'Planos sellados', v: sellados.length, titulo: sellados.join('\n') },
          { e: 'Dudas nuevas', v: this.lista(p.dudas_creadas).length, alerta: this.lista(p.dudas_creadas).length > 0 }
        ];
      },
      layoutOk: function (l) { return l === 'supervision 5.1'; },
      layoutPend: function (l) { return l === 'pendiente de verificar' || l === null || l === undefined || l === ''; }
    },
    template: `
      <section class="panel p-info" aria-labelledby="sync-t" data-resultado-sync>
        <div class="panel-cab">
          <h3 id="sync-t" class="panel-t"><Icono nombre="sync"/>Resultado de la sincronización</h3>
          <span class="panel-hora num">{{ resultado.hora }}</span>
          <button type="button" class="btn btn-sec panel-x" aria-label="Cerrar el resultado de la sincronización" @click="$emit('cerrar')"><Icono nombre="cerrar"/></button>
        </div>
        <p v-if="!resultado.proyectos.length" class="ayuda">El servidor no devolvió ninguna obra para sincronizar.</p>
        <div v-for="p in resultado.proyectos" :key="p.id" class="sync-obra" :data-sync-obra="p.id">
          <div class="sync-cab">
            <h4 class="sync-nombre">{{ p.nombre }}</h4>
            <Pendiente v-if="layoutPend(p.layout)">layout pendiente de verificar</Pendiente>
            <span v-else class="etq" :class="{ 'etq-acento': layoutOk(p.layout) }">{{ p.layout }}</span>
          </div>
          <dl class="cajetin sync-cont">
            <div v-for="c in contadores(p)" :key="c.e" :class="{ 'cont-alerta': c.alerta }" :title="c.titulo || null">
              <dt>{{ c.e }}</dt><dd><Pendiente v-if="c.v === null"/><template v-else>{{ c.v }}</template></dd>
            </div>
          </dl>
          <details v-if="lista(p.avisos).length" class="sync-lista" :open="lista(p.avisos).length <= 5">
            <summary>{{ lista(p.avisos).length }} {{ lista(p.avisos).length === 1 ? 'aviso' : 'avisos' }} del sincronizador</summary>
            <ul><li v-for="(a, i) in lista(p.avisos)" :key="i"><Icono nombre="info"/>{{ a }}</li></ul>
          </details>
          <details v-if="lista(p.desaparecidas).length" class="sync-lista sync-mal" :open="lista(p.desaparecidas).length <= 5">
            <summary>{{ lista(p.desaparecidas).length }} {{ lista(p.desaparecidas).length === 1 ? 'carpeta' : 'carpetas' }} que ya no están en Dropbox</summary>
            <ul><li v-for="d in lista(p.desaparecidas)" :key="d.id"><Icono nombre="carpeta"/>Carpeta ya no encontrada en Dropbox: {{ d.nombre_carpeta }} <span class="ayuda">({{ d.estado }})</span></li></ul>
          </details>
          <details v-if="lista(p.omitidas).length" class="sync-lista" :open="lista(p.omitidas).length <= 5">
            <summary>{{ lista(p.omitidas).length }} {{ lista(p.omitidas).length === 1 ? 'carpeta omitida' : 'carpetas omitidas' }}</summary>
            <ul><li v-for="(o, i) in lista(p.omitidas)" :key="i"><Icono nombre="carpeta"/>Omitida: {{ o.nombre_carpeta }} — {{ o.motivo }}</li></ul>
          </details>
          <p v-if="lista(p.dudas_creadas).length && hrefVisita(p, lista(p.dudas_creadas)[0])" class="sync-mesa"><Icono nombre="pregunta"/><a class="enlace" :href="hrefMesa(p)" data-abrir-mesa-sync>{{ lista(p.dudas_creadas).length }} {{ lista(p.dudas_creadas).length === 1 ? 'duda nueva' : 'dudas nuevas' }} · Abrir la Mesa de Dudas</a></p>
          <details v-if="lista(p.dudas_creadas).length" class="sync-lista sync-dudas" :open="lista(p.dudas_creadas).length <= 5">
            <summary>{{ lista(p.dudas_creadas).length }} {{ lista(p.dudas_creadas).length === 1 ? 'duda creada' : 'dudas creadas' }}</summary>
            <ul><li v-for="(d, i) in lista(p.dudas_creadas)" :key="i"><Icono nombre="pregunta"/>
              <a v-if="hrefVisita(p, d)" :href="hrefVisita(p, d)">{{ d.visita_id }}</a><template v-else>{{ d.visita_id }}</template>
              · {{ d.campo_afectado }}: {{ d.descripcion_pregunta }}</li></ul>
          </details>
        </div>
      </section>`
  };

  /* Z4: resultado de subir una visita o conectar Dropbox. */
  C.componentes.ResultadoVisitas = {
    props: { resultado: { type: Object, required: true } },
    emits: ['cerrar'],
    methods: {
      claseEstado: function (e) { return C.cola.claseEstado(e); },
      hrefVisita: function (v) { return C.rutas.hashVisita(v.proyectoId, v.id); }
    },
    template: `
      <section class="panel p-ok" aria-labelledby="resv-t" data-resultado-visitas>
        <div class="panel-cab">
          <h3 id="resv-t" class="panel-t"><Icono nombre="check"/>{{ resultado.titulo }}</h3>
          <button type="button" class="btn btn-sec panel-x" aria-label="Cerrar el resultado" @click="$emit('cerrar')"><Icono nombre="cerrar"/></button>
        </div>
        <p v-if="resultado.resumen" class="panel-d">{{ resultado.resumen }}</p>
        <p v-if="!resultado.visitas.length" class="panel-d">No hay visitas nuevas.</p>
        <ul v-else class="res-visitas">
          <li v-for="v in resultado.visitas" :key="v.id" :data-visita-nueva="v.id">
            <b class="num">#{{ v.numero }}</b>
            <span class="res-carpeta">{{ v.nombre_carpeta }}</span>
            <span class="est" :class="claseEstado(v.estado)"><Icono v-if="v.estado === 'Con dudas'" nombre="pregunta"/>{{ v.estado }}</span>
            <span v-if="v.lector" class="ayuda">{{ v.lector }}</span>
            <a v-if="v.dudas > 0" class="enlace" :href="hrefVisita(v)" :data-abrir-dudas-visita="v.id">{{ v.dudas }} {{ v.dudas === 1 ? 'duda nueva' : 'dudas nuevas' }} · Abrir la Mesa de Dudas<Icono nombre="flecha"/></a>
          </li>
        </ul>
        <details v-if="resultado.avisos.length" class="sync-lista" :open="resultado.avisos.length <= 5">
          <summary>{{ resultado.avisos.length }} {{ resultado.avisos.length === 1 ? 'aviso' : 'avisos' }} del sincronizador</summary>
          <ul><li v-for="(a, i) in resultado.avisos" :key="i"><Icono nombre="info"/>{{ a }}</li></ul>
        </details>
      </section>`
  };

  /* Botones y paneles de Procesar cola y Sincronizar.
     props: proyecto ('' = todas las obras) · sincronizar / procesar (mostrar el botón)
     emite `actualizar` cuando hay datos nuevos (terminó un trabajo o una sincronización): la pantalla recarga tablero y dudas. */
  C.componentes.AccionesCola = {
    props: {
      proyecto: { type: String, default: '' },
      conSincronizar: { type: Boolean, default: true },
      conProcesar: { type: Boolean, default: true }
    },
    emits: ['actualizar'],
    data: function () {
      return { lanzando: false, errorLanzar: null, sincronizando: false, errorSync: '', resumenSync: null, seg: null };
    },
    computed: {
      trabajo: function () { return C.cola.tienda.trabajo; },
      corriendo: function () { return !!this.trabajo && this.trabajo.estado === 'corriendo'; },
      ocupado: function () { return this.lanzando || this.corriendo; },
      // Un trabajo en marcha se ve en cualquier pantalla (el cerrojo del servidor es uno solo); uno terminado, solo donde le toca.
      verTrabajo: function () {
        var t = this.trabajo;
        return !!t && (t.estado === 'corriendo' || !this.proyecto || !t.proyecto || t.proyecto === this.proyecto);
      },
      claseTrabajo: function () {
        var e = this.trabajo && this.trabajo.estado;
        return e === 'terminado' ? 'p-ok' : (e === 'corriendo' ? 'p-corre' : 'p-mal');
      },
      iconoTrabajo: function () {
        var e = this.trabajo && this.trabajo.estado;
        return e === 'terminado' ? 'check' : (e === 'corriendo' ? 'reloj' : 'alerta');
      },
      hrefTrabajo: function () { return this.trabajo && this.trabajo.id ? C.rutas.hashTrabajo(this.trabajo.id) : ''; },
      hrefOtro: function () { return this.errorLanzar && this.errorLanzar.trabajoId ? C.rutas.hashTrabajo(this.errorLanzar.trabajoId) : ''; }
    },
    mounted: function () { if (this.corriendo && this.trabajo.id) this.seguir(); },
    beforeUnmount: function () { this.parar(); },
    methods: {
      parar: function () { if (this.seg) { this.seg.cancelar(); this.seg = null; } },
      procesar: function () {
        var self = this, proyecto = this.proyecto;
        if (this.ocupado) return;
        this.errorLanzar = null; this.lanzando = true;
        C.api.post('/api/visitas/procesar-cola', undefined, { consulta: { proyecto_id: proyecto } }).then(function (d) {
          self.lanzando = false;
          if (!d || !d.trabajo || !d.trabajo.id) {   // nada que procesar: se muestra el mensaje del servidor
            C.cola.fijarTrabajo({ id: '', estado: 'terminado', mensaje: (d && d.mensaje) || 'No hay visitas Sin procesar ni En cola.', proyecto: proyecto });
            return;
          }
          C.cola.fijarTrabajo({ id: d.trabajo.id, estado: 'corriendo', mensaje: d.mensaje || 'Trabajo lanzado.', proyecto: proyecto });
          self.seguir();
        }, function (e) {
          self.lanzando = false;
          var m = RE_TRABAJO.exec(e.mensaje || '');
          self.errorLanzar = { mensaje: e.mensaje, estado: e.estado, trabajoId: m ? m[0] : '' };
        });
      },
      seguir: function () {
        var self = this, t0 = this.trabajo, id = t0.id;
        this.parar();
        this.seg = C.cola.seguir(id, {
          alLeer: function (t) { if (self.trabajo && self.trabajo.id === id) self.trabajo.eventos = t.eventos; },
          alTerminar: function (t) {
            self.seg = null;
            C.cola.fijarTrabajo({
              id: id, estado: t.estado || 'desconocido', proyecto: t0.proyecto || '', eventos: t.eventos,
              mensaje: t.estado === 'terminado' ? 'Procesamiento terminado.' : 'El procesamiento falló.',
              resumen: C.cola.resumirTrabajo(t), error: t.error || ''
            });
            self.$emit('actualizar');
          },
          alFallar: function (e) {
            self.seg = null;
            if (e && e.estado === 404 && t0.retomado) { C.cola.cerrarTrabajo(); return; }   // el trabajo retomado ya no existe
            C.cola.fijarTrabajo({ id: id, estado: 'desconocido', proyecto: t0.proyecto || '', mensaje: 'No se pudo leer el estado del trabajo.', error: e && e.mensaje });
          }
        });
      },
      cerrarTrabajo: function () { if (!this.corriendo) C.cola.cerrarTrabajo(); },
      reintentarLectura: function () { this.trabajo.estado = 'corriendo'; this.seguir(); },
      sincronizar: function () {
        var self = this;
        if (this.sincronizando) return;
        this.errorSync = ''; this.sincronizando = true;
        C.api.post('/api/dropbox/sync', undefined, { consulta: { proyecto_id: this.proyecto }, tiempo: TIEMPO_SYNC }).then(function (d) {
          if (!d || d.status !== 'ok' || !Array.isArray(d.proyectos)) throw { mensaje: 'Respuesta inesperada del servidor de sincronización.' };
          self.resumenSync = { hora: C.formato.ahoraTexto(), proyectos: d.proyectos };
          self.sincronizando = false;
          self.$emit('actualizar');
        }).catch(function (e) {
          self.sincronizando = false; self.resumenSync = null;
          self.errorSync = (e && e.mensaje) || 'No se pudo completar la sincronización.';
        });
      }
    },
    template: `
      <div class="acciones-cola">
        <div class="acc-botones">
          <button v-if="conProcesar" type="button" class="btn btn-pri" data-procesar-cola :disabled="ocupado" :aria-busy="ocupado ? 'true' : null"
            :title="corriendo ? 'Hay un trabajo procesando la cola; espera a que termine.' : null" @click="procesar"><Icono nombre="rayo"/>{{ ocupado ? 'Procesando…' : 'Procesar cola' }}</button>
          <button v-if="conSincronizar" type="button" class="btn btn-sec" data-sincronizar :disabled="sincronizando" :aria-busy="sincronizando ? 'true' : null" @click="sincronizar"><Icono nombre="sync"/>{{ sincronizando ? 'Sincronizando…' : 'Sincronizar desde Dropbox' }}</button>
        </div>

        <section v-if="errorLanzar" class="panel p-mal" role="alert" data-error-procesar>
          <div class="panel-cab">
            <p class="panel-t"><Icono nombre="alerta"/>No se pudo lanzar el procesamiento.</p>
            <button type="button" class="btn btn-sec panel-x" aria-label="Cerrar el error" @click="errorLanzar = null"><Icono nombre="cerrar"/></button>
          </div>
          <p class="panel-e">{{ errorLanzar.mensaje }}</p>
          <p v-if="hrefOtro" class="panel-acc"><a class="enlace" :href="hrefOtro">Ver ese trabajo<Icono nombre="flecha"/></a></p>
        </section>

        <section v-if="verTrabajo" class="panel" :class="claseTrabajo" role="status" aria-live="polite" data-trabajo-cola>
          <div class="panel-cab">
            <p class="panel-t"><Icono :nombre="iconoTrabajo"/>{{ trabajo.mensaje }}</p>
            <button v-if="!corriendo" type="button" class="btn btn-sec panel-x" aria-label="Cerrar el aviso del trabajo" @click="cerrarTrabajo"><Icono nombre="cerrar"/></button>
          </div>
          <p v-if="trabajo.id" class="panel-d">Trabajo <span class="num">{{ trabajo.id }}</span> · estado: <b>{{ trabajo.estado }}</b><template v-if="trabajo.resumen"> · {{ trabajo.resumen }}</template><template v-else-if="corriendo && trabajo.eventos"> · {{ trabajo.eventos }} eventos</template></p>
          <p v-if="trabajo.error" class="panel-e">{{ trabajo.error }}</p>
          <p v-if="trabajo.id" class="panel-acc">
            <a class="enlace" :href="hrefTrabajo" data-ver-avance>Ver el avance elemento por elemento<Icono nombre="flecha"/></a>
            <button v-if="trabajo.estado === 'desconocido'" type="button" class="btn btn-sec" @click="reintentarLectura">Reintentar la lectura</button>
          </p>
        </section>

        <section v-if="errorSync" class="panel p-mal" role="alert" data-error-sync>
          <div class="panel-cab">
            <p class="panel-t"><Icono nombre="alerta"/>No se pudo sincronizar con Dropbox</p>
            <button type="button" class="btn btn-sec panel-x" aria-label="Cerrar el error de sincronización" @click="errorSync = ''"><Icono nombre="cerrar"/></button>
          </div>
          <p class="panel-e">{{ errorSync }}</p>
        </section>

        <ResultadoSync v-if="resumenSync" :resultado="resumenSync" @cerrar="resumenSync = null"/>
      </div>`
  };
})();
