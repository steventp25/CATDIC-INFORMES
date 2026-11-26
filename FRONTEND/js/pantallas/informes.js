/* CATDIC-WEB · pantalla «Informes» (#/informes), B3g. Los informes viven dentro de cada obra (#/obra/<id>/informes):
   aquí está el acceso a los de cada obra. La vista de todas las obras juntas queda pendiente. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.pantallas = C.pantallas || {};
  C.pantallas['informes'] = {
    template: `
      <div class="pagina">
        <header class="pagina-cabeza"><h1 tabindex="-1">Informes</h1></header>
        <p class="bajada">Los informes se hacen y se consultan dentro de cada obra. Elige la obra para ver sus PDF generados.</p>
        <ElegirObra modo="informes"/>
        <section class="caja" aria-labelledby="inf-todos">
          <div class="caja-cabeza"><h2 id="inf-todos">Todos los informes juntos</h2></div>
          <p class="ayuda"><Pendiente>vista de todas las obras pendiente</Pendiente> Por ahora cada obra tiene su lista; juntarlas en una sola queda para después.</p>
        </section>
      </div>`
  };
})();
