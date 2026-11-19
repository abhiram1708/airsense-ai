"""AirSense assistant.

Two layers:
  * a grounded, offline answer engine with a small air-quality knowledge base
    (works with no key, no model download, no network), and
  * optional hosted / local LLM calls that receive the same live context.
"""

import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are AirSense, a calm, precise guide to air quality and atmospheric chemistry.
You are talking to a curious member of the public, not an examiner: write short paragraphs, plain words, concrete numbers.
Rules:
- Ground every statement about the current place in the supplied context. Never invent readings, dates, sources or citations.
- If a field is missing, say it is missing instead of guessing.
- Distinguish measured values, model forecasts and the chemistry lab's conceptual simulation.
- Do not mix US AQI, European AQI and India's CPCB AQI.
- Do not diagnose or give personalised medical advice; encourage a clinician for personal health decisions.
- Prefer 60-140 words unless the question genuinely needs more. No bullet-point walls, no markdown tables."""


def _number(value):
    """Return a finite float, or None when the value is missing."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result else None


def _reading(context, key):
    return _number((context.get("current_readings") or {}).get(key))


def _place(context):
    name = context.get("location") or "this location"
    country = context.get("country")
    return f"{name}, {country}" if country and country != name else name


def _city(context):
    return context.get("location") or "this city"


def _ordinal(value):
    number = int(round(float(value)))
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def _current_line(context):
    aqi = _number(context.get("current_aqi"))
    if aqi is None:
        return f"I do not have a live AQI for {_place(context)} right now."
    category = context.get("current_category") or "unclassified"
    dominant = context.get("dominant_pollutant")
    extra = f" The pollutant furthest above its WHO reference is {dominant}." if dominant else ""
    return f"The US AQI for {_place(context)} is {aqi:.0f} — {category}.{extra}"


def _fmt(value, unit="µg/m³"):
    number = _number(value)
    if number is None:
        return None
    return f"{number:.1f}".rstrip("0").rstrip(".") + f" {unit}"


def _with_reading(context, key, unit="µg/m³", prefix=" Right now", verb="it reads"):
    value = _fmt(_reading(context, key), unit)
    return f"{prefix} {verb} {value} at {_place(context)}." if value else ""


def _aqi_advice(aqi):
    if aqi is None:
        return ""
    if aqi <= 50:
        return "That is a clean reading — ordinary outdoor plans are fine for most people."
    if aqi <= 100:
        return "It is acceptable for most people, though unusually sensitive individuals may notice mild effects during long or hard outdoor effort."
    if aqi <= 150:
        return "Sensitive groups — asthma, heart or lung conditions, children, older adults — should ease off prolonged or intense outdoor exertion."
    if aqi <= 200:
        return "Everyone should reduce long or strenuous outdoor effort, and sensitive groups should keep it short or move indoors."
    return "Treat this as a stay-in day where possible: keep windows shut, filter indoor air if you can, and avoid outdoor exercise."


def _forecast_answer(context):
    forecast = context.get("forecast") or {}
    place = _place(context)
    peak = _number(forecast.get("next_24h_peak_aqi"))
    peak_time = forecast.get("next_24h_peak_time")
    window = forecast.get("cleanest_window_next_12h")
    window_aqi = _number(forecast.get("cleanest_window_aqi"))
    tomorrow = _number(forecast.get("tomorrow_peak_aqi"))
    if peak is None and tomorrow is None and not window:
        return f"I do not have a forward forecast for {place} right now."

    parts = []
    if peak is not None:
        timing = f" around {peak_time} local" if peak_time else ""
        parts.append(f"Over the next 24 hours the model peaks at {peak:.0f}{timing}.")
    if window:
        about = f", around AQI {window_aqi:.0f}" if window_aqi is not None else ""
        parts.append(f"The cleanest three-hour stretch is {window}{about}.")
    if tomorrow is not None and (peak is None or abs(tomorrow - peak) >= 2):
        parts.append(f"Tomorrow's peak is forecast at {tomorrow:.0f}.")
    change_24 = _number((context.get("history") or {}).get("change_24h_percent"))
    if change_24 is not None:
        if abs(change_24) < 5:
            parts.append("For context, the last 24 hours were broadly steady against the day before.")
        else:
            direction = "above" if change_24 > 0 else "below"
            parts.append(f"For context, the last 24 hours averaged {abs(change_24):.0f}% {direction} the day before.")
    parts.append("Forecasts are model guidance rather than promises, so re-check before a hard outdoor session.")
    return " ".join(parts)


