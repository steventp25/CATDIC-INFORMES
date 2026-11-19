/* CATDIC-WEB · datos compartidos de Inicio y Mis obras (B3a).
   Las dos pantallas leen las mismas rutas: GET /api/dashboard y GET /api/dudas?resuelta=false.
   Cada lectura tiene su propio estado (cargando | listo | error) y su propio «Reintentar»; si falla una,
   la otra sigue mostrándose. Nada se vuelve a pedir solo por tiempo. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};

  var DIA = 86400000;

  /* Fecha de hoy en DD/MM/AAAA (hora local). */
  function hoyTexto() {
    var d = new Date();
    function dos(n) { return (n < 10 ? '0' : '') + n; }
    return dos(d.getDate()) + '/' + dos(d.getMonth() + 1) + '/' + d.getFullYear();
  }

  /* Días desde una fecha AAAA-MM-DD (la de la visita) hasta hoy. Solo sale de un dato real: si no es una fecha
     reconocible devuelve null y la pantalla muestra «pendiente de verificar». */
  function diasDesde(fecha) {
    var m = typeof fecha === 'string' ? /^(\d{4})-(\d{2})-(\d{2})/.exec(fecha) : null;
    if (!m) return null;
    var f = new Date(+m[1], +m[2] - 1, +m[3]);
    if (isNaN(f.getTime()) || f.getMonth() !== +m[2] - 1) return null;
    var h = new Date(); h = new Date(h.getFullYear(), h.getMonth(), h.getDate());
    return Math.round((h.getTime() - f.getTime()) / DIA);
  }

  function plural(n, uno, varios) { return n + ' ' + (n === 1 ? uno : varios); }

  /* Prioridades de Inicio: filas con datos reales, ordenadas por bloqueante → «Con dudas» → cola.
       - visita con estado «Con dudas» o con dudas bloqueantes abiertas
       - dudas de obra (sin visita)
       - visita en cola (Sin procesar / En cola) sin dudas listadas
     `dudas` es null si no se pudieron leer: entonces solo se usa el estado de la visita. */
  function prioridades(tablero, dudas) {
    var proy = {}, filas = [], listaDudas = dudas || [];
    (tablero.proyectos || []).forEach(function (p) { proy[p.id] = p; });
    var nombreObra = function (id) { return proy[id] ? proy[id].nombre : id; };
    var porVisita = {}, deObra = {}, vistas = {};
    listaDudas.forEach(function (d) {
      if (d.visita_id) (porVisita[d.visita_id] = porVisita[d.visita_id] || []).push(d);
      else (deObra[d.proyecto_id] = deObra[d.proyecto_id] || []).push(d);
    });
    function cuenta(ds) {
      var bq = ds.filter(function (d) { return d.categoria === 'DUDA_BLOQUEANTE'; }).length;
      return { bq: bq, otras: ds.length - bq };
    }
    function textoDudas(c) {
      var t = [];
      if (c.bq) t.push(plural(c.bq, 'duda bloqueante abierta', 'dudas bloqueantes abiertas'));
      if (c.otras) t.push(plural(c.otras, 'hallazgo o duda abierta', 'hallazgos o dudas abiertas'));
      return t.join(' · ');
    }
    function enlaceVisita(pid, vid) { return C.rutas.hashObra(pid, 'visitas') + '?visita=' + encodeURIComponent(vid); }

    (tablero.visitas || []).forEach(function (v) {
      vistas[v.id] = true;
      var ds = porVisita[v.id] || [], c = cuenta(ds);
      var conDudas = v.estado === 'Con dudas' || c.bq > 0;
      var cola = v.estado === 'Sin procesar' || v.estado === 'En cola';
      if (!conDudas && !cola) return;
      var num = v.numero !== null && v.numero !== undefined && v.numero !== '' ? 'Visita ' + v.numero : 'Visita';
      var donde = num + (C.formato.texto(v.nombre_carpeta) ? ' · ' + v.nombre_carpeta : '');
      var f = {
        clave: 'v:' + v.id, obraId: v.proyecto_id, obra: nombreObra(v.proyecto_id), donde: donde,
        href: enlaceVisita(v.proyecto_id, v.id), dias: diasDesde(v.fecha_visita), fecha: C.formato.fecha(v.fecha_visita)
      };
      if (c.bq > 0) {
        f.rango = 0; f.bloq = true; f.tipo = 'Duda bloqueante'; f.motivo = textoDudas(c); f.siguiente = 'Responder las dudas de la visita';
      } else if (conDudas) {
        f.rango = 1; f.tipo = 'Visita con dudas';
        f.motivo = ds.length ? textoDudas(c) : (dudas === null ? 'Estado «Con dudas» (no se pudieron leer las dudas)' : 'Estado «Con dudas»');
        f.siguiente = ds.length ? 'Responder las dudas de la visita' : 'Revisar la visita';
      } else {
        f.rango = 2; f.tipo = 'Visita en cola'; f.motivo = 'Estado «' + v.estado + '»: falta procesarla'; f.siguiente = 'Abrir la visita';
      }
      filas.push(f);
    });
    // Dudas de una visita que el tablero no trae: se listan con lo que dice la propia duda.
    Object.keys(porVisita).forEach(function (vid) {
      if (vistas[vid]) return;
      var ds = porVisita[vid], c = cuenta(ds), d0 = ds[0];
      filas.push({
        clave: 'v:' + vid, obraId: d0.proyecto_id, obra: nombreObra(d0.proyecto_id),
        donde: (d0.visita_numero != null ? 'Visita ' + d0.visita_numero : 'Visita') + (C.formato.texto(d0.visita_carpeta) ? ' · ' + d0.visita_carpeta : ''),
        href: enlaceVisita(d0.proyecto_id, vid), dias: null, fecha: null,
        rango: c.bq ? 0 : 1, bloq: c.bq > 0, tipo: c.bq ? 'Duda bloqueante' : 'Visita con dudas',
        motivo: textoDudas(c), siguiente: 'Responder las dudas de la visita'
      });
    });
    Object.keys(deObra).forEach(function (pid) {
      var ds = deObra[pid], c = cuenta(ds);
      filas.push({
        clave: 'o:' + pid, obraId: pid, obra: nombreObra(pid), donde: 'Dudas de la obra (sin visita)',
        href: C.rutas.hashObra(pid, 'resumen'), dias: null, fecha: null,
        rango: c.bq ? 0 : 1, bloq: c.bq > 0, tipo: 'Duda de obra', motivo: textoDudas(c), siguiente: 'Responder las dudas de la obra'
      });
    });
    filas.sort(function (a, b) {
      if (a.rango !== b.rango) return a.rango - b.rango;
      var da = a.dias === null ? -Infinity : a.dias, db = b.dias === null ? -Infinity : b.dias;
      if (da !== db) return db - da;
      return a.obra.localeCompare(b.obra, 'es') || a.donde.localeCompare(b.donde, 'es', { numeric: true });
    });
    return filas;
  }

  /* Mixin con las dos lecturas. Las pantallas lo usan y añaden lo suyo. */
  var mixin = {
    data: function () {
      return {
        estadoTablero: 'cargando', mensajeTablero: '', tablero: null, nTablero: 0,
        estadoDudas: 'cargando', mensajeDudas: '', dudas: null, nDudas: 0
      };
    },
    computed: {
      proyectos: function () { return this.tablero && Array.isArray(this.tablero.proyectos) ? this.tablero.proyectos : []; },
      visitasTodas: function () { return this.tablero && Array.isArray(this.tablero.visitas) ? this.tablero.visitas : []; },
      stats: function () { return (this.tablero && this.tablero.stats) || {}; },
      planos: function () { return (this.tablero && this.tablero.planos_vigentes) || {}; },
      obrasOrdenadas: function () {
        return this.proyectos.slice().sort(function (a, b) { return String(a.nombre).localeCompare(String(b.nombre), 'es'); });
      }
    },
    created: function () { this.leerTablero(); this.leerDudas(); },
    methods: {
      leerTablero: function () {
        var self = this, n = ++this.nTablero;
        this.estadoTablero = 'cargando'; this.mensajeTablero = '';
        return C.api.get('/api/dashboard').then(function (d) {
          if (n !== self.nTablero) return;
          self.tablero = d || {}; self.estadoTablero = 'listo';
        }, function (e) {
          if (n !== self.nTablero) return;
          self.mensajeTablero = e.mensaje; self.estadoTablero = 'error';
        });
      },
      leerDudas: function () {
        var self = this, n = ++this.nDudas;
        this.estadoDudas = 'cargando'; this.mensajeDudas = '';
        return C.api.get('/api/dudas', { consulta: { resuelta: 'false' } }).then(function (d) {
          if (n !== self.nDudas) return;
          self.dudas = Array.isArray(d) ? d : []; self.estadoDudas = 'listo';
        }, function (e) {
          if (n !== self.nDudas) return;
          self.mensajeDudas = e.mensaje; self.estadoDudas = 'error';
        });
      },
      recargar: function () { this.leerTablero(); this.leerDudas(); }
    }
  };

  C.datos = { mixin: mixin, prioridades: prioridades, hoyTexto: hoyTexto, diasDesde: diasDesde, plural: plural };
})();
