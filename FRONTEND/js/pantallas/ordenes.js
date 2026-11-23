/* CATDIC-WEB · pantalla «Órdenes de trabajo» (#/ordenes) — B3f, kanban Z16 de solo lectura.
   Lee GET /api/dashboard (`ordenes[]`, `proyectos[]`). No existe ruta para crear ni mover órdenes (Fase D): se rotula, no se simula.
   En la dirección viven los filtros y el estado elegido en pantallas estrechas:  #/ordenes?obra=<id>&tipo=Supervisión|Levantamiento&estado=<estado>
   Escritorio: las 6 columnas lado a lado (el tablero se desplaza dentro de sí mismo). Estrecho: un estado a la vez, con pestañas. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.pantallas = C.pantallas || {};

  var TIPOS = ['Supervisión', 'Levantamiento'];

  C.pantallas['ordenes'] = {
    data: function () { return { estado: 'cargando', mensaje: '', datos: null, solicitud: 0, desborda: false, masIzq: false, masDer: false, destino: '' }; },
    computed: {
      ruta: function () { return C.rutas.ruta; },
      consulta: function () { return this.ruta.consulta || {}; },
      todas: function () { return C.ordenes.lista(this.datos); },
      proyectos: function () { return this.datos && Array.isArray(this.datos.proyectos) ? this.datos.proyectos : []; },
      obrasOrdenadas: function () {
        return this.proyectos.slice().sort(function (a, b) { return String(a.nombre).localeCompare(String(b.nombre), 'es'); });
      },
      nombres: function () { var m = {}; this.proyectos.forEach(function (p) { m[p.id] = p.nombre; }); return m; },
      filtroObra: function () { return this.consulta.obra ? String(this.consulta.obra) : ''; },
      filtroTipo: function () { return TIPOS.indexOf(this.consulta.tipo) !== -1 ? this.consulta.tipo : ''; },
      tipoDesconocido: function () { return this.consulta.tipo && !this.filtroTipo ? String(this.consulta.tipo) : ''; },
      obraDesconocida: function () { return this.estado === 'listo' && this.filtroObra && !this.nombres[this.filtroObra]; },
      nombreFiltroObra: function () { return this.nombres[this.filtroObra] || this.filtroObra; },
      filtradas: function () {
        var ob = this.filtroObra, ti = this.filtroTipo;
        return this.todas.filter(function (o) { return (!ob || o.proyecto_id === ob) && (!ti || o.tipo === ti); });
      },
      grupos: function () { return C.ordenes.agrupar(this.filtradas); },
      estados: function () { return C.ordenes.ESTADOS; },
      elegido: function () {
        // Con ?estado= válido se respeta. Sin él, abre la primera pestaña (en el orden de las columnas) que tenga órdenes;
        // si no hay ninguna, «Pendiente». Con filtros puestos cuenta lo que se ve, no lo que se ocultó.
        var e = this.consulta.estado, ES = C.ordenes.ESTADOS, porEstado = this.grupos.porEstado;
        if (ES.indexOf(e) !== -1) return e;
        for (var i = 0; i < ES.length; i++) if (porEstado[ES[i]] && porEstado[ES[i]].length) return ES[i];
        return ES[0];
      },
      porId: function () {
        var m = {}; this.filtradas.forEach(function (o) { if (o.doc_id) m[o.doc_id] = o; }); return m;
      },
      enTodas: function () {
        var m = {}; this.todas.forEach(function (o) { if (o.doc_id) m[o.doc_id] = o; }); return m;
      },
      estadoBloque: function () {
        if (this.estado !== 'listo') return this.estado;
        return this.todas.length ? 'listo' : 'vacio';
      },
      hayFiltros: function () { return !!(this.filtroObra || this.filtroTipo); }
    },
    created: function () { this.leer(); },
    // El tablero ancho se desplaza dentro de sí mismo cuando las 6 columnas no caben (≈1280 px de ventana): se mide para que el
    // contenedor reciba foco (flechas del teclado) y para dibujar el sombreado del borde donde hay más columnas.
    mounted: function () { window.addEventListener('resize', this.medir); },
    updated: function () { this.enlazar(); this.medir(); },
    beforeUnmount: function () {
      window.removeEventListener('resize', this.medir); clearTimeout(this._reloj);
      if (this._ro) { this._ro.disconnect(); this._ro = null; }
    },
    methods: {
      enlazar: function () {
        var el = this.$refs.cols;
        if (el === this._elCols) return;
        if (this._ro) { this._ro.disconnect(); this._ro = null; }
        this._elCols = el || null;
        if (el && window.ResizeObserver) { this._ro = new ResizeObserver(this.medir); this._ro.observe(el); }
      },
      medir: function () {
        var el = this.$refs.cols;
        if (!el) { this.desborda = false; this.masIzq = false; this.masDer = false; return; }
        var sobra = el.scrollWidth - el.clientWidth;
        this.desborda = sobra > 1;
        this.masIzq = this.desborda && el.scrollLeft > 1;
        this.masDer = this.desborda && el.scrollLeft < sobra - 1;
      },
      leer: function () {
        var self = this, n = ++this.solicitud;
        this.estado = 'cargando'; this.mensaje = '';
        return C.api.get('/api/dashboard').then(function (d) {
          if (n !== self.solicitud) return;
          self.datos = d || {}; self.estado = 'listo';
        }, function (e) {
          if (n !== self.solicitud) return;
          self.mensaje = e.mensaje; self.estado = 'error';
        });
      },
      // Filtros: cada cambio es una entrada del historial (Atrás vuelve al filtro anterior). El estado elegido no se pierde.
      filtrar: function (cambio) {
        var q = { obra: this.filtroObra, tipo: this.filtroTipo, estado: this.consulta.estado || '' };
        Object.keys(cambio).forEach(function (k) { q[k] = cambio[k]; });
        C.rutas.irA(C.ordenes.hash(q));
      },
      cambiarObra: function (ev) { this.filtrar({ obra: ev.target.value }); },
      cambiarTipo: function (ev) { this.filtrar({ tipo: ev.target.value }); },
      quitarFiltros: function () { this.filtrar({ obra: '', tipo: '' }); },
      // El estado elegido se sustituye en el historial (no se llena de entradas); recargar y volver con Atrás lo conservan.
      elegir: function (e, enfocar) {
        var self = this;
        C.rutas.reemplazar(C.ordenes.hash({ obra: this.filtroObra, tipo: this.filtroTipo, estado: e }));
        if (enfocar) this.$nextTick(function () {
          var t = self.$el.querySelector('[data-ord-tab="' + e + '"]');
          if (t) t.focus();
        });
      },
      teclaTab: function (ev, i) {
        var n = this.estados.length, j = null;
        if (ev.key === 'ArrowRight' || ev.key === 'ArrowDown') j = (i + 1) % n;
        else if (ev.key === 'ArrowLeft' || ev.key === 'ArrowUp') j = (i + n - 1) % n;
        else if (ev.key === 'Home') j = 0;
        else if (ev.key === 'End') j = n - 1;
        if (j === null) return;
        ev.preventDefault();
        this.elegir(this.estados[j], true);
      },
      icono: function (e) { return C.ordenes.ICONOS[e] || 'info'; },
      texto: function (v) { return C.formato.texto(v); },
      obraDe: function (o) { return this.nombres[o.proyecto_id] || null; },
      hrefObra: function (o) { return C.rutas.hashObra(o.proyecto_id, 'visitas'); },
      fecha: function (o) {
        var f = C.formato.fecha(o.fecha_comprometida);
        if (f) return { texto: f, pend: false };
        var crudo = C.formato.texto(o.fecha_comprometida);
        return { texto: crudo, pend: true };
      },
      tieneVersion: function (o) { return o.version !== null && o.version !== undefined && o.version !== ''; },
      dep: function (o) { return C.formato.texto(o.depende_de); },
      // «depende de X»: enlaza a esa orden si está en la pantalla; si existe pero los filtros la ocultan, lo dice; si no existe, lo dice.
      irA: function (id) {
        var o = this.porId[id], self = this;
        if (!o) return;
        var e = C.ordenes.ESTADOS.indexOf(o.estado) !== -1 ? o.estado : null;
        if (e && e !== this.elegido) C.rutas.reemplazar(C.ordenes.hash({ obra: this.filtroObra, tipo: this.filtroTipo, estado: e }));
        this.$nextTick(function () {
          var tarjetas = self.$el.querySelectorAll('[data-orden]'), t = null;
          for (var i = 0; i < tarjetas.length; i++) if (tarjetas[i].getAttribute('data-orden') === id) { t = tarjetas[i]; break; }
          if (t) {
            t.scrollIntoView({ block: 'center' }); t.focus({ preventScroll: true });
            // Señal breve en la tarjeta de destino (fondo y borde, ~450 ms + 150 ms de salida) para ver adónde fue el foco
            self.destino = id; clearTimeout(self._reloj);
            self._reloj = setTimeout(function () { self.destino = ''; }, 450);
          }
        });
      },
      cuenta: function (n, uno, varios) { return n + ' ' + (n === 1 ? uno : varios); }
    },
    template: `
      <div class="pagina pagina-ordenes">
        <header class="pagina-cabeza">
          <h1 tabindex="-1">Órdenes de trabajo</h1>
          <p v-if="estado === 'listo' && todas.length" class="fecha" data-ord-resumen>Se muestran <span class="num">{{ filtradas.length }}</span> de <span class="num">{{ todas.length }}</span> {{ todas.length === 1 ? 'orden' : 'órdenes' }}</p>
        </header>

        <Bloque :estado="estadoBloque" :huesos="4" vacio-titulo="No hay órdenes de trabajo registradas."
          error-titulo="No se pudieron leer las órdenes de trabajo." :error-mensaje="mensaje" @reintentar="leer">
          <section class="caja" aria-labelledby="t-ord-fil" data-ord-filtros>
            <div class="caja-cabeza"><h2 id="t-ord-fil">Filtros</h2></div>
            <div class="ord-filtros">
              <label class="campo"><span class="campo-e">Obra</span>
                <select class="campo-i" :value="filtroObra" @change="cambiarObra" data-ord-obra>
                  <option value="">Todas las obras</option>
                  <option v-if="obraDesconocida" :value="filtroObra">{{ filtroObra }} (no figura en el tablero)</option>
                  <option v-for="p in obrasOrdenadas" :key="p.id" :value="p.id">{{ p.nombre }}</option>
                </select></label>
              <label class="campo"><span class="campo-e">Tipo</span>
                <select class="campo-i" :value="filtroTipo" @change="cambiarTipo" data-ord-tipo>
                  <option value="">Supervisión y Levantamiento</option>
                  <option value="Supervisión">Supervisión</option>
                  <option value="Levantamiento">Levantamiento</option>
                </select></label>
            </div>
            <p v-if="tipoDesconocido" class="ayuda" role="status">El tipo «{{ tipoDesconocido }}» no existe; se ignora. Los tipos son Supervisión y Levantamiento.</p>
            <div v-if="hayFiltros" class="ord-aplicados" data-ord-aplicados>
              <span class="ayuda">Filtros aplicados:</span>
              <span v-if="filtroObra" class="etq ord-chip">Obra: {{ nombreFiltroObra }}</span>
              <span v-if="filtroTipo" class="etq ord-chip">Tipo: {{ filtroTipo }}</span>
              <button type="button" class="btn btn-sec ord-quitar" @click="quitarFiltros" data-ord-quitar>Quitar filtros</button>
            </div>
          </section>

          <p v-if="hayFiltros && !filtradas.length" class="aviso" role="status" data-ord-sin-coincidencias>
            <span>Ninguna orden coincide con los filtros. <button type="button" class="enlace" @click="quitarFiltros">Quitar filtros</button></span></p>

          <div class="ord-tablero" data-ord-tablero>
            <div class="ord-tabs" role="tablist" aria-label="Estado de las órdenes" data-ord-tabs>
              <button v-for="(e, i) in estados" :key="e" type="button" role="tab" class="ord-tab" :id="'ord-tab-' + i"
                :data-ord-tab="e" :data-estado="e" :aria-selected="e === elegido ? 'true' : 'false'" :aria-controls="'ord-col-' + i"
                :tabindex="e === elegido ? 0 : -1" @click="elegir(e)" @keydown="teclaTab($event, i)">
                <Icono :nombre="icono(e)"/><span class="ord-tab-t">{{ e }}</span><span class="num ord-n">{{ grupos.porEstado[e].length }}</span>
              </button>
            </div>
            <p v-show="desborda" class="ayuda ord-desliza" data-ord-desliza><Icono nombre="flecha"/>{{ estados.length }} columnas · desliza el tablero hacia los lados</p>
            <div class="ord-marco" :data-mas-izq="masIzq ? '' : null" :data-mas-der="masDer ? '' : null">
            <div ref="cols" class="ord-cols" data-ord-cols @scroll.passive="medir"
              :tabindex="desborda ? 0 : null" :role="desborda ? 'region' : null" :aria-label="desborda ? 'Tablero de órdenes, ' + estados.length + ' columnas: se desplaza hacia los lados con las flechas del teclado' : null">
              <section v-for="(e, i) in estados" :key="e" class="ord-col" :class="{ 'es-sel': e === elegido }" :data-estado="e" :data-ord-col="e"
                role="tabpanel" :id="'ord-col-' + i" :aria-labelledby="'ord-tab-' + i">
                <h2 class="ord-col-cab"><span class="ord-col-t"><Icono :nombre="icono(e)"/>{{ e }}</span><span class="num ord-n" :aria-label="cuenta(grupos.porEstado[e].length, 'orden', 'órdenes')">{{ grupos.porEstado[e].length }}</span></h2>
                <p v-if="!grupos.porEstado[e].length" class="ord-vacio" data-ord-vacio>Sin órdenes en este estado</p>
                <ul v-else class="ord-lista">
                  <li v-for="(o, k) in grupos.porEstado[e]" :key="(o.doc_id || '') + '#' + k">
                    <article class="ord-t" :class="{ 'es-destino': destino && o.doc_id === destino }" :data-estado="e" :data-orden="o.doc_id" tabindex="-1">
                      <header class="ord-t-cab">
                        <span class="num ord-id" v-if="texto(o.doc_id)">{{ o.doc_id }}</span><Pendiente v-else/>
                        <span class="etq" v-if="texto(o.tipo)">{{ o.tipo }}</span>
                      </header>
                      <p class="ord-sec"><template v-if="texto(o.seccion)">{{ o.seccion }}</template><Pendiente v-else/></p>
                      <p class="ord-nota"><template v-if="texto(o.nota)">{{ o.nota }}</template><span v-else class="ayuda">sin nota</span></p>
                      <dl class="ord-dl">
                        <div><dt>Obra</dt><dd><a v-if="obraDe(o)" class="enlace ord-obra" :href="hrefObra(o)">{{ obraDe(o) }}</a><template v-else><span class="num">{{ o.proyecto_id }}</span> <Pendiente>obra no registrada</Pendiente></template></dd></div>
                        <div><dt>Formato</dt><dd><template v-if="texto(o.formato)">{{ o.formato }}</template><Pendiente v-else/></dd></div>
                        <div><dt>Entregable</dt><dd><template v-if="texto(o.entregable)">{{ o.entregable }}</template><Pendiente v-else/></dd></div>
                        <div><dt>Prioridad</dt><dd><template v-if="texto(o.prioridad)">{{ o.prioridad }}</template><Pendiente v-else/></dd></div>
                        <div><dt>Fecha comprometida</dt><dd><span v-if="fecha(o).texto" class="num">{{ fecha(o).texto }}</span> <Pendiente v-if="fecha(o).pend"/></dd></div>
                        <div v-if="dep(o)"><dt>Depende de</dt><dd>
                          <button v-if="porId[dep(o)]" type="button" class="enlace ord-dep num" @click="irA(dep(o))">{{ dep(o) }}</button>
                          <template v-else><span class="num">{{ dep(o) }}</span> <span class="ayuda">{{ enTodas[dep(o)] ? '(fuera de los filtros)' : '(no figura en las órdenes)' }}</span></template></dd></div>
                        <div><dt>Versión</dt><dd><span v-if="tieneVersion(o)" class="num">{{ o.version }}</span><Pendiente v-else/></dd></div>
                      </dl>
                    </article>
                  </li>
                </ul>
              </section>
            </div>
            </div>
          </div>

          <section v-for="g in grupos.otros" :key="'otro:' + g.valor" class="caja ord-otro" :aria-label="'Otro estado: ' + (g.texto || 'pendiente de verificar')" data-ord-otro>
            <div class="caja-cabeza"><h2>Otro estado: <template v-if="g.texto">{{ g.texto }}</template><Pendiente v-else/></h2><span class="num ord-n">{{ g.items.length }}</span></div>
            <p class="ayuda">El servidor trae un estado que no es uno de los seis del kanban. No se oculta: se muestra tal cual y queda anotado.</p>
            <ul class="ord-lista">
              <li v-for="(o, k) in g.items" :key="(o.doc_id || '') + '#' + k">
                <article class="ord-t" data-estado="otro" :data-orden="o.doc_id" tabindex="-1">
                  <header class="ord-t-cab"><span class="num ord-id" v-if="texto(o.doc_id)">{{ o.doc_id }}</span><Pendiente v-else/><span class="etq" v-if="texto(o.tipo)">{{ o.tipo }}</span></header>
                  <p class="ord-sec"><template v-if="texto(o.seccion)">{{ o.seccion }}</template><Pendiente v-else/></p>
                  <p class="ord-nota"><template v-if="texto(o.nota)">{{ o.nota }}</template><span v-else class="ayuda">sin nota</span></p>
                  <dl class="ord-dl">
                    <div><dt>Obra</dt><dd><a v-if="obraDe(o)" class="enlace ord-obra" :href="hrefObra(o)">{{ obraDe(o) }}</a><template v-else><span class="num">{{ o.proyecto_id }}</span> <Pendiente>obra no registrada</Pendiente></template></dd></div>
                    <div><dt>Formato</dt><dd><template v-if="texto(o.formato)">{{ o.formato }}</template><Pendiente v-else/></dd></div>
                    <div><dt>Fecha comprometida</dt><dd><span v-if="fecha(o).texto" class="num">{{ fecha(o).texto }}</span> <Pendiente v-if="fecha(o).pend"/></dd></div>
                  </dl>
                </article>
              </li>
            </ul>
          </section>
        </Bloque>

        <section class="caja" aria-labelledby="t-ord-acc">
          <div class="caja-cabeza"><h2 id="t-ord-acc">Acciones</h2><FaseD fase="D"/></div>
          <div class="acc-botones">
            <button type="button" class="btn btn-sec" disabled aria-describedby="ord-motivo" data-ord-crear><Icono nombre="mas"/>Crear orden</button>
            <button type="button" class="btn btn-sec" disabled aria-describedby="ord-motivo" data-ord-cambiar>Cambiar estado</button>
          </div>
          <p id="ord-motivo" class="ayuda">Crear órdenes y cambiar su estado todavía no se puede: el programa aún no tiene una ruta para guardarlos. Es parte de la Fase D, y por eso las tarjetas no se arrastran.</p>
        </section>
      </div>`
  };
})();
