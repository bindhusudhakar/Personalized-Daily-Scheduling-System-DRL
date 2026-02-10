# context_utils.py (STANDBY - save, don't run yet)
"""
Context utility to merge travel info, weather conditions, and user preferences.
This keeps rl_env and itinerary code clean by centralizing context gathering.
"""

from google_maps_utils import get_travel_time_distance
from weather_utils import get_weather

def get_route_context(origin, destination, mode="driving", realtime_weather=False):
    """
    Combines route info (distance, time) with weather data at destination.

    Args:
        origin: (lat, lon) tuple
        destination: (lat, lon) tuple
        mode: str, travel mode ("driving", "walking", etc.)
        realtime_weather: bool, if True -> call live API, else dummy

    Returns:
        dict {
            "duration_sec": int,
            "distance_meters": int,
            "weather": dict {...}
        }
    """
    duration_sec, distance_meters = get_travel_time_distance(
        origin[0], origin[1],
        destination[0], destination[1],
        mode=mode
    )

    weather = get_weather(destination[0], destination[1], realtime=realtime_weather)

    return {
        "duration_sec": duration_sec,
        "distance_meters": distance_meters,
        "weather": weather
    }

# ----------------------------
# Wrapper for compatibility
# ----------------------------
def safe_travel_time_and_distance(lat1, lon1, lat2, lon2, mode="driving", realtime_weather=False):
    """
    Wrapper so other modules can call a unified travel estimator.
    Returns (duration_sec, distance_meters).
    Weather is fetched but not returned here (kept internal for RL reward logic).
    """
    context = get_route_context((lat1, lon1), (lat2, lon2), mode=mode, realtime_weather=realtime_weather)
    return context["duration_sec"], context["distance_meters"]

