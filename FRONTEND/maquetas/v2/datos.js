/* Etapa 5 · B1 v3 — DATOS SINTÉTICOS DE DEMOSTRACIÓN.
   Nada de esto es una obra, una visita ni un valor de plano real.
   Los nombres llevan «(sintético)» para que nadie los confunda con datos de la BD. */
window.DATOS = {
  hoy: '19/11/2026',
  obras: [
    { id: 'norte', nombre: 'Residencial Ejemplo Norte', corto: 'Ej. Norte', tipo: 'Supervisión', niveles: 'S-2 a E-9',
      visitas: 14, dudasBloq: 3, enCola: 2, revisiones: 4, ultima: '17/11/2026', planos: 'Rev. 3 vigente (12/10/2026)' },
    { id: 'torre', nombre: 'Torre Ejemplo 12', corto: 'Torre Ej. 12', tipo: 'Supervisión', niveles: 'S-1 a E-14',
      visitas: 6, dudasBloq: 1, enCola: 0, revisiones: 1, ultima: '11/11/2026', planos: 'Rev. 1 vigente (02/09/2026)' },
    { id: 'nave', nombre: 'Nave Ejemplo Sur', corto: 'Nave Ej. Sur', tipo: 'Levantamiento', niveles: 'E-1',
      visitas: 2, dudasBloq: 0, enCola: 1, revisiones: 0, ultima: '05/11/2026', planos: 'pendiente de verificar' }
  ],
  // Pendientes de la bandeja común: leen los mismos registros que Mesa, Cola, Confirmar y Órdenes (Fase D-a).
  pendientes: [
    { id: 'p1', tipo: 'Duda bloqueante', origen: 'obra', obra: 'norte', donde: 'Visita #13 · Nivel E-3',
      motivo: 'La etiqueta «C4 B» no trae número de eje', siguiente: 'Responder en la Mesa de Dudas', abre: 'Mesa de Dudas', dias: 2, nuevo: true, cubo: 'vencido' },
    { id: 'p2', tipo: 'Revisión de plano', origen: 'obra', obra: 'norte', donde: 'Hoja E-3 · tabla de columnas',
      motivo: '6 valores propuestos sin confirmar', siguiente: 'Revisar planos', abre: 'Revisión de planos', dias: 1, nuevo: true, cubo: 'semana' },
    { id: 'p3', tipo: 'Visita en cola', origen: 'obra', obra: 'norte', donde: 'Visita #14 · E-4 Parcial',
      motivo: 'Lista para procesar', siguiente: 'Procesar cola', abre: 'Cola de visitas', dias: 0, nuevo: false, cubo: 'semana' },
    { id: 'p4', tipo: 'Duda bloqueante', origen: 'obra', obra: 'torre', donde: 'Visita #6 · Nivel E-2',
      motivo: 'Planta y detalle no coinciden en la viga V-7', siguiente: 'Responder en la Mesa de Dudas', abre: 'Mesa de Dudas', dias: 6, nuevo: false, cubo: 'vencido' },
    { id: 'p5', tipo: 'Fuente faltante', origen: 'trabajo', trabajo: 'Esclerometría · Local Ejemplo (sintético)', donde: 'Trabajo independiente',
      motivo: 'Falta el plano de planta del nivel 1', siguiente: 'Aportar fuente', abre: 'Ficha del trabajo', dias: 3, nuevo: false, cubo: 'sinfecha' },
    { id: 'p6', tipo: 'Entrega', origen: 'obra', obra: 'norte', donde: 'STP · Verticales E-3 Parcial',
      motivo: 'Informe generado, falta revisarlo', siguiente: 'Revisar informe', abre: 'Informes', dias: 1, nuevo: false, cubo: 'semana' },
    { id: 'p7', tipo: 'Orden de trabajo', origen: 'obra', obra: 'nave', donde: 'OT-EJ-002',
      motivo: 'Asignada sin fecha de visita', siguiente: 'Abrir orden', abre: 'Órdenes', dias: 9, nuevo: false, cubo: 'sinfecha' },
    { id: 'p8', tipo: 'Duda bloqueante', origen: 'obra', obra: 'norte', donde: 'Visita #12 · Nivel E-3',
      motivo: 'Foto sin etiqueta abre un elemento nuevo', siguiente: 'Responder en la Mesa de Dudas', abre: 'Mesa de Dudas', dias: 4, nuevo: false, cubo: 'mas' }
  ],
  actividad: [
    { cuando: '17/11/2026 16:40', que: 'Visita #14 sincronizada desde Dropbox', obra: 'norte' },
    { cuando: '17/11/2026 11:05', que: 'Duda de la visita #11 respondida', obra: 'norte' },
    { cuando: '15/11/2026 09:30', que: 'Plano Rev. 3 marcado como vigente', obra: 'norte' },
    { cuando: '11/11/2026 18:12', que: 'Informe STP · Losa E-2 generado (v2)', obra: 'torre' }
  ],
  // Revisión de planos: elementos propuestos por la lectura del plano (sintéticos).
  elementos: [
    { id: 'C1', tipo: 'Columna', ejes: 'EJE A-1', nivel: 'E-3', estado: 'propuesto', x: 70, y: 70 },
    { id: 'C2', tipo: 'Columna', ejes: 'EJE B-1', nivel: 'E-3', estado: 'confirmado', x: 230, y: 70 },
    { id: 'C3', tipo: 'Columna', ejes: 'EJE C-1', nivel: 'E-3', estado: 'propuesto', x: 390, y: 70 },
    { id: 'C4', tipo: 'Columna', ejes: 'EJE A-2', nivel: 'E-3', estado: 'conflicto', x: 70, y: 210 },
    { id: 'C5', tipo: 'Columna', ejes: 'EJE B-2', nivel: 'E-3', estado: 'propuesto', x: 230, y: 210 },
    { id: 'C6', tipo: 'Columna', ejes: 'pendiente de verificar', nivel: 'E-3', estado: 'pendiente', x: 390, y: 210 }
  ],
  // Valores propuestos por elemento. fuente = de dónde sale; null = no hay fuente → pendiente de verificar.
  valores: {
    C1: [
      { campo: 'Sección', valor: '0.40 × 0.40 m', fuente: 'Hoja E-3 · pág. 4 · tabla de columnas, fila C1', estado: 'propuesto' },
      { campo: 'Acero longitudinal', valor: '8 #6', fuente: 'Hoja E-3 · pág. 4 · tabla de columnas, fila C1', estado: 'propuesto' },
      { campo: 'Estribos', valor: '#3 @ 0.15 m', fuente: 'Hoja E-3 · pág. 4 · detalle típico de estribos', estado: 'propuesto' },
      { campo: 'Cuantía (cálculo)', valor: '0.0142', fuente: 'Calculada: As / (b × h)', estado: 'calculado' }
    ],
    C4: [
      { campo: 'Sección', valor: '0.40 × 0.50 m', fuente: 'Hoja E-3 · pág. 4 · tabla de columnas, fila C4', estado: 'conflicto',
        nota: 'La planta rotula 0.40 × 0.40 m. Manda el detalle, pero se detiene y va a la Mesa de Dudas.' },
      { campo: 'Acero longitudinal', valor: '10 #6', fuente: 'Hoja E-3 · pág. 4 · tabla de columnas, fila C4', estado: 'propuesto' },
      { campo: 'Estribos', valor: null, fuente: null, estado: 'pendiente' },
      { campo: 'Cuantía (cálculo)', valor: null, fuente: 'Se calcula al confirmar la sección', estado: 'pendiente' }
    ],
    C6: [
      { campo: 'Sección', valor: null, fuente: null, estado: 'pendiente' },
      { campo: 'Acero longitudinal', valor: null, fuente: null, estado: 'pendiente' },
      { campo: 'Ejes', valor: null, fuente: 'La etiqueta de visita «L5» puede ser un eje o un ID', estado: 'pendiente' }
    ]
  },
  visitaFoto: { visita: '#13', fecha: '14/11/2026', foto: 'IMG_0412 (sintética)', etiqueta: 'C1 4A', lectura: 'ID C1 · EJE A-4',
    regla: 'Un ID seguido del cruce: el orden número/letra puede venir cruzado (4A → A-4).' },
  servicios: [
    { id: 'stp', nombre: 'Supervisión STP', desc: 'Informe STP-MIVED por visita.', hoy: 'Generador existente, hoy solo dentro de una obra' },
    { id: 'levsup', nombre: 'Levantamiento de supervisión', desc: 'Fichas de elementos en obra.', hoy: null },
    { id: 'estructural', nombre: 'Levantamiento estructural', desc: 'Refuerzo con escáner y fichas HV.', hoy: null },
    { id: 'visual', nombre: 'Inspección visual', desc: 'Registro fotográfico y observaciones.', hoy: null },
    { id: 'dimensional', nombre: 'Levantamiento dimensional', desc: 'Medidas de elementos existentes.', hoy: null },
    { id: 'escler', nombre: 'Esclerometría', desc: 'Ensayo con martillo de rebote.', hoy: null }
  ]
};
