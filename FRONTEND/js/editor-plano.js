/* CATDIC-WEB · Editor de recuadros del plano (B3b). Es la pantalla M4 del inventario (A34–A44) con ruta propia:
     #/obra/<id>/planos?visor=1[&elemento=<uid>]
   Reutiliza VisorPlano (js/visor-revision.js) para la hoja, el zoom, el desplazamiento y el selector de hoja, y le añade:
   el panel del elemento (selector, «Proponer recuadros», tipo, estado, «Usar propuesta», «Confirmar y guardar», «Vista previa»),
   las cajas sobre la hoja (confirmado = trazo continuo, propuesto = discontinuo, sin guardar = punteado; cada una con su texto)
   y el dibujo por arrastre con ratón o dedo (un arrastre de menos de 5 pt se descarta).

   props   obra (Object, obligatoria: fila de `proyectos`) · uidInicial (String: ?elemento=<uid> de la ruta)
   eventos cerrar · elemento(uid)  (para dejar el elemento elegido en la dirección)

   Un elemento se identifica SIEMPRE por su `uid`: el mismo id_elemento se repite en varios niveles.
   Teclado: el dibujo por arrastre no tiene equivalente de teclado razonable; con teclado se puede «Proponer recuadros»,
   «Usar propuesta», «Confirmar y guardar» y «Vista previa» (todos son botones), y mover o acercar la hoja con las teclas del visor.
   Ningún PUT o POST se reintenta solo, y un envío en curso bloquea su botón (no hay doble envío).
   Tras guardar un recuadro se llama a C.visor.olvidar(obra.id): la Mesa y el visor de revisión no muestran uno viejo. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};

  var TIPOS = [{ tipo: 'localizacion', titulo: 'LOCALIZACION', sigla: 'LOC' }, { tipo: 'detalle', titulo: 'DETALLE', sigla: 'DET' }];
  var contador = 0;

  function enc(s) { return encodeURIComponent(s); }
  function rectOk(r) { return Array.isArray(r) && r.length === 4 && r.every(function (v) { return typeof v === 'number' && isFinite(v); }); }
  function fmtRect(x) { return 'p' + x.pagina + ' · [' + x.rect.map(function (n) { return Math.round(n); }).join(', ') + '] pt'; }
  function soltar(u) { if (u) { try { URL.revokeObjectURL(u); } catch (e) { /* nada */ } } }

  C.componentes.EditorPlano = {
    props: {
      obra: { type: Object, required: true },
      uidInicial: { type: String, default: '' }
    },
    emits: ['cerrar', 'elemento'],
    data: function () {
      contador++;
      return {
        id: 'ed' + contador, tipos: TIPOS,
        estadoEl: 'cargando', mensajeEl: '', elementos: [], planoVigente: null,
        uid: '', tipo: 'localizacion', herramienta: 'dibujar',
        propuestas: null, ocupadoProp: false,
        borrador: { localizacion: null, detalle: null },
        previas: { localizacion: '', detalle: '' }, cargandoPrevia: { localizacion: false, detalle: false },
        guardando: { localizacion: false, detalle: false },
        error: '', mensaje: '', pagina: 0, salto: null, nSalto: 0, nEl: 0, avisoUid: ''
      };
    },
    computed: {
      elegido: function () {
        var u = this.uid;
        return u ? (this.elementos.filter(function (e) { return e.uid === u; })[0] || null) : null;
      },
      textoElemento: function () { return this.elegido ? this.textoOpcion(this.elegido) : ''; },
      sinElementos: function () { return this.estadoEl === 'listo' && !this.elementos.length; },
      herramientaEfectiva: function () { return this.elegido ? this.herramienta : 'mover'; },
      // Cajas sobre la hoja: lo guardado y confirmado del plano vigente, la propuesta aún no usada y lo que está sin guardar.
      cajas: function () {
        var self = this, out = [];
        if (!this.elegido) return out;
        TIPOS.forEach(function (t) {
          var g = self.guardadoDe(t.tipo), p = self.propuestaDe(t.tipo), b = self.borrador[t.tipo];
          if (g) out.push({ clave: t.tipo + ':confirmado', tipo: t.tipo, estado: 'confirmado', pagina: g.pagina, rect: g.rect, texto: t.sigla + ' confirmado' });
          if (p && !b) out.push({ clave: t.tipo + ':propuesto', tipo: t.tipo, estado: 'propuesto', pagina: p.pagina, rect: p.rect, texto: t.sigla + ' propuesto · pendiente de verificar' });
          if (b) out.push({ clave: t.tipo + ':sin_guardar', tipo: t.tipo, estado: 'sin_guardar', pagina: b.pagina, rect: b.rect, texto: t.sigla + ' sin guardar' });
        });
        return out;
      }
    },
    created: function () { this.leerElementos(); this.leerPlano(); },
    beforeUnmount: function () { soltar(this.previas.localizacion); soltar(this.previas.detalle); },
    methods: {
      textoOpcion: function (e) { return [e.id_elemento, e.ejes, e.nivel_rango].filter(Boolean).join(' · ') || e.uid; },
      leerPlano: function () {
        var self = this;
        C.visor.leerIndice(this.obra.id).then(function (ind) { self.planoVigente = ind && ind.plano ? ind.plano.id : null; }, function () { self.planoVigente = null; });
      },
      leerElementos: function () {
        var self = this, n = ++this.nEl;
        this.estadoEl = 'cargando'; this.mensajeEl = '';
        return C.api.get('/api/proyectos/' + enc(this.obra.id) + '/elementos').then(function (r) {
          if (n !== self.nEl) return;
          self.elementos = r && Array.isArray(r.elementos) ? r.elementos : [];
          self.estadoEl = 'listo';
          if (self.uidInicial && !self.uid) {
            if (self.elementos.some(function (e) { return e.uid === self.uidInicial; })) { self.uid = self.uidInicial; self.alElegir(true); }
            else self.avisoUid = 'El elemento de la dirección («' + self.uidInicial + '») ya no está entre los elementos de diseño de la obra.';
          }
        }, function (e) {
          if (n !== self.nEl) return;
          self.mensajeEl = (e && e.mensaje) || 'No se pudieron leer los elementos de la obra.'; self.estadoEl = 'error';
        });
      },
      // ---- lo guardado, lo propuesto y su texto (A44) ----
      guardadoDe: function (tipo) {
        var e = this.elegido; if (!e) return null;
        var g = tipo === 'localizacion' ? e.recorte_planta : e.recorte_detalle;
        if (!g || !rectOk(g.rect)) return null;
        // Un recuadro de otro plano (que ya no es el vigente) no cuenta como confirmado: hay que volver a confirmarlo.
        if (g.plano_id !== undefined && g.plano_id !== null && this.planoVigente !== null && g.plano_id !== this.planoVigente) return null;
        return g;
      },
      deOtroPlano: function (tipo) {
        var e = this.elegido; if (!e) return null;
        var g = tipo === 'localizacion' ? e.recorte_planta : e.recorte_detalle;
        if (g && rectOk(g.rect) && g.plano_id !== null && g.plano_id !== undefined && this.planoVigente !== null && g.plano_id !== this.planoVigente) return g;
        return null;
      },
      propuestaDe: function (tipo) {
        var p = this.propuestas && this.propuestas[tipo];
        return p && rectOk(p.rect) && p.pagina ? p : null;
      },
      rectActual: function (tipo) {
        var b = this.borrador[tipo], g = this.guardadoDe(tipo);
        return b ? { pagina: b.pagina, rect: b.rect } : (g ? { pagina: g.pagina, rect: g.rect } : null);
      },
      estadoRecuadro: function (tipo) {
        if (this.borrador[tipo]) return { texto: 'sin guardar', clase: 'est-proc', icono: 'info' };
        if (this.guardadoDe(tipo)) return { texto: 'confirmado', clase: 'est-ok', icono: 'check' };
        var p = this.propuestas && this.propuestas[tipo];
        if (p) return { texto: p.rect ? 'propuesto · pendiente de verificar' : 'pendiente de verificar', clase: 'est-cola', icono: 'pregunta' };
        return { texto: 'pendiente de verificar', clase: 'est-cola', icono: 'pregunta' };
      },
      detalleRecuadro: function (tipo) {
        var b = this.borrador[tipo], g = this.guardadoDe(tipo), p = this.propuestas && this.propuestas[tipo], o = this.deOtroPlano(tipo);
        if (b) return fmtRect(b) + ' (' + b.origen + ')';
        if (g) return fmtRect(g) + ' · ' + g.origen + (g.confirmado_por ? ' por ' + g.confirmado_por : '');
        if (p) {
          if (!p.rect) return p.motivo || 'El programa no pudo proponer un recuadro y no se adivina.';
          var f = p.fuente || {};
          return fmtRect(p) + ' · fuente: ' + (f.metodo || 'sin dato') + (f.rotulo ? ' «' + f.rotulo + '»' : '');
        }
        if (o) return 'El recuadro guardado (' + fmtRect(o) + ') es del plano n.º ' + o.plano_id + ', que ya no es el vigente (el vigente es el n.º ' + this.planoVigente + '). Hay que volver a confirmarlo.';
        return 'Sin recuadro: elige un elemento y pulsa «Proponer recuadros», o dibújalo.';
      },
      // ---- elegir elemento (A37) ----
      alElegir: function (inicial) {
        this.propuestas = null; this.borrador = { localizacion: null, detalle: null };
        this.limpiarPrevias(); this.mensaje = ''; this.error = ''; this.avisoUid = '';
        if (!inicial) this.$emit('elemento', this.uid);
        var g = this.guardadoDe(this.tipo) || this.guardadoDe('localizacion') || this.guardadoDe('detalle');
        if (g && g.pagina) this.irAHoja(g.pagina);
      },
      irAHoja: function (pagina) { this.salto = { pagina: pagina, n: ++this.nSalto }; },
      alHoja: function (p) { this.pagina = p; },
      limpiarPrevias: function () {
        soltar(this.previas.localizacion); soltar(this.previas.detalle);
        this.previas = { localizacion: '', detalle: '' };
      },
      // ---- proponer (A38) y usar la propuesta (A39) ----
      proponer: function () {
        var self = this, uid = this.uid;
        if (!uid || this.ocupadoProp) return;
        this.ocupadoProp = true; this.error = ''; this.mensaje = '';
        C.api.post('/api/proyectos/' + enc(this.obra.id) + '/elementos/' + enc(uid) + '/propuesta', undefined, { tiempo: 60000 }).then(function (r) {
          self.ocupadoProp = false;
          if (uid !== self.uid) return;   // se eligió otro elemento mientras tanto
          self.propuestas = r || {};
          var l = self.propuestaDe('localizacion');
          if (l) self.irAHoja(l.pagina);
        }, function (e) {
          self.ocupadoProp = false;
          self.error = (e && e.mensaje) || 'No se pudo pedir la propuesta.';
        });
      },
      usarPropuesta: function (tipo) {
        var p = this.propuestaDe(tipo);
        if (!p) return;
        this.borrador[tipo] = { pagina: p.pagina, rect: p.rect.slice(), origen: 'confirmado' };
        this.tipo = tipo; this.mensaje = ''; this.error = '';
        this.irAHoja(p.pagina);
      },
      // ---- dibujar (A40) ----
      alDibujar: function (d) {
        if (!this.elegido) return;
        this.borrador[this.tipo] = { pagina: d.pagina, rect: d.rect, origen: 'dibujado' };
        this.mensaje = ''; this.error = '';
      },
      // ---- guardar (A41) ----
      guardar: function (tipo) {
        var self = this, b = this.borrador[tipo], uid = this.uid;
        if (!b || !uid || this.guardando[tipo]) return;
        this.guardando[tipo] = true; this.error = ''; this.mensaje = '';
        C.api.put('/api/proyectos/' + enc(this.obra.id) + '/elementos/' + enc(uid) + '/recuadro', { tipo: tipo, pagina: b.pagina, rect: b.rect, origen: b.origen }).then(function (r) {
          self.guardando[tipo] = false;
          var g = r && r.guardado;
          if (!g) { self.error = 'El servidor no devolvió el recuadro guardado.'; return; }
          var el = self.elementos.filter(function (x) { return x.uid === uid; })[0];
          if (el) { if (tipo === 'localizacion') el.recorte_planta = g; else el.recorte_detalle = g; }
          self.borrador[tipo] = null;
          C.visor.olvidar(self.obra.id);   // la Mesa y el visor de revisión no deben mostrar un recuadro viejo
          if (uid === self.uid) {
            self.mensaje = (tipo === 'localizacion' ? 'LOCALIZACION' : 'DETALLE') + ' guardado (confirmado por ' + (g.confirmado_por || 'pendiente de verificar') + ').';
            self.vistaPrevia(tipo);
          }
        }, function (e) {
          self.guardando[tipo] = false;
          self.error = (e && e.mensaje) || 'No se pudo guardar el recuadro.';
        });
      },
      // ---- vista previa (A42) ----
      vistaPrevia: function (tipo) {
        var self = this, ra = this.rectActual(tipo);
        if (!ra || this.cargandoPrevia[tipo]) return;
        this.cargandoPrevia[tipo] = true; this.error = '';
        C.api.pedir('POST', '/api/proyectos/' + enc(this.obra.id) + '/visor/vista-previa', { cuerpo: { tipo: tipo, pagina: ra.pagina, rect: ra.rect }, respuesta: 'blob', tiempo: 90000 }).then(function (blob) {
          self.cargandoPrevia[tipo] = false;
          soltar(self.previas[tipo]);
          self.previas[tipo] = URL.createObjectURL(blob);
        }, function (e) {
          self.cargandoPrevia[tipo] = false;
          soltar(self.previas[tipo]); self.previas[tipo] = '';
          self.error = (e && e.mensaje) || 'No se pudo generar la vista previa.';
        });
      }
    },
    template: `
      <VisorPlano editor :obra-id="obra.id" :pagina="0" :cajas="cajas" :herramienta="herramientaEfectiva" :salto="salto" :etiqueta="textoElemento"
        leyenda-propia="Editor de recuadros: trazo continuo = confirmado, discontinuo = propuesto (pendiente de verificar), punteado = sin guardar."
        @cerrar="$emit('cerrar')" @hoja="alHoja" @dibujado="alDibujar">
        <template #panel>
          <div class="ed-panel" data-editor-plano>
            <h3 class="ed-t">Recuadros del elemento</h3>

            <div v-if="estadoEl === 'cargando'" class="cargando" aria-busy="true" aria-live="polite"><span class="sr">Cargando los elementos…</span><span class="hueso" style="--i:0"></span><span class="hueso" style="--i:1"></span></div>
            <div v-else-if="estadoEl === 'error'" class="error" role="alert" data-error-elementos>
              <Icono nombre="alerta"/>
              <div><p class="error-t">No se pudieron leer los elementos.</p><p>{{ mensajeEl }}</p><button type="button" class="btn btn-sec" data-reintentar-elementos @click="leerElementos">Reintentar</button></div>
            </div>
            <template v-else>
              <label class="campo-i-et" :for="id + '-el'">Elemento</label>
              <select :id="id + '-el'" class="campo-i" v-model="uid" :disabled="sinElementos" data-visor-elemento @change="alElegir(false)">
                <option value="">— elige un elemento —</option>
                <option v-for="e in elementos" :key="e.uid" :value="e.uid" :title="textoOpcion(e)">{{ textoOpcion(e) }}</option>
              </select>
              <p v-if="sinElementos" class="ed-aviso" data-sin-elementos><Icono nombre="info"/>Esta obra aún no tiene elementos de diseño: los recuadros se guardan por elemento.</p>
              <p v-if="avisoUid" class="ed-aviso" data-aviso-uid><Icono nombre="alerta"/>{{ avisoUid }}</p>
              <p v-if="elegido && elegido.revisar_motivo" class="ed-aviso" data-revisar-motivo><Icono nombre="info"/>{{ elegido.revisar_motivo }}</p>
            </template>

            <button type="button" class="btn btn-sec" data-proponer :disabled="!elegido || ocupadoProp" :aria-busy="ocupadoProp ? 'true' : null" @click="proponer"><Icono nombre="rayo"/>{{ ocupadoProp ? 'Proponiendo…' : 'Proponer recuadros' }}</button>

            <fieldset class="ed-herr" :disabled="!elegido">
              <legend>Qué hace el ratón o el dedo sobre la hoja</legend>
              <label class="radio"><input type="radio" value="dibujar" v-model="herramienta" data-herramienta="dibujar">Dibujar un recuadro</label>
              <label class="radio"><input type="radio" value="mover" v-model="herramienta" data-herramienta="mover">Mover la hoja</label>
            </fieldset>

            <section v-for="t in tipos" :key="t.tipo" class="ed-rec" :class="{ 'es-activo': tipo === t.tipo }" :data-recuadro="t.tipo">
              <label class="radio ed-rec-t"><input type="radio" name="ed-tipo" :value="t.tipo" v-model="tipo" :data-tipo="t.tipo"><b>{{ t.titulo }}</b></label>
              <p class="ed-rec-e"><span class="est" :class="estadoRecuadro(t.tipo).clase" data-estado-recuadro><Icono :nombre="estadoRecuadro(t.tipo).icono"/>{{ estadoRecuadro(t.tipo).texto }}</span></p>
              <p class="ed-rec-d num" data-detalle-recuadro>{{ detalleRecuadro(t.tipo) }}</p>
              <div class="ed-rec-b">
                <button v-if="propuestaDe(t.tipo)" type="button" class="btn btn-sec" data-usar :data-usar-tipo="t.tipo" @click="usarPropuesta(t.tipo)">Usar propuesta</button>
                <button type="button" class="btn btn-pri" data-guardar-recuadro :data-guardar-tipo="t.tipo" :disabled="!borrador[t.tipo] || guardando[t.tipo]" :aria-busy="guardando[t.tipo] ? 'true' : null" @click="guardar(t.tipo)">{{ guardando[t.tipo] ? 'Guardando…' : 'Confirmar y guardar' }}</button>
                <button type="button" class="btn btn-sec" data-previa :data-previa-tipo="t.tipo" :disabled="!rectActual(t.tipo) || cargandoPrevia[t.tipo]" :aria-busy="cargandoPrevia[t.tipo] ? 'true' : null" @click="vistaPrevia(t.tipo)">{{ cargandoPrevia[t.tipo] ? 'Generando…' : 'Vista previa' }}</button>
              </div>
              <img v-if="previas[t.tipo]" class="ed-previa" :src="previas[t.tipo]" :alt="'Vista previa de ' + t.titulo + (textoElemento ? ' de ' + textoElemento : '')" data-previa-img>
            </section>

            <p class="ayuda" data-ayuda-editor>Dibuja un recuadro arrastrando sobre la hoja; se aplica al tipo marcado. Las coordenadas se guardan en puntos del PDF vectorial. El dibujo es solo con ratón o dedo; con el teclado usa «Proponer recuadros» y «Usar propuesta».</p>
            <p v-if="error" class="dlg-error" role="alert" data-visor-error><Icono nombre="alerta"/>{{ error }}</p>
            <p v-if="mensaje" class="aviso aviso-ok ed-ok" role="status" data-visor-mensaje><span><Icono nombre="check"/>{{ mensaje }}</span></p>
          </div>
        </template>
      </VisorPlano>`
  };
})();
