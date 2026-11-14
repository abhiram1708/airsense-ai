# AirSense AI

A student-built air-quality monitoring and PM2.5 forecasting prototype.

## Features
- Current and hourly pollutant data from Open-Meteo Air Quality API.
- Provider-reported US AQI and European AQI shown separately.
- A Random Forest baseline estimating next-hour PM2.5 concentration.
- A free, rule-based scientific Q&A assistant for the public website.
- An optional local Gemma chatbot through Ollama on your Mac.

## Run locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## Local Gemma chatbot
Install Ollama from https://ollama.com/download, then run:
```bash
ollama pull gemma3:1b
ollama serve
```
If Ollama is already running as a Mac app, you do not need to run `ollama serve` again. Select **Gemma AI (local Mac)** in the app. This mode only works when the app can reach Ollama on the same machine. It will not work on Streamlit Community Cloud because the cloud server cannot access your Mac's localhost.

## Public deployment
Deploy the repository on Streamlit Community Cloud with `app.py` as the main file. The **Scientific Q&A (free)** assistant works without an AI API key. The local Gemma option is intended for local use only.

## Data and scientific limitations
- Open-Meteo data are provider model-based estimates/forecasts, not necessarily measurements from a nearby physical monitoring station.
- US AQI and European AQI are different scales and are not India's CPCB AQI.
- The ML target is next-hour PM2.5 concentration, not official CPCB AQI.
- The Random Forest is a baseline. Report the held-out MAE honestly; do not describe it as guaranteed forecasting accuracy.
- The scientific assistant uses curated responses and keyword matching, not a generative model.


## Chemistry lab and hosted AI

The Chemistry Lab uses a dimensionless educational ozone-response surface. Its controls are not measured concentrations and its index is not ozone concentration, AQI, or a validated chemical-kinetics result.

The Research Assistant uses a hosted OpenAI-compatible chat-completions API. For local development, copy `.env.example` to `.env` and add an API key you are authorised to use. For Streamlit Community Cloud, add `OPENAI_API_KEY` under App settings → Secrets. Never commit API keys. API access, billing and age eligibility are governed by the provider; a parent/guardian may need to set up and manage access.

The PM2.5 Random Forest remains a baseline next-hour concentration estimate, not an official AQI forecast.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 -m streamlit run app.py
```


## Location search

The app now searches place names through the Open-Meteo Geocoding API. Users select a matching city/place; coordinates are resolved internally and passed to the Air Quality API. The air-quality data are model-based CAMS products, not guaranteed nearby sensor observations. The spatial and temporal resolution depends on the selected CAMS domain.


## AQI standards and data provenance

- For Indian locations, AirSense shows CPCB National AQI only when an explicit station AQI value is available from the configured Government of India Open Data API. Add `DATA_GOV_IN_API_KEY` to `.env` locally or Streamlit Cloud Secrets.
- If the API key is missing, the station data are missing, or the response does not contain an explicit AQI field, the CPCB tile says unavailable. AirSense does not calculate or guess CPCB AQI from CAMS model concentrations.
- US AQI and European AQI are placed under an expandable comparison section. They are different index systems and are not interchangeable.
- Open-Meteo/CAMS pollutant values are labelled model-based estimates, not nearby station measurements.
- The official OGD dataset is published by CPCB / Ministry of Environment, Forest and Climate Change: https://www.data.gov.in/catalog/real-time-air-quality-index
- CPCB monitoring network and methodology documents: https://app.cpcbccr.com/ccr_docs

No CPCB developer key is used by this experimental public-dashboard connector. Never scrape or present data as official when the source cannot be verified.


## CPCB public dashboard integration

For Indian cities, AirSense attempts to retrieve explicit station-level AQI values using the public CPCB dashboard endpoints `aqi_station_all_india` and `aqi_all_Parameters`. No personal data.gov.in developer key is required for this route. These are undocumented dashboard endpoints, not a versioned or guaranteed API; CPCB may change or restrict them. If the interface fails or no explicit AQI is returned, AirSense displays unavailable. It never derives CPCB AQI from CAMS model concentrations and never averages stations into a citywide AQI. The displayed value is tied to a named monitoring station.

Endpoint behaviour reference (third-party client documentation, not an official API specification): https://saketlab.github.io/vayuayan/_modules/vayuayan/air_quality_client.html


## Local AI with Ollama

AirSense supports a local model through Ollama, so the Research Assistant does not require a hosted API key. Install Ollama from https://ollama.com and open it. In Terminal, download a model using Ollama's model picker or the command shown in its app/docs. Keep Ollama running, select **Local LLM · Ollama** in the AirSense sidebar, and enter the exact model tag installed on your Mac (the default UI value is `llama3.2:3b`). Local requests use `http://localhost:11434/api/chat`; no hosted key is used.

The India station panel uses a third-party public mirror of CPCB/data.gov.in pollutant observations. It is not an official CPCB API and does not provide a verified National AQI. AirSense therefore shows station-level pollutant readings without inventing a citywide AQI.
