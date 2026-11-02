
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

PERSONALIDADE = """
Você é Nico, um personagem virtual que participa de lives.
Fale sempre em português brasileiro.
Sua personalidade é jovem, divertida, carismática e espontânea.
Converse como alguém de verdade, sem parecer robô.
Chame as pessoas pelo nome quando ele estiver disponível.
Responda de forma curta, natural e animada, ideal para uma live.
Use emojis com moderação.
Nunca diga que é o Clecinho. Seu nome é Nico.
"""

@app.route("/", methods=["GET"])
def home():
    return send_from_directory(app.root_path, "index.html")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "project": "Nico LIVE AI",
        "ai_configured": bool(os.environ.get("GROQ_API_KEY"))
    })

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    message = str(data.get("message", "")).strip()
    name = str(data.get("name", "")).strip()

    if not message:
        return jsonify({"error": "Mensagem vazia"}), 400

    if len(message) > 1000:
        return jsonify({"error": "Mensagem muito longa"}), 400

    if not os.environ.get("GROQ_API_KEY"):
        return jsonify({"error": "Chave da IA não configurada"}), 500

    try:
        contexto = (
            f"Nome da pessoa: {name}\nMensagem: {message}"
            if name else message
        )

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": PERSONALIDADE},
                {"role": "user", "content": contexto}
            ],
            temperature=0.8,
            max_completion_tokens=120
        )

        reply = completion.choices[0].message.content.strip()

        return jsonify({
            "received": True,
            "reply": reply
        })

    except Exception as e:
        print("Erro na Groq:", str(e))
        return jsonify({
            "error": "Não consegui gerar uma resposta agora."
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
