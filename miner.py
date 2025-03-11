from flask import Flask, request, jsonify
import requests
import json
import time
import ecdsa
import hashlib
import os

app = Flask(__name__)

# Configuración del servidor de la blockchain
BLOCKCHAIN_SERVER_URL = os.getenv("http://172.21.50.114:5000", "http://localhost:5000")

# Función para generar claves para el minero
def generate_miner_keys():
    private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    public_key = private_key.get_verifying_key()
    public_key_bytes = public_key.to_string()
    address = hashlib.sha256(public_key_bytes).hexdigest()
    return private_key.to_string().hex(), public_key.to_string().hex(), address

# Endpoint para registrar un nuevo minero
@app.route('/register', methods=['POST'])
def register():
    private_key, public_key, address = generate_miner_keys()
    return jsonify({
        "private_key": private_key,
        "public_key": public_key,
        "address": address
    }), 201

# Endpoint para minar un bloque
@app.route('/mine', methods=['POST'])
def mine():
    data = request.get_json()
    miner_address = data.get("miner_address")
    if not miner_address:
        return jsonify({"error": "Se requiere la dirección del minero"}), 400

    try:
        # Obtener el último bloque
        response = requests.get(f"{BLOCKCHAIN_SERVER_URL}/chain")
        if response.status_code != 200:
            return jsonify({"error": "No se pudo obtener la cadena"}), 500
        chain = response.json()["chain"]
        last_block = chain[-1]
        index = last_block["index"] + 1
        previous_hash = last_block["hash"]

        # Obtener transacciones pendientes
        response = requests.get(f"{BLOCKCHAIN_SERVER_URL}/pending_transactions")
        if response.status_code != 200:
            return jsonify({"error": "No se pudieron obtener las transacciones pendientes"}), 500
        transactions = response.json()

        # Añadir recompensa para el minero
        reward_tx = {
            "sender": "system",
            "receiver": miner_address,
            "amount": 50,  # Ajusta la recompensa según tu sistema
            "signature": None
        }
        transactions.append(reward_tx)

        # Crear el bloque
        block = {
            "index": index,
            "transactions": transactions,
            "timestamp": time.time(),
            "previous_hash": previous_hash,
            "nonce": 0  # Ajusta según tu algoritmo de consenso
        }

        # Proponer el bloque al servidor de la blockchain
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{BLOCKCHAIN_SERVER_URL}/propose_block", headers=headers, data=json.dumps(block))
        if response.status_code == 201:
            return jsonify({"message": "Bloque propuesto exitosamente"}), 201
        else:
            return jsonify({"error": "No se pudo proponer el bloque", "details": response.text}), 400
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

# Endpoint para enviar tokens (ejemplo básico)
@app.route('/send', methods=['POST'])
def send_tokens():
    data = request.get_json()
    sender_address = data.get("sender_address")
    receiver_address = data.get("receiver_address")
    amount = data.get("amount")
    private_key = data.get("private_key")  # La clave privada debe venir del cliente

    if not all([sender_address, receiver_address, amount, private_key]):
        return jsonify({"error": "Faltan datos requeridos"}), 400

    # Crear transacción
    tx = {
        "sender": sender_address,
        "receiver": receiver_address,
        "amount": amount,
        "signature": None  # Firma pendiente (ver más abajo)
    }

    # Firmar la transacción (simplificado)
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
    tx_string = json.dumps(tx, sort_keys=True).encode()
    signature = sk.sign(tx_string).hex()
    tx["signature"] = signature

    # Enviar la transacción al servidor de la blockchain
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{BLOCKCHAIN_SERVER_URL}/new_transaction", headers=headers, data=json.dumps(tx))
        if response.status_code == 201:
            return jsonify({"message": "Transacción enviada exitosamente"}), 201
        else:
            return jsonify({"error": "No se pudo enviar la transacción", "details": response.text}), 400
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)

