"""AQI classification, health guidance and derived analytics for AirSense.

US AQI categories follow the US EPA scale, including the 2024 PM2.5
breakpoint revision. Values supplied by Open-Meteo are provider-calculated.
Anything derived in this module is an indicative conversion for exploration,
never an official CPCB, EPA or station measurement.
"""

from __future__ import annotations

import math
from datetime import timedelta

import pandas as pd

AQI_BANDS = [
    {
        "low": 0,
        "high": 50,
        "name": "Good",
        "short": "Good",
        "color": "#2FAE77",
        "rgb": "47,174,119",
        "severity": 0,
        "general": "Air quality is satisfactory and air pollution poses little or no risk. Outdoor activity is fine for most people.",
        "sensitive": "No special precautions are needed for sensitive groups at this level.",
    },
    {
        "low": 51,
        "high": 100,
        "name": "Moderate",
        "short": "Moderate",
        "color": "#B08A1F",
        "rgb": "176,138,31",
        "severity": 1,
        "general": "Air quality is acceptable. There may be a mild concern for people who are unusually sensitive to air pollution.",
        "sensitive": "Unusually sensitive individuals should consider reducing prolonged or heavy outdoor exertion.",
    },
    {
        "low": 101,
        "high": 150,
        "name": "Unhealthy for sensitive groups",
        "short": "Sensitive groups",
        "color": "#C9752C",
        "rgb": "201,117,44",
        "severity": 2,
        "general": "Members of sensitive groups may experience effects. The general public is less likely to be affected.",
        "sensitive": "People with heart or lung conditions, older adults, children and pregnant people should reduce prolonged or heavy outdoor exertion.",
    },
    {
        "low": 151,
        "high": 200,
        "name": "Unhealthy",
        "short": "Unhealthy",
        "color": "#CF5150",
        "rgb": "207,81,80",
        "severity": 3,
        "general": "Some members of the general public may experience effects. Sensitive groups may feel more serious effects.",
        "sensitive": "Sensitive groups should avoid prolonged or heavy outdoor exertion and consider moving activity indoors.",
    },
    {
        "low": 201,
        "high": 300,
        "name": "Very unhealthy",
        "short": "Very unhealthy",
        "color": "#8E5CC4",
        "rgb": "142,92,196",
        "severity": 4,
        "general": "Health alert: everyone may experience more serious health effects. Avoid prolonged outdoor exertion.",
        "sensitive": "Sensitive groups should remain indoors where possible and keep outdoor activity brief.",
    },
    {
        "low": 301,
        "high": 500,
        "name": "Hazardous",
        "short": "Hazardous",
        "color": "#A33A50",
        "rgb": "163,58,80",
        "severity": 5,
        "general": "Emergency conditions: the entire population is likely to be affected. Avoid outdoor exertion.",
        "sensitive": "Stay indoors with windows closed and use filtered indoor air where available.",
    },
]

UNKNOWN_BAND = {
    "low": 0,
    "high": 500,
    "name": "Unavailable",
    "short": "Unavailable",
    "color": "#8BA295",
    "rgb": "139,162,149",
    "severity": 1,
    "general": "No AQI value is currently available for this location.",
    "sensitive": "Check the pollutant observations and try refreshing the feed.",
}

# US EPA PM2.5 breakpoints (2024 revision). Used only when a provider AQI is
# missing; the derived value is labelled as indicative in the interface.
PM25_AQI_BREAKPOINTS = [
    (0.0, 9.0, 0, 50),
    (9.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 125.4, 151, 200),
    (125.5, 225.4, 201, 300),
    (225.5, 325.4, 301, 500),
]

WHO_GUIDELINES = [
    {"key": "pm2_5", "label": "PM₂.₅", "guideline": 15.0, "unit": "µg/m³", "basis": "24-hour"},
    {"key": "pm10", "label": "PM₁₀", "guideline": 45.0, "unit": "µg/m³", "basis": "24-hour"},
    {"key": "nitrogen_dioxide", "label": "NO₂", "guideline": 25.0, "unit": "µg/m³", "basis": "24-hour"},
    {"key": "ozone", "label": "O₃", "guideline": 100.0, "unit": "µg/m³", "basis": "8-hour"},
    {"key": "sulphur_dioxide", "label": "SO₂", "guideline": 40.0, "unit": "µg/m³", "basis": "24-hour"},
    {"key": "carbon_monoxide", "label": "CO", "guideline": 4.0, "unit": "mg/m³", "basis": "24-hour"},
]

