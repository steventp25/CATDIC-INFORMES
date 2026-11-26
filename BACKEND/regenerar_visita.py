# BACKEND/regenerar_visita.py
# Etapa 5 · B3g-2 — Regenerar el informe de una visita YA «Procesada» (pedido de Steven, 22/11/2026: «Sí, lo necesito»).
#
# Qué hace: vuelve a generar SOLO el STP-MIVED de la visita, con lo que ya está en la BD (elementos de la visita,
# respuestas de la Mesa y plano vigente), y lo publica como versión nueva (` v2`, ` v3`…) sin sobrescribir nada
# (CLAUDE.md §5.2, error 15). Qué NO hace:
#   - no relee el PDF ni el paquete de la visita (no corre el lector) y no borra elementos ni dudas;
#   - no toca los FI-01/02/03 (error 18: un FI que ya existe nunca se rehace; ya incluyen esta visita);
#   - no hace la comprobación P3 («ya hay un STP de su fecha»), porque aquí la versión nueva es justo lo pedido;
#     el salto queda en `auditoria` (acción REGENERAR_SIN_P3);
#   - no cambia el estado de la visita: sigue «Procesada» genere o no. Si hoy hay bloqueos (dudas abiertas, elementos
#     en espera, plano cambiado, cabecera incompleta) no genera nada y lo dice con un evento `aviso`.
#
# Reutiliza `procesador_cola.ProcesoVisita` HEREDANDO de ella (sin editarla): el cruce de cada elemento (`_elemento`), las
# fichas (`_fichas_en_orden`), los bloqueos (`_bloqueos_de_visita`), la generación del STP (`_generar`), la publicación
# sin sobrescribir (`_publicar`) y las dudas con sus eventos. Sustituye: `ejecutar`, `_procesar` (sin lector ni
# estado «En proceso»), `_p3`, `_generar` (solo STP) y `_cerrar` (sin cambio de estado, sin tocar `salida_json`).
# El trabajo usa la misma tabla `trabajos` (tipo 'visita', el esquema no se cambia) y el mismo cerrojo; la regeneración se
# distingue por `"regenerar": true` en los eventos, por la acción `LANZAR_REGENERACION` de la auditoría y por
# `resumen.regenerar`.
import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import config
import procesador_cola as pc
from database import _respaldar_bd, get_connection, usuario_auditoria
from sync.sincronizador import ESTADO_PROCESADA

ACCION_LANZAR = "LANZAR_REGENERACION"
ACCION_SIN_P3 = "REGENERAR_SIN_P3"
ACCION_REGENERAR = "REGENERAR_VISITA"
MOTIVO_SIN_P3 = ("regeneración del informe de una visita Procesada: la versión nueva del STP-MIVED es lo que se pide, "
                 "así que no se comprueba si ya hay un STP de su fecha (P3); se publica como versión nueva sin "
                 "sobrescribir nada.")
TEXTO_FI = "Los formularios MIVED ya incluyen esta visita; no se vuelven a modificar."


