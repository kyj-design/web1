import { useState, useEffect } from 'react'
import {
  Sparkles,
  Plus,
  ExternalLink,
  Trash2,
  Upload,
  X,
  ChevronDown,
  ChevronUp,
  Tag,
  DollarSign,
  FileText,
  CheckCircle,
  Clock,
} from 'lucide-react'
import useListingStore from '../store/listingStore'
import useTemplateStore from '../store/templateStore'

const STATUS_COLORS = {
  draft: 'bg-yellow-100 text-yellow-700',
  published: 'bg-green-100 text-green-700',
  deactivated: 'bg-gray-100 text-gray-500',
}

// ── 메인 페이지 ──────────────────────────────────────

export default function Listings() {
  const {
    listings,
    totalListings,
    stats,
    loading,
    errors,
    fetchListings,
    fetchStats,
    deleteListing,
    publishListing,
  } = useListingStore()
  const { templates, fetchTemplates } = useTemplateStore()

  const [showCreateFlow, setShowCreateFlow] = useState(false)
  const [statusFilter, setStatusFilter] = useState('')
  const [publishResult, setPublishResult] = useState(null)

  useEffect(() => {
    fetchListings({ status: statusFilter || undefined })
    fetchStats()
    fetchTemplates()
  }, [statusFilter])

  const handlePublish = async (listing) => {
    setPublishResult(null)
    try {
      const result = await publishListing(listing.id)
      setPublishResult(result)
    } catch {
      /* error is in store */
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold text-gray-900">Etsy Listings</h1>
        <button
          onClick={() => setShowCreateFlow(true)}
          className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Listing
        </button>
      </div>
      <p className="text-gray-500 text-sm mb-6">
        Generate SEO content with AI and publish digital product listings to Etsy.
      </p>

      {/* 통계 카드 */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <MiniStat label="Total" value={stats.total_listings} color="gray" />
          <MiniStat label="Published" value={stats.published} color="green" />
          <MiniStat label="Draft" value={stats.draft} color="yellow" />
          <MiniStat label="Avg. Price" value={`$${stats.avg_price}`} color="purple" />
        </div>
      )}

      {/* 발행 성공 알림 */}
      {publishResult && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-green-800">
                Published to Etsy
                {publishResult.is_mock && (
                  <span className="ml-2 text-xs bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded">
                    Mock Mode
                  </span>
                )}
              </p>
              {publishResult.listing?.etsy_listing_id && (
                <p className="text-xs text-green-600 mt-0.5">
                  Etsy ID: {publishResult.listing.etsy_listing_id}
                </p>
              )}
            </div>
          </div>
          <button onClick={() => setPublishResult(null)} className="text-green-500 hover:text-green-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {errors.publish && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-600">
          {errors.publish}
        </div>
      )}

      {/* 필터 */}
      <div className="flex gap-2 mb-4">
        {['', 'draft', 'published', 'deactivated'].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              statusFilter === s
                ? 'bg-purple-600 text-white border-purple-600'
                : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
            }`}
          >
            {s === '' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* 목록 */}
      {loading.listings ? (
        <div className="text-center py-12 text-gray-400">
          <div className="animate-spin w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
          Loading listings...
        </div>
      ) : listings.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <FileText className="w-12 h-12 mx-auto mb-3 opacity-20" />
          <p className="font-medium text-gray-500">No listings yet</p>
          <p className="text-sm mt-1 mb-4">
            Generate SEO content from a template and create your first listing.
          </p>
          <button
            onClick={() => setShowCreateFlow(true)}
            className="inline-flex items-center gap-2 bg-purple-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Listing
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {listings.map((l) => (
            <ListingRow
              key={l.id}
              listing={l}
              onDelete={() => deleteListing(l.id)}
              onPublish={() => handlePublish(l)}
              isPublishing={loading.publish}
            />
          ))}
        </div>
      )}

      {/* 신규 리스팅 생성 흐름 (모달) */}
      {showCreateFlow && (
        <CreateListingFlow
          templates={templates}
          onClose={() => setShowCreateFlow(false)}
          onCreated={() => {
            setShowCreateFlow(false)
            fetchListings({ status: statusFilter || undefined })
            fetchStats()
          }}
        />
      )}
    </div>
  )
}

// ── 미니 통계 카드 ────────────────────────────────────

function MiniStat({ label, value, color }) {
  const bg = {
    gray: 'bg-gray-50',
    green: 'bg-green-50',
    yellow: 'bg-yellow-50',
    purple: 'bg-purple-50',
  }[color]
  const text = {
    gray: 'text-gray-700',
    green: 'text-green-700',
    yellow: 'text-yellow-700',
    purple: 'text-purple-700',
  }[color]
  return (
    <div className={`${bg} rounded-lg px-4 py-3`}>
      <p className="text-xs text-gray-500 mb-0.5">{label}</p>
      <p className={`text-xl font-bold ${text}`}>{value}</p>
    </div>
  )
}

// ── 리스팅 행 ─────────────────────────────────────────

function ListingRow({ listing, onDelete, onPublish, isPublishing }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-white border rounded-lg overflow-hidden hover:shadow-sm transition-shadow">
      <div className="flex items-center gap-4 px-5 py-4">
        {/* 상태 배지 */}
        <span
          className={`text-xs font-medium px-2 py-0.5 rounded-full flex-shrink-0 ${
            STATUS_COLORS[listing.status] || STATUS_COLORS.draft
          }`}
        >
          {listing.status}
        </span>

        {/* 제목 */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">{listing.title}</p>
          <div className="flex items-center gap-3 mt-0.5">
            <span className="text-xs text-gray-400">{listing.template_name}</span>
            <span className="text-xs text-purple-600 font-semibold">${listing.price}</span>
            <span className="text-xs text-gray-400">{listing.tags?.length ?? 0} tags</span>
          </div>
        </div>

        {/* Etsy 링크 */}
        {listing.etsy_url && (
          <a
            href={listing.etsy_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-400 hover:text-purple-600 flex-shrink-0"
            title="View on Etsy"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        )}

        {/* 액션 */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {listing.status === 'draft' && (
            <button
              onClick={onPublish}
              disabled={isPublishing}
              className="flex items-center gap-1 text-xs bg-green-600 text-white px-3 py-1.5 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              <Upload className="w-3 h-3" />
              {isPublishing ? '...' : 'Publish'}
            </button>
          )}
          <button
            onClick={() => setExpanded((e) => !e)}
            className="p-1.5 text-gray-400 hover:text-gray-700 border rounded-lg hover:bg-gray-50"
          >
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={onDelete}
            className="p-1.5 text-gray-400 hover:text-red-500 border rounded-lg hover:bg-red-50"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 펼침 상세 */}
      {expanded && (
        <div className="border-t bg-gray-50 px-5 py-4 space-y-3">
          <div>
            <p className="text-xs font-medium text-gray-500 mb-1">Tags</p>
            <div className="flex flex-wrap gap-1.5">
              {(listing.tags || []).map((t) => (
                <span
                  key={t}
                  className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-500 mb-1">Description (preview)</p>
            <p className="text-xs text-gray-600 leading-relaxed line-clamp-4">
              {listing.description}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

// ── 신규 리스팅 생성 흐름 (3단계 모달) ───────────────────

function CreateListingFlow({ templates, onClose, onCreated }) {
  const {
    seoVersions,
    activeSeo,
    loading,
    errors,
    generateSEO,
    fetchSEOVersions,
    selectSEO,
    createListing,
  } = useListingStore()

  const [step, setStep] = useState(1)
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [price, setPrice] = useState('4.99')

  // 템플릿 선택 → SEO 버전 로드
  const handleSelectTemplate = async (t) => {
    setSelectedTemplate(t)
    await fetchSEOVersions(t.id)
    setStep(2)
  }

  // SEO 생성
  const handleGenSEO = async () => {
    if (!selectedTemplate) return
    await generateSEO(selectedTemplate.id)
  }

  // 리스팅 생성
  const handleCreate = async () => {
    if (!activeSeo) return
    try {
      await createListing({
        template_id: selectedTemplate.id,
        seo_id: activeSeo.id,
        price: parseFloat(price) || 4.99,
      })
      onCreated()
    } catch {
      /* error in store */
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[92vh] overflow-y-auto">
        {/* 헤더 */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h2 className="font-semibold text-gray-900">New Listing</h2>
            <div className="flex items-center gap-2 mt-1">
              {[1, 2, 3].map((s) => (
                <div
                  key={s}
                  className={`h-1 w-12 rounded-full transition-colors ${
                    step >= s ? 'bg-purple-500' : 'bg-gray-200'
                  }`}
                />
              ))}
              <span className="text-xs text-gray-400 ml-1">Step {step}/3</span>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6">
          {/* Step 1: 템플릿 선택 */}
          {step === 1 && (
            <div>
              <h3 className="font-medium text-gray-900 mb-1">Select a Template</h3>
              <p className="text-sm text-gray-500 mb-4">
                Choose the Canva template this listing is based on.
              </p>
              {templates.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-8">
                  No templates found. Add templates first.
                </p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {templates.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => handleSelectTemplate(t)}
                      className="text-left border rounded-lg p-3 hover:border-purple-400 hover:bg-purple-50 transition-colors"
                    >
                      <p className="text-sm font-medium text-gray-900 truncate">{t.name}</p>
                      {t.category && (
                        <p className="text-xs text-gray-400 mt-0.5">{t.category}</p>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Step 2: SEO 생성 */}
          {step === 2 && (
            <div>
              <h3 className="font-medium text-gray-900 mb-1">Generate SEO Content</h3>
              <p className="text-sm text-gray-500 mb-4">
                AI will create an optimized title, description, and tags for your listing.
              </p>

              {/* 선택된 템플릿 */}
              <div className="bg-purple-50 border border-purple-100 rounded-lg px-4 py-3 mb-4 text-sm text-purple-800">
                <span className="font-medium">Template:</span> {selectedTemplate?.name}
              </div>

              {/* SEO 생성 버튼 */}
              <button
                onClick={handleGenSEO}
                disabled={loading.seoGenerate}
                className="w-full flex items-center justify-center gap-2 bg-purple-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50 transition-colors mb-4"
              >
                {loading.seoGenerate ? (
                  <>
                    <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                    Generating with AI...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Generate SEO Content
                  </>
                )}
              </button>

              {errors.seoGenerate && (
                <p className="text-sm text-red-500 mb-3">{errors.seoGenerate}</p>
              )}

              {/* 기존 버전 목록 */}
              {seoVersions.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-2">
                    Select a version ({seoVersions.length} available):
                  </p>
                  <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                    {seoVersions.map((seo) => (
                      <button
                        key={seo.id}
                        onClick={() => selectSEO(seo)}
                        className={`w-full text-left border rounded-lg p-3 transition-colors ${
                          activeSeo?.id === seo.id
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-200 hover:border-purple-300 hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-gray-500">v{seo.version}</span>
                          <span className="text-xs font-medium text-purple-600">
                            Score: {seo.performance_score?.toFixed(0)}
                          </span>
                        </div>
                        <p className="text-sm font-medium text-gray-900 line-clamp-1">
                          {seo.title}
                        </p>
                        <div className="flex items-center gap-1 mt-1 flex-wrap">
                          {(seo.tags || []).slice(0, 5).map((t) => (
                            <span
                              key={t}
                              className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded"
                            >
                              {t}
                            </span>
                          ))}
                          {seo.tags?.length > 5 && (
                            <span className="text-xs text-gray-400">
                              +{seo.tags.length - 5}
                            </span>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* 다음 버튼 */}
              <div className="flex gap-3 mt-5">
                <button
                  onClick={() => setStep(1)}
                  className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm hover:bg-gray-50 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={() => setStep(3)}
                  disabled={!activeSeo}
                  className="flex-1 bg-purple-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50 transition-colors"
                >
                  Next: Set Price
                </button>
              </div>
            </div>
          )}

          {/* Step 3: 가격 설정 및 확인 */}
          {step === 3 && (
            <div>
              <h3 className="font-medium text-gray-900 mb-1">Set Price & Confirm</h3>
              <p className="text-sm text-gray-500 mb-4">
                Review the SEO content and set your listing price.
              </p>

              {/* SEO 미리보기 */}
              {activeSeo && (
                <div className="bg-gray-50 border rounded-lg p-4 mb-4 space-y-2">
                  <div>
                    <p className="text-xs text-gray-500 mb-0.5">Title</p>
                    <p className="text-sm font-medium text-gray-900">{activeSeo.title}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {activeSeo.title.length}/140 chars
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Tags ({activeSeo.tags?.length}/13)</p>
                    <div className="flex flex-wrap gap-1">
                      {(activeSeo.tags || []).map((t) => (
                        <span
                          key={t}
                          className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-0.5">SEO Score</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                        <div
                          className="bg-purple-500 h-1.5 rounded-full"
                          style={{ width: `${Math.min(100, activeSeo.performance_score)}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium text-purple-600">
                        {activeSeo.performance_score?.toFixed(0)}/100
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* 가격 입력 */}
              <div className="mb-5">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Price (USD) <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="number"
                    min="0.20"
                    step="0.01"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <p className="text-xs text-gray-400 mt-1">Minimum $0.20 (Etsy requirement)</p>
              </div>

              {errors.create && (
                <p className="text-sm text-red-500 mb-3">{errors.create}</p>
              )}

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(2)}
                  className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm hover:bg-gray-50 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={handleCreate}
                  disabled={loading.create || !activeSeo}
                  className="flex-1 bg-purple-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50 transition-colors"
                >
                  {loading.create ? 'Creating...' : 'Create Draft Listing'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