ACTIVITIES = {
    "Resting / desk work": {
        "ventilation": 6.0,
        "note": "Approximate adult ventilation while seated (about 6 L/min).",
    },
    "Light activity · walking": {
        "ventilation": 12.0,
        "note": "Approximate adult ventilation during light activity (about 12 L/min).",
    },
    "Moderate exercise · cycling": {
        "ventilation": 25.0,
        "note": "Approximate adult ventilation during moderate exercise (about 25 L/min).",
    },
    "Vigorous exercise · running": {
        "ventilation": 45.0,
        "note": "Approximate adult ventilation during vigorous exercise (about 45 L/min).",
    },
}


def is_missing(value) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def aqi_band(value) -> dict:
    """Return the US AQI category for a numeric value."""
    if is_missing(value):
        return UNKNOWN_BAND
    numeric = float(value)
    for band in AQI_BANDS:
        if numeric <= band["high"]:
            return band
    return AQI_BANDS[-1]


def aqi_index(band: dict) -> int:
    try:
        return AQI_BANDS.index(band)
    except ValueError:
        return 0


def aqi_fraction(value) -> float:
    """Fractional position of a value inside its own category (0-1)."""
    if is_missing(value):
        return 0.0
    band = aqi_band(value)
    span = max(1.0, float(band["high"] - band["low"] + 1))
    return max(0.0, min(1.0, (float(value) - band["low"]) / span))


def us_aqi_from_pm25(value) -> int | None:
    """Indicative US AQI from a PM2.5 concentration (µg/m³).

    Uses the 2024 EPA PM2.5 breakpoints. This is a deterministic conversion,
    not an official monitoring value.
    """
    if is_missing(value):
        return None
    concentration = max(0.0, float(value))
    for c_low, c_high, i_low, i_high in PM25_AQI_BREAKPOINTS:
        if concentration <= c_high:
            aqi = i_low + (i_high - i_low) * (concentration - c_low) / (c_high - c_low)
            return int(round(max(0.0, min(500.0, aqi))))
    return 500


def aqi_trend(hourly: pd.DataFrame, reference_time=None) -> dict:
    """Compare the latest 24 hours with the preceding 24 hours."""
    if hourly is None or hourly.empty or "us_aqi" not in hourly.columns:
        return {"available": False, "text": "Trend unavailable", "direction": "flat", "delta": None}
    frame = hourly.dropna(subset=["us_aqi"]).sort_values("time")
    if reference_time is not None:
        reference = pd.to_datetime(reference_time)
        frame = frame[frame["time"] <= reference]
    if len(frame) < 12:
        return {"available": False, "text": "Trend needs more data", "direction": "flat", "delta": None}

    latest_time = frame["time"].iloc[-1]
    recent = frame[frame["time"] > latest_time - timedelta(hours=24)]["us_aqi"]
    previous = frame[
        (frame["time"] <= latest_time - timedelta(hours=24))
        & (frame["time"] > latest_time - timedelta(hours=48))
    ]["us_aqi"]
    if recent.empty or previous.empty:
        return {"available": False, "text": "Trend needs more data", "direction": "flat", "delta": None}

    recent_mean = float(recent.mean())
    previous_mean = float(previous.mean())
    delta = recent_mean - previous_mean
    pct = (delta / previous_mean * 100.0) if previous_mean else 0.0
    if abs(pct) < 5:
        return {
            "available": True,
            "text": "Broadly steady vs previous 24h",
            "direction": "flat",
            "delta": pct,
            "recent_mean": recent_mean,
        }
    direction = "up" if delta > 0 else "down"
    arrow = "↑" if delta > 0 else "↓"
    return {
        "available": True,
        "text": f"{arrow} {abs(pct):.0f}% vs previous 24h",
        "direction": direction,
        "delta": pct,
        "recent_mean": recent_mean,
    }


