import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

from src.air_quality import fetch_air_quality, search_locations, fetch_cpcb_city_readings
from src.model import train_pm25_model
from src.chat import ask_hosted_model, ask_local_ollama
from src.chemistry import simulate_ozone_response


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="AirSense — Atmospheric Intelligence",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# ATMOSPHERIC CANVAS BACKGROUND
# --------------------------------------------------

background_path = Path(__file__).parent / "background.html"
if background_path.exists():
    background_html = background_path.read_text(encoding="utf-8")

    st.markdown("""
    <style>
    /* The iframe is promoted to a fixed, viewport-sized background layer. */
    [data-testid="stIFrame"] {
        position: fixed !important;
        inset: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 0 !important;
        pointer-events: none !important;
        border: 0 !important;
        margin: 0 !important;
    }
    [data-testid="stIFrame"] iframe {
        width: 100% !important;
        height: 100% !important;
        border: 0 !important;
        background: transparent !important;
    }
    [data-testid="stAppViewContainer"] {
        background: #0B1422 !important;
    }
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    [data-testid="stMain"] {
        position: relative !important;
        z-index: 1 !important;
        background: transparent !important;
    }
    [data-testid="stMainBlockContainer"] {
        position: relative !important;
        z-index: 1 !important;
    }
    [data-testid="stSidebar"] {
        position: relative !important;
        z-index: 2 !important;
        background: rgba(11, 20, 34, .94) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    components.html(background_html, height=1, scrolling=False)
else:
    st.warning("background.html was not found. Add it to the project root to enable the animated background.")


# --------------------------------------------------
# DESIGN SYSTEM
# --------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --navy: #0B1422;
    --navy2: #111F30;
    --panel: rgba(24, 42, 59, 0.76);
    --cream: #F2EBDD;
    --muted: #A5B2C0;
    --coral: #F18470;
    --cyan: #79D5D3;
    --amber: #E9BB78;
    --line: rgba(218, 230, 239, 0.12);
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--navy) !important;
    color: var(--cream) !important;
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stAppViewContainer"] {
    position: relative;
    overflow: hidden;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stMainBlockContainer"] {
    position: relative;
    z-index: 1;
    padding-top: 2.5rem;
    max-width: 1450px;
}

[data-testid="stSidebar"] {
    background: rgba(11, 20, 34, 0.96) !important;
    border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] * {
    color: var(--cream);
}

h1, h2, h3 {
    font-family: 'Manrope', sans-serif !important;
    letter-spacing: -0.045em;
    color: var(--cream) !important;
}

p, label, .stMarkdown {
    color: var(--cream);
}

small, .muted {
    color: var(--muted) !important;
}

hr {
    border-color: var(--line) !important;
}

.stButton > button {
    background: var(--coral);
    color: #172131;
    border: none;
    border-radius: 9px;
    font-weight: 700;
    padding: 0.65rem 1.2rem;
    transition: all .2s ease;
}

.stButton > button:hover {
    background: #FFA08D;
    color: #101B2A;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(241, 132, 112, .2);
}

.stTextInput input, .stNumberInput input,
.stTextArea textarea {
    background: #17283A !important;
    color: var(--cream) !important;
    border: 1px solid var(--line) !important;
    border-radius: 9px !important;
}

[data-baseweb="select"] > div {
    background: #17283A !important;
    border-color: var(--line) !important;
    color: var(--cream) !important;
}

.stSlider [data-baseweb="slider"] {
    color: var(--coral);
}

[data-testid="stMetric"] {
    background: rgba(26, 44, 62, .76);
    border: 1px solid var(--line);
    border-radius: 13px;
    padding: 17px 19px;
    transition: all .2s ease;
}

[data-testid="stMetric"]:hover {
    border-color: rgba(241,132,112,.55);
    transform: translateY(-2px);
}

[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
    font-size: .78rem !important;
    text-transform: uppercase;
    letter-spacing: .09em;
}

[data-testid="stMetricValue"] {
    color: var(--cream) !important;
    font-family: 'DM Mono', monospace;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    border-bottom: 1px solid var(--line);
}

.stTabs [data-baseweb="tab"] {
    color: var(--muted);
    background: transparent;
    border-radius: 8px 8px 0 0;
}

.stTabs [aria-selected="true"] {
    color: var(--coral) !important;
    border-bottom: 2px solid var(--coral) !important;
}

[data-testid="stChatMessage"] {
    background: rgba(25, 43, 60, .8);
    border: 1px solid var(--line);
    border-radius: 13px;
}

[data-testid="stAlert"] {
    background: rgba(31, 52, 70, .85);
    border: 1px solid var(--line);
    color: var(--cream);
}

.eyebrow {
    color: var(--cyan);
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: .17em;
    text-transform: uppercase;
    margin-bottom: 12px;
}

.hero-title {
    font-family: 'Manrope', sans-serif;
    font-size: clamp(2.8rem, 6vw, 5.2rem);
    line-height: 1.02;
    font-weight: 800;
    letter-spacing: -.065em;
    color: var(--cream);
    margin: 0;
}

.hero-title span {
    color: var(--coral);
}

.hero-copy {
    color: #AAB8C5;
    font-size: 1.05rem;
    line-height: 1.8;
    max-width: 660px;
    margin-top: 18px;
}

.panel {
    background: linear-gradient(135deg, rgba(29,49,68,.88), rgba(17,31,48,.78));
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 22px;
    backdrop-filter: blur(15px);
}

.panel-label {
    color: var(--muted);
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: .15em;
    text-transform: uppercase;
}

.panel-value {
    color: var(--cream);
    font-family: 'DM Mono', monospace;
    font-size: 2rem;
    font-weight: 500;
    margin-top: 10px;
}

.panel-detail {
    color: var(--muted);
    font-size: .82rem;
    margin-top: 5px;
}

.coral { color: var(--coral); }
.cyan { color: var(--cyan); }
.amber { color: var(--amber); }

.section-heading {
    font-family: 'Manrope', sans-serif;
    font-size: 1.55rem;
    font-weight: 750;
    color: var(--cream);
    letter-spacing: -.04em;
    margin: 0 0 5px 0;
}

.section-copy {
    color: var(--muted);
    font-size: .9rem;
    margin-bottom: 20px;
}

.chem-equation {
    background: rgba(121,213,211,.055);
    border: 1px solid rgba(121,213,211,.22);
    border-radius: 12px;
    padding: 19px;
    text-align: center;
    font-family: 'DM Mono', monospace;
    color: var(--cyan);
    font-size: 1.1rem;
    line-height: 2;
}

.footer {
    border-top: 1px solid var(--line);
    padding-top: 20px;
    margin-top: 45px;
    color: #78899A;
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: .12em;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 22px 0;">
      <div style="font-family:Manrope;font-size:25px;font-weight:800;letter-spacing:-1.5px;color:#F2EBDD;">
        AIR<span style="color:#F18470;">SENSE</span>
      </div>
      <div style="font-family:'DM Mono';font-size:9px;letter-spacing:2px;color:#79D5D3;">
        ATMOSPHERIC INTELLIGENCE
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="eyebrow">01 / Observation point</div>', unsafe_allow_html=True)

    st.markdown("### Choose a location")
    if "location_query" not in st.session_state:
        st.session_state["location_query"] = "Bengaluru"
    location_query = st.text_input(
        "Search city or place",
        key="location_query",
        placeholder="e.g. Delhi, Mumbai, London",
        help="Search by place name. Coordinates are resolved automatically."
    )
    if st.button("Search locations", use_container_width=True):
        try:
            st.session_state["location_matches"] = search_locations(location_query)
            st.session_state.pop("location_error", None)
        except Exception as exc:
            st.session_state["location_matches"] = []
            st.session_state["location_error"] = str(exc)

    if st.session_state.get("location_error"):
        st.error(st.session_state["location_error"])

    matches = st.session_state.get("location_matches", [])
    if not matches:
        # Resolve the initial default once; never silently switch back to Bengaluru
        # after a failed search.
        if "selected_location" not in st.session_state:
            try:
                defaults = search_locations("Bengaluru")
                st.session_state["location_matches"] = defaults
                matches = defaults
            except Exception:
                matches = []

    if matches:
        labels = [
            ", ".join(part for part in [
                item.get("name", ""),
                item.get("admin1", ""),
                item.get("country", "")
            ] if part)
            for item in matches
        ]
        default_index = 0
        previous = st.session_state.get("selected_location")
        if previous:
            for idx, item in enumerate(matches):
                if (item.get("id") == previous.get("id")
                        or (item.get("name") == previous.get("name")
                            and item.get("country") == previous.get("country"))):
                    default_index = idx
                    break
        selected_label = st.selectbox("Select matching place", labels, index=default_index)
        selected = matches[labels.index(selected_label)]
        st.session_state["selected_location"] = selected
        city = selected["name"]
        country = selected.get("country", "")
        latitude = float(selected["latitude"])
        longitude = float(selected["longitude"])
        st.caption(f"Coordinates resolved automatically · {selected.get('timezone', 'local timezone')}")
    else:
        st.error("No location selected. Search for a city to load air-quality data.")
        st.stop()

    st.divider()

    st.markdown('<div class="eyebrow">02 / Research assistant</div>', unsafe_allow_html=True)

    chat_mode = st.selectbox("AI assistant", ["Local LLM · Ollama", "Hosted API"], key="assistant_provider")
    st.caption("Local Ollama runs on your Mac without a hosted API key." if chat_mode.startswith("Local") else "Hosted assistant · requires a provider API key.")

    st.divider()

    st.markdown("""
    <div style="font-family:'DM Mono';font-size:10px;color:#8495A7;line-height:2;">
    DATA SOURCE<br>
    CAMS / OPEN-METEO · MODELLED DATA<br><br>
    MODEL<br>
    RANDOM FOREST REGRESSION<br><br>
    AI ASSISTANT<br>
    LOCAL OLLAMA / HOSTED API
    </div>
    """, unsafe_allow_html=True)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown("""
<div class="eyebrow">ATMOSPHERIC RESEARCH PLATFORM &nbsp; / &nbsp; 2026</div>
<div class="hero-title">Understand<br>the <span>air.</span></div>
<div class="hero-copy">
Monitor atmospheric conditions, explore pollutant behaviour
and investigate the chemistry behind the air we breathe.
</div>
""", unsafe_allow_html=True)

st.write("")

# --------------------------------------------------
# DATA
# --------------------------------------------------

@st.cache_data(ttl=900, show_spinner=False)
def load_data(lat, lon):
    return fetch_air_quality(lat, lon)


try:
    with st.spinner("Connecting to atmospheric data..."):
        payload = load_data(latitude, longitude)

    current = payload["current"]
    hourly = payload["hourly"]

    if hourly.empty:
        st.warning("The data provider returned no hourly observations.")
        st.stop()

    # --------------------------------------------------
    # STATUS STRIP
    # --------------------------------------------------

    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
    border-top:1px solid rgba(218,230,239,.12);
    border-bottom:1px solid rgba(218,230,239,.12);
    padding:13px 0;margin:28px 0 20px 0;flex-wrap:wrap;gap:10px;">
      <div>
        <span style="color:#79D5D3;font-family:'DM Mono';font-size:10px;">● LIVE DATA</span>
        <span style="color:#A5B2C0;font-size:12px;margin-left:10px;">{city}</span>
      </div>
      <div style="color:#8293A4;font-family:'DM Mono';font-size:10px;">
        PROVIDER TIME: {current.get('time', 'Not supplied')}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------
    # TABS
    # --------------------------------------------------

    overview, chemistry, prediction, assistant, about = st.tabs([
        "01  Overview",
        "02  Chemistry Lab",
        "03  Prediction Lab",
        "04  Research Assistant",
        "05  About",
    ])

    # ==================================================
    # OVERVIEW
    # ==================================================

    with overview:
        st.markdown('<div class="section-heading">Atmospheric overview</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">Current pollutant measurements at your selected observation point.</div>', unsafe_allow_html=True)

        # The public mirror contains station pollutant observations, not CPCB AQI.
        if country.lower() in {"india", "in"}:
            cpcb_data = fetch_cpcb_city_readings(city)
            c1, c2, c3 = st.columns([1.25, 1, 1])
            c1.metric("India National AQI · CPCB", "Not supplied")
            c2.metric("PM₂.₅ · CAMS model", f'{current.get("pm2_5", "—")} μg/m³')
            c3.metric("PM₁₀ · CAMS model", f'{current.get("pm10", "—")} μg/m³')
            st.info("The public feed supplies pollutant concentrations, not a verified National AQI. AirSense will not invent an AQI from partial station data.")
            if cpcb_data.get("records"):
                st.markdown("**CPCB station observations**")
                st.caption("CPCB/data.gov.in observations via a third-party public mirror · station-level, not citywide averages")
                st.dataframe(cpcb_data["records"], use_container_width=True, hide_index=True)
            else:
                st.warning(cpcb_data.get("message", "Station observations are temporarily unavailable."))
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("PM₂.₅ · CAMS model", f'{current.get("pm2_5", "—")} μg/m³')
            c2.metric("PM₁₀ · CAMS model", f'{current.get("pm10", "—")} μg/m³')
            c3.metric("O₃ · CAMS model", f'{current.get("ozone", "—")} μg/m³')

        with st.expander("International AQI comparison (different scales)"):
            st.caption("These are provider-calculated comparison indices, not India's CPCB National AQI. They are model-derived and should not be compared numerically across systems.")
            aqi_a, aqi_b = st.columns(2)
            aqi_a.metric("US AQI", current.get("us_aqi", "—"))
            aqi_b.metric("European AQI", current.get("european_aqi", "—"))

        st.caption("Pollutant concentrations below are CAMS model-based estimates, not necessarily readings from a nearby physical monitoring station.")

        st.markdown("---")

        left, right = st.columns([1.7, 1])

        with left:
            st.markdown('<div class="section-heading">Pollutant behaviour</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-copy">Hourly pollutant concentration trends.</div>', unsafe_allow_html=True)

            chart_columns = [
                col for col in [
                    "pm2_5", "pm10", "nitrogen_dioxide",
                    "sulphur_dioxide", "ozone"
                ]
                if col in hourly.columns
            ]

            selected_pollutants = st.multiselect(
                "Select pollutants",
                chart_columns,
                default=chart_columns[:3],
                format_func=lambda x: {
                    "pm2_5": "PM₂.₅",
                    "pm10": "PM₁₀",
                    "nitrogen_dioxide": "NO₂",
                    "sulphur_dioxide": "SO₂",
                    "ozone": "O₃",
                }.get(x, x),
            )

            if selected_pollutants:
                st.line_chart(
                    hourly.set_index("time")[selected_pollutants],
                    height=330,
                )
            else:
                st.info("Select at least one pollutant to display its trend.")

        with right:
            st.markdown('<div class="section-heading">Chemical profile</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-copy">Latest available measurements.</div>', unsafe_allow_html=True)

            pollutant_names = {
                "pm2_5": ("PM₂.₅", "μg/m³"),
                "pm10": ("PM₁₀", "μg/m³"),
                "nitrogen_dioxide": ("NO₂", "μg/m³"),
                "sulphur_dioxide": ("SO₂", "μg/m³"),
                "ozone": ("O₃", "μg/m³"),
                "carbon_monoxide": ("CO", "μg/m³"),
            }

            for key, (name, unit) in pollutant_names.items():
                value = current.get(key)
                if value is not None:
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;
                    border-bottom:1px solid rgba(218,230,239,.09);
                    padding:11px 0;">
                      <span style="color:#A5B2C0;">{name}</span>
                      <span style="font-family:'DM Mono';color:#F2EBDD;">
                        {value} <span style="color:#8293A4;font-size:11px;">{unit}</span>
                      </span>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown('<div class="section-heading">Recent observations</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">Inspect the latest hourly data returned by the provider.</div>', unsafe_allow_html=True)

        st.dataframe(
            hourly.tail(12).sort_values("time", ascending=False),
            use_container_width=True,
            hide_index=True,
        )


    # ==================================================
    # CHEMISTRY LAB
    # ==================================================

    with chemistry:
        st.markdown('<div class="eyebrow">EXPERIMENT 001 / PHOTOCHEMISTRY</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Atmospheric chemistry laboratory</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">Explore how sunlight, nitrogen oxides and volatile organic compounds interact in simplified ground-level ozone chemistry.</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="chem-equation">
        NO₂ + hν → NO + O(³P)<br>
        O(³P) + O₂ + M → O₃ + M
        <div style="font-family:'DM Sans';font-size:12px;color:#A5B2C0;margin-top:8px;">
        Simplified ozone formation sequence · hν represents absorbed light · M is a third body
        </div></div>
        """, unsafe_allow_html=True)

        controls, output = st.columns([0.9, 1.35], gap="large")
        with controls:
            st.markdown("#### Experiment conditions")
            sunlight = st.slider("Relative sunlight", 0, 100, 65, help="Dimensionless teaching control; not measured irradiance.")
            nox = st.slider("NOx availability", 0, 100, 50, help="Dimensionless teaching control; not a concentration.")
            voc = st.slider("VOC reactivity / availability", 0, 100, 55, help="Dimensionless teaching control; VOC mixtures differ in reactivity.")
            regime = st.selectbox("Illustrative chemical regime", ["Balanced sensitivity", "VOC-limited tendency", "NOx-limited tendency"])
            st.caption("All controls are relative teaching inputs, not measured atmospheric concentrations.")

        simulation = simulate_ozone_response(sunlight, nox, voc, regime)
        with output:
            st.markdown("#### Simulation response")
            st.markdown(
                f"""<div class="panel"><div class="panel-label">ILLUSTRATIVE RELATIVE RESPONSE INDEX</div>
                <div class="panel-value">{simulation['index']:.0f}<span style="font-size:14px;color:#A5B2C0;"> / 100</span></div>
                <div style="color:#A5B2C0;line-height:1.7;margin-top:8px;">{simulation['summary']}</div>
                <div style="margin-top:18px;height:8px;background:rgba(255,255,255,.08);border-radius:9px;overflow:hidden;">
                <div style="width:{simulation['index']:.1f}%;height:100%;background:linear-gradient(90deg,#79D5D3,#E9BB78,#F18470);border-radius:9px;"></div></div></div>""",
                unsafe_allow_html=True,
            )
            st.markdown("**What drives this result?**")
            st.write(simulation["interpretation"])
            st.caption("This index is a dimensionless response from a conceptual model. It is not ozone concentration, AQI, or a validated chemical-kinetics output.")

        st.markdown("---")
        st.markdown("#### Explore the response surface")
        st.caption("Hold NOx and the selected regime fixed while varying sunlight and VOC input.")
        surface_rows = []
        for light in range(0, 101, 10):
            row = {"Sunlight": light}
            for v in range(0, 101, 20):
                row[f"VOC {v}"] = simulate_ozone_response(light, nox, v, regime)["index"]
            surface_rows.append(row)
        import pandas as pd
        surface = pd.DataFrame(surface_rows).set_index("Sunlight")
        st.line_chart(surface, height=280)

        st.markdown("#### Reaction pathway")
        pathway = [
            ("01", "NO₂ photolysis", "Nitrogen dioxide absorbs sunlight and can split into nitric oxide and an oxygen atom."),
            ("02", "Ozone formation", "Atomic oxygen can combine with O₂ in a three-body reaction to form O₃."),
            ("03", "VOC oxidation and NO recycling", "VOC-derived peroxy radicals can convert NO to NO₂ without consuming ozone, supporting net ozone production in polluted air."),
            ("04", "Chemical regime matters", "The ozone response to NOx and VOC changes is nonlinear and depends on radical chemistry, emissions, sunlight and transport."),
        ]
        for number, heading, description in pathway:
            st.markdown(
                f"""<div style="display:flex;gap:17px;padding:15px 0;border-bottom:1px solid rgba(218,230,239,.10);">
                <div style="font-family:'DM Mono';color:#F18470;font-size:13px;">{number}</div><div><div style="font-weight:700;color:#F2EBDD;">{heading}</div>
                <div style="font-size:13px;color:#A5B2C0;margin-top:5px;">{description}</div></div></div>""",
                unsafe_allow_html=True,
            )
        st.info("Model scope: educational response surface only. It does not solve atmospheric chemical kinetics or predict real-world ozone. Quantitative prediction requires a chemically resolved mechanism, meteorology, emissions, boundary conditions and validation against observations.")
    # ==================================================
    # PREDICTION LAB
    # ==================================================

    with prediction:
        st.markdown('<div class="eyebrow">EXPERIMENT 002 / MACHINE LEARNING</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Predictive intelligence</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">A Random Forest regression baseline estimating PM₂.₅ concentration one hour ahead.</div>', unsafe_allow_html=True)

        try:
            result = train_pm25_model(hourly)

            p1, p2, p3 = st.columns(3)

            p1.metric(
                "Next-hour PM₂.₅ estimate",
                f'{result["prediction"]:.2f} μg/m³',
            )

            p2.metric(
                "Test MAE",
                f'{result["mae"]:.2f} μg/m³',
            )

            p3.metric(
                "Usable records",
                result["rows"],
            )

            if result.get("feature_importance"):
                st.markdown("#### Model feature importance")
                importance = pd.Series(result["feature_importance"]).sort_values(ascending=False)
                st.bar_chart(importance, height=220)


            st.markdown("---")

            st.markdown("#### Historical PM₂.₅ profile")

            if "pm2_5" in hourly.columns:
                st.line_chart(
                    hourly.set_index("time")["pm2_5"],
                    height=330,
                )

            st.markdown("#### How to interpret this model")

            st.markdown("""
            - **Prediction:** Estimated PM₂.₅ concentration for the next hour.
            - **MAE:** Mean absolute error on the model's held-out test data.
            - **Training data:** Historical hourly pollutant and time features.
            - **Evaluation:** The test period is later in time than the training period.
            """)

            st.info(
                "This is a baseline machine learning estimate, not an official "
                "CPCB AQI forecast. Its performance depends on the available "
                "data and should be evaluated against appropriate baselines."
            )

        except ValueError as exc:
            st.warning(str(exc))


    # ==================================================
    # RESEARCH ASSISTANT
    # ==================================================

    with assistant:
        st.markdown('<div class="eyebrow">EXPERIMENT 003 / SCIENTIFIC INTELLIGENCE</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Ask AirSense</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">An open-ended assistant for atmospheric chemistry, pollutant science and the data in this session.</div>', unsafe_allow_html=True)
        local_mode = st.session_state.get("assistant_provider", "Local LLM · Ollama").startswith("Local")
        if local_mode:
            local_model = st.text_input("Ollama model", value="llama3.2:3b", help="Enter a model tag already available in Ollama.")
            st.caption("Local inference · prompts are sent to Ollama running on this Mac.")
        else:
            local_model = ""
            st.caption("Hosted model · requires a provider API key.")
        st.caption("Answers may be imperfect · verify scientific claims against primary sources.")

        if "messages" not in st.session_state:
            st.session_state.messages = []
        if st.button("Clear conversation", key="clear_hosted_chat"):
            st.session_state.messages = []
            st.rerun()
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input("Ask anything about atmospheric chemistry...")
        if prompt:
            previous_history = st.session_state.messages.copy()
            st.session_state.messages.append({"role": "user", "content": prompt})
            context = {
                "location": city,
                "current_readings": current,
                "recent_hourly_readings": hourly.tail(8).to_dict(orient="records"),
                "chemistry_lab_note": "The interactive ozone lab is a dimensionless conceptual response model, not a real chemical kinetics calculation.",
            }
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                try:
                    with st.spinner("Thinking through the chemistry..."):
                        if local_mode:
                            answer = ask_local_ollama(prompt, context, previous_history, model=local_model.strip() or "llama3.2:3b")
                        else:
                            answer = ask_hosted_model(prompt, context, previous_history)
                    st.markdown(answer)
                except Exception as exc:
                    answer = f"Assistant unavailable: {exc}"
                    st.warning(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

    # ==================================================
    # ABOUT
    # ==================================================

    with about:
        st.markdown('<div class="eyebrow">PLATFORM INFORMATION</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">About AirSense</div>', unsafe_allow_html=True)

        st.markdown("""
        AirSense is an environmental monitoring and educational research
        platform combining live air-quality observations, baseline machine
        learning and atmospheric chemistry explanations.
        """)

        st.markdown("#### Data and methodology")

        st.markdown("""
        | Component | Implementation |
        |---|---|
        | Air quality data | Open-Meteo Air Quality API |
        | Prediction | Random Forest regression |
        | Target variable | Next-hour PM₂.₅ concentration |
        | Chemistry lab | Dimensionless conceptual response model |
        | AI assistant | Local Ollama or hosted chat-completions API |
        """)

        st.markdown("#### Important limitations")

        st.markdown("""
        - AQI values use the provider's US and European scales.
        - PM₂.₅ prediction is not an official CPCB AQI forecast.
        - The chemistry experiment is a dimensionless educational response model, not a kinetics solver.
        - Local AI uses Ollama at localhost:11434; hosted AI requires a provider key.
        - AI responses can contain errors; verify important scientific claims.
        """)

except Exception as exc:
    st.error(f"Unable to load atmospheric data: {exc}")
    st.info("Check your internet connection and your Open-Meteo data configuration.")


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("""
<div class="footer">
AIRSENSE AI &nbsp; / &nbsp; ATMOSPHERIC INTELLIGENCE
<br><br>
ENVIRONMENTAL DATA · CHEMISTRY · MACHINE LEARNING
</div>
""", unsafe_allow_html=True)
