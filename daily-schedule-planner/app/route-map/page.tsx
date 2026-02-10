"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { InteractiveMap } from "@/components/interactive-map"
import { RouteDetails } from "@/components/route-details"
import { POIRecommendations } from "@/components/poi-recommendations"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Download, Share2 } from "lucide-react"

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
  apiResponse?: any
}

export default function RouteMapPage() {
  const [scheduleData, setScheduleData] = useState<ScheduleData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const data = localStorage.getItem("currentSchedule")
    if (data) {
      setScheduleData(JSON.parse(data))
    } else {
      router.push("/dashboard")
    }
    setIsLoading(false)
  }, [router])

  const handleBack = () => {
    router.push("/dashboard")
  }

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: "My Optimized Route - ScheduleAI",
        text: "Check out my optimized daily route!",
        url: window.location.href,
      })
    } else {
      navigator.clipboard.writeText(window.location.href)
      alert("Route link copied to clipboard!")
    }
  }

  const handleDownload = () => {
    if (!scheduleData) return

    const routeData = {
      ...scheduleData,
      generatedAt: new Date().toISOString(),
    }

    const blob = new Blob([JSON.stringify(routeData, null, 2)], {
      type: "application/json",
    })

    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `route-${new Date().toISOString().split("T")[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading your optimized route...</p>
        </div>
      </div>
    )
  }

  if (!scheduleData) {
    return null
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={handleBack}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Dashboard
              </Button>
              <div>
                <h1 className="text-xl font-bold">Optimized Route</h1>
                <p className="text-sm text-muted-foreground">
                  {scheduleData.startLocation} → {scheduleData.endLocation}
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        <div className="grid lg:grid-cols-3 gap-6 h-[calc(100vh-140px)]">
          {/* Map Section */}
          <div className="lg:col-span-2">
            {scheduleData.apiResponse?.optimized_plan?.legs && scheduleData.apiResponse?.optimized_plan?.sequence ? (
              <InteractiveMap
                legs={scheduleData.apiResponse.optimized_plan.legs}
                sequence={scheduleData.apiResponse.optimized_plan.sequence}
                startCoords={scheduleData.apiResponse.start_coords || [12.9716, 77.5946]}
              />
            ) : (
              <div className="h-full flex items-center justify-center bg-muted rounded-lg">
                <p className="text-muted-foreground">Loading map...</p>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6 overflow-y-auto">
            <RouteDetails scheduleData={scheduleData} />
          </div>
        </div>
      </div>
    </div>
  )
}