class ProcesoRegeneracion(pc.ProcesoVisita):
    """Una visita Procesada: solo vuelve a generar el STP-MIVED. Nunca cambia el estado de la visita."""

    # --- Flujo ---
    def ejecutar(self) -> Dict:
        visita = self._visita()
        if visita is None:
            raise LookupError(f"No existe la visita '{self.visita_id}'.")
        if visita["estado"] != ESTADO_PROCESADA:
            raise pc.VisitaNoProcesable(f"La visita '{self.visita_id}' está '{visita['estado']}': solo se regenera una "
                                        f"visita {ESTADO_PROCESADA}.")
        pc._evento(self.trabajo_id, "visita_inicio", {"visita_id": self.visita_id, "numero": visita["numero"],
                                                      "carpeta": visita["nombre_carpeta"], "regenerar": True,
                                                      "estado_anterior": visita["estado"]})
        return self._procesar(visita)

    def _procesar(self, visita) -> Dict:
        # Sin lector: la visita ya fue leída y sus elementos y fotos (caché) están en la BD.
        self.pdf_visita = self._pdf_de_la_visita(visita)
        self.contexto = self._contexto(visita)
        elementos = pc._con_conexion(lambda c: c.execute("""SELECT * FROM elementos_visita WHERE visita_id = ?
                                                            ORDER BY orden_en_log""", (self.visita_id,)).fetchall())
        resultados: Dict[str, Dict] = {}
        for ev in elementos:
            resultados[ev["uid"]] = self._elemento(ev)
        cambio = True  # mismo reintento que el procesador: Steven pudo responder en la Mesa mientras corría
        while cambio:
            cambio = False
            for ev in elementos:
                r = resultados[ev["uid"]]
                if r["estado"] == "espera" and r["esperando"] and self._todas_resueltas(r["esperando"]):
                    resultados[ev["uid"]] = self._elemento(ev, reintento=True)
                    cambio = cambio or resultados[ev["uid"]]["estado"] != "espera"

        fichas = self._fichas_en_orden(elementos, resultados)
        bloqueos = self._bloqueos_de_visita(visita)
        en_espera = [r for r in resultados.values() if r["estado"] == "espera"]
        if not elementos:
            self.duda("procesador:sin_elementos", "(visita)", "La visita no tiene elementos leídos: no hay nada que "
                      f"informar ({pc.PENDIENTE}).")
            bloqueos.append("sin elementos")
        if pc.FORMATO_STP not in pc._lista(visita["formatos_solicitados"]):
            bloqueos.append(f"la visita no pide {pc.FORMATO_STP}, el único formato que se regenera")
        generado = {}
        if not bloqueos and not en_espera and fichas:
            generado = self._generar(visita, fichas)
        else:
            motivo = "; ".join(bloqueos + ([f"{len(en_espera)} elementos en espera"] if en_espera else []))
            self.avisos.append(f"No se generó ninguna versión nueva del informe: {motivo}.")
            pc._evento(self.trabajo_id, "aviso", {"visita_id": self.visita_id, "regenerar": True,
                                                  "texto": self.avisos[-1]})
        return self._cerrar(visita, resultados, generado)

    # --- Lo que se sustituye ---
    def _p3(self, visita) -> List[str]:
        """Se salta P3 y lo deja en la auditoría; nunca bloquea ni abre la duda de estado."""
        pc._con_conexion(lambda c: pc._auditar(c, ACCION_SIN_P3, self.visita_id,
                                               {"visita_id": self.visita_id, "trabajo": self.trabajo_id,
                                                "motivo": MOTIVO_SIN_P3}, self.usuario))
        return []

    def _generar(self, visita, fichas) -> Dict:
        # Solo el STP-MIVED: sin FI ni CATDIC-STP. `_generar_fi` no se llama nunca.
        solo_stp = {**dict(visita), "formatos_solicitados": json.dumps([pc.FORMATO_STP])}
        return super()._generar(solo_stp, fichas)

    def _cerrar(self, visita, resultados: Dict[str, Dict], generado: Dict) -> Dict:
        abiertas = pc._con_conexion(self._dudas_abiertas)
        limpio = (bool(generado) and generado["limpio"] and not abiertas
                  and all(r["estado"] in ("listo", "anterior") for r in resultados.values()))
        hechos = {a["formato"] for a in generado.get("archivos", [])}
        if limpio and pc.FORMATO_STP not in hechos:
            limpio = False
        publicados = [self._publicar(a, con_dudas=not limpio) for a in generado.get("archivos", [])]
        if any(p["auditor"] for p in publicados):
            limpio = False
        paso = config.obtener_salida_pruebas() / pc.CARPETA_DE_PASO / self.trabajo_id
        for carpeta in (paso, paso.parent):
            try:
                carpeta.rmdir()  # solo si quedó vacía
            except OSError:
                pass
        pdf = [{"formato": p["formato"], "ruta": p["ruta"], "con_dudas": p["con_dudas"]} for p in publicados]
        cuenta = {e: sum(1 for r in resultados.values() if r["estado"] == e) for e in ("listo", "espera", "anterior")}

        def cerrar(conn):
            estado = self._visita(conn)["estado"]  # NO se cambia: sigue como estaba
            dudas = [d["id"] for d in self._dudas_abiertas(conn)]
            pc._auditar(conn, ACCION_REGENERAR, self.visita_id, {
                "trabajo": self.trabajo_id, "estado": estado, "generado": bool(pdf), "limpio": limpio,
                "elementos": {k: r["estado"] for k, r in resultados.items()}, "dudas_abiertas": dudas, "pdf": pdf,
                "fi": "sin tocar", "avisos": self.avisos}, self.usuario)
            return estado, dudas
        estado, dudas = pc._con_conexion(cerrar)
        res = {"visita_id": self.visita_id, "regenerar": True, "estado": estado, "generado": bool(pdf),
               "elementos": cuenta, "dudas": dudas, "pdf": pdf, "avisos": self.avisos, "fi": TEXTO_FI}
        pc._evento(self.trabajo_id, "visita_fin", res)
        return res


