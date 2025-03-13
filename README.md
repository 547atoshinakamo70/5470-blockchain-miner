# 5470-blockchain-miner
:

### Guide to Use the Mining Code Linked to 5470 Blockchain

#### 1. **Pre-requisites**

Before starting, make sure you have the following components installed:

- **Python 3.x**: You can verify the installed version by running:
  ```bash
  python3 --version
  ```

- **Required packages**: Ensure that the necessary packages are installed in your Python environment. If they are not installed, use the following command to install them:
  ```bash
  pip install flask requests ecdsa hashlib psycopg2 pika tensorflow python-dotenv
  ```

- **Blockchain Running**: You need to have your blockchain running on a server (local or remote) that is accessible from the mining terminal. This server should have the correct endpoints set up to interact with the miners.

#### 2. **Set up Your Blockchain Server**

Make sure your blockchain is running and that the endpoints are set up correctly. The main endpoints you'll need are:

- **/chain**: To get the blockchain.
- **/pending_transactions**: To get pending transactions.
- **/propose_block**: To propose new blocks.
- **/new_transaction**: To send new transactions.

Your blockchain URL might look like `http://localhost:5000` if it's on the same machine, or a remote IP address like `http://172.21.50.114:5000`.

#### 3. **Set Up Environment Variables**

You can use a `.env` file to set up the environment variables and keep them separate from the source code. Create a `.env` file in the root of your project with the following content:

```env
BLOCKCHAIN_SERVER_URL=http://localhost:5000
```

This file contains the URL of the blockchain server that your mining code will connect to. You can change this URL if your blockchain is hosted elsewhere.

#### 4. **Miner Code (Miner.py)**

Here’s an example of the mining code that interacts with your blockchain:

```python
from flask import Flask, request, jsonify
import requests
import json
import time
import ecdsa
import hashlib
import os

app = Flask(__name__)

# Blockchain server configuration
BLOCKCHAIN_SERVER_URL = os.getenv("BLOCKCHAIN_SERVER_URL", "http://localhost:5000")

# Function to generate keys for the miner
def generate_miner_keys():
    private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    public_key = private_key.get_verifying_key()
    public_key_bytes = public_key.to_string()
    address = hashlib.sha256(public_key_bytes).hexdigest()
    return private_key.to_string().hex(), public_key.to_string().hex(), address

# Endpoint to register a new miner
@app.route('/register', methods=['POST'])
def register():
    private_key, public_key, address = generate_miner_keys()
    return jsonify({
        "private_key": private_key,
        "public_key": public_key,
        "address": address
    }), 201

# Endpoint to mine a block
@app.route('/mine', methods=['POST'])
def mine():
    data = request.get_json()
    miner_address = data.get("miner_address")
    if not miner_address:
        return jsonify({"error": "Miner address is required"}), 400

    try:
        # Get the last block
        response = requests.get(f"{BLOCKCHAIN_SERVER_URL}/chain")
        if response.status_code != 200:
            return jsonify({"error": "Could not retrieve the chain"}), 500
        chain = response.json()["chain"]
        last_block = chain[-1]
        index = last_block["index"] + 1
        previous_hash = last_block["hash"]

        # Get pending transactions
        response = requests.get(f"{BLOCKCHAIN_SERVER_URL}/pending_transactions")
        if response.status_code != 200:
            return jsonify({"error": "Could not retrieve pending transactions"}), 500
        transactions = response.json()

        # Add miner's reward transaction
        reward_tx = {
            "sender": "system",
            "receiver": miner_address,
            "amount": 50,  # Adjust the reward based on your system
            "signature": None
        }
        transactions.append(reward_tx)

        # Create the block
        block = {
            "index": index,
            "transactions": transactions,
            "timestamp": time.time(),
            "previous_hash": previous_hash,
            "nonce": 0  # Adjust based on your consensus algorithm
        }

        # Propose the block to the blockchain server
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{BLOCKCHAIN_SERVER_URL}/propose_block", headers=headers, data=json.dumps(block))
        if response.status_code == 201:
            return jsonify({"message": "Block proposed successfully"}), 201
        else:
            return jsonify({"error": "Could not propose block", "details": response.text}), 400
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

# Endpoint to send tokens (basic example)
@app.route('/send', methods=['POST'])
def send_tokens():
    data = request.get_json()
    sender_address = data.get("sender_address")
    receiver_address = data.get("receiver_address")
    amount = data.get("amount")
    private_key = data.get("private_key")  # Private key must come from the client

    if not all([sender_address, receiver_address, amount, private_key]):
        return jsonify({"error": "Missing required data"}), 400

    # Create the transaction
    tx = {
        "sender": sender_address,
        "receiver": receiver_address,
        "amount": amount,
        "signature": None  # Pending signature (see below)
    }

    # Sign the transaction (simplified)
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
    tx_string = json.dumps(tx, sort_keys=True).encode()
    signature = sk.sign(tx_string).hex()
    tx["signature"] = signature

    # Send the transaction to the blockchain server
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{BLOCKCHAIN_SERVER_URL}/new_transaction", headers=headers, data=json.dumps(tx))
        if response.status_code == 201:
            return jsonify({"message": "Transaction sent successfully"}), 201
        else:
            return jsonify({"error": "Could not send transaction", "details": response.text}), 400
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
```

#### 5. **Run Your Miner**

1. **Set up the `BLOCKCHAIN_SERVER_URL` environment variable**:
   If you're not using `.env`, make sure the blockchain URL is correctly defined in the code. Ensure that your blockchain is running on the URL you provided (`http://localhost:5000` by default).

2. **Run the Flask server for the miner**:
   Run the file using the following command:
   ```bash
   python3 miner.py
   ```

   This will start your miner on port `5001` on your machine.

#### 6. **Start Mining**

- To register a new miner, you can make a `POST` request to `http://localhost:5001/register`.
- To mine a block, make a `POST` request to `http://localhost:5001/mine` with the `miner_address` in the request body.

Example of a `POST` request to `/mine`:

```json
{
  "miner_address": "your_miner_address_here"
}
```

#### 7. **Verification**

You can verify that blocks are being mined correctly by visiting the `/chain` endpoint on your blockchain.

---

### Summary

1. Set up the environment variables and the blockchain server.
2. Run the miner using Flask on port `5001`.
3. Use the `/register` endpoint to register a miner and `/mine` to mine blocks.
4. The mining server will interact with your blockchain locally, validating transactions and mining blocks.
