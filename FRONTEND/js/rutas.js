/* CATDIC-WEB · enrutador por hash. El botón Atrás del navegador funciona porque cada pantalla es un hash.
   Generales:  #/inicio  #/obras  #/bandeja  #/informes  #/configuracion  #/crear-informe  #/ordenes
   Órdenes de trabajo (B3f):  #/ordenes[?obra=<id>][&tipo=Supervisión|Levantamiento][&estado=<estado>]  (solo lectura; el estado elegido en pantallas estrechas va en la dirección)
   De obra:    #/obra/<id>/<pestaña>   con pestaña = resumen | visitas | planos | avance | informes | cierre
   Editor de recuadros (B3b):  #/obra/<id>/planos?visor=1[&elemento=<uid>]   (también ?subir=1 abre «Subir planos»)
   Confirmar datos del plano (B3c):  #/obra/<id>/planos?confirmar=1[&tabla=<id de la tabla extraída>]
   Mesa de Dudas (B3e, vista con dirección propia):
               #/obra/<id>/visitas?visita=<vid>[&duda=<n>]   modo visita
               #/obra/<id>/resumen?dudas=obra[&duda=<n>]     modo obra (dudas sin visita)
   De trabajo: #/trabajo/<id>          avance en vivo del procesador de la cola (B3d); el id del trabajo va en la ruta
   Una ruta desconocida lleva a Inicio con un aviso (se sustituye en el historial, para que Atrás no vuelva a ella). */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};

  var GENERALES = ['inicio', 'obras', 'bandeja', 'informes', 'configuracion', 'crear-informe', 'ordenes'];
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

  var primera = true;
  function leer() {
    var antes = ruta.nombre === 'obra' && ruta.pestana === 'planos' && ruta.consulta && ruta.consulta.visor === '1';
    // B3c: ¿se venía de «Planos y ficha» a secas, de la misma obra? Solo entonces «Cerrar» puede volver con Atrás.
    var antesConfirmar = ruta.nombre === 'obra' && ruta.pestana === 'planos' && !!(ruta.consulta && ruta.consulta.confirmar === '1');
    var antesPlanos = ruta.nombre === 'obra' && ruta.pestana === 'planos' && !antes && !antesConfirmar;
    var antesId = ruta.id;
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
    } else if (nombre === 'trabajo' && trozos.length === 2) {
      var tid; try { tid = decodeURIComponent(trozos[1]); } catch (e2) { desconocida(h); return; }
      ruta.nombre = 'trabajo'; ruta.id = tid; ruta.pestana = ''; ruta.clave = 'trabajo/' + tid;
    } else {
      desconocida(h); return;
    }
    if (ruta.nombre !== 'inicio') ruta.aviso = '';
    ruta.consulta = consulta; ruta.hash = h;
    var ahora = ruta.nombre === 'obra' && ruta.pestana === 'planos' && consulta.visor === '1';
    if (ahora && !antes && !primera) C.rutas.vinoDeDentro = true;
    var ahoraConfirmar = ruta.nombre === 'obra' && ruta.pestana === 'planos' && consulta.confirmar === '1';
    if (ahoraConfirmar && !antesConfirmar) {
      C.rutas.vinoDeDentroConfirmar = !primera && antesPlanos && antesId === ruta.id;
      C.rutas.confirmarDesdeCarga = primera;   // B5a: al recargar con ?confirmar=1 no hay disparador: al cerrar el foco va al <h1>
    }
    primera = false;
  }

  C.rutas = {
    ruta: ruta,
    PESTANAS: PESTANAS,
    irA: irA,
    hashObra: function (id, pestana) { return '#/obra/' + encodeURIComponent(id) + '/' + (pestana || 'resumen'); },
    // La Mesa de Dudas en modo visita: «Visitas y trabajos» de su obra con ?visita=<id>. Con dudaId abre esa duda (&duda=<id>).
    hashVisita: function (obraId, visitaId, dudaId) {
      return '#/obra/' + encodeURIComponent(obraId) + '/visitas?visita=' + encodeURIComponent(visitaId) +
        (dudaId !== undefined && dudaId !== null && dudaId !== '' ? '&duda=' + encodeURIComponent(dudaId) : '');
    },
    // La Mesa de Dudas en modo obra (dudas sin visita): el Resumen de la obra con ?dudas=obra. Con dudaId abre esa duda.
    hashMesaObra: function (obraId, dudaId) {
      return '#/obra/' + encodeURIComponent(obraId) + '/resumen?dudas=obra' +
        (dudaId !== undefined && dudaId !== null && dudaId !== '' ? '&duda=' + encodeURIComponent(dudaId) : '');
    },
    hashTrabajo: function (id) { return '#/trabajo/' + encodeURIComponent(id); },
    // B3b · el editor de recuadros de «Planos y ficha»: #/obra/<id>/planos?visor=1[&elemento=<uid>]
    hashVisorPlano: function (obraId, uid) {
      return '#/obra/' + encodeURIComponent(obraId) + '/planos?visor=1' + (uid ? '&elemento=' + encodeURIComponent(uid) : '');
    },
    // B3c · «Confirmar datos del plano»: #/obra/<id>/planos?confirmar=1[&tabla=<id>]. La tabla elegida va en la dirección (recargar la conserva).
    hashConfirmarPlano: function (obraId, tablaId) {
      return '#/obra/' + encodeURIComponent(obraId) + '/planos?confirmar=1' + (tablaId !== undefined && tablaId !== null && tablaId !== '' ? '&tabla=' + encodeURIComponent(tablaId) : '');
    },
    // Cambia la dirección sin añadir una entrada al historial (p. ej. al elegir otro elemento en el editor).
    reemplazar: function (hash) { sustituir(hash); },
    // Verdadero si el editor se abrió navegando dentro del tablero (entonces «Cerrar» vuelve con Atrás, sin duplicar el historial);
    // falso si se cargó directo (recarga o enlace): «Cerrar» lleva a la pestaña sustituyendo la entrada.
    vinoDeDentro: false,
    // Igual para «Confirmar datos del plano»: verdadero solo si se entró desde «Planos y ficha» de la misma obra (Cerrar = Atrás).
    // Si se volvió de la Mesa de Dudas con Atrás, o se cargó directo, «Cerrar» lleva a «Planos y ficha» sustituyendo la entrada.
    vinoDeDentroConfirmar: false,
    confirmarDesdeCarga: false,
    iniciar: function () { window.addEventListener('hashchange', leer); leer(); }
  };
})();
