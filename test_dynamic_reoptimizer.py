# test_dynamic_reoptimizer.py
from dynamic_reoptimizer import reoptimize_itinerary
import datetime

# Example current state
current_location = (12.9716, 77.5946)  # Central Bengaluru
current_time_minutes = 600  # e.g., 10:00 AM

# Example remaining POIs (dummy data for test)
remaining_pois = [
    {"name": "Cubbon Park", "lat": 12.9763, "lon": 77.5929, "priority": 5, "dwell": 60, "fixed_start": None, "is_break": False},
    {"name": "Lalbagh Botanical Garden", "lat": 12.9507, "lon": 77.5848, "priority": 4, "dwell": 45, "fixed_start": None, "is_break": False},
    {"name": "Commercial Street", "lat": 12.9761, "lon": 77.6051, "priority": 3, "dwell": 30, "fixed_start": None, "is_break": False}
]

# Run reoptimizer
result = reoptimize_itinerary(
    current_location=current_location,
    current_time_minutes=current_time_minutes,
    remaining_pois=remaining_pois,
    mode="driving",
    realtime_weather=False  # Use dummy weather to avoid API calls in test
)

# Print results
print("\n🚀 Dynamic Reoptimization Test Result:\n")
print(f"Optimized Sequence (names): {[p['name'] for p in result['optimized_sequence']]}")
print(f"Total Duration: {result['total_duration_sec'] // 60} minutes")
print(f"Total Distance: {result['total_distance_m'] / 1000:.2f} km")
print(f"Computation Timestamp: {result['timestamp']}")
print("\nLegs detail:")
for leg in result["legs"]:
    print(f" - {leg[0]} → {leg[1]}: {leg[2] // 60} mins, {leg[3] / 1000:.2f} km")
