"""
Itinerary optimizer and comparator (patched, full version).

- Handles user input: POI names, priority, dwell time, travel mode, start & end time, round trip option.
- Computes:
    1) User’s fixed-order plan (always shown in full, flagged if it goes over time).
    2) Optimized plan (priority-aware, minimal travel time) — pruning applied here only.
- Integrates Google Maps traffic/time where available; uses safe fallbacks otherwise.
- Outputs structured data ready for frontend consumption.
"""

import requests
import itertools
import sqlite3
import datetime
from typing import List, Tuple, Dict, Any, Optional
from context_utils import get_route_context
from google_maps_utils import get_travel_time_distance

DB_NAME = "poi_cache.db"

# -----------------------
# Helper wrappers
# -----------------------


def safe_get_route_context(origin: Tuple[float, float],
                           destination: Tuple[float, float],
                           mode: str = "driving",
                           realtime_weather: bool = True) -> Dict[str, Any]:
    """
    Wrapper around get_route_context to ensure graceful fallback to get_travel_time_distance
    when external APIs fail or are not available.
    Returns a dict with keys: duration_sec, distance_meters, weather (may be None).
    """
    try:
        ctx = get_route_context(origin, destination,
                                mode=mode, realtime_weather=realtime_weather)
        # Normalize keys (some wrappers might return different names)
        duration = ctx.get("duration_sec") or ctx.get(
            "duration") or ctx.get("duration_seconds") or 0
        dist = ctx.get("distance_meters") or ctx.get(
            "distance") or ctx.get("distance_m") or 0
        weather = ctx.get("weather", None)
        return {"duration_sec": int(duration), "distance_meters": int(dist), "weather": weather}
    except Exception:
        # Fallback to google_maps_utils (which itself has a fallback)
        try:
            duration, dist = get_travel_time_distance(
                origin[0], origin[1], destination[0], destination[1], mode)
            return {"duration_sec": int(duration), "distance_meters": int(dist), "weather": None}
        except Exception:
            # Last resort defaults (safe, small values so planner continues)
            return {"duration_sec": 60, "distance_meters": 1000, "weather": None}


