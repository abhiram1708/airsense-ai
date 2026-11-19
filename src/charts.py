"""Dependency-free SVG charts for the AirSense editorial layout.

Everything is rendered as plain SVG so the typography, colour bands and
spacing stay consistent with the rest of the site, and no chart runtime has
to load in the browser.
"""

from __future__ import annotations

import math
from datetime import datetime

import pandas as pd

from .aqi import AQI_BANDS, aqi_band


def _num(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _x(index: int, count: int, left: float, right: float) -> float:
    if count <= 1:
        return (left + right) / 2
    return left + (right - left) * index / (count - 1)


def _y(value: float, y_max: float, top: float, bottom: float) -> float:
    return bottom - (bottom - top) * max(0.0, min(value, y_max)) / y_max


def _fmt_time(value, span_hours: float) -> str:
    try:
        stamp = pd.to_datetime(value)
    except (TypeError, ValueError):
        return ""
    if span_hours <= 30:
        return stamp.strftime("%H:%M")
    if span_hours <= 72:
        return stamp.strftime("%a %H:%M")
    if span_hours <= 24 * 8:
        return stamp.strftime("%a")
    return stamp.strftime("%d %b")


def _label_indices(count: int) -> list[int]:
    if count <= 1:
        return [0]
    desired = 6
    step = max(1, round((count - 1) / (desired - 1)))
    indices = list(range(0, count, step))
    if indices[-1] != count - 1:
        indices.append(count - 1)
    if len(indices) > 2 and indices[-1] - indices[-2] < max(2, step // 2):
        indices.pop(-2)
    return indices[:7]


def aqi_chart(
    times,
    values,
    *,
    lows=None,
    highs=None,
    y_max=None,
    height: int = 250,
    now_index: int | None = None,
    spans=None,
    chart_id: str = "chart",
    aria: str = "Air quality over time",
) -> str:
    """Render a responsive AQI line/area chart with subtle category bands.

    ``spans`` is an optional list of ``(start, end)`` timestamps to shade as
    recommended outdoor windows. ``lows``/``highs`` draw daily ranges behind
    the mean line.
    """
    stamps = list(pd.to_datetime(pd.Series(list(times)), errors="coerce"))
    numbers = [_num(value) for value in values]
    points = [(stamp, value) for stamp, value in zip(stamps, numbers) if value is not None and not pd.isna(stamp)]
    if not points:
        return '<div class="chart-empty">No series available for this window.</div>'

    stamps = [point[0] for point in points]
    numbers = [point[1] for point in points]
    count = len(points)
    span_hours = max(1.0, (stamps[-1] - stamps[0]).total_seconds() / 3600.0)

    if y_max is None:
        peak = max(numbers)
        y_max = max(150.0, math.ceil(peak * 1.12 / 50.0) * 50.0)
    y_max = float(max(50.0, y_max))

    width, top, bottom = 1000.0, 20.0, height - 34.0
    left, right = 40.0, 964.0
    plot_h = bottom - top
    base = bottom

    parts: list[str] = []
    parts.append(
        f'<svg viewBox="0 0 {int(width)} {height}" preserveAspectRatio="none" '
        f'role="img" aria-label="{aria}">'
    )
    parts.append(
        f'<defs><linearGradient id="{chart_id}-fill" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="#1f7a4f" stop-opacity=".22"/>'
        f'<stop offset="100%" stop-color="#1f7a4f" stop-opacity="0"/>'
        "</linearGradient></defs>"
    )

    # Category bands across the plot, clipped to the visible range.
    for band in AQI_BANDS:
        low, high = float(band["low"]), float(band["high"])
        if low >= y_max:
            break
        top_y = _y(min(high, y_max), y_max, top, bottom)
        bottom_y = _y(low, y_max, top, bottom)
        parts.append(
            f'<rect x="{left}" y="{top_y:.1f}" width="{right - left:.1f}" '
            f'height="{max(0.0, bottom_y - top_y):.1f}" fill="{band["color"]}" opacity=".055"/>'
        )

    # Horizontal grid lines and labels.
    ticks = [0, 50, 100, 150, 200, 300]
    for tick in ticks:
        if tick > y_max:
            continue
        y = _y(tick, y_max, top, bottom)
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" '
            'stroke="#e2ede7" stroke-width="1" stroke-dasharray="2 5"/>'
        )
        parts.append(
            f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" '
            'font-size="11" fill="#8b9c92" font-family="Instrument Sans, sans-serif">'
            f"{tick}</text>"
        )

    def xpos(index: int) -> float:
        return _x(index, count, left, right)

    # Recommended windows.
    if spans:
        for start, end in spans:
            try:
                start_ts, end_ts = pd.to_datetime(start), pd.to_datetime(end)
            except (TypeError, ValueError):
                continue
            idx = [i for i, stamp in enumerate(stamps) if start_ts <= stamp <= end_ts]
            if not idx:
                continue
            x1, x2 = xpos(idx[0]), xpos(idx[-1])
            parts.append(
                f'<rect x="{x1:.1f}" y="{top}" width="{max(6.0, x2 - x1):.1f}" '
                f'height="{plot_h:.1f}" fill="#1f7a4f" opacity=".12"/>'
            )

    # Daily ranges behind the mean line.
    if lows is not None and highs is not None:
        low_values = [_num(value) for value in lows]
        high_values = [_num(value) for value in highs]
        for index, (low, high) in enumerate(zip(low_values, high_values)):
            if low is None or high is None:
                continue
            x = xpos(index)
            parts.append(
                f'<line x1="{x:.1f}" y1="{_y(low, y_max, top, bottom):.1f}" '
                f'x2="{x:.1f}" y2="{_y(high, y_max, top, bottom):.1f}" '
                'stroke="#9fc4b1" stroke-width="3" stroke-linecap="round" opacity=".75"/>'
            )

    line_points = " ".join(f"{xpos(i):.1f},{_y(value, y_max, top, bottom):.1f}" for i, value in enumerate(numbers))
    area_points = (
        f"{xpos(0):.1f},{base:.1f} "
        + line_points
        + f" {xpos(count - 1):.1f},{base:.1f}"
    )
    parts.append(f'<polygon points="{area_points}" fill="url(#{chart_id}-fill)"/>')
    parts.append(
        f'<polyline points="{line_points}" fill="none" stroke="#1f7a4f" '
        'stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>'
    )

    # "Now" marker for forecasts.
    if now_index is not None and 0 <= now_index < count:
        x = xpos(now_index)
        parts.append(
            f'<line x1="{x:.1f}" y1="{top - 4}" x2="{x:.1f}" y2="{bottom}" '
            'stroke="#33473c" stroke-width="1" stroke-dasharray="3 4" opacity=".45"/>'
        )
        parts.append(
            f'<text x="{x + 6:.1f}" y="{top + 6}" font-size="10" fill="#64796c" '
            'font-family="Instrument Sans, sans-serif" letter-spacing=".08em">NOW</text>'
        )

    # Endpoint and peak markers.
    last_y = _y(numbers[-1], y_max, top, bottom)
    parts.append(f'<circle cx="{xpos(count - 1):.1f}" cy="{last_y:.1f}" r="4" fill="#1f7a4f"/>')
    parts.append(
        f'<circle cx="{xpos(count - 1):.1f}" cy="{last_y:.1f}" r="8" fill="#1f7a4f" opacity=".14"/>'
    )

    peak_index = max(range(count), key=lambda i: numbers[i])
    peak_value = numbers[peak_index]
    if peak_index != count - 1:
        px, py = xpos(peak_index), _y(peak_value, y_max, top, bottom)
        band = aqi_band(peak_value)
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.2" fill="{band["color"]}"/>')
        anchor = "end" if px > right - 90 else "start"
        offset = -12 if anchor == "end" else 12
        parts.append(
            f'<text x="{px + offset:.1f}" y="{max(top + 10, py - 12):.1f}" text-anchor="{anchor}" '
            'font-size="10.5" fill="#64796c" font-family="Instrument Sans, sans-serif">'
            f"peak {peak_value:.0f}</text>"
        )

    # X labels. Alternate labels are hidden on narrow screens via CSS.
    for order, index in enumerate(_label_indices(count)):
        alternate = " x-alt" if order % 2 else ""
        parts.append(
            f'<text class="x-tick{alternate}" x="{xpos(index):.1f}" y="{height - 12}" text-anchor="middle" '
            'font-size="10.5" fill="#8b9c92" font-family="Instrument Sans, sans-serif">'
            f"{_fmt_time(stamps[index], span_hours)}</text>"
        )

    parts.append("</svg>")
    return "".join(parts)


def chart_legend(peak_label: str = "US AQI") -> str:
    """Small category legend that sits under a chart."""
    keys = [band["name"] for band in AQI_BANDS[:5]]
    items = "".join(
        f'<span><i style="background:{band["color"]}"></i>{label}</span>'
        for band, label in zip(AQI_BANDS[:5], keys)
    )
    return f'<div class="chart-legend">{items}<span class="chart-unit">{peak_label}</span></div>'


def day_outlook_html(days: list[dict]) -> str:
    """Five-day strip: each item has date, mean, low, high, band."""
    cards = []
    for day in days:
        band = day["band"]
        span = max(1.0, float(day["high"]) - float(day["low"]))
        top = max(0.0, min(1.0, (float(day["high"]) - 50.0) / 250.0))
        cards.append(
            f'<div class="day-chip" style="--band:{band["color"]}">'
            f'<span class="day-name">{day["label"]}</span>'
            f'<span class="day-aqi">{float(day["mean"]):.0f}</span>'
            f'<span class="day-range">{float(day["low"]):.0f}–{float(day["high"]):.0f}</span>'
            f'<span class="day-bar"><i style="height:{max(18.0, min(100.0, 18.0 + top * 82)):.0f}%"></i></span>'
            f'<span class="day-band">{band["short"]}</span>'
            "</div>"
        )
    return '<div class="day-strip">' + "".join(cards) + "</div>"
