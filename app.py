"""AirSense — the air, everywhere.

Two things, done properly: a live globe you can click anywhere on, and a
chemistry lab that shows what the numbers are made of.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import json
import math
import textwrap
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.aqi import (
    ACTIVITIES,
    aqi_band,
    aqi_trend,
    best_windows,
    daily_heatmap,
    daily_summary,
    dominant_pollutant,
    exposure_stats,
    forecast_frame,
    format_time,
    format_window,
    is_missing,
    pollutant_contributions,
    us_aqi_from_pm25,
    who_comparisons,
)
from src.air_quality import fetch_air_quality, search_locations
from src.charts import aqi_chart, chart_legend, day_outlook_html
from src.chat import answer_simple_question, ask_hosted_model, hosted_configured
from src.demo import demo_payload
from src.design import SITE_CSS
from src.rankings import city_ranking, country_ranking, fetch_ranked_cities, sample_rankings

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


@st.cache_data(ttl=900, show_spinner=False)
def load_rankings():
    return fetch_ranked_cities()


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


def html_block(markup: str) -> None:
    """Render raw HTML without st.html's SVG sanitising."""
    st.markdown(textwrap.dedent(markup).strip(), unsafe_allow_html=True)


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
contributions = pollutant_contributions(readings)
contribution_by_key = {row["key"]: row for row in contributions}
leading_key = contributions[0]["key"] if contributions else None

reference_time = pd.to_datetime(current.get("time"), errors="coerce")
if pd.isna(reference_time):
    reference_time = hourly["time"].max()
reference_time = pd.to_datetime(reference_time)

future = forecast_frame(hourly, reference_time, 120)
upcoming = future[future["time"] > reference_time.floor("h")] if not future.empty else future
next24 = upcoming[upcoming["time"] < reference_time.floor("h") + pd.Timedelta(hours=24)] if not upcoming.empty else upcoming
next12 = upcoming[upcoming["time"] < reference_time.floor("h") + pd.Timedelta(hours=12)] if not upcoming.empty else upcoming
tomorrow_start = (reference_time + pd.Timedelta(days=1)).normalize()
tomorrow = future[future["time"].dt.normalize() == tomorrow_start] if not future.empty else future
past24 = hourly[
    (hourly["time"] > reference_time - pd.Timedelta(hours=24))
    & (hourly["time"] <= reference_time)
]
clean_windows = (
    best_windows(next12["time"], next12["us_aqi"], window=3, count=1, horizon=12)
    if not next12.empty
    else []
)
best_window = clean_windows[0] if clean_windows else None
peak_row = next24.loc[next24["us_aqi"].idxmax()] if not next24.empty else None
trend = aqi_trend(hourly, reference_time)


def period_change(days: int) -> float | None:
    """Percentage change between the last N days and the N before them."""
    frame = hourly.dropna(subset=["us_aqi"])
    frame = frame[frame["time"] <= reference_time]
    if frame.empty:
        return None
    recent = frame[frame["time"] > reference_time - pd.Timedelta(days=days)]["us_aqi"]
    prior = frame[
        (frame["time"] <= reference_time - pd.Timedelta(days=days))
        & (frame["time"] > reference_time - pd.Timedelta(days=days * 2))
    ]["us_aqi"]
    expected = days * 24
    if len(recent) < expected * 0.7 or len(prior) < expected * 0.7:
        return None
    if recent.empty or prior.empty or not prior.mean():
        return None
    return (recent.mean() - prior.mean()) / prior.mean() * 100.0


def aqi_label(value) -> str:
    return "—" if value is None else f"{float(value):.0f}"


def time_label(value) -> str:
    try:
        return pd.to_datetime(value).strftime("%H:%M")
    except (TypeError, ValueError):
        return "—"


# Comparison boards. A provider hiccup leaves the rest of the page intact.
ranking_rows: list[dict] = []
rank_sample = False
try:
    ranking_rows = load_rankings()
except Exception:
    ranking_rows = sample_rankings()
    rank_sample = True

