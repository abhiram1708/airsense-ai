import requests
import pandas as pd

AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

def fetch_air_quality(latitude: float, longitude: float) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "us_aqi,european_aqi,pm2_5,pm10,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone",
        "hourly": "pm2_5,pm10,nitrogen_dioxide,sulphur_dioxide,ozone",
        "past_days": 30,
        "forecast_days": 2,
        "timezone": "auto",
    }
    response = requests.get(AIR_QUALITY_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "current" not in data or "hourly" not in data:
        raise ValueError("The air-quality provider did not return the expected current/hourly data.")

    hourly = pd.DataFrame(data["hourly"])
    hourly["time"] = pd.to_datetime(hourly["time"])
    return {"current": data["current"], "hourly": hourly}
