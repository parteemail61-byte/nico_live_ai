
import os
import requests
from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Voz Adam
VOICE_ID = "U5UjeJMsOvyhYhXfZdvZ"

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


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
        "voice_configured": bool(ELEVENLABS_API_KEY),
        "voice": VOICE_ID
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
                        "Conversa em português brasileiro natural. "
                        "Responde de forma curta, como numa LIVE. "
                        "Interage com as pessoas e chama cada uma pelo nome "
                        "quando ele estiver disponível."
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


@app.route("/speak", methods=["POST"])
def speak():
    try:
        data = request.get_json(silent=True) or {}
        text = data.get("text", "").strip()

        if not text:
            return jsonify({"error": "Texto vazio"}), 400

        if not ELEVENLABS_API_KEY:
            return jsonify({
                "error": "Chave do ElevenLabs não configurada"
            }), 500

        url = (
            f"https://api.elevenlabs.io/v1/text-to-speech/"
            f"{VOICE_ID}?output_format=mp3_44100_128"
        )

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.80,
                "style": 0.15,
                "use_speaker_boost": True
            }
        }

        result = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=60
        )

        if result.status_code != 200:
            return jsonify({
                "error": "Erro no ElevenLabs",
                "details": result.text
            }), result.status_code

        return Response(
            result.content,
            mimetype="audio/mpeg"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
