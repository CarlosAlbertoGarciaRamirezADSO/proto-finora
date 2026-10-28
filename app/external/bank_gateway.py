"""
Simulación de la pasarela bancaria externa (PSE / ACH).

Es el servicio del que no tenemos control y que puede caerse; por eso todas las
llamadas hacia él pasan por el Circuit Breaker. El flag '_caido' permite simular
una caída durante la demostración.
"""
import logging

log = logging.getLogger("finora.banco")
_caido = False


def set_caido(valor: bool):
    global _caido
    _caido = valor
    log.info("pasarela bancaria marcada como %s", "CAÍDA" if valor else "DISPONIBLE")


def procesar_cashin(id_billetera, monto):
    """Devuelve una referencia si el banco responde; lanza error si está caído."""
    if _caido:
        raise ConnectionError("La pasarela bancaria no responde (timeout)")
    return {"referencia": f"PSE-{id_billetera}-{monto}", "estado": "APROBADO"}
