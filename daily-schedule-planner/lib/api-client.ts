interface APIConfig {
  baseURL: string
  timeout?: number
}

interface SignupRequest {
  email: string
  password: string
  full_name: string
}

interface LoginRequest {
  email: string
  password: string
}

interface AuthUser {
  id: number
  email: string
  full_name: string
  created_at: string
}

interface AuthResponse {
  success: boolean
  message: string
  user?: AuthUser
  token?: string
}

interface POISearchRequest {
  query: string
}

interface POISearchResponse {
  name: string
  lat: number
  lon: number
}

interface ItineraryRequest {
  start: string | null
  end: string | null
  pois: Array<{
    name: string
    priority: number
    dwell: number
  }>
  mode: string
}

interface Leg {
  from: string
  to: string
  from_lat: number
  from_lon: number
  to_lat: number
  to_lon: number
  departure_time: string
  departure_time_hm: string
  arrival_time: string
  arrival_time_hm: string
  leave_time: string | null
  leave_time_hm: string | null
  duration_sec: number
  distance_m: number
  weather: {
    condition: string
    temp_c: number
    wind_speed: number
    rain: number
  }
  mode: string
  dwell_mins: number
}

interface POISequence {
  name: string
  priority: number
  dwell_mins: number
  target_arrival?: string
  lat?: number
  lon?: number
}

interface PlanData {
  sequence: POISequence[]
  dropped?: POISequence[]
  total_seconds: number
  total_distance_m: number
  legs: Leg[]
  over_time?: string[]
}

interface ItineraryResponse {
  start_time: string
  end_time: string
  mode: string
  round_trip: boolean
  start_coords: [number, number]
  user_plan: PlanData
  optimized_plan: PlanData
  alternative_optimized_plan?: PlanData | null
}

interface ReoptimizeRequest {
  current_location: [number, number]
  current_time_minutes: number
  remaining_pois: Array<{
    name: string
    lat: number
    lon: number
    priority: number
    dwell: number
  }>
  mode: string
}

interface ReoptimizeResponse {
  optimized_sequence: Array<{
    name: string
    priority: number
  }>
  total_duration_sec: number
  total_distance_m: number
}

interface ScheduleItem {
  id: string
  name: string
  type: string
  priority: number
  dwellTime: number
  targetArrival?: string
  notes?: string
}

class APIClient {
  private config: APIConfig

