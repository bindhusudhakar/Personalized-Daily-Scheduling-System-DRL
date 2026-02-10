"use client"

import { useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Navigation, Clock, Star, MapPin } from "lucide-react"

interface ScheduleItem {
  id: string
  name: string
  type: string
  priority: number
  dwellTime: number
  targetArrival?: string
  notes?: string
}

interface ScheduleData {
  startLocation: string
  endLocation: string
  scheduleItems: ScheduleItem[]
  timestamp: number
}

interface RouteMapProps {
  scheduleData: ScheduleData
}

// Mock coordinates for demonstration
const mockCoordinates = {
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

export function RouteMap({ scheduleData }: RouteMapProps) {
  const mapRef = useRef<HTMLDivElement>(null)
  const [selectedPoint, setSelectedPoint] = useState<string | null>(null)

  // Simulate optimized route order
  const optimizedRoute = [
    { name: scheduleData.startLocation, type: "start", priority: 5, dwellTime: 0 },
    ...scheduleData.scheduleItems.sort((a, b) => b.priority - a.priority),
    { name: scheduleData.endLocation, type: "end", priority: 5, dwellTime: 0 },
  ]

  const getCoordinate = (name: string) => {
    return mockCoordinates[name as keyof typeof mockCoordinates] || { lat: 12.9716, lng: 77.5946 }
  }

  const getPriorityColor = (priority: number) => {
    if (priority >= 5) return "#ef4444" // red - Critical
    if (priority >= 4) return "#f97316" // orange - High
    if (priority >= 3) return "#eab308" // yellow - Medium
    if (priority >= 2) return "#3b82f6" // blue - Low
    return "#22c55e" // green - Optional
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "start":
        return "🏠"
      case "end":
        return "🏁"
      case "Restaurant":
        return "🍽️"
      case "Temple":
        return "🛕"
      case "Shopping":
        return "🛍️"
      case "Hospital":
        return "🏥"
      case "Bank":
        return "🏦"
      case "Gas Station":
        return "⛽"
      case "Pharmacy":
        return "💊"
      case "Gym":
        return "💪"
      case "Park":
        return "🌳"
      default:
        return "📍"
    }
  }

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <Navigation className="h-5 w-5 text-primary" />
          Interactive Route Map
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0 h-[calc(100%-80px)]">
        <div className="relative h-full bg-gradient-to-br from-blue-50 to-green-50 rounded-b-lg overflow-hidden">
          <div className="absolute inset-0 opacity-30">
            <svg width="100%" height="100%" className="text-muted-foreground">
              <defs>
                <pattern id="streets" width="60" height="60" patternUnits="userSpaceOnUse">
                  <path d="M 0 30 L 60 30 M 30 0 L 30 60" fill="none" stroke="currentColor" strokeWidth="2" />
                  <path
                    d="M 0 15 L 60 15 M 0 45 L 60 45 M 15 0 L 15 60 M 45 0 L 45 60"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1"
                    opacity="0.5"
                  />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#streets)" />
            </svg>
          </div>

          {/* Route Points and Directions */}
          <div className="absolute inset-4">
            {optimizedRoute.map((point, index) => {
              const coord = getCoordinate(point.name)
              const isSelected = selectedPoint === point.name
              const nextPoint = optimizedRoute[index + 1]

              return (
                <div key={`${point.name}-${index}`} className="absolute">
                  <div
                    className="relative cursor-pointer transform -translate-x-1/2 -translate-y-1/2"
                    style={{
                      left: `${(((coord.lng - 77.5) * 1000) % 80) + 20}%`,
                      top: `${(((coord.lat - 12.9) * 2000) % 70) + 15}%`,
                    }}
                    onClick={() => setSelectedPoint(isSelected ? null : point.name)}
                  >
                    {nextPoint && (
                      <div className="absolute top-1/2 left-full z-0">
                        <div
                          className="w-20 h-1 bg-primary/70 relative"
                          style={{
                            transform: `rotate(${Math.random() * 60 - 30}deg)`,
                            transformOrigin: "left center",
                          }}
                        >
                          {/* Direction arrow */}
                          <div className="absolute right-0 top-1/2 transform -translate-y-1/2 translate-x-1">
                            <div className="w-0 h-0 border-l-4 border-l-primary/70 border-t-2 border-t-transparent border-b-2 border-b-transparent"></div>
                          </div>
                          {/* Distance label */}
                          <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-1 text-xs bg-white px-1 rounded shadow">
                            {(Math.random() * 2 + 0.5).toFixed(1)}km
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Point Marker */}
                    <div
                      className={`relative z-10 w-12 h-12 rounded-full border-4 border-white shadow-lg flex items-center justify-center text-lg transition-all duration-200 ${
                        isSelected ? "scale-125 shadow-xl" : "hover:scale-110"
                      }`}
                      style={{
                        backgroundColor:
                          point.type === "start" || point.type === "end" ? "#ea580c" : getPriorityColor(point.priority),
                      }}
                    >
                      {getTypeIcon(point.type)}
                    </div>

                    {/* Route Number */}
                    <div className="absolute -top-2 -right-2 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">
                      {index + 1}
                    </div>

                    {isSelected && (
                      <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 z-20">
                        <div className="bg-white rounded-lg shadow-lg border p-3 min-w-52">
                          <div className="text-sm font-medium mb-1">{point.name}</div>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                            <Badge variant="outline" className="text-xs">
                              {point.type}
                            </Badge>
                            {point.dwellTime > 0 && (
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {point.dwellTime}min
                              </span>
                            )}
                          </div>
                          <div className="space-y-1 text-xs">
                            <div className="flex items-center gap-1">
                              <Star className="h-3 w-3 text-yellow-500" />
                              <span>4.{Math.floor(Math.random() * 5 + 3)} rating</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <MapPin className="h-3 w-3 text-blue-500" />
                              <span>{(Math.random() * 5 + 1).toFixed(1)}km away</span>
                            </div>
                            <div className="text-green-600">ETA: {Math.floor(Math.random() * 30 + 10)} min</div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          <div className="absolute top-4 left-4 bg-white rounded-lg shadow-md p-3 max-w-xs">
            <div className="text-sm font-medium mb-2">Route Summary</div>
            <div className="space-y-1 text-xs">
              <div>Total Distance: {(optimizedRoute.length * 1.2 + Math.random() * 2).toFixed(1)} km</div>
              <div>Estimated Time: {Math.floor(optimizedRoute.length * 15 + Math.random() * 20)} min</div>
              <div>Stops: {optimizedRoute.length - 2}</div>
            </div>
          </div>

          {/* Map Controls */}
          <div className="absolute top-4 right-4 flex flex-col gap-2">
            <button className="w-10 h-10 bg-white rounded-lg shadow-md flex items-center justify-center hover:bg-gray-50">
              <span className="text-lg">+</span>
            </button>
            <button className="w-10 h-10 bg-white rounded-lg shadow-md flex items-center justify-center hover:bg-gray-50">
              <span className="text-lg">-</span>
            </button>
          </div>

          {/* Legend */}
          <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-md p-3">
            <div className="text-xs font-medium mb-2">Route Priority</div>
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <span>Critical (5)</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                <span>High (4)</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <span>Medium (3)</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <span>Low (2)</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span>Optional (1)</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
