/* CATDIC-WEB · tema claro/oscuro. Se carga en <head>, antes de pintar, para que no parpadee.
   Preferencia guardada en localStorage (con try/catch: puede fallar en ventanas privadas).
   Sin preferencia guardada («sistema») se quita el atributo data-tema y manda prefers-color-scheme. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  var CLAVE = 'catdic.tema';
  function leer() {
    try { var v = window.localStorage.getItem(CLAVE); return (v === 'claro' || v === 'oscuro') ? v : 'sistema'; } catch (e) { return 'sistema'; }
  }
  function aplicar(v) {
    var el = document.documentElement;
    if (v === 'claro' || v === 'oscuro') el.setAttribute('data-tema', v); else el.removeAttribute('data-tema');
  }
  function guardar(v) {
    try {
      if (v === 'claro' || v === 'oscuro') window.localStorage.setItem(CLAVE, v); else window.localStorage.removeItem(CLAVE);
    } catch (e) { /* sin almacenamiento: el cambio vale solo para esta sesión */ }
    aplicar(v);
  }
  C.tema = { leer: leer, guardar: guardar };
  aplicar(leer());
})();
