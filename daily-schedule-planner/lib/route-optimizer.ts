interface ScheduleItem {
  id: string
  name: string
  type: string
  priority: number
  dwellTime: number
  targetArrival?: string
  notes?: string
}

interface OptimizationResult {
  originalRoute: ScheduleItem[]
  optimizedRoute: ScheduleItem[]
  userPlan: ScheduleItem[]
  alternativePlan?: ScheduleItem[]
  metrics: {
    totalDistance: number
    totalTime: number
    timeSaved: number
    costSaved: number
    droppedPOIs: ScheduleItem[]
  }
}

interface RouteFactors {
  distance: number
  walkingDistance: number
  trafficLights: number
  expediteRatio: number
  slowRatio: number
  congestionRatio: number
  unknownRatio: number
  duration: number
  dailySales: number
  rating: number
  cost: number
}

// Mock coordinates for distance calculation
const mockCoordinates: Record<string, { lat: number; lng: number }> = {
  Home: { lat: 12.9716, lng: 77.5946 },
  Office: { lat: 12.9352, lng: 77.6245 },
  College: { lat: 12.9279, lng: 77.6271 },
  "City Mall": { lat: 12.9698, lng: 77.6469 },
  "Local Temple": { lat: 12.9634, lng: 77.5855 },
  Hospital: { lat: 12.9591, lng: 77.6402 },
  Restaurant: { lat: 12.9667, lng: 77.6102 },
  Bank: { lat: 12.9548, lng: 77.6321 },
  Gym: { lat: 12.9423, lng: 77.6156 },
  Park: { lat: 12.9512, lng: 77.5982 },
}

