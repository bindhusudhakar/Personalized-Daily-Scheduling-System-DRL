# train_rl.py
import gymnasium as gym
from stable_baselines3 import PPO
from rl_env import ItineraryEnv
from stable_baselines3.common.callbacks import BaseCallback
from tqdm import tqdm
import datetime

# ----------------------------
# Progress Bar Callback
# ----------------------------
class ProgressBarCallback(BaseCallback):
    def __init__(self, total_timesteps, verbose=0):
        super().__init__(verbose)
        self.progress_bar = tqdm(total=total_timesteps, desc="Training Progress")

    def _on_step(self) -> bool:
        self.progress_bar.update(1)
        return True

    def _on_training_end(self) -> None:
        self.progress_bar.close()

# ----------------------------
# Example POIs
# ----------------------------
pois = [
    {"name": "Orion Mall", "lat": 13.0110, "lon": 77.5550, "dwell": 210, "priority": 5, "fixed_start": None, "is_break": False},
    {"name": "Lalbagh", "lat": 12.9507, "lon": 77.5848, "dwell": 60, "priority": 2, "fixed_start": None, "is_break": False},
    {"name": "Mantri Square", "lat": 12.9900, "lon": 77.5710, "dwell": 60, "priority": 4, "fixed_start": None, "is_break": False},
]

start_coords = (12.9716, 77.5946)  # Bengaluru Central
end_coords = start_coords          # round trip (optional, set None for one-way)

# ----------------------------
# Build environment
# ----------------------------
start_time = datetime.datetime.combine(datetime.date.today(), datetime.time(7, 0))
env = ItineraryEnv(pois, start_coords, start_time=start_time, end_coords=end_coords)

# ----------------------------
# Train PPO agent
# ----------------------------
model = PPO("MlpPolicy", env, verbose=0, device="cpu")
callback = ProgressBarCallback(total_timesteps=5000)

print("🚀 Training started...")
model.learn(total_timesteps=5000, callback=callback)

# ----------------------------
# Save trained model
# ----------------------------
model.save("ppo_itinerary")

print("✅ Training finished. Model saved as 'ppo_itinerary.zip'")
