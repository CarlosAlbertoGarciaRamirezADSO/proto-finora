"""
Servicio de Notificaciones: suscriptor del bus de eventos.

No es llamado directamente por nadie; reacciona a los eventos que publican los
demás servicios. Así, agregar o quitar notificaciones no obliga a tocar el
Servicio de Transacciones.
"""
import logging
from app.patterns.event_bus import bus

log = logging.getLogger("finora.notificaciones")


def al_completar_transferencia(datos):
    log.info("push al usuario %s: «Transferencia de %s COP realizada con éxito»",
             datos["destino"], datos["monto"])


def al_fallar_transferencia(datos):
    log.info("push al usuario %s: «No se pudo completar la transferencia: %s»",
             datos["origen"], datos["motivo"])


def registrar_suscripciones():
    bus.suscribir("TransferenciaCompletada", al_completar_transferencia)
    bus.suscribir("TransferenciaFallida", al_fallar_transferencia)
