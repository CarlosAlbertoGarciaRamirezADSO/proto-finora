"""
Servicio de Transacciones: orquesta las operaciones de dinero.

- recargar(): usa el Circuit Breaker para hablar con la pasarela bancaria.
- transferir(): implementa el patrón Saga. Una transferencia son dos pasos
  (debitar al origen y acreditar al destino). Si el segundo paso falla, se
  ejecuta una acción compensatoria que revierte el primero, de modo que el
  sistema nunca queda en un estado inconsistente (dinero que desaparece).
"""
import logging
from app import store
from app.services import wallet_service
from app.services.wallet_service import SaldoInsuficiente
from app.patterns.circuit_breaker import CircuitBreaker, CircuitAbierto
from app.patterns.event_bus import bus
from app.external import bank_gateway

log = logging.getLogger("finora.transacciones")

# Un breaker por servicio externo
breaker_banco = CircuitBreaker("pasarela-bancaria", umbral_fallos=3, tiempo_reset=5)


def recargar(id_billetera, monto):
    try:
        ref = breaker_banco.llamar(bank_gateway.procesar_cashin, id_billetera, monto)
    except CircuitAbierto as e:
        store.registrar_transaccion("RECARGA", monto, "RECHAZADA", destino=id_billetera)
        raise e
    except ConnectionError as e:
        store.registrar_transaccion("RECARGA", monto, "FALLIDA", destino=id_billetera)
        raise e
    wallet_service.acreditar(id_billetera, monto)
    store.registrar_transaccion("RECARGA", monto, "COMPLETADA", destino=id_billetera)
    return ref


def transferir(id_origen, id_destino, monto):
    log.info("iniciando Saga de transferencia %s -> %s por %s", id_origen, id_destino, monto)
    # Paso 1: debitar al origen
    try:
        wallet_service.debitar(id_origen, monto)
    except SaldoInsuficiente as e:
        bus.publicar("TransferenciaFallida", {"origen": id_origen, "monto": monto, "motivo": str(e)})
        store.registrar_transaccion("TRANSFERENCIA", monto, "RECHAZADA", id_origen, id_destino)
        raise e

    # Paso 2: acreditar al destino; si falla, se compensa el débito
    try:
        wallet_service.acreditar(id_destino, monto)
    except Exception as e:
        log.error("fallo al acreditar; ejecutando compensación (revertir débito)")
        wallet_service.acreditar(id_origen, monto)  # acción compensatoria
        bus.publicar("TransferenciaFallida", {"origen": id_origen, "monto": monto, "motivo": str(e)})
        store.registrar_transaccion("TRANSFERENCIA", monto, "COMPENSADA", id_origen, id_destino)
        raise e

    tx = store.registrar_transaccion("TRANSFERENCIA", monto, "COMPLETADA", id_origen, id_destino)
    bus.publicar("TransferenciaCompletada", {"origen": id_origen, "destino": id_destino, "monto": monto})
    return tx
