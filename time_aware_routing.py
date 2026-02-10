# time_aware_routing.py
import sqlite3
import datetime
import math
import sys
from typing import List, Dict, Tuple, Optional
from optimizer import optimize_poi_sequence   # 🔹 import optimizer

DB_NAME = "poi_cache.db"

# Try importing Google helper functions (preferred).
try:
    from google_maps_utils import get_travel_time_distance, geocode_location
except Exception:
    # Fallback implementations (approximate) if google_maps_utils isn't available.
    print("⚠️ Warning: google_maps_utils not available — using local fallbacks for geocode and routing.")

    def geocode_location(address: str) -> Tuple[Optional[float], Optional[float]]:
        """Fallback geocode: 'Current Location' -> default Bengaluru coords; otherwise None."""
        if not address:
            return None, None
        if address.strip().lower() == "current location":
            return 12.975, 77.605  # central Bengaluru
        return None, None

    def haversine_meters(lat1, lon1, lat2, lon2):
        R = 6371000
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def get_travel_time_distance(orig_lat, orig_lon, dest_lat, dest_lon, mode="driving"):
        """Fallback: haversine + guessed speed. Returns (seconds, meters)."""
        dist_m = haversine_meters(orig_lat, orig_lon, dest_lat, dest_lon)
        speed_mps = {"walking": 1.4, "bicycling": 4.5, "two_wheeler": 10, "transit": 8, "driving": 12}.get(mode, 12)
        duration_sec = max(30, int(dist_m / speed_mps))
        return duration_sec, int(dist_m)


# -----------------------
# Utility / parsing
# -----------------------
def parse_user_line(s: str) -> Dict:
    """
    Flexible parser. Accepts formats:
      - Name, priority, dwell, [fixed_HH:MM], [mode]
      - or Name, priority, fixed_HH:MM, dwell, [mode]
    Special:
      - Use 'BREAK' as name to insert downtime (dwell minutes, no travel).
    Returns dict: {name, priority, dwell, fixed_start, leg_mode, is_break}
    """
    parts = [p.strip() for p in s.split(",") if p is not None]
    if len(parts) < 3:
        raise ValueError("Use: Name,priority,dwell[,fixed_HH:MM][,mode] OR Name,priority,fixed_HH:MM,dwell[,mode]")

    name = parts[0]
    try:
        priority = int(parts[1]) if parts[1] != "" else 0
    except ValueError:
        raise ValueError("Priority must be integer (1-5).")

    dwell = None
    fixed_start = None
    leg_mode = None

    for p in parts[2:]:
        if p == "":
            continue
        if ":" in p:  # time token
            try:
                hh, mm = map(int, p.split(":"))
                fixed_start = datetime.time(hh, mm)
                continue
            except Exception:
                pass
        if p.isdigit():  # dwell
            dwell = int(p)
            continue
        leg_mode = p.lower()  # mode

    if dwell is None:
        raise ValueError("Missing dwell time (minutes).")

    is_break = (name.strip().lower() == "break")

    return {"name": name, "priority": priority, "dwell": dwell,
            "fixed_start": fixed_start, "leg_mode": leg_mode, "is_break": is_break}


