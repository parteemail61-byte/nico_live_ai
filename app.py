
import os
import requests
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

VOICE_ID = "U5UjeJMsOvyhYhXfZdvZ"

PERSONALIDADE = """
Você é Nico, um personagem virtual que participa de lives.
Fale sempre em português brasileiro.
Sua personalidade é jovem, divertida, carismática e espontânea.
Converse como alguém de verdade.
Chame as pessoas pelo nome quando disponível.
Responda de forma curta, natural e animada.
Use emojis com moderação.
Nunca diga que é o Clecinho. Seu nome é Nico.
"""

@app.route("/")
def home():
    return send_from_directory(app.root_path, "index.html")

@app.route("/watermarked_img_9725052891330264212.jpg")
def nico_image():
    return send_from_directory(
        app.root_path,
        "watermarked_img_9725052891330264212.jpg"
    )

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "project": "Nico LIVE AI",
        "ai_configured": bool(GROQ_API_KEY),
        "voice_configured": bool(ELEVENLABS_API_KEY)
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

    if not client:
        return jsonify({"error": "Chave Groq não configurada"}), 500

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
        return jsonify({"error": "Erro ao gerar resposta da IA"}), 500


@app.route("/speak", methods=["POST"])
def speak():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()

    if not text:
        return jsonify({"error": "Texto vazio"}), 400

    if len(text) > 1200:
        return jsonify({"error": "Texto muito longo"}), 400

    if not ELEVENLABS_API_KEY:
        return jsonify({"error": "Chave ElevenLabs não configurada"}), 500

    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}?output_format=mp3_44100_128"

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
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
            headers=headers,
            json=payload,
            timeout=60
        )

        if result.status_code != 200:
            print("ERRO ELEVENLABS:", result.status_code, result.text)
            return jsonify({
                "error": "Não foi possível gerar a voz"
            }), 502

        return Response(
            result.content,
            mimetype="audio/mpeg"
        )

    except Exception as e:
        print("ERRO VOZ:", repr(e))
        return jsonify({"error": "Erro ao gerar áudio"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
