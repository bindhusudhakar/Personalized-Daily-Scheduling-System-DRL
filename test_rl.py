# test_rl.py
import datetime
from stable_baselines3 import PPO
from rl_env import ItineraryEnv

# ----------------------------
# Example POIs (same as training)
# ----------------------------
pois = [
    {"name": "Orion Mall", "lat": 13.0110, "lon": 77.5550, "dwell": 210, "priority": 5, "fixed_start": None, "is_break": False},
    {"name": "Lalbagh", "lat": 12.9507, "lon": 77.5848, "dwell": 60, "priority": 2, "fixed_start": None, "is_break": False},
    {"name": "Mantri Square", "lat": 12.9900, "lon": 77.5710, "dwell": 60, "priority": 4, "fixed_start": None, "is_break": False},
]

start_coords = (12.9716, 77.5946)  # Bengaluru Central
end_coords = start_coords          # round trip (set None for one-way)

# ----------------------------
# Build environment & load model
# ----------------------------
start_time = datetime.datetime.combine(datetime.date.today(), datetime.time(7, 0))
env = ItineraryEnv(pois, start_coords, start_time=start_time, end_coords=end_coords)

model = PPO.load("ppo_itinerary", env=env)

# ----------------------------
# Test run
# ----------------------------
obs, _ = env.reset()
done, truncated = False, False
total_reward = 0

print("\n🎯 RL Agent Itinerary Plan:\n")
while not (done or truncated):
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, done, truncated, info = env.step(action)
    total_reward += reward
    env.render()

print(f"\n✅ Test finished. Total Reward: {total_reward}")
if end_coords:
    print("ℹ️ Round trip enforced (ended at start location).")
else:
    print("ℹ️ One-way trip (last POI is the endpoint).")
