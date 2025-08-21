import os
import requests
import jwt
import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

APP = Flask(__name__)
CORS(APP)

# Config
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
PROVIDER = os.getenv("PROVIDER", "openai")  # openai | ollama
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Limiter
limiter = Limiter(get_remote_address, app=APP, default_limits=[])

# Roles & limits
ROLE_LIMITS = {
    "free": "40 per day",
    "pro": "500 per day",
    "admin": None  # unlimited
}


def get_role_from_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("role", "free")
    except Exception:
        return "free"


def generate_token(role="free"):
    payload = {
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def chat_openai(msg, system="You are WSB AI."):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_KEY}"}
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": msg}
        ]
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    j = r.json()
    return j["choices"][0]["message"]["content"]


def chat_ollama(msg, system="You are WSB AI."):
    url = f"{OLLAMA_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": msg}
        ]
    }
    r = requests.post(url, json=payload, timeout=60)
    j = r.json()
    return j["message"]["content"] if "message" in j else j


@APP.route("/")
def index():
    return render_template("index.html")


@APP.route("/token", methods=["POST"])
def issue_token():
    data = request.json
    role = data.get("role", "free")
    token = generate_token(role)
    return jsonify({"token": token})


@APP.route("/chat", methods=["POST"])
def chat():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    role = get_role_from_token(token)

    # Apply limit
    if role != "admin":
        limit = ROLE_LIMITS.get(role, "40 per day")
        limiter.limit(limit)(chat)(request)

    data = request.json
    msg = data.get("message", "")

    try:
        if PROVIDER == "openai":
            reply = chat_openai(msg)
        else:
            reply = chat_ollama(msg)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@APP.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    APP.run(host="0.0.0.0", port=5000)
