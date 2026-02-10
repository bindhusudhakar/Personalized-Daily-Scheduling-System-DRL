# weather_utils.py
import os
import requests
import random
from dotenv import load_dotenv

load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# ----------------------------
# Get weather (real-time or dummy)
# ----------------------------
def get_weather(lat: float, lon: float, realtime: bool = True) -> dict:
    """
    Fetch current weather for a given lat/lon.
    - If realtime=True: fetch from OpenWeather API
    - If realtime=False: return dummy weather (for training)
    Returns a dict with: {condition, temp_c, wind_speed, rain}
    """

    if realtime:
        params = {
            "lat": lat,
            "lon": lon,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }
        try:
            response = requests.get(OPENWEATHER_URL, params=params, timeout=10).json()
            if response.get("cod") == 200:
                condition = response["weather"][0]["main"]
                temp_c = response["main"]["temp"]
                wind_speed = response["wind"]["speed"]
                rain = response.get("rain", {}).get("1h", 0)  # mm in last hour
                return {
                    "condition": condition,
                    "temp_c": temp_c,
                    "wind_speed": wind_speed,
                    "rain": rain
                }
            else:
                print("⚠️ OpenWeather API failed:", response.get("message"))
        except Exception as e:
            print("⚠️ Weather API error:", e)

    # ----------------------------
    # Dummy weather for training
    # ----------------------------
    conditions = ["Clear", "Clouds", "Rain", "Thunderstorm", "Drizzle"]
    condition = random.choice(conditions)
    temp_c = round(random.uniform(20, 32), 1)
    wind_speed = round(random.uniform(0.5, 5.0), 1)
    rain = 0 if condition in ["Clear", "Clouds"] else round(random.uniform(0.1, 10.0), 1)

    return {
        "condition": condition,
        "temp_c": temp_c,
        "wind_speed": wind_speed,
        "rain": rain
    }


# ----------------------------
# Example test
# ----------------------------
if __name__ == "__main__":
    # Dummy training mode
    print("Dummy Weather:", get_weather(12.97, 77.59, realtime=False))

    # Real-time mode (Bengaluru)
    print("Realtime Weather:", get_weather(12.97, 77.59, realtime=True))