# -----------------------
# DB utilities
# -----------------------
def find_poi_in_db(poi_name: str) -> Optional[Tuple[str, float, float]]:
    """
    Look up POI by name (case-insensitive).
    Returns (name, lat, lon) if found, otherwise None.
    This function first checks poi_cache, then POIs table as a fallback.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Try poi_cache first (main cache)
    cursor.execute(
        "SELECT name, lat, lon FROM poi_cache WHERE LOWER(name) LIKE LOWER(?)",
        (f"%{poi_name}%",)
    )
    row = cursor.fetchone()

    if not row:
        # Fallback to POIs table if exists
        try:
            cursor.execute(
                "SELECT name, lat, lon FROM POIs WHERE LOWER(name) LIKE LOWER(?)",
                (f"%{poi_name}%",)
            )
            row = cursor.fetchone()
        except Exception:
            row = None

    conn.close()

    if not row:
        return None

    try:
        name, lat, lon = row[0], float(row[1]), float(row[2])
        return name, lat, lon
    except Exception:
        return None


# -----------------------
# Formatting helpers
# -----------------------
def format_datetime(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def hhmm_from_formatted(fmt_str: Optional[str]) -> str:
    if not fmt_str:
        return "-"
    if isinstance(fmt_str, str) and " " in fmt_str:
        return fmt_str.split()[1]
    return str(fmt_str)


def format_seconds(sec: Optional[int]) -> str:
    if sec is None:
        return "N/A"
    m = sec // 60
    h = m // 60
    m = m % 60
    if h > 0:
        return f"{h} hr {m} min"
    return f"{m} min"


# -----------------------
# Trip helpers
# -----------------------
def total_trip_time_for_sequence(
    seq: List[Dict[str, Any]],
    mode: str,
    round_trip: bool = False,
    start_coords: Optional[Tuple[float, float]] = None,
    start_time: Optional[datetime.datetime] = None,
    realtime_weather: bool = True
) -> Tuple[int, float, List[Dict[str, Any]]]:
    """
    Compute total_seconds, total_distance_m and legs[] for a given ordered sequence (seq).
    Legs include:
      - departure_time, departure_time_hm
      - arrival_time, arrival_time_hm
      - leave_time, leave_time_hm (time you leave the destination after dwell)
      - duration_sec (travel), distance_m, dwell_mins
    Uses safe_get_route_context for travel times (so pruning is based on real route durations).
    """
    if not seq:
        return 0, 0.0, []

    total_sec = 0
    total_dist = 0.0
    legs: List[Dict[str, Any]] = []

    # anchor current_time is when we depart the start point
    current_time = start_time or datetime.datetime.combine(
        datetime.date.today(), datetime.time(9, 0))

    # Helper to ensure dwell is sane
    def _normalize_dwell(p):
        d = p.get("dwell_mins", p.get("dwell", 15))
        try:
            d = int(d)
        except Exception:
            d = 15
        if d <= 0:
            d = 15
        return d

    # --- Start -> first POI ---
    first = seq[0]
    if start_coords:
        route_ctx = safe_get_route_context(
            start_coords,
            (first.get("lat", 12.9716), first.get("lon", 77.5946)),
            mode=mode,
            realtime_weather=realtime_weather
        )
        leg_duration = route_ctx.get("duration_sec") or 60
        leg_distance = route_ctx.get("distance_meters") or 1000
        leg_weather = route_ctx.get("weather")
    else:
        leg_duration = 0
        leg_distance = 0
        leg_weather = None

    # If first POI has target_arrival, adjust departure to meet it (small 5-minute early buffer)
    if first.get("target_arrival"):
        try:
            arrival_time = first["target_arrival"] - \
                datetime.timedelta(seconds=300)  # arrive 5 mins early
            departure_time = arrival_time - \
                datetime.timedelta(seconds=leg_duration)
            # If computed departure is before the current_time (start_time), then we'll have to leave immediately and be late possibly
            if departure_time < current_time:
                departure_time = current_time
                arrival_time = departure_time + \
                    datetime.timedelta(seconds=leg_duration)
        except Exception:
            departure_time = current_time
            arrival_time = departure_time + \
                datetime.timedelta(seconds=leg_duration)
    else:
        departure_time = current_time
        arrival_time = departure_time + \
            datetime.timedelta(seconds=leg_duration)

    dwell = _normalize_dwell(first)
    leave_time = arrival_time + datetime.timedelta(minutes=int(dwell))

    from_lat, from_lon = (
        start_coords if start_coords is not None else (12.9716, 77.5946))
    to_lat, to_lon = (first.get("lat", 12.9716), first.get("lon", 77.5946))

    legs.append({
        "from": "MG Road, Bengaluru" if (start_coords is None or start_coords == (12.9716, 77.5946)) else "Start Point",
        "to": first.get("name", "Unknown"),
        "from_lat": float(from_lat),
        "from_lon": float(from_lon),
        "to_lat": float(to_lat),
        "to_lon": float(to_lon),
        "departure_time": format_datetime(departure_time),
        "departure_time_hm": departure_time.strftime("%H:%M"),
        "arrival_time": format_datetime(arrival_time),
        "arrival_time_hm": arrival_time.strftime("%H:%M"),
        "leave_time": format_datetime(leave_time),
        "leave_time_hm": leave_time.strftime("%H:%M"),
        "duration_sec": int(leg_duration),
        "distance_m": float(leg_distance),
        "weather": leg_weather,
        "mode": mode,
        "dwell_mins": int(dwell)
    })

    total_sec += int(leg_duration) + int(dwell) * 60
    total_dist += float(leg_distance)
    current_time = leave_time

    # --- Between POIs ---
    for i in range(len(seq) - 1):
        a = seq[i]
        b = seq[i + 1]

        origin = (a.get("lat", start_coords[0] if start_coords else 12.9716),
                  a.get("lon", start_coords[1] if start_coords else 77.5946))
        destination = (b.get("lat", 12.9716), b.get("lon", 77.5946))

        route_ctx = safe_get_route_context(
            origin, destination, mode=mode, realtime_weather=realtime_weather)

        leg_duration = route_ctx.get("duration_sec") or 60
        leg_distance = route_ctx.get("distance_meters") or 1000
        leg_weather = route_ctx.get("weather")

        # If b has a target_arrival, compute desired departure to meet it (5 min early)
        if b.get("target_arrival"):
            try:
                target_time = b["target_arrival"] - \
                    datetime.timedelta(seconds=300)  # 5-min early
                # ideal departure to meet target
                ideal_departure = target_time - \
                    datetime.timedelta(seconds=leg_duration)
                if current_time < ideal_departure:
                    # we can wait and depart at ideal_departure
                    departure_time = ideal_departure
                    arrival_time = target_time
                else:
                    # we must leave now and will arrive after travel time (potentially late)
                    departure_time = current_time
                    arrival_time = departure_time + \
                        datetime.timedelta(seconds=leg_duration)
            except Exception:
                departure_time = current_time
                arrival_time = departure_time + \
                    datetime.timedelta(seconds=leg_duration)
        else:
            departure_time = current_time
            arrival_time = departure_time + \
                datetime.timedelta(seconds=leg_duration)

        dwell = _normalize_dwell(b)
        leave_time = arrival_time + datetime.timedelta(minutes=int(dwell))

        from_lat = a.get("lat", start_coords[0] if start_coords else 12.9716)
        from_lon = a.get("lon", start_coords[1] if start_coords else 77.5946)
        to_lat = b.get("lat", 12.9716)
        to_lon = b.get("lon", 77.5946)

        legs.append({
            "from": a.get("name", "Unknown"),
            "to": b.get("name", "Unknown"),
            "from_lat": float(from_lat),
            "from_lon": float(from_lon),
            "to_lat": float(to_lat),
            "to_lon": float(to_lon),
            "departure_time": format_datetime(departure_time),
            "departure_time_hm": departure_time.strftime("%H:%M"),
            "arrival_time": format_datetime(arrival_time),
            "arrival_time_hm": arrival_time.strftime("%H:%M"),
            "leave_time": format_datetime(leave_time),
            "leave_time_hm": leave_time.strftime("%H:%M"),
            "duration_sec": int(leg_duration),
            "distance_m": float(leg_distance),
            "weather": leg_weather,
            "mode": mode,
            "dwell_mins": int(dwell)
        })

        total_sec += int(leg_duration) + int(dwell) * 60
        total_dist += float(leg_distance)
        current_time = leave_time

    # --- Last POI -> Return to Start (round trip) ---
    if round_trip and start_coords and seq:
        last = seq[-1]
        route_ctx = safe_get_route_context(
            (last.get("lat", start_coords[0]),
             last.get("lon", start_coords[1])),
            start_coords,
            mode=mode,
            realtime_weather=realtime_weather
        )
        leg_duration = route_ctx.get("duration_sec") or 60
        leg_distance = route_ctx.get("distance_meters") or 1000
        leg_weather = route_ctx.get("weather")

        departure_time = current_time
        arrival_time = departure_time + \
            datetime.timedelta(seconds=leg_duration)

        from_lat = last.get("lat", start_coords[0])
        from_lon = last.get("lon", start_coords[1])
        to_lat, to_lon = start_coords

        legs.append({
            "from": last.get("name", "Unknown"),
            "to": "Return to Start",
            "from_lat": float(from_lat),
            "from_lon": float(from_lon),
            "to_lat": float(to_lat),
            "to_lon": float(to_lon),
            "departure_time": format_datetime(departure_time),
            "departure_time_hm": departure_time.strftime("%H:%M"),
            "arrival_time": format_datetime(arrival_time),
            "arrival_time_hm": arrival_time.strftime("%H:%M"),
            "leave_time": None,
            "leave_time_hm": None,
            "duration_sec": int(leg_duration),
            "distance_m": float(leg_distance),
            "weather": leg_weather,
            "mode": mode,
            "dwell_mins": 0
        })

        total_sec += int(leg_duration)
        total_dist += float(leg_distance)

    return int(total_sec), float(total_dist), legs


# -----------------------
# Optimization
# -----------------------
def build_optimized_sequence(entries: List[Dict[str, Any]], mode: str) -> List[Dict[str, Any]]:
    """
    Build an optimized ordering for entries.
    - If there are fixed items (priority == 1), they remain as anchors.
    - For small flexible lists, try permutations (<=6).
    - Otherwise use greedy insertion.
    """
    if not entries:
        return []

    # Identify fixed anchors (priority == 1)
    anchors = [p for p in entries if p.get("priority") == 1]
    flexible = [p for p in entries if p.get("priority") != 1]

    # If no fixed anchors, we can permute flexible
    if not anchors:
        if len(flexible) <= 6:
            best_seq, best_cost = None, float("inf")
            for perm in itertools.permutations(flexible):
                seq = list(perm)
                try:
                    sec, _, _ = total_trip_time_for_sequence(seq, mode)
                except Exception:
                    sec = float("inf")
                if sec < best_cost:
                    best_cost, best_seq = sec, seq
            return best_seq or flexible
        # greedy insertion for larger lists
        if flexible:
            seq = [flexible[0]]
            for p in flexible[1:]:
                best_seq, best_cost = None, float("inf")
                for i in range(len(seq) + 1):
                    trial = seq[:i] + [p] + seq[i:]
                    try:
                        sec, _, _ = total_trip_time_for_sequence(trial, mode)
                    except Exception:
                        sec = float("inf")
                    if sec < best_cost:
                        best_cost, best_seq = sec, trial
                seq = best_seq
            return seq
        return entries

    # If there are anchors, insert flexible items into best positions relative to anchors
    seq = anchors[:]
    for p in flexible:
        best_seq, best_cost = None, float("inf")
        for i in range(len(seq) + 1):
            trial = seq[:i] + [p] + seq[i:]
            try:
                sec, _, _ = total_trip_time_for_sequence(trial, mode)
            except Exception:
                sec = float("inf")
            if sec < best_cost:
                best_cost, best_seq = sec, trial
        seq = best_seq
    # If some flexible items remain (unlikely), append them
    return seq


# -----------------------
# Pruning (for optimized plan only)
# -----------------------
def prune_plan(
    seq: List[Dict[str, Any]],
    end_time: datetime.datetime,
    start_time: datetime.datetime,
    mode: str = "driving",
    round_trip: bool = False,
    start_coords: Optional[Tuple[float, float]] = None,
    realtime_weather: bool = True
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Prune sequence (only used for optimized plan).
    Strategy:
      - While total_time > allowed:
        * Consider only removable POIs (no target_arrival)
        * Among removable POIs, find those with the worst priority first (max numeric priority)
        * Within that priority bucket, remove the POI whose removal yields the largest reduction in total time.
        * Tie-break by distance saved, then dwell time, then deterministic fallback (index).
    """
    kept = seq[:]  # shallow copy
    dropped: List[Dict[str, Any]] = []

    total_sec, total_dist, _ = total_trip_time_for_sequence(
        kept, mode, round_trip, start_coords, start_time, realtime_weather)

    finish_time = start_time + datetime.timedelta(seconds=total_sec)
    if finish_time <= end_time:
        # Already feasible → return unchanged, no dropped POIs
        return kept, []

    while True:
        finish_time = start_time + datetime.timedelta(seconds=total_sec)
        if finish_time <= end_time:
            break  # fits within allowed window

        # First try to remove POIs without target_arrival (more flexible)
        removable = [p for p in kept if not p.get("target_arrival")]

        # If no flexible POIs left, allow removing POIs with target_arrival as last resort
        # But exclude start location (dwell_mins == 0)
        if not removable:
            removable = [p for p in kept if p.get("dwell_mins", 0) > 0]

        if not removable:
            # Can't remove anything (only start location left), give up
            break

        # find highest numeric priority among removable POIs (higher numeric value = lower importance)
        highest_priority_val = max(p.get("priority", 9999) for p in removable)
        # limit candidates to this priority bucket
        bucket = [p for p in removable if p.get(
            "priority", 9999) == highest_priority_val]

        # evaluate marginal savings for each candidate in bucket
        best_candidate = None
        best_marginal = -1
        best_dist_saved = -1
        best_dwell = -1
        fallback_index = None

        for candidate in bucket:
            trial_seq = [p for p in kept if p is not candidate]
            sec_without, dist_without, _ = total_trip_time_for_sequence(
                trial_seq, mode, round_trip, start_coords, start_time, realtime_weather)
            marginal = total_sec - sec_without
            dist_saved = total_dist - dist_without
            dwell_val = candidate.get("dwell_mins", candidate.get("dwell", 0))

            pick = False
            if marginal > best_marginal:
                pick = True
            elif marginal == best_marginal:
                if dist_saved > best_dist_saved:
                    pick = True
                elif dist_saved == best_dist_saved:
                    if dwell_val > best_dwell:
                        pick = True
                    elif dwell_val == best_dwell:
                        try:
                            kept_index_cand = kept.index(candidate)
                            if fallback_index is None or kept_index_cand > fallback_index:
                                pick = True
                        except ValueError:
                            pick = True

            if pick:
                best_candidate = candidate
                best_marginal = marginal
                best_dist_saved = dist_saved
                best_dwell = dwell_val
                try:
                    fallback_index = kept.index(candidate)
                except ValueError:
                    fallback_index = None

        if best_candidate is None:
            break

        kept.remove(best_candidate)
        dropped.append(best_candidate)

        total_sec, total_dist, _ = total_trip_time_for_sequence(
            kept, mode, round_trip, start_coords, start_time, realtime_weather)

    return kept, dropped


