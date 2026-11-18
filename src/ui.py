"""HTML/CSS fragments for the AirSense interface.

These helpers keep the visual language in one place and return plain HTML
strings that Streamlit can render with ``unsafe_allow_html``.
"""

from __future__ import annotations

import base64
import html
import math
from datetime import timedelta

import pandas as pd

from .aqi import AQI_BANDS, aqi_band, aqi_fraction, aqi_index, is_missing

FONT_DISPLAY = "Fraunces, Georgia, serif"
FONT_BODY = "Space Grotesk, sans-serif"
FONT_MONO = "JetBrains Mono, monospace"


def esc(value) -> str:
    return html.escape(str(value)) if value is not None else ""


def svg_data_uri(markup: str) -> str:
    """Encode inline SVG for use in an <img>, which survives HTML sanitizing."""
    encoded = base64.b64encode(markup.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def fmt(value, digits: int = 1, fallback: str = "—") -> str:
    if is_missing(value):
        return fallback
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(numeric) >= 100:
        return f"{numeric:,.0f}"
    return f"{numeric:,.{digits}f}"


def ratio_color(ratio: float | None) -> str:
    if ratio is None:
        return "#8BA295"
    if ratio <= 1:
        return "#2FAE77"
    if ratio <= 2:
        return "#B08A1F"
    if ratio <= 4:
        return "#C9752C"
    return "#CF5150"


def sparkline_svg(values, color: str = "#1F7A4F", width: int = 160, height: int = 42) -> str:
    clean = [float(value) for value in values if not is_missing(value)]
    if len(clean) < 2:
        return ""
    if len(clean) > 48:
        clean = clean[-48:]
    low, high = min(clean), max(clean)
    span = (high - low) or 1.0
    step = width / (len(clean) - 1)
    points = [
        (index * step, height - 4 - ((value - low) / span) * (height - 9))
        for index, value in enumerate(clean)
    ]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area = f"M0,{height} L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points) + f" L{width},{height} Z"
    last_x, last_y = points[-1]
    safe = esc(color)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{safe}" stop-opacity=".22"/>'
        f'<stop offset="1" stop-color="{safe}" stop-opacity="0"/>'
        f"</linearGradient></defs>"
        f'<path d="{area}" fill="url(#g)"/>'
        f'<polyline points="{line}" fill="none" stroke="{safe}" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="2.4" fill="{safe}"/>'
        "</svg>"
    )
    return f'<img class="spark" src="{svg_data_uri(svg)}" alt="" aria-hidden="true"/>'


def brand_markup() -> str:
    mark_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none">'
        '<circle cx="16" cy="16" r="13" stroke="#1F7A4F" stroke-opacity=".28" stroke-width="1.2"/>'
        '<circle cx="16" cy="16" r="8" stroke="#1F7A4F" stroke-opacity=".5" stroke-width="1.2"/>'
        '<circle cx="16" cy="16" r="3" fill="#1F7A4F"/>'
        '<path d="M16 3v6M29 16h-5M16 29v-6M3 16h5" stroke="#1F7A4F" stroke-width="1.2"/>'
        "</svg>"
    )
    return f"""
    <div class="brand-block">
      <div class="brand-row">
        <span class="brand-mark" aria-hidden="true">
          <img src="{svg_data_uri(mark_svg)}" alt=""/>
        </span>
        <span class="brand-word">AIR<span>SENSE</span></span>
      </div>
      <div class="brand-tag">Atmospheric intelligence · v2.0</div>
    </div>
    """


def topbar_html(city: str, country: str, live: bool) -> str:
    mode = "LIVE FEED" if live else "SAMPLE MODE"
    mode_class = "live" if live else "demo"
    return f"""
    <div class="topbar">
      <div class="topbar-brand">
        <span class="brand-word small">AIR<span>SENSE</span></span>
        <span class="topbar-slash">/</span>
        <span class="topbar-sub">Atmospheric intelligence</span>
      </div>
      <div class="topbar-right">
        <span class="status-pill {mode_class}"><span class="pulse"></span>{mode}</span>
        <span class="topbar-place">{esc(city)}<span class="topbar-country"> · {esc(country)}</span></span>
      </div>
    </div>
    """


def section_head(eyebrow: str, title: str, copy: str = "") -> str:
    copy_html = f'<p class="section-copy">{esc(copy)}</p>' if copy else ""
    return f"""
    <div class="section-head">
      <div class="eyebrow">{esc(eyebrow)}</div>
      <h2 class="section-heading">{title}</h2>
      {copy_html}
    </div>
    """


