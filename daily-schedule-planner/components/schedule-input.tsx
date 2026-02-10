"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { MapPin, Clock, Plus, X, Calendar, Navigation } from "lucide-react"
import { useRouter } from "next/navigation"
import { apiClient } from "@/lib/api-client"

interface ScheduleItem {
  id: string
  name: string
  type: string
  priority: number
  dwellTime: number
  targetArrival?: string
  notes?: string
}

export function ScheduleInput() {
  const [startLocation, setStartLocation] = useState("")
  const [endLocation, setEndLocation] = useState("")
  const [startTime, setStartTime] = useState("09:00")
  const [endTime, setEndTime] = useState("22:00")
  const [scheduleItems, setScheduleItems] = useState<ScheduleItem[]>([])
  const [currentItem, setCurrentItem] = useState<Partial<ScheduleItem>>({
    name: "",
    type: "",
    priority: 3, // Changed default priority to 3 (middle of 1-5 scale)
    dwellTime: 30,
    targetArrival: "",
    notes: "",
  })
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const poiTypes = [
    "Restaurant",
    "Temple",
    "Shopping",
    "Hospital",
    "Bank",
    "Gas Station",
    "Pharmacy",
    "Gym",
    "Park",
    "Office",
    "School",
    "Other",
  ]

  const addScheduleItem = () => {
    if (!currentItem.name || !currentItem.type) return

    const newItem: ScheduleItem = {
      id: Date.now().toString(),
      name: currentItem.name,
      type: currentItem.type,
      priority: currentItem.priority || 3, // Changed default to 3
      dwellTime: currentItem.dwellTime || 30,
      targetArrival: currentItem.targetArrival,
      notes: currentItem.notes,
    }

    setScheduleItems([...scheduleItems, newItem])
    setCurrentItem({
      name: "",
      type: "",
      priority: 3, // Reset to 3
      dwellTime: 30,
      targetArrival: "",
      notes: "",
    })
  }

  const removeScheduleItem = (id: string) => {
    setScheduleItems(scheduleItems.filter((item) => item.id !== id))
  }

  const handleOptimizeRoute = async () => {
    if (!startLocation || !endLocation || scheduleItems.length === 0) {
      alert("Please fill in start location, end location, and add at least one destination.")
      return
    }

    setIsLoading(true)

    try {
      // Prepare the payload for the API
      const payload = {
        startLocation,
        endLocation,
        scheduleItems,
        startTime,
        endTime,
      }

      console.log("Sending payload to API:", payload)

      // Call the API to generate itinerary
      const response = await apiClient.generateItinerary(payload)

      console.log("API Response received:", response)

      // Store the response and schedule data for the map page
      const scheduleData = {
        startLocation,
        endLocation,
        scheduleItems,
        startTime,
        endTime,
        timestamp: Date.now(),
        apiResponse: response,
      }

      localStorage.setItem("currentSchedule", JSON.stringify(scheduleData))

      // Redirect to route map page
      router.push("/route-map")
    } catch (error) {
      console.error("Error optimizing route:", error)
      alert(`Error: ${error instanceof Error ? error.message : "Failed to optimize route. Please try again."}`)
    } finally {
      setIsLoading(false)
    }
  }

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

  return (
    <div className="space-y-6">
      {/* Route Endpoints */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Navigation className="h-5 w-5 text-primary" />
            Route Endpoints
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="start">Starting Location</Label>
              <div className="relative">
                <MapPin className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="start"
                  placeholder="e.g., Home, Office, College"
                  className="pl-10"
                  value={startLocation}
                  onChange={(e) => setStartLocation(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="end">Ending Location</Label>
              <div className="relative">
                <MapPin className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="end"
                  placeholder="e.g., Home, Office, Mall"
                  className="pl-10"
                  value={endLocation}
                  onChange={(e) => setEndLocation(e.target.value)}
                />
              </div>
            </div>
          </div>
          
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="startTime">Start Time</Label>
              <div className="relative">
                <Clock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="startTime"
                  type="time"
                  className="pl-10"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="endTime">End Time</Label>
              <div className="relative">
                <Clock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="endTime"
                  type="time"
                  className="pl-10"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Add New Destination */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5 text-primary" />
            Add Destination
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="place-name">Place Name</Label>
              <Input
                id="place-name"
                placeholder="e.g., City Mall, Local Temple"
                value={currentItem.name}
                onChange={(e) => setCurrentItem({ ...currentItem, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="place-type">Place Type</Label>
              <Select
                value={currentItem.type}
                onValueChange={(value) => setCurrentItem({ ...currentItem, type: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select place type" />
                </SelectTrigger>
                <SelectContent>
                  {poiTypes.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="target-time">Target Arrival Time (Optional)</Label>
              <div className="relative">
                <Clock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="target-time"
                  type="time"
                  className="pl-10"
                  value={currentItem.targetArrival}
                  onChange={(e) => setCurrentItem({ ...currentItem, targetArrival: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="dwell-time">Time to Spend (minutes)</Label>
              <Input
                id="dwell-time"
                type="number"
                min="5"
                max="480"
                value={currentItem.dwellTime}
                onChange={(e) => setCurrentItem({ ...currentItem, dwellTime: Number.parseInt(e.target.value) })}
              />
            </div>
          </div>

          <div className="space-y-3">
            <Label>Priority Level: {getPriorityLabel(currentItem.priority || 3)}</Label>
            <Slider
              value={[currentItem.priority || 3]}
              onValueChange={(value) => setCurrentItem({ ...currentItem, priority: value[0] })}
              max={5} // Changed max from 10 to 5
              min={1}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Optional (1)</span>
              <span>Low (2)</span>
              <span>Medium (3)</span>
              <span>High (4)</span>
              <span>Critical (5)</span>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Notes (Optional)</Label>
            <Textarea
              id="notes"
              placeholder="Any specific requirements or preferences..."
              className="resize-none"
              rows={2}
              value={currentItem.notes}
              onChange={(e) => setCurrentItem({ ...currentItem, notes: e.target.value })}
            />
          </div>

          <Button onClick={addScheduleItem} className="w-full" disabled={!currentItem.name || !currentItem.type}>
            <Plus className="h-4 w-4 mr-2" />
            Add to Schedule
          </Button>
        </CardContent>
      </Card>

      {/* Current Schedule */}
      {scheduleItems.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-primary" />
              Your Schedule ({scheduleItems.length} destinations)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {scheduleItems.map((item, index) => (
                <div key={item.id} className="flex items-center gap-3 p-3 border rounded-lg bg-card">
                  <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium truncate">{item.name}</h4>
                      <Badge variant="outline" className="text-xs">
                        {item.type}
                      </Badge>
                      <Badge className={`text-xs ${getPriorityColor(item.priority)}`}>
                        {getPriorityLabel(item.priority)}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {item.dwellTime}min
                      </span>
                      {item.targetArrival && <span>Target: {item.targetArrival}</span>}
                    </div>
                    {item.notes && <p className="text-xs text-muted-foreground mt-1 truncate">{item.notes}</p>}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeScheduleItem(item.id)}
                    className="flex-shrink-0 text-muted-foreground hover:text-destructive"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Optimize Button */}
      <div className="flex justify-center">
        <Button
          onClick={handleOptimizeRoute}
          size="lg"
          disabled={!startLocation || !endLocation || scheduleItems.length === 0 || isLoading}
          className="px-8"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-foreground mr-2"></div>
              Optimizing Route...
            </>
          ) : (
            <>
              <Navigation className="h-4 w-4 mr-2" />
              Optimize My Route
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