def forecast_frame(hourly: pd.DataFrame, reference_time=None, hours: int = 48) -> pd.DataFrame:
    """Return the forward AQI window, classified by category."""
    if hourly is None or hourly.empty or "us_aqi" not in hourly.columns:
        return pd.DataFrame(columns=["time", "us_aqi", "category", "color", "label"])
    frame = hourly.copy()
    frame["us_aqi"] = pd.to_numeric(frame["us_aqi"], errors="coerce")
    if reference_time is not None:
        reference = pd.to_datetime(reference_time).floor("h")
        frame = frame[frame["time"] >= reference]
    else:
        latest = frame.loc[frame["us_aqi"].notna(), "time"].max()
        frame = frame[frame["time"] >= latest]
    frame = frame.dropna(subset=["us_aqi"]).sort_values("time").head(hours)
    if frame.empty:
        return pd.DataFrame(columns=["time", "us_aqi", "category", "color", "label"])
    bands = frame["us_aqi"].apply(aqi_band)
    frame = frame.copy()
    frame["category"] = bands.apply(lambda b: b["short"])
    frame["color"] = bands.apply(lambda b: b["color"])
    frame["label"] = bands.apply(lambda b: b["name"])
    return frame[["time", "us_aqi", "category", "color", "label"]]


def best_windows(times, values, window: int = 3, count: int = 3, horizon: int = 24) -> list[dict]:
    """Find the relative cleanest non-overlapping windows in a forecast."""
    frame = pd.DataFrame({"time": pd.to_datetime(times), "us_aqi": pd.to_numeric(values, errors="coerce")})
    frame = frame.dropna().sort_values("time").reset_index(drop=True).head(max(horizon, window))
    if len(frame) < window:
        return []
    frame["window_mean"] = frame["us_aqi"].rolling(window, min_periods=1).mean().shift(-(window - 1))
    candidates = frame.dropna(subset=["window_mean"]).sort_values("window_mean")
    chosen = []
    for _, row in candidates.iterrows():
        start = row["time"]
        end = start + timedelta(hours=window - 1)
        if any(abs((start - item["start"]).total_seconds()) < window * 3600 for item in chosen):
            continue
        band = aqi_band(row["window_mean"])
        chosen.append(
            {
                "start": start,
                "end": end,
                "mean": float(row["window_mean"]),
                "band": band,
            }
        )
        if len(chosen) >= count:
            break
    return sorted(chosen, key=lambda item: item["start"])


def daily_heatmap(hourly: pd.DataFrame, reference_time=None, days: int = 7) -> pd.DataFrame:
    """Long frame of hourly AQI for the previous N local days."""
    columns = ["time", "date", "hour", "us_aqi", "category", "color", "date_label"]
    if hourly is None or hourly.empty or "us_aqi" not in hourly.columns:
        return pd.DataFrame(columns=columns)
    frame = hourly.copy()
    frame["us_aqi"] = pd.to_numeric(frame["us_aqi"], errors="coerce")
    if reference_time is not None:
        reference = pd.to_datetime(reference_time)
    else:
        reference = frame["time"].max()
    start = (reference - timedelta(days=days)).floor("D")
    frame = frame[(frame["time"] >= start) & (frame["time"] <= reference)]
    frame = frame.dropna(subset=["us_aqi"]).sort_values("time")
    if frame.empty:
        return pd.DataFrame(columns=columns)
    frame = frame.copy()
    frame["date"] = frame["time"].dt.normalize()
    frame["hour"] = frame["time"].dt.hour
    bands = frame["us_aqi"].apply(aqi_band)
    frame["category"] = bands.apply(lambda b: b["short"])
    frame["color"] = bands.apply(lambda b: b["color"])
    frame["date_label"] = frame["time"].dt.strftime("%a %d")
    return frame[columns]


