/* Etapa 5 · B1 v3 — maqueta navegable. Mismo código para los 3 estilos; cambia solo el CSS
   (y dos detalles de firma que se leen de body[data-estilo]). Sin red, sin compilación. */
(function () {
  'use strict';
  var D = window.DATOS;
  var ESTILO = document.body.getAttribute('data-estilo');
  var main = document.getElementById('contenido');
  var estado = 'datos';            // datos | vacio | cargando | error  (control de la maqueta)
  var vistos = {};                 // filas «nuevas» ya vistas (firma del estilo Tablero)
  var sel = 'C1';                  // elemento elegido en Revisión de planos
  var origen = 'plano';            // plano | visita
  var etiquetaCruda = false;       // ver etiqueta tal cual o su lectura
  var paneMovil = 'lista';         // lista | plano | datos (Revisión en móvil)
  var paso = 1;                    // Crear informe
  var pedido = { servicios: ['stp'], nombre: '', lugar: '', fuentes: ['Planta nivel 1.pdf (sintético)'], preparado: false };

  /* ---------- utilidades ---------- */
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function obra(id) { for (var i = 0; i < D.obras.length; i++) if (D.obras[i].id === id) return D.obras[i]; return null; }
  function pend() { return '<span class="pendiente">pendiente de verificar</span>'; }
  function faseD(t) { return '<span class="fase-d" title="Necesita backend nuevo; en la maqueta no se simula">' + esc(t) + '</span>'; }
  var I = {
    inicio: '<path d="M4 11.5 12 5l8 6.5V20a1 1 0 0 1-1 1h-4.5v-6h-5v6H5a1 1 0 0 1-1-1z"/>',
    obras: '<path d="M4 21V8l6-3v16M10 21V3l10 4v14M3 21h18M14 10h2M14 14h2M6.5 12h1M6.5 16h1"/>',
    bandeja: '<path d="M3 13l2.5-8h13L21 13v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1zM3 13h5l1.5 3h5L16 13h5"/>',
    informes: '<path d="M7 3h7l5 5v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zM14 3v5h5M9 13h7M9 17h5"/>',
    config: '<path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    mas: '<path d="M12 5v14M5 12h14"/>',
    alerta: '<path d="M12 4 2.8 19.5h18.4zM12 10v4.5M12 17.2v.1"/>',
    flecha: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    volver: '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    plano: '<path d="M3 5h18v14H3zM3 10h18M9 5v14M15 5v14"/>',
    foto: '<path d="M4 7h3l2-2.5h6L17 7h3v12H4z"/><path d="M12 16a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4z"/>',
    check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    reloj: '<path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2"/>'
  };
  function ico(n, cls) { return '<svg class="ico ' + (cls || '') + '" viewBox="0 0 24 24" aria-hidden="true" focusable="false">' + I[n] + '</svg>'; }

  /* ---------- estados de un bloque ---------- */
  // Devuelve el HTML del bloque según el estado de la maqueta. vacio = {titulo, texto, accion:{txt, href}}
  function bloque(contenido, vacio, alto) {
    if (estado === 'cargando') {
      var s = '<div class="cargando" aria-busy="true" aria-live="polite"><span class="sr">Cargando…</span>';
      for (var i = 0; i < (alto || 3); i++) s += '<span class="hueso" style="--i:' + i + '"></span>';
      return s + '</div>';
    }
    if (estado === 'error') {
      return '<div class="error" role="alert">' + ico('alerta') + '<div><p class="error-t">No se pudo leer esta lista.</p>' +
        '<p>El backend no responde en esta PC. Comprueba que el servidor esté abierto y vuelve a intentarlo.</p>' +
        '<button type="button" class="btn btn-sec" data-accion="reintentar">Reintentar</button></div></div>';
    }
    if (estado === 'vacio') {
      return '<div class="vacio"><p class="vacio-t">' + esc(vacio.titulo) + '</p><p>' + esc(vacio.texto) + '</p>' +
        (vacio.accion ? '<a class="btn btn-sec" href="' + vacio.accion.href + '">' + esc(vacio.accion.txt) + '</a>' : '') + '</div>';
    }
    return contenido;
  }

  /* ---------- cabecera de obra (cajetín / placa / pase según estilo) ---------- */
  var PESTANAS = [['resumen', 'Resumen'], ['visitas', 'Visitas y trabajos'], ['planos', 'Planos y ficha'], ['avance', 'Avance'], ['informes', 'Informes'], ['cierre', 'Cierre']];
  function cabezaObra(o, activa) {
    var h = '<header class="obra-cabeza"><div class="obra-titulo"><a class="miga" href="#/obras">' + ico('volver') + 'Mis obras</a>' +
      '<h1>' + esc(o.nombre) + ' <span class="sint">(sintético)</span></h1></div>' +
      '<dl class="cajetin">' +
      '<div><dt>Servicio</dt><dd>' + esc(o.tipo) + '</dd></div>' +
      '<div><dt>Niveles</dt><dd>' + esc(o.niveles) + '</dd></div>' +
      '<div><dt>Planos</dt><dd>' + (o.planos === 'pendiente de verificar' ? pend() : esc(o.planos)) + '</dd></div>' +
      '<div><dt>Última visita</dt><dd class="num">' + esc(o.ultima) + '</dd></div>' +
      '<div><dt>Visitas</dt><dd class="num">' + o.visitas + '</dd></div></dl>' +
      '<nav class="pestanas" aria-label="Secciones de la obra">';
    PESTANAS.forEach(function (p) {
      h += '<a href="#/obra/' + o.id + '/' + p[0] + '"' + (p[0] === activa ? ' aria-current="page"' : '') + '>' + p[1] + '</a>';
    });
    return h + '</nav></header>';
  }

  /* ---------- pantallas ---------- */
  function filaPend(p, conObra) {
    var o = p.obra ? obra(p.obra) : null;
    var lugar = o ? esc(o.nombre) : esc(p.trabajo);
    var nuevo = p.nuevo && !vistos[p.id];
    var bloq = p.tipo === 'Duda bloqueante';
    return '<li class="fila' + (nuevo ? ' es-nuevo' : '') + (bloq ? ' es-bloq' : '') + '" data-id="' + p.id + '">' +
      '<a class="fila-a" href="#/abrir/' + p.id + '" data-visto="' + p.id + '">' +
      '<span class="f-tipo">' + (bloq ? ico('alerta', 'ico-bloq') : '') + esc(p.tipo) + (nuevo ? ' <span class="marca-nuevo">Nuevo</span>' : '') + '</span>' +
      (conObra ? '<span class="f-obra">' + lugar + (p.origen === 'trabajo' ? ' <span class="etq">Trabajo independiente</span>' : '') + '</span>' : '') +
      '<span class="f-donde">' + esc(p.donde) + '</span>' +
      '<span class="f-motivo">' + esc(p.motivo) + '</span>' +
      '<span class="f-sig">' + esc(p.siguiente) + ico('flecha') + '</span>' +
      '<span class="f-dias num">' + (p.dias === 0 ? 'hoy' : p.dias + ' d') + '</span></a></li>';
  }

  function inicio() {
    var cubos = [['vencido', 'Vencido'], ['semana', 'Próximos 7 días'], ['mas', 'Más adelante'], ['sinfecha', 'Sin fecha']];
    var cuenta = { dudas: 0, rev: 0, ent: 0, cola: 0 };
    D.pendientes.forEach(function (p) {
      if (p.tipo === 'Duda bloqueante') cuenta.dudas++;
      if (p.tipo === 'Revisión de plano') cuenta.rev++;
      if (p.tipo === 'Entrega') cuenta.ent++;
      if (p.tipo === 'Visita en cola') cuenta.cola++;
    });
    var prior = '';
    cubos.forEach(function (c) {
      var fs = D.pendientes.filter(function (p) { return p.cubo === c[0]; });
      if (!fs.length) return;
      prior += '<section class="cubo cubo-' + c[0] + '"><h3>' + c[1] + ' <span class="num">' + fs.length + '</span></h3><ul class="filas">' +
        fs.map(function (p) { return filaPend(p, true); }).join('') + '</ul></section>';
    });
    var h = '<div class="pagina pagina-inicio">' +
      '<header class="pagina-cabeza"><h1>Inicio</h1><p class="fecha">jueves ' + D.hoy + '</p></header>' +
      '<ul class="conteos" aria-label="Pendientes por tipo">' +
      '<li><a href="#/bandeja?tipo=Duda bloqueante"><span class="num">' + cuenta.dudas + '</span> dudas bloqueantes</a></li>' +
      '<li><a href="#/bandeja?tipo=Revisión de plano"><span class="num">' + cuenta.rev + '</span> revisiones de plano</a></li>' +
      '<li><a href="#/bandeja?tipo=Entrega"><span class="num">' + cuenta.ent + '</span> entregas por revisar</a></li>' +
      '<li><a href="#/bandeja?tipo=Visita en cola"><span class="num">' + cuenta.cola + '</span> visitas en cola</a></li></ul>' +
      '<div class="rejilla-inicio">' +
      '<section class="caja prioridades" aria-labelledby="t-prior"><div class="caja-cabeza"><h2 id="t-prior">Prioridades</h2>' + faseD('Vencimientos: Fase D-a') + '</div>' +
      bloque(prior, { titulo: 'No hay pendientes.', texto: 'Cuando entre una visita o aparezca una duda, sale aquí con su siguiente paso.', accion: { txt: 'Ver Mis obras', href: '#/obras' } }, 5) +
      '</section>' +
      '<div class="col-lateral">' +
      '<section class="caja" aria-labelledby="t-acc"><h2 id="t-acc">Próximas acciones</h2>' +
      bloque('<ol class="acciones">' +
        '<li><a href="#/obra/norte/planos">Revisar 6 valores de la hoja E-3 <span class="sub">Residencial Ejemplo Norte</span></a></li>' +
        '<li><a href="#/abrir/p1">Responder 3 dudas bloqueantes <span class="sub">Residencial Ejemplo Norte</span></a></li>' +
        '<li><a href="#/abrir/p3">Procesar la visita #14 <span class="sub">Residencial Ejemplo Norte</span></a></li>' +
        '<li><a href="#/abrir/p4">Resolver la viga V-7 <span class="sub">Torre Ejemplo 12</span></a></li></ol>',
        { titulo: 'Nada que hacer ahora.', texto: 'Las acciones salen de los pendientes abiertos.' }, 4) +
      '</section>' +
      '<section class="caja" aria-labelledby="t-obras"><h2 id="t-obras">Mis obras</h2>' +
      bloque('<ul class="obras-mini">' + D.obras.map(function (o) {
        return '<li><a href="#/obra/' + o.id + '/resumen"><span class="om-n">' + esc(o.nombre) + '</span><span class="om-d">' +
          (o.dudasBloq ? '<span class="num">' + o.dudasBloq + '</span> bloqueantes · ' : 'Sin bloqueantes · ') + 'última visita <span class="num">' + o.ultima + '</span></span></a></li>';
      }).join('') + '</ul>', { titulo: 'Aún no hay obras.', texto: 'Registra la primera obra para empezar.', accion: { txt: 'Registrar obra', href: '#/obras' } }, 3) +
      '</section></div></div></div>';
    return h;
  }

  function obras() {
    return '<div class="pagina"><header class="pagina-cabeza"><h1>Mis obras</h1></header><section class="caja">' +
      bloque('<ul class="obras-lista">' + D.obras.map(function (o) {
        return '<li><a href="#/obra/' + o.id + '/resumen"><span class="ol-n">' + esc(o.nombre) + ' <span class="sint">(sintético)</span></span>' +
          '<span class="ol-m">' + esc(o.tipo) + ' · ' + esc(o.niveles) + '</span>' +
          '<span class="ol-c"><span class="num">' + o.dudasBloq + '</span> bloqueantes · <span class="num">' + o.enCola + '</span> en cola · <span class="num">' + o.revisiones + '</span> revisiones</span></a></li>';
      }).join('') + '</ul>', { titulo: 'Aún no hay obras.', texto: 'Registra la primera obra para empezar.' }, 3) +
      '</section><p class="nota-b3">Pantalla de apoyo para navegar la maqueta; su diseño completo es de B3a.</p></div>';
  }

  var INDICADORES = [
    { n: 'Avance por entrepisos', f: 'Entrepisos ejecutados y confirmados ÷ total previsto en planos', falta: 'Falta definir qué evidencia cuenta un entrepiso como ejecutado.' },
    { n: 'Expediente completo', f: 'Unidades documentales completadas ÷ alcance documental final confirmado', falta: 'Falta definir las unidades documentales y el cierre documental.' },
    { n: 'Documentación al día', f: 'Unidades completadas y exigibles ÷ total exigible hasta el avance actual', falta: 'Falta definir qué es exigible en cada avance.' }
  ];

  function resumen(o) {
    var mias = D.pendientes.filter(function (p) { return p.obra === o.id; });
    var ind = INDICADORES.map(function (x) {
      return '<li class="indicador"><h3>' + x.n + '</h3><p class="ind-valor">' + pend() + '</p>' +
        '<div class="ind-barra" role="img" aria-label="Sin valor: pendiente de verificar"></div>' +
        '<p class="ind-f">' + esc(x.f) + '</p><p class="ind-falta">' + esc(x.falta) + ' Decisión D15 de Steven.</p></li>';
    }).join('');
    return '<div class="pagina pagina-obra">' + cabezaObra(o, 'resumen') +
      '<section class="caja" aria-labelledby="t-ind"><div class="caja-cabeza"><h2 id="t-ind">Indicadores</h2>' + faseD('Cálculo: Fase D-b, tras D15') + '</div>' +
      '<ul class="indicadores">' + ind + '</ul>' +
      '<p class="ind-regla">Sin datos no es 0 %. No se cuentan archivos, versiones ni visitas como sustituto.</p></section>' +
      '<div class="rejilla-obra">' +
      '<section class="caja" aria-labelledby="t-pend"><div class="caja-cabeza"><h2 id="t-pend">Pendientes de la obra</h2>' +
      '<a class="enlace" href="#/bandeja?obra=' + o.id + '&desde=' + o.id + '">Ver en la bandeja' + ico('flecha') + '</a></div>' +
      '<ul class="conteos conteos-obra"><li><a href="#/bandeja?obra=' + o.id + '&tipo=Duda bloqueante&desde=' + o.id + '"><span class="num">' + o.dudasBloq + '</span> dudas bloqueantes</a></li>' +
      '<li><a href="#/bandeja?obra=' + o.id + '&tipo=Visita en cola&desde=' + o.id + '"><span class="num">' + o.enCola + '</span> visitas en cola</a></li>' +
      '<li><a href="#/obra/' + o.id + '/planos"><span class="num">' + o.revisiones + '</span> revisiones de plano</a></li></ul>' +
      bloque('<ul class="filas">' + mias.map(function (p) { return filaPend(p, false); }).join('') + '</ul>',
        { titulo: 'Esta obra no tiene pendientes.', texto: 'Cuando entre una visita nueva aparecerá aquí.', accion: { txt: 'Subir visita', href: '#/obra/' + o.id + '/visitas' } }, 4) +
      '</section><div class="col-lateral">' +
      '<section class="caja" aria-labelledby="t-rap"><h2 id="t-rap">Acciones rápidas</h2><div class="rapidas">' +
      '<a class="btn btn-sec" href="#/obra/' + o.id + '/visitas">Subir visita</a>' +
      '<a class="btn btn-sec" href="#/obra/' + o.id + '/planos">Revisar planos</a>' +
      '<a class="btn btn-sec" href="#/abrir/p1">Mesa de Dudas</a>' +
      '<a class="btn btn-pri" href="#/crear-informe?obra=' + o.id + '">Crear informe de esta obra</a></div></section>' +
      '<section class="caja" aria-labelledby="t-act"><div class="caja-cabeza"><h2 id="t-act">Actividad reciente</h2>' + faseD('Fase D-a') + '</div>' +
      bloque('<ul class="actividad">' + D.actividad.filter(function (a) { return a.obra === o.id; }).map(function (a) {
        return '<li><span class="num">' + a.cuando + '</span> ' + esc(a.que) + '</li>';
      }).join('') + '</ul>', { titulo: 'Sin actividad todavía.', texto: '' }, 3) +
      '</section></div></div></div>';
  }

  function bandeja(q) {
    var lista = D.pendientes.slice().sort(function (a, b) {
      var ba = a.tipo === 'Duda bloqueante' ? 0 : 1, bb = b.tipo === 'Duda bloqueante' ? 0 : 1;
      return ba - bb || b.dias - a.dias;
    }).filter(function (p) {
      return (!q.obra || p.obra === q.obra) && (!q.tipo || p.tipo === q.tipo) && (!q.origen || p.origen === q.origen);
    });
    var tipos = ['Duda bloqueante', 'Revisión de plano', 'Visita en cola', 'Entrega', 'Orden de trabajo', 'Fuente faltante'];
    var desde = q.desde ? obra(q.desde) : null;
    var filtros = (q.obra ? 1 : 0) + (q.tipo ? 1 : 0) + (q.origen ? 1 : 0);
    var guia = lista.length ? 'Mostrando <span class="num">' + lista.length + '</span> de <span class="num">' + D.pendientes.length + '</span> · de «' + esc(lista[0].tipo) + '» a «' + esc(lista[lista.length - 1].tipo) + '»' : '';
    var cuerpo;
    if (estado === 'datos' && !lista.length) {
      cuerpo = '<div class="vacio"><p class="vacio-t">Ningún pendiente coincide con estos filtros.</p><p>Hay ' + D.pendientes.length + ' pendientes en total.</p><a class="btn btn-sec" href="#/bandeja' + (desde ? '?desde=' + desde.id : '') + '">Quitar filtros</a></div>';
    } else {
      cuerpo = bloque('<p class="guia">' + guia + '</p><div class="tabla-cab" aria-hidden="true"><span>Tipo</span><span>Obra o trabajo</span><span>Dónde</span><span>Motivo</span><span>Siguiente paso</span><span>Antigüedad</span></div>' +
        '<ul class="filas filas-bandeja">' + lista.map(function (p) { return filaPend(p, true); }).join('') + '</ul>',
        { titulo: 'Bandeja al día.', texto: 'No hay pendientes en ninguna obra ni trabajo independiente.' }, 6);
    }
    function sel_(nombre, etiqueta, opciones, val) {
      return '<label class="campo-filtro"><span>' + etiqueta + '</span><select data-filtro="' + nombre + '"><option value="">Todos</option>' +
        opciones.map(function (op) { return '<option value="' + esc(op[0]) + '"' + (op[0] === val ? ' selected' : '') + '>' + esc(op[1]) + '</option>'; }).join('') + '</select></label>';
    }
    return '<div class="pagina pagina-bandeja">' +
      (desde ? '<a class="miga volver-obra" href="#/obra/' + desde.id + '/resumen">' + ico('volver') + 'Volver a ' + esc(desde.nombre) + ' · Resumen</a>' : '') +
      '<header class="pagina-cabeza"><h1>Bandeja de trabajo</h1>' + faseD('Ruta común: Fase D-a · trabajos independientes: D-c') + '</header>' +
      '<p class="bajada">Los pendientes de todas las obras y trabajos independientes. Cada fila abre el registro original; resolverlo aquí es resolverlo allí.</p>' +
      '<div class="filtros" role="group" aria-label="Filtros">' +
      sel_('obra', 'Obra', D.obras.map(function (o) { return [o.id, o.nombre]; }), q.obra) +
      sel_('tipo', 'Tipo', tipos.map(function (t) { return [t, t]; }), q.tipo) +
      sel_('origen', 'Origen', [['obra', 'Obras'], ['trabajo', 'Trabajos independientes']], q.origen) +
      (filtros ? '<a class="enlace quitar" href="#/bandeja' + (desde ? '?desde=' + desde.id : '') + '">Quitar ' + filtros + (filtros > 1 ? ' filtros' : ' filtro') + '</a>' : '') +
      '</div><section class="caja caja-bandeja" aria-label="Pendientes">' + cuerpo + '</section></div>';
  }

  function plano_svg() {
    var s = '<svg class="plano-svg" viewBox="0 0 460 300" role="group" aria-label="Plano sintético del nivel E-3 con los elementos propuestos">';
    s += '<rect class="pl-papel" x="0" y="0" width="460" height="300"/>';
    [['A', 70], ['B', 230], ['C', 390]].forEach(function (e) {
      s += '<line class="pl-eje" x1="' + e[1] + '" y1="30" x2="' + e[1] + '" y2="262"/><circle class="pl-globo" cx="' + e[1] + '" cy="18" r="11"/><text class="pl-gt" x="' + e[1] + '" y="22">' + e[0] + '</text>';
    });
    [['1', 70], ['2', 210]].forEach(function (e) {
      s += '<line class="pl-eje" x1="30" y1="' + e[1] + '" x2="430" y2="' + e[1] + '"/><circle class="pl-globo" cx="16" cy="' + e[1] + '" r="11"/><text class="pl-gt" x="16" y="' + (e[1] + 4) + '">' + e[0] + '</text>';
    });
    s += '<rect class="pl-losa" x="70" y="70" width="320" height="140"/>';
    D.elementos.forEach(function (el) {
      var on = el.id === sel;
      s += '<g class="pl-el' + (on ? ' on' : '') + ' est-' + el.estado + '" data-el="' + el.id + '" tabindex="0" role="button" aria-pressed="' + on + '" aria-label="' + el.tipo + ' ' + el.id + ', ' + el.estado + '">' +
        '<rect class="pl-col" x="' + (el.x - 9) + '" y="' + (el.y - 9) + '" width="18" height="18"/>' +
        '<text class="pl-id" x="' + (el.x + 14) + '" y="' + (el.y - 12) + '">' + el.id + '</text>' +
        (on ? '<rect class="pl-recuadro" x="' + (el.x - 22) + '" y="' + (el.y - 22) + '" width="44" height="44"/>' : '') + '</g>';
    });
    s += '<text class="pl-rotulo" x="440" y="290" text-anchor="end">PLANO SINTÉTICO · NO ES REAL</text></svg>';
    return s;
  }

  var ESTADO_TXT = { propuesto: 'Propuesto', confirmado: 'Confirmado', conflicto: 'En conflicto', pendiente: 'pendiente de verificar', calculado: 'Calculado' };
  function revision(o) {
    var el = D.elementos.filter(function (e) { return e.id === sel; })[0];
    var vals = D.valores[sel] || D.valores.C1;
    var hayDuda = vals.some(function (v) { return v.estado === 'conflicto' || v.estado === 'pendiente'; });
    var lista = '<ul class="elementos" aria-label="Elementos propuestos">' + D.elementos.map(function (e) {
      return '<li><button type="button" class="el-b est-' + e.estado + '" data-el="' + e.id + '" aria-pressed="' + (e.id === sel) + '">' +
        '<span class="el-id">' + e.id + '</span><span class="el-t">' + e.tipo + '</span>' +
        '<span class="el-ejes">' + (e.ejes === 'pendiente de verificar' ? pend() : '<span class="eje">' + esc(e.ejes.replace('EJE ', '')) + '</span>') + '</span>' +
        '<span class="el-e">' + (e.estado === 'pendiente' ? 'Sin fuente' : ESTADO_TXT[e.estado]) + '</span></button></li>';
    }).join('') + '</ul>';
    var datos;
    if (origen === 'plano') {
      datos = '<table class="valores"><caption class="sr">Datos propuestos de ' + sel + '</caption><thead><tr><th scope="col">Dato</th><th scope="col">Valor propuesto y estado</th></tr></thead><tbody>' +
        vals.map(function (v) {
          return '<tr class="v-' + v.estado + '"><th scope="row">' + esc(v.campo) + '</th><td>' + (v.valor == null ? pend() : '<span class="num v-val">' + esc(v.valor) + '</span><span class="v-est">' + ESTADO_TXT[v.estado] + '</span>') + '</td></tr>' +
            '<tr class="v-fuente"><td colspan="2">' + (v.fuente ? '<span class="fuente-l">Fuente</span> ' + esc(v.fuente) : '<span class="fuente-l">Fuente</span> sin fuente: no se confirma') + (v.nota ? '<span class="v-nota">' + esc(v.nota) + '</span>' : '') + '</td></tr>';
        }).join('') + '</tbody></table>' +
        '<div class="acciones-datos"><button type="button" class="btn btn-pri" data-accion="confirmar"' + (hayDuda ? ' disabled aria-describedby="porque"' : '') + '>Confirmar valores con fuente</button>' +
        '<a class="btn btn-sec" href="#/abrir/p1">Enviar a la Mesa de Dudas</a>' +
        (hayDuda ? '<p id="porque" class="ayuda">No se puede confirmar: hay valores en conflicto o sin fuente. Van a la Mesa de Dudas.</p>' : '') + '</div>';
    } else {
      var v = D.visitaFoto;
      datos = '<figure class="foto-orig"><div class="foto-sint" role="img" aria-label="Foto de visita sintética">' + ico('foto') + '<span>Foto sintética · ' + esc(v.foto) + '</span></div>' +
        '<figcaption>Visita ' + v.visita + ' · <span class="num">' + v.fecha + '</span></figcaption></figure>' +
        '<div class="etiqueta"><div class="seg" role="group" aria-label="Cómo ver la etiqueta">' +
        '<button type="button" data-accion="cruda" aria-pressed="' + etiquetaCruda + '">Tal cual</button><button type="button" data-accion="leida" aria-pressed="' + !etiquetaCruda + '">Lectura</button></div>' +
        (etiquetaCruda ? '<p class="et-cruda">«' + esc(v.etiqueta) + '»</p><p class="ayuda">Etiqueta literal del log de la visita.</p>'
          : '<p class="et-leida">' + esc(v.lectura) + '</p><p class="ayuda">' + esc(v.regla) + '</p>') + '</div>';
    }
    return '<div class="pagina pagina-revision">' + cabezaObra(o, 'planos') +
      '<div class="rev-cabeza"><h2>Revisión de planos · Nivel E-3</h2>' +
      '<label class="campo-filtro"><span>Hoja</span><select><option>E-3 · Rev. 3 (vigente)</option><option>E-3 · Rev. 2 (no vigente)</option></select></label>' +
      '<div class="seg" role="group" aria-label="Origen de los datos"><button type="button" data-accion="o-plano" aria-pressed="' + (origen === 'plano') + '">' + ico('plano') + 'Del plano</button>' +
      '<button type="button" data-accion="o-visita" aria-pressed="' + (origen === 'visita') + '">' + ico('foto') + 'De la visita</button></div></div>' +
      '<div class="seg seg-movil" role="group" aria-label="Zona visible">' +
      [['lista', 'Elementos'], ['plano', 'Plano'], ['datos', 'Datos']].map(function (z) {
        return '<button type="button" data-pane="' + z[0] + '" aria-pressed="' + (paneMovil === z[0]) + '">' + z[1] + '</button>';
      }).join('') + '</div>' +
      '<div class="rev" data-pane-activo="' + paneMovil + '">' +
      '<section class="rev-lista caja" aria-labelledby="t-el"><h3 id="t-el">Elementos propuestos <span class="num">' + D.elementos.length + '</span></h3>' +
      bloque(lista, { titulo: 'No hay elementos propuestos.', texto: 'Extrae los datos del plano vigente para empezar.', accion: { txt: 'Extraer del plano vigente', href: '#/obra/' + o.id + '/planos' } }, 6) + '</section>' +
      '<section class="rev-plano caja" aria-label="Plano">' + bloque(plano_svg(), { titulo: 'No hay hoja para mostrar.', texto: 'Marca un plano como vigente en Planos y ficha.' }, 1) + '</section>' +
      '<section class="rev-datos caja" aria-labelledby="t-dat"><h3 id="t-dat">' + esc(el.tipo) + ' ' + el.id + ' · ' + (el.ejes === 'pendiente de verificar' ? pend() : esc(el.ejes)) + '</h3>' +
      bloque(datos, { titulo: 'Sin datos propuestos.', texto: 'Este elemento aún no tiene valores leídos.' }, 4) + '</section></div></div>';
  }

  function crear(q) {
    var o = q.obra ? obra(q.obra) : null;
    var pasos = ['Servicios', 'Datos y fuentes', 'Revisar pedido', 'Preparar'];
    var h = '<div class="pagina pagina-crear"><header class="pagina-cabeza"><h1>Crear informe</h1>' + faseD('Guardar trabajos independientes: Fase D-c') + '</header>' +
      '<p class="bajada">' + (o ? 'Informe para ' + esc(o.nombre) + '.' : 'Trabajo independiente: no crea una obra de seguimiento. Se puede vincular a una obra más adelante.') + '</p>' +
      '<ol class="pasos">' + pasos.map(function (p, i) {
        var n = i + 1;
        return '<li' + (n === paso ? ' aria-current="step"' : '') + (n < paso ? ' class="hecho"' : '') + '><span class="p-n num">' + (n < paso ? ico('check') : n) + '</span>' + p + '</li>';
      }).join('') + '</ol><section class="caja caja-paso">';
    if (paso === 1) {
      h += '<fieldset><legend>¿Qué servicios lleva el trabajo?</legend><ul class="servicios">' + D.servicios.map(function (s) {
        var on = pedido.servicios.indexOf(s.id) >= 0;
        return '<li><label class="servicio' + (on ? ' on' : '') + '"><input type="checkbox" data-serv="' + s.id + '"' + (on ? ' checked' : '') + '>' +
          '<span class="s-n">' + esc(s.nombre) + '</span><span class="s-d">' + esc(s.desc) + '</span>' +
          '<span class="s-h ' + (s.hoy ? 'hoy' : 'futuro') + '">' + (s.hoy ? esc(s.hoy) : 'Desarrollo futuro') + '</span></label></li>';
      }).join('') + '</ul></fieldset>' +
        '<p class="ayuda">Elegir un servicio no lo declara implementado: los formatos HV siguen fuera de la Etapa 5.</p>';
    } else if (paso === 2) {
      h += '<div class="form">' +
        '<label class="campo"><span>Nombre del trabajo</span><input type="text" data-campo="nombre" value="' + esc(pedido.nombre) + '" placeholder="Ej.: Esclerometría local comercial" aria-describedby="a-nombre"><span id="a-nombre" class="ayuda">Si lo dejas vacío queda «pendiente de verificar».</span></label>' +
        '<label class="campo"><span>Cliente y lugar</span><input type="text" data-campo="lugar" value="' + esc(pedido.lugar) + '" aria-describedby="a-lugar"><span id="a-lugar" class="ayuda">Tal como lo escribe el cliente; no se completa solo.</span></label>' +
        '<fieldset class="fuentes"><legend>Fuentes</legend><ul>' + pedido.fuentes.map(function (f) { return '<li>' + ico('informes') + esc(f) + '</li>'; }).join('') + '</ul>' +
        '<button type="button" class="btn btn-sec" data-accion="fuente">' + ico('mas') + 'Añadir fuente</button><p class="ayuda">Planos, fotos, reportes de equipo. En la maqueta solo se añade un nombre de ejemplo.</p></fieldset></div>';
    } else if (paso === 3) {
      h += '<div class="expediente"><h2>' + (pedido.nombre ? esc(pedido.nombre) : pend()) + '</h2><dl class="cajetin">' +
        '<div><dt>Servicios</dt><dd>' + pedido.servicios.map(function (id) { return esc(D.servicios.filter(function (s) { return s.id === id; })[0].nombre); }).join(', ') + '</dd></div>' +
        '<div><dt>Cliente y lugar</dt><dd>' + (pedido.lugar ? esc(pedido.lugar) : pend()) + '</dd></div>' +
        '<div><dt>Estado</dt><dd>Borrador</dd></div><div><dt>Obra</dt><dd>' + (o ? esc(o.nombre) : 'Sin vincular') + '</dd></div></dl>' +
        '<div class="exp-partes"><section><h3>Fuentes <span class="num">' + pedido.fuentes.length + '</span></h3><ul>' + pedido.fuentes.map(function (f) { return '<li>' + esc(f) + '</li>'; }).join('') + '</ul></section>' +
        '<section><h3>Dudas <span class="num">0</span></h3><p class="ayuda">Las dudas del trabajo irán a la Mesa de Dudas, como las de una obra.</p></section>' +
        '<section><h3>Documentos y versiones</h3><p class="ayuda">Aún no hay documentos. Cada informe guardará v1, v2… sin sobrescribir.</p></section>' +
        '<section><h3>Historial</h3><p class="ayuda">Se registra en la auditoría desde que se prepara.</p></section></div></div>';
    } else {
      h += pedido.preparado
        ? '<div class="resultado" role="status"><p class="vacio-t">Así quedaría el trabajo preparado.</p><p>Maqueta: no se guardó nada. Guardar y listar trabajos independientes es la Fase D-c.</p>' +
          '<div class="rapidas"><a class="btn btn-sec" href="#/bandeja?origen=trabajo">Ver en la bandeja</a><button type="button" class="btn btn-sec" disabled>Vincular a una obra</button></div></div>'
        : '<p>Se preparará el trabajo con ' + pedido.servicios.length + ' servicio(s) y ' + pedido.fuentes.length + ' fuente(s). No se crea ninguna obra.</p>' +
          '<button type="button" class="btn btn-pri" data-accion="preparar">Preparar trabajo</button>';
    }
    h += '</section><div class="nav-pasos">' + (paso > 1 ? '<button type="button" class="btn btn-sec" data-accion="atras">' + ico('volver') + 'Atrás</button>' : '<span></span>') +
      (paso < 4 ? '<button type="button" class="btn btn-pri" data-accion="sigue"' + (paso === 1 && !pedido.servicios.length ? ' disabled' : '') + '>Siguiente' + ico('flecha') + '</button>' : '') + '</div></div>';
    return h;
  }

  function apoyo(titulo, texto) {
    return '<div class="pagina"><header class="pagina-cabeza"><h1>' + titulo + '</h1></header><section class="caja"><div class="vacio"><p class="vacio-t">Fuera de las 5 pantallas de B1.</p><p>' + texto + '</p><a class="btn btn-sec" href="#/inicio">Volver a Inicio</a></div></section></div>';
  }

  /* ---------- enrutador ---------- */
  function ruta() {
    var h = location.hash.replace(/^#/, '') || '/inicio';
    var partes = h.split('?'), camino = partes[0].split('/').filter(Boolean), q = {};
    (partes[1] || '').split('&').forEach(function (kv) { if (!kv) return; var p = kv.split('='); q[decodeURIComponent(p[0])] = decodeURIComponent(p[1] || ''); });
    var html, nav = camino[0];
    if (camino[0] === 'abrir') {
      vistos[camino[1]] = true;
      var p = D.pendientes.filter(function (x) { return x.id === camino[1]; })[0];
      html = apoyo(esc(p ? p.abre : 'Registro'), 'Aquí se abre el registro original (' + esc(p ? p.abre : '') + '). La pantalla especializada se conserva y su diseño es de B3. En la maqueta, la fila ya quedó marcada como vista.');
      nav = 'bandeja';
    } else if (camino[0] === 'obra') {
      var o = obra(camino[1]) || D.obras[0];
      nav = 'obras';
      if (camino[2] === 'planos') html = revision(o);
      else if (!camino[2] || camino[2] === 'resumen') html = resumen(o);
      else html = '<div class="pagina pagina-obra">' + cabezaObra(o, camino[2]) + '<section class="caja"><div class="vacio"><p class="vacio-t">Pestaña de B3.</p><p>Esta pestaña existe en la organización aprobada; su contenido se diseña en B3 (paridad con el tablero actual).</p></div></section></div>';
    } else if (camino[0] === 'bandeja') html = bandeja(q);
    else if (camino[0] === 'obras') html = obras();
    else if (camino[0] === 'crear-informe') { html = crear(q); nav = 'crear'; }
    else if (camino[0] === 'informes') html = apoyo('Informes', 'Lista de informes generados de todas las obras y trabajos. Se diseña en B3g.');
    else if (camino[0] === 'configuracion') html = apoyo('Configuración', 'Tema, rutas de Dropbox y datos de CATDIC. Se diseña en B3.');
    else { html = inicio(); nav = 'inicio'; }
    // Firma del estilo Tablero: al filtrar la bandeja, las filas que siguen se deslizan a su nuevo sitio (FLIP).
    var antes = {};
    var flip = ESTILO === 'tablero' && camino[0] === 'bandeja' && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (flip) main.querySelectorAll('.fila[data-id]').forEach(function (f) { antes[f.getAttribute('data-id')] = f.getBoundingClientRect().top; });
    main.innerHTML = html;
    if (flip) main.querySelectorAll('.fila[data-id]').forEach(function (f) {
      var y0 = antes[f.getAttribute('data-id')];
      if (y0 == null) { f.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 160, easing: 'ease-out' }); return; }
      var dy = y0 - f.getBoundingClientRect().top;
      if (Math.abs(dy) > 1) f.animate([{ transform: 'translateY(' + dy + 'px)' }, { transform: 'none' }], { duration: 240, easing: 'cubic-bezier(0.23, 1, 0.32, 1)' });
    });
    document.querySelectorAll('[data-nav]').forEach(function (a) {
      if (a.getAttribute('data-nav') === nav) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
    var t = main.querySelector('h1');
    document.title = (t ? t.textContent : 'CATDIC') + ' · Maqueta B1 · ' + document.body.getAttribute('data-nombre-estilo');
  }

  function irA(h) { if (location.hash === h) ruta(); else location.hash = h; }

  /* ---------- eventos ---------- */
  window.addEventListener('hashchange', function () { ruta(); main.focus({ preventScroll: true }); window.scrollTo(0, 0); });
  document.addEventListener('change', function (e) {
    var t = e.target;
    if (t.matches('[data-filtro]')) {
      var h = location.hash.split('?'), q = {};
      (h[1] || '').split('&').forEach(function (kv) { if (kv) { var p = kv.split('='); q[p[0]] = decodeURIComponent(p[1] || ''); } });
      if (t.value) q[t.getAttribute('data-filtro')] = t.value; else delete q[t.getAttribute('data-filtro')];
      var qs = Object.keys(q).map(function (k) { return k + '=' + encodeURIComponent(q[k]); }).join('&');
      irA('#/bandeja' + (qs ? '?' + qs : ''));
    } else if (t.matches('[data-serv]')) {
      var id = t.getAttribute('data-serv'), i = pedido.servicios.indexOf(id);
      if (t.checked && i < 0) pedido.servicios.push(id); if (!t.checked && i >= 0) pedido.servicios.splice(i, 1);
      ruta(); var v = main.querySelector('[data-serv="' + id + '"]'); if (v) v.focus();
    } else if (t.matches('#estado-demo')) { estado = t.value; ruta(); }
  });
  document.addEventListener('input', function (e) { if (e.target.matches('[data-campo]')) pedido[e.target.getAttribute('data-campo')] = e.target.value; });
  function elegir(id) { sel = id; if (window.matchMedia('(max-width: 899px)').matches) paneMovil = 'datos'; ruta(); var b = main.querySelector('.el-b[data-el="' + id + '"]'); if (b && paneMovil !== 'datos') b.focus(); }
  document.addEventListener('click', function (e) {
    var a = e.target.closest('[data-accion],[data-el],[data-pane],[data-visto],#tema');
    if (!a) return;
    if (a.id === 'tema') {
      var oscuro = document.documentElement.getAttribute('data-tema') !== 'oscuro';
      document.documentElement.setAttribute('data-tema', oscuro ? 'oscuro' : 'claro');
      a.setAttribute('aria-pressed', oscuro); a.textContent = oscuro ? 'Tema: oscuro' : 'Tema: claro';
      try { localStorage.setItem('catdic-b1-tema', oscuro ? 'oscuro' : 'claro'); } catch (_) { }
      return;
    }
    if (a.hasAttribute('data-visto')) { vistos[a.getAttribute('data-visto')] = true; return; }
    if (a.hasAttribute('data-el')) { elegir(a.getAttribute('data-el')); return; }
    if (a.hasAttribute('data-pane')) { paneMovil = a.getAttribute('data-pane'); ruta(); return; }
    var acc = a.getAttribute('data-accion');
    if (acc === 'reintentar') { estado = 'datos'; document.getElementById('estado-demo').value = 'datos'; ruta(); }
    else if (acc === 'o-plano' || acc === 'o-visita') { origen = acc.slice(2); ruta(); }
    else if (acc === 'cruda' || acc === 'leida') { etiquetaCruda = acc === 'cruda'; ruta(); }
    else if (acc === 'sigue') { paso = Math.min(4, paso + 1); ruta(); }
    else if (acc === 'atras') { paso = Math.max(1, paso - 1); pedido.preparado = false; ruta(); }
    else if (acc === 'fuente') { pedido.fuentes.push('Fuente de ejemplo ' + (pedido.fuentes.length + 1) + ' (sintética).pdf'); ruta(); }
    else if (acc === 'preparar') { pedido.preparado = true; ruta(); }
    else if (acc === 'confirmar') { /* maqueta: no confirma nada */ }
  });
  document.addEventListener('keydown', function (e) {
    var g = e.target.closest && e.target.closest('g[data-el]');
    if (g && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); elegir(g.getAttribute('data-el')); }
  });

  var tm = null;
  try { tm = localStorage.getItem('catdic-b1-tema'); } catch (_) { }
  if (!tm && window.matchMedia('(prefers-color-scheme: dark)').matches) tm = 'oscuro';
  if (tm) document.documentElement.setAttribute('data-tema', tm);
  var bt = document.getElementById('tema');
  if (bt) { var osc = document.documentElement.getAttribute('data-tema') === 'oscuro'; bt.setAttribute('aria-pressed', osc); bt.textContent = osc ? 'Tema: oscuro' : 'Tema: claro'; }
  ruta();
})();
