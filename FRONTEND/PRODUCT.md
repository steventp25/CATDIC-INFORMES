# Product

<!-- impeccable:product-schema 1 -->

> Registro inferido del brief del Director (Etapa 5) y de `CLAUDE.md`, sin entrevista directa con Steven (regla de la fase: no hablarle salvo bloqueo). Lo marcado *(inferido)* está pendiente de confirmar por Steven al elegir dirección en B1.

## Platform

web

## Users
Steven, ingeniero civil de CATDIC (Consultoría y Asistencia Técnica de Ingeniería Civil, Santo Domingo). Es el único usuario hoy, en su PC con Windows, en `http://localhost:8000`. Usa la app en jornadas largas de oficina para convertir visitas a obra y planos estructurales sellados en informes de supervisión (MIVED) y de levantamiento (HV). Más adelante podría haber más usuarios en red local *(inferido del §1.2 de CLAUDE.md; sin roles en esta etapa)*.

## Product Purpose
Sustituir al 100 % los chats manuales con IA y el antiguo FileMaker: un tablero local donde se registran obras y sus planos vigentes, se sincronizan las visitas desde Dropbox, se confirman los datos de diseño extraídos del plano, se responden las dudas en la Mesa de Dudas y se procesa la cola de visitas para generar los PDF. Éxito: ningún dato de ingeniería llega a un informe sin fuente y sin confirmación de Steven.

## Positioning
Cada valor de diseño que muestra la app está anclado a una celda impresa del plano vectorial vigente (archivo, revisión, página, hoja, recuadro) y nace "pendiente de verificar" hasta que Steven lo confirma; la app nunca rellena ni estima. Lo que no se puede anclar va a la Mesa de Dudas.

## Operating Context
- Planos estructurales sellados (PDF de ~57 MB) y su vectorial; ejes con letra y número (`EJE F-11`, `A'`), niveles `S-4`, `E-9`.
- Carpetas de Dropbox sincronizadas localmente (solo lectura): `LEVANTAMIENTO\VISITA A OBRA\<N. ELEMENTOS NIVEL PARCIAL|COMPLETIVO DD-MM-AAAA>`.
- Visitas numeradas por obra (Terra Living tiene 24), con clase Parcial/Completivo y estados Sin procesar, En cola, En proceso, Con dudas, En revisión, Procesada.
- Formatos de salida: STP-MIVED, MIVED FI-01/02/03, CATDIC-STP, HV-LEV, HV-LEVEVAL, HV-LEVEST, HV-INFTEC.
- Fechas siempre `DD/MM/AAAA`.

## Capabilities and Constraints
- Funciona 100 % sin internet: todo (librerías, fuentes, iconos) se sirve desde `FRONTEND/`. Sin compilación (D5).
- El backend (FastAPI, 29 rutas) no se toca en esta fase; la interfaz tiene que cubrir todo lo que hace hoy el tablero (inventario B0).
- Textos en español. "pendiente de verificar" es un estado visible de primera clase, nunca un hueco.
- Nunca se fabrican firmas ni se muestran datos de ingeniería inventados.

## Brand Commitments
- Nombre: CATDIC. El tablero hoy se llama "Control Taller 2.0" con un distintivo amarillo; si se conservan el nombre y el amarillo es decisión de Steven (D6, sin respuesta) *(abierto)*.
- Tipografía oficial de CATDIC en documentos: Aptos / Aptos Narrow (Windows).
- Rojo de localización de los informes: `RGB(220,0,0)`.

## Evidence on Hand
Datos reales en la copia de la BD: obras Terra Living, Torre P16, Hotel Zoetry Cap Cana · H2 y H5; 24 visitas y 22 dudas de Terra Living; la OT-LEV-001. Tablas del vectorial de Terra Living documentadas en `PLANES/etapa-2-reconocimiento-plano.md` (zapata de muro lindero p. 6, acero en losa p. 10). No hay elementos de diseño confirmados todavía en la BD real.

## Product Principles
1. El plano manda: todo valor muestra de dónde salió.
2. Pendiente es un estado, no un vacío.
3. Lo bloqueante se ve primero.
4. Nada se pierde del tablero actual.
5. Local, rápido y sin red.
