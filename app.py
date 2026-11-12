import streamlit as st
import pandas as pd

from src.air_quality import fetch_air_quality
from src.model import train_pm25_model
from src.chat import ask_local_model, ask_science_assistant

st.set_page_config(page_title="AirSense AI", page_icon="🌍", layout="wide")

st.title("🌍 AirSense AI")
st.caption("Air-quality monitoring, PM₂.₅ forecasting, and environmental science explanations.")

with st.sidebar:
    st.header("Location")
    city = st.text_input("Location name", "Bengaluru")
    latitude = st.number_input("Latitude", value=12.9716, format="%.4f")
    longitude = st.number_input("Longitude", value=77.5946, format="%.4f")
    st.caption("These coordinates are an editable demo default. Change them for another location.")
    st.divider()
    st.header("AI assistant")
    chat_mode = st.radio(
    "Choose assistant",
    ["Scientific Q&A (Free)", "Gemma AI (Local Mac)"]
)

@st.cache_data(ttl=900, show_spinner=False)
def load_data(lat, lon):
    return fetch_air_quality(lat, lon)

try:
    with st.spinner("Fetching air-quality data..."):
        payload = load_data(latitude, longitude)
    current = payload["current"]
    hourly = payload["hourly"]

    st.subheader(f"Air quality around {city}")
    a, b, c, d = st.columns(4)
    a.metric("US AQI", current.get("us_aqi", "—"))
    b.metric("European AQI", current.get("european_aqi", "—"))
    c.metric("PM₂.₅", f'{current.get("pm2_5", "—")} μg/m³')
    d.metric("PM₁₀", f'{current.get("pm10", "—")} μg/m³')
    st.caption(
        f"Provider timestamp: {current.get('time', 'not supplied')} · "
        "AQI indices are shown using the provider's US and European scales, not India's CPCB scale."
    )

    st.subheader("Pollutant trends")
    chart_cols = [c for c in ["pm2_5", "pm10", "nitrogen_dioxide", "ozone"] if c in hourly.columns]
    if chart_cols:
        st.line_chart(hourly.set_index("time")[chart_cols])
    else:
        st.info("No hourly pollutant series was returned.")

    st.subheader("Your trained ML model")
    st.write("This starter model predicts **PM₂.₅ concentration one hour ahead** from recent pollutant and time data. It does not claim to predict India's official CPCB AQI.")
    try:
        result = train_pm25_model(hourly)
        m1, m2 = st.columns(2)
        m1.metric("Next-hour PM₂.₅ estimate", f'{result["prediction"]:.1f} μg/m³')
        m2.metric("Test MAE", f'{result["mae"]:.2f} μg/m³')
        st.caption(f"Trained on {result['rows']} usable hourly records. Test data is kept later in time than training data.")
    except ValueError as exc:
        st.warning(str(exc))

    st.divider()
    st.subheader("Ask AirSense")
    st.write("Ask about the readings, pollutants, atmospheric chemistry, or what the model's estimate means.")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Why is PM₂.₅ important?")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        context = {
            "location": city,
            "current_readings": current,
            "latest_hourly_readings": hourly.tail(6).to_dict(orient="records"),
        }
        with st.chat_message("assistant"):
            with st.spinner("AirSense is thinking..."):
                try:
                    if chat_mode == "API model":
                        answer = ask_api_model(prompt, context, st.session_state.messages[:-1])
                    else:
                        answer = ask_local_model(prompt, context, st.session_state.messages[:-1])
                    st.markdown(answer)
                except Exception as exc:
                    answer = (
                        f"**Chatbot connection issue:** {exc}\n\n"
                        "The AQI dashboard and ML model can still work independently. "
                        "Check the chatbot setup in the README."
                    )
                    st.warning(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

except Exception as exc:
    st.error(f"Couldn't load air-quality data: {exc}")
    st.info("Check your internet connection and try again. The Open-Meteo endpoint is documented in the project README.")