def _ranking_answer(context):
    rankings = context.get("rankings") or {}
    place = _place(context)
    india_pos = _number(rankings.get("india_position"))
    india_total = _number(rankings.get("india_total"))
    world_pos = _number(rankings.get("world_position"))
    world_total = _number(rankings.get("world_total"))
    india_cleanest = rankings.get("india_cleanest")
    india_dirtiest = rankings.get("india_dirtiest")
    world_cleanest = rankings.get("world_cleanest")
    world_dirtiest = rankings.get("world_dirtiest")

    if india_pos is None and world_pos is None:
        return "The comparison boards are not available for this place right now."

    parts = []
    city_name = _city(context)
    if india_pos and india_total:
        parts.append(f"In the live Indian board, {city_name} ranks {_ordinal(india_pos)} cleanest of {int(india_total)} cities.")
    if world_pos and world_total:
        parts.append(f"Across the world board it is {_ordinal(world_pos)} cleanest of {int(world_total)} cities.")
    if india_pos and india_cleanest and india_dirtiest:
        parts.append(f"Today's cleanest Indian city in the set is {india_cleanest}; the highest reading is {india_dirtiest}.")
    elif world_pos and world_cleanest and world_dirtiest:
        parts.append(f"Today's cleanest city in the world board is {world_cleanest}; the highest is {world_dirtiest}.")
    parts.append("All boards use the same hour of model data, so they are directly comparable but still estimates.")
    return " ".join(parts)


def _history_answer(context):
    history = context.get("history") or {}
    place = _place(context)
    mean = _number(history.get("last_24h_mean"))
    change_24 = _number(history.get("change_24h_percent"))
    change_7 = _number(history.get("change_7d_percent"))
    change_30 = _number(history.get("change_30d_percent"))
    if mean is None and change_24 is None and change_7 is None:
        return f"I do not have historical reanalysis for {place} right now."

    parts = []
    if mean is not None:
        parts.append(f"Over the past 24 hours {place} averaged US AQI {mean:.0f}.")
    if change_24 is not None:
        direction = "higher" if change_24 > 0 else "lower" if change_24 < 0 else "unchanged"
        parts.append(f"That is {abs(change_24):.0f}% {direction} than the previous day." if change_24 else "That is essentially unchanged from the previous day.")
    if change_7 is not None:
        direction = "above" if change_7 > 0 else "below"
        parts.append(f"Against the previous week it is {abs(change_7):.0f}% {direction}.")
    if change_30 is not None:
        direction = "above" if change_30 > 0 else "below"
        parts.append(f"Against the previous month it is {abs(change_30):.0f}% {direction}.")
    parts.append("These are reanalysis estimates for this point, useful for pattern-finding rather than regulatory reporting.")
    return " ".join(parts)


def _window_hint(context):
    forecast = context.get("forecast") or {}
    window = forecast.get("cleanest_window_next_12h")
    window_aqi = _number(forecast.get("cleanest_window_aqi"))
    if not window:
        return ""
    about = f" (about AQI {window_aqi:.0f})" if window_aqi is not None else ""
    return f" If you can choose, the cleanest stretch in the next twelve hours is {window}{about}."


# ---------------------------------------------------------------------------
# Knowledge base
# ---------------------------------------------------------------------------

