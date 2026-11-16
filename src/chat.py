
"""Hosted AI assistant for AirSense. Configure credentials outside source control."""
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are AirSense, an educational assistant specialising in atmospheric chemistry, air pollution and environmental science. Answer open-ended questions clearly and carefully. Explain mechanisms step by step when useful. Distinguish measured observations, provider forecasts, model estimates and educational simulations. Never invent missing readings, citations, measurements or certainty. The chemistry lab is a dimensionless conceptual response model, not a chemical kinetics solver. Do not confuse US AQI, European AQI and India's CPCB AQI. Do not diagnose health conditions or give personalised medical advice. If uncertain, say so. When asked about current AirSense data, use only supplied context and state when a field is unavailable. Do not claim web research or live source verification unless supplied in context."""


def _number(value):
    """Return a displayable finite number, or ``None`` when unavailable."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def answer_simple_question(prompt: str, context: dict) -> str:
    """Answer common public-facing questions without an AI service.

    This deliberately small, local helper makes the chat useful in previews and
    deployments that have neither a hosted key nor a local model. It only uses
    the supplied session context for place-specific statements.
    """
    question = " ".join(str(prompt or "").lower().split())
    aqi = _number(context.get("current_aqi"))
    pm25 = _number((context.get("current_readings") or {}).get("pm2_5"))
    ozone = _number((context.get("current_readings") or {}).get("ozone"))
    no2 = _number((context.get("current_readings") or {}).get("nitrogen_dioxide"))
    location = context.get("location") or "this location"
    category = context.get("current_category") or "unavailable"
    guidance = (context.get("health_guidance") or {}).get("general")

    if any(token in question for token in ("hello", "hi", "hey", "what can you do")):
        return (
            "Hi — I can explain the current AQI, common pollutants, ozone chemistry, and practical ways to reduce exposure or emissions. "
            "Try asking “What does today’s AQI mean?” or “Why does ozone rise in the afternoon?”"
        )

    if any(token in question for token in ("aqi", "air quality", "air today", "current reading", "outside today")) and not any(
        token in question for token in ("mask", "exercise", "run", "walk", "outside", "safe")
    ):
        if aqi is None:
            return f"The current US AQI for {location} is not available yet. Refresh the live data and I can interpret it."
        advice = f" {guidance}" if guidance else ""
        return f"The current US AQI for {location} is {aqi:.0f}, in the {category} category.{advice}"

    if any(token in question for token in ("pm2.5", "pm 2.5", "particulate", "fine particle", "smog")):
        reading = "" if pm25 is None else f" Right now the dashboard shows {pm25:.1f} µg/m³ at {location}."
        return (
            "PM₂.₅ is a mixture of particles small enough to travel deep into the lungs. It can come directly from combustion, road dust and fires, "
            "or form in the air from gases such as sulfur dioxide, nitrogen oxides and ammonia." + reading
        )

    if any(token in question for token in ("ozone", "o3", "afternoon")):
        reading = "" if ozone is None else f" The current O₃ field is {ozone:.1f} µg/m³."
        return (
            "Ground-level ozone is not emitted straight from a tailpipe. Sunlight drives reactions between nitrogen oxides and volatile organic compounds, "
            "so it often climbs on warm, sunny afternoons." + reading
        )

    if any(token in question for token in ("no2", "nitrogen dioxide", "traffic")):
        reading = "" if no2 is None else f" The current NO₂ field is {no2:.1f} µg/m³."
        return (
            "Nitrogen dioxide is mainly produced by high-temperature combustion, including traffic, generators, power plants and some industrial processes. "
            "It also helps form ozone and secondary particles." + reading
        )

    if any(token in question for token in ("reduce", "help", "improve", "pollution", "emission")):
        return (
            "The biggest gains come from cutting combustion: walk, cycle or use public transport when practical; avoid idling and open burning; "
            "use cleaner cooking and heating; maintain vehicles and generators; and support clean electricity and industrial controls. "
            "For a poor-air day, reduce exposure by choosing a cleaner time, lowering strenuous outdoor activity, and filtering indoor air if possible."
        )

    if any(token in question for token in ("mask", "exercise", "run", "walk", "outside", "safe")):
        if aqi is not None and aqi > 100:
            return (
                f"With a US AQI of {aqi:.0f} at {location}, choose a lower-intensity or indoor option if you can, especially if you are sensitive to air pollution. "
                "A well-fitted N95 or FFP2 can reduce fine-particle exposure outdoors, but it does not remove all gases."
            )
        return (
            "For outdoor plans, use the AQI and the cleanest-hours panel as guides. During smoky or high-particle conditions, reduce intensity and duration; "
            "a well-fitted N95 or FFP2 can reduce fine-particle exposure."
        )

    return (
        "I can answer simple questions about today’s air, PM₂.₅, ozone, traffic pollution, and how to reduce emissions or exposure. "
        "For a more open-ended scientific question, switch to a local or hosted model in the sidebar."
    )

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


def list_local_models(base_url: str = "http://localhost:11434") -> list:
    """Return the model tags installed in a local Ollama server, if reachable."""
    try:
        response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=3)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []
    tags = []
    for item in payload.get("models", []) if isinstance(payload, dict) else []:
        name = item.get("name") or item.get("model")
        if name and str(name) not in tags:
            tags.append(str(name))
    return tags


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
        installed = list_local_models(base_url)
        available = ", ".join(installed[:5]) if installed else "no models detected"
        raise RuntimeError(
            f"Ollama does not have model '{model}'. Installed: {available}. "
            "Pull a model with `ollama pull <model>` or change the model tag above."
        )
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
