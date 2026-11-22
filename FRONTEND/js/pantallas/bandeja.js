/* CATDIC-WEB · pantalla «Bandeja de trabajo».
   B3d construye la «Cola de visitas (todas las obras)» (Z15, el componente ColaVisitas de js/cola.js).
   El resto de la Bandeja (pendientes de todas las obras, filtros y Mesa de Dudas) lo construye B3e; la ruta común de
   pendientes es Fase D-a y se rotula como tal: no se simulan datos. */
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

        <section class="caja" aria-labelledby="t-pend">
          <div class="caja-cabeza"><h2 id="t-pend">Pendientes de todas las obras</h2><FaseD fase="D-a"/></div>
          <div class="vacio">
            <p class="vacio-t">Esta parte todavía no está construida.</p>
            <p>Aquí irán los pendientes de todas las obras con filtros, y la Mesa de Dudas. La ruta común de pendientes es Fase D-a: hasta que exista, la bandeja no simula datos.</p>
            <p>La construye la tarea <span class="num tarea">B3e</span> de la Fase B.</p>
          </div>
        </section>
      </div>`
  };
})();
