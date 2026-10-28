#!/usr/bin/env bash
API="http://127.0.0.1:8099"
jqid() { python3 -c "import sys,json;print(json.load(sys.stdin)$1)"; }

line() { printf '\n$ %s\n' "$1"; }

line "curl -s $API/health"
curl -s $API/health; echo

line 'Crear usuario Ana'
RA=$(curl -s -X POST $API/usuarios -H 'Content-Type: application/json' -d '{"nombre":"Ana Rojas","correo":"ana@correo.com"}')
echo "$RA"
WA=$(echo "$RA" | jqid "['billetera']['id']")

line 'Crear usuario Beto'
RB=$(curl -s -X POST $API/usuarios -H 'Content-Type: application/json' -d '{"nombre":"Beto Diaz","correo":"beto@correo.com"}')
echo "$RB"
WB=$(echo "$RB" | jqid "['billetera']['id']")
echo "   (billetera Ana=$WA  billetera Beto=$WB)"

line "Recargar 500000 a la billetera de Ana"
curl -s -X POST $API/billeteras/$WA/recargar -H 'Content-Type: application/json' -d '{"monto":500000}'; echo

line "Transferir 200000 de Ana a Beto  (Saga exitosa)"
curl -s -X POST $API/transferencias -H 'Content-Type: application/json' -d "{\"origen\":\"$WA\",\"destino\":\"$WB\",\"monto\":200000}"; echo

line "Transferir 100000 de Ana a un destino INVALIDO  (Saga con compensacion)"
curl -s -o /tmp/r.json -w "HTTP %{http_code}\n" -X POST $API/transferencias -H 'Content-Type: application/json' -d "{\"origen\":\"$WA\",\"destino\":\"ZZZZ0000\",\"monto\":100000}"; cat /tmp/r.json; echo

line "Transferir 999999 de Ana a Beto  (saldo insuficiente -> rechazada)"
curl -s -w "\nHTTP %{http_code}\n" -X POST $API/transferencias -H 'Content-Type: application/json' -d "{\"origen\":\"$WA\",\"destino\":\"$WB\",\"monto\":999999}"; echo

echo; echo "=========  DEMOSTRACION DEL CIRCUIT BREAKER  ========="
line "Simular caida de la pasarela bancaria"
curl -s -X POST $API/admin/banco -H 'Content-Type: application/json' -d '{"caido":true}'; echo

for i in 1 2 3 4; do
  line "Intento de recarga #$i (banco caido)"
  curl -s -w "\nHTTP %{http_code}\n" -X POST $API/billeteras/$WA/recargar -H 'Content-Type: application/json' -d '{"monto":50000}'; echo
done

line "Restablecer la pasarela bancaria"
curl -s -X POST $API/admin/banco -H 'Content-Type: application/json' -d '{"caido":false}'; echo
line "Esperar el tiempo de reset del circuito (5 s) ..."
sleep 6
line "Recarga tras la recuperacion (circuito MEDIO_ABIERTO -> CERRADO)"
curl -s -X POST $API/billeteras/$WA/recargar -H 'Content-Type: application/json' -d '{"monto":50000}'; echo

line "curl -s $API/transacciones  (historial)"
curl -s $API/transacciones | python3 -m json.tool
