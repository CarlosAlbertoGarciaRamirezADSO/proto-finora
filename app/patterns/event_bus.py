"""
Patrón Publicador/Suscriptor (bus de eventos en proceso).

Desacopla a los servicios: el Servicio de Transacciones no conoce al de
Notificaciones; solo publica un evento en el bus y quien esté suscrito reacciona.
En producción este bus se reemplaza por un message broker (RabbitMQ, Kafka o un
servicio administrado en la nube), pero el contrato de publicar/suscribir es el mismo.
"""
import logging
from collections import defaultdict

log = logging.getLogger("finora.eventbus")


class EventBus:
    def __init__(self):
        self._suscriptores = defaultdict(list)

    def suscribir(self, tipo_evento, manejador):
        self._suscriptores[tipo_evento].append(manejador)
        log.info("suscrito '%s' al evento '%s'", getattr(manejador, "__name__", manejador), tipo_evento)

    def publicar(self, tipo_evento, datos):
        log.info("publicando evento '%s' -> %s", tipo_evento, datos)
        for manejador in self._suscriptores.get(tipo_evento, []):
            manejador(datos)


# Instancia única compartida (patrón Singleton de acceso al bus)
bus = EventBus()
