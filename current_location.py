import requests

def get_current_location():
    try:
        resp = requests.get("https://ipinfo.io/json", timeout=5)
        data = resp.json()
        loc = data.get("loc")  # Format: "lat,lon"
        if loc:
            lat, lon = map(float, loc.split(","))
            return lat, lon
    except Exception as e:
        print("Error fetching location:", e)

    # Fallback if API fails
    return 12.9716, 77.5946  # MG Road, Bengaluru

# Example usage:
latitude, longitude = get_current_location()
print(f"Your current location is: Latitude={latitude}, Longitude={longitude}")
