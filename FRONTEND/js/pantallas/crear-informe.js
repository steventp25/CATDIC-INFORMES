/* CATDIC-WEB · pantalla «Crear informe» (#/crear-informe), B3g. El botón del riel lleva a elegir la obra y, después, al
   mismo flujo «Hacer informe» de esa obra (pestaña Informes con el diálogo abierto). El trabajo independiente, sin obra,
   sigue siendo Fase D-c y no se simula. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.pantallas = C.pantallas || {};
  C.pantallas['crear-informe'] = {
    template: `
      <div class="pagina">
        <header class="pagina-cabeza"><h1 tabindex="-1">Crear informe</h1></header>
        <p class="bajada">El informe sale de una visita de una obra: elige la obra y, después, la visita y los formatos.</p>
        <ElegirObra modo="hacer"/>
        <section class="caja" aria-labelledby="ci-solo">
          <div class="caja-cabeza"><h2 id="ci-solo">Informe independiente, sin obra</h2><FaseD fase="D-c" texto="Guardar trabajos independientes"/></div>
          <p class="ayuda">Un informe que no pertenezca a una obra necesita guardar trabajos sueltos en el backend. Todavía no existe y no se simula.</p>
        </section>
      </div>`
  };
})();