def _polar(cx: float, cy: float, radius: float, degrees: float) -> tuple[float, float]:
    radians = math.radians(degrees)
    return cx + radius * math.cos(radians), cy + radius * math.sin(radians)


def _arc_path(cx: float, cy: float, radius: float, start: float, end: float) -> str:
    x1, y1 = _polar(cx, cy, radius, start)
    x2, y2 = _polar(cx, cy, radius, end)
    large = 1 if (end - start) > 180 else 0
    return f"M {x1:.2f} {y1:.2f} A {radius} {radius} 0 {large} 1 {x2:.2f} {y2:.2f}"


def gauge_html(value, band: dict, trend: dict, source: str, updated: str) -> str:
    band = band or aqi_band(value)
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = None

    start_angle = 150.0
    total_angle = 240.0
    segment = total_angle / len(AQI_BANDS)
    index = aqi_index(band)
    fraction = aqi_fraction(numeric) if numeric is not None else 0.0
    marker_angle = start_angle + (index + fraction) * segment

    arcs = []
    for position, item in enumerate(AQI_BANDS):
        arc_start = start_angle + position * segment + 2.4
        arc_end = start_angle + (position + 1) * segment - 2.4
        active = position == index and numeric is not None
        width = 13 if active else 9
        opacity = 1.0 if active else 0.42
        arcs.append(
            f'<path d="{_arc_path(130, 116, 92, arc_start, arc_end)}" fill="none" '
            f'stroke="{item["color"]}" stroke-width="{width}" stroke-linecap="round" opacity="{opacity}"/>'
        )

    ticks = []
    for position in range(len(AQI_BANDS) + 1):
        angle = start_angle + position * segment
        x1, y1 = _polar(130, 116, 103, angle)
        x2, y2 = _polar(130, 116, 110, angle)
        ticks.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="rgba(18,74,46,.22)" stroke-width="1"/>'
        )

    marker = ""
    if numeric is not None:
        marker_x, marker_y = _polar(130, 116, 92, marker_angle)
        marker = (
            f'<circle cx="{marker_x:.2f}" cy="{marker_y:.2f}" r="7.5" fill="#FFFFFF" '
            f'stroke="{band["color"]}" stroke-width="3" style="filter:drop-shadow(0 2px 5px rgba(22,68,44,.24))"/>'
            f'<circle cx="{marker_x:.2f}" cy="{marker_y:.2f}" r="2.2" fill="{band["color"]}"/>'
        )

    value_text = "—" if numeric is None else f"{numeric:,.0f}"
    trend_direction = trend.get("direction", "flat") if trend else "flat"
    trend_text = trend.get("text", "Trend unavailable") if trend else "Trend unavailable"

    widths = []
    for item in AQI_BANDS:
        widths.append(((item["high"] - item["low"] + 1) / 501.0) * 100.0)
    segments = "".join(
        f'<span class="scale-segment" style="width:{width:.3f}%;background:{item["color"]}" '
        f'title="{esc(item["name"])}"></span>'
        for width, item in zip(widths, AQI_BANDS)
    )
    marker_percent = 0.0 if numeric is None else max(0.0, min(100.0, numeric / 500.0 * 100.0))

    gauge_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 196">'
        f'<path d="{_arc_path(130, 116, 92, 150, 390)}" fill="none" stroke="rgba(18,74,46,.08)" '
        f'stroke-width="13" stroke-linecap="round"/>'
        f'{"".join(arcs)}{"".join(ticks)}{marker}'
        "</svg>"
    )

    return f"""
    <div class="gauge-card" style="--accent:{band["color"]};--accent-rgb:{band["rgb"]}">
      <div class="gauge-top">
        <span class="live-chip"><span class="pulse"></span>LIVE · PROVIDER AQI</span>
        <span class="gauge-time">{esc(updated)}</span>
      </div>
      <div class="gauge-shell">
        <img class="gauge-svg" src="{svg_data_uri(gauge_svg)}" alt="US AQI gauge showing {esc(value_text)} {esc(band["name"])}"/>
        <div class="gauge-readout">
          <span class="gauge-kicker">US AQI</span>
          <span class="gauge-number" style="color:{band["color"]}">{value_text}</span>
          <span class="gauge-cat">{esc(band["name"])}</span>
        </div>
      </div>
      <div class="aqi-scale" aria-hidden="true">
        <div class="scale-track">{segments}
          <span class="scale-marker" style="left:{marker_percent:.2f}%"></span>
        </div>
        <div class="scale-labels"><span>0</span><span>100</span><span>300</span><span>500</span></div>
      </div>
      <div class="gauge-foot">
        <span class="gauge-source">{esc(source)}</span>
        <span class="trend-chip {trend_direction}">{esc(trend_text)}</span>
      </div>
    </div>
    """


