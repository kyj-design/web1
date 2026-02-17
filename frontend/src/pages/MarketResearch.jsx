import { useState, useEffect } from 'react'
import { Search, Trash2, TrendingUp, ChevronDown, ChevronUp } from 'lucide-react'
import useMarketStore from '../store/marketStore'

// 경쟁도 레이블 색상
function CompetitionBadge({ score }) {
  const level = score < 0.4 ? 'Low' : score < 0.7 ? 'Medium' : 'High'
  const colors = {
    Low: 'bg-green-100 text-green-700',
    Medium: 'bg-yellow-100 text-yellow-700',
    High: 'bg-red-100 text-red-700',
  }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[level]}`}>
      {level}
    </span>
  )
}

export default function MarketResearch() {
  const {
    niches,
    totalNiches,
    loading,
    errors,
    researchKeywordInput,
    setResearchKeyword,
    runResearch,
    fetchNiches,
    deleteNiche,
  } = useMarketStore()

  const [lastResult, setLastResult] = useState(null)
  const [sortBy, setSortBy] = useState('trend_score')
  const [expandedNiche, setExpandedNiche] = useState(null)

  useEffect(() => {
    fetchNiches(sortBy)
  }, [sortBy])

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!researchKeywordInput.trim()) return
    try {
      const result = await runResearch(researchKeywordInput.trim())
      setLastResult(result)
    } catch {
      // 에러는 store.errors에 반영됨
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Market Research</h1>
      <p className="text-gray-500 text-sm mb-6">
        Discover profitable niches by analyzing Etsy search data.
      </p>

      {/* 검색 폼 */}
      <form
        onSubmit={handleSearch}
        className="bg-white rounded-lg shadow-sm border p-6 mb-6"
      >
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Keyword to Research
        </label>
        <div className="flex gap-3">
          <input
            type="text"
            value={researchKeywordInput}
            onChange={(e) => setResearchKeyword(e.target.value)}
            placeholder="e.g., digital planner, resume template, wall art..."
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <button
            type="submit"
            disabled={loading.research || !researchKeywordInput.trim()}
            className="flex items-center gap-2 bg-purple-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading.research ? (
              <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            ) : (
              <Search className="w-4 h-4" />
            )}
            {loading.research ? 'Researching...' : 'Research'}
          </button>
        </div>
        {errors.research && (
          <p className="mt-2 text-sm text-red-600">{errors.research}</p>
        )}
        <p className="mt-2 text-xs text-gray-400">
          Fetches top 25 Etsy listings and analyzes pricing, competition, and trends.
          {' '}Results are saved automatically.
        </p>
      </form>

      {/* 직전 조사 결과 요약 */}
      {lastResult && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-purple-600" />
            <h3 className="font-semibold text-purple-800">
              Research complete: &ldquo;{lastResult.niche?.name}&rdquo;
            </h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div>
              <span className="text-gray-500 text-xs">Avg Price</span>
              <div className="font-semibold text-gray-900">
                ${lastResult.analysis?.avg_price?.toFixed(2)}
              </div>
            </div>
            <div>
              <span className="text-gray-500 text-xs">Competition</span>
              <div className="font-semibold text-gray-900 capitalize">
                {lastResult.analysis?.competition_level}
              </div>
            </div>
            <div>
              <span className="text-gray-500 text-xs">Trend Score</span>
              <div className="font-semibold text-gray-900">
                {lastResult.analysis?.trend_score}/100
              </div>
            </div>
            <div>
              <span className="text-gray-500 text-xs">Keywords Found</span>
              <div className="font-semibold text-gray-900">
                {lastResult.keywords?.length ?? 0}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Niche 목록 테이블 */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="font-semibold text-gray-900">
            Discovered Niches
            <span className="ml-2 text-sm text-gray-400 font-normal">
              ({totalNiches})
            </span>
          </h2>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="trend_score">Trend Score</option>
              <option value="profit_potential_score">Profit Score</option>
              <option value="avg_price">Avg Price</option>
              <option value="search_volume">Search Volume</option>
            </select>
          </div>
        </div>

        {loading.niches ? (
          <div className="p-8 text-center text-gray-400">
            <div className="animate-spin w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
            Loading niches...
          </div>
        ) : niches.length === 0 ? (
          <div className="p-12 text-center text-gray-400">
            <Search className="w-12 h-12 mx-auto mb-3 opacity-20" />
            <p className="text-sm font-medium">No niches discovered yet</p>
            <p className="text-xs mt-1">
              Enter a keyword above and click Research to get started.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {[
                    'Niche',
                    'Category',
                    'Avg Price',
                    'Competition',
                    'Trend Score',
                    'Profit Score',
                    '',
                  ].map((h) => (
                    <th
                      key={h}
                      className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {niches.map((niche) => (
                  <>
                    <tr
                      key={niche.id}
                      className="hover:bg-gray-50 transition-colors cursor-pointer"
                      onClick={() =>
                        setExpandedNiche(
                          expandedNiche === niche.id ? null : niche.id
                        )
                      }
                    >
                      <td className="px-4 py-3 font-medium text-gray-900">
                        <div className="flex items-center gap-2">
                          {expandedNiche === niche.id ? (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                          )}
                          {niche.name}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs">
                        {niche.category}
                      </td>
                      <td className="px-4 py-3 text-gray-800">
                        ${niche.avg_price?.toFixed(2)}
                      </td>
                      <td className="px-4 py-3">
                        <CompetitionBadge score={niche.competition_score} />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-20 bg-gray-200 rounded-full h-1.5">
                            <div
                              className="bg-purple-600 h-1.5 rounded-full"
                              style={{ width: `${niche.trend_score}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500">
                            {niche.trend_score?.toFixed(0)}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-semibold text-purple-600">
                          {niche.profit_potential_score?.toFixed(1)}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteNiche(niche.id)
                          }}
                          className="p-1 text-gray-300 hover:text-red-500 transition-colors"
                          title="Delete niche"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                    {/* 상세 정보 (클릭 시 펼침) */}
                    {expandedNiche === niche.id && (
                      <tr key={`${niche.id}-detail`}>
                        <td colSpan={7} className="px-6 py-3 bg-purple-50">
                          <div className="text-xs text-gray-600">
                            <span className="font-medium">Search Volume (est.):</span>{' '}
                            {niche.search_volume?.toLocaleString()}
                            {niche.discovered_at && (
                              <>
                                {' · '}
                                <span className="font-medium">Discovered:</span>{' '}
                                {new Date(niche.discovered_at).toLocaleDateString()}
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
