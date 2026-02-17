import { useState, useEffect, useRef } from 'react'
import { Search, RefreshCw, Layers } from 'lucide-react'
import useMarketStore from '../store/marketStore'

const STYLE_COLORS = {
  minimal: 'bg-gray-100 text-gray-700',
  bold: 'bg-red-100 text-red-700',
  vintage: 'bg-amber-100 text-amber-700',
  modern: 'bg-blue-100 text-blue-700',
  unknown: 'bg-gray-50 text-gray-400',
}

export default function Bestsellers() {
  const {
    bestsellers,
    totalBestsellers,
    loading,
    errors,
    bestsellerKeywordInput,
    setBestsellerKeyword,
    runBestsellerAnalysis,
    fetchBestsellers,
  } = useMarketStore()

  const [styleFilter, setStyleFilter] = useState('')
  const [analyzedOnly, setAnalyzedOnly] = useState(false)
  const [pollingActive, setPollingActive] = useState(false)
  const pollingRef = useRef(null)

  useEffect(() => {
    fetchBestsellers({ style: styleFilter || undefined, analyzed_only: analyzedOnly })
  }, [styleFilter, analyzedOnly])

  // 이미지 분석 완료 폴링 (5초마다 최대 5분)
  useEffect(() => {
    if (!pollingActive) {
      if (pollingRef.current) clearInterval(pollingRef.current)
      return
    }

    pollingRef.current = setInterval(() => {
      fetchBestsellers({ style: styleFilter || undefined, analyzed_only: analyzedOnly })
    }, 5000)

    const timeout = setTimeout(() => {
      setPollingActive(false)
    }, 300000)

    return () => {
      clearInterval(pollingRef.current)
      clearTimeout(timeout)
    }
  }, [pollingActive, styleFilter, analyzedOnly])

  const handleAnalyze = async (e) => {
    e.preventDefault()
    if (!bestsellerKeywordInput.trim()) return
    try {
      await runBestsellerAnalysis(bestsellerKeywordInput.trim(), true)
      setPollingActive(true)
    } catch {
      // 에러는 store.errors에 반영됨
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold text-gray-900">Bestseller Analysis</h1>
        {pollingActive && (
          <div className="flex items-center gap-2 text-sm text-blue-600">
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span>Image analysis running...</span>
          </div>
        )}
      </div>
      <p className="text-gray-500 text-sm mb-6">
        Extract color palettes, styles, and keywords from top Etsy sellers.
      </p>

      {/* 분석 요청 폼 */}
      <form
        onSubmit={handleAnalyze}
        className="bg-white rounded-lg shadow-sm border p-6 mb-6"
      >
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Search Bestsellers by Keyword
        </label>
        <div className="flex gap-3">
          <input
            type="text"
            value={bestsellerKeywordInput}
            onChange={(e) => setBestsellerKeyword(e.target.value)}
            placeholder="e.g., digital planner, wall art, resume template..."
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            type="submit"
            disabled={loading.analyze || !bestsellerKeywordInput.trim()}
            className="flex items-center gap-2 bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading.analyze ? (
              <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            ) : (
              <Search className="w-4 h-4" />
            )}
            {loading.analyze ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
        {errors.analyze && (
          <p className="mt-2 text-sm text-red-600">{errors.analyze}</p>
        )}
        <p className="mt-2 text-xs text-gray-400">
          Fetches top 10 listings. Color palette extraction runs in background (~10-30 seconds per image).
        </p>
      </form>

      {/* 필터 바 */}
      <div className="flex items-center gap-4 mb-4">
        <select
          value={styleFilter}
          onChange={(e) => setStyleFilter(e.target.value)}
          className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Styles</option>
          {['minimal', 'bold', 'vintage', 'modern'].map((s) => (
            <option key={s} value={s} className="capitalize">
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={analyzedOnly}
            onChange={(e) => setAnalyzedOnly(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          Analyzed only
        </label>
        <span className="text-sm text-gray-400 ml-auto">
          {totalBestsellers.toLocaleString()} total
        </span>
      </div>

      {/* 베스트셀러 그리드 */}
      {loading.bestsellers ? (
        <div className="text-center py-12 text-gray-400">
          <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2" />
          Loading bestsellers...
        </div>
      ) : bestsellers.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <Layers className="w-12 h-12 mx-auto mb-3 opacity-20" />
          <p className="text-sm font-medium">No bestsellers yet</p>
          <p className="text-xs mt-1">
            Enter a keyword above and click Analyze to get started.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {bestsellers.map((t) => (
            <BestsellerCard key={t.id} template={t} />
          ))}
        </div>
      )}
    </div>
  )
}

// ── BestsellerCard 서브 컴포넌트 ──────────────────────

function BestsellerCard({ template }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border overflow-hidden hover:shadow-md transition-shadow">
      {/* 이미지 */}
      <div className="relative h-44 bg-gray-100">
        {template.image_url ? (
          <img
            src={template.image_url}
            alt={template.title}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300 text-sm">
            No Image
          </div>
        )}
        {template.style && (
          <span
            className={`absolute top-2 right-2 px-2 py-0.5 rounded text-xs font-medium capitalize ${
              STYLE_COLORS[template.style] || STYLE_COLORS.unknown
            }`}
          >
            {template.style}
          </span>
        )}
      </div>

      {/* 정보 */}
      <div className="p-4">
        <h3 className="font-medium text-gray-900 text-sm line-clamp-2 mb-1 leading-snug">
          {template.title}
        </h3>
        {template.seller_name && (
          <p className="text-xs text-gray-400 mb-2">{template.seller_name}</p>
        )}
        <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
          <span className="font-medium text-gray-700">${template.price?.toFixed(2)}</span>
          <span>{template.reviews_count?.toLocaleString()} ♥</span>
        </div>

        {/* 색상 팔레트 */}
        {template.color_palette?.length > 0 ? (
          <div>
            <p className="text-xs text-gray-400 mb-1.5">Color Palette</p>
            <div className="flex gap-1">
              {template.color_palette.slice(0, 5).map((c, i) => (
                <div
                  key={i}
                  className="w-7 h-7 rounded border border-gray-200 flex-shrink-0 shadow-sm"
                  style={{ backgroundColor: c.color }}
                  title={`${c.color} (${c.percentage}%)`}
                />
              ))}
              {template.color_palette.length > 5 && (
                <div className="w-7 h-7 rounded border border-gray-200 flex-shrink-0 flex items-center justify-center text-xs text-gray-400">
                  +{template.color_palette.length - 5}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-xs text-gray-400">
            <span className="inline-block w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
            Analyzing colors...
          </div>
        )}

        {/* 키워드 태그 */}
        {template.keywords?.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {template.keywords.slice(0, 4).map((kw, i) => (
              <span
                key={i}
                className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded"
              >
                {kw}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