TOPICS = [
    {
        "id": "forecast",
        "keys": ["tomorrow", "forecast", "next few days", "best time", "best window", "cleanest time", "when is", "what time", "good time", "when should", "later today", "this afternoon", "this evening", "plan ahead", "get better", "clear up"],
        "answer": lambda c: _forecast_answer(c),
    },
    {
        "id": "ranking",
        "keys": ["rank", "ranking", "compare", "cleanest city", "dirtiest", "other cities", "around the world", "how does", "better than"],
        "answer": lambda c: _ranking_answer(c),
    },
    {
        "id": "history",
        "keys": ["trend", "last week", "past week", "history", "historical", "last 24 hours", "been rising", "getting worse", "over the past", "yesterday"],
        "answer": lambda c: _history_answer(c),
    },
    {
        "id": "greeting",
        "keys": ["hello", "hi ", "hey", "good morning", "good evening", "who are you", "what can you do", "help me"],
        "answer": lambda c: (
            f"Hello. I am sitting on the live reading for {_place(c)} — {_current_line(c).split('— ')[-1] if _number(c.get('current_aqi')) is not None else 'no reading yet'}. "
            "Ask me what the number means, why a pollutant is high, whether it is a good time to run, or how the chemistry lab works."
        ),
    },
    {
        "id": "aqi_now",
        "keys": ["my aqi", "the aqi", "air quality", "current reading", "how is the air", "air today", "reading mean", "aqi mean", "number mean", "outside right now"],
        "answer": lambda c: f"{_current_line(c)} {_aqi_advice(_number(c.get('current_aqi')))} "
        "The index is a communication scale, not a measurement of one gas: it is set by whichever pollutant is highest after its own breakpoints are applied.",
    },
    {
        "id": "aqi_scale",
        "keys": ["us aqi", "european aqi", "india aqi", "cpcb", "difference between aqi", "which aqi", "aqi scale", "scale work", "breakpoint"],
        "answer": lambda c: "There is no single world AQI. The US EPA scale runs 0–500 in six colour bands and is anchored on PM₂.₅ breakpoints; the European AQI uses a different index and band names; India's CPCB index uses its own sub-indices and categories. "
        "AirSense uses the US scale throughout, and compares concentrations against WHO 2021 guidelines separately — so a reading can be 'Moderate' on the US scale and still several times the WHO reference.",
    },
    {
        "id": "pm25",
        "keys": ["pm2.5", "pm 2.5", "pm₂.₅", "fine particle", "particulate", "soot"],
        "answer": lambda c: "PM₂.₅ is everything airborne smaller than 2.5 micrometres — combustion soot, road dust, sea salt, metals and organic compounds. It is a mixture, not a molecule, which is why no single structure describes it. "
        "Those particles travel deep into the lungs and into the bloodstream, and they are the pollutant most consistently linked with health effects."
        + _with_reading(c, "pm2_5")
        + " It comes both from direct emission and from gases like SO₂, NOₓ and ammonia reacting in the air.",
    },
    {
        "id": "pm10",
        "keys": ["pm10", "pm 10", "pm₁₀", "coarse", "dust"],
        "answer": lambda c: "PM₁₀ covers particles up to 10 micrometres: dust from roads and construction, pollen fragments, and mechanically generated debris. They mostly deposit in the upper airways, so they matter less for deep-lung exposure than PM₂.₅ but still irritate eyes, nose and throat."
        + _with_reading(c, "pm10")
        + " On a dry, windy day, dust can push PM₁₀ up while PM₂.₅ stays flat.",
    },
    {
        "id": "ozone",
        "keys": ["ozone", "o3", "o₃", "afternoon", "photochemical", "smog"],
        "answer": lambda c: "Ground-level ozone is made, not emitted. Sunlight splits NO₂ into NO and an oxygen atom; that atom joins O₂ to form O₃. VOCs keep NO from consuming the ozone again, so it accumulates through the afternoon and peaks in the early evening."
        + _with_reading(c, "ozone")
        + " That is why ozone is a warm, sunny, downwind problem — and why it can be high in a place with little traffic.",
    },
    {
        "id": "no2",
        "keys": ["no2", "no₂", "nitrogen dioxide", "traffic", "diesel", "vehicle"],
        "answer": lambda c: "NO₂ is the signature of high-temperature combustion — engines, generators, gas burners, power plants. It is a sharp traffic marker because it is short-lived and stays near its source."
        + _with_reading(c, "nitrogen_dioxide")
        + " It also feeds ozone and nitrate particles, so cutting NOₓ helps twice.",
    },
    {
        "id": "so2",
        "keys": ["so2", "so₂", "sulphur", "sulfur", "coal", "smelting"],
        "answer": lambda c: "SO₂ comes mostly from burning sulphur-containing coal and oil, plus metal smelting. It irritates the airways directly and oxidises into sulphate particles, which is the link to acid rain and to hazy regional sulphate plumes."
        + _with_reading(c, "sulphur_dioxide")
        + " Low-sulphur fuel and flue-gas desulphurisation are the two big levers.",
    },
    {
        "id": "co",
        "keys": ["carbon monoxide", " co ", "co level", "incomplete combustion", "generator"],
        "answer": lambda c: "CO is produced when carbon burns without enough oxygen. Outdoors it tracks traffic and biomass burning; indoors it is a genuine safety issue from stoves, generators and faulty heaters, because it binds haemoglobin far more strongly than oxygen."
        + _with_reading(c, "carbon_monoxide")
        + " Never run a generator in an enclosed space.",
    },
    {
        "id": "voc",
        "keys": ["voc", "volatile", "solvent", "paint", "benzene", "isoprene", "formaldehyde"],
        "answer": lambda c: "VOCs are a large family of carbon-based gases — fuels, solvents, paints, cleaning agents, cooking emissions and plant compounds like isoprene. They matter because they help convert NOₓ into ozone and secondary organic aerosol. "
        "The chemistry lab shows benzene as one example; real urban VOC mixtures contain hundreds of species with very different reactivity.",
    },
    {
        "id": "who",
        "keys": ["who guideline", "world health", "guideline", "safe level", "limit", "how clean"],
        "answer": lambda c: "The WHO 2021 air-quality guidelines are health-based reference concentrations, not legal limits: 15 µg/m³ for 24-hour PM₂.₅, 45 for PM₁₀, 25 for NO₂, 100 for 8-hour ozone, 40 for SO₂ and 4 mg/m³ for CO. "
        "AirSense compares the live reading against those values, so you can see how far the air is from the health reference even when the AQI looks acceptable.",
    },
    {
        "id": "mask",
        "keys": ["mask", "n95", "ffp2", "respirator", "surgical"],
        "answer": lambda c: "A well-fitted N95 or FFP2 respirator filters fine particles well when the seal is good — that is the part people get wrong. It does little for gases like ozone, NO₂ or CO. "
        "Surgical masks reduce large droplets but are not reliable for PM₂.₅. Fit matters more than the rating on the box.",
    },
    {
        "id": "exercise",
        "keys": ["run", "running", "jog", "cycle", "exercise", "workout", "walk", "outside", "safe to"],
        "answer": lambda c: _current_line(c) + " " + _aqi_advice(_number(c.get("current_aqi")))
        + " Hard effort multiplies the dose: ventilation can rise from roughly 6 L/min at rest to 40–50 L/min while running, so the same air delivers several times more particles."
        + _with_reading(c, "pm2_5", prefix=" Today", verb="PM₂.₅ reads")
        + _window_hint(c),
    },
    {
        "id": "indoor",
        "keys": ["indoor", "inside", "purifier", "filter", "hepa", "windows", "home air"],
        "answer": lambda c: "Indoors, the main levers are source control and ventilation. Cooking, candles and smoking dominate indoor PM; a HEPA purifier sized for the room helps most in a closed bedroom. "
        "During a bad outdoor episode, keeping windows shut and running filtration reduces exposure; when the air is clean, ventilation is the better choice. Gas stoves should always vent outdoors.",
    },
    {
        "id": "plants",
        "keys": ["plant", "plants", "tree", "indoor plant"],
        "answer": lambda c: "Houseplants do remove trace amounts of VOCs in sealed chambers, but at realistic indoor air-exchange rates their effect is negligible compared with ventilation or a filter. "
        "Trees outdoors help more — through shade and by intercepting particles — but they also emit VOCs that can feed ozone, so the effect is local and seasonal.",
    },
    {
        "id": "reduce",
        "keys": ["reduce", "improve", "fix", "emission", "what can i do", "help the air", "cleaner"],
        "answer": lambda c: "Most urban air pollution is a combustion problem, so the highest-leverage actions are the boring ones: use public transport, walking or cycling where it is realistic; stop idling; avoid open burning; service engines and generators; switch cooking and heating away from solid fuels; and support clean electricity. "
        "Individually, cutting a car trip is small; collectively those choices set the baseline everyone breathes.",
    },
    {
        "id": "smoke",
        "keys": ["wildfire", "fire", "smoke", "burning", "crop burning", "stubble"],
        "answer": lambda c: "Smoke from fires is a package: fine particles, black carbon, CO and a soup of organics. PM₂.₅ usually spikes hardest and travels furthest, which is why smoke can lift AQI hundreds of kilometres downwind. "
        "During a smoke episode, keep windows closed, run filtration, and treat the AQI as a ceiling rather than a target.",
    },
    {
        "id": "winter",
        "keys": ["winter", "delhi", "november", "cold", "inversion", "stubble"],
        "answer": lambda c: "Winter smog is largely meteorology plus emissions. A temperature inversion traps cool air under warmer air, so the boundary layer collapses from a kilometre or two to a few hundred metres and the same emissions concentrate. "
        "Add crop-residue burning, residential heating and traffic, and the AQI climbs fastest in the early morning before the inversion breaks.",
    },
    {
        "id": "health",
        "keys": ["asthma", "heart", "lung", "health effect", "children", "pregnant", "elderly", "copd", "sensitive"],
        "answer": lambda c: "Fine particles and ozone irritate airways and are associated with asthma flare-ups, reduced lung function and cardiovascular strain. Children, older adults, pregnant people and anyone with heart or lung conditions are more sensitive. "
        "The practical response is dose reduction — shorter, gentler outdoor effort, cleaner indoor air, and a clinician's advice for personal decisions.",
    },
    {
        "id": "aqi_100",
        "keys": ["100", "150", "200", "300", "unhealthy", "hazardous", "moderate mean"],
        "answer": lambda c: "On the US scale, 0–50 is Good, 51–100 Moderate, 101–150 Unhealthy for Sensitive Groups, 151–200 Unhealthy, 201–300 Very Unhealthy and above 300 Hazardous. "
        "Each band is a public-health message, not a cliff: risk rises smoothly with concentration, and the bands simply mark where advice changes.",
    },
    {
        "id": "pm25_vs_aqi",
        "keys": ["pm2.5 vs aqi", "difference between pm2.5", "aqi calculated", "how is aqi", "convert"],
        "answer": lambda c: "AQI is a transformed concentration, not a different measurement. For PM₂.₅ the US EPA maps concentrations onto index breakpoints (for example 35.4 µg/m³ is 100), then the overall AQI is the highest sub-index across pollutants. "
        "That is why a PM₂.₅ value of 12 can sit in 'Moderate' while still being close to the WHO 24-hour guideline of 15.",
    },
    {
        "id": "data",
        "keys": ["where does the data", "data from", "source", "open-meteo", "accurate", "sensor", "model"],
        "answer": lambda c: "The readings come from Open-Meteo's air-quality API, which serves the CAMS global model, not a local sensor. It is good for regional patterns and trends, weaker at street scale — a kerbside or indoor reading can differ a lot. "
        "Treat it as a well-informed estimate of the air around a point, and check a nearby monitor if you need regulatory-grade numbers.",
    },
    {
        "id": "lab",
        "keys": ["chemistry lab", "simulation", "model", "slider", "structure", "molecule", "3d"],
        "answer": lambda c: "The lab is a molecular field guide, not a kinetics solver. Pick a pollutant and the 3D structure is a simplified geometry — bond angles and atom counts are right, but real molecules vibrate and the particulate entry is a mixture by definition. "
        "The reading shown beside each molecule is live for the place you have selected.",
    },
    {
        "id": "acid_rain",
        "keys": ["acid rain", "sulphate", "nitrate", "deposition"],
        "answer": lambda c: "SO₂ and NOₓ oxidise in clouds to sulphuric and nitric acid, which can fall as acid deposition or travel as sulphate and nitrate particles. "
        "That is why coal sulphur controls changed both acid rain and regional haze: the same emissions were doing both jobs.",
    },
    {
        "id": "climate",
        "keys": ["climate", "warming", "methane", "co2", "carbon dioxide"],
        "answer": lambda c: "Air quality and climate share sources but are not the same problem. CO₂ warms slowly and globally; PM₂.₅, ozone and NO₂ act locally and over days. "
        "Cutting combustion usually helps both, though warming can raise ozone and wildfire smoke, so the two need to be planned together rather than assumed to move in lockstep.",
    },
    {
        "id": "car",
        "keys": ["car", "driving", "recirculate", "cabin", "ac"],
        "answer": lambda c: "In traffic, closing windows and using recirculation reduces cabin exposure to fresh exhaust — but do not recirculate for hours in a sealed car. "
        "A cabin particle filter helps with PM; it does nothing for CO or NO₂ once they are inside.",
    },
]


