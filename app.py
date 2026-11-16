"""AirSense — an atmospheric intelligence platform.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src import ui
from src.air_quality import fetch_air_quality, fetch_cpcb_city_readings, search_locations
from src.aqi import (
    ACTIVITIES,
    AQI_BANDS,
    aqi_band,
    aqi_trend,
    best_windows,
    compass,
    daily_heatmap,
    daily_summary,
    dominant_pollutant,
    exposure_curve,
    exposure_stats,
    format_time,
    forecast_frame,
    is_missing,
    seven_day_stats,
    us_aqi_from_pm25,
    who_comparisons,
)
from src.chat import answer_simple_question, ask_hosted_model, ask_local_ollama, list_local_models
from src.chemistry import simulate_ozone_response
from src.demo import demo_payload
from src.model import train_pm25_model
from src.styles import APP_CSS

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AirSense — Atmospheric Intelligence",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded",
)

POLLUTANT_LABELS = {
    "pm2_5": "PM₂.₅",
    "pm10": "PM₁₀",
    "nitrogen_dioxide": "NO₂",
    "sulphur_dioxide": "SO₂",
    "ozone": "O₃",
    "carbon_monoxide": "CO",
}
POLLUTANT_UNITS = {
    "pm2_5": "µg/m³",
    "pm10": "µg/m³",
    "nitrogen_dioxide": "µg/m³",
    "sulphur_dioxide": "µg/m³",
    "ozone": "µg/m³",
    "carbon_monoxide": "µg/m³",
}
REQUIRED_HOURLY = [
    "us_aqi",
    "european_aqi",
    "pm2_5",
    "pm10",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "carbon_monoxide",
]

# ---------------------------------------------------------------------------
# Cached data + model helpers
# ---------------------------------------------------------------------------


@st.cache_data(ttl=86_400, show_spinner=False)
def cached_search(query: str):
    return search_locations(query)


@st.cache_data(ttl=900, show_spinner=False)
def load_air_quality(latitude: float, longitude: float):
    return fetch_air_quality(latitude, longitude)


@st.cache_data(ttl=1_800, show_spinner=False)
def load_cpcb(city: str):
    return fetch_cpcb_city_readings(city)


@st.cache_data(ttl=900, show_spinner=False)
def cached_model(latitude: float, longitude: float, demo: bool, _hourly: pd.DataFrame):
    return train_pm25_model(_hourly)


@st.cache_data(ttl=300, show_spinner=False)
def cached_ollama_models():
    return list_local_models()


# ---------------------------------------------------------------------------
# Chart theme
# ---------------------------------------------------------------------------


def theme_chart(chart: alt.Chart, height: int = 320):
    return (
        chart.properties(height=height, background="transparent")
        .configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor="#93A2B2",
            titleColor="#6F7F90",
            gridColor="rgba(244,237,224,.06)",
            domainColor="rgba(244,237,224,.12)",
            tickColor="rgba(244,237,224,.12)",
            labelFont="JetBrains Mono",
            titleFont="JetBrains Mono",
            labelFontSize=9,
            titleFontSize=9,
            titleFontWeight=500,
            titlePadding=8,
        )
        .configure_legend(
            labelColor="#93A2B2",
            titleColor="#6F7F90",
            labelFont="JetBrains Mono",
            titleFont="JetBrains Mono",
            labelFontSize=9,
            titleFontSize=9,
            symbolSize=70,
        )
    )


def forecast_chart(frame: pd.DataFrame, threshold: int) -> alt.Chart:
    domain = [band["short"] for band in AQI_BANDS]
    palette = [band["color"] for band in AQI_BANDS]
    upper = max(65.0, float(frame["us_aqi"].max()) * 1.22)

    base = alt.Chart(frame).encode(
        x=alt.X(
            "time:T",
            title=None,
            axis=alt.Axis(
                format="%a %H:%M",
                tickCount=8,
                labelAngle=0,
                grid=False,
                labelFontSize=8.5,
            ),
        ),
        y=alt.Y(
            "us_aqi:Q",
            title="US AQI",
            scale=alt.Scale(domain=[0, upper], nice=True),
            axis=alt.Axis(labelFontSize=8.5),
        ),
        tooltip=[
            alt.Tooltip("time:T", title="Time", format="%a %d %b · %H:%M"),
            alt.Tooltip("us_aqi:Q", title="US AQI", format=".0f"),
            alt.Tooltip("label:N", title="Category"),
        ],
    )

    gradient = alt.Gradient(
        gradient="linear",
        x1=1,
        x2=1,
        y1=1,
        y2=0,
        stops=[
            alt.GradientStop(color="rgba(111,227,214,0)", offset=0),
            alt.GradientStop(color="rgba(111,227,214,.20)", offset=1),
        ],
    )

    area = base.mark_area(interpolate="monotone", color=gradient)
    line = base.mark_line(interpolate="monotone", color="#F4EDE0", strokeWidth=1.9)
    points = base.mark_circle(size=52, stroke="#060B12", strokeWidth=1.1).encode(
        color=alt.Color(
            "category:N",
            scale=alt.Scale(domain=domain, range=palette),
            legend=None,
        )
    )
    rule = (
        alt.Chart(pd.DataFrame({"threshold": [threshold]}))
        .mark_rule(color="#FF8069", strokeDash=[4, 4], strokeWidth=1)
        .encode(y="threshold:Q")
    )
    return theme_chart(area + line + points + rule, height=330)


def backtest_chart(frame: pd.DataFrame) -> alt.Chart:
    melted = frame.melt(
        id_vars=["time"],
        value_vars=["Observed", "Model", "Persistence"],
        var_name="Series",
        value_name="PM25",
    )
    chart = (
        alt.Chart(melted)
        .mark_line(strokeWidth=1.8, interpolate="monotone")
        .encode(
            x=alt.X("time:T", title=None, axis=alt.Axis(format="%d %b", tickCount=7, labelAngle=0)),
            y=alt.Y("PM25:Q", title="PM₂.₅ (µg/m³)"),
            color=alt.Color(
                "Series:N",
                scale=alt.Scale(
                    domain=["Observed", "Model", "Persistence"],
                    range=["#F4EDE0", "#6FE3D6", "#6F7F90"],
                ),
                legend=alt.Legend(orient="top", title=None),
            ),
            strokeDash=alt.StrokeDash(
                "Series:N",
                scale=alt.Scale(
                    domain=["Observed", "Model", "Persistence"],
                    range=[[1, 0], [1, 0], [5, 4]],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("time:T", title="Time", format="%d %b · %H:%M"),
                alt.Tooltip("Series:N", title="Series"),
                alt.Tooltip("PM25:Q", title="PM₂.₅", format=".1f"),
            ],
        )
    )
    return theme_chart(chart, height=300)


def importance_chart(importance: dict) -> alt.Chart:
    frame = (
        pd.DataFrame({"Feature": list(importance.keys()), "Importance": list(importance.values())})
        .sort_values("Importance", ascending=True)
        .reset_index(drop=True)
    )
    bars = (
        alt.Chart(frame)
        .mark_bar(cornerRadius=4, height=16)
        .encode(
            x=alt.X(
                "Importance:Q",
                title="Relative importance",
                scale=alt.Scale(domain=[0, 1]),
                axis=alt.Axis(format=".0%", tickCount=5),
            ),
            y=alt.Y("Feature:N", title=None, sort=None),
            color=alt.Color(
                "Importance:Q",
                scale=alt.Scale(range=["#35586B", "#6FE3D6", "#E9BB78"]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Feature:N", title="Feature"),
                alt.Tooltip("Importance:Q", title="Importance", format=".1%"),
            ],
        )
    )
    labels = bars.mark_text(align="left", dx=5, color="#93A2B2", font="JetBrains Mono", fontSize=8.5).encode(
        text=alt.Text("Importance:Q", format=".0%")
    )
    return theme_chart(bars + labels, height=260)


def surface_chart(frame: pd.DataFrame) -> alt.Chart:
    chart = (
        alt.Chart(frame)
        .mark_rect(cornerRadius=2, stroke="#08111A", strokeWidth=.6)
        .encode(
            x=alt.X("Sunlight:Q", title="Relative sunlight", scale=alt.Scale(domain=[0, 100])),
            x2=alt.X2("Sunlight end:Q"),
            y=alt.Y("VOC:Q", title="VOC input", scale=alt.Scale(domain=[0, 100])),
            y2=alt.Y2("VOC end:Q"),
            color=alt.Color(
                "Index:Q",
                title="Index",
                scale=alt.Scale(domain=[0, 35, 70, 100], range=["#0B1422", "#2BB3A3", "#E9BB78", "#F18470"]),
                legend=alt.Legend(orient="right", gradientLength=150),
            ),
            tooltip=[
                alt.Tooltip("Sunlight:Q", title="Sunlight"),
                alt.Tooltip("VOC:Q", title="VOC input"),
                alt.Tooltip("Index:Q", title="Response index", format=".0f"),
            ],
        )
    )
    return theme_chart(chart, height=330)


def exposure_chart(pm25, ventilation: float, minutes: int, max_minutes: int = 240) -> alt.Chart:
    curve = exposure_curve(pm25, ventilation, max_minutes=max_minutes, step=10)
    area = (
        alt.Chart(curve)
        .mark_area(color="#6FE3D6", opacity=.10, interpolate="monotone")
        .encode(
            x=alt.X("minutes:Q", title="Minutes exposed"),
            y=alt.Y("dose_ug:Q", title="Inhaled PM₂.₅ (µg)"),
        )
    )
    dose = (
        alt.Chart(curve)
        .mark_line(color="#6FE3D6", strokeWidth=2, interpolate="monotone")
        .encode(
            x="minutes:Q",
            y="dose_ug:Q",
            tooltip=[
                alt.Tooltip("minutes:Q", title="Minutes"),
                alt.Tooltip("dose_ug:Q", title="Inhaled dose", format=".1f"),
            ],
        )
    )
    reference = (
        alt.Chart(curve)
        .mark_line(color="#E9BB78", strokeDash=[5, 4], strokeWidth=1.4, interpolate="monotone")
        .encode(x="minutes:Q", y="reference_ug:Q")
    )
    marker = (
        alt.Chart(pd.DataFrame({"minutes": [minutes]}))
        .mark_rule(color="#FF8069", strokeDash=[3, 3], strokeWidth=1)
        .encode(x="minutes:Q")
    )
    return theme_chart(area + dose + reference + marker, height=300)


# ---------------------------------------------------------------------------
# Session defaults
# ---------------------------------------------------------------------------

# A complete local fallback keeps the dashboard useful when a preview sandbox
# cannot reach the geocoder. Live data still replaces this reading whenever the
# provider is available.
DEFAULT_LOCATION = {
    "id": "default-bengaluru",
    "name": "Bengaluru",
    "country": "India",
    "country_code": "IN",
    "admin1": "Karnataka",
    "latitude": 12.9716,
    "longitude": 77.5946,
    "timezone": "Asia/Kolkata",
}

if "location_query" not in st.session_state:
    st.session_state["location_query"] = DEFAULT_LOCATION["name"]
if "selected_location" not in st.session_state:
    st.session_state["selected_location"] = DEFAULT_LOCATION.copy()
if "location_matches" not in st.session_state:
    # Do not hold the first page render on a network lookup. Search runs when
    # the user asks for it, while the default coordinates remain immediately
    # available for the live AQI request or deterministic sample fallback.
    st.session_state["location_matches"] = []


def handle_quick_city():
    choice = st.session_state.get("quick_city")
    if choice:
        st.session_state["location_query"] = choice
        st.session_state["auto_search"] = True


def reset_location():
    st.session_state["location_query"] = "Bengaluru"
    st.session_state["auto_search"] = True


# ---------------------------------------------------------------------------
# Sidebar · observation point
# ---------------------------------------------------------------------------

with st.sidebar:
    st.html(ui.brand_markup())
    st.html('<div class="side-label">01 · Observation point</div>')
    st.html('<div class="side-title">Where are we reading?</div>')

    st.text_input(
        "Search city or place",
        key="location_query",
        placeholder="Delhi, London, São Paulo…",
        label_visibility="collapsed",
    )
    search_clicked = st.button("Search locations", type="primary", width="stretch", key="search_location")
    st.button("Reset to Bengaluru", width="stretch", key="reset_location", on_click=reset_location)

    st.pills(
        "Quick jump",
        ["Bengaluru", "Delhi", "Mumbai", "London", "New York"],
        key="quick_city",
        on_change=handle_quick_city,
        label_visibility="collapsed",
        width="stretch",
    )

    auto_search = st.session_state.pop("auto_search", False)
    if search_clicked or auto_search:
        try:
            st.session_state["location_matches"] = cached_search(st.session_state["location_query"])
            st.session_state.pop("location_error", None)
        except Exception as exc:
            st.session_state["location_matches"] = []
            st.session_state["location_error"] = str(exc)

    if st.session_state.get("location_error"):
        st.error(st.session_state["location_error"])

    matches = st.session_state.get("location_matches", [])
    selected = st.session_state.get("selected_location")

    if not matches and not selected:
        try:
            fallback = cached_search("Bengaluru")
            st.session_state["location_matches"] = fallback
            matches = fallback
        except Exception:
            matches = []

    if not matches and selected:
        st.caption("Showing the last valid observation point.")
    elif not matches:
        st.error("No location selected. Search for a city to load air-quality data.")
        st.stop()

    if matches:
        labels = []
        for item in matches:
            label = ", ".join(
                part for part in [item.get("name", ""), item.get("admin1", ""), item.get("country", "")] if part
            )
            if label in labels:
                label = f"{label} · {float(item.get('latitude', 0)):.2f}, {float(item.get('longitude', 0)):.2f}"
            labels.append(label)

        default_index = 0
        if selected:
            for index, item in enumerate(matches):
                if item.get("id") == selected.get("id") or (
                    item.get("name") == selected.get("name") and item.get("country") == selected.get("country")
                ):
                    default_index = index
                    break

        selected_label = st.selectbox("Select matching place", labels, index=default_index)
        selected = matches[labels.index(selected_label)]
        st.session_state["selected_location"] = selected
        st.caption(
            f"Resolved automatically · {selected.get('timezone', 'local timezone')} · "
            f"{float(selected.get('latitude', 0)):.2f}, {float(selected.get('longitude', 0)):.2f}"
        )

    city = selected.get("name", "Unknown")
    country = selected.get("country", "")
    country_code = (selected.get("country_code") or "").upper()
    latitude = float(selected.get("latitude", 0.0))
    longitude = float(selected.get("longitude", 0.0))
    timezone_name = selected.get("timezone", "local timezone")

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

demo_mode = False
data_error = ""
try:
    with st.spinner("Reading the atmosphere…"):
        payload = load_air_quality(latitude, longitude)
except Exception as exc:
    payload = demo_payload(city, country)
    demo_mode = True
    data_error = f"{type(exc).__name__}: {exc}"

hourly = payload["hourly"].copy()
current = payload.get("current", {}) or {}
if hourly is None or hourly.empty or "time" not in hourly.columns:
    st.error("The data provider returned no hourly observations.")
    st.stop()

hourly["time"] = pd.to_datetime(hourly["time"], errors="coerce")
for column in REQUIRED_HOURLY:
    if column in hourly.columns:
        hourly[column] = pd.to_numeric(hourly[column], errors="coerce")

aqi_is_derived = False
hourly_aqi_derived = False
if "us_aqi" not in hourly.columns or hourly["us_aqi"].isna().all():
    if "pm2_5" in hourly.columns:
        hourly["us_aqi"] = hourly["pm2_5"].apply(us_aqi_from_pm25)
        hourly_aqi_derived = True
    else:
        hourly["us_aqi"] = pd.NA
if "pm2_5" in hourly.columns:
    hourly["us_aqi"] = hourly["us_aqi"].fillna(hourly["pm2_5"].apply(us_aqi_from_pm25))

current_time = current.get("time")
if is_missing(current_time):
    current_time = hourly["time"].max()
reference_time = pd.to_datetime(current_time, errors="coerce")
if pd.isna(reference_time):
    reference_time = hourly["time"].max()


def resolve_current(key: str):
    value = current.get(key)
    if value is not None and not is_missing(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            pass
    if key in hourly.columns:
        subset = hourly[hourly["time"] <= reference_time][key].dropna()
        if not subset.empty:
            return float(subset.iloc[-1])
    return None


current_values = {key: resolve_current(key) for key in REQUIRED_HOURLY}
current_aqi = current_values.get("us_aqi")
if current_aqi is None and current_values.get("pm2_5") is not None:
    current_aqi = us_aqi_from_pm25(current_values["pm2_5"])
    hourly_aqi_derived = True
aqi_is_derived = is_missing(current.get("us_aqi")) and hourly_aqi_derived

band = aqi_band(current_aqi)
aqi_source = "Provider-calculated US AQI · Open-Meteo"
if demo_mode:
    aqi_source = "Sample atmosphere · derived US AQI"
elif aqi_is_derived:
    aqi_source = "Indicative US AQI · derived from PM₂.₅"

trend = aqi_trend(hourly, reference_time)
forecast = forecast_frame(hourly, reference_time, hours=48)
if forecast.empty:
    forecast = forecast_frame(hourly, None, hours=48)
forecast_24 = forecast.head(24)
windows = best_windows(forecast["time"], forecast["us_aqi"], window=3, count=3, horizon=24)
heatmap = daily_heatmap(hourly, reference_time, days=7)
daily = daily_summary(hourly, reference_time, days=7)
weekly = seven_day_stats(hourly, reference_time, days=7)
who_rows = who_comparisons(current_values)
who_lookup = {row["key"]: row["ratio"] for row in who_rows}
dominant = dominant_pollutant(current_values)

peak_value = None
peak_when = ""
if not forecast_24.empty:
    peak_row = forecast_24.sort_values("us_aqi", ascending=False).iloc[0]
    peak_value = float(peak_row["us_aqi"])
    peak_when = peak_row["time"].strftime("%a %H:%M")

recent = hourly[hourly["time"] <= reference_time].tail(24)

# ---------------------------------------------------------------------------
# Sidebar · live reading, watch level, assistant, sources
# ---------------------------------------------------------------------------

with st.sidebar:
    st.html(ui.sidebar_aqi_html(current_aqi, band, aqi_source))

    st.html('<div class="side-label">02 · AQI watch</div>')
    threshold = st.slider(
        "Alert me above this US AQI",
        50,
        300,
        100,
        step=10,
        key="watch_threshold",
        help="Used for the watch banner and the dashed line on the 48-hour AQI forecast.",
    )
    st.html(
        f'<div class="side-copy">Your watch level is <b>{int(threshold)} US AQI</b>. '
        "The banner appears when current or forecast air crosses it.</div>",
    )

    st.divider()
    st.html('<div class="side-label">03 · Research assistant</div>')
    chat_mode = st.selectbox(
        "Assistant provider",
        ["Quick answers · built in", "Local LLM · Ollama", "Hosted API"],
        key="assistant_provider",
        label_visibility="collapsed",
    )
    if str(chat_mode).startswith("Quick"):
        st.caption("Answers everyday air-quality questions instantly. No account, key or model download needed.")
    elif str(chat_mode).startswith("Local"):
        st.caption("Runs locally through Ollama when available. No hosted key required.")
    else:
        st.caption("Uses an OpenAI-compatible endpoint. Requires a configured API key.")

    st.divider()
    if st.button("Refresh live data", width="stretch", key="refresh_live_data"):
        load_air_quality.clear()
        load_cpcb.clear()
        cached_model.clear()
        st.rerun()

    st.html(
        f"""
        <div class="side-note">
          <b>DATA</b><br>
          Open-Meteo · CAMS model<br>
          {ui.esc(timezone_name)} · {ui.esc(payload.get("timezone_abbreviation", "")) or "local"}<br><br>
          <b>AQI SCALE</b><br>
          US EPA categories · provider values<br>
          WHO 2021 reference comparisons<br><br>
          <b>MODELS</b><br>
          Random Forest baseline<br>
          Rule-based / local / hosted assistant
        </div>
        """,
    )

# ---------------------------------------------------------------------------
# Visual system
# ---------------------------------------------------------------------------

st.html(f"<style>{APP_CSS}</style>")

# ---------------------------------------------------------------------------
# Top bar + hero
# ---------------------------------------------------------------------------

st.html(ui.topbar_html(city, country, not demo_mode))

updated_label = format_time(current_time)

# ---------------------------------------------------------------------------
# Interactive global AQI layer
# ---------------------------------------------------------------------------

globe_path = Path(__file__).parent / "globe.html"
if globe_path.exists():
    def globe_number(value):
        """Return a finite JSON-friendly number, or ``None`` for missing data."""
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if pd.notna(number) and math.isfinite(number) else None

    globe_state = {
        "selected": {
            "name": city,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "aqi": globe_number(current_aqi),
            "pm25": globe_number(current_values.get("pm2_5")),
            "category": band.get("name", "Unavailable"),
            "color": band.get("color", "#8795A6"),
            "updated": updated_label,
            "is_demo": demo_mode,
        }
    }
    globe_state_json = json.dumps(globe_state, ensure_ascii=False).replace("</", "<\\/")
    globe_html = globe_path.read_text(encoding="utf-8").replace(
        "__AIRSENSE_GLOBE_STATE__", globe_state_json
    )
    components.html(globe_html, height=640, scrolling=False)
else:
    st.info("The interactive AQI globe could not be loaded.")

hero_left = f"""
<div class="hero-left">
  <div class="eyebrow">Atmospheric intelligence · {ui.esc(country)}</div>
  <h1 class="hero-title">The air,<br><em>decoded.</em></h1>
  <p class="hero-lede">
    Read the atmosphere as a living system. Track how pollutants rise and travel,
    compare the reading with <b>WHO references</b>, find your cleanest hour, and see
    what the <b>next 48 hours</b> may hold — all in one instrument.
  </p>
  <div class="hero-meta">
    <span class="hero-chip accent"><strong>{ui.esc(band["name"])}</strong> · {ui.fmt(current_aqi)} US AQI</span>
    <span class="hero-chip">{ui.esc(city)}<strong> · {ui.esc(country)}</strong></span>
    <span class="hero-chip">Updated <strong>{ui.esc(updated_label)}</strong></span>
  </div>
  <div class="hero-coord">{ui.esc(compass(latitude, longitude))} · {ui.esc(timezone_name)} · live model layer</div>
