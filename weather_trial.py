from weather_utils import get_weather

# Example coordinates (MG Road, Bengaluru)
lat, lon = 12.975, 77.605

weather_info = get_weather(lat, lon, realtime=True)

print("\n✅ Weather API Test Result:")
print(weather_info)