// Calculate distance between two points using Haversine formula
function calculateDistance(point1: string, point2: string): number {
  const coord1 = mockCoordinates[point1] || { lat: 12.9716, lng: 77.5946 }
  const coord2 = mockCoordinates[point2] || { lat: 12.9716, lng: 77.5946 }

  const R = 6371 // Earth's radius in kilometers
  const dLat = ((coord2.lat - coord1.lat) * Math.PI) / 180
  const dLng = ((coord2.lng - coord1.lng) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((coord1.lat * Math.PI) / 180) *
      Math.cos((coord2.lat * Math.PI) / 180) *
      Math.sin(dLng / 2) *
      Math.sin(dLng / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

// Generate route factors for each POI pair
function generateRouteFactors(from: string, to: string): RouteFactors {
  const distance = calculateDistance(from, to)
  const baseTime = distance * 3 + Math.random() * 10 // Base travel time in minutes

  return {
    distance,
    walkingDistance: distance * 0.1 + Math.random() * 0.5,
    trafficLights: Math.floor(distance * 2 + Math.random() * 3),
    expediteRatio: 0.4 + Math.random() * 0.4,
    slowRatio: 0.2 + Math.random() * 0.3,
    congestionRatio: 0.1 + Math.random() * 0.2,
    unknownRatio: 0.1 + Math.random() * 0.1,
    duration: baseTime,
    dailySales: Math.floor(Math.random() * 1000) + 100,
    rating: 3.5 + Math.random() * 1.5,
    cost: distance * 15 + Math.random() * 50, // Cost in rupees
  }
}

// Deep Activity Factor Balancing Network (DAFB) simulation
function calculateDSRScore(factors: RouteFactors, priority: number): number {
  // Spatial factors (normalized to 0-1, lower is better)
  const spatialScore =
    1 -
    Math.min(factors.distance / 10, 1) * 0.4 -
    Math.min(factors.walkingDistance / 2, 1) * 0.3 -
    Math.min(factors.trafficLights / 10, 1) * 0.3

  // Traffic factors (normalized to 0-1, higher expedite ratio is better)
  const trafficScore = factors.expediteRatio * 0.6 + (1 - factors.congestionRatio) * 0.4

  // Service quality factors (normalized to 0-1, higher is better)
  const serviceScore = Math.min(factors.rating / 5, 1) * 0.7 + Math.min(factors.dailySales / 1000, 1) * 0.3

  // Combine factors with weights (as per research paper)
  const combinedScore = spatialScore * 0.3 + trafficScore * 0.3 + serviceScore * 0.4

  const priorityWeight = priority / 5
  return combinedScore * 0.7 + priorityWeight * 0.3
}

// Reinforcement Learning-based optimization (simplified)
function optimizeRouteRL(
  startLocation: string,
  endLocation: string,
  scheduleItems: ScheduleItem[],
  maxTime?: number,
): OptimizationResult {
  const userPlan = [...scheduleItems] // Original order as entered by user
  const currentRoute = [...scheduleItems]
  let bestRoute = [...scheduleItems]
  let bestScore = Number.NEGATIVE_INFINITY

  // Monte Carlo sampling for route optimization
  const iterations = 100
  for (let i = 0; i < iterations; i++) {
    // Create a random permutation
    const testRoute = [...currentRoute].sort(() => Math.random() - 0.5)

    // Calculate route score
    let routeScore = 0
    let totalTime = 0
    let totalCost = 0
    let currentLocation = startLocation

    for (const item of testRoute) {
      const factors = generateRouteFactors(currentLocation, item.name)
      const dsrScore = calculateDSRScore(factors, item.priority)

      routeScore += dsrScore
      totalTime += factors.duration + item.dwellTime
      totalCost += factors.cost
      currentLocation = item.name
    }

    // Add final leg to end location
    const finalFactors = generateRouteFactors(currentLocation, endLocation)
    totalTime += finalFactors.duration
    totalCost += finalFactors.cost

    // Apply time constraint penalty
    if (maxTime && totalTime > maxTime) {
      routeScore -= (totalTime - maxTime) * 0.1
    }

    // Update best route if this is better
    if (routeScore > bestScore) {
      bestScore = routeScore
      bestRoute = [...testRoute]
    }
  }

  // Apply pruning logic if time exceeds constraints
  let optimizedRoute = [...bestRoute]
  const droppedPOIs: ScheduleItem[] = []

  if (maxTime) {
    let currentTime = 0
    let currentLocation = startLocation
    const validRoute: ScheduleItem[] = []

    // Sort by priority for pruning decisions
    const sortedByPriority = [...optimizedRoute].sort((a, b) => b.priority - a.priority)

    for (const item of sortedByPriority) {
      const factors = generateRouteFactors(currentLocation, item.name)
      const itemTime = factors.duration + item.dwellTime

      if (currentTime + itemTime <= maxTime * 0.9) {
        // Keep 10% buffer
        validRoute.push(item)
        currentTime += itemTime
        currentLocation = item.name
      } else {
        droppedPOIs.push(item)
      }
    }

    optimizedRoute = validRoute
  }

  // Generate alternative plan (different optimization strategy)
  const alternativeRoute = [...scheduleItems].sort((a, b) => {
    // Alternative: optimize by type clustering and then priority
    if (a.type === b.type) {
      return b.priority - a.priority
    }
    return a.type.localeCompare(b.type)
  })

  // Calculate metrics
  const originalDistance = calculateTotalDistance(startLocation, endLocation, userPlan)
  const optimizedDistance = calculateTotalDistance(startLocation, endLocation, optimizedRoute)
  const originalTime = calculateTotalTime(startLocation, endLocation, userPlan)
  const optimizedTime = calculateTotalTime(startLocation, endLocation, optimizedRoute)

  return {
    originalRoute: userPlan,
    optimizedRoute,
    userPlan,
    alternativePlan: alternativeRoute.length !== optimizedRoute.length ? alternativeRoute : undefined,
    metrics: {
      totalDistance: optimizedDistance,
      totalTime: optimizedTime,
      timeSaved: Math.max(0, originalTime - optimizedTime),
      costSaved: Math.max(0, (originalDistance - optimizedDistance) * 15),
      droppedPOIs,
    },
  }
}

function calculateTotalDistance(startLocation: string, endLocation: string, route: ScheduleItem[]): number {
  let totalDistance = 0
  let currentLocation = startLocation

  for (const item of route) {
    totalDistance += calculateDistance(currentLocation, item.name)
    currentLocation = item.name
  }

  totalDistance += calculateDistance(currentLocation, endLocation)
  return totalDistance
}

function calculateTotalTime(startLocation: string, endLocation: string, route: ScheduleItem[]): number {
  let totalTime = 0
  let currentLocation = startLocation

  for (const item of route) {
    const factors = generateRouteFactors(currentLocation, item.name)
    totalTime += factors.duration + item.dwellTime
    currentLocation = item.name
  }

  const finalFactors = generateRouteFactors(currentLocation, endLocation)
  totalTime += finalFactors.duration
  return totalTime
}

// POI Recommendation Engine
export function generatePOIRecommendations(
  currentRoute: ScheduleItem[],
  startLocation: string,
  endLocation: string,
): Array<{
  id: string
  name: string
  type: string
  rating: number
  distance: number
  estimatedTime: number
  priceRange: string
  isOnRoute: boolean
  description: string
  dsrScore: number
}> {
  const poiDatabase = [
    { name: "Spice Garden Restaurant", type: "Restaurant", baseRating: 4.5 },
    { name: "Sri Lakshmi Temple", type: "Temple", baseRating: 4.7 },
    { name: "Quick Mart Pharmacy", type: "Pharmacy", baseRating: 4.2 },
    { name: "Green Valley Park", type: "Park", baseRating: 4.4 },
    { name: "City Center Mall", type: "Shopping", baseRating: 4.3 },
    { name: "Express Fuel Station", type: "Gas Station", baseRating: 4.1 },
    { name: "Fitness First Gym", type: "Gym", baseRating: 4.6 },
    { name: "Apollo Hospital", type: "Hospital", baseRating: 4.8 },
    { name: "HDFC Bank", type: "Bank", baseRating: 4.0 },
    { name: "Coffee Day Cafe", type: "Restaurant", baseRating: 4.3 },
  ]

  return poiDatabase
    .map((poi, index) => {
      const factors = generateRouteFactors(startLocation, poi.name)
      const dsrScore = calculateDSRScore(factors, 3)

      return {
        id: `poi-${index}`,
        name: poi.name,
        type: poi.type,
        rating: poi.baseRating + (Math.random() - 0.5) * 0.4,
        distance: factors.distance,
        estimatedTime: factors.duration,
        priceRange: factors.cost < 100 ? "₹" : factors.cost < 300 ? "₹₹" : "₹₹₹",
        isOnRoute: Math.random() > 0.6,
        description: `${poi.type} with excellent service and convenient location`,
        dsrScore,
      }
    })
    .sort((a, b) => b.dsrScore - a.dsrScore) // Sort by DSR score
}

// Backend integration option
import { apiClient, type RouteOptimizationRequest } from "./api-client"

// Enhanced optimization function with backend integration
export async function optimizeRouteWithBackend(
  startLocation: string,
  endLocation: string,
  scheduleItems: ScheduleItem[],
  maxTime?: number,
  useBackend = true,
): Promise<OptimizationResult> {
  console.log("[v0] Starting route optimization, useBackend:", useBackend)

  if (useBackend) {
    try {
      console.log("[v0] Calling backend API for route optimization")

      const request: RouteOptimizationRequest = {
        startLocation,
        endLocation,
        scheduleItems,
        maxTime,
        userPreferences: {
          prioritizeTime: true,
          prioritizeCost: false,
          avoidTraffic: true,
        },
      }

      const response = await apiClient.optimizeRoute(request)

      console.log("[v0] Backend optimization completed successfully")

      // Convert backend response to our OptimizationResult format
      return {
        originalRoute: response.originalRoute,
        optimizedRoute: response.optimizedRoute,
        userPlan: response.userPlan,
        alternativePlan: response.alternativePlan,
        metrics: response.metrics,
      }
    } catch (error) {
      console.error("[v0] Backend optimization failed, falling back to local optimization:", error)
      // Fallback to local optimization if backend fails
      return optimizeRouteRL(startLocation, endLocation, scheduleItems, maxTime)
    }
  } else {
    console.log("[v0] Using local optimization algorithm")
    return optimizeRouteRL(startLocation, endLocation, scheduleItems, maxTime)
  }
}

// Enhanced POI recommendations with backend integration
export async function getPOIRecommendationsWithBackend(
  currentRoute: ScheduleItem[],
  startLocation: string,
  endLocation: string,
  useBackend = true,
): Promise<
  Array<{
    id: string
    name: string
    type: string
    rating: number
    distance: number
    estimatedTime: number
    priceRange: string
    isOnRoute: boolean
    description: string
    dsrScore: number
  }>
> {
  console.log("[v0] Getting POI recommendations, useBackend:", useBackend)

  if (useBackend) {
    try {
      console.log("[v0] Calling backend API for POI recommendations")

      const response = await apiClient.getPOIRecommendations({
        currentRoute,
        startLocation,
        endLocation,
        filters: [],
        radius: 5, // 5km radius
      })

      console.log("[v0] Backend POI recommendations received")
      return response.recommendations
    } catch (error) {
      console.error("[v0] Backend POI recommendations failed, using local data:", error)
      // Fallback to local recommendations
      return generatePOIRecommendations(currentRoute, startLocation, endLocation)
    }
  } else {
    console.log("[v0] Using local POI recommendations")
    return generatePOIRecommendations(currentRoute, startLocation, endLocation)
  }
}

export { optimizeRouteRL, type OptimizationResult, type ScheduleItem }
