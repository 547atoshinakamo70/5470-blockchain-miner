#!/usr/bin/env python3
import time
import json
import hashlib
import logging
import requests
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Configuración del servidor de la blockchain y parámetros de minería
BLOCKCHAIN_SERVER_URL = os.getenv("BLOCKCHAIN_SERVER_URL", "http://localhost:5000")
BLOCK_TIME = int(os.getenv("BLOCK_TIME", 10))
DIFFICULTY = int(os.getenv("MINING_DIFFICULTY", 4))  # Ejemplo: 4 ceros al inicio del hash

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_chain():
    """Obtiene la cadena de bloques desde el servidor central."""
    try:
        response = requests.get(f"{BLOCKCHAIN_SERVER_URL}/chain")
        if response.status_code == 200:
            return response.json()["chain"]
        else:
            logging.error("Error al obtener la cadena: " + response.text)
            return None
    except Exception as e:
        logging.error(f"Error conectando con la blockchain: {e}")
        return None

def get_pending_transactions():
    """Obtiene las transacciones pendientes desde el servidor central."""
    try:
        response = requests.get(f"{BLOCKCHAIN_SERVER_URL}/pending_transactions")
        if response.status_code == 200:
            return response.json()
        else:
            logging.error("Error al obtener transacciones pendientes: " + response.text)
            return []
    except Exception as e:
        logging.error(f"Error conectando con la blockchain: {e}")
        return []

def calculate_hash(index, transactions, timestamp, previous_hash, nonce):
    """Calcula el hash del bloque a partir de sus datos."""
    block_data = {
        "index": index,
        "transactions": transactions,
        "timestamp": timestamp,
        "previous_hash": previous_hash,
        "nonce": nonce
    }
    block_string = json.dumps(block_data, sort_keys=True).encode()
    return hashlib.sha256(block_string).hexdigest()

def propose_block(block):
    """Envía el bloque minado al servidor central de la blockchain."""
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{BLOCKCHAIN_SERVER_URL}/propose_block",
                                 headers=headers, data=json.dumps(block))
        if response.status_code == 201:
            logging.info("Bloque propuesto exitosamente.")
        else:
            logging.error("Error al proponer el bloque: " + response.text)
    except Exception as e:
        logging.error(f"Error al enviar el bloque: {e}")

def mine_block():
    """Realiza el proceso de minería: obtiene datos, calcula el nonce y propone el bloque."""
    chain = get_chain()
    if not chain:
        logging.error("No se pudo obtener la cadena. Abortar minería.")
        return
    last_block = chain[-1]
    index = last_block["index"] + 1
    previous_hash = last_block["hash"]
    transactions = get_pending_transactions()
    # Se asume que la blockchain central agrega la transacción de recompensa,
    # por lo que el minero solo recopila las transacciones pendientes.
    timestamp = time.time()
    nonce = 0

    logging.info("Iniciando prueba de trabajo...")
    while True:
        block_hash = calculate_hash(index, transactions, timestamp, previous_hash, nonce)
        if block_hash.startswith("0" * DIFFICULTY):
            logging.info(f"Bloque minado: nonce={nonce}, hash={block_hash}")
            break
        nonce += 1

    # Construir el bloque minado
    block = {
        "index": index,
        "transactions": transactions,
        "timestamp": timestamp,
        "previous_hash": previous_hash,
        "nonce": nonce
    }
    propose_block(block)

def mining_loop():
    """Bucle continuo para minar bloques."""
    while True:
        logging.info("Ejecutando ciclo de minería...")
        mine_block()
        time.sleep(BLOCK_TIME)

if __name__ == "__main__":
    logging.info("Iniciando el proceso de minería...")
    mining_loop()
