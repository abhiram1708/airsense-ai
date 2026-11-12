

import requests


def ask_science_assistant(prompt, context=None, history=None):
    question = prompt.lower()

    answers = {
        "pm2.5": (
            "PM2.5 refers to fine particulate matter with a diameter "
            "of 2.5 micrometres or smaller. It can enter deep into "
            "the respiratory system."
        ),
        "pm10": (
            "PM10 is particulate matter with a diameter of 10 "
            "micrometres or smaller. Sources include dust, roads "
            "and construction."
        ),
        "nitrogen dioxide": (
            "Nitrogen dioxide (NO2) is a reactive gas mainly produced "
            "by combustion, especially vehicle engines. It contributes "
            "to the formation of ground-level ozone."
        ),
        "ozone": (
            "Ground-level ozone is a secondary pollutant formed when "
            "nitrogen oxides and volatile organic compounds react "
            "in sunlight."
        ),
        "sulphur dioxide": (
            "Sulphur dioxide (SO2) is mainly released by burning "
            "sulphur-containing fuels. It can contribute to acid rain "
            "and particulate pollution."
        ),
        "acid rain": (
            "Acid rain forms when sulphur dioxide and nitrogen oxides "
            "react in the atmosphere to produce acidic compounds."
        ),
    }

    for keyword, answer in answers.items():
        if keyword in question:
            return answer

    if context and "current_readings" in context:
        readings = context["current_readings"]

        if "current air quality" in question or "current readings" in question:
            return (
                f"Current readings for {context.get('location', 'your location')}:\n\n"
                f"US AQI: {readings.get('us_aqi', 'N/A')}\n"
                f"European AQI: {readings.get('european_aqi', 'N/A')}\n"
                f"PM2.5: {readings.get('pm2_5', 'N/A')} μg/m³\n"
                f"PM10: {readings.get('pm10', 'N/A')} μg/m³"
            )

    return (
        "I can explain PM2.5, PM10, nitrogen dioxide, ozone, "
        "sulphur dioxide, acid rain and basic atmospheric chemistry. "
        "Try asking about one of these topics."
    )


def ask_local_model(prompt, context=None, history=None):
    messages = [
        {
            "role": "system",
            "content": (
                "You are AirSense, an assistant specialising in "
                "air quality, environmental science and atmospheric "
                "chemistry. Give clear, scientifically grounded answers."
            )
        }
    ]

    if context:
        messages.append({
            "role": "system",
            "content": f"Current air-quality context: {context}"
        })

    if history:
        messages.extend(history[-6:])

    messages.append({
        "role": "user",
        "content": prompt
    })

    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "gemma3:1b",
            "messages": messages,
            "stream": False
        },
        timeout=120
    )

    response.raise_for_status()
    return response.json()["message"]["content"]