  constructor(config: APIConfig) {
    this.config = {
      timeout: 10000,
      ...config,
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.config.baseURL}${endpoint}`

    console.log(`[API] POST ${endpoint}`, {
      url,
      payload: options.body ? JSON.parse(options.body as string) : null,
    })

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout)

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorText = await response.text()
        console.error(`[API] Error ${response.status}:`, errorText)
        throw new Error(`API Error: ${response.status} ${response.statusText}\n${errorText}`)
      }

      const data = await response.json()
      console.log(`[API] Response from ${endpoint}:`, data)
      return data
    } catch (error) {
      clearTimeout(timeoutId)
      console.error(`[API] Request failed for ${endpoint}:`, error)
      throw error
    }
  }

  async searchPOIs(query: string): Promise<POISearchResponse[]> {
    return this.request<POISearchResponse[]>("/api/pois/search", {
      method: "POST",
      body: JSON.stringify({ query }),
    })
  }

  async generateItinerary(request: {
    startLocation: string
    endLocation: string
    scheduleItems: ScheduleItem[]
    mode?: string
    startTime?: string
    endTime?: string
    debug?: boolean
  }): Promise<ItineraryResponse> {
    console.log("[Integration] generateItinerary called with:", request)

    // Build POIs array including start and end locations
    const pois = []
    
    // Add starting location as first POI
    if (request.startLocation) {
      pois.push({
        name: request.startLocation,
        priority: 5, // High priority for start/end points
        dwell_mins: 0, // No dwell time at start
      })
    }
    
    // Add all destination POIs
    pois.push(...request.scheduleItems.map((item) => ({
      name: item.name,
      priority: item.priority,
      dwell_mins: item.dwellTime,
      target_arrival: item.targetArrival || undefined,
    })))
    
    // Add ending location as last POI (if different from start and not round trip)
    const isRoundTrip = !request.endLocation || request.endLocation === request.startLocation
    if (!isRoundTrip && request.endLocation) {
      pois.push({
        name: request.endLocation,
        priority: 5,
        dwell_mins: 0,
      })
    }

    const backendRequest = {
      pois,
      mode: request.mode || "driving",
      round_trip: isRoundTrip,
      start_time: request.startTime || "09:00",
      end_time: request.endTime || "22:00",
      debug: request.debug || false,
    }

    console.log("[Integration] Sending to backend:", backendRequest)

    try {
      const response = await this.request<ItineraryResponse>("/generate-itinerary", {
        method: "POST",
        body: JSON.stringify(backendRequest),
      })

      console.log("[Integration] Received response:", response)
      return response
    } catch (error) {
      console.error("[Integration] generateItinerary failed:", error)
      throw error
    }
  }

  async optimizeItinerary(request: {
    pois: Array<{
      name: string
      priority: number
      dwell_mins: number
    }>
    mode?: string
  }): Promise<any> {
    return this.request<any>("/optimize", {
      method: "POST",
      body: JSON.stringify(request),
    })
  }

  async reoptimizeItinerary(request: ReoptimizeRequest): Promise<ReoptimizeResponse> {
    return this.request<ReoptimizeResponse>("/reoptimize", {
      method: "POST",
      body: JSON.stringify(request),
    })
  }

  async healthCheck(): Promise<{ status: string }> {
    try {
      const response = await fetch(`${this.config.baseURL}/docs`, {
        method: "GET",
      })
      return { status: response.ok ? "healthy" : "unhealthy" }
    } catch (error) {
      console.error("[API] Health check failed:", error)
      return { status: "unhealthy" }
    }
  }

  // ===========================
  // Authentication Endpoints
  // ===========================
  async signup(data: SignupRequest): Promise<AuthResponse> {
    try {
      return await this.request<AuthResponse>("/api/auth/signup", {
        method: "POST",
        body: JSON.stringify(data),
      })
    } catch (error) {
      console.error("[API] Signup failed:", error)
      throw error
    }
  }

  async login(data: LoginRequest): Promise<AuthResponse> {
    try {
      return await this.request<AuthResponse>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(data),
      })
    } catch (error) {
      console.error("[API] Login failed:", error)
      throw error
    }
  }

  async getUser(userId: number, token: string): Promise<{ success: boolean; user: AuthUser }> {
    try {
      return await this.request(`/api/auth/user/${userId}`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      })
    } catch (error) {
      console.error("[API] Get user failed:", error)
      throw error
    }
  }

  // Fallback method for when backend is unavailable
  async optimizeRouteLocal(request: {
    startLocation: string
    endLocation: string
    scheduleItems: ScheduleItem[]
  }): Promise<{
    originalRoute: ScheduleItem[]
    optimizedRoute: ScheduleItem[]
    metrics: {
      totalDistance: number
      totalTime: number
      timeSaved: number
      costSaved: number
    }
  }> {
    // Simple local optimization - sort by priority
    const optimizedRoute = [...request.scheduleItems].sort((a, b) => b.priority - a.priority)

    return {
      originalRoute: request.scheduleItems,
      optimizedRoute,
      metrics: {
        totalDistance: 15000,
        totalTime: 3600,
        timeSaved: 600,
        costSaved: 150,
      },
    }
  }
}

// Configuration
const API_CONFIG: APIConfig = {
  baseURL: process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000",
  timeout: 60000, // Increased to 60 seconds to handle slower backend responses
}

export const apiClient = new APIClient(API_CONFIG)
export type {
  ItineraryRequest,
  ItineraryResponse,
  POISearchRequest,
  POISearchResponse,
  ReoptimizeRequest,
  ReoptimizeResponse,
  ScheduleItem,
  Leg,
  POISequence,
  PlanData,
  APIConfig,
  SignupRequest,
  LoginRequest,
  AuthResponse,
}