def kpi_card(
    label: str,
    value,
    unit: str,
    accent: str,
    ratio: float | None = None,
    spark_values=None,
    footnote: str = "",
) -> str:
    ratio_html = ""
    if ratio is not None:
        color = ratio_color(ratio)
        ratio_html = f'<span class="kpi-ratio" style="color:{color};border-color:{color}33">{ratio:.1f}× WHO</span>'
    spark = sparkline_svg([] if spark_values is None else spark_values, color=accent)
    return f"""
    <div class="kpi-card" style="--accent:{accent}">
      <div class="kpi-top"><span class="kpi-label">{esc(label)}</span>{ratio_html}</div>
      <div class="kpi-main">
        <span class="kpi-value">{fmt(value)}</span>
        <span class="kpi-unit">{esc(unit)}</span>
      </div>
      {spark}
      <div class="kpi-foot">{esc(footnote)}</div>
    </div>
    """


def health_card(band: dict, value, source: str) -> str:
    value_text = "—" if is_missing(value) else f"{float(value):,.0f}"
    return f"""
    <div class="glass-card health-card" style="--accent:{band["color"]};--accent-rgb:{band["rgb"]}">
      <div class="card-topline">
        <span class="card-kicker">HEALTH ADVISORY</span>
        <span class="band-badge"><span class="band-dot"></span>{esc(band["name"])}</span>
      </div>
      <div class="health-headline">
        <span class="health-value">{value_text}</span>
        <span class="health-unit">US AQI</span>
      </div>
      <p class="health-copy">{esc(band["general"])}</p>
      <div class="health-divider"></div>
      <div class="health-sensitive">
        <span class="mini-label">SENSITIVE GROUPS</span>
        <p>{esc(band["sensitive"])}</p>
      </div>
      <div class="card-source">{esc(source)}</div>
    </div>
    """


def alert_banner(value, band: dict, peak: float | None, threshold: int, when: str = "") -> str:
    peak_text = "—" if is_missing(peak) else f"{float(peak):.0f}"
    when_text = f" · lowest-cost window check below" if not when else f" · peak near {esc(when)}"
    return f"""
    <div class="alert-banner" style="--accent:{band["color"]};--accent-rgb:{band["rgb"]}">
      <span class="alert-icon" aria-hidden="true">!</span>
      <div class="alert-body">
        <strong>AQI watch threshold reached</strong>
        <p>Current reading {fmt(value)} and the next-24h peak of <b>{peak_text}</b> US AQI cross your watch level of {int(threshold)}.{when_text}</p>
      </div>
      <span class="alert-tag">WATCH · {int(threshold)}</span>
    </div>
    """


def demo_banner(reason: str) -> str:
    return f"""
    <div class="demo-banner">
      <span class="demo-badge">SAMPLE DATA</span>
      <div>
        <strong>The live provider could not be reached.</strong>
        <p>AirSense is showing a deterministic sample atmosphere so you can explore every feature. Nothing on this screen is a real observation. <span class="demo-reason">{esc(reason)}</span></p>
      </div>
    </div>
    """


def composition_card(rows: list[dict], dominant: dict | None) -> str:
    if not rows:
        body = '<p class="empty-copy">No pollutant concentrations were returned for this location.</p>'
        dominant_html = ""
    else:
        body = ""
        for row in rows[:4]:
            ratio = row.get("ratio")
            width = 0.0 if ratio is None else max(1.5, min(100.0, ratio / 4.0 * 100.0))
            color = ratio_color(ratio)
            ratio_text = "—" if ratio is None else f"{ratio:.1f}×"
            body += f"""
            <div class="load-row">
              <div class="load-head">
                <span class="load-name">{esc(row["label"])}</span>
                <span class="load-value">{fmt(row["value"], 1)} <span class="load-unit">{esc(row["unit"])}</span></span>
                <span class="load-ratio" style="color:{color}">{ratio_text}</span>
              </div>
              <div class="load-track"><span class="load-fill" style="width:{width:.1f}%;background:{color}"></span><span class="load-tick"></span></div>
            </div>
            """
        if dominant:
            ratio = dominant.get("ratio")
            dominant_html = f"""
            <div class="dominant-note">
              <span class="mini-label">LEADING SIGNAL</span>
              <p><b style="color:{ratio_color(ratio)}">{esc(dominant["label"])}</b> is {ratio:.1f}× the WHO 24-hour reference guideline. It is the largest relative load in this snapshot.</p>
            </div>
            """
        else:
            dominant_html = ""
    return f"""
    <div class="glass-card">
      <div class="card-topline"><span class="card-kicker">POLLUTANT LOAD</span><span class="mono-chip">VS WHO 2021</span></div>
      <div class="load-list">{body}</div>
      {dominant_html}
      <div class="card-source">Concentrations are CAMS model estimates. Hourly values are compared with 24-hour guidelines for context only.</div>
    </div>
    """


