# 5470-blockchain-miner
:

### Guide to Use the Mining Code Linked to 5470 Blockchain


### 1. **Install Necessary Libraries**

Before running the mining code, ensure that you have the required Python libraries installed. You will need `requests` for HTTP requests and other Python dependencies for the blockchain.

Run the following command to install the necessary libraries:

```bash
pip install requests
```

If you haven't already installed `flask` (for your blockchain API), make sure it's installed as well:

```bash
pip install flask
```

### 2. **Set Up Your Blockchain Server**

Make sure your blockchain is running on your public IP (`2.137.118.154`) on port `5000`. If you have an API endpoint to add blocks (e.g., `/api/add_block`), make sure it's correctly set up in your blockchain code.

For example, a simple Flask server to add blocks might look like this:

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/add_block', methods=['POST'])
def add_block():
    block_data = request.json  # Receive the block in JSON format
    # Here you would add the block to your blockchain
    # For now, we just print it
    print(f"Block added: {block_data}")
    return jsonify({'message': 'Block added successfully!'}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)  # Allow connections from any IP
```

Make sure this server is running on the same machine where you're mining, or configure the server to allow connections from your mining machine.

### 3. **Configure the Miner Code**

1. **IP Address and Port Configuration**: Update the `BLOCKCHAIN_API_URL` in the miner code with your public IP and port number (`2.137.118.154:5000`).
   - The URL should look like this: `"http://2.137.118.154:5000/api"`

2. **Replace the Miner Address**: In the `reward_miner()` method, replace `"miner_address"` with the actual miner's address. If you don’t have one, you could generate an address or use a placeholder.

3. **Ensure Blockchain API Is Running**: Verify that the blockchain API is properly running and accessible from the mining machine. You can test this by visiting `http://2.137.118.154:5000/api/add_block` from a browser or using `curl`:

```bash
curl -X POST http://2.137.118.154:5000/api/add_block -H "Content-Type: application/json" -d '{"block_data": "example"}'
```

### 4. **Run the Miner**

Once you have the blockchain API set up and the miner code configured, you can start the miner script.

1. Open a terminal on the mining machine.
2. Navigate to the directory where your mining code is saved.
3. Run the mining script:

```bash
python3 miner_script.py  # Replace miner_script.py with your actual file name
```

The miner should begin mining blocks every `BLOCK_TIME` seconds (configured in the script). If a block is mined, it will send the block to the blockchain API at `http://2.137.118.154:5000/api/add_block`.

### 5. **Debugging and Logs**

If there are any issues or errors, check the logs output in the terminal where you're running the miner. The script uses `logging.info()` to print status messages, so make sure you're looking at the console for updates.

If the miner can't connect to the API, check:
- Firewall settings on your blockchain server.
- Ensure the IP address and port are correct.
- Confirm that the server is listening on `0.0.0.0` to accept connections from any IP.

### 6. **Optional: Run as Background Process**

To run the mining script continuously in the background (especially on a remote machine), you can use tools like `screen`, `tmux`, or simply run it with `nohup`.

For example, to run with `nohup`:

```bash
nohup python3 miner_script.py &
```

This command will run the script in the background and allow it to keep running even if the terminal is closed.

### Conclusion

By following these steps, your mining code will mine blocks and send them to your blockchain API running on your public IP and port. Make sure to monitor both the miner and blockchain server for any issues or logs to ensure everything is working smoothly.

Good luck with your blockchain project!
