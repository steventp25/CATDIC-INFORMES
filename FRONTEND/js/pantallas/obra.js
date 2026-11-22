/* CATDIC-WEB · pantalla de obra «#/obra/<id>/<pestaña>» (B2).
   Lectura real: la cabecera lee la obra de GET /api/dashboard (campo `proyectos`) y muestra su nombre y su cajetín.
   Cada campo que la respuesta no trae (vacío o «pendiente de verificar») se muestra como «pendiente de verificar».
   Las 6 pestañas navegan; el contenido de cada una es el estado vacío de la tarea de B3 que la construye. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.pantallas = C.pantallas || {};

  var F = function () { return C.formato; };
  // Qué tarea de B3 construye cada pestaña (PLANES/etapa-5-fase-B.md).
  var CONTENIDO = {
    resumen: { titulo: 'Resumen', tarea: 'B3b', texto: 'Aquí irán los indicadores y los pendientes de la obra. Los tres indicadores se calculan en la Fase D-b, tras la decisión D15, y nunca se mostrarán como 0 %.' },
    planos: { titulo: 'Planos y ficha', tarea: 'B3b', tarea2: 'B3c', texto: 'Aquí irán los planos, la ficha de la obra, el visor con recuadros y la revisión de los datos del plano.' },
    avance: { titulo: 'Avance', tarea: 'B3b', texto: 'Aquí irá el avance por entrepisos de la obra. Se calcula en la Fase D-b, tras la decisión D15; hasta entonces se muestra «pendiente de verificar» y nunca 0 %.' },
    informes: { titulo: 'Informes', tarea: 'B3g', texto: 'Aquí irán los informes de la obra que ya genera el sistema.' },
    cierre: { titulo: 'Cierre', tarea: 'B3b', texto: 'Aquí irá lo que falta para cerrar la obra: expediente completo y documentación al día. Ambos se calculan en la Fase D-b, tras la decisión D15; hasta entonces se muestran «pendiente de verificar».' }
  };

  C.pantallas['obra'] = {
    data: function () { return { estado: 'cargando', mensaje: '', datos: null, solicitud: 0 }; },
    computed: {
      ruta: function () { return C.rutas.ruta; },
      obra: function () {
        if (!this.datos) return null;
        var id = this.ruta.id;
        return (this.datos.proyectos || []).filter(function (p) { return p.id === id; })[0] || null;
      },
      estadoCab: function () {
        if (this.estado !== 'listo') return this.estado;
        return this.obra ? 'listo' : 'vacio';
      },
      titulo: function () { return this.obra ? this.obra.nombre : 'Obra'; },
      campos: function () {
        var o = this.obra, f = F().texto, fe = F().fecha;
        if (!o) return [];
        var visitas = (this.datos.visitas || []).filter(function (v) { return v.proyecto_id === o.id; });
        var fechas = visitas.map(function (v) { return fe(v.fecha_visita) ? String(v.fecha_visita).slice(0, 10) : null; }).filter(Boolean).sort();
        var ultima = fechas.length ? fe(fechas[fechas.length - 1]) : null;
        var pv = (this.datos.planos_vigentes || {})[o.id];
        var plano = pv ? (f(pv.etiqueta_revision) || (pv.revision != null ? 'Revisión ' + pv.revision : null)) : null;
        return [
          { etiqueta: 'Servicio', valor: f(o.tipo) },
          { etiqueta: 'Cliente', valor: f(o.cliente) },
          { etiqueta: 'Supervisor', valor: f(o.supervisor) },
          { etiqueta: 'Residente de obra', valor: f(o.residente_obra) },
          { etiqueta: 'N.º de solicitud', valor: f(o.no_solicitud) },
          { etiqueta: 'N.º de licencia', valor: f(o.no_licencia) },
          { etiqueta: 'Dirección', valor: f(o.direccion_obra) },
          { etiqueta: 'Sector', valor: f(o.sector) },
          { etiqueta: 'Provincia', valor: f(o.provincia) },
          { etiqueta: 'Inicio de obra', valor: fe(o.inicio_obra) },
          { etiqueta: 'Plano vigente', valor: plano },
          { etiqueta: 'Última visita', valor: ultima },
          { etiqueta: 'Visitas registradas', valor: visitas.length }
        ];
      },
      contenido: function () { return CONTENIDO[this.ruta.pestana] || CONTENIDO.resumen; }
    },
    created: function () { this.leer(); },
    watch: {
      // Otra obra (no otra pestaña de la misma): se vuelve a leer.
      'ruta.id': function () { this.leer(); }
    },
    methods: {
      leer: function (silencioso) {
        var self = this, n = ++this.solicitud;
        // Releer sin vaciar la pantalla (tras procesar, sincronizar o subir): la pestaña de visitas sigue montada.
        if (silencioso !== true) { this.estado = 'cargando'; this.mensaje = ''; this.datos = null; }
        C.api.get('/api/dashboard').then(function (d) {
          if (n !== self.solicitud) return;
          self.datos = d || {}; self.estado = 'listo';
        }, function (e) {
          if (n !== self.solicitud) return;
          if (silencioso === true) return;
          self.mensaje = e.mensaje; self.estado = 'error';
        });
      },
      releer: function () { this.leer(true); }
    },
    template:
      '<div class="pagina">' +
        '<header class="obra-cabeza">' +
          '<div class="obra-titulo">' +
            '<a class="miga" href="#/obras"><Icono nombre="volver"/>Mis obras</a>' +
            '<h1 tabindex="-1">{{ titulo }}</h1>' +
          '</div>' +
          '<Bloque :estado="estadoCab" :huesos="2" vacio-titulo="No se encontró la obra" ' +
            ':vacio-texto="\'No hay ninguna obra con el identificador «\' + ruta.id + \'».\'" accion-texto="Ir a Mis obras" accion-href="#/obras" ' +
            'error-titulo="No se pudo leer la obra." :error-mensaje="mensaje" @reintentar="leer">' +
            '<Cajetin :campos="campos"/>' +
          '</Bloque>' +
          '<PestanasObra v-if="obra" :id="obra.id" :activa="ruta.pestana"/>' +
        '</header>' +
        '<PestanaVisitas v-if="obra && ruta.pestana === \'visitas\'" :obra="obra" :datos="datos" @actualizar="releer"/>' +
        '<section v-else-if="obra" class="caja" :aria-labelledby="\'t-pestana\'">' +
          '<div class="caja-cabeza"><h2 id="t-pestana">{{ contenido.titulo }}</h2></div>' +
          '<div class="vacio">' +
            '<p class="vacio-t">Esta pestaña todavía no está construida.</p>' +
            '<p>{{ contenido.texto }}</p>' +
            '<p v-if="contenido.tarea">La construye la tarea <span class="num">{{ contenido.tarea }}</span><template v-if="contenido.tarea2"> y la <span class="num">{{ contenido.tarea2 }}</span></template> de la Fase B.</p>' +
          '</div>' +
        '</section>' +
      '</div>'
  };
})();