# ---------- Trabajo ----------

def lanzar_regeneracion(visita_id: str, usuario: Optional[str] = None, en_hilo: bool = True) -> Dict:
    """
    Crea el trabajo (tabla `trabajos`, tipo 'visita', con el MISMO cerrojo que el procesador) y lo arranca en un hilo.
    Lanza TrabajoEnCurso (409), LookupError (404) o VisitaNoProcesable (409: la visita no está Procesada).
    """
    usuario = usuario or usuario_auditoria()
    with pc._cerrojo:
        conn = get_connection()
        try:
            corriendo = conn.execute("SELECT id FROM trabajos WHERE estado = ?", (pc.CORRIENDO,)).fetchone()
            if corriendo:
                raise pc.TrabajoEnCurso(f"Ya hay un trabajo corriendo ({corriendo['id']}); espera a que termine.")
            fila = conn.execute("SELECT estado FROM visitas WHERE id = ?", (visita_id,)).fetchone()
            if fila is None:
                raise LookupError(f"No existe la visita '{visita_id}'.")
            if fila["estado"] != ESTADO_PROCESADA:
                raise pc.VisitaNoProcesable(
                    f"La visita '{visita_id}' está '{fila['estado']}': solo se regenera el informe de una visita "
                    f"{ESTADO_PROCESADA}. Para las demás usa «Procesar».")
            trabajo_id = f"trab-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"
            conn.execute("""INSERT INTO trabajos (id, tipo, visitas_json, estado, usuario, creado)
                            VALUES (?, 'visita', ?, ?, ?, ?)""",
                         (trabajo_id, pc._json([visita_id]), pc.CORRIENDO, usuario, pc._ahora()))
            pc._auditar(conn, ACCION_LANZAR, trabajo_id, {"tipo": "visita", "regenerar": True, "visitas": [visita_id]},
                        usuario)
            conn.commit()
        finally:
            conn.close()
        hilo = threading.Thread(target=ejecutar_regeneracion, args=(trabajo_id,), name=trabajo_id, daemon=True)
        pc._hilos[trabajo_id] = hilo
    if en_hilo:
        hilo.start()
    else:
        hilo.run()
    return pc.obtener_trabajo(trabajo_id)


def ejecutar_regeneracion(trabajo_id: str):
    """Cuerpo del hilo: igual que `procesador_cola.ejecutar_trabajo` (un respaldo antes de escribir, el error se registra
    y el trabajo se cierra con su evento `fin`), pero con `ProcesoRegeneracion`."""
    trabajo = pc.obtener_trabajo(trabajo_id)
    usuario = trabajo["usuario"]
    resumen = {"regenerar": True, "visitas": [], "pdf": [], "dudas": 0}
    estado, error = pc.TERMINADO, ""
    try:
        conn = get_connection()
        try:
            respaldo = _respaldar_bd(conn, Path(config.obtener_db_path()))
        finally:
            conn.close()
        resumen["respaldo"] = respaldo.name
        for vid in trabajo["visitas"]:
            try:
                r = ProcesoRegeneracion(trabajo_id, vid, usuario).ejecutar()
            except Exception as exc:  # noqa: BLE001 — se registra; la visita no cambió de estado
                r = {"visita_id": vid, "regenerar": True, "estado": None, "error": f"{type(exc).__name__}: {exc}"}
                estado, error = pc.FALLIDO, r["error"]
                pc._evento(trabajo_id, "visita_fin", r)
            resumen["visitas"].append(r)
            resumen["pdf"].extend(r.get("pdf", []))
            resumen["dudas"] += len(r.get("dudas", []))
    except Exception as exc:  # noqa: BLE001
        estado, error = pc.FALLIDO, f"{type(exc).__name__}: {exc}"
    pc._evento(trabajo_id, "fin", {"estado": estado, "error": error, "regenerar": True, "resumen": resumen})

    def cerrar(conn):
        conn.execute("UPDATE trabajos SET estado = ?, terminado = ?, resumen_json = ?, error = ? WHERE id = ?",
                     (estado, pc._ahora(), pc._json(resumen), error, trabajo_id))
        pc._auditar(conn, "TERMINAR_TRABAJO", trabajo_id,
                    {"estado": estado, "error": error, "regenerar": True, "resumen": resumen}, usuario)
    pc._con_conexion(cerrar)