def _score(question: str, keys) -> int:
    score = 0
    for key in keys:
        token = key.strip().lower()
        if token and token in question:
            score += 2 if " " in token else 1
    return score


def answer_simple_question(prompt: str, context: dict) -> str:
    """Answer everyday air-quality questions without any external service."""
    question = " ".join(str(prompt or "").lower().split())
    if not question:
        return "Ask me about today's reading, a specific pollutant, or what to do with your afternoon outdoors."

    aqi = _number(context.get("current_aqi"))

    best, best_score = None, 0
    for topic in TOPICS:
        score = _score(question, topic["keys"])
        if score > best_score:
            best, best_score = topic, score

    if best is not None:
        return best["answer"](context)

    if aqi is not None:
        return (
            f"I am not sure that maps onto a topic I hold confidently, but here is the live picture: {_current_line(context)} "
            "You can ask me about PM₂.₅, ozone, NO₂, SO₂, CO, VOCs, masks, indoor air, or how the AQI scale works."
        )
    return (
        "I can explain the AQI, individual pollutants, exposure and the chemistry lab. "
        "Pick a city first so I can ground the answer in a live reading."
    )


# ---------------------------------------------------------------------------
# Optional model providers
# ---------------------------------------------------------------------------


def _setting(name: str, default=None):
    try:
        import streamlit as st

        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, default)


