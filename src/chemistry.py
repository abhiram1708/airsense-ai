
"""Transparent educational response model for photochemical ozone sensitivity.

This is not a chemical kinetics solver and does not estimate ambient ozone.
Inputs are dimensionless teaching controls on a 0-100 scale.
"""

def simulate_ozone_response(sunlight: float, nox: float, voc: float, regime: str = "Balanced sensitivity") -> dict:
    light, nitrogen_oxides, organics = [
        max(0.0, min(100.0, float(x))) for x in (sunlight, nox, voc)
    ]
    light_factor = light / 100.0
    nox_factor = nitrogen_oxides / (nitrogen_oxides + 25.0) if nitrogen_oxides else 0.0
    voc_factor = organics / (organics + 25.0) if organics else 0.0

    if regime == "VOC-limited tendency":
        precursor_factor = 0.25 * nox_factor + 0.75 * voc_factor
        interpretation = "This teaching scenario weights VOC availability more strongly. Real VOC-limited behaviour depends on VOC speciation and radical chemistry."
    elif regime == "NOx-limited tendency":
        precursor_factor = 0.75 * nox_factor + 0.25 * voc_factor
        interpretation = "This teaching scenario weights NOx availability more strongly. Real NOx-limited behaviour depends on background chemistry and transport."
    else:
        precursor_factor = (nox_factor * voc_factor) ** 0.5
        interpretation = "The balanced teaching scenario gives both precursor groups comparable influence. Actual ozone production is nonlinear and can change regimes across locations and times."

    index = max(0.0, min(100.0, 100.0 * light_factor * precursor_factor))
    if light < 10:
        summary = "Low sunlight input suppresses the photochemical response in this simplified model."
    elif nitrogen_oxides < 10 or organics < 10:
        summary = "One precursor input is very low, limiting the response represented by this teaching model."
    else:
        summary = "Sunlight and precursor inputs are available; this is a relative response, not an ozone mixing ratio."
    return {"index": index, "summary": summary, "interpretation": interpretation}
