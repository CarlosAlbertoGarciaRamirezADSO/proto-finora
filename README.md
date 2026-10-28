# Finora API — Prototipo

Prototipo del backend de **Finora**, una billetera digital y pasarela de pagos
para pequeños comercios. Implementa, sobre una arquitectura de microservicios, los
patrones de diseño orientados a la nube seleccionados en el informe:

| Patrón | Dónde se ve |
|---|---|
| API Gateway | `app/main.py` (punto de entrada único) |
| Circuit Breaker | `app/patterns/circuit_breaker.py` |
| Publicador/Suscriptor (event-driven) | `app/patterns/event_bus.py` |
| Saga (transacción con compensación) | `app/services/transaction_service.py` |
| Database per Service | `app/store.py` |

## Requisitos

- Python 3.11+
- `pip install -r requirements.txt`

## Ejecución

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8099
```

Documentación interactiva de la API en `http://127.0.0.1:8099/docs`.

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado del servicio |
| POST | `/usuarios` | Crea un usuario y su billetera |
| POST | `/billeteras/{id}/recargar` | Recarga de saldo (cash-in) |
| POST | `/transferencias` | Transferencia P2P (Saga) |
| GET | `/transacciones` | Historial de transacciones |

## Demostración

El script `demo.sh` ejecuta el flujo completo: creación de usuarios, recarga,
una transferencia exitosa, una transferencia con compensación (destino inválido),
un rechazo por saldo insuficiente y la apertura y recuperación del Circuit Breaker
al simular la caída de la pasarela bancaria.

```bash
bash demo.sh
```
