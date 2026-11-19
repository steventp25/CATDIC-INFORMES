/* CATDIC-WEB · enrutador por hash. El botón Atrás del navegador funciona porque cada pantalla es un hash.
   Generales:  #/inicio  #/obras  #/bandeja  #/informes  #/configuracion  #/crear-informe
   De obra:    #/obra/<id>/<pestaña>   con pestaña = resumen | visitas | planos | avance | informes | cierre
   Una ruta desconocida lleva a Inicio con un aviso (se sustituye en el historial, para que Atrás no vuelva a ella). */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};

  var GENERALES = ['inicio', 'obras', 'bandeja', 'informes', 'configuracion', 'crear-informe'];
  var PESTANAS = [
    ['resumen', 'Resumen'], ['visitas', 'Visitas y trabajos'], ['planos', 'Planos y ficha'],
    ['avance', 'Avance'], ['informes', 'Informes'], ['cierre', 'Cierre']
  ];

  // Estado reactivo: las pantallas lo leen; app.js lo observa para mover el foco.
  var ruta = Vue.reactive({ nombre: 'inicio', id: '', pestana: '', consulta: {}, hash: '#/inicio', clave: 'inicio', aviso: '' });

  function irA(hash) { if (location.hash !== hash) location.hash = hash; }
  function sustituir(hash) { history.replaceState(null, '', location.pathname + location.search + hash); leer(); }

  function consultaDe(txt) {
    var q = {};
    if (!txt) return q;
    new URLSearchParams(txt).forEach(function (v, k) { q[k] = v; });
    return q;
  }

  function desconocida(original) {
    ruta.aviso = 'No existe la dirección «' + original + '». Te llevamos a Inicio.';
    sustituir('#/inicio');
  }

  function leer() {
    var h = location.hash;
    if (!h || h === '#' || h === '#/') { sustituir('#/inicio'); return; }
    var sinAlmohadilla = h.replace(/^#\/?/, '');
    var corte = sinAlmohadilla.indexOf('?');
    var camino = corte === -1 ? sinAlmohadilla : sinAlmohadilla.slice(0, corte);
    var consulta = consultaDe(corte === -1 ? '' : sinAlmohadilla.slice(corte + 1));
    var trozos = camino.split('/').filter(Boolean);
    var nombre = trozos[0] || '';

    if (GENERALES.indexOf(nombre) !== -1 && trozos.length === 1) {
      ruta.nombre = nombre; ruta.id = ''; ruta.pestana = ''; ruta.clave = nombre;
    } else if (nombre === 'obra' && trozos.length >= 2 && trozos.length <= 3) {
      var id; try { id = decodeURIComponent(trozos[1]); } catch (e) { desconocida(h); return; }
      var pestana = trozos[2] || '';
      if (!pestana) { sustituir('#/obra/' + encodeURIComponent(id) + '/resumen'); return; }
      if (!PESTANAS.some(function (p) { return p[0] === pestana; })) { desconocida(h); return; }
      ruta.nombre = 'obra'; ruta.id = id; ruta.pestana = pestana; ruta.clave = 'obra/' + id;
    } else {
      desconocida(h); return;
    }
    if (ruta.nombre !== 'inicio') ruta.aviso = '';
    ruta.consulta = consulta; ruta.hash = h;
  }

  C.rutas = {
    ruta: ruta,
    PESTANAS: PESTANAS,
    irA: irA,
    hashObra: function (id, pestana) { return '#/obra/' + encodeURIComponent(id) + '/' + (pestana || 'resumen'); },
    iniciar: function () { window.addEventListener('hashchange', leer); leer(); }
  };
})();
