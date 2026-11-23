/* CATDIC-WEB · visor de revisión compartido (B3e). Se construye una sola vez: lo usan la Mesa de Dudas (B3e), la revisión
   de elementos (B3c) y «Planos y ficha» (B3b). Responde a lo que pidió Steven el 22/11/2026: que al pedir una revisión el
   programa UBIQUE el elemento, muestre su DETALLE y deje ABRIR EL PLANO.

   ── VisorRevision (<VisorRevision/>) ─────────────────────────────────────────────────────────────────────────────
   props
     obraId          (String, obligatoria)  obra cuyo plano vigente se muestra
     uid             (String)               uid del elemento de diseño (elementos_diseno.uid). NUNCA se ata por id_elemento:
                                            el mismo ID se repite en varios niveles. Sin uid ni `recuadros`, solo «Abrir plano».
     recuadros       (Object)               alternativa a `uid`: { localizacion, detalle } con el formato de recorte_planta /
                                            recorte_detalle ({ plano_id, pagina, rect, estado }). Si llega, no se lee el elemento.
     etiqueta        (String)               texto del elemento para el título accesible (por defecto sale del elemento leído)
     paginaInicial   (Number)               hoja (página del PDF, desde 1) en la que se abre «Abrir plano» cuando no hay recuadro
     notaPagina      (String)               texto que dice de dónde sale `paginaInicial` (se muestra en el visor)
     motivoSinElemento (String)             por qué no se pudo atar a un elemento (se muestra tal cual)
   hayPlano        (Boolean)              false = el tablero ya sabe que la obra no tiene plano vigente: no se pide nada al visor
   eventos
     ubicado({ localizacion, detalle })  cada pieza queda en 'confirmado' | 'propuesta' | 'pendiente' | 'error' | 'cargando'
     abrir() / cerrar()                  se abre o se cierra el diálogo «Abrir plano»
   Muestra tres piezas:
     1. Ubicación (M3): POST /api/proyectos/{id}/visor/vista-previa {tipo:'localizacion'} = la planta completa del nivel con el
        recuadro rojo, igual que en los informes. Nunca un zoom irreconocible.
     2. Detalle (M4): la misma ruta con {tipo:'detalle'}. Nunca una foto de campo.
     3. Abrir plano: la hoja completa, con zoom y desplazamiento, en un diálogo a pantalla completa (VisorPlano).
   De dónde sale el recuadro: confirmado = recorte_* con estado 'confirmado' y el plano_id del plano VIGENTE; sin confirmar =
   POST …/elementos/{uid}/propuesta (no guarda nada) rotulada «propuesta, pendiente de verificar»; de otro plano, sin plano
   vigente, sin propuesta o sin hoja = «pendiente de verificar» con el motivo. Nunca se adivina la ubicación por cercanía.

   ── VisorPlano (<VisorPlano/>) ───────────────────────────────────────────────────────────────────────────────────
   props: obraId · pagina (hoja inicial) · localizacion {pagina, rect, origen} · detalle {pagina, rect, origen} · etiqueta · nota
   evento: cerrar. Diálogo modal a pantalla completa: foco atrapado, Escape cierra y el foco vuelve a quien lo abrió.
   Zoom: rueda, botones, pellizco, teclas + − 0. Desplazamiento: arrastre, dedo, flechas. R lleva al recuadro.

   ── C.visor ───────────────────────────────────────────────────────────────────────────────────────────────────────
   olvidar(obraId?)  descarta lo guardado en memoria (índice, elementos, propuestas e imágenes): úsalo tras guardar un recuadro
   Lo ya pedido se guarda en memoria 60 s; las imágenes son Blob y se enlazan con URL.createObjectURL (se liberan al desmontar). */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};

  var TTL = 60000;            // lo ya pedido (índice, elementos, propuestas) vale 60 s
  var MAX_IMAGENES = 40;      // vistas previas guardadas
  var MAX_HOJAS = 3;          // hojas completas guardadas (pesan más)
  var LADO_MAX_PX = 5000;     // una hoja muy grande se rasteriza con menos dpi para no pasar de este lado
  var DPI_HOJA = 110, DPI_MIN = 30;

  var memoria = {};
  var vistas = new Map();
  var hojas = new Map();
  var contador = 0;

  function enc(s) { return encodeURIComponent(s); }
  function de(obraId) {
    var m = memoria[obraId];
    if (!m || Date.now() - m.t > TTL) m = memoria[obraId] = { t: Date.now(), indice: null, elementos: null, propuestas: {} };
    return m;
  }
  function olvidar(obraId) {
    if (obraId) delete memoria[obraId]; else memoria = {};
    vistas.clear(); hojas.clear();
  }
  function guardado(mapa, max, clave, pedir) {
    if (mapa.has(clave)) return mapa.get(clave);
    var p = pedir().catch(function (e) { mapa.delete(clave); throw e; });
    mapa.set(clave, p);
    while (mapa.size > max) mapa.delete(mapa.keys().next().value);
    return p;
  }

  function leerIndice(obraId) {
    var m = de(obraId);
    if (!m.indice) m.indice = C.api.get('/api/proyectos/' + enc(obraId) + '/visor/indice').catch(function (e) { m.indice = null; throw e; });
    return m.indice;
  }
  function leerElementos(obraId) {
    var m = de(obraId);
    if (!m.elementos) m.elementos = C.api.get('/api/proyectos/' + enc(obraId) + '/elementos').then(function (r) { return (r && r.elementos) || []; })
      .catch(function (e) { m.elementos = null; throw e; });
    return m.elementos;
  }
  function leerPropuesta(obraId, uid) {
    var m = de(obraId);
    if (!m.propuestas[uid]) m.propuestas[uid] = C.api.post('/api/proyectos/' + enc(obraId) + '/elementos/' + enc(uid) + '/propuesta', undefined, { tiempo: 60000 })
      .catch(function (e) { delete m.propuestas[uid]; throw e; });
    return m.propuestas[uid];
  }
  function vistaPrevia(obraId, planoId, tipo, pagina, rect) {
    var clave = ['vp', obraId, planoId, tipo, pagina, rect.join(',')].join('|');
    return guardado(vistas, MAX_IMAGENES, clave, function () {
      return C.api.pedir('POST', '/api/proyectos/' + enc(obraId) + '/visor/vista-previa', { cuerpo: { tipo: tipo, pagina: pagina, rect: rect }, respuesta: 'blob', tiempo: 90000 });
    });
  }
  function leerInfoHoja(obraId, pagina) {
    return C.api.get('/api/proyectos/' + enc(obraId) + '/visor/hojas/' + pagina + '/info', { consulta: { dpi: 60 } });
  }
  function dpiParaHoja(info) {
    var lado = Math.max(Number(info.ancho_pt) || 0, Number(info.alto_pt) || 0);
    if (!lado) return 60;
    return Math.max(DPI_MIN, Math.min(DPI_HOJA, Math.floor(LADO_MAX_PX * 72 / lado)));
  }
  function hojaPng(obraId, planoId, pagina, dpi) {
    var clave = ['hoja', obraId, planoId, pagina, dpi].join('|');
    return guardado(hojas, MAX_HOJAS, clave, function () {
      return C.api.get('/api/proyectos/' + enc(obraId) + '/visor/hojas/' + pagina + '.png', { consulta: { dpi: dpi }, respuesta: 'blob', tiempo: 120000 });
    });
  }
  function soltar(url) { if (url) { try { URL.revokeObjectURL(url); } catch (e) { /* nada que soltar */ } } }

  var METODOS = { cruce_de_ejes: 'cruce de ejes', bbox_id: 'ID leído en la planta', rotulo: 'rótulo del detalle' };
  function textoFuente(f) {
    if (!f || typeof f !== 'object') return '';
    var t = METODOS[f.metodo] || (f.metodo ? String(f.metodo) : '');
    if (f.metodo === 'rotulo' && f.rotulo) t += ' «' + f.rotulo + '»';
    if (f.hoja) t += (t ? ' · ' : '') + 'hoja ' + f.hoja;
    return t;
  }
  function pieza(clave, titulo, sub) {
    return { clave: clave, titulo: titulo, sub: sub, estado: 'cargando', motivo: '', origen: '', fuente: '', pagina: null, rect: null, url: '', error: '', por: '', en: '' };
  }
  function rectValido(r) { return Array.isArray(r) && r.length === 4 && r.every(function (v) { return typeof v === 'number' && isFinite(v); }); }

  /* ============================================================================================================
     VisorPlano: la hoja completa con zoom y desplazamiento
     ============================================================================================================ */
  C.componentes.VisorPlano = {
    props: {
      obraId: { type: String, required: true },
      pagina: { type: Number, default: 0 },
      localizacion: { type: Object, default: null },
      detalle: { type: Object, default: null },
      etiqueta: { type: String, default: '' },
      nota: { type: String, default: '' },
      // B3b · editor de recuadros (Planos y ficha). Sin `editor` el visor se comporta como en B3e.
      editor: { type: Boolean, default: false },
      cajas: { type: Array, default: function () { return []; } },     // [{ clave, tipo:'localizacion'|'detalle', estado:'confirmado'|'propuesto'|'sin_guardar', pagina, rect, texto }]
      herramienta: { type: String, default: 'mover' },                  // 'mover' | 'dibujar'
      salto: { type: Object, default: null },                           // { pagina, n }: lleva el visor a esa hoja
      leyendaPropia: { type: String, default: '' }
    },
    emits: ['cerrar', 'hoja', 'dibujado'],
    data: function () {
      contador++;
      return {
        uid: 'vpl' + contador, hojas: [], planoId: null, estadoIndice: 'cargando', errorIndice: '',
        pagActual: 0, info: null, estadoHoja: 'cargando', errorHoja: '', url: '', W: 0, H: 0, k: 1,
        vw: 0, vh: 0, e: 1, eAjuste: 1, eMin: 0.05, eMax: 4, tx: 0, ty: 0, cerrado: false, apertura: null, n: 0, tamanoListo: false, trazo: null, suave: false
      };
    },
    computed: {
      pct: function () { return Math.round(this.e / (this.eAjuste || 1) * 100); },
      estiloHoja: function () {
        return { width: this.W + 'px', height: this.H + 'px', transform: 'translate(' + this.tx + 'px, ' + this.ty + 'px) scale(' + this.e + ')' };
      },
      rectLoc: function () { return this.aPx(this.localizacion); },
      rectDet: function () { return this.aPx(this.detalle); },
      grosor: function () { return 3 / this.e; },
      // Cajas del editor sobre la hoja actual, en píxeles de la imagen. El texto va en la propia caja (no solo el color).
      cajasPx: function () {
        var self = this;
        return (this.cajas || []).map(function (c, i) { var r = self.aPx(c); return r ? { c: c, r: r, i: i } : null; }).filter(Boolean);
      },
      rectFoco: function () {
        var l = this.cajasPx.filter(function (x) { return x.c.tipo === 'localizacion'; })[0] || this.cajasPx[0];
        return l ? l.r : null;
      },
      trazoPx: function () {
        var t = this.trazo; if (!t || !this.W) return null;
        var k = this.k;
        return { x: Math.min(t.x0, t.x1) * k, y: Math.min(t.y0, t.y1) * k, w: Math.abs(t.x1 - t.x0) * k, h: Math.abs(t.y1 - t.y0) * k };
      },
      dibuja: function () { return this.editor && this.herramienta === 'dibujar' && this.tamanoListo; },
      motivoCorto: function () { return 'Dibuja uno primero'; },
      motivoSinRecuadro: function () { return 'No hay ningún recuadro ni borrador en esta hoja: dibuja uno para poder ir a él.'; },
      leyenda: function () {
        var l = this.localizacion;
        if (l && rectValido(l.rect)) return l.origen === 'propuesta' ? 'Ubicación: propuesta, pendiente de verificar (recuadro punteado).' : 'Ubicación: recuadro confirmado.';
        return 'Sin recuadro de ubicación: pendiente de verificar.';
      },
      hojaActual: function () { var p = this.pagActual; return this.hojas.filter(function (h) { return h.pagina === p; })[0] || null; },
      altImagen: function () {
        return 'Hoja ' + (this.hojaActual && this.hojaActual.hoja ? this.hojaActual.hoja + ' ' : '') + 'del plano vigente' + (this.etiqueta ? ', con el recuadro de ' + this.etiqueta : '');
      }
    },
    mounted: function () {
      var self = this;
      this.apertura = document.activeElement;
      var dlg = this.$refs.dlg;
      if (dlg && dlg.showModal) dlg.showModal(); else if (dlg) dlg.setAttribute('open', '');
      this._p = {}; this._pinch = null; this._dib = null;
      if (window.ResizeObserver && this.$refs.lienzo) {
        this._ro = new ResizeObserver(function () { self.medir(false); });
        this._ro.observe(this.$refs.lienzo);
      }
      this.cargarIndice();
    },
    beforeUnmount: function () {
      if (this._ro) this._ro.disconnect();
      soltar(this.url); this.url = '';
      this.devolverFoco();
    },
    watch: {
      // El editor pide una hoja (por ejemplo, la del recuadro guardado del elemento elegido).
      salto: function (s) {
        if (!s || !this.hojas.length || !this.hojas.some(function (h) { return h.pagina === s.pagina; })) return;
        if (s.pagina !== this.pagActual) { this.pagActual = s.pagina; this.cargarHoja(); this.$emit('hoja', this.pagActual); }
        else if (this.tamanoListo) { this.medir(true); }
      }
    },
    methods: {
      aPx: function (r) {
        if (!r || !rectValido(r.rect) || r.pagina !== this.pagActual || !this.W) return null;
        var k = this.k, a = r.rect;
        return { x: a[0] * k, y: a[1] * k, w: (a[2] - a[0]) * k, h: (a[3] - a[1]) * k };
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
      devolverFoco: function () {
        var a = this.apertura; this.apertura = null;
        if (a && a.isConnected && a.focus) { a.focus({ preventScroll: true }); return; }
        var h1 = document.querySelector('main h1'); if (h1) h1.focus({ preventScroll: true });
      },
      cerrar: function () {
        var dlg = this.$refs.dlg;
        this.cerrado = true;
        if (dlg && dlg.open && dlg.close) dlg.close();
        this.$emit('cerrar');
      },
      alCerrar: function () { if (!this.cerrado) { this.cerrado = true; this.$emit('cerrar'); } },
      enfocarLienzo: function () { var l = this.$refs.lienzo; if (l) l.focus({ preventScroll: true }); },
      // ---- datos ----
      cargarIndice: function () {
        var self = this;
        this.estadoIndice = 'cargando'; this.errorIndice = '';
        leerIndice(this.obraId).then(function (ind) {
          self.hojas = (ind && ind.hojas) || [];
          self.planoId = ind && ind.plano ? ind.plano.id : null;
          if (!self.hojas.length) { self.estadoIndice = 'error'; self.errorIndice = 'El plano vigente no trae ninguna hoja.'; return; }
          var ini = (self.localizacion && self.localizacion.pagina) || (self.detalle && self.detalle.pagina) || self.pagina || 0;
          var existe = self.hojas.some(function (h) { return h.pagina === ini; });
          var s0 = self.salto && self.hojas.some(function (h) { return h.pagina === self.salto.pagina; }) ? self.salto.pagina : 0;
          self.pagActual = s0 || (existe ? ini : self.hojas[0].pagina);
          self.estadoIndice = 'listo';
          self.$emit('hoja', self.pagActual);
          self.cargarHoja();
        }, function (e) { self.estadoIndice = 'error'; self.errorIndice = (e && e.mensaje) || 'No se pudo leer el índice del plano.'; });
      },
      cargarHoja: function () {
        var self = this, n = ++this.n, pagina = this.pagActual;
        soltar(this.url); this.url = ''; this.tamanoListo = false; this.W = 0; this.H = 0;
        this.estadoHoja = 'cargando'; this.errorHoja = '';
        leerInfoHoja(this.obraId, pagina).then(function (info) {
          if (n !== self.n) return;
          self.info = info;
          return hojaPng(self.obraId, info.plano_id, pagina, dpiParaHoja(info)).then(function (blob) {
            if (n !== self.n) return;
            self.url = URL.createObjectURL(blob);
            self.estadoHoja = 'listo';
          });
        }).catch(function (e) {
          if (n !== self.n) return;
          self.estadoHoja = 'error'; self.errorHoja = (e && e.mensaje) || 'No se pudo cargar la hoja.';
        });
      },
      alCargarImagen: function (ev) {
        var img = ev.target;
        this.W = img.naturalWidth; this.H = img.naturalHeight;
        this.k = this.info && this.info.ancho_pt ? this.W / this.info.ancho_pt : 1;
        this.medir(true);
        this.tamanoListo = true;
        this.$nextTick(this.enfocarLienzo);
      },
      alFallarImagen: function () { this.estadoHoja = 'error'; this.errorHoja = 'La imagen de la hoja no se pudo leer.'; },
      cambiarHoja: function () { this.cargarHoja(); this.$emit('hoja', this.pagActual); },
      // ---- zoom y desplazamiento ----
      medir: function (reiniciar) {
        var l = this.$refs.lienzo; if (!l) return;
        this.suave = false;
        this.vw = l.clientWidth; this.vh = l.clientHeight;
        if (!this.W || !this.H || !this.vw || !this.vh) return;
        this.eAjuste = Math.min(this.vw / this.W, this.vh / this.H);
        this.eMin = this.eAjuste * 0.5;
        this.eMax = Math.max(4, this.eAjuste * 2);
        if (reiniciar) {
          if (this.rectLoc) this.irAlRecuadro('localizacion'); else if (this.rectDet) this.irAlRecuadro('detalle'); else if (this.rectFoco) this.irAlRecuadro('foco'); else this.ajustar();
        } else {
          this.poner(this.e, this.tx, this.ty);
        }
      },
      // Mover suave solo si el clic vino de un puntero (detail > 0), no del teclado (Enter o espacio dan detail 0), y sin movimiento reducido.
      suavizar: function (ev) {
        var reducido = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.suave = !!(ev && ev.detail > 0 && !reducido);
      },
      poner: function (e, tx, ty) {
        e = Math.max(this.eMin, Math.min(this.eMax, e));
        var w = this.W * e, h = this.H * e, m = 60;
        tx = w <= this.vw ? (this.vw - w) / 2 : Math.min(m, Math.max(this.vw - w - m, tx));
        ty = h <= this.vh ? (this.vh - h) / 2 : Math.min(m, Math.max(this.vh - h - m, ty));
        this.e = e; this.tx = tx; this.ty = ty;
      },
      ajustar: function () { this.poner(this.eAjuste, 0, 0); },
      irAlRecuadro: function (cual) {
        var r = cual === 'detalle' ? this.rectDet : (cual === 'foco' ? this.rectFoco : this.rectLoc);
        if (!r) return;
        var e = Math.min(0.5 * this.vw / Math.max(r.w, 1), 0.5 * this.vh / Math.max(r.h, 1));
        e = Math.max(this.eAjuste, Math.min(this.eMax, e));
        this.poner(e, this.vw / 2 - (r.x + r.w / 2) * e, this.vh / 2 - (r.y + r.h / 2) * e);
      },
      zoomEn: function (f, cx, cy) {
        var ne = Math.max(this.eMin, Math.min(this.eMax, this.e * f));
        if (ne === this.e) return;
        this.poner(ne, cx - (cx - this.tx) * ne / this.e, cy - (cy - this.ty) * ne / this.e);
      },
      zoomCentro: function (f) { this.zoomEn(f, this.vw / 2, this.vh / 2); },
      mover: function (dx, dy) { this.poner(this.e, this.tx + dx, this.ty + dy); },
      rueda: function (ev) {
        this.suave = false;
        var r = this.$refs.lienzo.getBoundingClientRect();
        var d = ev.deltaMode === 1 ? ev.deltaY * 0.05 : ev.deltaY * 0.0015;
        this.zoomEn(Math.exp(-d), ev.clientX - r.left, ev.clientY - r.top);
      },
      teclas: function (ev) {
        this.suave = false;
        if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
        var paso = ev.shiftKey ? 240 : 80, k = ev.key, hecho = true;
        if (k === 'ArrowLeft') this.mover(paso, 0);
        else if (k === 'ArrowRight') this.mover(-paso, 0);
        else if (k === 'ArrowUp') this.mover(0, paso);
        else if (k === 'ArrowDown') this.mover(0, -paso);
        else if (k === '+' || k === '=') this.zoomCentro(1.25);
        else if (k === '-' || k === '_') this.zoomCentro(0.8);
        else if (k === '0') this.ajustar();
        else if (k === 'r' || k === 'R' || k === 'Home') { if (this.rectLoc) this.irAlRecuadro('localizacion'); else if (this.rectDet) this.irAlRecuadro('detalle'); else if (this.rectFoco) this.irAlRecuadro('foco'); else this.ajustar(); }
        else hecho = false;
        if (hecho) ev.preventDefault();
      },
      alBajarPuntero: function (ev) {
        this.suave = false;
        if (ev.pointerType === 'mouse' && ev.button !== 0) return;
        var l = this.$refs.lienzo;
        try { l.setPointerCapture(ev.pointerId); } catch (e) { /* sin captura */ }
        this._p[ev.pointerId] = { x: ev.clientX, y: ev.clientY };
        this._pinch = null;
        this.arrastrando = true;
        if (this.dibuja) {
          // Un dedo o el ratón dibuja; con un segundo dedo se cancela el trazo y pasa a pellizco.
          if (Object.keys(this._p).length === 1) this.empezarDibujo(ev); else this.cancelarDibujo();
        }
      },
      alMoverPuntero: function (ev) {
        var p = this._p[ev.pointerId]; if (!p) return;
        var ids = Object.keys(this._p);
        if (ids.length === 1) {
          if (this.dibuja) { this.seguirDibujo(ev); p.x = ev.clientX; p.y = ev.clientY; return; }
          this.mover(ev.clientX - p.x, ev.clientY - p.y);
          p.x = ev.clientX; p.y = ev.clientY;
        } else if (ids.length === 2) {
          p.x = ev.clientX; p.y = ev.clientY;
          var a = this._p[ids[0]], b = this._p[ids[1]];
          var d = Math.hypot(a.x - b.x, a.y - b.y) || 1, mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
          if (this._pinch) {
            var r = this.$refs.lienzo.getBoundingClientRect();
            this.mover(mx - this._pinch.mx, my - this._pinch.my);
            this.zoomEn(d / this._pinch.d, mx - r.left, my - r.top);
          }
          this._pinch = { d: d, mx: mx, my: my };
        }
      },
      alSubirPuntero: function (ev) {
        if (this._dib && Object.keys(this._p).length === 1) this.terminarDibujo(ev);
        delete this._p[ev.pointerId]; this._pinch = null;
        if (!Object.keys(this._p).length) this.arrastrando = false;
      },
      alCancelarPuntero: function (ev) { this.cancelarDibujo(); this.alSubirPuntero(ev); },
      // ---- dibujo de recuadros (B3b): coordenadas en puntos del PDF, redondeadas a 2 decimales ----
      ptDe: function (ev) {
        var r = this.$refs.lienzo.getBoundingClientRect(), k = this.k || 1;
        var x = (ev.clientX - r.left - this.tx) / this.e / k, y = (ev.clientY - r.top - this.ty) / this.e / k;
        return { x: Math.max(0, Math.min(this.W / k, x)), y: Math.max(0, Math.min(this.H / k, y)) };
      },
      empezarDibujo: function (ev) {
        var q = this.ptDe(ev);
        this._dib = { x0: q.x, y0: q.y };
        this.trazo = { x0: q.x, y0: q.y, x1: q.x, y1: q.y };
      },
      seguirDibujo: function (ev) {
        if (!this._dib) return;
        var q = this.ptDe(ev);
        this.trazo = { x0: this._dib.x0, y0: this._dib.y0, x1: q.x, y1: q.y };
      },
      cancelarDibujo: function () { this._dib = null; this.trazo = null; },
      terminarDibujo: function (ev) {
        var d = this._dib; if (!d) return;
        this.seguirDibujo(ev);
        var t = this.trazo; this._dib = null; this.trazo = null;
        if (!t) return;
        var redondo = function (v) { return Math.round(v * 100) / 100; };
        var x0 = Math.min(t.x0, t.x1), x1 = Math.max(t.x0, t.x1), y0 = Math.min(t.y0, t.y1), y1 = Math.max(t.y0, t.y1);
        if (x1 - x0 < 5 || y1 - y0 < 5) return;   // un clic suelto o un arrastre de menos de 5 pt no es un recuadro
        this.$emit('dibujado', { pagina: this.pagActual, rect: [redondo(x0), redondo(y0), redondo(x1), redondo(y1)] });
      }
    },
    template: `
      <dialog ref="dlg" class="dlg vp" :aria-labelledby="uid + '-t'" @cancel.prevent="cerrar" @close="alCerrar" @keydown.tab="atrapar" data-visor-plano>
        <div class="vp-int">
          <header class="vp-barra">
            <div class="vp-tit">
              <h2 :id="uid + '-t'" class="nombre-largo">Plano vigente<template v-if="etiqueta"> · {{ etiqueta }}</template></h2>
              <p class="vp-leyenda" data-visor-leyenda><Icono :nombre="localizacion && localizacion.origen === 'propuesta' ? 'info' : 'plano'"/>{{ leyendaPropia || leyenda }}<template v-if="nota"> {{ nota }}</template></p>
            </div>
            <div class="vp-ctl">
              <label class="vp-hoja-sel"><span>Hoja</span>
                <select v-model.number="pagActual" :disabled="estadoIndice !== 'listo'" @change="cambiarHoja" data-visor-hoja>
                  <option v-for="h in hojas" :key="h.pagina" :value="h.pagina">p{{ h.pagina }} · hoja {{ h.hoja || '—' }}<template v-if="h.titulos && h.titulos.length"> · {{ h.titulos[0].slice(0, 40) }}</template></option>
                </select>
              </label>
              <div class="vp-zoom" role="group" aria-label="Zoom">
                <button type="button" class="btn btn-sec" aria-label="Alejar" :disabled="!tamanoListo" data-zoom-menos @click="suavizar($event); zoomCentro(0.8)"><span aria-hidden="true">−</span></button>
                <output class="vp-pct num" data-zoom aria-live="off">{{ pct }} %</output>
                <button type="button" class="btn btn-sec" aria-label="Acercar" :disabled="!tamanoListo" data-zoom-mas @click="suavizar($event); zoomCentro(1.25)"><span aria-hidden="true">+</span></button>
                <button type="button" class="btn btn-sec" :disabled="!tamanoListo" data-ajustar @click="suavizar($event); ajustar()">Ajustar</button>
              </div>
              <div class="vp-ir vp-ir-ed" v-if="editor"><button type="button" class="btn btn-sec" data-ir-recuadro :disabled="!rectFoco" :aria-describedby="rectFoco ? null : uid + '-sinrec'" :title="rectFoco ? null : motivoSinRecuadro" @click="suavizar($event); irAlRecuadro('foco'); enfocarLienzo()">Ir al recuadro</button><span class="vp-sinrec" aria-hidden="true" :data-sin-recuadro-visible="rectFoco ? null : ''">{{ rectFoco ? '' : motivoCorto }}</span><span v-if="!rectFoco" :id="uid + '-sinrec'" class="sr" data-sin-recuadro>{{ motivoSinRecuadro }}</span></div>
              <div class="vp-ir" v-if="localizacion || detalle">
                <button v-if="localizacion && rectLoc" type="button" class="btn btn-sec" data-ir-ubicacion @click="suavizar($event); irAlRecuadro('localizacion'); enfocarLienzo()">Ir a la ubicación</button>
                <button v-if="detalle && rectDet" type="button" class="btn btn-sec" data-ir-detalle @click="suavizar($event); irAlRecuadro('detalle'); enfocarLienzo()">Ir al detalle</button>
              </div>
              <button type="button" class="btn btn-pri vp-cerrar" data-cerrar-visor @click="cerrar"><Icono nombre="cerrar"/>Cerrar</button>
            </div>
          </header>

          <div class="vp-medio" :class="{ 'es-editor': editor }">
          <div class="vp-cuerpo">
            <div v-if="estadoIndice === 'cargando'" class="vp-msg cargando" aria-busy="true" role="status"><span class="sr">Cargando el índice del plano…</span><span class="hueso" style="--i:0"></span></div>
            <div v-else-if="estadoIndice === 'error'" class="vp-msg error" role="alert"><Icono nombre="alerta"/><div><p class="error-t">No se pudo abrir el plano.</p><p>{{ errorIndice }}</p><button type="button" class="btn btn-sec" @click="cargarIndice">Reintentar</button></div></div>
            <template v-else>
              <p v-if="estadoHoja === 'cargando'" class="vp-msg" role="status" aria-live="polite">Cargando la hoja…</p>
              <div v-else-if="estadoHoja === 'error'" class="vp-msg error" role="alert"><Icono nombre="alerta"/><div><p class="error-t">No se pudo cargar la hoja.</p><p>{{ errorHoja }}</p><button type="button" class="btn btn-sec" @click="cargarHoja">Reintentar</button></div></div>
              <div ref="lienzo" class="vp-lienzo" tabindex="0" role="group" data-lienzo
                aria-label="Hoja del plano. Flechas: mover. Más y menos: acercar y alejar. Cero: ajustar a la ventana. R: ir al recuadro."
                @keydown="teclas" @wheel.prevent="rueda" @pointerdown="alBajarPuntero" @pointermove="alMoverPuntero" @pointerup="alSubirPuntero" @pointercancel="alCancelarPuntero">
                <div v-if="url" class="vp-hoja" :class="{ suave: suave }" :style="estiloHoja" data-hoja-lienzo @transitionend.self="suave = false">
                  <img :src="url" :alt="altImagen" draggable="false" @load="alCargarImagen" @error="alFallarImagen" data-hoja-img>
                  <svg v-if="W" class="vp-svg" :viewBox="'0 0 ' + W + ' ' + H" :width="W" :height="H" aria-hidden="true">
                    <g v-for="x in cajasPx" :key="x.c.clave" :data-caja="x.c.clave" :data-estado-caja="x.c.estado">
                      <rect class="vp-halo" :x="x.r.x" :y="x.r.y" :width="x.r.w" :height="x.r.h" :stroke-width="grosor * 2" fill="none"/>
                      <rect :class="x.c.tipo === 'localizacion' ? 'vp-rojo' : 'vp-det'" :x="x.r.x" :y="x.r.y" :width="x.r.w" :height="x.r.h" :stroke-width="grosor * (x.c.tipo === 'localizacion' ? 1 : 0.9)"
                        :stroke-dasharray="x.c.estado === 'propuesto' ? (grosor * 4) + ' ' + (grosor * 2.5) : (x.c.estado === 'sin_guardar' ? grosor + ' ' + (grosor * 2) : null)"
                        :stroke-linecap="x.c.estado === 'sin_guardar' ? 'round' : null" fill="none"/>
                      <text class="vp-etq" :class="x.c.tipo === 'localizacion' ? 'es-loc' : 'es-det'" :x="x.r.x" :y="Math.max(15 / e * (x.i + 1), x.r.y - 4 / e - x.i * 15 / e)" :font-size="12 / e" :stroke-width="3 / e">{{ x.c.texto }}</text>
                    </g>
                    <rect v-if="trazoPx" class="vp-det" :x="trazoPx.x" :y="trazoPx.y" :width="trazoPx.w" :height="trazoPx.h" :stroke-width="grosor" :stroke-dasharray="grosor + ' ' + (grosor * 2)" stroke-linecap="round" fill="none" data-trazo/>
                    <g v-if="rectLoc" data-rect-ubicacion>
                      <rect class="vp-halo" :x="rectLoc.x" :y="rectLoc.y" :width="rectLoc.w" :height="rectLoc.h" :stroke-width="grosor * 2" fill="none"/>
                      <rect class="vp-rojo" :class="{ 'es-propuesta': localizacion.origen === 'propuesta' }" :x="rectLoc.x" :y="rectLoc.y" :width="rectLoc.w" :height="rectLoc.h"
                        :stroke-width="grosor" :stroke-dasharray="localizacion.origen === 'propuesta' ? (grosor * 4) + ' ' + (grosor * 2.5) : null" fill="none" data-rect-rojo/>
                    </g>
                    <g v-if="rectDet" data-rect-detalle>
                      <rect class="vp-halo" :x="rectDet.x" :y="rectDet.y" :width="rectDet.w" :height="rectDet.h" :stroke-width="grosor * 1.8" fill="none"/>
                      <rect class="vp-det" :x="rectDet.x" :y="rectDet.y" :width="rectDet.w" :height="rectDet.h" :stroke-width="grosor * 0.8" :stroke-dasharray="(grosor * 5) + ' ' + (grosor * 3)" fill="none"/>
                    </g>
                  </svg>
                </div>
              </div>
            </template>
          </div>
          <aside v-if="editor" class="vp-panel" aria-label="Recuadros del elemento" data-panel-editor><slot name="panel"></slot></aside>
          </div>
          <p class="vp-ayuda ayuda">Arrastra o usa las flechas para mover · rueda, pellizco o + y − para acercar · 0 ajusta a la ventana · R va al recuadro · Escape cierra.<template v-if="rectDet"> El recuadro azul punteado es el detalle.</template></p>
        </div>
      </dialog>`
  };

  /* ============================================================================================================
     VisorRevision: Ubicación · Detalle · Abrir plano
     ============================================================================================================ */
  C.componentes.VisorRevision = {
    props: {
      obraId: { type: String, required: true },
      uid: { type: String, default: '' },
      recuadros: { type: Object, default: null },
      etiqueta: { type: String, default: '' },
      paginaInicial: { type: Number, default: 0 },
      notaPagina: { type: String, default: '' },
      motivoSinElemento: { type: String, default: '' },
      hayPlano: { type: Boolean, default: null }
    },
    emits: ['ubicado', 'abrir', 'cerrar'],
    data: function () {
      contador++;
      return {
        id: 'vr' + contador, base: 'cargando', errorBase: '', sinPlano: false, motivoPlano: '', plano: null,
        elemento: null, piezas: [pieza('localizacion', 'Ubicación', 'Planta completa del nivel, con el recuadro rojo'), pieza('detalle', 'Detalle', 'Recorte nítido del plano')],
        abierto: false, n: 0
      };
    },
    computed: {
      sinAtar: function () { return !this.uid && !this.recuadros; },
      porClave: function () { var m = {}; this.piezas.forEach(function (p) { m[p.clave] = p; }); return m; },
      loc: function () { return this.porClave.localizacion; },
      det: function () { return this.porClave.detalle; },
      textoElemento: function () {
        var el = this.elemento;
        if (this.etiqueta) return this.etiqueta;
        if (!el) return '';
        return [el.id_elemento, el.ejes, el.nivel_rango].filter(Boolean).join(' · ');
      },
      locParaVisor: function () { return this.paraVisor(this.loc); },
      detParaVisor: function () { return this.paraVisor(this.det); },
      paginaApertura: function () {
        return (this.locParaVisor && this.locParaVisor.pagina) || (this.detParaVisor && this.detParaVisor.pagina) || this.paginaInicial || 0;
      },
      puedeAbrir: function () { return this.base === 'listo' && !this.sinPlano; },
      notaApertura: function () {
        if (this.locParaVisor || this.detParaVisor) return '';
        return this.paginaInicial && this.notaPagina ? this.notaPagina : '';
      },
      resumenEstados: function () {
        var r = {};
        this.piezas.forEach(function (p) { r[p.clave] = p.estado === 'ok' ? p.origen : p.estado; });
        return r;
      }
    },
    watch: {
      resumenEstados: { deep: true, handler: function (v) { this.$emit('ubicado', v); } },
      obraId: function () { this.cargar(); },
      uid: function () { this.cargar(); }
    },
    created: function () { this.cargar(); },
    beforeUnmount: function () { this.limpiar(); },
    methods: {
      paraVisor: function (p) {
        if (!p || p.estado !== 'ok' || !p.rect) return null;
        return { pagina: p.pagina, rect: p.rect, origen: p.origen };
      },
      limpiar: function () {
        this.piezas.forEach(function (p) { soltar(p.url); p.url = ''; });
      },
      reiniciar: function () {
        this.limpiar();
        this.piezas.forEach(function (p) { p.estado = 'cargando'; p.motivo = ''; p.origen = ''; p.fuente = ''; p.pagina = null; p.rect = null; p.error = ''; p.por = ''; p.en = ''; });
        this.elemento = null; this.sinPlano = false; this.motivoPlano = ''; this.errorBase = '';
      },
      pendiente: function (clave, motivo) {
        var p = this.porClave[clave]; p.estado = 'pendiente'; p.motivo = motivo; p.rect = null; p.pagina = null;
      },
      cargar: function () {
        var self = this, n = ++this.n;
        this.reiniciar();
        this.base = 'cargando';
        if (this.hayPlano === false) {   // el tablero ya dice que no hay plano vigente: no se pide el índice (evita un 409 inútil)
          this.base = 'listo'; this.sinPlano = true; this.motivoPlano = 'La obra no tiene plano vigente: sube primero el vectorial y el sellado.';
          this.piezas.forEach(function (p) { self.pendiente(p.clave, self.motivoPlano); });
          return;
        }
        leerIndice(this.obraId).then(function (ind) {
          if (n !== self.n) return;
          self.plano = ind && ind.plano ? ind.plano : null;
          self.base = 'listo';
          self.resolver(n);
        }, function (e) {
          if (n !== self.n) return;
          if (e && e.estado === 409) {
            self.base = 'listo'; self.sinPlano = true; self.motivoPlano = e.mensaje || 'La obra no tiene plano vigente.';
            self.piezas.forEach(function (p) { self.pendiente(p.clave, self.motivoPlano); });
            return;
          }
          self.base = 'error'; self.errorBase = (e && e.mensaje) || 'No se pudo leer el plano de la obra.';
          self.piezas.forEach(function (p) { p.estado = 'error'; p.error = self.errorBase; });
        });
      },
      resolver: function (n) {
        var self = this;
        if (this.recuadros) {
          ['localizacion', 'detalle'].forEach(function (c) { self.desdeRecorte(c, self.recuadros[c], n); });
          return;
        }
        if (!this.uid) {
          var m = this.motivoSinElemento || 'Esta duda no está atada a un elemento del plano: no se adivina su ubicación.';
          this.piezas.forEach(function (p) { self.pendiente(p.clave, m); });
          return;
        }
        leerElementos(this.obraId).then(function (lista) {
          if (n !== self.n) return;
          var el = lista.filter(function (x) { return x.uid === self.uid; })[0] || null;
          if (!el) {
            self.piezas.forEach(function (p) { self.pendiente(p.clave, 'El elemento ya no está entre los elementos de diseño de la obra (puede haber cambiado el plano).'); });
            return;
          }
          self.elemento = el;
          var faltan = [];
          [['localizacion', el.recorte_planta], ['detalle', el.recorte_detalle]].forEach(function (par) {
            var r = par[1] || {};
            if (rectValido(r.rect) && r.estado === 'confirmado') self.desdeRecorte(par[0], r, n);
            else faltan.push(par[0]);
          });
          if (faltan.length) self.proponer(faltan, n);
        }, function (e) {
          if (n !== self.n) return;
          self.piezas.forEach(function (p) { p.estado = 'error'; p.error = (e && e.mensaje) || 'No se pudieron leer los elementos de la obra.'; });
        });
      },
      desdeRecorte: function (clave, r, n) {
        if (!r || !rectValido(r.rect)) { this.pendiente(clave, 'Todavía no hay recuadro confirmado para este elemento.'); return; }
        var vigente = this.plano ? this.plano.id : null;
        if (r.plano_id !== undefined && r.plano_id !== null && vigente !== null && r.plano_id !== vigente) {
          this.pendiente(clave, 'El recuadro guardado es del plano n.º ' + r.plano_id + ', que ya no es el vigente (el vigente es el n.º ' + vigente + '). Hay que volver a confirmarlo.');
          return;
        }
        this.mostrar(clave, { origen: 'confirmado', pagina: r.pagina, rect: r.rect, por: r.confirmado_por || '', en: r.confirmado_en || '' }, n);
      },
      proponer: function (claves, n) {
        var self = this;
        leerPropuesta(this.obraId, this.uid).then(function (r) {
          if (n !== self.n) return;
          claves.forEach(function (c) {
            var p = r && r[c];
            if (p && rectValido(p.rect) && p.pagina) self.mostrar(c, { origen: 'propuesta', pagina: p.pagina, rect: p.rect, fuente: textoFuente(p.fuente) }, n);
            else self.pendiente(c, (p && p.motivo) || 'El programa no pudo proponer un recuadro y no se adivina.');
          });
        }, function (e) {
          if (n !== self.n) return;
          claves.forEach(function (c) { var p = self.porClave[c]; p.estado = 'error'; p.error = (e && e.mensaje) || 'No se pudo pedir la propuesta.'; });
        });
      },
      mostrar: function (clave, d, n) {
        var self = this, p = this.porClave[clave];
        p.origen = d.origen; p.pagina = d.pagina; p.rect = d.rect; p.fuente = d.fuente || ''; p.por = d.por || ''; p.en = d.en || '';
        p.estado = 'cargando'; p.error = '';
        vistaPrevia(this.obraId, this.plano ? this.plano.id : 0, clave, d.pagina, d.rect).then(function (blob) {
          if (n !== self.n) return;
          soltar(p.url);
          p.url = URL.createObjectURL(blob);
          p.estado = 'ok';
        }, function (e) {
          if (n !== self.n) return;
          p.estado = 'error'; p.error = (e && e.mensaje) || 'No se pudo generar la imagen.';
        });
      },
      reintentarPieza: function () { this.cargar(); },
      abrir: function () { this.abierto = true; this.$emit('abrir'); },
      alCerrar: function () { this.abierto = false; this.$emit('cerrar'); },
      fechaTxt: function (v) { return C.formato.fechaHora(v) || ''; },
      aviso: function (p) {
        if (p.estado !== 'ok') return '';
        return p.origen === 'propuesta' ? 'Propuesta, pendiente de verificar' : 'Confirmado';
      }
    },
    template: `
      <section class="vr" :aria-labelledby="id + '-t'" data-visor-revision>
        <header class="vr-cab">
          <h3 :id="id + '-t'" class="vr-t">Ubicación en el plano</h3>
          <p v-if="textoElemento" class="vr-el">Elemento del plano: <b class="num" data-visor-elemento>{{ textoElemento }}</b></p>
          <p v-if="elemento && elemento.revisar_motivo" class="vr-nota"><Icono nombre="info"/>{{ elemento.revisar_motivo }}</p>
        </header>

        <div v-if="base === 'cargando'" class="cargando" aria-busy="true" aria-live="polite"><span class="sr">Cargando el plano…</span><span class="hueso" style="--i:0"></span><span class="hueso" style="--i:1"></span></div>
        <div v-else-if="base === 'error'" class="error" role="alert">
          <Icono nombre="alerta"/>
          <div><p class="error-t">No se pudo leer el plano de la obra.</p><p>{{ errorBase }}</p><button type="button" class="btn btn-sec" data-reintentar-visor @click="cargar">Reintentar</button></div>
        </div>
        <template v-else>
          <div class="vr-piezas">
            <section v-for="p in piezas" :key="p.clave" class="vr-pieza" :class="'vr-' + p.estado" :data-pieza="p.clave" :data-estado="p.estado">
              <h4 class="vr-pt">{{ p.titulo }} <span class="vr-sub">{{ p.sub }}</span></h4>
              <div v-if="p.estado === 'cargando'" class="vr-marco cargando" aria-busy="true" role="status"><span class="sr">Cargando {{ p.titulo.toLowerCase() }}…</span><span class="hueso" style="--i:0"></span></div>
              <figure v-else-if="p.estado === 'ok'" class="vr-fig">
                <img class="vr-img" :src="p.url" :alt="(p.clave === 'localizacion' ? 'Planta completa del nivel con el recuadro rojo' : 'Detalle del plano') + (textoElemento ? ' de ' + textoElemento : '')" data-pieza-img>
                <figcaption class="vr-leyenda">
                  <span class="vr-sello" :class="p.origen === 'propuesta' ? 'es-propuesta' : 'es-confirmado'"><Icono :nombre="p.origen === 'propuesta' ? 'info' : 'check'"/>{{ aviso(p) }}</span>
                  <span v-if="p.fuente" class="vr-fuente">Fuente: {{ p.fuente }}</span>
                  <span class="vr-fuente">Hoja del plano: p. <span class="num">{{ p.pagina }}</span></span>
                  <span v-if="p.por" class="vr-fuente">Confirmado por {{ p.por }}<template v-if="fechaTxt(p.en)"> · {{ fechaTxt(p.en) }}</template></span>
                </figcaption>
              </figure>
              <div v-else-if="p.estado === 'pendiente'" class="vr-marco vr-falta">
                <p><Pendiente/></p>
                <p class="vr-motivo" data-motivo>{{ p.motivo }}</p>
              </div>
              <div v-else class="vr-marco error" role="alert">
                <Icono nombre="alerta"/>
                <div><p class="error-t">No se pudo mostrar {{ p.titulo.toLowerCase() }}.</p><p>{{ p.error }}</p><button type="button" class="btn btn-sec" data-reintentar-pieza @click="reintentarPieza">Reintentar</button></div>
              </div>
            </section>
          </div>

          <div class="vr-acc">
            <button type="button" class="btn btn-sec" :disabled="!puedeAbrir" data-abrir-plano @click="abrir"><Icono nombre="plano"/>Abrir plano</button>
            <p v-if="sinPlano" class="ayuda vr-motivo">{{ motivoPlano }}</p>
            <p v-else-if="notaApertura" class="ayuda">{{ notaApertura }}</p>
            <p v-else-if="!locParaVisor && !detParaVisor" class="ayuda">Sin recuadro: «Abrir plano» muestra la primera hoja del índice y no marca nada.</p>
          </div>
        </template>

        <VisorPlano v-if="abierto" :obra-id="obraId" :pagina="paginaApertura" :localizacion="locParaVisor" :detalle="detParaVisor" :etiqueta="textoElemento"
          :nota="notaApertura" @cerrar="alCerrar"/>
      </section>`
  };

  C.visor = { olvidar: olvidar, leerIndice: leerIndice, leerElementos: leerElementos };
})();
