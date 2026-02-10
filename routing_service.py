"""Routing Service: Fetches routes between POIs using Google Directions API"""
import sqlite3
import os
import requests
from dotenv import load_dotenv

# Load API Key
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

DB_NAME = "poi_cache.db"

def get_poi_coords(poi_name):
    """Fetch latitude & longitude of a POI by name (search in POIs, then fallback to poi_cache)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # First check POIs
    cursor.execute("""
        SELECT name, lat, lon FROM POIs WHERE LOWER(name) LIKE LOWER(?)
    """, (f"%{poi_name}%",))
    row = cursor.fetchone()

    # If not found, fallback to poi_cache
    if not row:
        cursor.execute("""
            SELECT name, lat, lon FROM poi_cache WHERE LOWER(name) LIKE LOWER(?)
        """, (f"%{poi_name}%",))
        row = cursor.fetchone()

    conn.close()

    if row:
        matched_name, lat, lon = row
        print(f"✅ Matched POI: {matched_name}")
        return lat, lon
    else:
        raise ValueError(f"POI '{poi_name}' not found in database (neither POIs nor poi_cache).")

def get_route(start_poi, end_poi, mode="driving"):
    """Fetch route between two POIs using Google Directions API"""
    start_lat, start_lon = get_poi_coords(start_poi)
    end_lat, end_lon = get_poi_coords(end_poi)

    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{start_lat},{start_lon}",
        "destination": f"{end_lat},{end_lon}",
        "mode": mode,
        "key": GOOGLE_API_KEY
    }

    response = requests.get(url, params=params, timeout=15)
    data = response.json()

    print(f"Fetching route from {start_poi} → {end_poi}...")
    print("API Status:", data["status"])

    if data["status"] != "OK":
        print("Error:", data.get("error_message", "No route found."))
        return None

    # Extract details
    route = data["routes"][0]["legs"][0]
    distance = route["distance"]["text"]
    duration = route["duration"]["text"]

    print(f"Distance: {distance}")
    print(f"Duration: {duration}")
    print("Steps:")
    for step in route["steps"]:
        instruction = step["html_instructions"]
        clean_instruction = instruction.replace("<b>", "").replace("</b>", "")
        clean_instruction = clean_instruction.replace("<div style=\"font-size:0.9em\">", " ").replace("</div>", "")
        print(" -", clean_instruction)

    return distance, duration


if __name__ == "__main__":
    # Example test
    try:
        get_route("Cubbon Park", "Lalbagh")
    except ValueError as e:
        print(e)
