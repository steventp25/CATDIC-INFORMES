/* CATDIC-WEB · pantalla «Bandeja de trabajo».
   B3d construye la «Cola de visitas (todas las obras)» (Z15, el componente ColaVisitas de js/cola.js).
   B3e añade «Dudas abiertas (todas las obras)» (DudasBandeja), con enlace a la Mesa de Dudas de cada grupo.
   La ruta común de pendientes es Fase D-a y se rotula como tal: no se simulan datos. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.pantallas = C.pantallas || {};

  C.pantallas['bandeja'] = {
    mixins: [C.datos.mixin],
    computed: {
      ruta: function () { return C.rutas.ruta; },
      seleccionada: function () { return this.ruta.consulta && this.ruta.consulta.visita ? String(this.ruta.consulta.visita) : ''; }
    },
    template: `
      <div class="pagina pagina-bandeja">
        <header class="pagina-cabeza"><h1 tabindex="-1">Bandeja de trabajo</h1></header>

        <ColaVisitas titulo="Cola de visitas (todas las obras)" :estado="estadoTablero" :mensaje="mensajeTablero"
          :visitas="visitasTodas" :proyectos="proyectos" :dudas="estadoDudas === 'listo' ? dudas : null" mostrar-obra
          :seleccionada="seleccionada" @reintentar="recargar">
          <p class="ayuda cola-nota">Procesar cola y Sincronizar desde Dropbox están en <a class="enlace" href="#/inicio">Inicio</a> y, por obra, en su pestaña «Visitas y trabajos».</p>
        </ColaVisitas>

        <DudasBandeja :dudas="dudas || []" :estado="estadoDudas" :mensaje="mensajeDudas" :proyectos="proyectos" @reintentar="leerDudas"/>

        <section class="caja" aria-labelledby="t-ord" data-bandeja-ordenes>
          <div class="caja-cabeza"><h2 id="t-ord">Órdenes de trabajo</h2></div>
          <Bloque :estado="estadoTablero" :huesos="1" error-titulo="No se pudo leer el número de órdenes." :error-mensaje="mensajeTablero" @reintentar="leerTablero">
            <a class="enlace ord-acceso" href="#/ordenes">Órdenes de trabajo: <span class="num">{{ stats.ordenes_abiertas }}</span> {{ stats.ordenes_abiertas === 1 ? 'abierta' : 'abiertas' }}<Icono nombre="flecha"/></a>
          </Bloque>
        </section>

        <section class="caja" aria-labelledby="t-pend">
          <div class="caja-cabeza"><h2 id="t-pend">Pendientes de todas las obras</h2><FaseD fase="D-a"/></div>
          <div class="vacio">
            <p class="vacio-t">Esta parte todavía no está construida.</p>
            <p>Aquí irán los pendientes de todas las obras con filtros. La ruta común de pendientes es Fase D-a: hasta que exista, la bandeja no simula datos. Las dudas abiertas están arriba.</p>
          </div>
        </section>
      </div>`
  };
})();
