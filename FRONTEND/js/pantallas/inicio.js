/* CATDIC-WEB · pantalla «Inicio» (B3a). Necesidades N6 y N7 de PLANES/etapa-5-inventario-ui.md §10.2.
   Lee GET /api/dashboard y GET /api/dudas?resuelta=false (js/datos.js), cada una con su estado.
   Lo que el backend no calcula (bloqueadas, vencen en 7 días, entregas y vencimientos) sale «pendiente de verificar»
   con la etiqueta Fase D-a; nada se rellena ni se muestra como 0. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.pantallas = C.pantallas || {};
  var LIMITE = 10;

  C.pantallas['inicio'] = {
    mixins: [C.datos.mixin],
    computed: {
      ruta: function () { return C.rutas.ruta; },
      hoy: function () { return C.datos.hoyTexto(); },
      // Prioridades: necesitan las dos lecturas. Si las dudas fallan, se muestra lo del tablero y el error de dudas aparte.
      estadoPrior: function () {
        if (this.estadoTablero === 'error') return 'error';
        if (this.estadoTablero === 'cargando' || this.estadoDudas === 'cargando') return 'cargando';
        if (!this.filas.length && this.estadoDudas === 'listo') return 'vacio';
        return 'listo';
      },
      filasTodas: function () {
        if (this.estadoTablero !== 'listo') return [];
        return C.datos.prioridades(this.tablero, this.estadoDudas === 'listo' ? this.dudas : null);
      },
      filas: function () { return this.filasTodas.slice(0, LIMITE); },
      // Solo el resumen: la lista única de visitas es la de la Bandeja (no hay una segunda tabla que pueda desincronizarse).
      resumenCola: function () {
        var r = C.cola.resumen(this.visitasTodas);
        return C.cola.plural(r.total, 'visita', 'visitas') + ' · ' + r.enCola + ' en cola · ' + r.conDudas + ' con dudas';
      },
      restantes: function () { return Math.max(0, this.filasTodas.length - LIMITE); },
      obrasConPlano: function () {
        var pl = this.planos;
        return this.obrasOrdenadas.filter(function (p) { return !!pl[p.id]; });
      },
      estadoRevisiones: function () {
        if (this.estadoTablero !== 'listo') return this.estadoTablero;
        return this.obrasConPlano.length ? 'listo' : 'vacio';
      },
      estadoObras: function () {
        if (this.estadoTablero !== 'listo') return this.estadoTablero;
        return this.obrasOrdenadas.length ? 'listo' : 'vacio';
      },
      acciones: function () {
        return this.obrasOrdenadas.map(function (p) { return { id: p.id, nombre: p.nombre, texto: C.formato.texto(p.observaciones) }; });
      }
    },
    methods: {
      cerrarAviso: function () { C.rutas.ruta.aviso = ''; },
      etiquetaDias: function (f) {
        if (f.dias === null) return null;
        if (f.dias < 0) return f.fecha;
        return f.dias === 0 ? 'hoy' : 'hace ' + f.dias + ' d';
      },
      hrefObra: function (id, pestana) { return C.rutas.hashObra(id, pestana); },
      textoObra: function (p) {
        return [C.formato.texto(p.tipo), C.formato.texto(p.formato_defecto)].filter(Boolean).join(' · ');
      },
      revision: function (id) {
        var pv = this.planos[id] || {};
        var et = C.formato.texto(pv.etiqueta_revision);
        return 'Rev. ' + pv.revision + (et ? ' · ' + et : '');
      }
    },
    template: `
      <div class="pagina pagina-inicio">
        <div v-if="ruta.aviso" class="aviso" role="status">
          <p>{{ ruta.aviso }}</p>
          <button type="button" class="btn btn-sec" @click="cerrarAviso">Entendido</button>
        </div>
        <header class="pagina-cabeza">
          <h1 tabindex="-1">Inicio</h1>
          <p class="fecha">Hoy <span class="num">{{ hoy }}</span></p>
        </header>

        <section class="caja" aria-labelledby="t-cifras">
          <div class="caja-cabeza"><h2 id="t-cifras">En números</h2></div>
          <Bloque :estado="estadoTablero" :huesos="2" error-titulo="No se pudo cargar el tablero." :error-mensaje="mensajeTablero" @reintentar="leerTablero">
            <dl class="cajetin cifras">
              <div><dt>Obras activas</dt><dd><a class="cifra-n num" href="#/obras">{{ stats.proyectos_activos }}</a></dd></div>
              <div><dt>Visitas en cola</dt><dd><a class="cifra-n num" href="#/bandeja">{{ stats.visitas_en_cola }}</a></dd></div>
              <div><dt>Órdenes abiertas</dt><dd><span class="cifra-n num">{{ stats.ordenes_abiertas }}</span> <span class="ayuda">Se verán en la pantalla de órdenes (B3f).</span></dd></div>
              <div><dt>Bloqueadas</dt><dd class="cifra-p"><Pendiente/> <FaseD fase="D-a"/></dd></div>
              <div><dt>Vencen en ≤ 7 días</dt><dd class="cifra-p"><Pendiente/> <FaseD fase="D-a"/></dd></div>
            </dl>
          </Bloque>
        </section>

        <section class="caja" aria-labelledby="t-cola">
          <div class="caja-cabeza"><h2 id="t-cola">Cola de visitas</h2><a class="enlace" href="#/bandeja">Ver la cola completa<Icono nombre="flecha"/></a></div>
          <Bloque :estado="estadoTablero" :huesos="2" error-titulo="Sin datos: no se pudo leer la cola de visitas del backend." :error-mensaje="mensajeTablero" @reintentar="leerTablero">
            <p class="cola-resumen num" data-cola-resumen>{{ resumenCola }}</p>
          </Bloque>
          <AccionesCola @actualizar="recargar"/>
        </section>

        <div class="rejilla-inicio">
          <div class="col-principal">
            <section class="caja" aria-labelledby="t-prior">
              <div class="caja-cabeza"><h2 id="t-prior">Prioridades</h2></div>
              <Bloque :estado="estadoDudas === 'error' ? 'error' : 'listo'" error-titulo="No se pudo leer la Mesa de Dudas." :error-mensaje="mensajeDudas" @reintentar="leerDudas"/>
              <Bloque :estado="estadoPrior" :huesos="4" vacio-titulo="No hay pendientes."
                vacio-texto="Cuando entre una visita o aparezca una duda, saldrá aquí con su siguiente paso."
                accion-texto="Ver Mis obras" accion-href="#/obras"
                error-titulo="No se pudo cargar el tablero." :error-mensaje="mensajeTablero" @reintentar="leerTablero">
                <ul class="filas">
                  <li v-for="f in filas" :key="f.clave" class="fila" :class="{ 'es-bloq': f.bloq }">
                    <a class="fila-a con-obra" :href="f.href">
                      <span class="f-tipo"><Icono v-if="f.bloq" nombre="alerta" class="ico-bloq"/>{{ f.tipo }}</span>
                      <span class="f-obra">{{ f.obra }}</span>
                      <span class="f-donde">{{ f.donde }}</span>
                      <span class="f-motivo">{{ f.motivo }}</span>
                      <span class="f-sig">{{ f.siguiente }}<Icono nombre="flecha"/></span>
                      <span class="f-dias num" :title="f.fecha ? 'Fecha de la visita ' + f.fecha : ''"><template v-if="etiquetaDias(f)">{{ etiquetaDias(f) }}</template><Pendiente v-else/></span>
                    </a>
                  </li>
                </ul>
                <p v-if="restantes" class="ayuda resto">Y {{ restantes }} más. La lista completa de pendientes es la Bandeja de trabajo.</p>
                <p v-if="estadoDudas === 'listo'" class="ayuda resto">Antigüedad: días desde la fecha de la visita. Las dudas de obra no tienen visita y no traen fecha.</p>
              </Bloque>
            </section>

            <section class="caja" aria-labelledby="t-rev">
              <div class="caja-cabeza"><h2 id="t-rev">Revisiones de planos</h2></div>
              <Bloque :estado="estadoRevisiones" :huesos="2" vacio-titulo="Ninguna obra tiene plano vigente."
                vacio-texto="Cuando subas el plano de una obra, la revisión de sus datos saldrá aquí." accion-texto="Ver Mis obras" accion-href="#/obras"
                error-titulo="No se pudo cargar el tablero." :error-mensaje="mensajeTablero" @reintentar="leerTablero">
                <ul class="filas">
                  <li v-for="p in obrasConPlano" :key="p.id" class="fila">
                    <a class="fila-a con-obra" :href="hrefObra(p.id, 'planos')">
                      <span class="f-tipo">Revisión de plano</span>
                      <span class="f-obra">{{ p.nombre }}</span>
                      <span class="f-donde">Plano vigente {{ revision(p.id) }}</span>
                      <span class="f-motivo">Tablas por confirmar: <Pendiente/> <FaseD fase="D-a"/></span>
                      <span class="f-sig">Revisar los datos del plano<Icono nombre="flecha"/></span>
                    </a>
                  </li>
                </ul>
                <p class="ayuda resto">La lista de tablas extraídas que trae el servidor no dice cuáles están confirmadas, y no se deduce. Mientras tanto la revisión se abre desde la obra.</p>
              </Bloque>
            </section>

            <section class="caja" aria-labelledby="t-ent">
              <div class="caja-cabeza"><h2 id="t-ent">Entregas y vencimientos</h2><FaseD fase="D-a"/></div>
              <p><Pendiente/></p>
              <p class="ayuda">El servidor todavía no calcula entregas ni vencimientos. No se muestran fechas inventadas.</p>
            </section>
          </div>

          <div class="col-lateral">
            <section class="caja" aria-labelledby="t-acc">
              <div class="caja-cabeza"><h2 id="t-acc">Próximas acciones</h2></div>
              <Bloque :estado="estadoObras" :huesos="3" vacio-titulo="Nada que hacer ahora." vacio-texto="Las acciones salen de cada obra registrada."
                accion-texto="Ver Mis obras" accion-href="#/obras"
                error-titulo="No se pudo cargar el tablero." :error-mensaje="mensajeTablero" @reintentar="leerTablero">
                <ul class="acciones">
                  <li v-for="a in acciones" :key="a.id">
                    <a :href="hrefObra(a.id, 'resumen')"><template v-if="a.texto">{{ a.texto }}</template><Pendiente v-else/><span class="sub">{{ a.nombre }}</span></a>
                  </li>
                </ul>
              </Bloque>
            </section>

            <section class="caja" aria-labelledby="t-obras">
              <div class="caja-cabeza"><h2 id="t-obras">Mis obras</h2><a class="enlace" href="#/obras">Ver todas<Icono nombre="flecha"/></a></div>
              <Bloque :estado="estadoObras" :huesos="3" vacio-titulo="Aún no hay obras." vacio-texto="Registra la primera obra desde Mis obras."
                accion-texto="Ir a Mis obras" accion-href="#/obras"
                error-titulo="No se pudo cargar el tablero." :error-mensaje="mensajeTablero" @reintentar="leerTablero">
                <ul class="obras-mini">
                  <li v-for="p in obrasOrdenadas" :key="p.id">
                    <a :href="hrefObra(p.id, 'resumen')"><span class="om-n">{{ p.nombre }}</span><span class="om-d">{{ textoObra(p) }}<Pendiente v-if="!textoObra(p)"/></span></a>
                  </li>
                </ul>
              </Bloque>
            </section>
          </div>
        </div>
      </div>`
  };
})();
