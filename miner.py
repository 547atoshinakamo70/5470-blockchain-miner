import requests
import json
import time
import ecdsa
import hashlib

# Generar clave privada y pública para el minero
private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
public_key = private_key.get_verifying_key()

# Derivar la dirección (hash SHA-256 de la clave pública)
public_key_bytes = public_key.to_string()
address = hashlib.sha256(public_key_bytes).hexdigest()

# Mostrar las claves y la dirección generada
print(f"Clave privada: {private_key.to_string().hex()}")
print(f"Clave pública: {public_key.to_string().hex()}")
print(f"Dirección de minero: {address}")

# Configuración del minero
SERVER_URL = ""  # Cambia esto a la URL pública de tu servidor si lo compartes
MINER_ADDRESS = address  # Usa la dirección generada automáticamente

# Función para obtener transacciones pendientes
def get_pending_transactions():
    try:
        response = requests.get(f"{SERVER_URL}/pending_transactions")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error al obtener transacciones pendientes: {response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"Error de conexión: {e}")
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
    try:
        response = requests.post(f"{SERVER_URL}/propose_block", headers=headers, data=json.dumps(block))
        if response.status_code == 201:
            print("Bloque propuesto exitosamente")
        else:
            print(f"Error al proponer bloque: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Error de conexión: {e}")

# Ciclo de minado
while True:
    try:
        # Obtener el último bloque
        response = requests.get(f"{SERVER_URL}/chain")
        if response.status_code == 200:
            chain = response.json()["chain"]
            last_block = chain[-1]
            index = last_block["index"] + 1
            previous_hash = last_block["hash"]
        else:
            print(f"Error al obtener la cadena: {response.status_code}")
            time.sleep(10)
            continue
    except requests.RequestException as e:
        print(f"Error de conexión: {e}")
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
    print(f"Minando bloque {index} con {len(transactions)} transacciones...")
    propose_block(block)

    # Esperar antes de minar el siguiente bloque
    time.sleep(10)
