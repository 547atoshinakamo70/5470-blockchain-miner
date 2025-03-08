import requests
import json
import time

# Configuración
SERVER_URL = "http://127.0.0.1:5000"    
MINER_ADDRESS = "tu_direccion_de_miner"  # Dirección donde recibirás recompensas

# Función para obtener transacciones pendientes
def get_pending_transactions():
    response = requests.get(f"{SERVER_URL}/pending_transactions")
    if response.status_code == 200:
        return response.json()
    else:
        print("Error al obtener transacciones pendientes")
        return []

# Función para crear un nuevo bloque
def create_block(index, transactions, previous_hash, nonce=0):
    block = {
        "index": index,
        "transactions": transactions,
        "timestamp": time.time(),
        "previous_hash": previous_hash,
        "nonce": nonce
    }
    return block

# Función para enviar el bloque propuesto al servidor
def propose_block(block):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f"{SERVER_URL}/propose_block", headers=headers, data=json.dumps(block))
    if response.status_code == 201:
        print("Bloque propuesto exitosamente")
    else:
        print(f"Error al proponer bloque: {response.text}")

# Ciclo de minado
while True:
    # Obtener el último bloque
    response = requests.get(f"{SERVER_URL}/chain")
    if response.status_code == 200:
        chain = response.json()["chain"]
        last_block = chain[-1]
        index = last_block["index"] + 1
        previous_hash = last_block["hash"]
    else:
        print("Error al obtener la cadena")
        time.sleep(10)
        continue

    # Obtener transacciones pendientes
    transactions = get_pending_transactions()

    # Añadir recompensa para el minero
    reward_tx = {
        "sender": "system",
        "receiver": MINER_ADDRESS,
        "amount": 50,  # Ajusta la recompensa según tu sistema
        "signature": None
    }
    transactions.append(reward_tx)

    # Crear y proponer el bloque
    block = create_block(index, transactions, previous_hash)
    propose_block(block)

    # Esperar antes de minar el siguiente bloque
    time.sleep(10)
