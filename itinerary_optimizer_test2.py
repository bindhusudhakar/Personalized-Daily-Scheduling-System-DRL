import datetime
from itinerary_optimizer2 import generate_itinerary, format_seconds, format_datetime


def run_itinerary_optimizer_test():
    print("Interactive Itinerary Optimizer Test")
    mode = input("Enter mode (driving/walking/bicycling/transit/two_wheeler) [driving]: ").strip() or "driving"

    n_str = input("How many POIs? ").strip()
    try:
        n = int(n_str) if n_str else 0
    except ValueError:
        print("⚠️ Invalid number entered. Defaulting to 0.")
        n = 0

    round_trip_in = input("Return to start? (y/n) [n]: ").strip().lower()
    round_trip = (round_trip_in == "y")

    start_time = datetime.datetime.combine(datetime.date.today(), datetime.time(9, 0))
    end_time_str = input("Enter end time (HH:MM) or blank for 22:00: ").strip()
    try:
        hh, mm = map(int, end_time_str.split(":"))
        end_time = datetime.datetime.combine(datetime.date.today(), datetime.time(hh, mm))
    except Exception:
        end_time = datetime.datetime.combine(datetime.date.today(), datetime.time(22, 0))

    raw = []
    for i in range(n):
        s = input(f"POI {i+1} (Name,priority,dwell_mins,target_arrival HH:MM or blank): ")
        parts = [p.strip() for p in s.split(",")]
        if len(parts) < 2:
            print("⚠️ Invalid input format. Skipping this POI.")
            continue

        name = parts[0]
        try:
            pri = int(parts[1])
        except Exception:
            pri = 1

        dwell = 15
        if len(parts) > 2 and parts[2]:
            try:
                dwell = int(parts[2])
            except Exception:
                dwell = 15

        target_arrival = None
        if len(parts) > 3 and parts[3]:
            try:
                hh, mm = map(int, parts[3].split(":"))
                target_arrival = datetime.datetime.combine(datetime.date.today(), datetime.time(hh, mm))
            except Exception:
                target_arrival = None

        raw.append((name, pri, dwell, target_arrival))

    itinerary = generate_itinerary(
        raw_entries=raw,
        mode=mode,
        round_trip=round_trip,
        start_time=start_time,
        end_time=end_time,
        debug=True
    )

    def print_plan(title, plan, mark_over_time=False):
        print(f"\n=== {title} ===")
        legs = plan.get("legs", [])
        if not legs:
            print("No itinerary legs to show.")
            return

        headers = ["From", "Leave At", "To", "Travel Time", "Arrive At", "Stay(mins)", "Distance(km)"]
        col_widths = [25, 10, 25, 12, 10, 10, 12]

        def format_row(values, sep="│"):
            return sep + sep.join(f" {str(v)[:w]:{w}} " for v, w in zip(values, col_widths)) + sep

        top = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
        mid = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
        bottom = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"

        print(top)
        print(format_row(headers))
        print(mid)
        for leg in legs:
            over_note = ""
            if mark_over_time:
                at_str = leg.get("arrival_time")
                try:
                    at_dt = datetime.datetime.strptime(at_str, "%Y-%m-%d %H:%M")
                except Exception:
                    at_dt = None
                if at_dt and at_dt > end_time:
                    over_note = " ⚠️ Over time"
            row = [
                leg.get("from", "-"),
                leg.get("departure_time_hm") or "-",
                leg.get("to", "-") + over_note,
                format_seconds(leg.get("duration_sec", 0)),
                leg.get("arrival_time_hm") or "-",
                str(leg.get("dwell_mins", "-")),
                f"{(leg.get('distance_m', 0)/1000):.2f}"
            ]
            print(format_row(row))
        print(bottom)

        total_sec = plan.get("total_seconds", 0)
        total_dist_km = round(plan.get("total_distance_m", 0) / 1000, 2)
        print(f"\nTotal Time: {format_seconds(total_sec)} | Total Distance: {total_dist_km} km")

        dropped = plan.get("dropped", [])
        if dropped:
            print("\n⚠️ Dropped POIs (insufficient time):")
            for p in dropped:
                name = p.get("name", "Unknown POI")
                pri = p.get("priority", "-")
                dwell = p.get("dwell_mins", "-")
                print(f" - {name} (priority={pri}, dwell={dwell} mins)")

    # Print user plan (always full, mark any over-time POIs)
    print_plan("User Plan", itinerary["user_plan"], mark_over_time=True)

    # Print optimized plan (best) and optional alternative
    print("\n=== Optimized Plan (Primary Suggestion) ===")
    print_plan("Optimized Plan", itinerary["optimized_plan"])

    if itinerary.get("alternative_optimized_plan"):
        print("\n=== Optimized Plan (Alternative Suggestion) ===")
        print_plan("Alternative Optimized Plan", itinerary["alternative_optimized_plan"])

    # Conclusion + comparison
    print("\n=== Conclusion ===")
    user_sec = itinerary["user_plan"].get("total_seconds", 0)
    user_dist = itinerary["user_plan"].get("total_distance_m", 0)

    opt_plan = itinerary["optimized_plan"]
    opt_sec = opt_plan.get("total_seconds", 0)
    opt_dist = opt_plan.get("total_distance_m", 0)

    sec_diff = user_sec - opt_sec
    dist_diff = user_dist - opt_dist

    if sec_diff > 0 or dist_diff > 0:
        print(f"The Optimized Plan is recommended as it saves "
              f"{format_seconds(sec_diff) if sec_diff > 0 else '0 min'} "
              f"and {dist_diff/1000:.2f} km compared to your entered plan.")
    else:
        print("The Optimized Plan is recommended as it best balances travel time, "
              "POI priorities, and efficiency.")

    dropped = opt_plan.get("dropped", [])
    if dropped:
        print("\nNote: The following POIs were excluded from the Optimized Plan due to time or distance limits:")
        for p in dropped:
            name = p.get("name", "Unknown POI")
            pri = p.get("priority", "-")
            dwell = p.get("dwell_mins", "-")
            print(f" - {name} (priority={pri}, dwell={dwell} mins)")

    if itinerary.get("alternative_optimized_plan"):
        print("\nThe Alternative Optimized Plan is provided for flexibility, "
              "but the primary Optimized Plan is the best recommendation.")


if __name__ == "__main__":
    run_itinerary_optimizer_test()