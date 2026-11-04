import os
import asyncio
import tempfile
import threading
from io import BytesIO
from collections import deque

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from groq import Groq
import edge_tts

from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, GiftEvent, ConnectEvent, DisconnectEvent

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ai_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

VOICE = "pt-BR-AntonioNeural"
TIKTOK_USERNAME = ""
live_client = None
live_thread = None
live_status = "desconectado"
live_error = ""

live_events = deque(maxlen=300)
event_id = 0
events_lock = threading.Lock()
client_lock = threading.Lock()


def add_live_event(username, message, event_type="comment", extra=None):
    global event_id
    with events_lock:
        event_id += 1
        item = {
            "id": event_id,
            "username": username or "Visitante",
            "message": message,
            "type": event_type
        }
        if extra:
            item.update(extra)
        live_events.append(item)


@app.route("/")
def home():
    path = os.path.join(app.root_path, "index.html")
    if os.path.exists(path):
        return send_file(path)
    return jsonify({"project": "Clecinho LIVE AI", "status": "online"})


@app.route("/avatar")
def avatar():
    path = os.path.join(app.root_path, "watermarked_img_9725052891330264212.jpg")
    if not os.path.exists(path):
        return jsonify({"error": "Arquivo de avatar não encontrado."}), 404
    return send_file(path)


@app.route("/scene1")
def scene1():
    path = os.path.join(app.root_path, "nico_cena1.mp4")
    if not os.path.exists(path):
        return jsonify({"error": "Vídeo da cena 1 não encontrado."}), 404
    return send_file(path, mimetype="video/mp4")


@app.route("/scene2")
def scene2():
    path = os.path.join(app.root_path, "nico_cena2.mp4")
    if not os.path.exists(path):
        return jsonify({"error": "Vídeo da cena 2 não encontrado."}), 404
    return send_file(path, mimetype="video/mp4")


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "project": "Clecinho LIVE AI",
        "ai_configured": ai_client is not None,
        "voice_configured": True,
        "tiktok_status": live_status
    })


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).strip()
        username = str(data.get("username", "visitante")).strip() or "visitante"

        if not message:
            return jsonify({"error": "Digite uma mensagem."}), 400

        if ai_client is None:
            return jsonify({"error": "Chave GROQ_API_KEY não configurada."}), 500

        result = ai_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é o personagem virtual da LIVE do Clecinho. "
                        "Fale português brasileiro natural, com carisma e bom humor. "
                        "Responda de forma curta, espontânea e respeitosa. "
                        "Chame a pessoa pelo nome quando disponível. "
                        "Se a mensagem mencionar presente, agradeça e cite o presente "
                        "e a quantidade quando informados. Não invente presentes ou valores."
                    )
                },
                {"role": "user", "content": f"Mensagem de {username}: {message}"}
            ],
            temperature=0.8,
            max_tokens=180
        )

        return jsonify({"reply": result.choices[0].message.content.strip()})

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
                message, VOICE, rate="+5%", pitch="-2Hz"
            )

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp:
                path = temp.name

            try:
                await communication.save(path)
                with open(path, "rb") as audio_file:
                    return audio_file.read()
            finally:
                if os.path.exists(path):
                    os.remove(path)

        audio_data = asyncio.run(generate_audio())

        return send_file(
            BytesIO(audio_data),
            mimetype="audio/mpeg",
            download_name="clecinho.mp3"
        )

    except Exception as error:
        return jsonify({"error": "Não consegui gerar a voz: " + str(error)}), 500


def run_tiktok(username):
    global live_client, live_status, live_error

    try:
        client = TikTokLiveClient(unique_id=username)
        live_client = client

        @client.on(ConnectEvent)
        async def on_connect(event):
            global live_status, live_error
            live_status = "conectado"
            live_error = ""

        @client.on(DisconnectEvent)
        async def on_disconnect(event):
            global live_status
            live_status = "desconectado"

        @client.on(CommentEvent)
        async def on_comment(event):
            user = (
                getattr(event.user, "nickname", None)
                or getattr(event.user, "unique_id", "Visitante")
            )
            add_live_event(user, str(event.comment), "comment")

        @client.on(GiftEvent)
        async def on_gift(event):
            gift = getattr(event, "gift", None)

            if gift is None:
                return

            if getattr(event, "streaking", False):
                return

            user = (
                getattr(event.user, "nickname", None)
                or getattr(event.user, "unique_id", "Visitante")
            )

            gift_name = getattr(gift, "name", None) or "presente"
            quantity = int(getattr(event, "repeat_count", 1) or 1)

            message = (
                f"🎁 enviou {quantity}x o presente {gift_name}. "
                "Agradeça pelo presente!"
            )

            add_live_event(
                user,
                message,
                "gift",
                {"gift_name": str(gift_name), "quantity": quantity}
            )

        live_status = "conectando"
        client.run()

        if live_status == "conectado":
            live_status = "desconectado"

    except Exception as error:
        live_status = "erro"
        live_error = str(error)


@app.route("/tiktok/start", methods=["POST"])
def tiktok_start():
    global live_thread, live_status, live_error, TIKTOK_USERNAME

    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip().lstrip("@")

    if not username:
        username = TIKTOK_USERNAME

    if not username:
        return jsonify({
            "status": "erro",
            "error": "Informe o @ do perfil do TikTok."
        }), 400

    with client_lock:
        if live_thread and live_thread.is_alive():

            if username.lower() != TIKTOK_USERNAME.lower():
                return jsonify({
                    "status": live_status,
                    "error": (
                        "Já existe uma conexão ativa com outro perfil. "
                        "Reinicie o serviço para trocar."
                    )
                }), 409

            return jsonify({
                "status": live_status,
                "username": TIKTOK_USERNAME,
                "message": "A conexão já foi iniciada."
            })

        TIKTOK_USERNAME = username
        live_error = ""
        live_status = "iniciando"

        live_thread = threading.Thread(
            target=run_tiktok,
            args=(username,),
            daemon=True
        )

        live_thread.start()

    return jsonify({
        "status": "iniciando",
        "username": TIKTOK_USERNAME,
        "message": "Tentando conectar ao TikTok."
    })


@app.route("/tiktok/status")
def tiktok_status():
    return jsonify({
        "status": live_status,
        "username": TIKTOK_USERNAME,
        "connected": live_status == "conectado",
        "error": live_error
    })


@app.route("/tiktok/events")
def tiktok_events():
    try:
        last_id = int(request.args.get("since", 0))
    except (TypeError, ValueError):
        last_id = 0

    with events_lock:
        new_events = [
            item for item in live_events
            if item["id"] > last_id
        ]

    return jsonify({
        "comments": new_events,
        "events": new_events,
        "last_id": new_events[-1]["id"] if new_events else last_id
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000"))
    )
