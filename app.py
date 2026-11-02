
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

PERSONALIDADE = """
Você é Nico, um personagem virtual que participa de lives.
Fale sempre em português brasileiro.
Você é jovem, divertido, carismático e espontâneo.
Converse como uma pessoa de verdade.
Chame os espectadores pelo nome quando disponível.
Responda de forma curta, natural e animada.
Use emojis com moderação.
Nunca diga que é o Clecinho. Seu nome é Nico.
"""

@app.route("/", methods=["GET"])
def home():
    return send_from_directory(app.root_path, "index.html")


@app.route("/watermarked_img_9725052891330264212.jpg")
def nico_image():
    return send_from_directory(
        app.root_path,
        "watermarked_img_9725052891330264212.jpg"
    )


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
            f"Nome do espectador: {name}\nMensagem: {message}"
            if name else message
        )

        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": PERSONALIDADE},
                {"role": "user", "content": contexto}
            ],
            temperature=0.7,
            max_completion_tokens=300
        )

        reply = completion.choices[0].message.content.strip()

        return jsonify({
            "received": True,
            "reply": reply
        })

    except Exception as e:
        print("ERRO GROQ:", repr(e))

        return jsonify({
            "error": "A IA não conseguiu responder. Verifique os logs do servidor."
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
