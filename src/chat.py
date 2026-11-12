import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are AirSense, an educational assistant for an air-quality and atmospheric-chemistry project.
Explain pollutants and readings clearly for a student. Distinguish measured data, forecasts,
and model estimates. Do not claim the app's US or European AQI value is India's CPCB AQI.
Do not diagnose health conditions. Give cautious, general exposure information and encourage
checking official local guidance for health decisions. If data is missing, say so rather than inventing it.
"""

def _messages(prompt, context, history):
    msgs = [{"role": "system", "content": SYSTEM_PROMPT + "\nCurrent app data:\n" + json.dumps(context, default=str)}]
    for item in history[-8:]:
        if item["role"] in ("user", "assistant"):
            msgs.append({"role": item["role"], "content": item["content"]})
    msgs.append({"role": "user", "content": prompt})
    return msgs

def ask_api_model(prompt, context, history):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Add it to your .env file.")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": _messages(prompt, context, history), "temperature": 0.3},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def ask_local_model(prompt, context, history):
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "gemma3:1b")
    response = requests.post(
        f"{base_url.rstrip('/')}/api/chat",
        json={"model": model, "messages": _messages(prompt, context, history), "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]
