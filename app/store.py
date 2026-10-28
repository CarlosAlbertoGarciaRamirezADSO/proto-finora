"""
Repositorios en memoria (patrón Database per Service, simplificado).

Cada servicio tendría su propia base de datos. Para el prototipo se usan
diccionarios protegidos con un lock, suficientes para evidenciar la arquitectura
sin depender de infraestructura externa.
"""
import threading
import uuid
from datetime import datetime, timezone

_lock = threading.Lock()

usuarios = {}      # id -> dict
billeteras = {}    # id -> dict
transacciones = {} # id -> dict


def nuevo_id():
    return str(uuid.uuid4())[:8]


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def crear_usuario(nombre, correo):
    with _lock:
        uid = nuevo_id()
        bid = nuevo_id()
        usuarios[uid] = {"id": uid, "nombre": nombre, "correo": correo, "estadoKYC": "VERIFICADO"}
        billeteras[bid] = {"id": bid, "idUsuario": uid, "saldo": 0, "moneda": "COP"}
        return usuarios[uid], billeteras[bid]


def billetera_de(id_usuario):
    for b in billeteras.values():
        if b["idUsuario"] == id_usuario:
            return b
    return None


def registrar_transaccion(tipo, monto, estado, origen=None, destino=None):
    with _lock:
        tid = nuevo_id()
        transacciones[tid] = {
            "id": tid, "tipo": tipo, "monto": monto, "estado": estado,
            "origen": origen, "destino": destino, "fecha": ahora(),
        }
        return transacciones[tid]