def who_panel(rows: list[dict]) -> str:
    if not rows:
        return '<div class="glass-card"><p class="empty-copy">No comparable pollutant values are available.</p></div>'
    body = ""
    for row in rows:
        ratio = row.get("ratio")
        width = 0.0 if ratio is None else max(2.0, min(100.0, ratio / 4.0 * 100.0))
        color = ratio_color(ratio)
        ratio_text = "—" if ratio is None else f"{ratio:.1f}×"
        body += f"""
        <div class="who-row">
          <div class="who-name">{esc(row["label"])}<span>{esc(row["basis"])} guideline</span></div>
          <div class="who-track"><span class="who-fill" style="width:{width:.1f}%;background:{color}"></span><span class="who-marker"></span></div>
          <div class="who-reading">{fmt(row["value"], 2)} <span>{esc(row["unit"])}</span></div>
          <div class="who-guide">WHO {row["guideline"]:g} {esc(row["unit"])}</div>
          <div class="who-ratio" style="color:{color}">{ratio_text}</div>
        </div>
        """
    return f"""
    <div class="glass-card who-card">
      <div class="card-topline"><span class="card-kicker">GUIDELINE WATCH</span><span class="mono-chip">WHO AIR QUALITY GUIDELINES</span></div>
      <div class="who-head"><span>Pollutant</span><span>Relative load · marker at guideline</span><span>Now</span><span>Reference</span><span>Ratio</span></div>
      {body}
      <div class="card-source">WHO 2021 guideline values are 24-hour or 8-hour references; hourly CAMS values are not directly equivalent. The bar caps visually at 4×.</div>
    </div>
    """


def window_card_html(window: dict, number: int) -> str:
    band = window["band"]
    time_label = window["start"].strftime("%H:%M") + " – " + window["end"].strftime("%H:%M")
    return f"""
    <div class="window-card" style="--accent:{band["color"]}">
      <div class="window-top"><span class="window-index">0{number}</span><span class="window-tag">CLEANEST WINDOW</span></div>
      <div class="window-time">{time_label}</div>
      <div class="window-aqi" style="color:{band["color"]}">{window["mean"]:.0f}<span> US AQI</span></div>
      <div class="window-cat">{esc(band["name"])} · relative low point</div>
    </div>
    """


def stat_card(label: str, value: str, sub: str, accent: str = "#1F7A4F") -> str:
    return f"""
    <div class="stat-card" style="--accent:{accent}">
      <div class="stat-label">{esc(label)}</div>
      <div class="stat-value">{value}</div>
      <div class="stat-sub">{esc(sub)}</div>
    </div>
    """


def heatmap_html(frame: pd.DataFrame) -> str:
    if frame is None or frame.empty:
        return '<div class="glass-card"><p class="empty-copy">Not enough hourly history for a heatmap yet.</p></div>'

    dates = list(dict.fromkeys(frame["date"].tolist()))
    lookup = {(row.date, int(row.hour)): row for row in frame.itertuples()}
    header = '<div class="heat-head"><span></span>' + "".join(
        f'<span>{hour:02d}</span>' if hour % 3 == 0 else "<span></span>" for hour in range(24)
    ) + "</div>"

    rows = ""
    for date in dates:
        sample = frame[frame["date"] == date].iloc[0]
        cells = ""
        for hour in range(24):
            row = lookup.get((date, hour))
            if row is None:
                cells += '<span class="heat-cell empty" title="No data"></span>'
            else:
                label = f"{row.date_label} {hour:02d}:00 · US AQI {row.us_aqi:.0f} · {row.category}"
                cells += (
                    f'<span class="heat-cell" style="background:{row.color}" '
                    f'title="{esc(label)}"></span>'
                )
        rows += f'<div class="heat-row"><span class="heat-day">{esc(sample.date_label)}</span>{cells}</div>'

    legend = "".join(
        f'<span class="legend-item"><span class="legend-dot" style="background:{band["color"]}"></span>{esc(band["short"])}</span>'
        for band in AQI_BANDS
    )
    return f"""
    <div class="glass-card heat-card">
      <div class="card-topline"><span class="card-kicker">SEVEN-DAY PULSE</span><span class="mono-chip">HOURLY US AQI</span></div>
      <div class="heat-grid">{header}{rows}</div>
      <div class="heat-legend">{legend}</div>
      <div class="card-source">Hover any cell for the timestamp and category. Colour is the US AQI band, not a station measurement.</div>
    </div>
    """


