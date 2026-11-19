"""AirSense — the air, everywhere.

Two things, done properly: a live globe you can click anywhere on, and a
chemistry lab that shows what the numbers are made of.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.aqi import (
    aqi_band,
    dominant_pollutant,
    format_time,
    is_missing,
    us_aqi_from_pm25,
    who_comparisons,
)
from src.air_quality import fetch_air_quality, search_locations
from src.chat import answer_simple_question, ask_hosted_model, hosted_configured
from src.demo import demo_payload
from src.design import SITE_CSS

# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AirSense — the air, everywhere",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PLACES = {
    "Bengaluru": ("India", 12.9716, 77.5946, "Asia/Kolkata"),
    "Delhi": ("India", 28.6139, 77.2090, "Asia/Kolkata"),
    "Mumbai": ("India", 19.0760, 72.8777, "Asia/Kolkata"),
    "London": ("United Kingdom", 51.5072, -0.1276, "Europe/London"),
    "New York": ("United States", 40.7128, -74.0060, "America/New_York"),
    "São Paulo": ("Brazil", -23.5505, -46.6333, "America/Sao_Paulo"),
}

POLLUTANTS = [
    ("pm2_5", "PM₂.₅", "Fine particles"),
    ("pm10", "PM₁₀", "Coarse dust"),
    ("nitrogen_dioxide", "NO₂", "Traffic marker"),
    ("ozone", "O₃", "Photochemical"),
    ("sulphur_dioxide", "SO₂", "Fuel sulphur"),
    ("carbon_monoxide", "CO", "Incomplete burn"),
]
READING_KEYS = [key for key, _, _ in POLLUTANTS]
UNITS = {key: "µg/m³" for key in READING_KEYS}


def place(name: str) -> dict:
    country, lat, lon, tz = PLACES[name]
    return {
        "name": name,
        "country": country,
        "latitude": lat,
        "longitude": lon,
        "timezone": tz,
    }


if "place" not in st.session_state:
    st.session_state.place = place("Bengaluru")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False
if "chat_pending" not in st.session_state:
    st.session_state.chat_pending = None


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


@st.cache_data(ttl=900, show_spinner=False)
def load_air(latitude: float, longitude: float):
    return fetch_air_quality(latitude, longitude)


@st.cache_data(ttl=86_400, show_spinner=False)
def find_places(query: str):
    return search_locations(query)


def run_search(term: str) -> None:
    term = (term or "").strip()
    if len(term) < 2:
        return
    try:
        matches = find_places(term)
    except Exception:
        matches = []
    if not matches:
        st.session_state["search_error"] = f"Nothing found for “{term}”. Try a city name."
        return
    best = matches[0]
    st.session_state["search_error"] = None
    st.session_state["place"] = {
        "name": best.get("name") or term.title(),
        "country": best.get("country") or "",
        "latitude": float(best.get("latitude") or 0.0),
        "longitude": float(best.get("longitude") or 0.0),
        "timezone": best.get("timezone") or "local time",
    }
    st.rerun()


current_place = st.session_state.place
city = current_place["name"]
country = current_place["country"]
latitude = float(current_place["latitude"])
longitude = float(current_place["longitude"])
timezone_name = current_place.get("timezone") or "local time"

demo_mode = False
data_error = ""
try:
    payload = load_air(latitude, longitude)
except Exception as exc:  # offline or provider hiccup — keep the page usable
    payload = demo_payload(city, country)
    demo_mode = True
    data_error = f"{type(exc).__name__}: {exc}"

_hourly = payload.get("hourly")
hourly = _hourly.copy() if isinstance(_hourly, pd.DataFrame) else pd.DataFrame()
current = payload.get("current") or {}
if hourly.empty or "time" not in hourly.columns:
    st.error("No observations came back for this place. Try another search.")
    st.stop()

hourly["time"] = pd.to_datetime(hourly["time"], errors="coerce")
for key in READING_KEYS + ["us_aqi"]:
    if key in hourly.columns:
        hourly[key] = pd.to_numeric(hourly[key], errors="coerce")


def number(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def resolve(key: str):
    value = current.get(key)
    if not is_missing(value):
        return number(value)
    if key in hourly.columns:
        reference = pd.to_datetime(current.get("time"), errors="coerce")
        if pd.isna(reference):
            reference = hourly["time"].max()
        recent = hourly[hourly["time"] <= reference][key].dropna()
        if not recent.empty:
            return number(recent.iloc[-1])
    return None


readings = {key: resolve(key) for key in READING_KEYS}
aqi = resolve("us_aqi")
derived = False
if aqi is None and readings.get("pm2_5") is not None:
    aqi = us_aqi_from_pm25(readings["pm2_5"])
    derived = True

band = aqi_band(aqi)
updated = format_time(current.get("time") or hourly["time"].max())
source = "Open-Meteo · CAMS model"
if demo_mode:
    source = "Sample data · provider unreachable"
elif derived:
    source = "Indicative US AQI · derived from PM₂.₅"

ratios = {row["key"]: row["ratio"] for row in who_comparisons(readings)}
dominant = dominant_pollutant(readings)

# ---------------------------------------------------------------------------
# Context handed to the assistant
# ---------------------------------------------------------------------------

chat_context = {
    "location": city,
    "country": country,
    "latitude": latitude,
    "longitude": longitude,
    "timezone": timezone_name,
    "current_aqi": aqi,
    "aqi_scale": "US EPA AQI",
    "current_category": band.get("name"),
    "current_readings": readings,
    "units": "µg/m³",
    "who_ratios": ratios,
    "dominant_pollutant": dominant if isinstance(dominant, str) else (dominant or {}).get("label"),
    "updated": updated,
    "data_source": source,
    "is_sample_data": demo_mode,
}

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------

st.html(f"<style>{SITE_CSS}</style>")

# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------

st.html(
    f"""
    <div class="topbar">
      <div class="brand">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M12 21c0-6 0-10 0-16" stroke="#1F7A4F" stroke-width="1.4" stroke-linecap="round"/>
          <path d="M12 13c-4 0-6-2.4-6-6 4 0 6 2.4 6 6Z" fill="#1F7A4F" opacity=".18" stroke="#1F7A4F" stroke-width="1.2" stroke-linejoin="round"/>
          <path d="M12 10c0-3.6 2.2-6 6-6 0 3.6-2.2 6-6 6Z" fill="#1F7A4F" opacity=".32" stroke="#1F7A4F" stroke-width="1.2" stroke-linejoin="round"/>
        </svg>
        <span class="brand-name">Air<em>Sense</em></span>
      </div>
      <div class="topbar-meta">
        <span class="topbar-place"><b>{city}</b>, {country or "—"} · {updated}</span>
        <span class="status-pill{' demo' if demo_mode else ''}">{'Sample data' if demo_mode else 'Live'}</span>
      </div>
    </div>
    """,
)

# ---------------------------------------------------------------------------
# Hero + search
# ---------------------------------------------------------------------------

hero_left, hero_right = st.columns([1.45, .8], gap="large")
with hero_left:
    st.html(
        f"""
        <div class="hero-copy">
          <div class="eyebrow">Atmospheric intelligence · {country or "global"}</div>
          <h1>The air,<br><em>everywhere.</em></h1>
          <p class="hero-lede">
            One live map of the air you are breathing, and a small laboratory for
            what is actually in it. Tap any point on the planet to read its
            <b>AQI and pollutants</b>; ask the assistant anything in plain language.
          </p>
        </div>
        """,
    )

with hero_right:
    with st.container(key="search_box"):
        with st.form("search_form", border=False):
            st.markdown('<div class="search-label">Your observation point</div>', unsafe_allow_html=True)
            query = st.text_input(
                "Search a city",
                value="",
                placeholder="Search any city — Delhi, Lagos, Osaka…",
                label_visibility="collapsed",
                key="search_input",
            )
            submitted = st.form_submit_button("Search this place", type="primary", width="stretch")
        if submitted:
            run_search(query)
        if st.session_state.get("search_error"):
            st.caption(st.session_state["search_error"])
        picked = st.pills(
            "Quick jump",
            list(PLACES.keys()),
            key="quick_pick",
            label_visibility="collapsed",
        )
        st.markdown(
            f'<div class="search-hint">{city} · {latitude:.2f}, {longitude:.2f}<br>{timezone_name}</div>',
            unsafe_allow_html=True,
        )

if picked and picked != st.session_state.get("last_pick"):
    st.session_state["last_pick"] = picked
    st.session_state.place = place(picked)
    st.rerun()

# ---------------------------------------------------------------------------
# Current reading
# ---------------------------------------------------------------------------

bars = []
for key, label, note in POLLUTANTS[:4]:
    value = readings.get(key)
    ratio = ratios.get(key)
    if ratio is None:
        color, width = "#cbd9d1", 0
    else:
        color = "#2f9e6b" if ratio <= 1 else "#c39127" if ratio <= 2.5 else "#c4695f"
        width = min(ratio / 5, 1) * 100
    shown = "—" if value is None else (f"{value:.0f}" if value >= 100 else f"{value:.1f}")
    bars.append(
        f"""
        <div class="pol" title="{note}">
          <div class="pol-top"><span class="pol-name">{label}</span><span class="pol-val">{shown}<span>µg/m³</span></span></div>
          <div class="pol-track"><i style="width:{width:.0f}%;background:{color}"></i></div>
        </div>
        """
    )

st.html(
    f"""
    <div class="now-wrap">
      <div class="now-card" style="--band:{band.get('color', '#1f7a4f')}">
        <div class="now-aqi">
          <div class="now-kicker">Now in {city}</div>
          <div class="now-value">{'—' if aqi is None else f'{aqi:.0f}'}<small>US AQI</small></div>
          <div class="now-band"><b>{band.get('name', 'Unavailable')}</b></div>
          <div class="now-source">{source} · updated {updated}</div>
        </div>
        <div class="pol-grid">{''.join(bars)}</div>
      </div>
    </div>
    """,
)

if demo_mode:
    st.caption(f"Live data was unavailable ({data_error.split(':')[0]}), so this page is showing a realistic sample. Search another city or refresh to retry.")

# ---------------------------------------------------------------------------
# Globe
# ---------------------------------------------------------------------------

st.html(
    """
    <div class="section">
      <div class="section-head">
        <div>
          <div class="section-kicker">Live AQI field</div>
          <h2 class="section-title">Every place is a reading.</h2>
        </div>
        <p class="section-note">Drag to turn the planet, scroll to zoom, then click or tap anywhere — ocean included — for that point’s air.</p>
      </div>
      <div class="section-body"></div>
    </div>
    """
)

globe_path = Path(__file__).parent / "globe.html"
if globe_path.exists():
    globe_state = {
        "selected": {
            "name": city,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "aqi": number(aqi),
            "pm25": number(readings.get("pm2_5")),
            "category": band.get("name", "Unavailable"),
            "color": band.get("color", "#8BA295"),
            "updated": updated,
            "is_demo": demo_mode,
        }
    }
    globe_json = json.dumps(globe_state, ensure_ascii=False).replace("</", "<\\/")
    components.html(
        globe_path.read_text(encoding="utf-8").replace("__AIRSENSE_GLOBE_STATE__", globe_json),
        height=640,
        scrolling=False,
    )
else:
    st.info("The globe could not be loaded.")

# ---------------------------------------------------------------------------
# Chemistry lab
# ---------------------------------------------------------------------------

st.html(
    """
    <div class="section">
      <div class="section-head">
        <div>
          <div class="section-kicker">Chemistry lab</div>
          <h2 class="section-title">What the numbers are made of.</h2>
        </div>
        <p class="section-note">Pick a pollutant, spin its structure, and see where it comes from and what actually reduces it.</p>
      </div>
      <div class="section-body"></div>
    </div>
    """
)

lab_path = Path(__file__).parent / "chemistry_lab.html"
if lab_path.exists():
    lab_state = {"readings": {key: number(readings.get(key)) for key in READING_KEYS}}
    lab_json = json.dumps(lab_state, ensure_ascii=False).replace("</", "<\\/")
    components.html(
        lab_path.read_text(encoding="utf-8").replace("__AIRSENSE_CHEMISTRY_STATE__", lab_json),
        height=640,
        scrolling=False,
    )
else:
    st.info("The chemistry lab could not be loaded.")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.html(
    """
    <div class="site-footer">
      <div><b>AirSense</b> — live air, honestly read.<br>AQI values follow the US EPA scale; WHO 2021 guidelines are shown for comparison.</div>
      <div>Data from <b>Open-Meteo</b> (CAMS model).<br>Educational tool — not medical advice.</div>
    </div>
    """
)

# ---------------------------------------------------------------------------
# Floating assistant
# ---------------------------------------------------------------------------

SUGGESTIONS = {
    "Today’s air": "What does my AQI mean right now?",
    "Ozone at 3pm": "Why does ozone peak in the afternoon?",
    "Can I run?": "Is it safe to run outside today?",
}


def reply(prompt: str) -> str:
    history = st.session_state.chat_history
    if hosted_configured():
        try:
            return ask_hosted_model(prompt, chat_context, history)
        except Exception:
            pass
    return answer_simple_question(prompt, chat_context)


def push_message(role: str, content: str) -> None:
    st.session_state.chat_history.append({"role": role, "content": content})
    st.session_state.chat_history = st.session_state.chat_history[-24:]


def remember_suggestion() -> None:
    value = st.session_state.get("chat_suggestion")
    if value:
        st.session_state.chat_pending = SUGGESTIONS.get(value)


with st.container(key="chat_fab"):
    if st.button("💬", key="chat_toggle", help="Ask AirSense about the air"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.session_state.chat_pending = None

if st.session_state.chat_open:
    with st.container(key="chat_panel"):
        st.markdown(
            '<div class="chat-head">'
            '<div class="chat-title">Ask Air<span>Sense</span></div>'
            '</div>'
            f'<div class="chat-sub">{city} · {band.get("name", "no reading")}</div>',
            unsafe_allow_html=True,
        )
        with st.container(key="chat_close"):
            if st.button("✕", key="chat_close_btn", help="Close"):
                st.session_state.chat_open = False
                st.rerun()

        st.markdown('<div class="chat-rule"></div>', unsafe_allow_html=True)

        st.pills(
            "Suggested questions",
            list(SUGGESTIONS.keys()),
            key="chat_suggestion",
            label_visibility="collapsed",
            on_change=remember_suggestion,
        )

        thread = st.container(key="chat_thread", height=190, border=False)
        with thread:
            if not st.session_state.chat_history:
                st.markdown(
                    f"I’m reading **{city}** right now — US AQI **{('—' if aqi is None else f'{aqi:.0f}')}** "
                    f"({band.get('name', 'unavailable')}). Ask me about the number, a pollutant, "
                    "or what to do with your afternoon.",
                    unsafe_allow_html=True,
                )
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        with st.form("chat_form", clear_on_submit=True, border=False):
            text_col, send_col = st.columns([5, 1], vertical_alignment="center")
            with text_col:
                typed = st.text_input(
                    "Message",
                    placeholder="Ask about the air…",
                    label_visibility="collapsed",
                    key="chat_text",
                )
            with send_col:
                sent = st.form_submit_button("↑", type="primary")

        st.markdown(
            '<div class="chat-foot">Grounded in the live reading above. Educational guidance, not medical advice.</div>',
            unsafe_allow_html=True,
        )

    prompt = None
    if typed and sent:
        prompt = typed.strip()
    elif st.session_state.chat_pending:
        prompt = st.session_state.chat_pending
        st.session_state.chat_pending = None

    if prompt:
        push_message("user", prompt)
        with st.spinner("Reading the air…"):
            answer = reply(prompt)
        push_message("assistant", answer)
        st.rerun()
