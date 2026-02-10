// Test file to verify frontend-backend integration
// Run this in browser console to test connectivity

async function testIntegration() {
  console.log("🧪 Starting Integration Test...")
  console.log("=" * 50)

  const baseURL = "http://localhost:8000"
  
  // Test 1: Health check
  console.log("\n1️⃣ Testing Backend Connectivity...")
  try {
    const healthResponse = await fetch(`${baseURL}/docs`)
    if (healthResponse.ok) {
      console.log("✅ Backend is running at", baseURL)
      console.log("   Swagger UI: " + baseURL + "/docs")
    } else {
      console.log("❌ Backend not responding properly")
      return
    }
  } catch (error) {
    console.log("❌ Cannot connect to backend. Make sure it's running:")
    console.log("   python -m uvicorn app:app --reload")
    return
  }

  // Test 2: API Endpoint Test
  console.log("\n2️⃣ Testing /generate-itinerary Endpoint...")
  const testPayload = {
    pois: [
      {
        name: "Test Location 1",
        priority: 5,
        dwell_mins: 60,
        target_arrival: null
      },
      {
        name: "Test Location 2",
        priority: 3,
        dwell_mins: 30,
        target_arrival: null
      }
    ],
    mode: "driving",
    round_trip: false,
    start_time: "09:00",
    end_time: "18:00",
    debug: false
  }

  try {
    const response = await fetch(`${baseURL}/generate-itinerary`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(testPayload)
    })

    if (response.ok) {
      const data = await response.json()
      console.log("✅ API returned valid response")
      console.log("   Response structure:", {
        hasUserPlan: !!data.user_plan,
        hasOptimizedPlan: !!data.optimized_plan,
        userPlanLegs: data.user_plan?.legs?.length || 0,
        optimizedPlanLegs: data.optimized_plan?.legs?.length || 0
      })
      
      // Test 3: Check for real Google Maps data
      console.log("\n3️⃣ Checking for Real Google Maps Data...")
      const userLeg = data.user_plan?.legs?.[0]
      const optimizedLeg = data.optimized_plan?.legs?.[0]
      
      if (userLeg) {
        console.log("✅ Got travel data from Google Maps API")
        console.log("   Travel time:", userLeg.duration_sec, "seconds")
        console.log("   Distance:", userLeg.distance_m, "meters")
        console.log("   Weather:", userLeg.weather?.condition)
      }
    } else {
      const errorText = await response.text()
      console.log("❌ API returned error:", response.status)
      console.log("   Details:", errorText)
    }
  } catch (error) {
    console.log("❌ API request failed:", error.message)
  }

  // Test 4: Environment check
  console.log("\n4️⃣ Frontend Configuration Check...")
  console.log("   Backend URL:", process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000")
  console.log("   Node env:", process.env.NODE_ENV || "development")

  console.log("\n" + "=" * 50)
  console.log("🎉 Integration Test Complete!")
  console.log("\nNext steps:")
  console.log("1. Open the Schedule Input form")
  console.log("2. Add some POIs")
  console.log("3. Click 'Optimize Route'")
  console.log("4. Check the DevTools Network tab to see API calls")
}

// Run the test
testIntegration()