selected_for_rank = {"name": city, "country": country, "aqi": aqi}
local_rank = city_ranking(selected_for_rank, "India", ranking_rows) if ranking_rows else {"available": False}
world_rank = city_ranking(selected_for_rank, "World", ranking_rows) if ranking_rows else {"available": False}
country_rank = country_ranking(selected_for_rank, ranking_rows) if ranking_rows else {"available": False}


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

chat_context.update(
    {
        "pollutant_subindices": {
            row["label"]: row["index"] for row in contributions
        },
        "forecast": {
            "next_24h_peak_aqi": None if peak_row is None else round(float(peak_row["us_aqi"])),
            "next_24h_peak_time": None if peak_row is None else str(pd.to_datetime(peak_row["time"]).strftime("%H:%M")),
            "cleanest_window_next_12h": None if best_window is None else format_window(best_window),
            "cleanest_window_aqi": None if best_window is None else round(float(best_window["mean"])),
            "tomorrow_peak_aqi": None if tomorrow.empty else round(float(tomorrow["us_aqi"].max())),
            "trend_24h": trend.get("text"),
        },
        "history": {
            "last_24h_mean": None if past24.empty else round(float(past24["us_aqi"].mean())),
            "change_24h_percent": trend.get("delta"),
            "change_7d_percent": period_change(7),
            "change_30d_percent": period_change(30),
        },
        "rankings": {
            "india_position": local_rank.get("position"),            "india_total": local_rank.get("total"),
            "india_cleanest": (local_rank.get("cleanest") or {}).get("name"),
            "india_dirtiest": (local_rank.get("dirtiest") or {}).get("name"),
            "world_position": world_rank.get("position"),
            "world_total": world_rank.get("total"),
            "world_cleanest": (world_rank.get("cleanest") or {}).get("name"),
            "world_dirtiest": (world_rank.get("dirtiest") or {}).get("name"),
            "country_position": country_rank.get("position"),
            "country_total": country_rank.get("total"),
            "is_sample": rank_sample,
        },
    }
)

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
for key, label, note in POLLUTANTS:
    value = readings.get(key)
    contribution = contribution_by_key.get(key)
    index = contribution["index"] if contribution else None
    if index is None:
        color, width = "#cbd9d1", 0
        chip = "no reading"
    else:
        color = contribution["band"]["color"]
        width = min(index / 300, 1) * 100
        chip = f"sub-index {index}"
    shown = "—" if value is None else (f"{value:.0f}" if value >= 100 else f"{value:.1f}")
    ratio = ratios.get(key)
    who = "" if ratio is None else f"{ratio:.1f}× WHO"
    lead = key == leading_key
    bars.append(
        f"""
        <div class="pol{' lead' if lead else ''}" title="{note}">
          <div class="pol-top"><span class="pol-name">{label}{'<em class="pol-lead">drives today</em>' if lead else ''}</span><span class="pol-val">{shown}<span>µg/m³</span></span></div>
          <div class="pol-track"><i style="width:{width:.0f}%;background:{color}"></i></div>
          <div class="pol-sub"><span style="color:{color}">{chip}</span><span>{who}</span></div>
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
        <div class="pol-grid">{''.join(bars)}<div class="pol-note">Pollutant sub-indices are indicative conversions; the headline AQI is the provider value.</div></div>
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
# Forecast
# ---------------------------------------------------------------------------

forecast_view = future.head(48)
if not forecast_view.empty:
    forecast_peak = forecast_view.loc[forecast_view["us_aqi"].idxmax()]
    chart_peak_value = aqi_label(forecast_peak["us_aqi"])
    chart_peak_time = pd.to_datetime(forecast_peak["time"]).strftime("%a %H:%M")
    forecast_spans = [(best_window["start"], best_window["end"])] if best_window else []
    forecast_svg = aqi_chart(
        forecast_view["time"],
        forecast_view["us_aqi"],
        now_index=0,
        spans=forecast_spans,
        chart_id="forecast",
        height=250,
        aria="Forecast US AQI for the next 48 hours",
    )

    outlook = []
    local_future = future[future["time"] >= reference_time.floor("h")].copy()
    if not local_future.empty:
        local_future["date"] = local_future["time"].dt.normalize()
        grouped = (
            local_future.groupby("date", as_index=False)
            .agg(mean=("us_aqi", "mean"), low=("us_aqi", "min"), high=("us_aqi", "max"))
            .head(5)
        )
        for _, day in grouped.iterrows():
            if day["date"] == reference_time.normalize():
                label = "Today"
            elif day["date"] == tomorrow_start:
                label = "Tomorrow"
            else:
                label = day["date"].strftime("%a")
            outlook.append(
                {
                    "label": label,
                    "mean": float(day["mean"]),
                    "low": float(day["low"]),
                    "high": float(day["high"]),
                    "band": aqi_band(day["mean"]),
                }
            )

    peak_value = aqi_label(peak_row["us_aqi"]) if peak_row is not None else "—"
    peak_time = time_label(peak_row["time"]) if peak_row is not None else "—"
    window_text = format_window(best_window) if best_window else "—"
    window_aqi = aqi_label(best_window["mean"] if best_window else None)
    tomorrow_peak = aqi_label(tomorrow["us_aqi"].max()) if not tomorrow.empty else "—"
    tomorrow_band = aqi_band(tomorrow["us_aqi"].max())["short"] if not tomorrow.empty else "no data"

    html_block(
        f"""
        <div class="section">
          <div class="section-head">
            <div>
              <div class="section-kicker">Forecast</div>
              <h2 class="section-title">What the next days hold.</h2>
            </div>
            <p class="section-note">Hourly model guidance for planning, not a promise. The shaded stretch is the cleanest three-hour window in the next twelve hours.</p>
          </div>
          <div class="section-body">
            <div class="panel">
              <div class="panel-head">
                <span class="panel-label">Next 48 hours · hourly US AQI</span>
                <span class="panel-badge">48h peak {chart_peak_value} · {chart_peak_time}</span>
              </div>
              {forecast_svg}
              {chart_legend()}
              <div class="stat-row">
                <div><span>Next 24h peak</span><b>{peak_value}</b><small>{peak_time} local</small></div>
                <div><span>Cleanest window</span><b>{window_text}</b><small>about AQI {window_aqi}</small></div>
                <div><span>Tomorrow</span><b>{tomorrow_peak}</b><small>{tomorrow_band}</small></div>
                <div><span>Trend</span><b>{trend.get('text', '—').replace(' vs previous 24h', '')}</b><small>against the previous day</small></div>
              </div>
            </div>
            <div class="subhead">Five-day outlook</div>
            {day_outlook_html(outlook)}
          </div>
        </div>
        """
    )
else:
    st.html(
        """
        <div class="section">
          <div class="section-head">
            <div><div class="section-kicker">Forecast</div><h2 class="section-title">What the next days hold.</h2></div>
            <p class="section-note">The forecast feed is unavailable for this place right now.</p>
          </div>
        </div>
        """
    )

# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

st.html(
    """
    <div class="section history-head">
      <div class="section-head">
        <div>
          <div class="section-kicker">History</div>
          <h2 class="section-title">How the air got here.</h2>
        </div>
        <p class="section-note">Model reanalysis for this point. Hours are local; the daily view shows the mean with its minimum–maximum range.</p>
      </div>
    </div>
    """
)

history_range = st.pills(
    "History range",
    ["24 hours", "7 days", "30 days"],
    default="7 days",
    key="history_range",
    label_visibility="collapsed",
)

history_svg = ""
history_stats: list[tuple[str, str, str]] = []
history_label = ""
history_heat = ""
history_change = None

if history_range == "24 hours":
    hist = past24.dropna(subset=["us_aqi"])
    if not hist.empty:
        history_svg = aqi_chart(
            hist["time"],
            hist["us_aqi"],
            chart_id="history24",
            height=230,
            aria="US AQI over the past 24 hours",
        )
        clean_hours = int((hist["us_aqi"] <= 50).sum())
        history_stats = [
            ("Average", f"{hist['us_aqi'].mean():.0f}", "US AQI"),
            ("Peak", f"{hist['us_aqi'].max():.0f}", time_label(hist.loc[hist['us_aqi'].idxmax(), 'time'])),
            ("Good hours", f"{clean_hours} / {len(hist)}", "at or below AQI 50"),
            ("Change", f"{history_change:+.0f}%" if (history_change := trend.get('delta')) is not None else "—", "vs previous 24h"),
        ]
    history_label = "Past 24 hours · hourly US AQI"
else:
    days = 7 if history_range == "7 days" else 30
    heat = daily_heatmap(hourly, reference_time, days)
    summary = daily_summary(hourly, reference_time, days)
    if not summary.empty:
        history_svg = aqi_chart(
            summary["date"],
            summary["mean_aqi"],
            lows=summary["min_aqi"],
            highs=summary["peak_aqi"],
            chart_id=f"history{days}",
            height=240,
            aria=f"Daily mean US AQI over the past {days} days",
        )
        change = period_change(days)
        clean_share = float((heat["us_aqi"] <= 50).mean() * 100) if not heat.empty else 0.0
        over_share = float((heat["us_aqi"] > 100).mean() * 100) if not heat.empty else 0.0
        history_stats = [
            ("Average", f"{heat['us_aqi'].mean():.0f}", "US AQI"),
            ("Peak", f"{heat['us_aqi'].max():.0f}", "worst hour"),
            ("Good hours", f"{clean_share:.0f}%", "at or below AQI 50"),
            ("Change", f"{change:+.0f}%" if change is not None else "—", f"vs previous {days} days" if change is not None else "needs a longer record"),
        ]
        if days == 7:
            lookup = {(row["date"], row["hour"]): row for _, row in heat.iterrows()}
            dates = sorted(heat["date"].unique())
            cells = []
            for date in dates:
                cells.append(f'<span class="heat-date">{pd.Timestamp(date).strftime("%a %d")}</span>')
                for hour in range(24):
                    row = lookup.get((date, hour))
                    if row is None:
                        cells.append('<span class="heat-cell empty"></span>')
                    else:
                        cells.append(
                            f'<span class="heat-cell" style="background:{row["color"]}" '
                            f'title="{pd.Timestamp(date).strftime("%a %d")} · {hour:02d}:00 · AQI {row["us_aqi"]:.0f}"></span>'
                        )
            history_heat = (
                '<div class="heat"><div class="heat-head"><span>Last 7 days · hour by hour</span>'
                '<span class="heat-axis">00h → 23h</span></div>'
                f'<div class="heat-grid">{"".join(cells)}</div></div>'
            )
    history_label = f"Past {days} days · daily mean with min–max range"

if history_svg:
    stat_html = "".join(
        f"<div><span>{label}</span><b>{value}</b><small>{note}</small></div>"
        for label, value, note in history_stats
    )
    html_block(
        f"""
        <div class="section-body history-body">
          <div class="panel">
            <div class="panel-head">
              <span class="panel-label">{history_label}</span>
              <span class="panel-badge">{source}</span>
            </div>
            {history_svg}
            {chart_legend()}
            <div class="stat-row">{stat_html}</div>
          </div>
          {history_heat}
        </div>
        """
    )
else:
    st.caption("Historical reanalysis is unavailable for this window.")

# ---------------------------------------------------------------------------
# Personal health advisory
# ---------------------------------------------------------------------------

GROUPS = {
    "General public": 1.0,
    "Children": 1.3,
    "Older adults": 1.25,
    "Asthma or heart": 1.5,
}
ACTIVITY_CHOICES = {
    "Walking": ("Light activity · walking", 1.0),
    "Cycling": ("Moderate exercise · cycling", 1.15),
    "Running": ("Vigorous exercise · running", 1.35),
}
VERDICTS = [
    ("Go ahead", "This is clean air for the activity you chose. Ordinary plans need no adjustment."),
    ("Fine for most", "Reasonable for most people. If you are unusually sensitive, keep the effort gentle and stop if your chest tightens."),
    ("Keep it gentle", "Shorten the hard parts and take breaks. Sensitive groups should keep this session easy."),
    ("Shorten it", "Cut the duration and intensity, and prefer a route away from traffic. Sensitive groups should move this indoors."),
    ("Move it indoors", "Outdoor effort is not worth it at this level. Train inside with filtered air, or postpone."),
    ("Stay in", "Treat this as an indoor day: windows closed, filtration on, outdoor time kept brief."),
]

st.html(
    """
    <div class="section">
      <div class="section-head">
        <div>
          <div class="section-kicker">Personal advisory</div>
          <h2 class="section-title">Should you go outside?</h2>
        </div>
        <p class="section-note">A dose-aware answer for your body and your plan, using the live reading and the next twelve hours of forecast.</p>
      </div>
    </div>
    """
)

health_group = st.pills(
    "Who is going outside?",
    list(GROUPS.keys()),
    default="General public",
    key="health_group",
)
health_activity = st.pills(
    "What are you doing?",
    list(ACTIVITY_CHOICES.keys()),
    default="Walking",
    key="health_activity",
)

health_group = health_group or "General public"
health_activity = health_activity or "Walking"
group_factor = GROUPS[health_group]
activity_key, activity_factor = ACTIVITY_CHOICES[health_activity]
risk_aqi = (aqi or 0) * group_factor * activity_factor
risk_band = aqi_band(risk_aqi)
verdict, verdict_body = VERDICTS[min(int(risk_band["severity"]), len(VERDICTS) - 1)]

dose = exposure_stats(readings.get("pm2_5"), 45, ACTIVITIES[activity_key]["ventilation"])
dose_ratio = dose.get("ratio") or 0.0
avoid_row = next12.loc[next12["us_aqi"].idxmax()] if not next12.empty else None
window_text = format_window(best_window) if best_window else "—"
window_aqi_text = aqi_label(best_window["mean"] if best_window else None)
avoid_text = time_label(avoid_row["time"]) if avoid_row is not None else "—"
avoid_aqi_text = aqi_label(avoid_row["us_aqi"]) if avoid_row is not None else "—"

group_note = {
    "General public": "At this level the main lever is duration: the longer and harder the session, the larger the dose.",
    "Children": "Children take in more air per kilogram of body weight, so the same hour outdoors lands as a larger dose.",
    "Older adults": "Cardiovascular strain rises with pollution exposure, so a gentler and shorter session is the safer default.",
    "Asthma or heart": risk_band["sensitive"],
}[health_group]

html_block(
    f"""
    <div class="section-body health-body">
      <div class="advisory" style="--band:{risk_band['color']}">
        <div class="advisory-top">
          <div>
            <div class="advisory-kicker">{health_group} · {health_activity.lower()}</div>
            <div class="advisory-verdict">{verdict}</div>
          </div>
          <div class="advisory-aqi"><b>{aqi_label(aqi)}</b><span>US AQI now</span></div>
        </div>
        <p class="advisory-body">{verdict_body} {group_note}</p>
        <div class="advisory-grid">
          <div><span>Best window</span><b>{window_text}</b><small>about AQI {window_aqi_text}</small></div>
          <div><span>Hardest hour</span><b>{avoid_text}</b><small>forecast AQI {avoid_aqi_text}</small></div>
          <div><span>45-minute dose</span><b>{dose_ratio:.1f}×</b><small>vs guideline-clean air</small></div>
        </div>
        <div class="advisory-foot">Estimate for {health_activity.lower()} at {ACTIVITIES[activity_key]['ventilation']:.0f} L/min ventilation. Educational guidance, not medical advice.</div>
      </div>
    </div>
    """
)

chat_context["health_advisory"] = {
    "group": health_group,
    "activity": health_activity,
    "verdict": verdict,
    "risk_weighted_aqi": round(risk_aqi),
    "best_window": window_text,
    "dose_multiple": round(dose_ratio, 2),
}

# ---------------------------------------------------------------------------
# Rankings
# ---------------------------------------------------------------------------

st.html(
    f"""
    <div class="section">
      <div class="section-head">
        <div>
          <div class="section-kicker">Rankings</div>
          <h2 class="section-title">How this city compares.</h2>
        </div>
        <p class="section-note">{'Sample board — the live ranking provider is temporarily unavailable, so values are illustrative.' if rank_sample else 'Live CAMS estimates for a fixed set of cities. The country board uses one representative city per country. Ranked cleanest first, all from the same hour of data.'}</p>
      </div>
    </div>
    """
)

default_rank_scope = "India" if country == "India" else "World cities"
rank_scope = st.pills(
    "Ranking scope",
    ["India", "World cities", "Countries"],
    default=default_rank_scope,
    key=f"rank_scope_{country or 'world'}",
    label_visibility="collapsed",
)

if rank_scope == "Countries":
    board = country_rank
    scope_label = "countries"
else:
    board = local_rank if rank_scope == "India" else world_rank
    scope_label = "Indian cities" if rank_scope == "India" else "world cities"

if not board.get("available"):
    st.caption("The comparison board could not be loaded right now. The rest of the page is unaffected.")
else:
    rows = board["rows"]
    position = board.get("position")
    total = board["total"]
    cleanest = board["cleanest"]
    dirtiest = board["dirtiest"]

    subject = country if rank_scope == "Countries" and country else city
    if position:
        summary = (
            f"<b>{subject}</b> is <b>{position}{'st' if position % 10 == 1 and position != 11 else 'nd' if position % 10 == 2 and position != 12 else 'rd' if position % 10 == 3 and position != 13 else 'th'}</b> "
            f"cleanest of {total} {scope_label}."
        )
    else:
        summary = f"{total} {scope_label} ranked cleanest first."

    def rank_rows(items) -> str:
        peak = max(row["aqi"] for row in rows) or 1.0
        html = []
        for row in items:
            width = max(3.0, min(100.0, row["aqi"] / peak * 100))
            if "city" in row:
                sub = row["city"]
            elif row.get("cities", 0) > 1:
                sub = f"{row['cities']} cities"
            else:
                sub = row.get("country", "")
            html.append(
                f'<div class="rank-row{" me" if row.get("is_selected") else ""}">'
                f'<span class="rank-n">{row["rank"]:02d}</span>'
                f'<span class="rank-name">{row["name"]}<small>{sub}</small></span>'
                f'<span class="rank-bar"><i style="width:{width:.0f}%;background:{row["band"]["color"]}"></i></span>'
                f'<span class="rank-aqi">{row["aqi"]:.0f}</span>'
                "</div>"
            )
        return "".join(html)

    half = (len(rows) + 1) // 2
    html_block(
        f"""
        <div class="section-body rank-body">
          <div class="panel rank-panel">
            <div class="rank-summary">
              <div>{summary}</div>
              <div class="rank-extremes">
                <span><i style="background:{cleanest['band']['color']}"></i>Cleanest · {cleanest['name']} {cleanest['aqi']:.0f}</span>
                <span><i style="background:{dirtiest['band']['color']}"></i>Highest · {dirtiest['name']} {dirtiest['aqi']:.0f}</span>
              </div>
            </div>
            <div class="rank-cols">
              <div class="rank-col">{rank_rows(rows[:half])}</div>
              <div class="rank-col">{rank_rows(rows[half:])}</div>
            </div>
            <div class="panel-foot">Cleanest first · {total} {scope_label} · {'Sample board — live ranking provider unavailable, values labelled for layout preview only.' if rank_sample else ('One representative city per country · Open-Meteo CAMS estimates, refreshed every 15 minutes.' if rank_scope == 'Countries' else 'Open-Meteo CAMS estimates, refreshed every 15 minutes.')}</div>
          </div>
        </div>
        """
    )

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
    "Best time": "When is the cleanest time to go outside today?",
    "Tomorrow?": "Will the air be better tomorrow?",
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
                    "the forecast, how this city compares, or what to do with your afternoon.",
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
