
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

VOICE_NAME = "Android - voz do celular"

@app.route("/")
def home():
    return send_file("index.html")

@app.route("/watermarked_img_9725052891330264212.jpg")
def avatar():
    return send_file("watermarked_img_9725052891330264212.jpg")

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "project": "Nico LIVE AI",
        "ai_configured": bool(GROQ_API_KEY),
        "voice": VOICE_NAME,
        "voice_configured": True
    })

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = data.get("message", "").strip()

        if not message:
            return jsonify({"error": "Mensagem vazia"}), 400

        if not groq_client:
            return jsonify({"error": "IA não configurada"}), 500

        result = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Seu nome é Nico. Você é um rapaz jovem, "
                        "simpático, divertido e espontâneo. "
                        "Fala português brasileiro natural. "
                        "Responde de forma curta, como numa LIVE. "
                        "Chama as pessoas pelo nome quando disponível. "
                        "Não diga que é um robô."
                    )
                },
                {"role": "user", "content": message}
            ],
            temperature=0.8,
            max_tokens=180
        )

        reply = result.choices[0].message.content.strip()
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    
