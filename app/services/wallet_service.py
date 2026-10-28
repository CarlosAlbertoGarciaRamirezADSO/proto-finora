"""Servicio de Billetera: operaciones atómicas sobre el saldo."""
import logging
from app import store

log = logging.getLogger("finora.billetera")


class SaldoInsuficiente(Exception):
    pass


class BilleteraNoEncontrada(Exception):
    pass


def debitar(id_billetera, monto):
    b = store.billeteras[id_billetera]
    if b["saldo"] < monto:
        raise SaldoInsuficiente(f"Saldo {b['saldo']} < monto {monto}")
    b["saldo"] -= monto
    log.info("debitado %s de billetera %s (saldo: %s)", monto, id_billetera, b["saldo"])
    return b["saldo"]


def acreditar(id_billetera, monto):
    if id_billetera not in store.billeteras:
        raise BilleteraNoEncontrada(f"La billetera destino {id_billetera} no existe")
    b = store.billeteras[id_billetera]
    b["saldo"] += monto
    log.info("acreditado %s a billetera %s (saldo: %s)", monto, id_billetera, b["saldo"])
    return b["saldo"]
