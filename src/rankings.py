"""City and country rankings for AirSense.

A single Open-Meteo request returns the current model reading for many
coordinates at once. Values are CAMS-based estimates, refreshed every
15 minutes, and are only meant for comparison — not regulatory reporting.
"""

from __future__ import annotations

import requests

from .air_quality import AIR_QUALITY_URL, POLLUTANT_COLUMNS

CURRENT_FIELDS = "us_aqi," + ",".join(POLLUTANT_COLUMNS)

# One representative city per country for the country board, so every
# country is compared on the same basis instead of averaging unequal samples.
REPRESENTATIVE = {
    "India": "Delhi",
    "China": "Beijing",
    "Japan": "Tokyo",
    "South Korea": "Seoul",
    "Singapore": "Singapore",
    "Indonesia": "Jakarta",
    "Thailand": "Bangkok",
    "Bangladesh": "Dhaka",
    "Pakistan": "Karachi",
    "Nepal": "Kathmandu",
    "United Arab Emirates": "Dubai",
    "Egypt": "Cairo",
    "Nigeria": "Lagos",
    "Kenya": "Nairobi",
    "South Africa": "Johannesburg",
    "United Kingdom": "London",
    "France": "Paris",
    "Spain": "Madrid",
    "Germany": "Berlin",
    "Italy": "Rome",
    "Russia": "Moscow",
    "United States": "New York",
    "Mexico": "Mexico City",
    "Brazil": "São Paulo",
    "Argentina": "Buenos Aires",
    "Peru": "Lima",
    "Australia": "Sydney",
}


CITIES = [
    # India — the local board.
    {"name": "Delhi", "country": "India", "region": "India", "latitude": 28.6139, "longitude": 77.2090},
    {"name": "Mumbai", "country": "India", "region": "India", "latitude": 19.0760, "longitude": 72.8777},
    {"name": "Kolkata", "country": "India", "region": "India", "latitude": 22.5726, "longitude": 88.3639},
    {"name": "Bengaluru", "country": "India", "region": "India", "latitude": 12.9716, "longitude": 77.5946},
    {"name": "Chennai", "country": "India", "region": "India", "latitude": 13.0827, "longitude": 80.2707},
    {"name": "Hyderabad", "country": "India", "region": "India", "latitude": 17.3850, "longitude": 78.4867},
    {"name": "Pune", "country": "India", "region": "India", "latitude": 18.5204, "longitude": 73.8567},
    {"name": "Ahmedabad", "country": "India", "region": "India", "latitude": 23.0225, "longitude": 72.5714},
    {"name": "Jaipur", "country": "India", "region": "India", "latitude": 26.9124, "longitude": 75.7873},
    {"name": "Lucknow", "country": "India", "region": "India", "latitude": 26.8467, "longitude": 80.9462},
    {"name": "Patna", "country": "India", "region": "India", "latitude": 25.5941, "longitude": 85.1376},
    {"name": "Guwahati", "country": "India", "region": "India", "latitude": 26.1445, "longitude": 91.7362},
    # World board.
    {"name": "Beijing", "country": "China", "region": "World", "latitude": 39.9042, "longitude": 116.4074},
    {"name": "Shanghai", "country": "China", "region": "World", "latitude": 31.2304, "longitude": 121.4737},
    {"name": "Tokyo", "country": "Japan", "region": "World", "latitude": 35.6762, "longitude": 139.6503},
    {"name": "Seoul", "country": "South Korea", "region": "World", "latitude": 37.5665, "longitude": 126.9780},
    {"name": "Singapore", "country": "Singapore", "region": "World", "latitude": 1.3521, "longitude": 103.8198},
    {"name": "Jakarta", "country": "Indonesia", "region": "World", "latitude": -6.2088, "longitude": 106.8456},
    {"name": "Bangkok", "country": "Thailand", "region": "World", "latitude": 13.7563, "longitude": 100.5018},
    {"name": "Dhaka", "country": "Bangladesh", "region": "World", "latitude": 23.8103, "longitude": 90.4125},
    {"name": "Karachi", "country": "Pakistan", "region": "World", "latitude": 24.8607, "longitude": 67.0011},
    {"name": "Kathmandu", "country": "Nepal", "region": "World", "latitude": 27.7172, "longitude": 85.3240},
    {"name": "Dubai", "country": "United Arab Emirates", "region": "World", "latitude": 25.2048, "longitude": 55.2708},
    {"name": "Cairo", "country": "Egypt", "region": "World", "latitude": 30.0444, "longitude": 31.2357},
    {"name": "Lagos", "country": "Nigeria", "region": "World", "latitude": 6.5244, "longitude": 3.3792},
    {"name": "Nairobi", "country": "Kenya", "region": "World", "latitude": -1.2921, "longitude": 36.8219},
    {"name": "Johannesburg", "country": "South Africa", "region": "World", "latitude": -26.2041, "longitude": 28.0473},
    {"name": "London", "country": "United Kingdom", "region": "World", "latitude": 51.5072, "longitude": -0.1276},
    {"name": "Paris", "country": "France", "region": "World", "latitude": 48.8566, "longitude": 2.3522},
    {"name": "Madrid", "country": "Spain", "region": "World", "latitude": 40.4168, "longitude": -3.7038},
    {"name": "Berlin", "country": "Germany", "region": "World", "latitude": 52.5200, "longitude": 13.4050},
    {"name": "Rome", "country": "Italy", "region": "World", "latitude": 41.9028, "longitude": 12.4964},
    {"name": "Moscow", "country": "Russia", "region": "World", "latitude": 55.7558, "longitude": 37.6173},
    {"name": "New York", "country": "United States", "region": "World", "latitude": 40.7128, "longitude": -74.0060},
    {"name": "Los Angeles", "country": "United States", "region": "World", "latitude": 34.0522, "longitude": -118.2437},
    {"name": "Mexico City", "country": "Mexico", "region": "World", "latitude": 19.4326, "longitude": -99.1332},
    {"name": "São Paulo", "country": "Brazil", "region": "World", "latitude": -23.5505, "longitude": -46.6333},
    {"name": "Buenos Aires", "country": "Argentina", "region": "World", "latitude": -34.6037, "longitude": -58.3816},
    {"name": "Lima", "country": "Peru", "region": "World", "latitude": -12.0464, "longitude": -77.0428},
    {"name": "Sydney", "country": "Australia", "region": "World", "latitude": -33.8688, "longitude": 151.2093},
]


