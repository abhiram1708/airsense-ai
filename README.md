# AirSense AI

A student-built air-quality monitoring and PM2.5 forecasting prototype.

## What it does

- Fetches current and hourly pollutant data from Open-Meteo.
- Displays provider-reported US AQI and European AQI separately.
- Trains a Random Forest model to estimate PM2.5 one hour ahead.
- Offers an API chatbot mode and a local Ollama chatbot mode.

**Important:** The initial ML target is next-hour PM2.5 concentration, not India's official CPCB AQI. The API's US and European AQI indices use their own scales. Do not present them as CPCB values.

## Setup (macOS / Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## API chatbot

Add your API key to `.env`:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

Keep `.env` private. Never paste your key into GitHub, screenshots, or public chats. API usage may incur charges; check the provider's current pricing and account requirements first.

## Local chatbot with Ollama

1. Install Ollama from https://ollama.com/download
2. In a terminal, download a small model:

```bash
ollama pull gemma3:1b
```

3. Make sure Ollama is running, then select **Local model (Ollama)** in the app.

Local model speed depends on your computer's memory and hardware.

## Data source

Open-Meteo Air Quality API:
https://open-meteo.com/en/docs/air-quality-api

The app requests up to 30 past days and 2 forecast days. Availability and spatial resolution depend on the provider's atmospheric model.

## Current limitations

- This is a prototype, not a certified air-quality monitoring instrument.
- Provider data are model-based estimates/forecasts, not necessarily readings from a nearby physical monitoring station.
- The first ML model is a baseline. Its test MAE should be reported honestly, and performance may vary by location and time.
- The chatbot can make mistakes. Verify scientific claims against reliable references.
