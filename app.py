
import os
import asyncio
import tempfile
from io import BytesIO

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from groq import Groq
import edge_tts

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

NICO_VOICE = "pt-BR-AntonioNeural"


@app.route("/")
def home():
    return send_file("index.html")


@app.route("/avatar")
def avatar():
    return send_file("watermarked_img_9725052891330264212.jpg")


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "project": "Nico LIVE AI",
        "ai_configured": client is not None,
        "voice": "Antonio Neural",
        "voice_configured": True
    })


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).strip()
        username = str(data.get("username", "visitante")).strip()

        if not message:
            return jsonify({"error": "Digite uma mensagem."}), 400

        if client is None:
            return jsonify({
                "error": "Chave GROQ_API_KEY não configurada."
            }), 500

        result = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Seu nome é Nico. Você é um rapaz jovem, "
                        "divertido, carismático e espontâneo. "
                        "Fale português brasileiro natural. "
                        "Você está numa LIVE e conversa com o público. "
                        "Responda de forma curta, animada e natural. "
                        "Chame a pessoa pelo nome quando disponível. "
                        "Não diga que é um robô ou assistente virtual."
                    )
                },
                {
                    "role": "user",
                    "content": f"Mensagem de {username}: {message}"
                }
            ],
            temperature=0.8,
            max_tokens=180
        )

        reply = result.choices[0].message.content.strip()
        return jsonify({"reply": reply})

    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route("/speak", methods=["POST"])
def speak():
    try:
        data = request.get_json(silent=True) or {}
        message = str(data.get("text", "")).strip()

        if not message:
            return jsonify({"error": "Texto vazio."}), 400

        if len(message) > 1500:
            return jsonify({"error": "Texto muito longo."}), 400

        async def generate_audio():
            communication = edge_tts.Communicate(
                message,
                NICO_VOICE,
                rate="+5%",
                pitch="-2Hz"
            )

            with tempfile.NamedTemporaryFile(
                suffix=".mp3", delete=False
            ) as temp:
                path = temp.name

            try:
                await communication.save(path)

                with open(path, "rb") as audio_file:
                    audio_data = audio_file.read()

                return audio_data
            finally:
                if os.path.exists(path):
                    os.remove(path)

        audio_data = asyncio.run(generate_audio())

        return send_file(
            BytesIO(audio_data),
            mimetype="audio/mpeg",
            download_name="nico.mp3"
        )

    except Exception as error:
        return jsonify({
            "error": "Não consegui gerar a voz: " + str(error)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
