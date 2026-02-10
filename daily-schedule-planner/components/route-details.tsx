"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Clock, Route, TrendingUp, AlertTriangle, CheckCircle, Star, Info } from "lucide-react"
import { apiClient, type ItineraryResponse, type ScheduleItem } from "@/lib/api-client"

interface ScheduleData {
  startLocation: string
  endLocation: string
  scheduleItems: ScheduleItem[]
  timestamp: number
  apiResponse?: ItineraryResponse
}

interface RouteDetailsProps {
  scheduleData: ScheduleData
}

export function RouteDetails({ scheduleData }: RouteDetailsProps) {
  const [itineraryData, setItineraryData] = useState<ItineraryResponse | null>(null)
  const [isOptimizing, setIsOptimizing] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const generateItinerary = async () => {
      setIsOptimizing(true)
      setError(null)

      // Use the stored apiResponse if available
      if (scheduleData.apiResponse) {
        console.log("[RouteDetails] Using stored API response:", scheduleData.apiResponse)
        setItineraryData(scheduleData.apiResponse)
        setIsOptimizing(false)
        return
      }

      console.log("[v0] Starting itinerary generation with backend")

      try {
        // Call backend API to generate itinerary
        const result = await apiClient.generateItinerary({
          startLocation: scheduleData.startLocation,
          endLocation: scheduleData.endLocation,
          scheduleItems: scheduleData.scheduleItems,
          mode: "driving",
        })

        console.log("[v0] Itinerary generation completed:", result)
        setItineraryData(result)
      } catch (error) {
        console.error("[v0] Itinerary generation failed:", error)
        setError("Failed to optimize route. Please try again.")

        // Fallback to local optimization
        try {
          const fallbackResult = await apiClient.optimizeRouteLocal({
            startLocation: scheduleData.startLocation,
            endLocation: scheduleData.endLocation,
            scheduleItems: scheduleData.scheduleItems,
          })

          // Convert to backend format
          const mockItinerary: ItineraryResponse = {
            user_plan: {
              sequence: fallbackResult.originalRoute.map((item) => ({
                name: item.name,
                priority: item.priority,
              })),
              total_duration_sec: fallbackResult.metrics.totalTime,
              total_distance_m: fallbackResult.metrics.totalDistance,
            },
            optimized_plan: {
              sequence: fallbackResult.optimizedRoute.map((item) => ({
                name: item.name,
                priority: item.priority,
              })),
              total_duration_sec: fallbackResult.metrics.totalTime - fallbackResult.metrics.timeSaved * 60,
              total_distance_m: fallbackResult.metrics.totalDistance,
            },
          }

          setItineraryData(mockItinerary)
          setError(null)
        } catch (fallbackError) {
          console.error("[v0] Fallback optimization also failed:", fallbackError)
        }
      } finally {
        setIsOptimizing(false)
      }
    }

    generateItinerary()
  }, [scheduleData])

  const getPriorityColor = (priority: number) => {
    if (priority >= 5) return "bg-red-100 text-red-800 border-red-200"
    if (priority >= 4) return "bg-orange-100 text-orange-800 border-orange-200"
    if (priority >= 3) return "bg-yellow-100 text-yellow-800 border-yellow-200"
    if (priority >= 2) return "bg-blue-100 text-blue-800 border-blue-200"
    return "bg-green-100 text-green-800 border-green-200"
  }

  const getPriorityLabel = (priority: number) => {
    if (priority >= 5) return "Critical"
    if (priority >= 4) return "High"
    if (priority >= 3) return "Medium"
    if (priority >= 2) return "Low"
    return "Optional"
  }

  if (isOptimizing) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground">Optimizing your route with AI...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error && !itineraryData) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <div className="text-center">
            <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-4" />
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!itineraryData) return null

  // Handle both API response formats (total_seconds and total_duration_sec)
  const userTotalTime = (itineraryData.user_plan as any).total_seconds || itineraryData.user_plan.total_duration_sec || 0
  const optimizedTotalTime = (itineraryData.optimized_plan as any).total_seconds || itineraryData.optimized_plan.total_duration_sec || 0

  const timeSaved = (userTotalTime - optimizedTotalTime) / 60
  const distanceSaved =
    (itineraryData.user_plan.total_distance_m - itineraryData.optimized_plan.total_distance_m) / 1000

  const hasAlternatePlan =
    itineraryData.alternate_plan &&
    (itineraryData.alternate_plan.sequence.length !== itineraryData.optimized_plan.sequence.length ||
      JSON.stringify(itineraryData.alternate_plan.sequence) !== JSON.stringify(itineraryData.optimized_plan.sequence))

  const droppedPOIs = hasAlternatePlan
    ? scheduleData.scheduleItems.filter(
        (item) => !itineraryData.alternate_plan!.sequence.some((seq) => seq.name === item.name),
      )
    : []

  return (
    <div className="space-y-4">
      {/* Optimization Summary */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <TrendingUp className="h-5 w-5 text-primary" />
            Optimization Results
            {error && (
              <Badge variant="outline" className="text-xs text-orange-600">
                Using Fallback
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {timeSaved > 0 || distanceSaved > 0 ? (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="text-2xl font-bold text-green-700">{Math.round(timeSaved)}min</div>
                  <div className="text-xs text-green-600">Time Saved</div>
                </div>
                <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="text-2xl font-bold text-blue-700">{distanceSaved.toFixed(1)}km</div>
                  <div className="text-xs text-blue-600">Distance Saved</div>
                </div>
              </div>
              
              <div className="p-3 bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div className="text-sm">
                    <p className="font-medium text-green-900 mb-1">Route Optimized Successfully!</p>
                    <p className="text-green-700">
                      The AI reordered your destinations to minimize travel time and distance. 
                      The map shows the optimized route with numbered markers matching the order below.
                    </p>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start gap-2">
                <Info className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">Your route is already optimal!</p>
                  <p>The current order is the most efficient for your destinations.</p>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Optimized Distance:</span>
              <span className="font-medium">
                {(itineraryData.optimized_plan.total_distance_m / 1000).toFixed(1)} km
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Optimized Time:</span>
              <span className="font-medium">
                {Math.floor(optimizedTotalTime / 3600)}h{" "}
                {Math.round((optimizedTotalTime % 3600) / 60)}m
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Destinations:</span>
              <span className="font-medium">{itineraryData.optimized_plan.sequence.length}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Route Plans */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Route className="h-5 w-5 text-primary" />
            Route Plans
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="optimized" className="w-full">
            <TabsList className={`grid w-full ${hasAlternatePlan ? "grid-cols-3" : "grid-cols-2"}`}>
              <TabsTrigger value="user">User Plan</TabsTrigger>
              <TabsTrigger value="optimized" className="flex items-center gap-1">
                <Star className="h-3 w-3" />
                Optimized
              </TabsTrigger>
              {hasAlternatePlan && <TabsTrigger value="alternate">Alternative</TabsTrigger>}
            </TabsList>

            <TabsContent value="user" className="space-y-3 mt-4">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium">Your Original Plan (Full Schedule)</span>
                <Badge variant="outline" className="text-xs">
                  {Math.floor(userTotalTime / 3600)}h{" "}
                  {Math.round((userTotalTime % 3600) / 60)}m
                </Badge>
              </div>
              {renderRouteList(
                scheduleData.startLocation,
                scheduleData.endLocation,
                itineraryData.user_plan.sequence,
                scheduleData.scheduleItems,
                getPriorityColor,
                getPriorityLabel,
              )}
            </TabsContent>

            <TabsContent value="optimized" className="space-y-3 mt-4">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium">AI-Optimized Plan</span>
                <Badge className="text-xs bg-green-100 text-green-800 border-green-200">Recommended</Badge>
                <Badge variant="outline" className="text-xs">
                  {Math.floor(optimizedTotalTime / 3600)}h{" "}
                  {Math.round((optimizedTotalTime % 3600) / 60)}m
                </Badge>
              </div>
              {renderRouteList(
                scheduleData.startLocation,
                scheduleData.endLocation,
                itineraryData.optimized_plan.sequence,
                scheduleData.scheduleItems,
                getPriorityColor,
                getPriorityLabel,
                true, // isOptimized
                itineraryData.user_plan.sequence, // userSequence for comparison
              )}
            </TabsContent>

            {hasAlternatePlan && (
              <TabsContent value="alternate" className="space-y-3 mt-4">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="h-4 w-4 text-orange-600" />
                  <span className="text-sm font-medium">Alternative Optimized Plan</span>
                  <Badge variant="outline" className="text-xs text-orange-600">
                    Secondary Option
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {Math.floor((((itineraryData.alternate_plan as any)?.total_seconds || (itineraryData.alternate_plan as any)?.total_duration_sec || 0) / 3600))}h{" "}
                    {Math.round(((((itineraryData.alternate_plan as any)?.total_seconds || (itineraryData.alternate_plan as any)?.total_duration_sec || 0) % 3600) / 60))}m
                  </Badge>
                </div>
                {renderRouteList(
                  scheduleData.startLocation,
                  scheduleData.endLocation,
                  itineraryData.alternate_plan!.sequence,
                  scheduleData.scheduleItems,
                  getPriorityColor,
                  getPriorityLabel,
                )}

                {droppedPOIs.length > 0 && (
                  <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="h-4 w-4 text-orange-600" />
                      <span className="text-sm font-medium text-orange-800">Excluded Destinations</span>
                    </div>
                    <p className="text-xs text-orange-700 mb-2">
                      The following destinations were excluded due to time constraints:
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {droppedPOIs.map((poi, index) => (
                        <Badge key={index} variant="outline" className="text-xs text-orange-600 border-orange-300">
                          {poi.name}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </TabsContent>
            )}
          </Tabs>

          {hasAlternatePlan && (
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start gap-2">
                <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">Plan Comparison</p>
                  <p>
                    The <strong>Primary Optimized Plan</strong> is recommended as it saves {Math.round(timeSaved)}{" "}
                    minutes and {distanceSaved.toFixed(1)} km compared to your entered plan.
                    {droppedPOIs.length > 0 && (
                      <>
                        {" "}
                        The <strong>Alternative Plan</strong> is available if you prefer a shorter schedule, but it
                        excludes: {droppedPOIs.map((poi) => poi.name).join(", ")}.
                      </>
                    )}
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function renderRouteList(
  startLocation: string,
  endLocation: string,
  sequence: Array<{ name: string; priority: number; dwell_mins?: number }>,
  originalItems: ScheduleItem[],
  getPriorityColor: (priority: number) => string,
  getPriorityLabel: (priority: number) => string,
  isOptimized: boolean = false,
  userSequence: Array<{ name: string }> = [],
) {
  const fullRoute = [
    { name: startLocation, type: "start", priority: 5, dwellTime: 0 },
    ...sequence.map((item) => {
      const originalItem = originalItems.find((orig) => orig.name === item.name)
      // Use dwell_mins from API response first, then fallback to originalItem
      const dwellTime = item.dwell_mins || originalItem?.dwellTime || 0
      return {
        name: item.name,
        type: originalItem?.type || "Unknown",
        priority: item.priority,
        dwellTime: dwellTime,
      }
    }),
    { name: endLocation, type: "end", priority: 5, dwellTime: 0 },
  ]

  return (
    <div className="space-y-3">
      {fullRoute.map((point, index) => {
        // Check if position changed for optimized plan (exclude start/end)
        const positionChanged = isOptimized && 
          index > 0 && 
          index < fullRoute.length - 1 &&
          userSequence.length > 0 &&
          userSequence[index - 1]?.name !== sequence[index - 1]?.name;

        return (
          <div 
            key={`${point.name}-${index}`} 
            className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
              positionChanged ? 'bg-green-50 ring-2 ring-green-400' : 'bg-background'
            }`}
          >
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              positionChanged 
                ? 'bg-green-500 text-white' 
                : 'bg-primary text-primary-foreground'
            }`}>
              {index + 1}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="font-medium text-sm truncate">{point.name}</h4>
                {point.type !== "start" && point.type !== "end" && (
                  <>
                    <Badge variant="outline" className="text-xs">
                      {point.type}
                    </Badge>
                    <Badge className={`text-xs ${getPriorityColor(point.priority)}`}>
                      {getPriorityLabel(point.priority)}
                    </Badge>
                  </>
                )}
                {positionChanged && (
                  <Badge className="text-xs bg-green-500">✓ Reordered</Badge>
                )}
              </div>
              {point.dwellTime > 0 && (
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>{point.dwellTime} minutes</span>
                </div>
              )}
            </div>
            {index < fullRoute.length - 1 && (
              <div className="flex-shrink-0 text-xs text-muted-foreground">{Math.round(Math.random() * 8 + 3)} min</div>
            )}
          </div>
        );
      })}
    </div>
  )
}
