import sys
import time
import logging
import hashlib
import json
import subprocess
import threading
import os
import random
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from cryptography.fernet import Fernet
import psycopg2
from psycopg2 import pool
import pika
import tensorflow as tf
from tensorflow.keras import layers
import numpy as np
from dotenv import load_dotenv
import requests

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("blockchain.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Parámetros de la blockchain
TOKEN_NAME = "5470"
TOKEN_SYMBOL = "547"
TOKEN_SUPPLY = 5470000      # Total de tokens
BLOCK_TIME = 10           # Tiempo entre bloques en segundos
NUM_NODES = 5             # Número de nodos en la red
DB_URL = 'postgresql://postgres:YOUR_DB_PASSWORD@localhost:5432/blockchain'
KYC_API_URL = 'https://YOUR_KYC_API_URL/verify'
BLOCK_REWARD_INITIAL = 50   # Recompensa inicial por bloque
COMMISSION_RATE = 0.002     # Comisión por transacción

# Parámetros API y puerto para la minería
API_URL = "http://2.137.118.154:5000"  # Tu IP pública y puerto para la API

# Conexión a la base de datos
db_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=50,
    dbname="blockchain",
    user="postgres",
    password=os.getenv('DB_PASSWORD', 'YOUR_DB_PASSWORD'),
    host="localhost",
    port="5432"
)

# Clave de cifrado para datos sensibles
FERNET_KEY = os.getenv('FERNET_KEY', Fernet.generate_key().decode()).encode()
cipher = Fernet(FERNET_KEY)

# Clase para representar una transacción
class Transaction:
    def __init__(self, from_address, to_address, amount, timestamp, metadata=None):
        self.from_address = from_address
        self.to_address = to_address
        self.amount = amount
        self.timestamp = timestamp
        self.metadata = metadata or {}  # Para KYC u otros datos
        self.signature = None
        self.zk_proof = None

    def to_dict(self):
        return {
            "from": self.from_address,
            "to": self.to_address,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "signature": self.signature,
            "zk_proof": self.zk_proof
        }

    def sign(self, private_key):
        tx_data = f"{self.from_address}{self.to_address}{self.amount}{self.timestamp}{json.dumps(self.metadata)}"
        sk = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
        self.signature = sk.sign(tx_data.encode()).hex()

    def generate_zk_proof(self):
        try:
            tx_data = json.dumps(self.to_dict())
            result = subprocess.run(['./zk_proof_generator', tx_data], capture_output=True, text=True, timeout=5)
            self.zk_proof = result.stdout.strip()
        except Exception as e:
            logging.error(f"Error generando zk-proof: {e}")
            self.zk_proof = "simulated_proof"

    def verify_signature(self):
        tx_data = f"{self.from_address}{self.to_address}{self.amount}{self.timestamp}{json.dumps(self.metadata)}"
        vk = VerifyingKey.from_string(bytes.fromhex(self.from_address), curve=SECP256k1)
        try:
            return vk.verify(bytes.fromhex(self.signature), tx_data.encode())
        except Exception:
            return False

# Clase para representar un bloque
class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "transactions": [t.to_dict() for t in self.transactions],
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

# Clase de la blockchain
class Blockchain:
    def __init__(self):
        self.chain = self.load_chain_from_db()
        self.pending_transactions = []
        self.balances = self.load_balances_from_db()
        self.owner_private_key, self.owner_public_key = self.create_genesis_block()

    def create_genesis_block(self):
        private_key, public_key = generate_key_pair()
        genesis_tx = Transaction("genesis", public_key, TOKEN_SUPPLY, time.time(), {"ico": True})
        genesis_block = Block(0, [genesis_tx], time.time(), "0")
        if not self.chain:
            self.chain.append(genesis_block)
            self.balances[public_key] = TOKEN_SUPPLY
            self.save_chain_to_db()
            self.save_balances_to_db()
        return private_key, public_key

    def add_block(self, block):
        if self.validate_block(block):
            self.chain.append(block)
            for tx in block.transactions:
                if tx.from_address == "system":
                    self.balances[tx.to_address] = self.balances.get(tx.to_address, 0) + tx.amount
                elif tx.from_address != "genesis":
                    commission = int(tx.amount * COMMISSION_RATE)
                    self.balances[tx.from_address] -= (tx.amount + commission)
                    self.balances[tx.to_address] = self.balances.get(tx.to_address, 0) + tx.amount
                    self.balances[self.owner_public_key] = self.balances.get(self.owner_public_key, 0) + commission
                else:
                    self.balances[tx.to_address] = self.balances.get(tx.to_address, 0) + tx.amount
            self.save_chain_to_db()
            self.save_balances_to_db()
            return True
        return False

    def load_chain_from_db(self):
        conn = db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT data FROM blockchain ORDER BY index")
                chain = [json.loads(row[0]) for row in cur.fetchall()]
                return [Block(b["index"], [Transaction(**t) for t in b["transactions"]],
                              b["timestamp"], b["previous_hash"], b["nonce"]) for b in chain]
        except Exception as e:
            logging.error(f"Error cargando cadena desde DB: {e}")
            return []
        finally:
            db_pool.putconn(conn)

    def save_chain_to_db(self):
        conn = db_pool.getconn()
        try:
            with conn.cursor() as cur:
                for block in self.chain:
                    cur.execute(
                        "INSERT INTO blockchain (index, data) VALUES (%s, %s) ON CONFLICT (index) DO UPDATE SET data = %s",
                        (block.index, json.dumps(block.__dict__), json.dumps(block.__dict__))
                    )
                conn.commit()
        except Exception as e:
            logging.error(f"Error guardando cadena en DB: {e}")
        finally:
            db_pool.putconn(conn)

    def load_balances_from_db(self):
        conn = db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT address, balance FROM balances")
                return {row[0]: row[1] for row in cur.fetchall()}
        except Exception as e:
            logging.error(f"Error cargando saldos desde DB: {e}")
            return {}
        finally:
            db_pool.putconn(conn)

    def save_balances_to_db(self):
        conn = db_pool.getconn()
        try:
            with conn.cursor() as cur:
                for address, balance in self.balances.items():
                    cur.execute(
                        "INSERT INTO balances (address, balance) VALUES (%s, %s) ON CONFLICT (address) DO UPDATE SET balance = %s",
                        (address, balance, balance)
                    )
                conn.commit()
        except Exception as e:
            logging.error(f"Error guardando saldos en DB: {e}")
        finally:
            db_pool.putconn(conn)

# Función para generar un par de claves
def generate_key_pair():
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()
    return sk.to_string().hex(), vk.to_string().hex()

# Configuración de la conexión API
def connect_to_api():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            logging.info("Conexión exitosa con la API.")
        else:
            logging.error(f"Error conectando con la API: {response.status_code}")
    except Exception as e:
        logging.error(f"Error conectando con la API: {e}")

# Función para la minería
def mining_loop():
    blockchain = Blockchain()
    while True:
        try:
            connect_to_api()  # Conectar a la API en cada ciclo
            # Aquí incluirás la lógica de minería del bloque
            time.sleep(BLOCK_TIME)
        except Exception as e:
            logging.error(f"Error durante el ciclo de minería: {e}")

# Iniciar el ciclo de minería
if __name__ == "__main__":
    logging.info("Blockchain operativa. Iniciando minería...")
    threading.Thread(target=mining_loop, daemon=True).start()
