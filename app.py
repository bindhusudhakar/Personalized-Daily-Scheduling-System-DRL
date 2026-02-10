from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from compare_rl_vs_heuristic import compare_plans
from dynamic_reoptimizer import reoptimize_itinerary
from itinerary_optimizer2 import generate_itinerary
import datetime
import auth_utils


app = FastAPI(title="Itinerary Planner API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "http://localhost:3001", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
auth_utils.init_users_table()

# ----------------------------
# Request Models
# ----------------------------


class POIEntry(BaseModel):
    name: str
    priority: int
    dwell_mins: int


class POIEntryWithTarget(BaseModel):
    name: str
    priority: int
    dwell_mins: int
    target_arrival: Optional[str] = None  # Format: "HH:MM"


class GenerateItineraryRequest(BaseModel):
    pois: List[POIEntryWithTarget]
    mode: Optional[str] = "driving"
    round_trip: Optional[bool] = False
    start_time: Optional[str] = "09:00"  # Format: "HH:MM"
    end_time: Optional[str] = "22:00"    # Format: "HH:MM"
    debug: Optional[bool] = False


class OptimizeRequest(BaseModel):
    pois: List[POIEntry]
    mode: Optional[str] = "driving"


class ReoptimizeRequest(BaseModel):
    current_state: dict   # Include current location, visited POIs, time, etc.
    new_entries: Optional[List[POIEntry]] = []
    available_time: Optional[int] = 480  # in minutes


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


# ----------------------------
# API Endpoints
# ----------------------------


@app.post("/generate-itinerary")
def generate_itinerary_endpoint(req: GenerateItineraryRequest):
    """
    Generate a complete itinerary with user plan and optimized plan(s).

    Example request:
    {
        "pois": [
            {"name": "orion mall", "priority": 5, "dwell_mins": 180, "target_arrival": "13:00"},
            {"name": "lalbagh", "priority": 2, "dwell_mins": 45}
        ],
        "mode": "driving",
        "round_trip": true,
        "start_time": "09:00",
        "end_time": "16:00",
        "debug": true
    }
    """
    try:
        # Parse times
        start_h, start_m = map(int, req.start_time.split(":"))
        start_time = datetime.datetime.combine(
            datetime.date.today(), datetime.time(start_h, start_m))

        end_h, end_m = map(int, req.end_time.split(":"))
        end_time = datetime.datetime.combine(
            datetime.date.today(), datetime.time(end_h, end_m))

        # Parse POIs with target arrival times
        raw_entries = []
        for poi in req.pois:
            target_arrival = None
            if poi.target_arrival:
                try:
                    ta_h, ta_m = map(int, poi.target_arrival.split(":"))
                    target_arrival = datetime.datetime.combine(
                        datetime.date.today(), datetime.time(ta_h, ta_m))
                except Exception:
                    pass
            raw_entries.append(
                (poi.name, poi.priority, poi.dwell_mins, target_arrival))

        # Generate itinerary
        result = generate_itinerary(
            raw_entries=raw_entries,
            mode=req.mode,
            round_trip=req.round_trip,
            start_time=start_time,
            end_time=end_time,
            debug=req.debug
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/optimize")
def optimize_itinerary(req: OptimizeRequest):
    try:
        raw_entries = [(p.name, p.priority, p.dwell_mins) for p in req.pois]
        result = compare_plans(raw_entries, mode=req.mode)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reoptimize")
def reoptimize_itinerary(req: ReoptimizeRequest):
    try:
        result = reoptimize_itinerary(
            current_state=req.current_state,
            new_entries=[(p.name, p.priority, p.dwell_mins)
                         for p in req.new_entries],
            available_time=req.available_time
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    token = auth_utils.create_access_token(user_data["id"])

    return AuthResponse(
        success=True,
        message=message,
        user=user_data,
        token=token
    )


@app.get("/api/auth/user/{user_id}")
def get_user(user_id: int):
    """
    Fetch user data by ID (requires valid token)
    """
    user = auth_utils.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "success": True,
        "user": user
    }


@app.get("/api/auth/user/{user_id}")
def get_user(user_id: int):
    """
    Fetch user data by ID (requires valid token)
    """
    user = auth_utils.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "success": True,
        "user": user
    }


@app.get("/api/auth/users")
def get_all_users():
    """
    Fetch all users from the database
    """
    users = auth_utils.get_all_users()

    return {
        "success": True,
        "total": len(users),
        "users": users
    }


@app.delete("/api/auth/user/{user_id}")
def delete_user(user_id: int):
    """
    Delete a user by ID
    """
    success, message = auth_utils.delete_user_by_id(user_id)

    if not success:
        raise HTTPException(status_code=404, detail=message)

    return {
        "success": True,
        "message": message
    }


@app.delete("/api/auth/user/email/{email}")
def delete_user_by_email(email: str):
    """
    Delete a user by email
    """
    success, message = auth_utils.delete_user_by_email(email)

    if not success:
        raise HTTPException(status_code=404, detail=message)

    return {
        "success": True,
        "message": message
    }


@app.delete("/api/auth/users/all")
def delete_all_users():
    """
    Delete all users from the database (use with caution!)
    """
    success, message = auth_utils.delete_all_users()

    if not success:
        raise HTTPException(status_code=500, detail=message)

    return {
        "success": True,
        "message": message
    }
