/* CATDIC-WEB · pantalla «Mis obras» (B3a). Paridad Z14 y Z14a (matriz de proyectos y celda de plano vigente),
   accesos A11–A17 como enlaces a la pestaña que los construirá, y «Nueva obra» (M2 en modo nueva, A28).
   Lee las mismas rutas que Inicio (js/datos.js). Lo que falta se muestra «pendiente de verificar»;
   «sin plano vigente» es un estado real, no un dato que falte. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.pantallas = C.pantallas || {};

  C.pantallas['obras'] = {
    mixins: [C.datos.mixin],
    data: function () { return { dialogo: false, avisoNueva: null }; },
    computed: {
      estadoLista: function () {
        if (this.estadoTablero !== 'listo') return this.estadoTablero;
        return this.obrasOrdenadas.length ? 'listo' : 'vacio';
      },
      // Por obra: cuántas visitas, cuántas dudas abiertas y cuántas son de la obra (sin visita). null = no se pudo leer.
      resumenes: function () {
        var out = {}, self = this;
        this.proyectos.forEach(function (p) { out[p.id] = { visitas: 0, dudas: self.dudas ? 0 : null, dudasObra: self.dudas ? 0 : null }; });
        this.visitasTodas.forEach(function (v) { if (out[v.proyecto_id]) out[v.proyecto_id].visitas++; });
        (this.dudas || []).forEach(function (d) {
          var r = out[d.proyecto_id]; if (!r) return;
          r.dudas++; if (!d.visita_id) r.dudasObra++;
        });
        return out;
      },
      filas: function () {
        var self = this, f = C.formato;
        return this.obrasOrdenadas.map(function (p) {
          var pv = self.planos[p.id] || null, r = self.resumenes[p.id];
          var plano = null;
          if (pv) {
            var et = f.texto(pv.etiqueta_revision);
            plano = {
              rev: 'Rev. ' + pv.revision + (et ? ' · ' + et : ''),
              fecha: f.fecha(pv.fecha_plano), certificado: f.texto(pv.certificado_por),
              titulo: 'Vectorial sha256 ' + (pv.vectorial_sha256 || 'pendiente de verificar') + ' · Sellado sha256 ' + (pv.sellado_sha256 || 'pendiente de verificar')
            };
          }
          return {
            id: p.id, nombre: p.nombre, tipo: f.texto(p.tipo), formato: f.texto(p.formato_defecto), cliente: f.texto(p.cliente),
            supervisor: f.texto(p.supervisor), informe: f.texto(p.estado_informe), accion: f.texto(p.observaciones),
            supervision: p.tipo === 'Supervisión', plano: plano, visitas: r.visitas, dudas: r.dudas, dudasObra: r.dudasObra
          };
        });
      }
    },
    methods: {
      abrir: function () { this.avisoNueva = null; this.dialogo = true; },
      alCancelar: function (info) {
        this.dialogo = false;
        if (info && info.proyectoCreado) this.recargar();   // la obra se creó aunque los planos no se subieron
      },
      alHecho: function (r) {
        this.dialogo = false;
        var p = r.plano || {};
        var nombre = r.proyecto.nombre || r.proyecto.id;
        this.avisoNueva = {
          id: r.proyecto.id,
          texto: nombre + ': plano rev. ' + p.revision + ' vigente' +
            (p.elementos_marcados ? ' · ' + p.elementos_marcados + ' elementos marcados «plano cambiado: revisar»' : '') +
            (p.aviso_paginas ? ' · ' + p.aviso_paginas : '') +
            '. Quedan dudas por responder: equivalencias E-n ↔ nivel, tipos de losa y emparejamiento de hojas (se responden en la pestaña «Planos y ficha» de la obra).'
        };
        this.recargar();
      },
      hrefObra: function (id, pestana) { return C.rutas.hashObra(id, pestana); }
    },
    template: `
      <div class="pagina">
        <header class="pagina-cabeza">
          <h1 tabindex="-1">Mis obras</h1>
          <button type="button" class="btn btn-pri" @click="abrir"><Icono nombre="mas"/>Nueva obra</button>
        </header>

        <div v-if="avisoNueva" class="aviso aviso-ok" role="status">
          <div>
            <p><Icono nombre="check"/> {{ avisoNueva.texto }}</p>
            <a class="enlace" :href="hrefObra(avisoNueva.id, 'planos')">Abrir la obra nueva<Icono nombre="flecha"/></a>
          </div>
          <button type="button" class="btn btn-sec" @click="avisoNueva = null">Cerrar aviso</button>
        </div>

        <Bloque :estado="estadoDudas === 'error' ? 'error' : 'listo'" error-titulo="No se pudo leer la Mesa de Dudas." :error-mensaje="mensajeDudas" @reintentar="leerDudas"/>

        <section class="caja" aria-labelledby="t-lista">
          <div class="caja-cabeza"><h2 id="t-lista">Obras registradas</h2></div>
          <Bloque :estado="estadoLista" :huesos="4" vacio-titulo="Aún no hay obras."
            vacio-texto="Registra la primera obra con «Nueva obra»: se crea y se suben sus planos."
            error-titulo="No se pudo cargar el tablero." :error-mensaje="mensajeTablero" @reintentar="leerTablero">
            <ul class="obras-lista">
              <li v-for="o in filas" :key="o.id" class="of">
                <div class="of-cab">
                  <h3 class="of-nombre"><a :href="hrefObra(o.id, 'resumen')">{{ o.nombre }}</a></h3>
                  <p class="of-tipo"><template v-if="o.tipo">{{ o.tipo }}</template><Pendiente v-else/><template v-if="o.formato"> · {{ o.formato }}</template></p>
                </div>
                <dl class="of-datos">
                  <div><dt>Cliente</dt><dd><template v-if="o.cliente">{{ o.cliente }}</template><Pendiente v-else/></dd></div>
                  <div><dt>Supervisor</dt><dd><template v-if="o.supervisor">{{ o.supervisor }}</template><Pendiente v-else/></dd></div>
                  <div><dt>Estado del informe</dt><dd><template v-if="o.informe">{{ o.informe }}</template><Pendiente v-else/></dd></div>
                  <div class="of-plano"><dt>Plano vigente</dt>
                    <dd v-if="o.plano" :title="o.plano.titulo">
                      <span class="num">{{ o.plano.rev }}</span><br>
                      <span class="of-sub"><template v-if="o.plano.fecha"><span class="num">{{ o.plano.fecha }}</span></template><Pendiente v-else/>
                      · certificado por <template v-if="o.plano.certificado">{{ o.plano.certificado }}</template><Pendiente v-else/></span>
                    </dd>
                    <dd v-else><span class="etq">sin plano vigente</span></dd>
                  </div>
                  <div><dt>Visitas</dt><dd class="num">{{ o.visitas }}</dd></div>
                  <div><dt>Dudas abiertas</dt><dd class="num"><template v-if="o.dudas !== null">{{ o.dudas }}</template><Pendiente v-else/></dd></div>
                  <div class="of-accion"><dt>Próxima acción</dt><dd><template v-if="o.accion">{{ o.accion }}</template><Pendiente v-else/></dd></div>
                </dl>
                <p class="of-acc">
                  <a class="enlace" :href="hrefObra(o.id, 'planos')">Planos y ficha<Icono nombre="flecha"/></a>
                  <a v-if="o.supervision" class="enlace" :href="hrefObra(o.id, 'visitas')">Visitas<Icono nombre="flecha"/></a>
                  <a v-if="o.dudasObra > 0" class="enlace" :href="hrefObra(o.id, 'resumen')">Dudas de la obra: {{ o.dudasObra }}<Icono nombre="flecha"/></a>
                </p>
              </li>
            </ul>
          </Bloque>
        </section>

        <FormularioPlanos v-if="dialogo" modo="nueva" @hecho="alHecho" @cancelar="alCancelar"/>
      </div>`
  };
})();
