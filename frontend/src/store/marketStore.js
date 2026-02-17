import { create } from 'zustand'
import axios from 'axios'

const api = axios.create({ baseURL: (import.meta.env.VITE_API_BASE_URL || '') + '/api' })

const useMarketStore = create((set, get) => ({
  // ── 상태 ──────────────────────────────────────
  niches: [],
  totalNiches: 0,
  bestsellers: [],
  totalBestsellers: 0,
  stats: null,

  // 검색 입력 (상태/액션 명명 충돌 방지: Input 접미사 사용)
  researchKeywordInput: '',
  bestsellerKeywordInput: '',

  loading: {
    research: false,
    niches: false,
    bestsellers: false,
    analyze: false,
    stats: false,
  },
  errors: {
    research: null,
    niches: null,
    bestsellers: null,
    analyze: null,
  },

  // ── 입력 액션 ──────────────────────────────────

  setResearchKeyword: (keyword) => set({ researchKeywordInput: keyword }),
  setBestsellerKeyword: (keyword) => set({ bestsellerKeywordInput: keyword }),

  // ── Market Research 액션 ──────────────────────

  runResearch: async (keyword) => {
    set((s) => ({
      loading: { ...s.loading, research: true },
      errors: { ...s.errors, research: null },
    }))
    try {
      const { data } = await api.post('/market/research', {
        keyword,
        limit: 25,
      })
      await get().fetchNiches()
      return data
    } catch (err) {
      const message = err.response?.data?.detail || 'Research failed'
      set((s) => ({ errors: { ...s.errors, research: message } }))
      throw err
    } finally {
      set((s) => ({ loading: { ...s.loading, research: false } }))
    }
  },

  fetchNiches: async (sortBy = 'trend_score', limit = 20) => {
    set((s) => ({ loading: { ...s.loading, niches: true } }))
    try {
      const { data } = await api.get('/market/niches', {
        params: { sort_by: sortBy, limit },
      })
      set({ niches: data.niches, totalNiches: data.total })
    } catch (err) {
      set((s) => ({ errors: { ...s.errors, niches: err.message } }))
    } finally {
      set((s) => ({ loading: { ...s.loading, niches: false } }))
    }
  },

  deleteNiche: async (nicheId) => {
    try {
      await api.delete(`/market/niches/${nicheId}`)
      set((s) => ({
        niches: s.niches.filter((n) => n.id !== nicheId),
        totalNiches: s.totalNiches - 1,
      }))
    } catch (err) {
      console.error('Failed to delete niche:', err)
    }
  },

  // ── Bestsellers 액션 ──────────────────────────

  runBestsellerAnalysis: async (keyword, analyzeImages = true) => {
    set((s) => ({
      loading: { ...s.loading, analyze: true },
      errors: { ...s.errors, analyze: null },
    }))
    try {
      const { data } = await api.post('/bestsellers/analyze', {
        keyword,
        limit: 10,
        analyze_images: analyzeImages,
      })
      await get().fetchBestsellers()
      return data
    } catch (err) {
      const message = err.response?.data?.detail || 'Analysis failed'
      set((s) => ({ errors: { ...s.errors, analyze: message } }))
      throw err
    } finally {
      set((s) => ({ loading: { ...s.loading, analyze: false } }))
    }
  },

  fetchBestsellers: async (filters = {}) => {
    set((s) => ({ loading: { ...s.loading, bestsellers: true } }))
    try {
      const params = {}
      if (filters.style) params.style = filters.style
      if (filters.analyzed_only) params.analyzed_only = true

      const { data } = await api.get('/bestsellers/', { params })
      set({ bestsellers: data.templates, totalBestsellers: data.total })
    } catch (err) {
      set((s) => ({ errors: { ...s.errors, bestsellers: err.message } }))
    } finally {
      set((s) => ({ loading: { ...s.loading, bestsellers: false } }))
    }
  },

  // ── Dashboard Stats 액션 ──────────────────────

  fetchStats: async () => {
    set((s) => ({ loading: { ...s.loading, stats: true } }))
    try {
      const [marketRes, bestsellerRes] = await Promise.all([
        api.get('/market/stats'),
        api.get('/bestsellers/stats'),
      ])
      set({
        stats: {
          market: marketRes.data,
          bestsellers: bestsellerRes.data,
        },
      })
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    } finally {
      set((s) => ({ loading: { ...s.loading, stats: false } }))
    }
  },
}))

export default useMarketStore
