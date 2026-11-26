/* CATDIC-WEB · pestaña «Resumen» de la obra (B3b).
   props   obra (fila de `proyectos` del tablero) · datos (respuesta de GET /api/dashboard)
   emite   actualizar  (se subió una visita o se procesó la cola de la obra: la pantalla relee el tablero)
   Muestra: los 3 indicadores (siempre «pendiente de verificar», Fase D-b), los pendientes de la obra con datos reales y acceso
   directo (N12: dudas y visitas, plano vigente, elementos con «plano cambiado: revisar», últimos informes), la actividad reciente
   (Fase D-a) y las acciones rápidas, que reutilizan los flujos que ya existen (FormularioVisita, AccionesCola, «Hacer informe»
   de la pestaña Informes y el editor de recuadros). La Mesa de Dudas en modo obra (?dudas=obra) la pinta la pantalla de la obra.
   Cada bloque tiene sus estados de cargando, vacío y error; ningún dato se inventa. */
(function () {
  'use strict';
  var C = window.CATDIC = window.CATDIC || {};
  C.componentes = C.componentes || {};

  var MAX_ELEMENTOS = 5;

  C.componentes.PestanaResumen = {
    mixins: [C.obraHechos.mixin],
    emits: ['actualizar'],
    data: function () { return { dialogo: '', resultado: null }; },
    computed: {
      estadoPrior: function () {
        if (this.estadoDudas === 'cargando') return 'cargando';
        return this.filas.length ? 'listo' : (this.estadoDudas === 'error' ? 'listo' : 'vacio');
      },
      muestraElementos: function () { return this.revisar.slice(0, MAX_ELEMENTOS); },
      restanElementos: function () { return Math.max(0, this.revisar.length - MAX_ELEMENTOS); },
      estadoRevisar: function () {
        if (!this.hayPlano) return 'listo';
        if (this.estadoEl !== 'listo') return this.estadoEl;
        return this.revisar.length ? 'listo' : 'vacio';
      },
      estadoUltimos: function () { return this.estadoInf === 'listo' && !this.ultimosInformes.length ? 'vacio' : this.estadoInf; },
      hrefInformes: function () { return C.rutas.hashObra(this.obra.id, 'informes'); },
      hrefHacerInforme: function () { return C.rutas.hashObra(this.obra.id, 'informes') + '?hacer=1'; },
      hrefSubirPlanos: function () { return C.rutas.hashObra(this.obra.id, 'planos') + '?subir=1'; },
      hrefPlanos: function () { return C.rutas.hashObra(this.obra.id, 'planos'); },
      hrefVisor: function () { return C.rutas.hashVisorPlano(this.obra.id); },
      hrefMesaObra: function () { return C.rutas.hashMesaObra(this.obra.id); }
    },
    methods: {
      abrirSubir: function () { this.resultado = null; this.dialogo = 'subir'; },
      cerrarDialogo: function () { this.dialogo = ''; },
      hechoVisita: function (r) { this.dialogo = ''; this.resultado = r.resultado; this.$emit('actualizar'); this.leerDudas(); },
      alProcesar: function () { this.$emit('actualizar'); this.leerDudas(); this.leerInformes(); }
    },
    template: `
      <div class="pestana-resumen">
        <section class="caja" aria-labelledby="rs-ind" data-indicadores>
          <div class="caja-cabeza"><h2 id="rs-ind">Indicadores de la obra</h2></div>
          <p class="ayuda rs-nota">Los tres indicadores quedan «pendiente de verificar» hasta que Steven defina qué cuenta como entrepiso ejecutado y qué es una unidad documental (decisión D15). Mientras tanto no se muestra ninguna cifra ni barra, y no se calculan con el número de archivos, versiones o visitas.</p>
          <div class="ind-rejilla">
            <Indicador codigo="n8"/><Indicador codigo="n9"/><Indicador codigo="n10"/>
          </div>
        </section>

        <div class="rejilla-inicio">
          <div class="col-principal">
            <section class="caja" aria-labelledby="rs-pend" data-pendientes>
              <div class="caja-cabeza"><h2 id="rs-pend">Pendientes de la obra</h2></div>

              <h3 class="rs-sub" id="rs-dudas">Dudas y visitas</h3>
              <Bloque v-if="estadoDudas === 'error'" estado="error" error-titulo="No se pudieron leer las dudas abiertas." :error-mensaje="mensajeDudas" @reintentar="leerDudas"/>
              <p v-if="estadoDudas === 'error' && filas.length" class="ayuda">Mientras tanto se muestran las visitas según su estado; sin el conteo de dudas.</p>
              <Bloque :estado="estadoPrior" :huesos="3" vacio-titulo="No hay dudas abiertas ni visitas por procesar." vacio-texto="Cuando entre una visita o aparezca una duda de esta obra, saldrá aquí con su siguiente paso.">
                <ul class="filas" aria-labelledby="rs-dudas" data-filas-pendientes>
                  <li v-for="f in filas" :key="f.clave" class="fila" :class="{ 'es-bloq': f.bloq }">
                    <a class="fila-a" :href="f.href">
                      <span class="f-tipo"><Icono v-if="f.bloq" nombre="alerta" class="ico-bloq"/>{{ f.tipo }}</span>
                      <span class="f-donde">{{ f.donde }}</span>
                      <span class="f-motivo">{{ f.motivo }}</span>
                      <span class="f-sig">{{ f.siguiente }}<Icono nombre="flecha"/></span>
                      <span class="f-dias num"><template v-if="etiquetaDias(f)">{{ etiquetaDias(f) }}</template><Pendiente v-else/></span>
                    </a>
                  </li>
                </ul>
              </Bloque>

              <h3 class="rs-sub" id="rs-plano">Plano</h3>
              <div v-if="!hayPlano" class="rs-fila rs-falta" data-sin-plano-resumen>
                <p class="rs-t"><Icono nombre="alerta"/>Sin plano vigente</p>
                <p class="ayuda">Sin el plano no se pueden ubicar los elementos ni confirmar los datos del plano.</p>
                <a class="btn btn-sec" :href="hrefSubirPlanos">Subir planos</a>
              </div>
              <div v-else class="rs-fila" data-plano-resumen>
                <p class="rs-t"><Icono nombre="check"/>Plano vigente · <span class="num">{{ textoPlano }}</span></p>
                <a class="enlace" :href="hrefPlanos">Ver Planos y ficha<Icono nombre="flecha"/></a>
              </div>

              <h3 class="rs-sub" id="rs-rev">Elementos con «plano cambiado: revisar»</h3>
              <Bloque :estado="estadoRevisar" :huesos="2" vacio-titulo="Ningún elemento está marcado para revisar." vacio-texto="Cuando subas un plano nuevo, los elementos ya extraídos del anterior aparecerán aquí."
                error-titulo="No se pudieron leer los elementos." :error-mensaje="mensajeEl" @reintentar="leerElementos">
                <p v-if="!hayPlano" class="ayuda">Esta obra no tiene plano vigente: no hay elementos de diseño que revisar.</p>
                <template v-else>
                  <ul class="filas" aria-labelledby="rs-rev" data-filas-revisar>
                    <li v-for="e in muestraElementos" :key="e.uid" class="fila">
                      <a class="fila-a" :href="hrefElemento(e)">
                        <span class="f-tipo">{{ e.revisar_motivo }}</span>
                        <span class="f-donde num">{{ textoElemento(e) }}</span>
                        <span class="f-motivo">Su recuadro puede ser del plano anterior.</span>
                        <span class="f-sig">Abrir en el visor<Icono nombre="flecha"/></span>
                      </a>
                    </li>
                  </ul>
                  <p v-if="restanElementos" class="ayuda resto">Y {{ restanElementos }} más. Elígelos en el selector del visor.</p>
                </template>
              </Bloque>

              <h3 class="rs-sub" id="rs-inf">Últimos informes generados</h3>
              <Bloque :estado="estadoUltimos" :huesos="2" vacio-titulo="Esta obra todavía no tiene informes generados." vacio-texto="Cuando el sistema procese una visita, sus PDF aparecerán aquí."
                error-titulo="No se pudo leer la lista de informes." :error-mensaje="mensajeInf" @reintentar="leerInformes">
                <ul class="rs-inf" aria-labelledby="rs-inf" data-ultimos-informes>
                  <li v-for="(i, k) in ultimosInformes" :key="(i.trabajo_id || '') + '-' + k" class="rs-inf-f">
                    <div class="rs-inf-d">
                      <span class="rs-inf-n" :title="i.nombre"><template v-if="i.nombre">{{ i.nombre }}</template><Pendiente v-else>nombre pendiente de verificar</Pendiente></span>
                      <span class="ayuda"><template v-if="i.formato">{{ i.formato }} · </template><template v-if="fechaInforme(i)"><span class="num">{{ fechaInforme(i) }}</span></template><Pendiente v-else>fecha pendiente de verificar</Pendiente></span>
                    </div>
                    <p v-if="!i.existe" class="inf-falta"><Icono nombre="alerta"/>El archivo ya no está en la carpeta</p>
                    <a v-else class="btn btn-sec" :href="hrefInforme(i)" target="_blank" rel="noopener" data-abrir-pdf><Icono nombre="externo"/>Abrir PDF<span class="sr"> {{ i.nombre }} (se abre en una pestaña nueva)</span></a>
                  </li>
                </ul>
                <p class="resto"><a class="enlace" :href="hrefInformes">Ver todos los informes<Icono nombre="flecha"/></a></p>
              </Bloque>
            </section>
          </div>

          <div class="col-lateral">
            <section class="caja" aria-labelledby="rs-acc" data-acciones-rapidas>
              <div class="caja-cabeza"><h2 id="rs-acc">Acciones rápidas</h2></div>
              <div v-if="supervision" class="rs-acc">
                <button type="button" class="btn btn-sec" data-abrir-subir @click="abrirSubir"><Icono nombre="subir"/>Subir visita</button>
                <a class="btn btn-sec" :href="hrefHacerInforme" data-hacer-informe-resumen><Icono nombre="mas"/>Hacer informe</a>
              </div>
              <p v-else class="ayuda" data-no-supervision>Esta obra no es de Supervisión: «Subir visita», «Procesar cola» y «Hacer informe» solo existen en las obras de Supervisión.</p>
              <div v-if="hayPlano" class="rs-acc"><a class="btn btn-sec" :href="hrefVisor" data-abrir-el-plano><Icono nombre="plano"/>Abrir el plano</a></div>
              <p v-else class="ayuda"><a class="enlace" :href="hrefSubirPlanos">Subir planos<Icono nombre="flecha"/></a> para abrir el plano de la obra.</p>
              <AccionesCola v-if="supervision" :proyecto="obra.id" :con-sincronizar="false" @actualizar="alProcesar"/>
              <ResultadoVisitas v-if="resultado" :resultado="resultado" @cerrar="resultado = null"/>
            </section>

            <section class="caja" aria-labelledby="rs-act" data-actividad>
              <div class="caja-cabeza"><h2 id="rs-act">Actividad reciente</h2><FaseD fase="D-a"/></div>
              <p><Pendiente/></p>
              <p class="ayuda">El servidor todavía no guarda un registro de actividad por obra. No se muestran movimientos inventados.</p>
            </section>
          </div>
        </div>

        <FormularioVisita v-if="dialogo" :modo="dialogo" :proyecto="obra" @hecho="hechoVisita" @cancelar="cerrarDialogo"/>
      </div>`
  };
})();
