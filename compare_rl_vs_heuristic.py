import datetime
import math
from stable_baselines3 import PPO
from rl_env import ItineraryEnv
from context_utils import get_route_context  # ✅ Correct import

# ----------------------------
# Example POIs
# ----------------------------
pois = [
    {"name": "Orion Mall", "lat": 13.0110, "lon": 77.5550, "dwell": 210,
        "priority": 5, "fixed_start": None, "is_break": False},
    {"name": "Lalbagh", "lat": 12.9507, "lon": 77.5848, "dwell": 60,
        "priority": 2, "fixed_start": None, "is_break": False},
    {"name": "Mantri Square", "lat": 12.9900, "lon": 77.5710, "dwell": 60,
        "priority": 4, "fixed_start": None, "is_break": False},
]

start_coords = (12.9716, 77.5946)   # Bengaluru Central
end_coords = start_coords           # set None for one-way

# ----------------------------
# Helper: Haversine (km)
# ----------------------------


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# ----------------------------
# Heuristic: Nearest Neighbor
# ----------------------------


def heuristic_plan(pois, start_coords, end_coords=None):
    unvisited = pois[:]
    seq = []
    curr = start_coords
    total_dist = 0.0

    while unvisited:
        nearest = min(unvisited, key=lambda p: haversine_km(
            curr[0], curr[1], p["lat"], p["lon"]))
        dist = haversine_km(curr[0], curr[1], nearest["lat"], nearest["lon"])
        total_dist += dist
        seq.append(nearest["name"])
        curr = (nearest["lat"], nearest["lon"])
        unvisited.remove(nearest)

    if end_coords:
        total_dist += haversine_km(curr[0],
                                   curr[1], end_coords[0], end_coords[1])
        seq.append("End (Round Trip)")
    else:
        seq.append("End (One-Way)")

    return seq, total_dist

# ----------------------------
# RL Plan
# ----------------------------


def rl_plan(pois, start_coords, start_time, end_coords=None):
    """
    Generate a plan using the trained RL model.
    """
    env = ItineraryEnv(pois, start_coords,
                       start_time=start_time, end_coords=end_coords)

    model = PPO.load("ppo_itinerary", env=env, device='cpu')

    obs, _ = env.reset()
    done, truncated = False, False
    rl_seq = []

    while not (done or truncated):
        action, _ = model.predict(obs, deterministic=True)
        poi = env.pois[action]

        route_info = get_route_context(
            origin=env.current_coords,
            destination=(poi["lat"], poi["lon"]),
            mode=poi.get("mode", "driving"),
            realtime_weather=False  # Set True later when integrating real-time weather
        )

        travel_sec = route_info["duration_sec"]
        dist_m = route_info["distance_meters"]

        # Simulate travel by advancing time
        env.current_time += datetime.timedelta(seconds=travel_sec)
        env.current_coords = (poi["lat"], poi["lon"])
        poi["visited"] = True

        rl_seq.append(poi["name"])

        obs, _, done, truncated, _ = env.step(action)

    if end_coords:
        rl_seq.append("End (Round Trip)")
    else:
        rl_seq.append("End (One-Way)")

    return rl_seq

# ----------------------------
# Compare Plans Function
# ----------------------------


def compare_plans(raw_entries, mode="driving"):
    """
    Compare heuristic and RL plans for the given POIs.
    Returns a comparison result.
    """
    # This is a simplified version - adapt as needed for your API
    start_time = datetime.datetime.combine(
        datetime.date.today(), datetime.time(7, 0))

    # Convert raw_entries to POI format if needed
    # For now, using the example POIs
    heuristic_seq, heuristic_dist = heuristic_plan(
        pois, start_coords, end_coords=end_coords)
    rl_sequence = rl_plan(pois, start_coords, start_time,
                          end_coords=end_coords)

    return {
        "heuristic": {
            "sequence": heuristic_seq,
            "distance_km": round(heuristic_dist, 2)
        },
        "rl": {
            "sequence": rl_sequence,
            "note": "RL balances time, dwell, and priorities"
        }
    }


# ----------------------------
# Main execution (for testing)
# ----------------------------
if __name__ == "__main__":
    start_time = datetime.datetime.combine(
        datetime.date.today(), datetime.time(7, 0))

    heuristic_seq, heuristic_dist = heuristic_plan(
        pois, start_coords, end_coords=end_coords)
    rl_sequence = rl_plan(pois, start_coords, start_time,
                          end_coords=end_coords)

    print("\n=== RL vs Heuristic Comparison ===")
    print("Heuristic order:", " -> ".join(heuristic_seq))
    print(f"Heuristic total distance: {heuristic_dist:.2f} km")

    print("RL order:", " -> ".join(rl_sequence))
    print("RL does not directly optimize distance but balances time, dwell, and priorities.")

    if end_coords:
        print("ℹ️ Round trip enforced.")
    else:
        print("ℹ️ One-way trip.")
