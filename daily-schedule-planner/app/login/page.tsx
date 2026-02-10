import { LoginForm } from "@/components/login-form"

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100 flex items-center justify-center p-4">
      <div className="text-center mb-8 absolute top-8 left-1/2 transform -translate-x-1/2 w-full">
        <div className="flex items-center justify-center gap-2 mb-2">
          <div className="bg-orange-600 text-white rounded-full p-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10.5 1.5H3.75A2.25 2.25 0 001.5 3.75v12.5A2.25 2.25 0 003.75 18.5h12.5a2.25 2.25 0 002.25-2.25V9.5" />
              <path d="M10 10l4-4m0 0l-4-4m4 4H6" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">ScheduleAI</h1>
        </div>
        <p className="text-gray-600">Optimize your daily schedule with AI-powered route recommendations</p>
      </div>

      <LoginForm />
    </div>
  )
}
