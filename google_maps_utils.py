# google_maps_utils.py
"""
Google Maps Utilities
- Provides travel time & distance between points
- Supports both Google Maps API (online) and Haversine fallback (offline/prototype)
- Handles geocoding text addresses into coordinates
"""

import os
import requests
from math import radians, sin, cos, sqrt, atan2
from dotenv import load_dotenv

# ----------------------------
# Load API Key
# ----------------------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

# ----------------------------
# Utility: Haversine distance (in meters)
# ----------------------------


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2) ** 2 + cos(radians(lat1)) * \
        cos(radians(lat2)) * sin(dlon/2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# ----------------------------
# Travel Time & Distance
# ----------------------------


def get_travel_time_distance(origin_lat, origin_lon, dest_lat, dest_lon,
                             mode="driving", use_api=True, traffic_model="best_guess"):
    """
    Returns travel time & distance between two coordinates.
    - If use_api=True → use Google Directions API
    - If use_api=False OR API fails → fallback to Haversine estimate

    Args:
        origin_lat, origin_lon : float
        dest_lat, dest_lon     : float
        mode                   : str ("driving","walking","bicycling","transit")
        use_api                : bool (default True)
        traffic_model          : str ("best_guess","pessimistic","optimistic") - only for driving
    Returns:
        (duration_sec, distance_meters)
    """
    # Track if we've already shown the billing warning
    if not hasattr(get_travel_time_distance, '_billing_warning_shown'):
        get_travel_time_distance._billing_warning_shown = False

    if use_api and GOOGLE_API_KEY:
        params = {
            "origin": f"{origin_lat},{origin_lon}",
            "destination": f"{dest_lat},{dest_lon}",
            "mode": mode,
            "key": GOOGLE_API_KEY
        }
        if mode == "driving":
            params["departure_time"] = "now"
            params["traffic_model"] = traffic_model

        try:
            response = requests.get(
                DIRECTIONS_URL,
                params=params,
                timeout=15,
                verify=True  # Ensure SSL verification is enabled
            )
            response.raise_for_status()  # Raise exception for bad status codes
            data = response.json()

            if data.get("status") == "OK":
                leg = data["routes"][0]["legs"][0]
                duration_sec = leg["duration"]["value"]
                distance_meters = leg["distance"]["value"]

                # --- Optional: consider traffic duration if available ---
                if "duration_in_traffic" in leg:
                    duration_sec = leg["duration_in_traffic"]["value"]

                # Safety check
                if distance_meters > 100000:  # >100 km → probably invalid
                    return 0, 0
                return duration_sec, distance_meters
            elif data.get("status") == "REQUEST_DENIED":
                if not get_travel_time_distance._billing_warning_shown:
                    print(f"⚠️ Google Maps API Billing Required")
                    print(f"   Using Haversine distance estimation as fallback.")
                    get_travel_time_distance._billing_warning_shown = True
            else:
                if not get_travel_time_distance._billing_warning_shown:
                    print(
                        f"⚠️ Google API error: {data.get('status')} - Using fallback estimation")
        except requests.exceptions.SSLError as e:
            if not get_travel_time_distance._billing_warning_shown:
                print(f"⚠️ SSL Error - Using fallback estimation")
                get_travel_time_distance._billing_warning_shown = True
        except requests.exceptions.RequestException as e:
            if not get_travel_time_distance._billing_warning_shown:
                print(f"⚠️ Network error - Using fallback estimation")
                get_travel_time_distance._billing_warning_shown = True
        except Exception as e:
            if not get_travel_time_distance._billing_warning_shown:
                print(f"⚠️ API error - Using fallback estimation")
                get_travel_time_distance._billing_warning_shown = True

    # --- Fallback ---
    distance_meters = haversine(origin_lat, origin_lon, dest_lat, dest_lon)
    avg_speed_mps = {
        "walking": 1.4,      # ~5 km/h
        "bicycling": 4.16,   # ~15 km/h
        "transit": 8.33,     # ~30 km/h
        "driving": 12.5      # ~45 km/h
    }.get(mode, 12.5)
    duration_sec = int(distance_meters / avg_speed_mps)
    return duration_sec, int(distance_meters)

# ----------------------------
# Geocode Address
# ----------------------------


def geocode_location(address: str, use_api=True):
    """
    Convert a text address (like 'MG Road, Bangalore' or 'Current Location')
    into latitude & longitude using Google Maps Geocoding API.
    - If use_api=False → fallback defaults
    """
    if address.lower() == "current location":
        # Placeholder until GPS integration
        return 12.975, 77.605

    if use_api and GOOGLE_API_KEY:
        params = {"address": address, "key": GOOGLE_API_KEY}
        try:
            response = requests.get(
                GEOCODE_URL, params=params, timeout=15).json()
            if response.get("status") == "OK":
                loc = response["results"][0]["geometry"]["location"]
                return loc["lat"], loc["lng"]
        except Exception as e:
            print(f"⚠️ Geocoding failed with API: {e}")

    # --- Fallback ---
    return None, None
