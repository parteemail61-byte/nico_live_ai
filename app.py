
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.get("/")
def home():
    return jsonify({
        "project": "Nico LIVE AI",
        "status": "online",
        "message": "Servidor do Nico está funcionando!"
    })

@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "project": "Nico LIVE AI"
    })

@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "Mensagem vazia"}), 400

    if len(message) > 1000:
        return jsonify({"error": "Mensagem muito longa"}), 400

    return jsonify({
        "received": True,
        "message": message,
        "reply": "Recebi sua mensagem! Estou preparando minha inteligência artificial."
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