def exposure_metric(label: str, value: str, unit: str, sub: str, accent: str) -> str:
    return f"""
    <div class="exposure-metric" style="--accent:{accent}">
      <span class="stat-label">{esc(label)}</span>
      <div class="exposure-value">{value}<span>{esc(unit)}</span></div>
      <div class="stat-sub">{esc(sub)}</div>
    </div>
    """


def index_meter(value: float, summary: str, interpretation: str) -> str:
    value = max(0.0, min(100.0, float(value)))
    color = "#2FAE77" if value < 34 else ("#B08A1F" if value < 67 else "#C4513F")
    return f"""
    <div class="glass-card index-card" style="--accent:{color}">
      <div class="card-topline"><span class="card-kicker">RELATIVE RESPONSE INDEX</span><span class="mono-chip">0–100 · NOT CONCENTRATION</span></div>
      <div class="index-value">{value:.0f}<span>/ 100</span></div>
      <div class="index-track"><span style="width:{value:.1f}%;background:linear-gradient(90deg,#2FAE77,#C9A227,#C4513F)"></span></div>
      <p class="index-summary">{esc(summary)}</p>
      <div class="health-divider"></div>
      <p class="index-interpretation">{esc(interpretation)}</p>
      <div class="card-source">Dimensionless teaching model. This is not ozone concentration, AQI, or validated chemical kinetics.</div>
    </div>
    """


def pathway_grid(items: list[tuple[str, str, str]]) -> str:
    cards = "".join(
        f"""
        <div class="pathway-card">
          <span class="pathway-number">{esc(number)}</span>
          <div>
            <h4>{esc(title)}</h4>
            <p>{esc(body)}</p>
          </div>
        </div>
        """
        for number, title, body in items
    )
    return f'<div class="pathway-grid">{cards}</div>'


def sidebar_aqi_html(value, band: dict, source: str) -> str:
    value_text = "—" if is_missing(value) else f"{float(value):,.0f}"
    percent = 0.0 if is_missing(value) else max(0.0, min(100.0, float(value) / 500.0 * 100.0))
    return f"""
    <div class="side-aqi" style="--accent:{band["color"]};--accent-rgb:{band["rgb"]}">
      <div class="side-aqi-top"><span>US AQI · NOW</span><span class="pulse"></span></div>
      <div class="side-aqi-value">{value_text}</div>
      <div class="side-aqi-cat">{esc(band["name"])}</div>
      <div class="side-aqi-track"><span style="width:{percent:.1f}%;background:{band["color"]}"></span></div>
      <div class="side-aqi-copy">{esc(source)}</div>
    </div>
    """


def stats_grid(items: list[tuple[str, str, str, str]]) -> str:
    cards = "".join(stat_card(label, value, sub, accent) for label, value, sub, accent in items)
    return f'<div class="stats-grid">{cards}</div>'


def footer_html() -> str:
    return """
    <div class="site-footer">
      <div class="footer-brand">
        <span class="brand-word small">AIR<span>SENSE</span></span>
        <p>An open atmospheric intelligence platform for reading the air, understanding its chemistry and exploring what comes next.</p>
      </div>
      <div class="footer-col">
        <span class="footer-label">DATA</span>
        <span>Open-Meteo · CAMS</span>
        <span>CPCB station mirror</span>
        <span>Model-based estimates</span>
      </div>
      <div class="footer-col">
        <span class="footer-label">MODELS</span>
        <span>Random Forest baseline</span>
        <span>US EPA AQI categories</span>
        <span>WHO 2021 references</span>
      </div>
      <div class="footer-note">
        <span class="footer-label">A NOTE ON CERTAINTY</span>
        <p>AirSense distinguishes observations, model estimates and educational simulations. It is not a regulatory monitor and does not provide medical advice.</p>
      </div>
    </div>
    <div class="footer-rule">
      <span>© 2026 AIRSENSE</span>
      <span>BUILT FOR CURIOUS BREATHERS</span>
    </div>
    """