# -----------------------
# DB helpers
# -----------------------
def db_find_pois_by_name(query_name: str) -> List[Tuple]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    q = f"%{query_name}%"
    cursor.execute("""
        SELECT id, name, friendly_category, lat, lon, avg_dwell_time, rating
        FROM poi_cache
        WHERE name LIKE ?
        ORDER BY name COLLATE NOCASE
        LIMIT 20
    """, (q,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def choose_poi_from_db(name: str):
    matches = db_find_pois_by_name(name)
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]

    print(f"\nMultiple POI matches found for '{name}':")
    for idx, r in enumerate(matches, start=1):
        rid, rname, friendly, lat, lon, dwell, rating = r
        hint = f"{friendly}" if friendly else ""
        print(f" {idx}. {rname} {(' - ' + hint) if hint else ''} (lat:{lat:.5f}, lon:{lon:.5f}, dwell:{dwell}m, rating:{rating})")

    while True:
        sel = input(f"Pick a POI number 1-{len(matches)} (or 0 to skip): ").strip()
        if sel.isdigit():
            sel_i = int(sel)
            if sel_i == 0:
                return None
            if 1 <= sel_i <= len(matches):
                return matches[sel_i - 1]
        print("Invalid selection, try again.")


# -----------------------
# Time helpers
# -----------------------
def fmt_time(dt: datetime.datetime) -> str:
    return dt.strftime("%H:%M")


# -----------------------
# Main planner
# -----------------------
def build_time_aware_plan(user_entries: List[Dict],
                          start_dt: datetime.datetime,
                          start_loc: Optional[str] = None,
                          end_loc: Optional[str] = None,
                          default_mode: str = "driving"):

    # Resolve start coordinates
    current_lat = current_lon = None
    if start_loc:
        latlon = geocode_location(start_loc)
        if latlon and latlon[0] is not None:
            current_lat, current_lon = latlon
        else:
            print("⚠️ Could not geocode start location; starting without coords.")

    # End coords (round trip if blank)
    end_coords = None
    if end_loc:
        elatlon = geocode_location(end_loc)
        if elatlon and elatlon[0] is not None:
            end_coords = elatlon
    elif start_loc:
        end_coords = (current_lat, current_lon)

    plan_details = []
    total_time_mins = 0
    total_dist_km = 0.0
    curr_dt = start_dt

    if start_loc:
        plan_details.append(f"Start location: {start_loc} (start {fmt_time(curr_dt)})")

    last_lat, last_lon = current_lat, current_lon
    poi_counter = 1

    for entry in user_entries:
        pname = entry.get("resolved_name", entry["name"])
        pri, dwell = entry["priority"], entry["dwell"]
        plat, plon = entry.get("lat"), entry.get("lon")
        fixed_start, leg_mode, is_break = entry["fixed_start"], entry["leg_mode"] or default_mode, entry["is_break"]

        # --- Break ---
        if is_break:
            if fixed_start:
                fixed_dt = datetime.datetime.combine(curr_dt.date(), fixed_start)
                if fixed_dt > curr_dt:
                    wait_mins = (fixed_dt - curr_dt).seconds // 60
                    plan_details.append(f" • Wait until {fmt_time(fixed_dt)} (break start) — wait {wait_mins} mins")
                    total_time_mins += wait_mins
                    curr_dt = fixed_dt
            end_dt = curr_dt + datetime.timedelta(minutes=dwell)
            plan_details.append(f"{poi_counter}. BREAK | {dwell} mins (from {fmt_time(curr_dt)} to {fmt_time(end_dt)})")
            poi_counter += 1
            total_time_mins += dwell
            curr_dt = end_dt
            continue

        # --- Travel leg ---
        travel_min, dist_km = 0, 0.0
        if last_lat and last_lon and plat and plon:
            travel_sec, dist_m = get_travel_time_distance(last_lat, last_lon, plat, plon, leg_mode)
            if travel_sec and dist_m:
                travel_min = travel_sec // 60
                dist_km = dist_m / 1000.0
        else:
            plan_details.append(f" → Reach first POI: {pname} (start at {fmt_time(curr_dt)})")

        # --- Fixed start correction ---
        if fixed_start:
            fixed_dt = datetime.datetime.combine(curr_dt.date(), fixed_start)
            latest_departure = fixed_dt - datetime.timedelta(minutes=travel_min)
            if curr_dt < latest_departure:
                wait_mins = (latest_departure - curr_dt).seconds // 60
                plan_details.append(f" • Wait until {fmt_time(latest_departure)} to leave for {pname} (wait {wait_mins} mins)")
                total_time_mins += wait_mins
                curr_dt = latest_departure
            if travel_min > 0:
                plan_details.append(f" -> Travel to {pname} [{leg_mode}]: {travel_min} mins, {dist_km:.2f} km (arrive {fmt_time(fixed_dt)})")
                total_time_mins += travel_min
                total_dist_km += dist_km
                curr_dt = fixed_dt
        else:
            if travel_min > 0:
                plan_details.append(f" -> Travel to {pname} [{leg_mode}]: {travel_min} mins, {dist_km:.2f} km (arrive {fmt_time(curr_dt + datetime.timedelta(minutes=travel_min))})")
                total_time_mins += travel_min
                total_dist_km += dist_km
                curr_dt += datetime.timedelta(minutes=travel_min)

        # --- Stay ---
        leave_dt = curr_dt + datetime.timedelta(minutes=dwell)
        plan_details.append(f"{poi_counter}. {pname} | Priority {pri} | Stay {dwell} mins (leave {fmt_time(leave_dt)})")
        poi_counter += 1
        total_time_mins += dwell
        curr_dt = leave_dt

        last_lat, last_lon = plat, plon

    # --- Return leg ---
    if end_coords and last_lat and last_lon:
        elat, elon = end_coords
        travel_sec, dist_m = get_travel_time_distance(last_lat, last_lon, elat, elon, default_mode)
        if travel_sec and dist_m:
            travel_min = travel_sec // 60
            dist_km = dist_m / 1000.0
            plan_details.append(f" -> Travel to end location: {travel_min} mins, {dist_km:.2f} km (arrive {fmt_time(curr_dt + datetime.timedelta(minutes=travel_min))})")
            total_time_mins += travel_min
            total_dist_km += dist_km
            curr_dt += datetime.timedelta(minutes=travel_min)
            plan_details.append(f"End at provided end location (arrive {fmt_time(curr_dt)})")

    return total_time_mins, total_dist_km, plan_details


# -----------------------
# Runner
# -----------------------
def run_time_aware_optimizer(show_mode: str = None):
    print("=== Time-Aware Itinerary Optimizer ===")

    start_loc = input("Enter your starting location (text) or leave blank for 'Current Location': ").strip() or "Current Location"
    start_input = input("Enter global start time (HH:MM, 24hr) OR leave blank to use 07:00: ").strip() or "07:00"
    try:
        hh, mm = map(int, start_input.split(":"))
    except Exception:
        print("Invalid format. Using 07:00.")
        hh, mm = 7, 0
    start_time = datetime.datetime.combine(datetime.date.today(), datetime.time(hh, mm))

    end_loc = input("Enter end location (leave blank to return to start location): ").strip() or None

    # --- Geocode start/end coordinates ---
    start_coords = None
    end_coords = None
    if start_loc:
        s_latlon = geocode_location(start_loc)
        if s_latlon and s_latlon[0] is not None:
            start_coords = s_latlon
    if end_loc:
        e_latlon = geocode_location(end_loc)
        if e_latlon and e_latlon[0] is not None:
            end_coords = e_latlon
    elif start_coords:
        end_coords = start_coords  # round trip

    n = int(input("How many POIs to schedule? ").strip() or "0")
    entries = []
    for i in range(n):
        s = input(f"POI {i+1} (Name, priority, dwell, [fixed_HH:MM],[mode]) — use 'BREAK' for downtime: ").strip()
        try:
            parsed = parse_user_line(s)
            if not parsed["is_break"]:
                chosen = choose_poi_from_db(parsed["name"])
                if chosen:
                    pid, pname, pfriendly, plat, plon, p_dwell_default, p_rating = chosen
                    parsed.update({
                        "lat": plat,
                        "lon": plon,
                        "resolved_name": pname,
                        "rating": p_rating
                    })
                else:
                    parsed["lat"] = parsed["lon"] = None
                    parsed["resolved_name"] = parsed["name"]
            entries.append(parsed)
        except Exception as ex:
            print(f"❌ {ex}")
            return

    default_mode = input("Default travel mode (driving/walking/bicycling/transit/two_wheeler) [driving]: ").strip() or "driving"

    # -----------------------
    # Decide display mode
    # -----------------------
    if not show_mode:
        show_mode = input("Show (1) Both Plans or (2) Optimized Only? [1]: ").strip() or "1"

    # -----------------------
    # Build user-order plan
    # -----------------------
    if show_mode == "1":
        print("\n📅 Final Time-Aware Plan (User Order):")
        total_time, total_dist, details = build_time_aware_plan(
            entries, start_time, start_loc, end_loc, default_mode
        )
        for d in details:
            print(" ", d)
        print(f"\nTotal Duration: {total_time} mins | Total Distance: {total_dist:.2f} km")
        if total_time > 24 * 60:
            print("⚠️ Duration exceeds 24 hrs — review plan.")

    # -----------------------
    # Build optimized plan
    # -----------------------
    optimized_entries = optimize_poi_sequence(entries, start_coords, end_coords)

    print("\n📅 Final Time-Aware Plan (Optimized Order):")
    opt_time, opt_dist, opt_details = build_time_aware_plan(
        optimized_entries, start_time, start_loc, end_loc, default_mode
    )
    for d in opt_details:
        print(" ", d)
    print(f"\nTotal Duration: {opt_time} mins | Total Distance: {opt_dist:.2f} km")
    if opt_time > 24 * 60:
        print("⚠️ Duration exceeds 24 hrs — review plan.")


if __name__ == "__main__":
    # Allow CLI args to skip prompt
    arg_mode = None
    if len(sys.argv) > 1:
        if "--optimized-only" in sys.argv:
            arg_mode = "2"
        elif "--both" in sys.argv:
            arg_mode = "1"
    run_time_aware_optimizer(show_mode=arg_mode)