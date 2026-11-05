
from flask import Flask, jsonify, request
from flask_cors import CORS
from collections import deque
from threading import Lock
import time

app = Flask(__name__)
CORS(app)

events = deque(maxlen=500)
lock = Lock()
last_id = 0
status = {
    "connected": False,
    "message": "Backend Ninja ativo. Aguardando integração autorizada."
}

@app.get("/")
def home():
    return jsonify({
        "name": "Ninja Backend",
        "status": "online",
        "version": "1.0"
    })

@app.get("/health")
def health():
    return jsonify({"ok": True, "time": time.time()})

@app.post("/tiktok/start")
def start():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip().lstrip("@")

    if not username:
        return jsonify({"error": "Informe o usuário"}), 400

    status["connected"] = False
    status["message"] = (
        "Backend ativo. A leitura de eventos do TikTok "
        "precisa de integração autorizada."
    )

    return jsonify(status)

@app.get("/tiktok/status")
def get_status():
    return jsonify(status)

@app.get("/tiktok/events")
def get_events():
    try:
        since = int(request.args.get("since", 0))
    except ValueError:
        since = 0

    with lock:
        result = [event for event in events if event["id"] > since]

    return jsonify({"events": result})

# Endpoint para testes locais de eventos.
# Não representa conexão real com o TikTok.
@app.post("/test/event")
def test_event():
    global last_id

    data = request.get_json(silent=True) or {}
    event_type = data.get("type")

    if event_type not in ("gift", "comment", "like"):
        return jsonify({"error": "Tipo inválido"}), 400

    with lock:
        last_id += 1
        event = {
            "id": last_id,
            "type": event_type,
            "gift_id": data.get("gift_id"),
            "gift_name": data.get("gift_name", ""),
            "username": data.get("username", "Teste"),
            "created_at": time.time()
        }
        events.append(event)

    return jsonify({"ok": True, "event": event})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
