import requests
import pandas as pd

AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


def search_locations(name: str, count: int = 8) -> list[dict]:
    """Resolve a place name to candidate locations and coordinates."""
    query = (name or "").strip()
    if len(query) < 2:
        raise ValueError("Enter at least two characters to search for a location.")
    response = requests.get(
        GEOCODING_URL,
        params={"name": query, "count": count, "language": "en", "format": "json"},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get("results") or []
    if not results:
        raise ValueError(f"No matching locations found for '{query}'. Try adding the state or country.")
    return results


POLLUTANT_COLUMNS = [
    "pm2_5",
    "pm10",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "carbon_monoxide",
]


def fetch_air_quality(latitude: float, longitude: float) -> dict:
    """Fetch current and hourly CAMS-based air quality from Open-Meteo.

    Returns provider-calculated US and European AQI values alongside hourly
    pollutant concentrations. These are model-based estimates, not station
    measurements.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "us_aqi,european_aqi,pm2_5,pm10,carbon_monoxide,"
            "nitrogen_dioxide,sulphur_dioxide,ozone"
        ),
        "hourly": (
            "us_aqi,european_aqi,pm2_5,pm10,nitrogen_dioxide,"
            "sulphur_dioxide,ozone,carbon_monoxide"
        ),
        "past_days": 30,
        "forecast_days": 5,
        "timezone": "auto",
    }
    # Short connect/read budget: the page falls back to labelled sample data
    # rather than leaving someone staring at a blank screen.
    response = requests.get(AIR_QUALITY_URL, params=params, timeout=(4, 8))
    response.raise_for_status()
    data = response.json()

    if "current" not in data or "hourly" not in data:
        raise ValueError("The air-quality provider did not return current and hourly data.")

    hourly = pd.DataFrame(data["hourly"])
    if "time" not in hourly.columns:
        raise ValueError("The provider response did not include hourly timestamps.")
    hourly["time"] = pd.to_datetime(hourly["time"], errors="coerce")
    for column in hourly.columns:
        if column != "time":
            hourly[column] = pd.to_numeric(hourly[column], errors="coerce")
    hourly = hourly.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)

    return {
        "current": data["current"],
        "hourly": hourly,
        "timezone": data.get("timezone", "auto"),
        "timezone_abbreviation": data.get("timezone_abbreviation", ""),
        "units": data.get("hourly_units", {}),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "elevation": data.get("elevation"),
        "is_demo": False,
    }


# Public mirror of CPCB/data.gov.in station pollutant observations.
# This feed does NOT provide an official CPCB AQI value; never derive one here.
CPCB_INDEX_URL = "https://snapdata.dev/api/v1/aqi/in/index.json"
CPCB_CITY_URL = "https://snapdata.dev/api/v1/aqi/in/city/{}.json"


def _city_slug(value):
    import re
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower())).strip("-")


def _records(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("records", "readings", "stations", "data", "results", "cities"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def fetch_cpcb_city_readings(city_name):
    """Return CPCB-origin station pollutant observations through a public mirror."""
    slug = _city_slug(city_name)
    if not slug:
        return {"records": [], "message": "Choose an Indian city first."}
    headers = {"User-Agent": "AirSense/1.1", "Accept": "application/json"}
    try:
        index_response = requests.get(CPCB_INDEX_URL, headers=headers, timeout=20)
        index_response.raise_for_status()
        index = index_response.json()
        selected_slug = slug
        for city_item in _records(index):
            if not isinstance(city_item, dict):
                continue
            name = city_item.get("city") or city_item.get("name") or city_item.get("label") or ""
            candidate = city_item.get("slug") or city_item.get("id")
            if candidate and (_city_slug(name) == slug or str(candidate).lower() == slug):
                selected_slug = str(candidate)
                break
        response = requests.get(CPCB_CITY_URL.format(selected_slug), headers=headers, timeout=25)
        response.raise_for_status()
        payload = response.json()
        rows = []
        for row in _records(payload):
            if not isinstance(row, dict):
                continue
            pollutant = row.get("pollutant") or row.get("pollutant_id") or row.get("parameter") or "—"
            rows.append({
                "Station": row.get("station") or row.get("station_name") or "—",
                "Pollutant": pollutant,
                "Average": row.get("avg", row.get("avg_value", row.get("average"))),
                "Minimum": row.get("min", row.get("min_value", row.get("minimum"))),
                "Maximum": row.get("max", row.get("max_value", row.get("maximum"))),
                "Unit": row.get("unit") or ("mg/m³" if str(pollutant).upper() == "CO" else "µg/m³"),
                "Updated": row.get("updated_at") or row.get("last_update") or "—",
            })
        return {"records": rows, "message": "CPCB/data.gov.in station observations via a third-party public mirror; not an official CPCB AQI feed."}
    except requests.RequestException as exc:
        return {"records": [], "message": f"Station observations could not be loaded from the public mirror: {exc}"}
    except (ValueError, TypeError) as exc:
        return {"records": [], "message": f"Station data response could not be interpreted: {exc}"}
