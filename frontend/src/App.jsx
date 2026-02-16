import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [healthStatus, setHealthStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check backend health
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        setHealthStatus(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to fetch health status:', err)
        setLoading(false)
      })
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🎨 Canva-Etsy Automation
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Automate your Canva template listing to Etsy with AI-powered SEO
          </p>

          {loading && (
            <div className="text-gray-500">Loading...</div>
          )}

          {!loading && healthStatus && (
            <div className="bg-white rounded-lg shadow-md p-6 max-w-md mx-auto">
              <h2 className="text-2xl font-semibold mb-4 text-green-600">
                ✅ System Status
              </h2>
              <div className="space-y-2 text-left">
                <div className="flex justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span className="font-medium">{healthStatus.status}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Database:</span>
                  <span className="font-medium">{healthStatus.database}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">LLM Provider:</span>
                  <span className="font-medium">{healthStatus.llm_provider}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Etsy API:</span>
                  <span className="font-medium">{healthStatus.etsy_api}</span>
                </div>
              </div>
            </div>
          )}

          {!loading && !healthStatus && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 max-w-md mx-auto">
              <p className="text-red-600">
                ❌ Cannot connect to backend. Please check your server.
              </p>
            </div>
          )}

          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <FeatureCard
              icon="📊"
              title="Market Research"
              description="Discover profitable niches and analyze Etsy trends automatically"
            />
            <FeatureCard
              icon="🎨"
              title="Template Management"
              description="Manage your Canva templates and generate delivery PDFs"
            />
            <FeatureCard
              icon="🚀"
              title="Auto Upload"
              description="AI-powered SEO optimization and automatic Etsy listing creation"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="text-xl font-semibold mb-2 text-gray-900">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}

export default App
