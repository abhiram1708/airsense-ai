"""Deterministic sample atmosphere for offline or provider-outage use.

The UI always labels this data as sample data. It exists so the interface can
be explored and deployed without silently pretending that synthetic values
are live observations.
"""

from __future__ import annotations

import zlib

import numpy as np
import pandas as pd

from .aqi import us_aqi_from_pm25


def demo_payload(city: str = "Bengaluru", country: str = "India", days_past: int = 30, days_forecast: int = 5) -> dict:
    seed = zlib.crc32(f"{city}|{country}".lower().encode("utf-8"))
    rng = np.random.default_rng(seed)

    now = pd.Timestamp.now().floor("h")
    start = now - pd.Timedelta(days=days_past)
    end = now + pd.Timedelta(days=days_forecast)
    times = pd.date_range(start=start, end=end, freq="h")
    hours = times.hour.to_numpy()
    position = np.arange(len(times))

    # A plausible urban diurnal cycle with morning and evening peaks.
    base = 20.0 + (seed % 42)
    diurnal = 13.0 * np.exp(-((hours - 8) / 3.0) ** 2) + 17.0 * np.exp(-((hours - 20) / 3.4) ** 2)
    synoptic = 9.0 * np.sin(position / 24.0 / 5.0 * 2 * np.pi + (seed % 10))
    noise = rng.normal(0, 3.2, len(times))
    pm25 = np.clip(base + diurnal + synoptic + noise, 4.0, 240.0)

    pm10 = np.clip(pm25 * 1.55 + rng.normal(0, 6, len(times)) + 6, 6.0, 400.0)
    nitrogen_dioxide = np.clip(pm25 * 0.62 + 8 + rng.normal(0, 3, len(times)), 2.0, 200.0)
    sulphur_dioxide = np.clip(pm25 * 0.18 + 2.5 + rng.normal(0, 1.5, len(times)), 0.5, 90.0)
    ozone = np.clip(52 + 34 * np.sin((hours - 8) / 24 * 2 * np.pi) + rng.normal(0, 6, len(times)), 6.0, 220.0)
    carbon_monoxide = np.clip(280 + pm25 * 13 + rng.normal(0, 70, len(times)), 60.0, 4200.0)

    us_aqi = [us_aqi_from_pm25(value) or 0 for value in pm25]

    hourly = pd.DataFrame(
        {
            "time": times,
            "us_aqi": us_aqi,
            "pm2_5": np.round(pm25, 1),
            "pm10": np.round(pm10, 1),
            "nitrogen_dioxide": np.round(nitrogen_dioxide, 1),
            "sulphur_dioxide": np.round(sulphur_dioxide, 1),
            "ozone": np.round(ozone, 1),
            "carbon_monoxide": np.round(carbon_monoxide, 0),
        }
    )

    current_row = hourly[hourly["time"] <= now].iloc[-1]
    current = {
        "time": now.strftime("%Y-%m-%dT%H:%M"),
        "interval": 3600,
        "us_aqi": int(current_row["us_aqi"]),
        "pm2_5": float(current_row["pm2_5"]),
        "pm10": float(current_row["pm10"]),
        "nitrogen_dioxide": float(current_row["nitrogen_dioxide"]),
        "sulphur_dioxide": float(current_row["sulphur_dioxide"]),
        "ozone": float(current_row["ozone"]),
        "carbon_monoxide": float(current_row["carbon_monoxide"]),
    }

    return {
        "current": current,
        "hourly": hourly,
        "timezone": "local timezone",
        "units": {},
        "is_demo": True,
    }
