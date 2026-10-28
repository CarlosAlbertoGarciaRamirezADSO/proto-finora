"""
Finora - Punto de entrada (API Gateway).

Expone una sola fachada HTTP y enruta cada petición al servicio correspondiente.
Este archivo concentra el patrón API Gateway: autenticación, validación y
enrutamiento en un único punto de entrada para los clientes.
"""
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app import store
from app.services import transaction_service, notification_service
from app.services.wallet_service import SaldoInsuficiente, BilleteraNoEncontrada
from app.patterns.circuit_breaker import CircuitAbierto
from app.external import bank_gateway

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)-22s | %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(title="Finora API", version="1.0")
notification_service.registrar_suscripciones()


# ----- Esquemas de entrada (validación automática) -----
class UsuarioIn(BaseModel):
    nombre: str
    correo: str

class MontoIn(BaseModel):
    monto: int

class TransferenciaIn(BaseModel):
    origen: str
    destino: str
    monto: int


# ----- Rutas -----
@app.get("/health")
def health():
    return {"estado": "ok", "servicio": "finora-api"}


@app.post("/usuarios", status_code=201)
def crear_usuario(body: UsuarioIn):
    u, b = store.crear_usuario(body.nombre, body.correo)
    return {"usuario": u, "billetera": b}


@app.post("/billeteras/{id_billetera}/recargar")
def recargar(id_billetera: str, body: MontoIn):
    if id_billetera not in store.billeteras:
        raise HTTPException(404, "Billetera no encontrada")
    try:
        ref = transaction_service.recargar(id_billetera, body.monto)
    except CircuitAbierto as e:
        raise HTTPException(503, str(e))
    except ConnectionError as e:
        raise HTTPException(502, str(e))
    return {"estado": "COMPLETADA", "referencia": ref["referencia"],
            "saldo": store.billeteras[id_billetera]["saldo"]}


@app.post("/transferencias", status_code=201)
def transferir(body: TransferenciaIn):
    try:
        tx = transaction_service.transferir(body.origen, body.destino, body.monto)
    except SaldoInsuficiente as e:
        raise HTTPException(422, f"Saldo insuficiente: {e}")
    except BilleteraNoEncontrada as e:
        raise HTTPException(409, f"Transferencia compensada (se revirtió el débito): {e}")
    return tx


@app.get("/transacciones")
def listar():
    return list(store.transacciones.values())


# ----- Endpoint auxiliar para la demostración (simula caída del banco) -----
@app.post("/admin/banco")
def set_banco(body: dict):
    bank_gateway.set_caido(bool(body.get("caido", False)))
    return {"pasarela_caida": bool(body.get("caido", False))}
