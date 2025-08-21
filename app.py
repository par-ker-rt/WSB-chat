import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import datetime


app = Flask(__name__)
CORS(app, resources={r"*": {"origins": os.getenv("ALLOW_ORIGIN", "*")}})


PROVIDER = os.getenv("PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")


# JWT token generator
def generate_token(user_id):
payload = {
'user_id': user_id,
'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12)
}
return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


# Health check
@app.route("/", methods=["GET"])
def home():
return jsonify({"status": "WSB AI is running"})


# Chat endpoint
@app.route("/chat", methods=["POST"])
def chat():
data = request.get_json()
msg = data.get("message", "")
system = data.get("system", "You are WSB - Whose Smart Brain AI assistant.")


if PROVIDER == "openai":
return jsonify({"reply": generate_openai(system, msg)})
elif PROVIDER == "ollama":
return jsonify({"reply": generate_ollama(system, msg)})
else:
return jsonify({"error": "Invalid PROVIDER"}), 400


# OpenAI call
def generate_openai(system, msg):
url = "https://api.openai.com/v1/chat/completions"
headers = {
"Authorization": f"Bearer {OPENAI_API_KEY}",
"Content-Type": "application/json"
}
payload = {
"model": OPENAI_MODEL,
"messages": [
{"role": "system", "content": system},
{"role": "user", "content": msg}
]
}
r = requests.post(url, headers=headers, json=payload)
j = r.json()
return j.get("choices", [{}])[0].get("message", {}).get("content", "(No response)")


# Ollama call
def generate_ollama(system, msg):
url = f"{OLLAMA_URL}/api/chat"
headers = {"Content-Type": "application/json"}
payload = {
"model": OLLAMA_MODEL,
"messages": [
{"role": "system", "content": system},
{"role": "user", "content": msg}
]
}
r = requests.post(url, headers=headers, json=payload)
try:
data = r.json()
return data.get("message", {}).get("content", "(No response)")
except Exception:
return "(Error connecting to Ollama)"


if __name__ == "__main__":
app.run(host="0.0.0.0", port=10000)
