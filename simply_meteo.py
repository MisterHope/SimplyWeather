from dotenv import load_dotenv
load_dotenv()

import os

import requests
from datetime import datetime

API_TOKEN = os.environ["API_TOKEN"]
INSEE = os.environ["INSEE"]
TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT_ID = os.environ["TG_CHAT_ID"]


WEATHER_CODES = {
    # ciel
    0: "ensoleillé",
    1: "peu nuageux",
    2: "ciel voilé",
    3: "couvert",

    # brouillard
    4: "brouillard",
    5: "brume",
    6: "brume épaisse",

    # pluie
    10: "pluie faible",
    11: "pluie",
    12: "pluie forte",

    # averses
    20: "averses faibles",
    21: "averses",
    22: "averses fortes",

    # neige
    30: "neige",
    31: "neige modérée",
    32: "neige forte",

    # orages
    40: "orage",
    41: "orage fort",
}



# Mapping simplifié (à ajuster si besoin)
def simplify_weather(code):
    return WEATHER_CODES.get(code, None)



def get_forecast():
    url = f"https://api.meteo-concept.com/api/forecast/nextHours?token={API_TOKEN}&insee={INSEE}"
    r = requests.get(url)
    data = r.json()
#    print(data)
    return data["forecast"]

def filter_day_hours(forecast):
    result = []

    for f in forecast:
        dt = datetime.fromisoformat(f["datetime"])
        hour = dt.hour

        if 6 <= hour <= 22:
            weather = simplify_weather(f["weather"])

            if weather is None:
                continue

            result.append({
                "hour": hour,
                "weather": weather
            })

    return result

def group_periods(data):
    if not data:
        return []

    periods = []
    current = data[0]

    start = current["hour"]
    weather = current["weather"]

    for i in range(1, len(data)):
        if data[i]["weather"] != weather:
            periods.append((weather, start, data[i]["hour"]))
            start = data[i]["hour"]
            weather = data[i]["weather"]

    periods.append((weather, start, data[-1]["hour"]))
    return periods

def extract_temperatures(forecast):
    temps = []

    for f in forecast:
        dt = datetime.fromisoformat(f["datetime"])
        hour = dt.hour

        if 6 <= hour <= 22:
            temps.append({
                "hour": hour,
                "temp": f["temp2m"]
            })

    return temps

def analyze_temperatures(temps):
    values = [t["temp"] for t in temps]

    tmin = min(values)
    tmax = max(values)

    # tendance simple
    start = temps[0]["temp"]
    end = temps[-1]["temp"]

    if end > start + 1:
        trend = "hausse"
    elif end < start - 1:
        trend = "baisse"
    else:
        trend = "stable"

    return tmin, tmax, trend


def format_message(periods, tmin, tmax, trend):
    # --- Partie météo ---
    parts = []

    for i, (weather, start, end) in enumerate(periods):
        if i == 0:
            parts.append(f"{weather} jusqu’à {end}h")
        else:
            parts.append(f"puis {weather} jusqu’à {end}h")

    meteo_part = ", ".join(parts)

    # --- Partie température (fusionnée) ---
    if trend == "stable":
        temp_part = f"température stable entre {tmin}°C et {tmax}°C, c'est plutôt cool!"
    elif trend == "hausse":
        temp_part = f"température de {tmin}°C le matin, qui va monter jusqu’à {tmax}°C l’aprem (ça douille!)"
    else:
        temp_part = f"température de {tmax}°C le matin, qui va baisser jusqu’à {tmin}°C (glaglagla!)"

    # --- Message final ---
    return f"aujourd’hui, {meteo_part}\n{temp_part}"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TG_CHAT_ID,
        "text": msg
    })


if __name__ == "__main__":
    # 1. Récupération des données API
    forecast = get_forecast()

    # 2. Traitement météo (pluie / soleil / etc.)
    day_data = filter_day_hours(forecast)
    periods = group_periods(day_data)

    # 3. Traitement températures
    temps = extract_temperatures(forecast)
    tmin, tmax, trend = analyze_temperatures(temps)

    # 4. Génération du message final
    message = format_message(periods, tmin, tmax, trend)

    # 5. Debug local (optionnel)
    print(message)
    
    # 6. Envoi Telegram
    send_telegram(message)