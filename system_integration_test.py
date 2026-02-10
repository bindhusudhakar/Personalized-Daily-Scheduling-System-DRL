import datetime
from db_utils import get_connection, add_poi, add_user_pref
from context_utils import get_route_context
from dynamic_reoptimizer import reoptimize_itinerary
from itinerary_optimizer import compare_plans
from rl_env import ItineraryEnv
from stable_baselines3 import PPO

def simulate_user_session():
    print("\n🚀 Starting System Integration Test\n")

    # Step 1: Setup test data
    print("🔧 Adding sample POIs to DB...")
    sample_pois = [
        {"name": "Cubbon Park", "lat": 12.9763, "lon": 77.5929, "priority": 2, "dwell_mins": 60},
        {"name": "Lalbagh Botanical Garden", "lat": 12.9507, "lon": 77.5848, "priority": 1, "dwell_mins": 45},
        {"name": "Vidhana Soudha", "lat": 12.9799, "lon": 77.5913, "priority": 3, "dwell_mins": 30},
    ]

    for poi in sample_pois:
        add_user_pref("test_user", poi_id=1, priority=poi["priority"], time_spent=poi["dwell_mins"])

    # Step 2: Simulate user input for itinerary
    raw_entries = [(poi["name"], poi["priority"], poi["dwell_mins"]) for poi in sample_pois]
    mode = "driving"

    print("\n📋 Comparing Plans (User vs Optimized)...")
    plan_comparison = compare_plans(raw_entries, mode)

    print("\n🧱 User's Plan Sequence:")
    for poi in plan_comparison["user_plan"]["sequence"]:
        print(f" - {poi['name']} (Priority {poi['priority']})")

    print("\n✨ Optimized Plan Sequence:")
    for poi in plan_comparison["optimized_plan"]["sequence"]:
        print(f" - {poi['name']} (Priority {poi['priority']})")

    # Step 3: Fetch route context for first leg
    origin = (12.9763, 77.5929)  # Cubbon Park
    destination = (12.9507, 77.5848)  # Lalbagh
    context = get_route_context(origin, destination, mode, realtime_weather=True)

    print("\n📡 Fetched Context (First Leg):")
    print(f" Duration: {context['duration_sec']} sec | Distance: {context['distance_meters']} meters")
    print(f" Weather: {context['weather']}")

    # Step 4: Test Dynamic Reoptimization (simulate abrupt plan change)
    print("\n🔄 Simulating Dynamic Reoptimization...")
    new_pois = plan_comparison["optimized_plan"]["sequence"][:-1]  # Assume user skips last POI
    reoptimized_plan = dynamic_reoptimize(new_pois, available_time=240, mode=mode)

    print("\n✅ Reoptimized Plan after change:")
    for poi in reoptimized_plan:
        print(f" - {poi['name']} (Priority {poi['priority']})")

    print("\n🎉 System Integration Test Completed Successfully!\n")

if __name__ == "__main__":
    simulate_user_session()