def daily_summary(hourly: pd.DataFrame, reference_time=None, days: int = 7) -> pd.DataFrame:
    frame = daily_heatmap(hourly, reference_time, days)
    if frame.empty:
        return pd.DataFrame(columns=["date", "date_label", "mean_aqi", "peak_aqi", "min_aqi", "hours"])
    grouped = (
        frame.groupby(["date", "date_label"], as_index=False)
        .agg(mean_aqi=("us_aqi", "mean"), peak_aqi=("us_aqi", "max"), min_aqi=("us_aqi", "min"), hours=("us_aqi", "count"))
        .sort_values("date")
    )
    return grouped


def seven_day_stats(hourly: pd.DataFrame, reference_time=None, days: int = 7) -> dict:
    frame = daily_heatmap(hourly, reference_time, days)
    if frame.empty:
        return {"available": False}
    values = frame["us_aqi"]
    clean_hours = int((values <= 50).sum())
    return {
        "available": True,
        "mean": float(values.mean()),
        "peak": float(values.max()),
        "clean_hours": clean_hours,
        "total_hours": int(values.count()),
        "clean_share": float(clean_hours / max(1, values.count()) * 100.0),
    }


def who_comparisons(values: dict) -> list[dict]:
    """Build WHO guideline comparison rows from a mapping of concentrations."""
    rows = []
    for guideline in WHO_GUIDELINES:
        key = guideline["key"]
        raw = values.get(key)
        if is_missing(raw):
            continue
        value = float(raw)
        unit = guideline["unit"]
        if key == "carbon_monoxide":
            value = value / 1000.0  # Open-Meteo supplies CO in µg/m³
        ratio = value / guideline["guideline"] if guideline["guideline"] else None
        rows.append(
            {
                **guideline,
                "value": value,
                "ratio": ratio,
            }
        )
    return rows


def dominant_pollutant(values: dict) -> dict | None:
    rows = [row for row in who_comparisons(values) if row.get("ratio") is not None]
    if not rows:
        return None
    return max(rows, key=lambda row: row["ratio"])


def exposure_stats(pm25, minutes: int, ventilation_l_min: float) -> dict:
    """Indicative inhaled PM2.5 mass for an activity scenario."""
    if is_missing(pm25):
        pm25_value = None
    else:
        pm25_value = max(0.0, float(pm25))
    minutes = max(0, int(minutes))
    ventilation = max(0.0, float(ventilation_l_min))
    volume_m3 = ventilation * minutes / 1000.0
    dose = (pm25_value or 0.0) * volume_m3
    reference_concentration = 15.0
    reference_dose = reference_concentration * volume_m3
    ratio = (dose / reference_dose) if reference_dose > 0 else 0.0
    return {
        "pm25": pm25_value,
        "minutes": minutes,
        "ventilation": ventilation,
        "volume_m3": volume_m3,
        "dose_ug": dose,
        "reference_dose_ug": reference_dose,
        "ratio": ratio,
        "reference_concentration": reference_concentration,
    }


def exposure_curve(pm25, ventilation_l_min: float, max_minutes: int = 240, step: int = 10) -> pd.DataFrame:
    minutes = list(range(0, max_minutes + step, step))
    rows = []
    for value in minutes:
        stats = exposure_stats(pm25, value, ventilation_l_min)
        rows.append(
            {
                "minutes": value,
                "dose_ug": stats["dose_ug"],
                "reference_ug": stats["reference_dose_ug"],
            }
        )
    return pd.DataFrame(rows)


def format_time(value) -> str:
    if is_missing(value):
        return "—"
    try:
        return pd.to_datetime(value).strftime("%d %b · %H:%M")
    except (ValueError, TypeError):
        return str(value)


def format_window(window: dict) -> str:
    start = window["start"].strftime("%H:%M")
    end = window["end"].strftime("%H:%M")
    same_day = window["start"].normalize() == window["end"].normalize()
    if same_day:
        return f"{start} – {end}"
    return f"{start} – next day {end}"


def compass(latitude: float, longitude: float) -> str:
    lat_dir = "N" if latitude >= 0 else "S"
    lon_dir = "E" if longitude >= 0 else "W"
    return f"{abs(latitude):.4f}° {lat_dir}  ·  {abs(longitude):.4f}° {lon_dir}"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
