# rl_env.py
import copy
import math
import random
import datetime
from typing import List, Dict, Tuple, Optional

import numpy as np
import gymnasium as gym
from gymnasium import spaces

# Import real-time travel + weather context
try:
    from context_utils import get_route_context  # returns dict {travel_sec, dist_m, weather, adjusted_sec}
except Exception as e:
    get_route_context = None


# ----------------------------
# Synthetic fallback router (offline / training)
# ----------------------------
def _synthetic_travel_time_distance(lat1, lon1, lat2, lon2, mode="driving"):
    """Fallback travel time using haversine + rough speed + noise."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2.0) ** 2
    d = 2 * R * math.asin(math.sqrt(a))

    speeds_kmh = {"walking": 4.5, "cycling": 15.0, "driving": 28.0, "transit": 22.0}
    v_m_s = speeds_kmh.get(mode, 28.0) * 1000.0 / 3600.0
    t_sec = d / max(v_m_s, 1e-6)
    t_sec *= random.uniform(0.9, 1.15)
    return int(t_sec), int(d)


def safe_travel_time_distance(lat1, lon1, lat2, lon2, mode="driving"):
    """Unified travel time (real-time if available, else fallback)."""
    if get_route_context:
        try:
            ctx = get_route_context(lat1, lon1, lat2, lon2, mode)
            return ctx["adjusted_sec"], ctx["dist_m"]
        except Exception:
            pass
    return _synthetic_travel_time_distance(lat1, lon1, lat2, lon2, mode)


# ----------------------------
# Itinerary Environment
# ----------------------------
class ItineraryEnv(gym.Env):
    """
    Gymnasium environment for time-aware itinerary planning with weather & end-time constraints.

    Obs: [time_norm, lat_norm, lon_norm, visited_mask...]
    Action: choose POI index
    Reward: balances priority bonuses, travel/weather penalties, dwell penalties, lateness penalties.
    """

    metadata = {"render_modes": ["human"], "render_fps": 4}

    def __init__(
        self,
        pois: List[Dict],
        start_coords: Tuple[float, float],
        start_time: Optional[datetime.datetime] = None,
        end_coords: Optional[Tuple[float, float]] = None,
        day_end_hour: Optional[int] = 22,   # None → no limit
    ):
        super().__init__()

        self.pois: List[Dict] = copy.deepcopy(pois)
        self.start_coords = start_coords
        self.end_coords = end_coords or start_coords

        self.start_time = start_time or datetime.datetime.combine(
            datetime.date.today(), datetime.time(7, 0)
        )

        self.current_time: datetime.datetime = None
        self.current_coords: Tuple[float, float] = None

        self.n_pois = max(1, len(self.pois))
        self.action_space = spaces.Discrete(self.n_pois)

        obs_dim = 3 + self.n_pois
        self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=(obs_dim,), dtype=np.float32)

        self.day_end_hour = day_end_hour
        self.reset()

    # ----------------------------
    # Obs encoding
    # ----------------------------
    def _get_obs(self):
        visited_mask = np.array(
            [1.0 if p.get("visited", False) else 0.0 for p in self.pois], dtype=np.float32
        )

        lat, lon = self.current_coords
        lat_norm = (lat - 12.8) / (13.2 - 12.8) * 2.0 - 1.0
        lon_norm = (lon - 77.4) / (77.8 - 77.4) * 2.0 - 1.0

        minutes = float(self.current_time.hour * 60 + self.current_time.minute)
        time_norm = minutes / 1440.0 * 2.0 - 1.0

        return np.concatenate(([time_norm, lat_norm, lon_norm], visited_mask)).astype(np.float32)

    # ----------------------------
    # Action masks
    # ----------------------------
    def action_masks(self):
        mask = np.ones(self.n_pois, dtype=bool)
        for i, p in enumerate(self.pois):
            if p.get("visited", False) or p.get("is_break", False):
                mask[i] = False
        return mask

    # ----------------------------
    # Step
    # ----------------------------
    def step(self, action: int):
        terminated, truncated = False, False
        info = {}

        if (not isinstance(action, (int, np.integer))) or action < 0 or action >= self.n_pois:
            return self._get_obs(), -10.0, terminated, truncated, info

        poi = self.pois[action]

        if poi.get("visited", False) or poi.get("is_break", False):
            return self._get_obs(), -5.0, terminated, truncated, info

        # --- Travel with weather ---
        travel_sec, dist_m = safe_travel_time_distance(
            self.current_coords[0], self.current_coords[1],
            poi["lat"], poi["lon"], poi.get("mode", "driving")
        )
        travel_min = max(1, int(travel_sec // 60))
        arrival_time = self.current_time + datetime.timedelta(minutes=travel_min)

        # --- Time window (fixed start) ---
        lateness_pen, earliness_pen, wait_pen, on_time_bonus = 0.0, 0.0, 0.0, 0.0
        fixed_start = poi.get("fixed_start")
        if fixed_start:
            if isinstance(fixed_start, str):
                hh, mm = map(int, fixed_start.split(":"))
                fixed_start_time = datetime.time(hh, mm)
            else:
                fixed_start_time = fixed_start

            target_time = datetime.datetime.combine(self.current_time.date(), fixed_start_time)
            if arrival_time < target_time:
                wait_mins = (target_time - arrival_time).seconds // 60
                arrival_time = target_time
                wait_pen = 0.05 * wait_mins
            else:
                late_mins = (arrival_time - target_time).seconds // 60
                lateness_pen = 0.2 * late_mins
                if late_mins <= 10:
                    on_time_bonus = 2.0

        # --- Stay ---
        dwell = int(max(1, poi.get("dwell", 15)))
        leave_time = arrival_time + datetime.timedelta(minutes=dwell)

        # --- Rewards ---
        priority_bonus = float(poi.get("priority", 0)) * 5.0
        travel_pen = 0.15 * travel_min
        dwell_pen = 0.03 * dwell

        overrun_pen = 0.0
        if self.day_end_hour:
            day_end = datetime.datetime.combine(
                self.current_time.date(), datetime.time(self.day_end_hour, 0)
            )
            if leave_time > day_end:
                overrun_min = (leave_time - day_end).seconds // 60
                overrun_pen = 0.2 * overrun_min

        reward = (
            priority_bonus + on_time_bonus
            - (travel_pen + dwell_pen + wait_pen + lateness_pen + earliness_pen + overrun_pen)
        )

        # --- Update state ---
        poi["visited"] = True
        self.current_coords = (poi["lat"], poi["lon"])
        self.current_time = leave_time

        # Inside ItineraryEnv.step()

        # --- Termination condition ---
        all_done = all(p.get("visited", False) or p.get("is_break", False) for p in self.pois)

        if all_done:
            if self.end_coords:  # user specified an end location
                # Travel to end location
                travel_sec, dist_m = safe_travel_time_distance(
                    self.current_coords[0], self.current_coords[1],
                    self.end_coords[0], self.end_coords[1],
                    "driving"
                )
                travel_min = max(1, int(travel_sec // 60))
                self.current_time += datetime.timedelta(minutes=travel_min)

                reward -= 0.15 * travel_min  # penalize travel effort
                reward += 2.0  # small bonus for completing trip properly

        terminated = True
        minutes_used = int((self.current_time - self.start_time).total_seconds() // 60)
        reward += max(0.0, 1440 - minutes_used) * 0.01


        if self.current_time.hour >= 23 and self.current_time.minute >= 59:
            truncated = True
            reward -= 10.0

        if terminated or truncated:
            unvisited_high = sum(
                1
                for p in self.pois
                if not p.get("visited", False) and not p.get("is_break", False) and p.get("priority", 0) >= 4
            )
            reward -= 5.0 * unvisited_high

        return self._get_obs(), float(reward), terminated, truncated, info

    # ----------------------------
    # Reset
    # ----------------------------
    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None):
        super().reset(seed=seed)
        for p in self.pois:
            p["visited"] = False
            p.setdefault("lat", self.start_coords[0])
            p.setdefault("lon", self.start_coords[1])
            p.setdefault("dwell", 15)
            p.setdefault("priority", 0)
            p.setdefault("fixed_start", None)
            p.setdefault("is_break", False)
        self.current_coords = self.start_coords
        self.current_time = self.start_time
        return self._get_obs(), {}

    def render(self, mode="human"):
        visited = [p.get("name", f"POI#{i}") for i, p in enumerate(self.pois) if p.get("visited", False)]
        print(f"[ItineraryEnv] {self.current_time.strftime('%H:%M')} @ {self.current_coords} | Visited: {visited}")