# -----------------------
# Get current location (fallback)
# -----------------------
def get_current_location() -> Tuple[float, float]:
    try:
        resp = requests.get("https://ipinfo.io/json", timeout=3)
        data = resp.json()
        loc = data.get("loc")
        if loc:
            lat, lon = map(float, loc.split(","))
            return lat, lon
    except Exception:
        pass
    return 12.9716, 77.5946  # MG Road fallback


# -----------------------
# Prepare entries
# -----------------------
def prepare_entries_from_user(
    raw: List[Tuple[str, int, int, Optional[datetime.datetime]]]
) -> List[Dict[str, Any]]:
    """
    Convert user tuples (name, priority, dwell_mins, optional target_arrival)
    into structured entries for itinerary computation.
    """
    entries: List[Dict[str, Any]] = []
    if not raw:
        entries.append({
            "name": "Start Point",
            "priority": 1,
            "dwell_mins": 0,
            "target_arrival": None,
            "lat": 12.9716,
            "lon": 77.5946
        })
        return entries

    for item in raw:
        if len(item) == 3:
            name, pri, dwell = item
            target_arrival = None
        elif len(item) == 4:
            name, pri, dwell, target_arrival = item
        else:
            raise ValueError(f"Invalid entry: {item}")

        found = find_poi_in_db(name)
        if not found:
            # Not found in DB: fallback to using raw name and default coords
            print(
                f"⚠️ POI '{name}' not found in DB. Using fallback coordinates (MG Road, Bengaluru).")
            matched_name, lat, lon = name, 12.9756, 77.6047
        else:
            matched_name, lat, lon = found

        if dwell is None or (isinstance(dwell, (int, float)) and dwell < 0):
            print(f"⚠️ Invalid dwell for POI '{name}'. Using default 15 mins.")
            dwell = 15
        if pri is None or (isinstance(pri, (int, float)) and pri < 1):
            print(f"⚠️ Invalid priority for POI '{name}'. Defaulting to 1.")
            pri = 1

        entries.append({
            "name": matched_name,
            "priority": int(pri),
            "dwell_mins": int(dwell),
            "target_arrival": target_arrival,
            "lat": lat,
            "lon": lon
        })
    return entries


