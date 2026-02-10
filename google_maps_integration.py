"""POIs"""
import os
import requests
from dotenv import load_dotenv
from db_utils import add_poi

load_dotenv()

CATEGORY_MAPPING = {
    "restaurant": "Restaurant",
    "cafe": "Cafe",
    "bar": "Bar",
    "park": "Park",
    "museum": "Museum",
    "shopping_mall": "Shopping Mall",
    "movie_theater": "Movie Theater",
    "art_gallery": "Art Gallery",
    "hindu_temple": "Temple",
    "church": "Church",
    "mosque": "Mosque",
    "supermarket": "Supermarket",
    "atm": "ATM",
    "hospital": "Hospital",
    "pharmacy": "Pharmacy",
    "library": "Library",
    "zoo": "Zoo",
    "stadium": "Stadium"
}

print("Loaded API Key:", os.getenv("GOOGLE_API_KEY"))

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
BASE_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

def fetch_pois(poi_lat, poi_lon, radius=5000, place_type="restaurant"):
    """
    Fetch POIs from Google Maps API around a location.
    :param lat: Latitude of location
    :param lon: Longitude of location
    :param radius: Search radius in meters
    :param place_type: Type of POI (restaurant, park, cafe, museum, etc.)
    """
    params = {
        "location": f"{poi_lat},{poi_lon}",
        "radius": radius,
        "type": place_type,
        "key": GOOGLE_API_KEY
    }

    response = requests.get(BASE_URL, params=params, timeout=15)
    data = response.json()

    print("API Status:", data.get("status"))

    pois_list = []
    if "results" in data:
        for place in data["results"]:
            name = place.get("name")
            poi_lat = place["geometry"]["location"]["lat"]
            poi_lon = place["geometry"]["location"]["lng"]

            rating = place.get("rating", 0)
            # avg_dwell_time is just an estimate (default: 60 mins for demo)
            avg_dwell_time = 60

            # Map to friendly category
            friendly_category = CATEGORY_MAPPING.get(place_type, place_type)

             # Save both raw and friendly categories
            add_poi(
                name,
                place_type,          # raw_category
                friendly_category,   # friendly_category
                poi_lat,
                poi_lon,
                avg_dwell_time,
                rating
                )

    return pois_list

center_points = [
    ("MG Road", 12.9716, 77.5946),
    ("Whitefield", 12.9698, 77.7499),
    ("Electronic City", 12.8390, 77.6770),
    ("Yeshwanthpur", 13.0285, 77.5407),
    ("Hebbal", 13.0358, 77.5970)
]

poi_types = [
    "restaurant", "cafe", "bar", "park", "museum",
    "shopping_mall", "movie_theater", "art_gallery",
    "hindu_temple", "church", "mosque",
    "supermarket", "atm", "hospital", "pharmacy",
    "library", "zoo", "stadium"
]

if __name__ == "__main__":
    for area_name, lat, lon in center_points:
        for p_type in poi_types:
            print(f"Fetching {p_type}s near {area_name}...")
            pois = fetch_pois(lat, lon, radius=5000, place_type=p_type)
            print(f"Stored {len(pois)} {p_type}(s) for {area_name}")

# End-of-file