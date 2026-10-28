"""
Patrón Circuit Breaker.

Protege al sistema frente a fallos de un servicio externo (en Finora, la
pasarela bancaria). Cuando se acumulan varios fallos consecutivos el circuito
se "abre" y las llamadas siguientes fallan de inmediato (fail-fast), sin seguir
golpeando un servicio que ya se sabe caído. Tras un tiempo de espera el circuito
pasa a "medio abierto" y deja pasar una llamada de prueba para decidir si vuelve
a cerrarse.
"""
import time
import logging

log = logging.getLogger("finora.circuit")


class CircuitAbierto(Exception):
    """Se lanza cuando el circuito está abierto y se rechaza la llamada."""


class CircuitBreaker:
    CERRADO = "CERRADO"
    ABIERTO = "ABIERTO"
    MEDIO_ABIERTO = "MEDIO_ABIERTO"

    def __init__(self, nombre, umbral_fallos=3, tiempo_reset=5):
        self.nombre = nombre
        self.umbral_fallos = umbral_fallos
        self.tiempo_reset = tiempo_reset
        self.estado = self.CERRADO
        self.fallos = 0
        self.abierto_desde = 0.0

    def llamar(self, funcion, *args, **kwargs):
        if self.estado == self.ABIERTO:
            if time.time() - self.abierto_desde >= self.tiempo_reset:
                self.estado = self.MEDIO_ABIERTO
                log.info("[%s] tiempo de reset cumplido -> MEDIO_ABIERTO", self.nombre)
            else:
                raise CircuitAbierto(
                    f"Circuito '{self.nombre}' ABIERTO: se rechaza la llamada (fail-fast)"
                )
        try:
            resultado = funcion(*args, **kwargs)
        except Exception as e:
            self._registrar_fallo()
            raise e
        self._registrar_exito()
        return resultado

    def _registrar_fallo(self):
        self.fallos += 1
        log.warning("[%s] fallo registrado (%d/%d)", self.nombre, self.fallos, self.umbral_fallos)
        if self.estado == self.MEDIO_ABIERTO or self.fallos >= self.umbral_fallos:
            self.estado = self.ABIERTO
            self.abierto_desde = time.time()
            log.error("[%s] umbral superado -> estado ABIERTO", self.nombre)

    def _registrar_exito(self):
        if self.estado in (self.MEDIO_ABIERTO, self.ABIERTO):
            log.info("[%s] llamada exitosa -> estado CERRADO", self.nombre)
        self.estado = self.CERRADO
        self.fallos = 0
