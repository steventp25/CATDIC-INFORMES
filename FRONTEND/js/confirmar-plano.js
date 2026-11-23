/* CATDIC-WEB · «Confirmar datos del plano» (B3c). Es la pantalla M6 del inventario (A45–A51) con ruta propia:
     #/obra/<id>/planos?confirmar=1[&tabla=<id de la tabla extraída>]
   Pantalla completa (un <dialog> modal, como el editor de recuadros de B3b): barra superior, lista de tablas y detalle de la tabla elegida.
   En 1024 px o más (de la propia pantalla) la lista queda a la izquierda y el detalle a la derecha; en estrecho son pasos
   (lista → tabla) con «Volver a las tablas», que no pierde la selección.

   props   obra (Object, obligatoria: fila de `proyectos`)
   eventos cerrar · actualizar (cambió algo en el servidor: la pantalla de la obra relee el tablero)

   Rutas del servidor (solo se leen, no se modifican):
     POST …/extraer-diseno                      (A45)  → { revision, tablas[], elementos:{propuestos}, dudas_creadas, dudas_cerradas }
     GET  …/tablas-extraidas                    (R22)  → { tablas: [...] }
     GET  …/tablas-extraidas/{id}               (R23)  → detalle con comprobaciones, campos, recorte, confirmable, certificable…
     POST …/visor/vista-previa {tipo:'detalle', pagina, rect}  (A46, imagen) → el recorte de la tabla
     POST …/tablas-extraidas/{id}/certificar-notas {certifico:true, extraido_en}  (A47)
     POST …/tablas-extraidas/{id}/confirmar {confirmo:true, extraido_en}          (A48)
     GET  /api/dudas?sin_visita=true&proyecto_id=…   (A49, solo para contar las dudas abiertas de la obra)

   Regla de Oro: nada se confirma ni se certifica solo; cada acción pide su casilla («Revisé…», «Certifico…») y el botón queda
   deshabilitado sin ella. Un valor sin fuente o que no coincide con la tabla se muestra «pendiente de verificar», con salida a la
   Mesa de Dudas. Un elemento se identifica por su `uid`, nunca por `id_elemento` (el mismo ID se repite en varios niveles).
   Un 409 o un 422 del servidor muestra su `detail` tal cual. Ningún POST se reintenta solo ni se envía dos veces. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};

  var NOMBRES = { acero_en_losa: 'Acero en losa', zapata_muro_lindero: 'Zapata de muro lindero', fc_por_rango: 'f\'c por rango', losa_aligerada: 'Losa aligerada' };
  var contador = 0;

  function enc(s) { return encodeURIComponent(s); }
  function soltar(u) { if (u) { try { URL.revokeObjectURL(u); } catch (e) { /* nada */ } } }
  function bboxOk(b) { return Array.isArray(b) && b.length === 4 && b.every(function (v) { return typeof v === 'number' && isFinite(v); }); }
  function nombreTabla(t) { return NOMBRES[t] || (t === null || t === undefined || t === '' ? 'pendiente de verificar' : String(t)); }
  function num(v) { return typeof v === 'number' && isFinite(v) ? String(v) : '(pendiente de verificar)'; }
  /* Cada comprobación tiene dos textos legibles en vez de la clave del servidor:
     [0] un nombre neutro para la lista «Comprobaciones» (vale tanto si cumple como si falla);
     [1] la frase de falla, solo para «Falla:» y «Falló:».
     Salen de BACKEND/plano/extractor.py (qué comprueba cada una). Para una clave desconocida solo se cambian los «_» por espacios
     y se pone la primera en mayúscula, sin inventar su significado. La clave original queda en `title` y en `data-clave`. */
  var COMPROBACIONES = {
    celdas_completas: ['Celdas completas', 'Hay celdas vacías o fuera de la tabla'],
    unidades: ['Unidades y rangos', 'Hay valores fuera de la unidad o del rango esperado'],
    total_de_barras: ['Formato de barras', 'Hay acero que no tiene el formato de barras esperado'],
    ids_duplicados: ['Sin filas repetidas', 'Hay filas repetidas'],
    espesor_total: ['H = h1 + h2', 'H no es igual a h1 + h2'],
    rangos_expandidos: ['Rangos de niveles expandidos', 'Hay rangos de niveles que no se pudieron expandir'],
    rangos_sin_choque: ["Un solo f'c por nivel (E-n)", "Un mismo nivel (E-n) queda con dos f'c distintos"],
    igual_en_todas_las_hojas: ['Igual en todas las hojas', 'La tabla no es igual en todas las hojas'],
    nivel_impreso: ['Un único nivel impreso', 'La hoja no tiene un único nivel impreso'],
    ids_en_planta_sin_duplicados: ['IDs de losa sin repetir', 'Hay IDs de losa repetidos en la planta'],
    losa_tipo_asignado: ['Tipo de losa asignado', 'Hay losas sin tipo asignado'],
    sin_notas_de_modificacion: ['Sin notas de modificación', 'La hoja tiene notas de modificación']
  };
  function textoComprobacion(k, cual) {
    var c = String(k === null || k === undefined ? '' : k);
    if (!c) return 'pendiente de verificar';
    if (COMPROBACIONES[c]) return COMPROBACIONES[c][cual];
    var t = c.replace(/_/g, ' ').trim();
    return t ? t.charAt(0).toUpperCase() + t.slice(1) : 'pendiente de verificar';
  }
  function nombreComprobacion(k) { return textoComprobacion(k, 0); }
  function fallaLegible(k) { return textoComprobacion(k, 1); }
  function fallasClaves(t) { return (t.comprobaciones || []).filter(function (c) { return !c.ok; }).map(function (c) { return c.comprobacion; }); }
  function fallas(t) { return fallasClaves(t).map(fallaLegible).join('; '); }

  C.componentes.ConfirmarPlano = {
    props: { obra: { type: Object, required: true } },
    emits: ['cerrar', 'actualizar'],
    data: function () {
      contador++;
      return {
        uid: 'cf' + contador, apertura: null, cerrado: false,
        estadoL: 'cargando', mensajeL: '', tablas: [], nL: 0,
        selId: null, estadoT: 'ninguna', mensajeT: '', det: null, nT: 0, avisoTabla: '',
        urlRecorte: '', cargandoRecorte: false, errorRecorte: '', nR: 0,
        hoverBbox: null, focoBbox: null, textoCelda: '', filaActiva: 0,
        revisado: false, certifico: false, enviando: '',
        error: '', mensaje: '',
        nDudas: null, estadoD: 'cargando', nD: 0,
        paso: 'lista', verPlano: false
      };
    },
    computed: {
      ruta: function () { return C.rutas.ruta; },
      tablaRuta: function () { var t = this.ruta.consulta && this.ruta.consulta.tabla; return t ? String(t) : ''; },
      hrefMesa: function () { return C.rutas.hashMesaObra(this.obra.id); },
      textoDudas: function () {
        if (this.estadoD === 'cargando') return '…';
        return this.nDudas === null ? 'no se pudieron contar' : this.nDudas + (this.nDudas === 1 ? ' abierta' : ' abiertas');
      },
      sel: function () { var id = this.selId; return id === null ? null : (this.tablas.filter(function (t) { return t.id === id; })[0] || null); },
      resaltado: function () { return this.hoverBbox || this.focoBbox || null; },
      caja: function () {
        var d = this.det, b = this.resaltado;
        if (!d || !bboxOk(d.recorte) || !bboxOk(b)) return null;
        var x0 = d.recorte[0], y0 = d.recorte[1], w = d.recorte[2] - x0, h = d.recorte[3] - y0;
        if (w <= 0 || h <= 0) return null;
        function pc(v) { return Math.max(0, Math.min(100, v)) + '%'; }
        return { left: pc((b[0] - x0) / w * 100), top: pc((b[1] - y0) / h * 100), width: pc((b[2] - b[0]) / w * 100), height: pc((b[3] - b[1]) / h * 100) };
      },
      campos: function () { return this.det && Array.isArray(this.det.campos) ? this.det.campos : []; },
      pendientes: function () { return this.campos.filter(function (x) { return x.estado !== 'confirmado'; }).length; },
      dudosos: function () {
        return this.campos.filter(function (x) {
          return x.estado !== 'confirmado' && (x.valor_tabla === null || x.valor_tabla === undefined || x.valor_tabla === '' || x.valor !== x.valor_tabla);
        }).length;
      },
      comprobaciones: function () { return this.det && Array.isArray(this.det.comprobaciones) ? this.det.comprobaciones : []; },
      notas: function () {
        var out = [];
        this.comprobaciones.forEach(function (c) { if (c.comprobacion === 'sin_notas_de_modificacion' && Array.isArray(c.detalle)) c.detalle.forEach(function (n) { out.push(n); }); });
        return out;
      },
      motivosNo: function () { return this.det && Array.isArray(this.det.motivos_no_confirmable) ? this.det.motivos_no_confirmable : []; },
      cuentaTablas: function () { return C.cola.plural(this.tablas.length, 'tabla', 'tablas'); }
    },
    watch: {
      // Atrás / Adelante del navegador: la tabla de la dirección manda
      tablaRuta: function (v) {
        if (v === (this.selId === null ? '' : String(this.selId))) return;
        if (!v) { this.deseleccionar(); return; }
        this.abrirDesdeRuta(v);
      }
    },
    created: function () {
      this.paso = this.tablaRuta ? 'tabla' : 'lista';
      var self = this;
      this.leerDudas();
      this.leerTablas().then(function () { if (self.tablaRuta) self.abrirDesdeRuta(self.tablaRuta); });
    },
    mounted: function () {
      this.apertura = document.activeElement;
      var dlg = this.$refs.dlg;
      if (dlg && dlg.showModal) dlg.showModal(); else if (dlg) dlg.setAttribute('open', '');
      var t = this.$refs.titulo; if (t) t.focus({ preventScroll: true });   // no se enfoca «Extraer»: un Enter suelto no debe lanzar una extracción
    },
    beforeUnmount: function () {
      this.nT++; this.nR++;
      soltar(this.urlRecorte); this.urlRecorte = '';   // A51: se libera la URL del recorte al cerrar
      // B5a: el foco vuelve a lo que abrió el diálogo. Si no hay disparador (se llegó de vuelta desde la Mesa, o se recargó con ?confirmar=1),
      // vuelve al enlace «Confirmar datos del plano» de la pestaña y, tras una recarga, al <h1>. Nunca queda en el <body>.
      var a = this.apertura; this.apertura = null;
      var utilA = a && a !== document.body && a !== document.documentElement && a.isConnected && a.focus;
      if (utilA) { a.focus({ preventScroll: true }); return; }
      var destino = (!C.rutas.confirmarDesdeCarga && document.querySelector('[data-confirmar-plano]:not([disabled])')) || document.querySelector('main h1');
      if (destino) destino.focus({ preventScroll: true });
    },
    methods: {
      nombre: nombreTabla,
      fallas: fallas,
      fallasClaves: fallasClaves,
      nombreComprobacion: nombreComprobacion,
      bboxOk: bboxOk,
      fh: function (v) { return C.formato.fechaHora(v); },
      txt: function (v) { return C.formato.texto(v); },
      insignia: function (r) {
        if (r === 'verde') return { clase: 'est-ok', icono: 'check', texto: 'verde' };
        if (r === 'rojo') return { clase: 'est-mal', icono: 'alerta', texto: 'rojo' };
        return { clase: 'est-sin', icono: 'info', texto: 'pendiente de verificar' };
      },
      // ---- diálogo ----
      atrapar: function (ev) {
        var dlg = this.$refs.dlg; if (!dlg) return;
        var f = [].slice.call(dlg.querySelectorAll('a[href], button, input, select, textarea, [tabindex]')).filter(function (x) { return !x.disabled && x.tabIndex >= 0 && x.offsetParent !== null; });
        if (!f.length) return;
        var primero = f[0], ultimo = f[f.length - 1];
        if (ev.shiftKey && document.activeElement === primero) { ev.preventDefault(); ultimo.focus(); }
        else if (!ev.shiftKey && document.activeElement === ultimo) { ev.preventDefault(); primero.focus(); }
      },
      cerrar: function () {
        var dlg = this.$refs.dlg;
        this.cerrado = true;
        if (dlg && dlg.open && dlg.close) dlg.close();
        this.$emit('cerrar');
      },
      alCerrar: function () { if (!this.cerrado) { this.cerrado = true; this.$emit('cerrar'); } },
      // ---- lecturas ----
      leerTablas: function () {
        var self = this, n = ++this.nL;
        this.estadoL = this.tablas.length ? this.estadoL : 'cargando'; this.mensajeL = '';
        return C.api.get('/api/proyectos/' + enc(this.obra.id) + '/tablas-extraidas').then(function (r) {
          if (n !== self.nL) return;
          if (!r || !Array.isArray(r.tablas)) { self.mensajeL = 'El servidor respondió algo que no se pudo leer.'; self.estadoL = 'error'; return; }
          self.tablas = r.tablas; self.estadoL = 'listo';
        }, function (e) {
          if (n !== self.nL) return;
          self.mensajeL = (e && e.mensaje) || 'No se pudieron leer las tablas.'; self.estadoL = 'error';
        });
      },
      leerDudas: function () {
        var self = this, n = ++this.nD;
        this.estadoD = 'cargando';
        return C.api.get('/api/dudas', { consulta: { resuelta: 'false', sin_visita: 'true', proyecto_id: this.obra.id } }).then(function (d) {
          if (n !== self.nD) return;
          self.nDudas = Array.isArray(d) ? d.length : null; self.estadoD = 'listo';
        }, function () {
          if (n !== self.nD) return;
          self.nDudas = null; self.estadoD = 'error';
        });
      },
      // Elegir una tabla (A46): GET del detalle y, si trae recorte, la vista previa del plano
      abrirDesdeRuta: function (v) {
        var id = parseInt(v, 10);
        if (!isFinite(id) || String(id) !== String(v) || !this.tablas.some(function (t) { return t.id === id; })) {
          this.avisoTabla = 'La tabla de la dirección («' + v + '») ya no está entre las tablas extraídas del plano vigente.';
          this.selId = null; this.det = null; this.estadoT = 'ninguna'; this.soltarRecorte();
          C.rutas.reemplazar(C.rutas.hashConfirmarPlano(this.obra.id));
          return;
        }
        this.avisoTabla = '';
        this.paso = 'tabla';
        this.abrirTabla(id);
      },
      elegir: function (t) {
        this.error = ''; this.mensaje = ''; this.avisoTabla = '';
        this.paso = 'tabla';
        if (this.selId !== t.id) C.rutas.reemplazar(C.rutas.hashConfirmarPlano(this.obra.id, t.id));
        this.abrirTabla(t.id);
      },
      deseleccionar: function () {
        this.nT++; this.selId = null; this.det = null; this.estadoT = 'ninguna'; this.soltarRecorte(); this.paso = 'lista';
        this.revisado = false; this.certifico = false; this.hoverBbox = null; this.focoBbox = null;
      },
      volverALista: function () { this.paso = 'lista'; },
      abrirTabla: function (id) {
        var self = this, n = ++this.nT;
        this.selId = id; this.estadoT = 'cargando'; this.mensajeT = ''; this.det = null;
        this.revisado = false; this.certifico = false; this.hoverBbox = null; this.focoBbox = null; this.textoCelda = ''; this.filaActiva = 0;
        this.soltarRecorte();
        return C.api.get('/api/proyectos/' + enc(this.obra.id) + '/tablas-extraidas/' + enc(id)).then(function (d) {
          if (n !== self.nT) return;
          if (!d || typeof d !== 'object') { self.mensajeT = 'El servidor respondió algo que no se pudo leer.'; self.estadoT = 'error'; return; }
          self.det = d; self.estadoT = 'listo';
          self.cargarRecorte();
        }, function (e) {
          if (n !== self.nT) return;
          self.mensajeT = (e && e.mensaje) || 'No se pudo leer la tabla.'; self.estadoT = 'error';
        });
      },
      reintentarTabla: function () { if (this.selId !== null) this.abrirTabla(this.selId); },
      soltarRecorte: function () {
        this.nR++; soltar(this.urlRecorte); this.urlRecorte = ''; this.cargandoRecorte = false; this.errorRecorte = '';
      },
      cargarRecorte: function () {
        var self = this, d = this.det, n = ++this.nR;
        soltar(this.urlRecorte); this.urlRecorte = ''; this.errorRecorte = '';
        if (!d || !bboxOk(d.recorte) || !d.pagina) { this.cargandoRecorte = false; return; }
        this.cargandoRecorte = true;
        C.api.pedir('POST', '/api/proyectos/' + enc(this.obra.id) + '/visor/vista-previa', { cuerpo: { tipo: 'detalle', pagina: d.pagina, rect: d.recorte }, respuesta: 'blob', tiempo: 90000 }).then(function (blob) {
          if (n !== self.nR) return;
          self.cargandoRecorte = false; self.urlRecorte = URL.createObjectURL(blob);
        }, function (e) {
          if (n !== self.nR) return;
          self.cargandoRecorte = false; self.errorRecorte = (e && e.mensaje) || 'No se pudo generar el recorte del plano.';
        });
      },
      // ---- resaltar la celda (A50): ratón y teclado ----
      textoDe: function (x) { return x.id_elemento + ' · ' + x.campo + (x.fuente && x.fuente.fila ? ' (fila ' + x.fuente.fila + ')' : ''); },
      entra: function (x) { this.hoverBbox = bboxOk(x.fuente && x.fuente.bbox) ? x.fuente.bbox : null; this.textoCelda = this.hoverBbox ? 'Celda resaltada: ' + this.textoDe(x) + '.' : 'Esta celda no tiene posición en el recorte.'; },
      sale: function () { this.hoverBbox = null; if (!this.focoBbox) this.textoCelda = ''; },
      enfoca: function (x, i) { this.filaActiva = i; this.focoBbox = bboxOk(x.fuente && x.fuente.bbox) ? x.fuente.bbox : null; this.textoCelda = this.focoBbox ? 'Celda resaltada: ' + this.textoDe(x) + '.' : 'Esta celda no tiene posición en el recorte.'; },
      desenfoca: function () { this.focoBbox = null; if (!this.hoverBbox) this.textoCelda = ''; },
      teclasFilas: function (ev) {
        var k = ev.key;
        if (k !== 'ArrowDown' && k !== 'ArrowUp' && k !== 'Home' && k !== 'End') return;
        var filas = this.$el.querySelectorAll('[data-campo]');
        if (!filas.length) return;
        var i = this.filaActiva;
        if (k === 'ArrowDown') i = Math.min(filas.length - 1, i + 1); else if (k === 'ArrowUp') i = Math.max(0, i - 1);
        else if (k === 'Home') i = 0; else i = filas.length - 1;
        ev.preventDefault();
        this.filaActiva = i;
        this.$nextTick(function () { if (filas[i]) filas[i].focus(); });
      },
      // ---- valores: lo que difiere de la tabla o no tiene fuente es «pendiente de verificar» (N19) ----
      valorCelda: function (x) { return C.formato.texto(x.valor); },
      sinFuente: function (x) { return x.valor_tabla === null || x.valor_tabla === undefined || x.valor_tabla === ''; },
      difiere: function (x) { return !this.sinFuente(x) && x.valor !== x.valor_tabla; },
      certificadaTexto: function (c) {
        var q = c.certificada || {};
        return '(certificada por ' + (this.txt(q.por) || 'pendiente de verificar') + ' el ' + (this.fh(q.en) || 'pendiente de verificar') +
          ' para el vectorial ' + (typeof q.sha256 === 'string' && q.sha256 ? q.sha256.slice(0, 12) + '…' : 'pendiente de verificar') + ')';
      },
      // ---- A45: extraer del plano vigente ----
      extraer: function () {
        var self = this;
        if (this.enviando) return;
        this.enviando = 'extraer'; this.error = ''; this.mensaje = '';
        C.api.post('/api/proyectos/' + enc(this.obra.id) + '/extraer-diseno', undefined, { tiempo: 300000 }).then(function (d) {
          d = d || {};
          var tablas = Array.isArray(d.tablas) ? d.tablas : [];
          var verdes = tablas.filter(function (t) { return t.resultado === 'verde'; }).length;
          self.mensaje = 'Extracción rev. ' + (d.revision !== undefined && d.revision !== null ? d.revision : '(pendiente de verificar)') + ': ' + tablas.length + ' tablas (' + verdes + ' en verde), ' +
            num(d.elementos && d.elementos.propuestos) + ' elementos propuestos, ' + num(d.dudas_creadas) + ' dudas nuevas, ' + num(d.dudas_cerradas) +
            ' cerradas. Todo queda pendiente hasta que lo confirmes.';
          C.visor.olvidar(self.obra.id);   // los elementos cambiaron: el visor de revisión no debe usar los de antes
          self.deseleccionar();
          C.rutas.reemplazar(C.rutas.hashConfirmarPlano(self.obra.id));
        }, function (e) { self.error = (e && e.mensaje) || 'No se pudo extraer del plano vigente.'; }).then(function () {
          self.enviando = '';
          self.leerTablas(); self.leerDudas(); self.$emit('actualizar');
        });
      },
      // ---- A47: certificar las notas de modificación ----
      certificar: function () {
        var self = this, d = this.det;
        if (!d || !this.certifico || this.enviando) return;
        var id = d.id;
        this.enviando = 'certificar'; this.error = ''; this.mensaje = '';
        C.api.post('/api/proyectos/' + enc(this.obra.id) + '/tablas-extraidas/' + enc(id) + '/certificar-notas', { certifico: true, extraido_en: d.extraido_en }, { tiempo: 120000 }).then(function (r) {
          r = r || {};
          var sha = typeof r.sha256 === 'string' ? r.sha256.slice(0, 12) + '…' : '(pendiente de verificar)';
          var cerradas = Array.isArray(r.dudas_cerradas) ? r.dudas_cerradas.length : 0;
          self.mensaje = 'Tabla ' + (r.tabla || '(pendiente de verificar)') + ' certificada para el vectorial ' + sha + ': queda en ' + (r.resultado || '(pendiente de verificar)') +
            (cerradas ? ' · ' + cerradas + ' duda cerrada' : '') + '.';
        }, function (e) { self.error = (e && e.mensaje) || 'No se pudo certificar la tabla.'; }).then(function () {
          self.enviando = ''; self.certifico = false;
          self.leerTablas(); self.leerDudas(); self.abrirTabla(id); self.$emit('actualizar');
        });
      },
      // ---- A48: confirmar la tabla completa ----
      confirmar: function () {
        var self = this, d = this.det;
        if (!d || !this.revisado || this.enviando) return;
        var id = d.id;
        this.enviando = 'confirmar'; this.error = ''; this.mensaje = '';
        C.api.post('/api/proyectos/' + enc(this.obra.id) + '/tablas-extraidas/' + enc(id) + '/confirmar', { confirmo: true, extraido_en: d.extraido_en }, { tiempo: 120000 }).then(function (r) {
          r = r || {};
          var cerradas = Array.isArray(r.dudas_cerradas) ? r.dudas_cerradas.length : 0;
          self.mensaje = 'Lote ' + (r.lote || '(pendiente de verificar)') + ': ' + num(r.confirmados) + ' valores confirmados en ' + num(r.elementos) + ' elementos' +
            (r.conflictos ? ' · ' + r.conflictos + ' ya confirmados con otro valor (duda abierta en la Mesa)' : '') +
            (cerradas ? ' · ' + cerradas + ' dudas cerradas' : '') + '.';
        }, function (e) { self.error = (e && e.mensaje) || 'No se pudo confirmar la tabla.'; }).then(function () {
          self.enviando = ''; self.revisado = false;
          self.leerTablas(); self.leerDudas(); self.abrirTabla(id); self.$emit('actualizar');
        });
      }
    },
    template: `
      <dialog ref="dlg" class="dlg vp conf" :aria-labelledby="uid + '-t'" @cancel.prevent="cerrar" @close="alCerrar" @keydown.tab="atrapar" data-confirmar>
        <div class="conf-int">
          <header class="conf-barra">
            <div class="conf-tit">
              <h2 :id="uid + '-t'" ref="titulo" tabindex="-1" class="nombre-largo" :title="'Confirmar datos del plano · ' + obra.nombre">Confirmar datos del plano · {{ obra.nombre }}</h2>
              <p class="ayuda">Revisa lo que el programa leyó del plano vigente. Nada se confirma solo: cada acción pide su casilla.</p>
            </div>
            <div class="conf-acc">
              <button type="button" class="btn btn-pri" data-extraer :disabled="!!enviando" :aria-busy="enviando === 'extraer' ? 'true' : null" @click="extraer"><Icono nombre="rayo"/><span class="conf-largo">{{ enviando === 'extraer' ? 'Extrayendo…' : 'Extraer del plano vigente' }}</span><span class="conf-corto" aria-hidden="true">{{ enviando === 'extraer' ? 'Extrayendo…' : 'Extraer' }}</span></button>
              <a class="btn btn-sec" :href="hrefMesa" data-mesa-obra><Icono nombre="pregunta"/><span class="conf-largo">Mesa de Dudas de la obra</span><span class="conf-corto" aria-hidden="true">Mesa</span><span class="conf-n num" data-dudas-obra>{{ textoDudas }}</span></a>
              <button type="button" class="btn btn-sec" data-cerrar-confirmar @click="cerrar"><Icono nombre="cerrar"/>Cerrar</button>
            </div>
          </header>

          <div class="conf-msgs">
            <div role="alert"><p v-if="error" class="dlg-error" data-confirmar-error><Icono nombre="alerta"/>{{ error }}</p></div>
            <div role="status"><p v-if="mensaje" class="aviso aviso-ok conf-ok" data-confirmar-mensaje><span><Icono nombre="check"/>{{ mensaje }}</span></p></div>
            <div role="status"><p v-if="avisoTabla" class="ed-aviso" data-aviso-tabla><Icono nombre="info"/>{{ avisoTabla }}</p></div>
            <div role="status"><p v-if="enviando === 'extraer'" class="ayuda conf-espera" data-extrayendo><Icono nombre="reloj"/>Extrayendo del plano vigente: puede tardar un rato.</p></div>
          </div>

          <div class="conf-cuerpo" :data-paso="paso">
            <section class="conf-lista" :aria-labelledby="uid + '-l'" data-lista-tablas>
              <h3 :id="uid + '-l'" class="conf-h">Tablas extraídas<span v-if="estadoL === 'listo' && tablas.length" class="conf-n num">{{ cuentaTablas }}</span></h3>
              <div v-if="estadoL === 'cargando'" class="cargando" aria-busy="true" aria-live="polite" data-cargando-tablas><p class="ayuda">Cargando tablas…</p><span class="hueso" style="--i:0"></span><span class="hueso" style="--i:1"></span><span class="hueso" style="--i:2"></span></div>
              <div v-else-if="estadoL === 'error'" class="error" role="alert" data-error-tablas>
                <Icono nombre="alerta"/>
                <div><p class="error-t">No se pudieron leer las tablas.</p><p>{{ mensajeL }}</p><button type="button" class="btn btn-sec" data-reintentar-tablas @click="leerTablas">Reintentar</button></div>
              </div>
              <p v-else-if="!tablas.length" class="vacio conf-vacio" data-sin-tablas>Aún no hay tablas extraídas del plano vigente. Pulsa «Extraer del plano vigente».</p>
              <ul v-else class="conf-ul">
                <li v-for="t in tablas" :key="t.id">
                  <button type="button" class="conf-t" :class="{ 'es-sel': t.id === selId, 'no-vig': !t.vigente }" :aria-current="t.id === selId ? 'true' : null" :data-tabla="t.clave" @click="elegir(t)">
                    <span class="conf-t-cab"><b class="conf-t-n">{{ nombre(t.tabla) }}</b><span class="est" :class="insignia(t.resultado).clase"><Icono :nombre="insignia(t.resultado).icono"/>{{ insignia(t.resultado).texto }}</span></span>
                    <span class="conf-t-id num" data-tabla-id>tabla n.º {{ t.id }} · {{ t.clave }}</span>
                    <span class="conf-t-m num">pág. {{ t.pagina }} · hoja {{ txt(t.hoja) ? t.hoja : "pendiente de verificar" }} · {{ txt(t.nivel_rango) ? t.nivel_rango : "pendiente de verificar" }}</span>
                    <span v-if="t.resultado === 'rojo'" class="conf-t-f" :title="fallasClaves(t).join(', ')" :data-claves="fallasClaves(t).join(',')"><Icono nombre="alerta"/>Falla: {{ fallas(t) }}</span>
                    <span v-if="!t.vigente" class="conf-t-nv"><Icono nombre="reloj"/>No vigente: {{ (t.motivos_no_vigente || [])[0] || 'pendiente de verificar' }}</span>
                    <span v-if="t.id === selId" class="conf-t-sel"><Icono nombre="check"/>Tabla elegida</span>
                  </button>
                </li>
              </ul>
            </section>

            <section class="conf-det" :aria-labelledby="uid + '-d'" data-detalle-tabla>
              <button type="button" class="btn btn-sec conf-volver" data-volver-tablas @click="volverALista"><Icono nombre="volver"/>Volver a las tablas</button>
              <h3 :id="uid + '-d'" class="sr">Detalle de la tabla</h3>

              <p v-if="estadoT === 'ninguna'" class="vacio conf-vacio" data-sin-eleccion>Elige una tabla para ver sus filas propuestas junto al recorte del plano.</p>
              <div v-else-if="estadoT === 'cargando'" class="cargando" aria-busy="true" aria-live="polite" data-cargando-tabla><p class="ayuda">Cargando la tabla…</p><span class="hueso" style="--i:0"></span><span class="hueso" style="--i:1"></span><span class="hueso" style="--i:2"></span></div>
              <div v-else-if="estadoT === 'error'" class="error" role="alert" data-error-tabla>
                <Icono nombre="alerta"/>
                <div><p class="error-t">No se pudo leer la tabla.</p><p>{{ mensajeT }}</p><button type="button" class="btn btn-sec" data-reintentar-tabla @click="reintentarTabla">Reintentar</button></div>
              </div>

              <template v-else-if="det">
                <div class="conf-cab">
                  <h4 class="conf-tt" data-titulo-tabla>{{ nombre(det.tabla) }}</h4>
                  <span class="est" :class="insignia(det.resultado).clase" data-resultado><Icono :nombre="insignia(det.resultado).icono"/>{{ insignia(det.resultado).texto }}</span>
                  <span v-if="!det.vigente" class="est est-cola"><Icono nombre="reloj"/>No vigente</span>
                </div>
                <p class="conf-meta num" data-meta-tabla>{{ det.clave }} · pág. {{ det.pagina }} · hoja <template v-if="txt(det.hoja)">{{ det.hoja }}</template><Pendiente v-else/> · nivel <template v-if="txt(det.nivel_rango)">{{ det.nivel_rango }}</template><Pendiente v-else/> · extraída <template v-if="fh(det.extraido_en)">{{ fh(det.extraido_en) }}</template><Pendiente v-else/></p>
                <p v-if="!det.vigente" class="ed-aviso" data-no-vigente><Icono nombre="reloj"/>No vigente: {{ (det.motivos_no_vigente || []).join('; ') || 'pendiente de verificar' }}. Vuelve a extraer para poder confirmarla.</p>

                <section class="conf-sec" aria-label="Comprobaciones de la tabla">
                  <h4 class="conf-sub">Comprobaciones</h4>
                  <ul class="conf-comp" data-comprobaciones>
                    <li v-for="c in comprobaciones" :key="c.comprobacion" class="conf-comp-f" :class="c.ok ? 'es-ok' : 'es-mal'">
                      <span class="est" :class="c.ok ? 'est-ok' : 'est-mal'"><Icono :nombre="c.ok ? 'check' : 'alerta'"/>{{ c.ok ? 'cumple' : 'falla' }}</span>
                      <span class="conf-comp-n" :title="c.comprobacion" :data-clave="c.comprobacion">{{ nombreComprobacion(c.comprobacion) }}</span>
                      <span v-if="!c.ok && c.detalle && c.detalle.length" class="conf-comp-d">{{ c.detalle.join('; ') }}</span>
                      <span v-if="c.certificada" class="conf-comp-c" data-certificada>{{ certificadaTexto(c) }}</span>
                    </li>
                  </ul>
                </section>

                <section v-if="det.certificable" class="conf-bloque conf-cert" data-certificar aria-label="Certificar las notas de modificación">
                  <p class="conf-bt">La hoja de esta tabla tiene notas de modificación:</p>
                  <ul class="conf-notas"><li v-for="(n, i) in notas" :key="i">{{ n }}</li></ul>
                  <label class="certifico"><input type="checkbox" v-model="certifico" :disabled="!!enviando" data-certifico><span>Revisé las notas y certifico que esta tabla vale para el plano vigente. <span class="ayuda">(queda auditado con tu usuario, la tabla y el sha256 del vectorial; si cambia el plano, la certificación se pierde)</span></span></label>
                  <div class="acc-botones"><button type="button" class="btn btn-pri" data-certificar-notas :disabled="!certifico || !!enviando" :aria-busy="enviando === 'certificar' ? 'true' : null" @click="certificar">{{ enviando === 'certificar' ? 'Certificando…' : 'Certificar que vale para el plano vigente' }}</button></div>
                </section>

                <div class="conf-dos">
                  <section class="conf-rec" aria-label="Recorte del plano">
                    <h4 class="conf-sub">Recorte del plano vectorial (pág. {{ det.pagina }})</h4>
                    <div v-if="urlRecorte" class="conf-img" data-recorte>
                      <img :src="urlRecorte" :alt="'Recorte del plano, página ' + det.pagina + ', con la tabla ' + nombre(det.tabla)" data-recorte-img>
                      <div v-if="caja" class="conf-caja" :style="caja" data-resaltado></div>
                    </div>
                    <div v-else-if="cargandoRecorte" class="cargando" aria-busy="true" aria-live="polite" data-cargando-recorte><p class="ayuda">Cargando el recorte del plano…</p><span class="hueso" style="--i:0"></span></div>
                    <div v-else-if="errorRecorte" class="error" role="alert" data-error-recorte>
                      <Icono nombre="alerta"/>
                      <div><p class="error-t">No se pudo mostrar el recorte del plano.</p><p>{{ errorRecorte }}</p><button type="button" class="btn btn-sec" data-reintentar-recorte @click="cargarRecorte">Reintentar</button></div>
                    </div>
                    <p v-else class="conf-sinrec" data-sin-recorte><Icono nombre="info"/>Sin recorte: la tabla no tiene celdas con posición.</p>
                    <p class="ayuda">Pasa el ratón o el foco del teclado por un valor para ver su celda en el recorte.</p>
                    <p class="ayuda conf-celda" aria-live="polite" data-celda-texto>{{ textoCelda }}</p>
                    <button type="button" class="btn btn-sec" data-abrir-plano-tabla @click="verPlano = true"><Icono nombre="plano"/>Abrir plano</button>
                  </section>

                  <section class="conf-val" aria-label="Valores propuestos">
                    <h4 class="conf-sub">Valores propuestos que vienen de esta tabla ({{ campos.length }})</h4>
                    <p v-if="!campos.length" class="ayuda" data-sin-campos>Ningún elemento toma valores de esta tabla.</p>
                    <template v-else>
                      <p v-if="dudosos" class="ed-aviso" data-valores-dudosos><Icono nombre="alerta"/><span>{{ dudosos === 1 ? '1 valor pendiente no coincide con la tabla o no tiene fuente: queda «pendiente de verificar». Resuélvelo' : dudosos + ' valores pendientes no coinciden con la tabla o no tienen fuente: quedan «pendiente de verificar». Resuélvelos' }} en la <a :href="hrefMesa">Mesa de Dudas de la obra</a>.</span></p>
                      <div class="conf-tabla-cont" tabindex="-1">
                        <table class="conf-tabla" data-campos>
                          <caption class="sr">Valores propuestos que vienen de la tabla {{ nombre(det.tabla) }}</caption>
                          <thead><tr><th scope="col">Elemento</th><th scope="col">Campo</th><th scope="col">Valor</th><th scope="col">Estado</th></tr></thead>
                          <tbody @keydown="teclasFilas">
                            <tr v-for="(x, i) in campos" :key="x.uid + '|' + x.campo" :tabindex="i === filaActiva ? 0 : -1" :data-campo="x.id_elemento + '|' + x.campo" :data-uid="x.uid"
                              @mouseenter="entra(x)" @mouseleave="sale" @focus="enfoca(x, i)" @blur="desenfoca">
                              <th scope="row"><span class="conf-el">{{ x.id_elemento }}</span> <span class="conf-niv">{{ x.nivel_rango }}</span></th>
                              <td>{{ x.campo }} <span class="conf-niv">(fila {{ x.fuente && x.fuente.fila ? x.fuente.fila : '—' }})</span></td>
                              <td class="num">
                                <Pendiente v-if="valorCelda(x) === null"/><template v-else>{{ x.valor }}</template>
                                <span v-if="sinFuente(x)" class="conf-dif" data-sin-fuente><Icono nombre="alerta"/>tabla: <Pendiente/></span>
                                <span v-else-if="difiere(x)" class="conf-dif" data-difiere><Icono nombre="alerta"/>tabla: {{ x.valor_tabla }}</span>
                              </td>
                              <td><span class="est" :class="x.estado === 'confirmado' ? 'est-ok' : 'est-cola'"><Icono :nombre="x.estado === 'confirmado' ? 'check' : 'reloj'"/>{{ x.estado === 'confirmado' ? 'confirmado' : 'pendiente' }}</span></td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </template>
                  </section>
                </div>

                <section class="conf-sec conf-lote" aria-label="Confirmación por lote">
                  <template v-if="det.confirmable">
                    <label class="certifico"><input type="checkbox" v-model="revisado" :disabled="!!enviando" data-revisado><span>Revisé los {{ pendientes }} valores pendientes contra el recorte del plano y los confirmo<span v-if="det.identidad_pendiente" data-identidad>, junto con la identidad de los elementos ({{ det.identidad_pendiente }} campos: ID, nivel, ejes, hoja y archivo)</span>. <span class="ayuda">(queda auditado campo por campo con tu usuario y el lote)</span></span></label>
                    <div class="acc-botones"><button type="button" class="btn btn-pri" data-confirmar-tabla :disabled="!revisado || !!enviando" :aria-busy="enviando === 'confirmar' ? 'true' : null" @click="confirmar">{{ enviando === 'confirmar' ? 'Confirmando…' : 'Confirmar tabla completa' }}</button></div>
                  </template>
                  <div v-else-if="det.resultado === 'rojo'" class="conf-bloque conf-roja" data-tabla-roja>
                    <p class="conf-bt"><Icono nombre="alerta"/>Esta tabla está en rojo: no se confirma por lote.</p>
                    <p>Falló: <b :title="fallasClaves(det).join(', ')">{{ fallas(det) }}</b>. Los campos dudosos se resuelven uno por uno en la Mesa de Dudas; los datos que el plano no trae (E-n ↔ nivel, tipo de losa, plantas repetidas) van en «Datos de la obra», y después se vuelve a extraer.</p>
                    <div class="acc-botones"><a class="btn btn-pri" :href="hrefMesa" data-ir-mesa><Icono nombre="pregunta"/>Ir a la Mesa de Dudas</a></div>
                  </div>
                  <p v-else class="conf-no" data-no-confirmable><Icono nombre="info"/>No se puede confirmar: {{ motivosNo.join('; ') || 'pendiente de verificar' }}.</p>
                </section>
              </template>
            </section>
          </div>
        </div>

        <VisorPlano v-if="verPlano && det" :obra-id="obra.id" :pagina="det.pagina" :detalle="bboxOk(det.recorte) ? { pagina: det.pagina, rect: det.recorte, origen: 'recorte' } : null"
          :etiqueta="nombre(det.tabla)" nota="El recuadro azul punteado es el recorte de la tabla." @cerrar="verPlano = false"/>
      </dialog>`
  };
})();
