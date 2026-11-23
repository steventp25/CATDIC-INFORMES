/* CATDIC-WEB · pestañas «Avance» y «Cierre» de la obra (B3b).
   props   obra (fila de `proyectos` del tablero) · datos (respuesta de GET /api/dashboard)
   Avance: el indicador de avance por entrepisos (N8) «pendiente de verificar» (falta D15, Fase D-b) y, aparte, lo que sí se sabe
   hoy como HECHOS del registro (las visitas con su fecha, carpeta, clase y estado), nunca como porcentaje ni como medida de avance
   (N11: ningún indicador se calcula con el número de archivos, versiones o visitas).
   Cierre: los indicadores de expediente completo (N9) y documentación al día (N10), «pendiente de verificar» (D15, Fase D-b), y lo
   que hoy impide cerrar, como hechos con enlace: dudas abiertas, visitas sin procesar o con dudas, si hay plano vigente y los
   informes generados. No hay ningún «listo para cerrar» calculado: que no haya hechos pendientes no significa que la obra pueda cerrarse. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};

  C.componentes.PestanaAvance = {
    mixins: [C.obraHechos.mixin],
    computed: {
      vacioTexto: function () { return this.supervision ? 'Pulsa "Sincronizar desde Dropbox" en Inicio, o conecta la carpeta de visitas de la obra y sube una visita.' : 'Las visitas se leen solo en las obras de Supervisión.'; },
      dudasParaCola: function () { return this.estadoDudas === 'listo' ? this.dudas : null; }
    },
    template: `
      <div class="pestana-avance">
        <section class="caja" aria-labelledby="av-ind" data-avance-indicador>
          <div class="caja-cabeza"><h2 id="av-ind">Avance por entrepisos</h2></div>
          <div class="ind-rejilla ind-uno"><Indicador codigo="n8"/></div>
        </section>

        <ColaVisitas titulo="Lo que sí se sabe hoy: las visitas de la obra" estado="listo" :visitas="visitas" :proyectos="[obra]" :dudas="dudasParaCola" :vacio-texto="vacioTexto">
          <p class="ayuda cola-nota" data-hechos-no-avance>Son hechos del registro de visitas, no una medida de avance: el nombre de la carpeta dice los elementos y el nivel de cada visita, y no se interpreta. El avance por entrepisos se calcula en la Fase D-b, con la decisión D15.</p>
        </ColaVisitas>
      </div>`
  };

  C.componentes.PestanaCierre = {
    mixins: [C.obraHechos.mixin],
    computed: {
      sinProcesar: function () { return this.filasVisita; },
      hrefInformes: function () { return C.rutas.hashObra(this.obra.id, 'informes'); },
      hrefSubirPlanos: function () { return C.rutas.hashObra(this.obra.id, 'planos') + '?subir=1'; },
      hrefPlanos: function () { return C.rutas.hashObra(this.obra.id, 'planos'); },
      hrefMesaObra: function () { return C.rutas.hashMesaObra(this.obra.id); },
      hrefVisitas: function () { return C.rutas.hashObra(this.obra.id, 'visitas'); },
      estadoInformes: function () { return this.estadoInf; },
      conteoDudas: function () {
        var n = this.dudasLista.length;
        return { total: n, bq: this.bloqueantes, visita: this.dudasDeVisita.length, obra: this.dudasDeObra.length };
      }
    },
    template: `
      <div class="pestana-cierre">
        <section class="caja" aria-labelledby="ci-ind" data-cierre-indicadores>
          <div class="caja-cabeza"><h2 id="ci-ind">Indicadores del cierre</h2></div>
          <div class="ind-rejilla ind-dos"><Indicador codigo="n9"/><Indicador codigo="n10"/></div>
        </section>

        <section class="caja" aria-labelledby="ci-hechos" data-cierre-hechos>
          <div class="caja-cabeza"><h2 id="ci-hechos">Lo que hoy impide cerrar</h2></div>
          <p class="ayuda ci-nota">Son hechos del registro, cada uno con su enlace. No hay un «listo para cerrar» calculado: que aquí no quede nada pendiente no significa que la obra pueda cerrarse; el expediente y la documentación se evalúan en la Fase D-b.</p>

          <div class="ci-hecho" data-hecho="dudas">
            <h3 class="ci-t">Dudas abiertas</h3>
            <Bloque :estado="estadoDudas === 'listo' ? 'listo' : estadoDudas" :huesos="1" error-titulo="No se pudieron leer las dudas abiertas." :error-mensaje="mensajeDudas" @reintentar="leerDudas">
              <p v-if="!conteoDudas.total" class="ci-ok"><span class="est est-ok"><Icono nombre="check"/>Sin dudas abiertas</span></p>
              <template v-else>
                <p class="ci-n"><span class="est est-dudas"><Icono nombre="pregunta"/>{{ plural(conteoDudas.total, 'duda abierta', 'dudas abiertas') }}</span>
                  <template v-if="conteoDudas.bq"> · <b>{{ plural(conteoDudas.bq, 'bloqueante', 'bloqueantes') }}</b></template></p>
                <ul class="ci-enl">
                  <li v-if="conteoDudas.obra"><a class="enlace" :href="hrefMesaObra" data-ir-mesa-obra>{{ plural(conteoDudas.obra, 'duda de la obra (sin visita)', 'dudas de la obra (sin visita)') }}: abrir la Mesa<Icono nombre="flecha"/></a></li>
                  <li v-if="conteoDudas.visita"><a class="enlace" :href="hrefVisitas">{{ plural(conteoDudas.visita, 'duda en visitas', 'dudas en visitas') }}: ir a Visitas y trabajos<Icono nombre="flecha"/></a></li>
                </ul>
              </template>
            </Bloque>
          </div>

          <div class="ci-hecho" data-hecho="visitas">
            <h3 class="ci-t">Visitas sin procesar o con dudas</h3>
            <p v-if="!sinProcesar.length" class="ci-ok"><span class="est est-ok"><Icono nombre="check"/>Ninguna visita sin procesar ni con dudas</span></p>
            <ul v-else class="filas" data-filas-visitas>
              <li v-for="f in sinProcesar" :key="f.clave" class="fila" :class="{ 'es-bloq': f.bloq }">
                <a class="fila-a" :href="f.href">
                  <span class="f-tipo"><Icono v-if="f.bloq" nombre="alerta" class="ico-bloq"/>{{ f.tipo }}</span>
                  <span class="f-donde">{{ f.donde }}</span>
                  <span class="f-motivo">{{ f.motivo }}</span>
                  <span class="f-sig">{{ f.siguiente }}<Icono nombre="flecha"/></span>
                  <span class="f-dias num"><template v-if="etiquetaDias(f)">{{ etiquetaDias(f) }}</template><Pendiente v-else/></span>
                </a>
              </li>
            </ul>
          </div>

          <div class="ci-hecho" data-hecho="plano">
            <h3 class="ci-t">Plano vigente</h3>
            <p v-if="hayPlano" class="ci-n"><span class="est est-ok"><Icono nombre="check"/>Hay plano vigente</span> <span class="num">{{ textoPlano }}</span> · <a class="enlace" :href="hrefPlanos">Planos y ficha<Icono nombre="flecha"/></a></p>
            <p v-else class="ci-n"><span class="est est-mal"><Icono nombre="alerta"/>Sin plano vigente</span> · <a class="enlace" :href="hrefSubirPlanos" data-subir-planos-cierre>Subir planos<Icono nombre="flecha"/></a></p>
          </div>

          <div class="ci-hecho" data-hecho="informes">
            <h3 class="ci-t">Informes generados</h3>
            <Bloque :estado="estadoInformes === 'listo' && !informes.length ? 'vacio' : estadoInformes" :huesos="1" vacio-titulo="Esta obra todavía no tiene informes generados." error-titulo="No se pudo leer la lista de informes." :error-mensaje="mensajeInf" @reintentar="leerInformes">
              <p class="ci-n"><span class="est"><Icono nombre="info"/>{{ plural(informes.length, 'informe generado', 'informes generados') }}</span>
                · <a class="enlace" :href="hrefInformes">Ver los informes<Icono nombre="flecha"/></a></p>
            </Bloque>
          </div>
        </section>
      </div>`
  };
})();
