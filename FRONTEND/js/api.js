/* CATDIC-WEB · cliente de la API (rutas relativas, mismo origen que sirve el tablero).
   - get / post / put / patch / del con JSON; enviarFormulario para multipart.
   - Cada petición tiene un tiempo límite (AbortController). Ningún POST se reintenta solo.
   - Los errores llegan como objeto { estado, mensaje, detalle }:
       estado  = código HTTP, o 0 si no hubo respuesta (sin conexión o tiempo agotado)
       mensaje = texto en español legible (sale del `detail` de FastAPI cuando existe)
       detalle = el `detail` original, tal cual, por si la pantalla necesita más.
   Cubre las 26 combinaciones de método y ruta de PLANES/etapa-5-inventario-ui.md §5: B3 agrega
   funciones con nombre encima de estas, no hace falta una por ruta. */
(function () {
  'use strict';
  window.CATDIC = window.CATDIC || {};

  var TIEMPO_LECTURA = 15000;   // GET
  var TIEMPO_ESCRITURA = 60000; // POST, PUT, PATCH, DELETE y formularios

  function error(estado, mensaje, detalle) { return { estado: estado, mensaje: mensaje, detalle: detalle === undefined ? null : detalle }; }

  // El `detail` de FastAPI es un texto (HTTPException) o una lista de errores de validación (422).
  function mensajeDe(estado, detalle) {
    if (typeof detalle === 'string' && detalle.trim()) return detalle;
    if (Array.isArray(detalle) && detalle.length) {
      var partes = detalle.map(function (d) {
        if (typeof d === 'string') return d;
        var donde = Array.isArray(d && d.loc) ? d.loc.filter(function (x) { return x !== 'body' && x !== 'query'; }).join('.') : '';
        var que = d && d.msg ? d.msg : 'valor no válido';
        return donde ? donde + ': ' + que : que;
      });
      return 'Dato no válido. ' + partes.join('; ');
    }
    if (estado === 404) return 'No se encontró lo que se pidió.';
    if (estado === 409) return 'La acción choca con el estado actual del registro.';
    if (estado === 422) return 'Dato no válido.';
    if (estado >= 500) return 'El servidor local tuvo un error interno.';
    return 'El servidor local respondió con un error (' + estado + ').';
  }

  function url(ruta, consulta) {
    if (!consulta) return ruta;
    var q = new URLSearchParams();
    Object.keys(consulta).forEach(function (k) {
      var v = consulta[k];
      if (v !== undefined && v !== null && v !== '') q.append(k, String(v));
    });
    var s = q.toString();
    return s ? ruta + (ruta.indexOf('?') === -1 ? '?' : '&') + s : ruta;
  }

  /* pedir(metodo, ruta, opciones)
     opciones: { cuerpo (objeto JSON), formulario (FormData), consulta (objeto), tiempo (ms), respuesta ('json' | 'blob'),
               senal (AbortSignal: al abortarla se corta la petición y el error trae `cancelada: true`) } */
  function pedir(metodo, ruta, opciones) {
    var o = opciones || {};
    var control = new AbortController();
    var tiempo = o.tiempo || (metodo === 'GET' ? TIEMPO_LECTURA : TIEMPO_ESCRITURA);
    var agotado = false;
    var cancelada = false;
    var reloj = setTimeout(function () { agotado = true; control.abort(); }, tiempo);
    if (o.senal) {
      var cortar = function () { cancelada = true; control.abort(); };
      if (o.senal.aborted) cortar(); else o.senal.addEventListener('abort', cortar, { once: true });
    }
    function sinRespuesta() {
      if (cancelada) { var c = error(0, 'La petición se canceló.', null); c.cancelada = true; return c; }
      return agotado ? error(0, 'El servidor local tardó demasiado en responder.', null) : error(0, 'No se pudo conectar con el servidor local.', null);
    }
    var init = { method: metodo, signal: control.signal, headers: { 'Accept': 'application/json' } };
    if (o.formulario) {
      init.body = o.formulario; // el navegador pone el boundary del multipart
    } else if (o.cuerpo !== undefined) {
      init.headers['Content-Type'] = 'application/json';
      init.body = JSON.stringify(o.cuerpo);
    }
    return fetch(url(ruta, o.consulta), init).then(function (r) {
      if (!r.ok) {
        return r.text().then(function (txt) {
          var detalle = null;
          try { var j = JSON.parse(txt); detalle = j && j.detail !== undefined ? j.detail : null; } catch (e) { detalle = null; }
          throw error(r.status, mensajeDe(r.status, detalle), detalle);
        });
      }
      if (r.status === 204) return null;
      if (o.respuesta === 'blob') return r.blob();
      return r.text().then(function (txt) {
        if (!txt) return null;
        try { return JSON.parse(txt); } catch (e) { throw error(r.status, 'El servidor local respondió algo que no se pudo leer.', null); }
      });
    }, function () {
      throw sinRespuesta();
    }).then(function (datos) { clearTimeout(reloj); return datos; }, function (e) {
      clearTimeout(reloj);
      if (e && typeof e.estado === 'number') throw e;
      throw sinRespuesta();
    });
  }

  window.CATDIC.api = {
    pedir: pedir,
    get: function (ruta, o) { return pedir('GET', ruta, o); },
    post: function (ruta, cuerpo, o) { return pedir('POST', ruta, Object.assign({}, o, { cuerpo: cuerpo })); },
    put: function (ruta, cuerpo, o) { return pedir('PUT', ruta, Object.assign({}, o, { cuerpo: cuerpo })); },
    patch: function (ruta, cuerpo, o) { return pedir('PATCH', ruta, Object.assign({}, o, { cuerpo: cuerpo })); },
    del: function (ruta, o) { return pedir('DELETE', ruta, o); },
    // Multipart (R10 planos, R13 visitas): `formulario` es un FormData; `metodo` por defecto POST.
    enviarFormulario: function (ruta, formulario, o) { return pedir((o && o.metodo) || 'POST', ruta, Object.assign({}, o, { formulario: formulario })); }
  };
})();