def fetch_ranked_cities() -> list[dict]:
    """Current readings for every ranking city, in one batched request."""
    params = {
        "latitude": ",".join(str(city["latitude"]) for city in CITIES),
        "longitude": ",".join(str(city["longitude"]) for city in CITIES),
        "current": CURRENT_FIELDS,
        "timezone": "auto",
    }
    response = requests.get(AIR_QUALITY_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise ValueError("The ranking provider returned an unexpected response.")

    rows = []
    for city, item in zip(CITIES, payload):
        current = (item or {}).get("current") or {}
        try:
            aqi = float(current.get("us_aqi"))
        except (TypeError, ValueError):
            continue
        rows.append(
            {
                **city,
                "aqi": aqi,
                "time": current.get("time"),
                "pm2_5": current.get("pm2_5"),
                "pm10": current.get("pm10"),
                "ozone": current.get("ozone"),
                "nitrogen_dioxide": current.get("nitrogen_dioxide"),
                "sulphur_dioxide": current.get("sulphur_dioxide"),
                "carbon_monoxide": current.get("carbon_monoxide"),
            }
        )
    if not rows:
        raise ValueError("No ranking readings were available.")
    return rows


def sample_rankings() -> list[dict]:
    """Deterministic sample board for provider outages.

    The interface labels these values as sample data, exactly like the rest of
    the page when the live feed is unreachable.
    """
    from .demo import demo_payload

    rows = []
    for city in CITIES:
        payload = demo_payload(city["name"], city["country"], days_past=1, days_forecast=0)
        current = payload.get("current") or {}
        try:
            aqi = float(current.get("us_aqi"))
        except (TypeError, ValueError):
            continue
        rows.append(
            {
                **city,
                "aqi": aqi,
                "time": current.get("time"),
                "pm2_5": current.get("pm2_5"),
                "pm10": current.get("pm10"),
                "ozone": current.get("ozone"),
                "nitrogen_dioxide": current.get("nitrogen_dioxide"),
                "sulphur_dioxide": current.get("sulphur_dioxide"),
                "carbon_monoxide": current.get("carbon_monoxide"),
                "is_sample": True,
            }
        )
    return rows


def _decorate(rows: list[dict], selected: dict | None) -> list[dict]:
    from .aqi import aqi_band

    ranked = sorted(rows, key=lambda row: row["aqi"])
    selected_name = (selected or {}).get("name")
    for index, row in enumerate(ranked, start=1):
        band = aqi_band(row["aqi"])
        row["rank"] = index
        row["band"] = band
        row["is_selected"] = bool(selected_name and row["name"] == selected_name)
    return ranked


def city_ranking(selected: dict | None = None, scope: str = "India", readings: list[dict] | None = None) -> dict:
    """Rank cities by current AQI. ``scope`` is India or World."""
    rows = readings if readings is not None else fetch_ranked_cities()
    if scope == "India":
        board = [row for row in rows if row["country"] == "India"]
    else:
        board = [row for row in rows if row["region"] == "World"]

    selected_name = (selected or {}).get("name")
    selected_country = (selected or {}).get("country")
    # A city outside India belongs on the world board, never among Indian cities.
    can_join = scope != "India" or selected_country == "India"
    if selected and selected_name and can_join and not any(row["name"] == selected_name for row in board):
        try:
            board.append(
                {
                    "name": selected_name,
                    "country": selected_country or "",
                    "region": scope,
                    "aqi": float(selected.get("aqi") or 0),
                    "is_you": True,
                }
            )
        except (TypeError, ValueError):
            pass

    if not board:
        return {"available": False, "scope": scope, "rows": []}

    ranked = _decorate(board, selected)
    total = len(ranked)
    me = next((row for row in ranked if row["is_selected"]), None)
    cleanest = min(ranked, key=lambda row: row["aqi"])
    dirtiest = max(ranked, key=lambda row: row["aqi"])
    return {
        "available": True,
        "scope": scope,
        "rows": ranked,
        "total": total,
        "position": me["rank"] if me else None,
        "cleanest": cleanest,
        "dirtiest": dirtiest,
        "median": sorted(row["aqi"] for row in ranked)[total // 2],
    }


def country_ranking(selected: dict | None = None, readings: list[dict] | None = None) -> dict:
    """Rank countries by one representative city each.

    Comparing country averages would mix unequal sample sizes — India has
    twelve cities in the set while most countries have one — so every country
    is represented by the same kind of single-city reading.
    """
    from .aqi import aqi_band

    rows = readings if readings is not None else fetch_ranked_cities()
    chosen: dict[str, dict] = {}
    counts: dict[str, int] = {}
    for row in rows:
        country = row["country"]
        counts[country] = counts.get(country, 0) + 1
        preferred = REPRESENTATIVE.get(country)
        if country not in chosen or row["name"] == preferred:
            chosen[country] = row

    countries = []
    for country, row in chosen.items():
        countries.append(
            {
                "name": country,
                "country": country,
                "city": row["name"],
                "aqi": row["aqi"],
                "cities": counts[country],
                "band": aqi_band(row["aqi"]),
            }
        )
    ranked = sorted(countries, key=lambda row: row["aqi"])
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
        row["is_selected"] = bool(selected and row["name"] == (selected or {}).get("country"))

    if not ranked:
        return {"available": False, "scope": "Countries", "rows": []}

    me = next((row for row in ranked if row["is_selected"]), None)
    return {
        "available": True,
        "scope": "Countries",
        "rows": ranked,
        "total": len(ranked),
        "position": me["rank"] if me else None,
        "cleanest": ranked[0],
        "dirtiest": ranked[-1],
        "median": sorted(row["aqi"] for row in ranked)[len(ranked) // 2],
    }
