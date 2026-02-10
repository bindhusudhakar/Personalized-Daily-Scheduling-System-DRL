from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import datetime
import itinerary_optimizer2 as optimizer
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Itinerary Optimizer API")

# Initialize users table on startup
auth_utils.init_users_table()

app.add_middleware(
    CORSMiddleware,
    # for testing allow all, later restrict to your frontend domain
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------------
# Request Models
# -----------------------------


class POIRequest(BaseModel):
    name: str
    dwell_time: Optional[int] = 30   # minutes
    priority: Optional[int] = 5
    target_arrival: Optional[str] = None  # ISO format "2025-09-18T10:00"


class GenerateRequest(BaseModel):
    pois: List[POIRequest]
    start_time: str
    end_time: str
    mode: str = "driving"
    round_trip: bool = False


class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None
    token: Optional[str] = None

# -----------------------------
# Response Formatter
# -----------------------------


def format_plan(plan: dict):
    return {
        "total_time": optimizer.format_seconds(plan.get("total_seconds", 0)),
        "total_distance_km": round(plan.get("total_distance_m", 0) / 1000, 2),
        "dropped_pois": [p["name"] for p in plan.get("dropped", [])],
        "legs": [
            {
                "from": leg.get("from"),
                "to": leg.get("to"),
                "departure": leg.get("departure_time_hm"),
                "arrival": leg.get("arrival_time_hm"),
                "travel_time": optimizer.format_seconds(leg.get("duration_sec")),
                "stay_mins": leg.get("dwell_mins", 0),
                "distance_km": round(leg.get("distance_m", 0) / 1000, 2),
                "from_lat": leg.get("from_lat"),
                "from_lon": leg.get("from_lon"),
                "to_lat": leg.get("to_lat"),
                "to_lon": leg.get("to_lon"),
            }
            for leg in plan.get("legs", [])
        ]
    }

# -----------------------------
# Endpoints
# -----------------------------


@app.post("/api/itinerary/generate")
def generate_itinerary(request: GenerateRequest):
    try:
        # Convert POIs into raw_entries format
        raw_entries = []
        for poi in request.pois:
            target_dt = None
            if poi.target_arrival:
                try:
                    target_dt = datetime.datetime.fromisoformat(
                        poi.target_arrival)
                except Exception:
                    target_dt = None
            raw_entries.append(
                (poi.name, poi.priority, poi.dwell_time, target_dt))

        start_time = datetime.datetime.fromisoformat(request.start_time)
        end_time = datetime.datetime.fromisoformat(request.end_time)

        # Run optimizer
        itinerary = optimizer.generate_itinerary(
            raw_entries=raw_entries,
            mode=request.mode,
            round_trip=request.round_trip,
            start_time=start_time,
            end_time=end_time
        )

        # Build frontend-friendly response
        return {
            "user_plan": format_plan(itinerary["user_plan"]),
            "optimized_plan": format_plan(itinerary["optimized_plan"]),
            "alternative_plan": (
                format_plan(itinerary["alternative_optimized_plan"])
                if itinerary.get("alternative_optimized_plan") else None
            )
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# Authentication Endpoints
# -----------------------------


@app.post("/api/auth/signup", response_model=AuthResponse)
def signup(request: SignupRequest):
    """
    Create a new user account
    """
    # Validate input
    if not request.email or not request.password or not request.full_name:
        raise HTTPException(
            status_code=400, detail="Email, password, and full name are required")

    if len(request.password) < 6:
        raise HTTPException(
            status_code=400, detail="Password must be at least 6 characters")

    success, message, user_id = auth_utils.create_user(
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    # Create token
    token = auth_utils.create_access_token(user_id)
    user_data = auth_utils.get_user_by_id(user_id)

    return AuthResponse(
        success=True,
        message=message,
        user=user_data,
        token=token
    )


@app.post("/api/auth/login", response_model=AuthResponse)
def login(request: LoginRequest):
    """
    Authenticate user and return JWT token
    """
    if not request.email or not request.password:
        raise HTTPException(
            status_code=400, detail="Email and password are required")

    success, message, user_data = auth_utils.authenticate_user(
        email=request.email,
        password=request.password
    )

    if not success:
        raise HTTPException(status_code=401, detail=message)

    # Create token
    print(f"[Auth] Creating token for user {user_data['id']}")
    token = auth_utils.create_access_token(user_data["id"])

    if not token:
        print("[Auth] ❌ Token is None!")
    else:
        print(f"[Auth] ✅ Token created: {token[:20]}...")

    return AuthResponse(
        success=True,
        message=message,
        user=user_data,
        token=token
    )
