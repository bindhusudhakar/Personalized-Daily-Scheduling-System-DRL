# optimizer.py
import math
from typing import List, Dict, Tuple

# ------------------------
# Utility: Haversine Distance
# ------------------------
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance between two coords (km)."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# ------------------------
# Core Optimizer
# ------------------------
def optimize_poi_sequence(
    pois: List[Dict],
    start_coords: Tuple[float, float],
    end_coords: Tuple[float, float] = None
) -> List[Dict]:
    """
    Reorder flexible POIs to reduce travel distance.
    - Fixed-time POIs remain anchors.
    - BREAK entries are left untouched.
    - Flexible POIs are arranged by nearest-neighbor.
    - If start coords missing OR no coords for flexible POIs, returns original order.
    """

    # --- Sanity checks ---
    if not pois or len(pois) <= 1:
        return pois
    if (not start_coords or
        start_coords[0] is None or start_coords[1] is None):
        return pois  # No meaningful reference point

    # Separate anchors, breaks, and flexible
    anchors = [p for p in pois if p.get("fixed_start")]
    flexible_all = [p for p in pois if not p.get("fixed_start") and not p.get("is_break")]

    # Split flexible into valid coords vs invalid coords
    flexible_valid = [p for p in flexible_all if p.get("lat") is not None and p.get("lon") is not None]
    flexible_invalid = [p for p in flexible_all if p.get("lat") is None or p.get("lon") is None]

    if not flexible_valid:
        return pois  # nothing to optimize

    # Sort anchors by time
    anchors.sort(key=lambda x: x["fixed_start"])

    # Build optimized order for flexible
    optimized_flexible: List[Dict] = []
    current_coords = start_coords

    for anchor in anchors:
        nearest_chunk = []
        while flexible_valid:
            nearest = min(
                flexible_valid,
                key=lambda f: haversine_km(
                    current_coords[0], current_coords[1], f["lat"], f["lon"]
                )
            )
            # Heuristic to avoid long detours
            dist_to_flex = haversine_km(current_coords[0], current_coords[1], nearest["lat"], nearest["lon"])
            dist_to_anchor = haversine_km(nearest["lat"], nearest["lon"], anchor["lat"], anchor["lon"])
            direct_dist = haversine_km(current_coords[0], current_coords[1], anchor["lat"], anchor["lon"])

            if dist_to_flex + dist_to_anchor > direct_dist * 1.5:
                break

            nearest_chunk.append(nearest)
            current_coords = (nearest["lat"], nearest["lon"])
            flexible_valid.remove(nearest)

        optimized_flexible.extend(nearest_chunk)
        current_coords = (anchor["lat"], anchor["lon"])  # jump to anchor

    # Add remaining flexible POIs
    while flexible_valid:
        nearest = min(
            flexible_valid,
            key=lambda f: haversine_km(
                current_coords[0], current_coords[1], f["lat"], f["lon"]
            )
        )
        optimized_flexible.append(nearest)
        current_coords = (nearest["lat"], nearest["lon"])
        flexible_valid.remove(nearest)

    # Append those without coords at the end
    optimized_flexible.extend(flexible_invalid)

    # Rebuild final sequence, preserving anchors & breaks in place
    final_seq = []
    flex_iter = iter(optimized_flexible)
    for p in pois:
        if p.get("fixed_start") or p.get("is_break"):
            final_seq.append(p)
        else:
            final_seq.append(next(flex_iter))

    # Awareness of end location (reserved for extension)
    if end_coords:
        pass

    return final_seq