# -----------------------
def _add_return_leg(plan, current_loc, current_time, debug=False, tag="[PLAN]"):
    """Helper to add return-to-start leg. (Kept for backward compatibility)"""
    travel_sec = 1200  # stub travel time
    travel_dist = 5000
    arrival_time = current_time + datetime.timedelta(seconds=travel_sec)

    if debug:
        print(f"{tag} Returning to Start → arrive {arrival_time.time()}")

    leg = {
        "from": current_loc,
        "to": "Start",
        "duration_sec": travel_sec,
        "distance_m": travel_dist,
        "arrival_time": arrival_time,
        "arrival_time_hm": arrival_time.strftime("%H:%M"),
        "departure_time_hm": current_time.strftime("%H:%M"),
        "dwell_mins": 0,
    }
    plan["legs"].append(leg)
    plan["total_seconds"] += travel_sec
    plan["total_distance_m"] += travel_dist

    return arrival_time, "Start"


# -----------------------
# Generate itinerary (public entry point)
# -----------------------
def generate_itinerary(
    raw_entries: List[Tuple[str, int, int, Optional[datetime.datetime]]],
    mode: str = "driving",
    start_coords: Optional[Tuple[float, float]] = None,
    start_time: Optional[datetime.datetime] = None,
    end_time: Optional[datetime.datetime] = None,
    round_trip: bool = False,
    debug: bool = False
) -> Dict[str, Any]:
    entries = prepare_entries_from_user(raw_entries)

    if start_coords is None:
        start_coords = get_current_location()

    first_poi = entries[0] if entries else None
    if first_poi and first_poi.get("target_arrival"):
        try:
            route_ctx = safe_get_route_context(
                start_coords,
                (first_poi.get("lat", 12.9716), first_poi.get("lon", 77.5946)),
                mode=mode,
                realtime_weather=True
            )
            travel_sec = route_ctx.get("duration_sec") or 60
            start_time = first_poi["target_arrival"] - datetime.timedelta(
                seconds=travel_sec) - datetime.timedelta(minutes=5)
        except Exception:
            start_time = start_time or datetime.datetime.combine(
                datetime.date.today(), datetime.time(9, 0))
    else:
        start_time = start_time or datetime.datetime.combine(
            datetime.date.today(), datetime.time(9, 0))

    end_time = end_time or datetime.datetime.combine(
        datetime.date.today(), datetime.time(22, 0))

    # --- USER PLAN (unchanged, no pruning) ---
    user_sec, user_dist, user_legs = total_trip_time_for_sequence(
        entries, mode, round_trip, start_coords, start_time, realtime_weather=True
    )

    over_time: List[str] = []
    for leg in user_legs:
        at_str = leg.get("arrival_time")
        try:
            at_dt = datetime.datetime.strptime(at_str, "%Y-%m-%d %H:%M")
        except Exception:
            at_dt = None
        if at_dt and at_dt > end_time:
            over_time.append(leg.get("to"))

    user_plan = {
        "sequence": entries,
        "dropped": [],  # Never prune user plan
        "total_seconds": user_sec,
        "total_distance_m": user_dist,
        "legs": user_legs,
        "over_time": over_time
    }

    # --- OPTIMIZED PLANS (pruning applied) ---
    optimized_sequences: List[Dict[str, Any]] = []

    # The first POI (start location) should always be at position 0
    # Flexible items are those without strict target arrivals (we will permute these)
    # IMPORTANT: Exclude the first POI (start location with dwell=0) from permutations
    start_poi = entries[0] if entries else None

    # Items with target_arrival are fixed in position, others are flexible
    fixed_pois = [p for p in entries[1:] if p.get("target_arrival")]
    flexible = [p for p in entries[1:] if not p.get("target_arrival")]

    # Try to generate at most 2 viable optimized options
    tried_seqs = []

    # If there are flexible items, generate permutations
    if len(flexible) <= 6:
        all_permutations = list(itertools.permutations(flexible))
    else:
        all_permutations = []

    # If no flexible items, create at least one candidate with the fixed sequence
    if not all_permutations:
        # Empty tuple for when there are no flexible items
        all_permutations = [tuple()]

    # Sort permutations by expected travel time heuristic (safely)
    def perm_cost(seq):
        total = 0
        try:
            for i in range(len(seq) - 1):
                a = seq[i]
                b = seq[i + 1]
                try:
                    dur, _ = get_travel_time_distance(
                        a["lat"], a["lon"], b["lat"], b["lon"], mode)
                    total += dur or 0
                except Exception:
                    total += 10**7  # bad permutations get large cost
        except Exception:
            total = 10**9
        return total

    sorted_perms = sorted(all_permutations, key=lambda s: perm_cost(s))

    for seq in sorted_perms[:3]:
        # Build candidate sequence: start_poi + fixed_pois + permuted flexible items
        candidate_seq = []
        if start_poi:
            candidate_seq.append(start_poi)
        candidate_seq.extend(fixed_pois)
        candidate_seq.extend(list(seq))

        # Avoid duplicate POIs
        if candidate_seq in tried_seqs:
            continue
        tried_seqs.append(candidate_seq)

        kept, dropped = prune_plan(
            candidate_seq, end_time, start_time, mode, round_trip, start_coords)

        if start_poi and start_poi not in kept:
            continue  # Start POI must remain

        total_sec, total_dist, legs = total_trip_time_for_sequence(
            kept, mode, round_trip, start_coords, start_time, realtime_weather=True
        )

        if not dropped and kept == candidate_seq and optimized_sequences:
            # Skip adding duplicate “alternative” if same as existing
            continue

        if len(kept) >= 1 and total_sec > 0:
            optimized_sequences.append({
                "sequence": kept,
                "dropped": dropped,
                "total_seconds": total_sec,
                "total_distance_m": total_dist,
                "legs": legs
            })

        if len(optimized_sequences) >= 2:
            break

    # Ensure at least 1 optimized plan exists (fallback to user plan if nothing else viable)
    if not optimized_sequences:
        total_sec, total_dist, legs = total_trip_time_for_sequence(
            entries, mode, round_trip, start_coords, start_time, realtime_weather=True
        )
        optimized_sequences.append({
            "sequence": entries,
            "dropped": [],
            "total_seconds": total_sec,
            "total_distance_m": total_dist,
            "legs": legs
        })

    # If primary and alternative are identical (same POI sequence), discard the alternative
    if len(optimized_sequences) > 1:
        try:
            first_seq_ids = [poi["name"]
                             for poi in optimized_sequences[0]["sequence"]]
            second_seq_ids = [poi["name"]
                              for poi in optimized_sequences[1]["sequence"]]
            if first_seq_ids == second_seq_ids:
                optimized_sequences.pop(1)
        except Exception:
            pass

    return {
        "start_time": format_datetime(start_time),
        "end_time": format_datetime(end_time),
        "mode": mode,
        "round_trip": round_trip,
        "start_coords": start_coords,
        "user_plan": user_plan,
        "optimized_plan": optimized_sequences[0],
        "alternative_optimized_plan": optimized_sequences[1] if len(optimized_sequences) > 1 else None
    }
