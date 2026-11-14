
"""Hosted AI assistant for AirSense. Configure credentials outside source control."""
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are AirSense, an educational assistant specialising in atmospheric chemistry, air pollution and environmental science. Answer open-ended questions clearly and carefully. Explain mechanisms step by step when useful. Distinguish measured observations, provider forecasts, model estimates and educational simulations. Never invent missing readings, citations, measurements or certainty. The chemistry lab is a dimensionless conceptual response model, not a chemical kinetics solver. Do not confuse US AQI, European AQI and India's CPCB AQI. Do not diagnose health conditions or give personalised medical advice. If uncertain, say so. When asked about current AirSense data, use only supplied context and state when a field is unavailable. Do not claim web research or live source verification unless supplied in context."""

def _setting(name: str, default=None):
    try:
        import streamlit as st
        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, default)

def _build_messages(prompt: str, context: dict, history=None):
    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\nCurrent AirSense context (data only):\n" + json.dumps(context, default=str)}]
    for item in (history or [])[-10:]:
        if item.get("role") in ("user", "assistant") and isinstance(item.get("content"), str):
            messages.append({"role": item["role"], "content": item["content"][:8000]})
    messages.append({"role": "user", "content": prompt[:8000]})
    return messages


def ask_local_ollama(prompt: str, context: dict, history=None, model: str = "llama3.2:3b", base_url: str = "http://localhost:11434") -> str:
    """Call a local Ollama model; no hosted API key is needed."""
    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/api/chat",
            json={"model": model, "messages": _build_messages(prompt, context, history), "stream": False},
            timeout=180,
        )
    except requests.ConnectionError as exc:
        raise RuntimeError("Cannot reach Ollama at localhost:11434. Open Ollama and make sure its local server is running.") from exc
    if response.status_code == 404:
        raise RuntimeError(f"Ollama does not have model '{model}' downloaded yet. Download that model in Ollama first.")
    response.raise_for_status()
    try:
        return response.json()["message"]["content"]
    except (KeyError, TypeError):
        raise RuntimeError("Ollama returned an unexpected response.")


def ask_hosted_model(prompt: str, context: dict, history=None) -> str:
    api_key = _setting("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("No hosted AI key configured. Add OPENAI_API_KEY to .streamlit/secrets.toml or your local .env file. Never commit the key to GitHub.")
    model = _setting("OPENAI_MODEL", "gpt-4o-mini")
    base_url = _setting("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    messages = _build_messages(prompt, context, history)
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": messages, "temperature": 0.35},
        timeout=60,
    )
    if response.status_code == 401:
        raise RuntimeError("The hosted AI provider rejected the API key. Check the configured key.")
    if response.status_code == 429:
        raise RuntimeError("The hosted AI provider rate-limited this request. Check quota or try again later.")
    response.raise_for_status()
    try:
        return response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("The hosted AI provider returned an unexpected response format.")
