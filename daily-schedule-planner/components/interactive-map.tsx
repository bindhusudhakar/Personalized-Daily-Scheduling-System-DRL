"use client"

import { useEffect, useRef } from "react"
import L from "leaflet"
import "leaflet/dist/leaflet.css"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Navigation } from "lucide-react"

// Fix for default marker icons in Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
})

interface Leg {
  from: string
  to: string
  from_lat: number
  from_lon: number
  to_lat: number
  to_lon: number
  duration_sec: number
  distance_m: number
  dwell_mins: number
}

interface POISequence {
  name: string
  priority: number
  dwell_mins: number
  lat: number
  lon: number
}

interface InteractiveMapProps {
  legs: Leg[]
  sequence: POISequence[]
  startCoords: [number, number]
}

export function InteractiveMap({ legs, sequence, startCoords }: InteractiveMapProps) {
  const mapRef = useRef<L.Map | null>(null)
  const mapContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!mapContainerRef.current || !legs || legs.length === 0) return

    // Initialize map
    if (!mapRef.current) {
      mapRef.current = L.map(mapContainerRef.current).setView(startCoords, 12)

      // Add OpenStreetMap tiles
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(mapRef.current)
    }

    const map = mapRef.current

    // Clear existing layers (except tile layer)
    map.eachLayer((layer) => {
      if (layer instanceof L.Marker || layer instanceof L.Polyline) {
        map.removeLayer(layer)
      }
    })

    // Create custom icons for different priorities
    const createIcon = (number: number, color: string) => {
      return L.divIcon({
        html: `<div style="background-color: ${color}; width: 32px; height: 32px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">${number}</div>`,
        className: "",
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      })
    }

    const startIcon = createIcon(0, "#ea580c") // Orange for start
    const colors = ["#3b82f6", "#f97316", "#eab308", "#22c55e"] // Blue, Orange, Yellow, Green

    // Add start marker
    const startMarker = L.marker(startCoords, { icon: startIcon }).addTo(map)
    startMarker.bindPopup(`<b>Start Point</b>`)

    // Collect all coordinates for route
    const routeCoords: L.LatLngExpression[] = [startCoords]
    const bounds = L.latLngBounds([startCoords])

    // Add markers for each POI in sequence (matches the order in right panel)
    sequence.forEach((poi, index) => {
      const destCoords: [number, number] = [poi.lat, poi.lon]
      routeCoords.push(destCoords)
      bounds.extend(destCoords)

      // Add destination marker
      const color = colors[index % colors.length]
      const marker = L.marker(destCoords, {
        icon: createIcon(index + 1, color),
      }).addTo(map)

      const dwellText = poi.dwell_mins > 0 ? `<br><b>Dwell Time:</b> ${poi.dwell_mins} min` : ""
      const priorityText = `<br><b>Priority:</b> ${poi.priority}`
      marker.bindPopup(`
        <div style="font-family: system-ui;">
          <b>Stop ${index + 1}: ${poi.name}</b>${dwellText}${priorityText}
        </div>
      `)
    })

    // Add return to start if it's a round trip
    if (legs.length > 0 && legs[legs.length - 1].to.includes("Return")) {
      routeCoords.push(startCoords)
    }

    // Draw route polyline
    const polyline = L.polyline(routeCoords, {
      color: "#3b82f6",
      weight: 4,
      opacity: 0.7,
      dashArray: "10, 10",
    }).addTo(map)

    // Add arrows to show direction
    const arrowIcon = L.divIcon({
      html: '<div style="color: #3b82f6; font-size: 20px;">▶</div>',
      className: "",
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    })

    // Add direction arrows along the route
    for (let i = 0; i < routeCoords.length - 1; i++) {
      const start = routeCoords[i] as [number, number]
      const end = routeCoords[i + 1] as [number, number]
      const midLat = (start[0] + end[0]) / 2
      const midLng = (start[1] + end[1]) / 2

      const angle = Math.atan2(end[1] - start[1], end[0] - start[0]) * (180 / Math.PI)
      const arrowMarker = L.marker([midLat, midLng], {
        icon: L.divIcon({
          html: `<div style="transform: rotate(${angle}deg); color: #3b82f6; font-size: 16px;">➤</div>`,
          className: "",
          iconSize: [16, 16],
          iconAnchor: [8, 8],
        }),
      }).addTo(map)
    }

    // Fit map to show entire route
    map.fitBounds(bounds, { padding: [50, 50] })

    // Cleanup
    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
      }
    }
  }, [legs, sequence, startCoords])

  // Calculate total stats
  const totalDistance = legs.reduce((sum, leg) => sum + leg.distance_m, 0) / 1000
  const totalTime = legs.reduce((sum, leg) => sum + leg.duration_sec, 0) / 60
  const stops = legs.length - 1 // Exclude return leg

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <Navigation className="h-5 w-5 text-primary" />
          Interactive Route Map
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0 h-[calc(100%-80px)]">
        <div className="relative h-full">
          <div ref={mapContainerRef} className="w-full h-full rounded-b-lg" style={{ minHeight: "500px" }} />

          {/* Route Summary Overlay */}
          <div className="absolute top-4 left-4 bg-white rounded-lg shadow-md p-3 max-w-xs z-[1000]">
            <div className="text-sm font-medium mb-2">Route Summary</div>
            <div className="space-y-1 text-xs">
              <div>
                <b>Total Distance:</b> {totalDistance.toFixed(1)} km
              </div>
              <div>
                <b>Estimated Time:</b> {Math.round(totalTime)} min
              </div>
              <div>
                <b>Stops:</b> {stops}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