def hosted_configured() -> bool:
    return bool(_setting("OPENAI_API_KEY"))


def _build_messages(prompt: str, context: dict, history=None):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
            + "\n\nCurrent AirSense context (data only):\n"
            + json.dumps(context, default=str),
        }
    ]
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


def ask_local_ollama(
    prompt: str,
    context: dict,
    history=None,
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434",
) -> str:
    """Call a local Ollama model; no hosted API key is needed."""
    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/api/chat",
            json={"model": model, "messages": _build_messages(prompt, context, history), "stream": False},
            timeout=180,
        )
    except requests.ConnectionError as exc:
        raise RuntimeError(
            "Cannot reach Ollama at localhost:11434. Open Ollama and make sure its local server is running."
        ) from exc
    if response.status_code == 404:
        installed = list_local_models(base_url)
        available = ", ".join(installed[:5]) if installed else "no models detected"
        raise RuntimeError(
            f"Ollama does not have model '{model}'. Installed: {available}. "
            "Pull a model with `ollama pull <model>` or change the model tag."
        )
    response.raise_for_status()
    try:
        return response.json()["message"]["content"]
    except (KeyError, TypeError):
        raise RuntimeError("Ollama returned an unexpected response.")


def ask_hosted_model(prompt: str, context: dict, history=None) -> str:
    api_key = _setting("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No hosted AI key configured. Add OPENAI_API_KEY to .streamlit/secrets.toml or .env."
        )
    model = _setting("OPENAI_MODEL", "gpt-4o-mini")
    base_url = _setting("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": _build_messages(prompt, context, history), "temperature": 0.35},
        timeout=60,
    )
    if response.status_code == 401:
        raise RuntimeError("The hosted AI provider rejected the API key. Check the configured key.")
    if response.status_code == 429:
        raise RuntimeError("The hosted AI provider rate-limited this request. Try again shortly.")
    response.raise_for_status()
    try:
        return response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("The hosted AI provider returned an unexpected response format.")
