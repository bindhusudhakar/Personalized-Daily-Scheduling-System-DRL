"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Star, MapPin, Clock, Plus, Filter } from "lucide-react"
import { getPOIRecommendationsWithBackend } from "@/lib/route-optimizer"

interface ScheduleData {
  startLocation: string
  endLocation: string
  scheduleItems: any[]
  timestamp: number
}

interface POIRecommendationsProps {
  scheduleData: ScheduleData
}

interface POI {
  id: string
  name: string
  type: string
  rating: number
  distance: number
  estimatedTime: number
  priceRange: string
  isOnRoute: boolean
  description: string
}

export function POIRecommendations({ scheduleData }: POIRecommendationsProps) {
  const [selectedFilter, setSelectedFilter] = useState<string>("all")
  const [recommendations, setRecommendations] = useState<POI[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadRecommendations = async () => {
      setIsLoading(true)
      console.log("[v0] Loading POI recommendations")

      try {
        const pois = await getPOIRecommendationsWithBackend(
          scheduleData.scheduleItems,
          scheduleData.startLocation,
          scheduleData.endLocation,
          true, // Use backend if available
        )

        console.log("[v0] POI recommendations loaded:", pois.length)
        setRecommendations(pois)
      } catch (error) {
        console.error("[v0] Failed to load POI recommendations:", error)
        // Fallback to empty array or show error message
        setRecommendations([])
      } finally {
        setIsLoading(false)
      }
    }

    loadRecommendations()
  }, [scheduleData])

  const filters = [
    { key: "all", label: "All" },
    { key: "onRoute", label: "On Route" },
    { key: "Restaurant", label: "Restaurants" },
    { key: "Temple", label: "Temples" },
    { key: "Shopping", label: "Shopping" },
    { key: "highRated", label: "4.5+ Rating" },
  ]

  const filteredRecommendations = recommendations.filter((poi) => {
    switch (selectedFilter) {
      case "onRoute":
        return poi.isOnRoute
      case "highRated":
        return poi.rating >= 4.5
      case "all":
        return true
      default:
        return poi.type === selectedFilter
    }
  })

  const handleAddToPlan = (poi: POI) => {
    // In a real app, this would add the POI to the current schedule
    alert(`Added "${poi.name}" to your plan!`)
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <MapPin className="h-5 w-5 text-primary" />
            Recommended Places
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground">Loading recommendations...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <MapPin className="h-5 w-5 text-primary" />
          Recommended Places
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Filters */}
        <div className="flex flex-wrap gap-2">
          {filters.map((filter) => (
            <Button
              key={filter.key}
              variant={selectedFilter === filter.key ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedFilter(filter.key)}
              className="text-xs"
            >
              {filter.key === "all" && <Filter className="h-3 w-3 mr-1" />}
              {filter.label}
            </Button>
          ))}
        </div>

        {/* Recommendations List */}
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {filteredRecommendations.map((poi) => (
            <div key={poi.id} className="border rounded-lg p-3 space-y-2">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-medium text-sm truncate">{poi.name}</h4>
                    {poi.isOnRoute && (
                      <Badge variant="secondary" className="text-xs">
                        On Route
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline" className="text-xs">
                      {poi.type}
                    </Badge>
                    <div className="flex items-center gap-1 text-xs">
                      <Star className="h-3 w-3 text-yellow-500 fill-current" />
                      <span>{poi.rating}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">{poi.priceRange}</span>
                  </div>
                </div>
                <Button size="sm" variant="outline" onClick={() => handleAddToPlan(poi)} className="flex-shrink-0 ml-2">
                  <Plus className="h-3 w-3 mr-1" />
                  Add
                </Button>
              </div>

              <p className="text-xs text-muted-foreground">{poi.description}</p>

              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  {poi.distance} km away
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {poi.estimatedTime} min detour
                </span>
              </div>
            </div>
          ))}
        </div>

        {filteredRecommendations.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            <MapPin className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No recommendations found for this filter.</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
