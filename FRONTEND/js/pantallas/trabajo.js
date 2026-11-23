/* CATDIC-WEB · pantalla «Avance del trabajo» (#/trabajo/<id>), B3d (T10b, parte de la Etapa 3).
   La cabecera y la ruta viven aquí; el avance en vivo es el componente común `AvanceTrabajo` (js/avance-trabajo.js),
   que también usa la pestaña «Informes» de cada obra. La ruta lleva el id: se puede cerrar y volver a abrir sin perder nada. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.pantallas = C.pantallas || {};

  C.pantallas['trabajo'] = {
    computed: {
      id: function () { return C.rutas.ruta.id; }
    },
    template: `
      <div class="pagina pagina-trabajo">
        <header class="pagina-cabeza">
          <div class="obra-titulo">
            <a class="miga" href="#/bandeja"><Icono nombre="volver"/>Bandeja de trabajo</a>
            <h1 tabindex="-1">Avance del trabajo</h1>
          </div>
          <p class="ayuda tr-id">Trabajo <span class="num" data-trabajo-id>{{ id }}</span></p>
        </header>
        <AvanceTrabajo :trabajo-id="id" :key="id"/>
      </div>`
  };
})();
