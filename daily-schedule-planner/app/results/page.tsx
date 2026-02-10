"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, ArrowLeft, Download, MapPin, Clock, CheckCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface Leg {
  from: string
  to: string
  from_lat: number
  from_lon: number
  to_lat: number
  to_lon: number
  departure_time: string
  arrival_time: string
  duration_sec: number
  distance_m: number
  weather: {
    condition: string
    temp_c: number
  }
  mode: string
}

interface POISequence {
  name: string
  priority: number
  dwell_mins: number
}

interface PlanData {
  sequence: POISequence[]
  dropped?: POISequence[]
  total_seconds: number
  total_distance_m: number
  legs: Leg[]
}

interface ItineraryResponse {
  start_time: string
  end_time: string
  mode: string
  round_trip: boolean
  start_coords: [number, number]
  user_plan: PlanData
  optimized_plan: PlanData
}

interface ScheduleData {
  startLocation: string
  endLocation: string
  scheduleItems: any[]
  timestamp: number
  apiResponse: ItineraryResponse
}

export default function ResultsPage() {
  const [scheduleData, setScheduleData] = useState<ScheduleData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const data = localStorage.getItem("currentSchedule")
    if (data) {
      try {
        const parsed = JSON.parse(data)
        if (parsed.apiResponse) {
          setScheduleData(parsed)
        } else {
          router.push("/dashboard")
        }
      } catch (error) {
        console.error("Error parsing schedule data:", error)
        router.push("/dashboard")
      }
    } else {
      router.push("/dashboard")
    }
    setIsLoading(false)
  }, [router])

  const formatTime = (timeStr: string) => {
    return new Date(timeStr).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    })
  }

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  const formatDistance = (meters: number) => {
    const km = (meters / 1000).toFixed(1)
    return `${km} km`
  }

  const handleDownload = () => {
    if (!scheduleData) return

    const downloadData = {
      ...scheduleData,
      downloadedAt: new Date().toISOString(),
    }

    const blob = new Blob([JSON.stringify(downloadData, null, 2)], {
      type: "application/json",
    })

    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `optimized-route-${new Date().toISOString().split("T")[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleViewMap = () => {
    router.push("/route-map")
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading results...</p>
        </div>
      </div>
    )
  }

  if (!scheduleData || !scheduleData.apiResponse) {
    return null
  }

  const { apiResponse } = scheduleData
  const optimizedPlan = apiResponse.optimized_plan
  const userPlan = apiResponse.user_plan

  const timeSaved = userPlan.total_seconds - optimizedPlan.total_seconds
  const distanceSaved = userPlan.total_distance_m - optimizedPlan.total_distance_m
  const timeSavedPercent = ((timeSaved / userPlan.total_seconds) * 100).toFixed(1)
  const distanceSavedPercent = ((distanceSaved / userPlan.total_distance_m) * 100).toFixed(1)

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-card to-muted">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => router.push("/dashboard")}
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div>
                <h1 className="text-xl font-bold">Optimization Results</h1>
                <p className="text-sm text-muted-foreground">Your route has been optimized</p>
              </div>
            </div>

            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleDownload}>
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
              <Button size="sm" onClick={handleViewMap}>
                View Map
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Success Alert */}
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              Your route has been successfully optimized! Check the improvements below.
            </AlertDescription>
          </Alert>

          {/* Key Metrics */}
          <div className="grid md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Time Saved
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {formatDuration(timeSaved)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {timeSavedPercent}% reduction
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Distance Saved
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {formatDistance(distanceSaved)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {distanceSavedPercent}% reduction
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Duration
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatDuration(optimizedPlan.total_seconds)}
                </div>
                <p className="text-xs text-muted-foreground">Optimized route</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Distance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatDistance(optimizedPlan.total_distance_m)}
                </div>
                <p className="text-xs text-muted-foreground">Optimized route</p>
              </CardContent>
            </Card>
          </div>

          {/* Optimized Sequence */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                Optimized Route Sequence
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 bg-primary/10 border border-primary/20 rounded-lg">
                  <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                    S
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">{scheduleData.startLocation}</p>
                    <p className="text-sm text-muted-foreground">Start: {formatTime(apiResponse.start_time)}</p>
                  </div>
                </div>

                {optimizedPlan.sequence.map((poi, index) => (
                  <div key={index} className="flex items-center gap-3 p-3 border rounded-lg hover:bg-accent/50 transition-colors">
                    <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium truncate">{poi.name}</h4>
                        <Badge variant="outline" className="text-xs">
                          {poi.dwell_mins}min
                        </Badge>
                        <Badge
                          className="text-xs"
                          variant={
                            poi.priority >= 4
                              ? "default"
                              : poi.priority >= 3
                                ? "secondary"
                                : "outline"
                          }
                        >
                          Priority {poi.priority}
                        </Badge>
                      </div>
                      {optimizedPlan.legs[index] && (
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatDuration(optimizedPlan.legs[index].duration_sec)}
                          </span>
                          <span className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {formatDistance(optimizedPlan.legs[index].distance_m)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                <div className="flex items-center gap-3 p-3 bg-primary/10 border border-primary/20 rounded-lg">
                  <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                    E
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">{scheduleData.endLocation}</p>
                    <p className="text-sm text-muted-foreground">End: {formatTime(apiResponse.end_time)}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Dropped POIs */}
          {optimizedPlan.dropped && optimizedPlan.dropped.length > 0 && (
            <Card className="border-yellow-200 bg-yellow-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-yellow-900">
                  <AlertCircle className="h-5 w-5" />
                  Could Not Fit ({optimizedPlan.dropped.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-yellow-800 mb-4">
                  The following destinations couldn't fit in your available time. Consider extending your time window or adjusting priorities.
                </p>
                <div className="space-y-2">
                  {optimizedPlan.dropped.map((poi, index) => (
                    <div key={index} className="flex items-center gap-3 p-2 bg-white border border-yellow-200 rounded">
                      <MapPin className="h-4 w-4 text-yellow-600" />
                      <span className="flex-1">{poi.name}</span>
                      <Badge variant="outline" className="text-xs">
                        {poi.dwell_mins}min
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Action Buttons */}
          <div className="flex gap-4 justify-center">
            <Button variant="outline" size="lg" onClick={() => router.push("/dashboard")}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
            <Button size="lg" onClick={handleViewMap}>
              View on Map
            </Button>
          </div>
        </div>
      </main>
    </div>
  )
}
