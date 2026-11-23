/* CATDIC-WEB · pestaña «Planos y ficha» de la obra (B3b).
   props   obra (fila de `proyectos` del tablero) · datos (respuesta de GET /api/dashboard)
   emite   actualizar  (se subió un plano nuevo: la pantalla de la obra relee el tablero)
   Muestra: el plano vigente (Z14a, de `planos_vigentes[id]`), el historial (GET /api/proyectos/{id}/planos), «Cambiar plano» o
   «Subir planos» (FormularioPlanos, modo cambiar: A11 y A28), el editor de recuadros (EditorPlano, M4: ruta
   #/obra/<id>/planos?visor=1[&elemento=<uid>]), «Datos de la obra» (DatosObra, M5), el enlace «Dudas de la obra: N» (A15) y
   «Confirmar datos del plano» (ConfirmarPlano, M6, B3c: ruta #/obra/<id>/planos?confirmar=1[&tabla=<id>]; A14: solo con plano vigente).
   Con ?subir=1 en la ruta el diálogo «Subir planos» se abre solo (y la dirección queda limpia).
   Ningún POST se reintenta solo. Un elemento de diseño se identifica por su `uid`, nunca por `id_elemento`. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};

  function corto(h) { return typeof h === 'string' && h ? h.slice(0, 12) : null; }

  C.componentes.PestanaPlanos = {
    props: {
      obra: { type: Object, required: true },
      datos: { type: Object, required: true }
    },
    emits: ['actualizar'],
    data: function () {
      return {
        estadoH: 'cargando', mensajeH: '', historial: [], nH: 0,
        estadoD: 'cargando', nDudas: null, nD: 0,
        dialogo: '', datosObra: false, aviso: null
      };
    },
    computed: {
      ruta: function () { return C.rutas.ruta; },
      pv: function () { return (this.datos.planos_vigentes || {})[this.obra.id] || null; },
      hayPlano: function () { return !!this.pv; },
      conVisor: function () { return !!(this.ruta.consulta && this.ruta.consulta.visor === '1'); },
      conConfirmar: function () { return !!(this.ruta.consulta && this.ruta.consulta.confirmar === '1'); },
      hrefConfirmar: function () { return C.rutas.hashConfirmarPlano(this.obra.id); },
      uidVisor: function () { return this.ruta.consulta && this.ruta.consulta.elemento ? String(this.ruta.consulta.elemento) : ''; },
      tituloDialogo: function () { return this.hayPlano ? 'Cambiar plano' : 'Subir planos'; },
      campos: function () {
        var p = this.pv, f = C.formato;
        if (!p) return [];
        var rev = (p.revision !== null && p.revision !== undefined ? 'Rev. ' + p.revision : null);
        var et = f.texto(p.etiqueta_revision);
        return [
          { etiqueta: 'Revisión', valor: rev ? rev + (et ? ' · ' + et : '') : null },
          { etiqueta: 'Fecha del plano', valor: f.fecha(p.fecha_plano) || 'sin fecha de plano' },
          { etiqueta: 'Certificado por', valor: f.texto(p.certificado_por) },
          { etiqueta: 'Certificado el', valor: f.fechaHora(p.certificado_en) },
          { etiqueta: 'Vectorial (sha256)', valor: corto(p.vectorial_sha256) },
          { etiqueta: 'Sellado (sha256)', valor: corto(p.sellado_sha256) }
        ];
      },
      estadoBloqueH: function () { return this.estadoH === 'listo' && !this.historial.length ? 'vacio' : this.estadoH; },
      textoDudas: function () {
        if (this.estadoD === 'cargando') return 'Dudas de la obra: …';
        return this.nDudas === null ? 'Dudas de la obra' : 'Dudas de la obra: ' + this.nDudas;
      },
      hrefDudas: function () { return C.rutas.hashMesaObra(this.obra.id); },
      hrefVisor: function () { return C.rutas.hashVisorPlano(this.obra.id); },
      cuentaH: function () { return C.cola.plural(this.historial.length, 'revisión', 'revisiones'); }
    },
    created: function () {
      this.leerHistorial(); this.leerDudas();
      if (this.ruta.consulta && this.ruta.consulta.subir) {
        this.dialogo = 'plano';
        C.rutas.reemplazar(C.rutas.hashObra(this.obra.id, 'planos'));   // recargar no vuelve a abrir el diálogo
      }
    },
    methods: {
      leerHistorial: function () {
        var self = this, n = ++this.nH;
        this.estadoH = 'cargando'; this.mensajeH = '';
        return C.api.get('/api/proyectos/' + encodeURIComponent(this.obra.id) + '/planos').then(function (d) {
          if (n !== self.nH) return;
          if (!d || !Array.isArray(d.planos)) { self.mensajeH = 'El servidor respondió algo que no se pudo leer.'; self.estadoH = 'error'; return; }
          self.historial = d.planos; self.estadoH = 'listo';
        }, function (e) {
          if (n !== self.nH) return;
          self.mensajeH = (e && e.mensaje) || 'No se pudo leer el historial de planos.'; self.estadoH = 'error';
        });
      },
      leerDudas: function () {
        var self = this, n = ++this.nD;
        this.estadoD = 'cargando';
        return C.api.get('/api/dudas', { consulta: { resuelta: 'false', sin_visita: 'true', proyecto_id: this.obra.id } }).then(function (d) {
          if (n !== self.nD) return;
          self.nDudas = Array.isArray(d) ? d.length : null; self.estadoD = Array.isArray(d) ? 'listo' : 'error';
        }, function () {
          if (n !== self.nD) return;
          self.nDudas = null; self.estadoD = 'error';
        });
      },
      abrirPlano: function () { this.aviso = null; this.dialogo = 'plano'; },
      cerrarPlano: function () { this.dialogo = ''; },
      // A28: el aviso final con la revisión, los elementos marcados y el aviso de páginas.
      hecho: function (r) {
        var p = r.plano || {}, n = r.proyecto && r.proyecto.nombre ? r.proyecto.nombre : this.obra.nombre || this.obra.id;
        var partes = [n + ': plano rev. ' + (p.revision !== undefined && p.revision !== null ? p.revision : '(pendiente de verificar)') + ' vigente'];
        if (p.elementos_marcados) partes.push(p.elementos_marcados + ' elementos marcados «plano cambiado: revisar»');
        if (p.aviso_paginas) partes.push(String(p.aviso_paginas));
        this.dialogo = '';
        this.aviso = { texto: partes.join(' · ') + '.', pendiente: 'Quedan dudas por responder: equivalencias E-n ↔ nivel, tipos de losa y emparejamiento de hojas.' };
        C.visor.olvidar(this.obra.id);
        this.$emit('actualizar');
        this.leerHistorial(); this.leerDudas();
      },
      abrirDatos: function () { this.datosObra = true; },
      cerrarDatos: function () { this.datosObra = false; },
      datosGuardados: function () { this.leerDudas(); },
      abrirDatosDesdeAviso: function () { this.datosObra = true; },
      cerrarEditor: function () {
        if (C.rutas.vinoDeDentro) { C.rutas.vinoDeDentro = false; history.back(); }
        else C.rutas.reemplazar(C.rutas.hashObra(this.obra.id, 'planos'));
      },
      // «Cerrar» de Confirmar: con Atrás si se entró desde esta pestaña; si no (recarga, enlace o regreso de la Mesa), sustituyendo la entrada.
      cerrarConfirmar: function () {
        if (C.rutas.vinoDeDentroConfirmar) { C.rutas.vinoDeDentroConfirmar = false; history.back(); }
        else C.rutas.reemplazar(C.rutas.hashObra(this.obra.id, 'planos'));
      },
      elementoElegido: function (uid) { C.rutas.reemplazar(C.rutas.hashVisorPlano(this.obra.id, uid)); },
      fecha: function (v) { return C.formato.fecha(v); },
      txt: function (v) { return C.formato.texto(v); },
      fh: function (v) { return C.formato.fechaHora(v); },
      vigente: function (p) { return p.estado === 'vigente'; }
    },
    template: `
      <div class="pestana-planos">
        <section class="caja" aria-labelledby="pp-vig" data-plano-vigente>
          <div class="caja-cabeza"><h2 id="pp-vig">Plano vigente</h2></div>
          <template v-if="hayPlano">
            <Cajetin :campos="campos"/>
            <p class="ayuda pp-nota">El vectorial es la fuente de lectura y el sellado es la referencia legal; las huellas sha256 de abajo identifican cada archivo.</p>
          </template>
          <div v-else class="vacio" data-sin-plano>
            <p class="vacio-t">Sin plano vigente</p>
            <p>Sube el plano vectorial y el sellado de esta obra para ver los recuadros y confirmar los datos del plano.</p>
          </div>

          <div class="acc-botones pv-botones">
            <button v-if="!hayPlano" type="button" class="btn btn-pri" data-abrir-plano-dlg @click="abrirPlano"><Icono nombre="subir"/>Subir planos</button>
            <button v-else type="button" class="btn btn-sec" data-abrir-plano-dlg @click="abrirPlano"><Icono nombre="subir"/>Cambiar plano</button>
            <a v-if="hayPlano" class="btn btn-pri" :href="hrefVisor" data-ver-plano><Icono nombre="plano"/>Ver plano y recuadros</a>
            <button type="button" class="btn btn-sec" data-abrir-datos @click="abrirDatos"><Icono nombre="info"/>Datos de la obra</button>
            <a class="btn btn-sec" :href="hrefDudas" data-dudas-obra><Icono nombre="pregunta"/>{{ textoDudas }}</a>
          </div>
          <p v-if="estadoD === 'error'" class="ayuda" role="status" data-error-dudas>No se pudieron contar las dudas de la obra. <button type="button" class="btn btn-sec pp-reint" @click="leerDudas">Reintentar</button></p>
          <p v-if="hayPlano" class="ayuda">«Cambiar plano»: el plano nuevo queda vigente; el anterior pasa al histórico y los elementos ya extraídos de él se marcan «plano cambiado: revisar».</p>

          <div v-if="aviso" class="aviso aviso-ok" role="status" data-aviso-plano>
            <div>
              <p><Icono nombre="check"/>{{ aviso.texto }}</p>
              <p class="ayuda">{{ aviso.pendiente }} <button type="button" class="btn btn-sec pp-reint" @click="abrirDatosDesdeAviso">Datos de la obra</button></p>
            </div>
            <button type="button" class="btn btn-sec" aria-label="Cerrar el aviso" @click="aviso = null"><Icono nombre="cerrar"/></button>
          </div>
        </section>

        <section class="caja pp-hist" aria-labelledby="pp-hist" data-historial-planos>
          <div class="caja-cabeza"><h2 id="pp-hist">Historial de planos</h2><p v-if="estadoH === 'listo' && historial.length" class="cola-cuenta num">{{ cuentaH }}</p></div>
          <Bloque :estado="estadoBloqueH" :huesos="3" vacio-titulo="Esta obra todavía no tiene planos subidos"
            vacio-texto="Cuando subas el vectorial y el sellado, cada revisión quedará aquí con su estado y quién la certificó."
            error-titulo="No se pudo leer el historial de planos." :error-mensaje="mensajeH" @reintentar="leerHistorial">
            <ul class="pp-lista">
              <li v-for="p in historial" :key="p.id" class="pp-f" :class="{ 'es-vigente': vigente(p) }" data-plano-fila>
                <div class="pp-rev"><b class="num">Rev. {{ p.revision }}</b><span v-if="txt(p.etiqueta_revision)" class="pp-et">{{ p.etiqueta_revision }}</span></div>
                <div class="pp-fecha"><span class="cola-r" aria-hidden="true">Fecha del plano</span><span v-if="fecha(p.fecha_plano)" class="num">{{ fecha(p.fecha_plano) }}</span><span v-else class="ayuda">sin fecha de plano</span></div>
                <div class="pp-estado"><span class="est" :class="vigente(p) ? 'est-ok' : 'est-sin'"><Icono :nombre="vigente(p) ? 'check' : 'reloj'"/>{{ vigente(p) ? 'Vigente' : 'Histórico' }}</span></div>
                <div class="pp-cert"><span class="cola-r" aria-hidden="true">Certificó</span><template v-if="txt(p.certificado_por)">{{ p.certificado_por }}<template v-if="fh(p.certificado_en)"> · <span class="num">{{ fh(p.certificado_en) }}</span></template></template><Pendiente v-else/></div>
              </li>
            </ul>
          </Bloque>
        </section>

        <section class="caja" aria-labelledby="pp-conf" data-confirmar-datos>
          <div class="caja-cabeza"><h2 id="pp-conf">Confirmar datos del plano</h2></div>
          <p>Revisa las tablas que el programa leyó del plano vigente (acero en losa, zapata de muro lindero, f'c por rango, losa aligerada) junto al recorte del plano, y confirma sus valores. Nada se confirma solo.</p>
          <div class="acc-botones pv-botones">
            <a v-if="hayPlano" class="btn btn-pri" :href="hrefConfirmar" data-confirmar-plano><Icono nombre="check"/>Confirmar datos del plano</a>
            <button v-else type="button" class="btn btn-pri" disabled aria-describedby="pp-conf-motivo" data-confirmar-plano><Icono nombre="check"/>Confirmar datos del plano</button>
          </div>
          <p v-if="!hayPlano" id="pp-conf-motivo" class="ayuda" data-confirmar-sin-plano>No disponible: esta obra no tiene plano vigente. Sube el vectorial y el sellado para poder confirmar sus datos.</p>
        </section>

        <section v-if="conConfirmar && !hayPlano" class="caja" aria-labelledby="pp-sc" data-confirmar-sin-plano-pantalla>
          <div class="caja-cabeza"><h2 id="pp-sc">Confirmar datos del plano</h2></div>
          <p class="vacio-t">Esta obra no tiene plano vigente.</p>
          <p>Las tablas se leen del plano vigente. Sube primero el vectorial y el sellado.</p>
          <div class="acc-botones"><button type="button" class="btn btn-pri" @click="abrirPlano"><Icono nombre="subir"/>Subir planos</button><button type="button" class="btn btn-sec" @click="cerrarConfirmar">Volver a la pestaña</button></div>
        </section>
        <ConfirmarPlano v-if="conConfirmar && hayPlano" :obra="obra" @cerrar="cerrarConfirmar" @actualizar="$emit('actualizar')"/>

        <section v-if="conVisor && !hayPlano" class="caja" aria-labelledby="pp-sv" data-visor-sin-plano>
          <div class="caja-cabeza"><h2 id="pp-sv">Editor de recuadros</h2></div>
          <p class="vacio-t">Esta obra no tiene plano vigente.</p>
          <p>El editor necesita el plano. Sube primero el vectorial y el sellado.</p>
          <div class="acc-botones"><button type="button" class="btn btn-pri" @click="abrirPlano"><Icono nombre="subir"/>Subir planos</button><button type="button" class="btn btn-sec" @click="cerrarEditor">Volver a la pestaña</button></div>
        </section>
        <EditorPlano v-if="conVisor && hayPlano" :obra="obra" :uid-inicial="uidVisor" @cerrar="cerrarEditor" @elemento="elementoElegido"/>

        <FormularioPlanos v-if="dialogo === 'plano'" modo="cambiar" :proyecto="{ id: obra.id, nombre: obra.nombre }" :titulo="tituloDialogo" @hecho="hecho" @cancelar="cerrarPlano"/>
        <DatosObra v-if="datosObra" :obra="obra" @cerrar="cerrarDatos" @guardado="datosGuardados"/>
      </div>`
  };
})();