</div>
"""
hero_right = ui.gauge_html(current_aqi, band, trend, aqi_source, updated_label)
st.html(f'<div class="hero-grid">{hero_left}{hero_right}</div>')

if demo_mode:
    st.html(ui.demo_banner(data_error))

alert_active = (
    (current_aqi is not None and float(current_aqi) >= threshold)
    or (peak_value is not None and peak_value >= threshold)
)
if alert_active:
    st.html(ui.alert_banner(current_aqi, band, peak_value, threshold, peak_when))

# ---------------------------------------------------------------------------
# KPI strip
# ---------------------------------------------------------------------------

kpi_columns = st.columns(4, gap="small")
kpi_specs = [
    ("pm2_5", "PM₂.₅", "#C9795E", "Primary fine-particle signal"),
    ("pm10", "PM₁₀", "#D4B06B", "Coarse-particle signal"),
    ("nitrogen_dioxide", "NO₂", "#86B9A5", "Traffic and combustion tracer"),
    ("ozone", "O₃", "#A5A0C7", "Photochemical product"),
]
for column, (key, label, accent, note) in zip(kpi_columns, kpi_specs):
    with column:
        st.html(
            ui.kpi_card(
                label,
                current_values.get(key),
                POLLUTANT_UNITS[key],
                accent,
                ratio=who_lookup.get(key),
                spark_values=recent[key] if key in recent.columns else [],
                footnote=note,
            ),
        )

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tracker_tab, health_tab, chemistry_tab, prediction_tab, assistant_tab, about_tab = st.tabs(
    [
        "01 · AQI Tracker",
        "02 · Health & Exposure",
        "03 · Chemistry Lab",
        "04 · Prediction Lab",
        "05 · Research Assistant",
        "06 · About",
    ]
)

# ===========================================================================
# 01 · AQI TRACKER
# ===========================================================================

with tracker_tab:
    st.html(
        ui.section_head(
            "NOW · HEALTH & COMPOSITION",
            "What the number means",
            "An AQI category is a communication tool, not a diagnosis. This reading combines the current category with the pollutant loads that produced it.",
        ),
    )
    health_col, composition_col = st.columns([1.05, 1], gap="medium")
    with health_col:
        st.html(ui.health_card(band, current_aqi, aqi_source))
    with composition_col:
        st.html(ui.composition_card(who_rows, dominant))

    st.html(
        ui.section_head(
            "NEXT 48 HOURS · PROVIDER FORECAST",
            "The air ahead",
            "Hourly US AQI from the provider's CAMS-based forecast, coloured by category. The dashed line is your watch threshold.",
        ),
    )
    if forecast.empty:
        st.info("No forward hourly AQI is available for this location right now.")
    else:
        st.altair_chart(forecast_chart(forecast, threshold), use_container_width=True, theme=None)
        st.caption(
            "Provider-calculated US AQI · forecast, not a measurement. Forecast skill falls with distance; "
            "use the shape of the curve, not a single hour, to plan."
        )
        if windows:
            st.html(
                ui.section_head(
                    "RELATIVE CLEANEST WINDOWS",
                    "Choose your moment",
                    "Lowest 3-hour rolling mean in the next 24 hours. Relative windows, not guarantees.",
                ),
            )
            window_columns = st.columns(len(windows), gap="small")
            for index, (column, window) in enumerate(zip(window_columns, windows), start=1):
                with column:
                    st.html(ui.window_card_html(window, index))

    st.html(
        ui.section_head(
            "SEVEN DAYS · HOURLY HISTORY",
            "A week in breath",
            "Each cell is one hour. Scan for the rhythm: traffic peaks, evening stagnation, clean afternoons, and the days that never clear.",
        ),
    )
    stats_html = ""
    if weekly.get("available"):
        mean_band = aqi_band(weekly["mean"])
        peak_band = aqi_band(weekly["peak"])
        peak_day = "—"
        if not daily.empty:
            peak_row = daily.loc[daily["peak_aqi"].idxmax()]
            peak_day = str(peak_row["date_label"])
        stats_html = ui.stats_grid(
            [
                ("7-DAY MEAN", f'{weekly["mean"]:.0f}', f'{mean_band["short"]} · US AQI', mean_band["color"]),
                ("7-DAY PEAK", f'{weekly["peak"]:.0f}', f'peak on {peak_day}', peak_band["color"]),
                (
                    "CLEAN HOURS",
                    f'{weekly["clean_hours"]}',
                    f'of {weekly["total_hours"]} hours ≤ 50 · {weekly["clean_share"]:.0f}%',
                    "#6FE3D6",
                ),
                (
                    "24H TREND",
                    f'{trend["delta"]:+.0f}%' if trend.get("available") else "—",
                    trend.get("text", "Trend unavailable"),
                    "#6FE3D6" if trend.get("direction") == "down" else ("#FF8069" if trend.get("direction") == "up" else "#93A2B2"),
                ),
            ]
        )
    history_html = f'<div class="history-layout">{ui.heatmap_html(heatmap)}{stats_html}</div>' if stats_html else ui.heatmap_html(heatmap)
    st.html(history_html)

    st.html(
        ui.section_head(
            "REFERENCE CHECK · WHO 2021",
            "Measured against the guidelines",
            "A relative load view: how each pollutant compares with its WHO reference value. This is context, not a compliance verdict.",
        ),
    )
    st.html(ui.who_panel(who_rows))

    with st.expander("Recent hourly observations, index comparison & data export"):
        if not forecast.empty:
            us_value = current_values.get("us_aqi")
            eu_value = current_values.get("european_aqi")
            st.html(
                ui.stats_grid(
                    [
                        ("US AQI · NOW", ui.fmt(us_value), "Provider scale", band["color"]),
                        ("EUROPEAN AQI · NOW", ui.fmt(eu_value), "Different scale · not comparable", "#93A2B2"),
                        ("PROVIDER", "OPEN-METEO", "CAMS-based model layer", "#6FE3D6"),
                        ("REFERENCE", "WHO 2021", "24h / 8h guidelines", "#E9BB78"),
                    ]
                ),
            )
            st.caption(
                "US AQI and European AQI are different index systems and should not be compared numerically. "
                "Neither is India's CPCB National AQI."
            )

        display = hourly.copy()
        available = [column for column in ["time"] + REQUIRED_HOURLY if column in display.columns]
        display = display[available].tail(24).sort_values("time", ascending=False)
        display["time"] = display["time"].dt.strftime("%d %b · %H:%M")
        display = display.rename(
            columns={
                "time": "Time",
                "us_aqi": "US AQI",
                "european_aqi": "EU AQI",
                "pm2_5": "PM₂.₅",
                "pm10": "PM₁₀",
                "nitrogen_dioxide": "NO₂",
                "sulphur_dioxide": "SO₂",
                "ozone": "O₃",
                "carbon_monoxide": "CO",
            }
        )
        st.dataframe(display, width="stretch", hide_index=True)
        csv = hourly.to_csv(index=False).encode("utf-8")
        slug = "".join(character if character.isalnum() else "-" for character in city.lower()).strip("-") or "location"
        st.download_button(
            "Download full dataset (CSV)",
            data=csv,
            file_name=f"airsense-{slug}-{reference_time:%Y%m%d-%H%M}.csv",
            mime="text/csv",
            width="stretch",
        )
        if demo_mode:
            st.caption("This export contains sample data, not observations.")

        st.markdown("---")
        st.markdown("**India · CPCB station observations**")
        st.caption(
            "Station-level pollutant observations through a public mirror. This is not an official CPCB AQI feed; "
            "AirSense never derives or invents a National AQI from these rows or from CAMS model concentrations."
        )
        if country_code == "IN" or country.lower() == "india":
            if st.button("Load station observations", key="load_cpcb_button"):
                st.session_state["cpcb_payload"] = {"city": city, "data": load_cpcb(city)}
            stored = st.session_state.get("cpcb_payload")
            if stored and stored.get("city") == city:
                cpcb_data = stored["data"]
                if cpcb_data.get("records"):
                    st.dataframe(pd.DataFrame(cpcb_data["records"]), width="stretch", hide_index=True)
                else:
                    st.warning(cpcb_data.get("message", "Station observations are temporarily unavailable."))
                st.caption(cpcb_data.get("message", ""))
            else:
                st.caption("Load on demand to avoid a slow external request on every interaction.")
        else:
            st.caption("Station observations are available for Indian locations only.")

# ===========================================================================
# 02 · HEALTH & EXPOSURE
# ===========================================================================

with health_tab:
    st.html(
        ui.section_head(
            "PERSONAL EXPOSURE LAB",
            "How much are you breathing in?",
            "Estimate the mass of fine particles you inhale during an activity, then compare it with a WHO-aligned reference dose. Indicative, not medical advice.",
        ),
    )

    control_col, result_col = st.columns([0.9, 1.35], gap="large")

    with control_col:
        activity = st.selectbox("Activity", list(ACTIVITIES.keys()), index=1)
        minutes = st.slider("Minutes exposed", 10, 240, 60, step=10)
        scenario = st.radio(
            "Air quality scenario",
            ["Current PM₂.₅", "Next 24h average"],
            horizontal=True,
        )

        current_pm25 = current_values.get("pm2_5")
        future_pm25 = None
        if "pm2_5" in hourly.columns:
            future = hourly[hourly["time"] >= reference_time].head(24)["pm2_5"].dropna()
            if not future.empty:
                future_pm25 = float(future.mean())

        if scenario.startswith("Current"):
            exposure_pm25 = current_pm25
            scenario_label = "Current PM₂.₅"
        else:
            exposure_pm25 = future_pm25 if future_pm25 is not None else current_pm25
            scenario_label = "Next-24h mean PM₂.₅"

        ventilation = ACTIVITIES[activity]["ventilation"]
        stats = exposure_stats(exposure_pm25, minutes, ventilation)
        st.caption(
            f"{ACTIVITIES[activity]['note']} Scenario concentration: "
            f"{ui.fmt(exposure_pm25)} µg/m³ ({scenario_label})."
        )

    with result_col:
        ratio = stats["ratio"]
        ratio_band_color = "#3ECF8E" if ratio <= 1 else ("#F5C451" if ratio <= 2 else ("#F59E5B" if ratio <= 4 else "#EF6E6E"))
        metric_columns = st.columns(3, gap="small")
        with metric_columns[0]:
            st.html(
                ui.exposure_metric(
                    "INHALED PM₂.₅",
                    f'{stats["dose_ug"]:.1f}',
                    "µg",
                    f'{minutes} min · {ventilation:.0f} L/min',
                    "#FF8069",
                ),
            )
        with metric_columns[1]:
            st.html(
                ui.exposure_metric(
                    "AIR BREATHED",
                    f'{stats["volume_m3"]:.2f}',
                    "m³",
                    "Approximate ventilation volume",
                    "#6FE3D6",
                ),
            )
        with metric_columns[2]:
            st.html(
                ui.exposure_metric(
                    "VS WHO REFERENCE",
                    f'{ratio:.1f}×',
                    "",
                    f'Reference dose {stats["reference_dose_ug"]:.1f} µg',
                    ratio_band_color,
                ),
            )

        if ratio <= 1:
            guidance = "Within the WHO-aligned reference dose for this activity and duration. Keep in mind that no threshold is a guarantee of no effect."
        elif ratio <= 2:
            guidance = "Above the WHO-aligned reference dose. Consider shortening the activity, lowering intensity, or choosing a cleaner window."
        elif ratio <= 4:
            guidance = "Several times the WHO-aligned reference dose. Sensitive groups should reduce outdoor exertion and consider indoor alternatives."
        else:
            guidance = "Well above the WHO-aligned reference dose. Move vigorous activity indoors or postpone it until the air improves."
        st.html(
            f"""
            <div class="glass-card mt-1" style="--accent:{ratio_band_color}">
              <div class="card-topline"><span class="card-kicker">READING THE DOSE</span><span class="mono-chip">INDICATIVE</span></div>
              <p class="index-summary" style="margin-top:.7rem;">{ui.esc(guidance)}</p>
              <div class="health-divider"></div>
              <p class="index-interpretation">Reference dose = 15 µg/m³ (WHO 24-hour PM₂.₅ guideline) × the volume of air you breathe during the scenario. It is not a personal medical assessment.</p>
            </div>
            """,
        )

    st.html(
        ui.section_head(
            "DOSE CURVE",
            "Duration changes everything",
            "The same air produces a larger inhaled dose the longer and harder you breathe. The dashed amber line is the WHO-aligned reference.",
        ),
    )
    st.altair_chart(
        exposure_chart(exposure_pm25, ventilation, minutes, max_minutes=240),
        use_container_width=True,
        theme=None,
    )
    st.caption(
        "Adult ventilation values are approximations (rest ≈ 6, light ≈ 12, moderate ≈ 25, vigorous ≈ 45 L/min). "
        "Real exposure depends on breathing pattern, particle composition, indoor/outdoor mixing and individual physiology."
    )

    st.html(
        ui.section_head(
            "TIMING · NEXT 24 HOURS",
            "Choose your moment",
            "The lowest relative AQI windows, paired with a practical intensity check.",
        ),
    )
    if windows:
        window_columns = st.columns(len(windows), gap="small")
        for index, (column, window) in enumerate(zip(window_columns, windows), start=1):
            with column:
                st.html(ui.window_card_html(window, index))
        safest = windows[0]
        if safest["mean"] <= 50:
            timing_note = "The cleanest window is in the Good band — a reasonable default for outdoor activity."
        elif safest["mean"] <= 100:
            timing_note = "The cleanest window is Moderate. Sensitive individuals may still prefer lower intensity."
        else:
            timing_note = "Even the cleanest window is above 100 US AQI. Shift vigorous activity indoors if you can."
        st.html(
            f"""
            <div class="glass-card mt-2">
              <div class="card-topline"><span class="card-kicker">PRACTICAL CHECK</span><span class="mono-chip">NEXT 24H</span></div>
              <p class="index-summary" style="margin-top:.7rem;">{ui.esc(timing_note)}</p>
              <div class="health-divider"></div>
              <div class="lever-list">
                <span>↳ Shift vigorous exercise toward the cleanest window.</span>
                <span>↳ Reduce duration or intensity when the category climbs.</span>
                <span>↳ A well-fitted N95/FFP2 respirator can reduce fine-particle inhalation when worn correctly.</span>
                <span>↳ Indoors, closing windows and using filtration can lower exposure during poor-air episodes.</span>
              </div>
              <div class="card-source">General exposure-reduction information, not medical advice. People with heart or lung conditions should follow their clinician's guidance.</div>
            </div>
            """,
        )
    else:
        st.info("No forward window is available for timing guidance right now.")

    st.html(
        ui.section_head(
            "CATEGORY GUIDE",
            "What each band asks of you",
            "US EPA category language, paraphrased for a public dashboard.",
        ),
    )
    guide_columns = st.columns(3, gap="small")
    for index, band_item in enumerate(AQI_BANDS):
        with guide_columns[index % 3]:
            st.html(
                f"""
                <div class="glass-card" style="--accent:{band_item["color"]};border-top:2px solid {band_item["color"]};margin-bottom:.6rem;">
                  <div class="card-topline"><span class="card-kicker">{band_item["low"]}–{band_item["high"]} US AQI</span><span class="band-badge" style="--accent:{band_item["color"]};--accent-rgb:{band_item["rgb"]}"><span class="band-dot"></span>{band_item["short"]}</span></div>
                  <p class="index-summary" style="font-size:.79rem;margin-top:.7rem;">{ui.esc(band_item["general"])}</p>
                </div>
                """,
            )

# ===========================================================================
# 03 · CHEMISTRY LAB
# ===========================================================================

with chemistry_tab:
    st.html(
        ui.section_head(
            "MOLECULAR FIELD GUIDE",
            "Meet the pollutants behind the numbers",
            "Select a pollutant to see its simplified structure, how it reaches the air, and which emission cuts make a difference.",
        ),
    )

    chemistry_lab_path = Path(__file__).parent / "chemistry_lab.html"
    if chemistry_lab_path.exists():
        def chemistry_number(value):
            try:
                number = float(value)
            except (TypeError, ValueError):
                return None
            return number if pd.notna(number) and math.isfinite(number) else None

        chemistry_state = {
            "readings": {
                key: chemistry_number(current_values.get(key))
                for key in ("pm2_5", "nitrogen_dioxide", "ozone", "sulphur_dioxide", "carbon_monoxide")
            }
        }
        chemistry_state_json = json.dumps(chemistry_state, ensure_ascii=False).replace("</", "<\\/")
        chemistry_html = chemistry_lab_path.read_text(encoding="utf-8").replace(
            "__AIRSENSE_CHEMISTRY_STATE__", chemistry_state_json
        )
        components.html(chemistry_html, height=570, scrolling=False)

    st.html(
        ui.section_head(
            "EXPERIMENT 001 · PHOTOCHEMISTRY",
            "Explore ozone formation",
            "Use the conceptual response surface to see how sunlight, NOx and VOCs can alter ozone chemistry.",
        ),
    )

    st.html(
        """
        <div class="chem-equation">
          NO₂ + hν → NO + O(³P)<br>
          O(³P) + O₂ + M → O₃ + M
          <small>Simplified ozone formation sequence · hν represents absorbed light · M is a third body</small>
        </div>
        """,
    )

    controls_col, output_col = st.columns([0.85, 1.2], gap="large")
    with controls_col:
        st.markdown("#### Experiment conditions")
        sunlight = st.slider(
            "Relative sunlight",
            0,
            100,
            65,
            help="Dimensionless teaching control; not measured irradiance.",
        )
        nox = st.slider(
            "NOx availability",
            0,
            100,
            50,
            help="Dimensionless teaching control; not a concentration.",
        )
        voc = st.slider(
            "VOC reactivity / availability",
            0,
            100,
            55,
            help="VOC mixtures differ substantially in reactivity.",
        )
        regime = st.selectbox(
            "Illustrative chemical regime",
            ["Balanced sensitivity", "VOC-limited tendency", "NOx-limited tendency"],
        )
        st.caption("All controls are relative teaching inputs, not measured atmospheric concentrations.")

    simulation = simulate_ozone_response(sunlight, nox, voc, regime)
    with output_col:
        st.markdown("#### Simulation response")
        st.html(
            ui.index_meter(simulation["index"], simulation["summary"], simulation["interpretation"]),
        )

    st.markdown("---")
    st.html(
        ui.section_head(
            "RESPONSE SURFACE",
            "Where the chemistry becomes nonlinear",
            "Hold NOx and the selected regime fixed while varying sunlight and VOC input. The colour is the dimensionless response index.",
        ),
    )
    surface_rows = []
    for light in range(0, 100, 10):
        for voc_value in range(0, 100, 10):
            surface_rows.append(
                {
                    "Sunlight": light,
                    "Sunlight end": light + 10,
                    "VOC": voc_value,
                    "VOC end": voc_value + 10,
                    "Index": simulate_ozone_response(light + 5, nox, voc_value + 5, regime)["index"],
                }
            )
    surface = pd.DataFrame(surface_rows)
    st.altair_chart(surface_chart(surface), use_container_width=True, theme=None)
    st.caption(f"NOx fixed at {nox} · regime: {regime}. This surface is conceptual; it is not a chemical transport model.")

    st.html(
        ui.section_head("PATHWAY", "How the reaction unfolds", "A four-step teaching narrative."),
    )
    st.html(
        ui.pathway_grid(
            [
                (
                    "01",
                    "NO₂ photolysis",
                    "Nitrogen dioxide absorbs sunlight and can split into nitric oxide and an oxygen atom.",
                ),
                (
                    "02",
                    "Ozone formation",
                    "Atomic oxygen can combine with O₂ in a three-body reaction to form O₃.",
                ),
                (
                    "03",
                    "VOC oxidation and NO recycling",
                    "VOC-derived peroxy radicals can convert NO to NO₂ without consuming ozone, supporting net ozone production in polluted air.",
                ),
                (
                    "04",
                    "Chemical regime matters",
                    "The ozone response to NOx and VOC changes is nonlinear and depends on radical chemistry, emissions, sunlight and transport.",
                ),
            ]
        ),
    )
    st.info(
        "Model scope: educational response surface only. It does not solve atmospheric chemical kinetics or predict real-world ozone. "
        "Quantitative prediction requires a chemically resolved mechanism, meteorology, emissions, boundary conditions and validation against observations."
    )

# ===========================================================================
# 04 · PREDICTION LAB
# ===========================================================================

with prediction_tab:
    st.html(
        ui.section_head(
            "EXPERIMENT 002 · MACHINE LEARNING",
            "A baseline for the next hour",
            "A Random Forest estimates next-hour PM₂.₅ from recent pollutant and time features. It is evaluated on a later, held-out slice and compared with a persistence baseline.",
        ),
    )

    try:
        result = cached_model(latitude, longitude, demo_mode, hourly)
        model_row_one = st.columns(2, gap="small")
        model_row_one[0].metric("Next-hour PM₂.₅", f'{result["prediction"]:.1f} µg/m³')
        model_row_one[1].metric("Model MAE", f'{result["mae"]:.1f} µg/m³', help="Mean absolute error on the held-out test slice.")
        model_row_two = st.columns(2, gap="small")
        model_row_two[0].metric(
            "Persistence MAE",
            f'{result["persistence_mae"]:.1f} µg/m³',
            help="Baseline that assumes next hour equals the current hour.",
        )
        model_row_two[1].metric("Test R²", f'{result["r2"]:.2f}', help="Variance explained on the held-out test slice; can be negative.")

        improvement = result["persistence_mae"] - result["mae"]
        if improvement > 0:
            st.caption(
                f"The model beats persistence by {improvement:.1f} µg/m³ MAE on the held-out slice. "
                f"Trained on {result['train_rows']} hourly rows; tested on {result['test_rows']}."
            )
        else:
            st.warning(
                "The model does not beat the persistence baseline on this slice. Treat the estimate as a baseline demonstration, not a forecasting win. "
                f"Trained on {result['train_rows']} rows; tested on {result['test_rows']}."
            )

        st.html(
            ui.section_head(
                "BACKTEST",
                "Observed, modelled, and the naive baseline",
                "The held-out test slice, ordered in time. A useful model should track the shape, not just the average.",
            ),
        )
        st.altair_chart(backtest_chart(result["backtest"]), use_container_width=True, theme=None)
        st.caption("Observed values are provider model estimates, not station measurements. The test slice is later in time than the training slice.")

        importance_col, notes_col = st.columns([1.25, 1], gap="large")
        with importance_col:
            st.markdown("#### Feature importance")
            st.altair_chart(importance_chart(result["feature_importance"]), use_container_width=True, theme=None)
        with notes_col:
            st.markdown("#### How to read this model")
            st.markdown(
                """
                - **Prediction:** estimated PM₂.₅ concentration for the next hour.
                - **MAE:** mean absolute error on the held-out test period.
                - **Persistence baseline:** assumes the next hour is identical to the current one.
                - **Test R²:** how much variance the model explains; values near or below zero mean it adds little over a mean predictor.
                - **Training data:** historical hourly CAMS model values and time features.
                """
            )
            st.info(
                "This is a baseline machine-learning estimate, not an official CPCB or EPA AQI forecast. "
                "Its performance depends on the available data and should always be compared with simple baselines."
            )

        with st.expander("Model card & limitations"):
            st.markdown(
                f"""
                | Component | Detail |
                |---|---|
                | Algorithm | Random Forest Regressor · 180 trees |
                | Features | PM₂.₅, PM₁₀, NO₂, SO₂, O₃, hour of day, day of week |
                | Target | Next-hour PM₂.₅ concentration (µg/m³) |
                | Split | Chronological 80 / 20 |
                | Training rows | {result["train_rows"]} |
                | Test rows | {result["test_rows"]} |
                | Test MAE | {result["mae"]:.2f} µg/m³ |
                | Persistence MAE | {result["persistence_mae"]:.2f} µg/m³ |
                | Test R² | {result["r2"]:.3f} |
                """
            )
            st.markdown(
                "The model does not use meteorology, emissions inventories, station observations or spatial transport. "
                "It should not be described as guaranteed forecasting accuracy or as an AQI forecast."
            )
    except ValueError as exc:
        st.warning(str(exc))

# ===========================================================================
# 05 · RESEARCH ASSISTANT
# ===========================================================================

with assistant_tab:
    st.html(
        ui.section_head(
            "ASK AIRSENSE",
            "Ask AirSense",
            "Start with Quick Answers for everyday questions, or switch to a local or hosted model for open-ended research help.",
        ),
    )

    assistant_provider = str(st.session_state.get("assistant_provider", "Quick answers · built in"))
    quick_mode = assistant_provider.startswith("Quick")
    local_mode = assistant_provider.startswith("Local")
    if quick_mode:
        local_model = ""
        st.caption("Quick Answers is built in and works for everyday air-quality questions without any AI setup.")
    elif local_mode:
        installed_models = cached_ollama_models()
        if "ollama_model" not in st.session_state:
            st.session_state["ollama_model"] = installed_models[0] if installed_models else "llama3.2:3b"
        local_model = st.text_input(
            "Ollama model tag",
            key="ollama_model",
            help="Enter a model tag already downloaded in Ollama.",
        )
        if installed_models:
            shown = ", ".join(installed_models[:3])
            more = f" +{len(installed_models) - 3} more" if len(installed_models) > 3 else ""
            st.caption(f"Local inference · installed: {shown}{more}. Prompts stay on this machine.")
        else:
            st.caption(
                "Local inference · no Ollama models detected. Start Ollama and run `ollama pull <model>`, "
                "or switch to the hosted provider in the sidebar."
            )
    else:
        local_model = ""
        st.caption("Hosted model · requires a configured OpenAI-compatible API key.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if not st.session_state.messages:
        st.html(
            """
            <div class="glass-card" style="margin-bottom:1rem;">
              <div class="card-topline"><span class="card-kicker">START HERE</span><span class="mono-chip">CONTEXT-AWARE</span></div>
              <p class="index-summary" style="margin-top:.7rem;">The assistant receives the current reading, the category advisory, the recent hourly window and the 48-hour forecast context. It is instructed to distinguish measurements from estimates.</p>
            </div>
            """,
        )
        suggestions = [
            ("Can I go for a walk?", "Can I go for a walk outside today?"),
            ("Why is PM₂.₅ elevated?", "Why is PM₂.₅ elevated right now?"),
            ("How can I help?", "How can I help reduce air pollution?"),
            ("How does ozone form?", "How does ground-level ozone form?"),
        ]
        prompt_from_button = None
        for row_start in (0, 2):
            suggestion_columns = st.columns(2, gap="small")
            for column, (label, question) in zip(suggestion_columns, suggestions[row_start : row_start + 2]):
                if column.button(label, key=f"suggest_{row_start}_{label}", width="stretch"):
                    prompt_from_button = question
    else:
        prompt_from_button = None

    if st.button("Clear conversation", key="clear_chat"):
        st.session_state.messages = []
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    st.caption(
        "Assistant output can be wrong, especially with small local models. Verify scientific claims against the "
        "guidance and sources in this app; never treat a reply as medical advice."
    )
    prompt = st.chat_input("Ask about the air, the chemistry, or this reading…") or prompt_from_button
    if prompt:
        previous_history = st.session_state.messages.copy()
        st.session_state.messages.append({"role": "user", "content": prompt})
        context = {
            "location": f"{city}, {country}",
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "current_aqi": current_aqi,
            "current_category": band["name"],
            "aqi_scale": "US AQI (provider-calculated; not CPCB National AQI)",
            "health_guidance": {"general": band["general"], "sensitive": band["sensitive"]},
            "current_readings": current_values,
            "recent_hourly_readings": hourly[hourly["time"] <= reference_time].tail(8).to_dict(orient="records"),
            "forecast_next_24h": forecast_24[["time", "us_aqi", "category"]].to_dict(orient="records") if not forecast_24.empty else [],
            "cleanest_windows": [
                {"start": str(window["start"]), "end": str(window["end"]), "mean_us_aqi": round(window["mean"], 1)}
                for window in windows
            ],
            "chemistry_lab_note": "The interactive ozone lab is a dimensionless conceptual response model, not a real chemical kinetics calculation.",
            "prediction_note": "The Random Forest predicts next-hour PM2.5 concentration, not AQI.",
        }
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            try:
                with st.spinner("Thinking through the chemistry…"):
                    if quick_mode:
                        answer = answer_simple_question(prompt, context)
                    elif local_mode:
                        answer = ask_local_ollama(
                            prompt,
                            context,
                            previous_history,
                            model=local_model.strip() or "llama3.2:3b",
                        )
                    else:
                        answer = ask_hosted_model(prompt, context, previous_history)
                st.markdown(answer)
            except Exception as exc:
                answer = f"Assistant unavailable: {exc}"
                st.warning(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

# ===========================================================================
# 06 · ABOUT
# ===========================================================================

with about_tab:
    st.html(
        ui.section_head(
            "PLATFORM INFORMATION",
            "About AirSense",
            "A student-built atmospheric intelligence platform: live model data, transparent AQI tracking, chemistry teaching tools and a baseline forecast.",
        ),
    )

    st.html(
        """
        <div class="glass-card">
          <div class="card-topline"><span class="card-kicker">DESIGN PRINCIPLE</span><span class="mono-chip">TRACEABLE BY DEFAULT</span></div>
          <p class="index-summary" style="margin-top:.8rem;">
            AirSense is built around a simple rule: <b>never make a model estimate look like a measurement.</b>
            Provider-calculated AQI, derived indicators, CAMS concentrations, CPCB station rows and educational simulations
            are labelled separately throughout the interface.
          </p>
          <div class="health-divider"></div>
          <p class="index-interpretation">
            The globe pairs a NASA satellite surface with colour-coded AQI samples from selected cities. The heat halos show
            city-level samples, not a continuous global pollution field. The numbers, provenance labels and limitations carry the evidential weight.
          </p>
        </div>
        """,
    )

    about_cards = [
        (
            "WHAT IT DOES",
            "Live AQI tracking, a 48-hour category forecast, a seven-day hourly pulse, WHO guideline comparisons, a personal inhaled-dose lab and a cleanest-window finder.",
            "#6FE3D6",
        ),
        (
            "WHAT POWERS IT",
            "Open-Meteo Air Quality (CAMS-based model data), a scikit-learn Random Forest baseline, a conceptual ozone response surface, and an optional local or hosted language model.",
            "#FF8069",
        ),
        (
            "WHAT IT IS NOT",
            "Not a regulatory monitor. Not an official CPCB or EPA AQI forecast. Not a medical device. Not a chemical-kinetics solver. Not a substitute for local public-health guidance.",
            "#E9BB78",
        ),
    ]
    about_html = "".join(
        f'<div class="glass-card about-card" style="border-top:2px solid {accent};">'
        f'<div class="card-kicker">{title}</div>'
        f'<p class="index-summary" style="font-size:.84rem;">{body}</p></div>'
        for title, body, accent in about_cards
    )
    st.html(f'<div class="about-grid">{about_html}</div>')

    st.html(
        ui.section_head(
            "METHODOLOGY",
            "The stack, line by line",
            "Every layer has a source and a limitation.",
        ),
    )
    st.markdown(
        """
        | Layer | Implementation | Honest scope |
        |---|---|---|
        | Air quality data | Open-Meteo Air Quality API | CAMS model-based estimates, not nearby station readings |
        | Current AQI | Provider US / European AQI | Different scales; not India's CPCB National AQI |
        | Derived AQI | US EPA 2024 PM₂.₅ breakpoints | Used only when a provider value is missing; labelled indicative |
        | Forecast | Provider hourly US AQI, next 48h | Forecast, not observation; skill decays with time |
        | Personal dose | Concentration × ventilation × duration | Indicative adult estimate; not medical advice |
        | WHO comparison | WHO 2021 guideline values | Hourly values vs 24h/8h references; context only |
        | Globe surface | NASA Blue Marble satellite texture + Open-Meteo city samples | Satellite imagery is visual context; heat halos are discrete city readings, not a global interpolation |
        | Chemistry lab | Dimensionless conceptual response surface | Not a kinetics solver and not ambient ozone |
        | PM₂.₅ model | Random Forest, chronological split | Baseline next-hour concentration model, not AQI |
        | AI assistant | Local Ollama or hosted chat-completions | Can be wrong; verify scientific claims |
        | India stations | CPCB/data.gov.in public mirror | Station-level pollutants; no derived National AQI |
        """
    )

    st.markdown("#### Data & science references")
    st.markdown(
        """
        - [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) — CAMS-based model fields, provider AQI.
        - [US EPA AQI](https://www.airnow.gov/aqi/aqi-basics/) — category meanings and the 2024 PM₂.₅ breakpoint revision.
        - [WHO Air Quality Guidelines (2021)](https://www.who.int/publications/i/item/9789240034228) — reference values used for context.
        - [CPCB / data.gov.in real-time AQI catalogue](https://www.data.gov.in/catalog/real-time-air-quality-index) — official Indian source context.
        - [CPCB monitoring methodology](https://app.cpcbccr.com/ccr_docs) — network and methodology documents.
        - [NASA SVS Blue Marble texture](https://svs.gsfc.nasa.gov/3615/) — satellite surface used by the interactive globe.
        """
    )

    with st.expander("Deploy this app"):
        st.markdown(
            """
            1. Push the repository to GitHub (never commit `.env` or `.streamlit/secrets.toml`).
            2. Create a Streamlit Community Cloud app with `app.py` as the main file.
            3. Optional: add `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`, `OPENAI_BASE_URL`) under **App settings → Secrets** for the hosted assistant.
            4. Local Ollama only works when Streamlit runs on the same machine as Ollama; it cannot reach your Mac from a cloud host.
            5. If the live provider is unreachable, AirSense automatically switches to a clearly labelled sample atmosphere so every screen remains explorable.
            """
        )
        st.code("pip install -r requirements.txt\nstreamlit run app.py", language="bash")

    st.html(
        """
        <div class="glass-card mt-2">
          <div class="card-topline"><span class="card-kicker">PRIVACY</span><span class="mono-chip">NO ACCOUNTS · NO TRACKING</span></div>
          <p class="index-summary" style="font-size:.82rem;margin-top:.7rem;">
            City searches and air-quality requests go directly to Open-Meteo. Chat prompts are sent only to the assistant
            you configure (local Ollama or your hosted provider). AirSense stores no user accounts, profiles or analytics.
          </p>
        </div>
        """,
    )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.html(ui.footer_html())
