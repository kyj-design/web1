import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { Search, TrendingUp, Layers, Image, ArrowRight, FileText } from 'lucide-react'
import useMarketStore from '../store/marketStore'
import axios from 'axios'
import { useState } from 'react'

export default function Dashboard() {
  const { stats, loading, fetchStats } = useMarketStore()
  const [templateStats, setTemplateStats] = useState(null)

  useEffect(() => {
    fetchStats()
    axios.get('/api/templates/stats')
      .then((r) => setTemplateStats(r.data))
      .catch(() => {})
  }, [])

  if (loading.stats && !stats) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-purple-600 border-t-transparent rounded-full mx-auto mb-3" />
          <p className="text-sm">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  const marketStats = stats?.market
  const bestsellerStats = stats?.bestsellers
  const topNiches = marketStats?.top_niches ?? []

  // Recharts 데이터 (이름이 길면 잘라냄)
  const chartData = topNiches.map((n) => ({
    name: n.name.length > 15 ? n.name.slice(0, 13) + '…' : n.name,
    score: n.profit_potential_score ?? 0,
  }))

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Dashboard</h1>
      <p className="text-gray-500 text-sm mb-6">
        Canva-Etsy Automation · Phase 2: Market Research & Bestseller Analysis
      </p>

      {/* 요약 카드 */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        <StatCard
          label="Total Niches"
          value={marketStats?.total_niches ?? 0}
          icon={Search}
          color="purple"
        />
        <StatCard
          label="Total Keywords"
          value={marketStats?.total_keywords ?? 0}
          icon={TrendingUp}
          color="blue"
        />
        <StatCard
          label="Bestsellers"
          value={bestsellerStats?.total ?? 0}
          icon={Layers}
          color="green"
        />
        <StatCard
          label="Analyzed"
          value={bestsellerStats?.analyzed ?? 0}
          icon={Image}
          color="orange"
        />
        <StatCard
          label="Templates"
          value={templateStats?.total_templates ?? 0}
          icon={FileText}
          color="purple"
        />
        <StatCard
          label="PDFs Generated"
          value={templateStats?.total_pdfs ?? 0}
          icon={FileText}
          color="blue"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Top Niches 차트 */}
        {chartData.length > 0 ? (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-4">
              Top Niches by Profit Potential
            </h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData} margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(v) => [v.toFixed(1), 'Profit Score']}
                  contentStyle={{ fontSize: 12 }}
                />
                <Bar dataKey="score" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border p-6 flex items-center justify-center">
            <div className="text-center text-gray-400">
              <Search className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No niches yet</p>
              <p className="text-xs mt-1">Run market research to see charts</p>
            </div>
          </div>
        )}

        {/* 스타일 분포 */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">
            Bestseller Style Distribution
          </h2>
          {bestsellerStats && Object.keys(bestsellerStats.style_distribution ?? {}).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(bestsellerStats.style_distribution).map(([style, count]) => {
                const total = bestsellerStats.analyzed || 1
                const pct = Math.round((count / total) * 100)
                const styleColors = {
                  minimal: 'bg-gray-400',
                  bold: 'bg-red-500',
                  vintage: 'bg-amber-500',
                  modern: 'bg-blue-500',
                }
                return (
                  <div key={style}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="capitalize font-medium text-gray-700">{style}</span>
                      <span className="text-gray-500">{count} ({pct}%)</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${styleColors[style] || 'bg-purple-500'}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="text-center text-gray-400 py-8">
              <Layers className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No analyzed bestsellers yet</p>
              <p className="text-xs mt-1">Run bestseller analysis to see styles</p>
            </div>
          )}
        </div>
      </div>

      {/* 빠른 액션 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <QuickActionCard
          to="/market"
          title="Run Market Research"
          description="Discover profitable niches with keyword analysis using Etsy search data."
          cta="Start Research"
          color="purple"
          icon={Search}
        />
        <QuickActionCard
          to="/bestsellers"
          title="Analyze Bestsellers"
          description="Extract color palettes and style tags from top-selling Etsy templates."
          cta="Analyze Now"
          color="blue"
          icon={TrendingUp}
        />
        <QuickActionCard
          to="/templates"
          title="Manage Templates"
          description="Register Canva template links and generate delivery PDFs for buyers."
          cta="Go to Templates"
          color="green"
          icon={FileText}
        />
      </div>
    </div>
  )
}

// ── 서브 컴포넌트 ──────────────────────────────────

function StatCard({ label, value, icon: Icon, color }) {
  const colorMap = {
    purple: 'bg-purple-50 text-purple-600',
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    orange: 'bg-orange-50 text-orange-600',
  }
  return (
    <div className="bg-white rounded-lg shadow-sm border p-5">
      <div className={`inline-flex p-2 rounded-lg mb-3 ${colorMap[color]}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="text-2xl font-bold text-gray-900">
        {(value ?? 0).toLocaleString()}
      </div>
      <div className="text-sm text-gray-500 mt-1">{label}</div>
    </div>
  )
}

function QuickActionCard({ to, title, description, cta, color, icon: Icon }) {
  const btnColors = {
    purple: 'bg-purple-600 hover:bg-purple-700',
    blue: 'bg-blue-600 hover:bg-blue-700',
    green: 'bg-green-600 hover:bg-green-700',
  }
  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 flex flex-col">
      <h3 className="text-base font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-500 text-sm flex-1 mb-4">{description}</p>
      <Link
        to={to}
        className={`inline-flex items-center justify-center gap-2 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors ${btnColors[color]}`}
      >
        {cta}
        <ArrowRight className="w-4 h-4" />
      </Link>
    </div>
  )
}
