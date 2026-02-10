# dynamic_reoptimizer.py
from typing import List, Dict, Tuple
from context_utils import get_route_context
from itinerary_optimizer2 import total_trip_time_for_sequence, build_optimized_sequence
import copy


def reoptimize_itinerary(
    current_location: Tuple[float, float],
    current_time_minutes: int,
    remaining_pois: List[Dict],
    mode: str = "driving",
    realtime_weather: bool = True
) -> Dict:
    """
    Dynamically reoptimize itinerary based on current state.

    Args:
        current_location: (lat, lon) of user’s current location.
        current_time_minutes: minutes since start of day (0–1440).
        remaining_pois: List of dicts, each with {name, lat, lon, priority, dwell, fixed_start, is_break}.
        mode: Travel mode ("driving", "walking", etc.).
        realtime_weather: Whether to consider real-time weather data.

    Returns:
        dict with optimized sequence and updated context.
    """

    # Compute current time as datetime object (today + current_time_minutes)
    import datetime
    now = datetime.datetime.combine(datetime.date.today(), datetime.time(
        0, 0)) + datetime.timedelta(minutes=current_time_minutes)

    # Inject weather and traffic info into POIs context
    enriched_pois = []
    for poi in remaining_pois:
        context = get_route_context(
            origin=current_location,
            destination=(poi["lat"], poi["lon"]),
            mode=mode,
            realtime_weather=realtime_weather
        )
        enriched_poi = copy.deepcopy(poi)
        enriched_poi.update({
            "travel_sec": context["duration_sec"],
            "travel_dist": context["distance_meters"],
            "weather": context["weather"]
        })
        enriched_pois.append(enriched_poi)

    # Perform optimization considering enriched context
    optimized_sequence = build_optimized_sequence(enriched_pois, mode)

    # Ensure 'dwell_mins' key is present for compatibility
    for p in optimized_sequence:
        p.setdefault('dwell_mins', p.get('dwell', 15))

    # Compute updated total time and distance
    total_sec, total_dist, legs = total_trip_time_for_sequence(
        optimized_sequence, mode)

    return {
        "optimized_sequence": optimized_sequence,
        "total_duration_sec": total_sec,
        "total_distance_m": total_dist,
        "legs": legs,
        "timestamp": now.isoformat()
    }
