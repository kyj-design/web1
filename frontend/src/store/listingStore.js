import { create } from 'zustand'
import axios from 'axios'

const api = axios.create({ baseURL: (import.meta.env.VITE_API_BASE_URL || '') + '/api' })

const useListingStore = create((set, get) => ({
  // ── 상태 ──────────────────────────────────────
  listings: [],
  totalListings: 0,
  stats: null,

  // SEO
  seoVersions: [],      // 현재 선택된 템플릿의 SEO 버전 목록
  activeSeo: null,      // 선택된 SEO 버전

  loading: {
    listings: false,
    seoGenerate: false,
    seoList: false,
    create: false,
    publish: false,
    stats: false,
  },
  errors: {
    seoGenerate: null,
    create: null,
    publish: null,
  },

  // ── SEO 액션 ──────────────────────────────────

  generateSEO: async (templateId) => {
    set((s) => ({
      loading: { ...s.loading, seoGenerate: true },
      errors: { ...s.errors, seoGenerate: null },
      activeSeo: null,
    }))
    try {
      const { data } = await api.post('/listings/seo/generate', null, {
        params: { template_id: templateId },
      })
      set((s) => ({
        activeSeo: data,
        seoVersions: [data, ...s.seoVersions.filter((v) => v.id !== data.id)],
      }))
      return data
    } catch (err) {
      const message = err.response?.data?.detail || 'SEO generation failed'
      set((s) => ({ errors: { ...s.errors, seoGenerate: message } }))
      throw err
    } finally {
      set((s) => ({ loading: { ...s.loading, seoGenerate: false } }))
    }
  },

  fetchSEOVersions: async (templateId) => {
    set((s) => ({ loading: { ...s.loading, seoList: true }, seoVersions: [] }))
    try {
      const { data } = await api.get(`/listings/seo/${templateId}`)
      set({ seoVersions: data.seo_versions })
      if (data.seo_versions.length > 0 && !get().activeSeo) {
        set({ activeSeo: data.seo_versions[0] })
      }
    } catch (err) {
      console.error('Failed to fetch SEO versions:', err)
    } finally {
      set((s) => ({ loading: { ...s.loading, seoList: false } }))
    }
  },

  selectSEO: (seo) => set({ activeSeo: seo }),

  deleteSEO: async (seoId) => {
    try {
      await api.delete(`/listings/seo/${seoId}`)
      set((s) => ({
        seoVersions: s.seoVersions.filter((v) => v.id !== seoId),
        activeSeo: s.activeSeo?.id === seoId ? null : s.activeSeo,
      }))
    } catch (err) {
      console.error('Failed to delete SEO:', err)
    }
  },

  // ── 리스팅 액션 ──────────────────────────────

  fetchListings: async (filters = {}) => {
    set((s) => ({ loading: { ...s.loading, listings: true } }))
    try {
      const { data } = await api.get('/listings/', { params: filters })
      set({ listings: data.listings, totalListings: data.total })
    } catch (err) {
      console.error('Failed to fetch listings:', err)
    } finally {
      set((s) => ({ loading: { ...s.loading, listings: false } }))
    }
  },

  fetchStats: async () => {
    set((s) => ({ loading: { ...s.loading, stats: true } }))
    try {
      const { data } = await api.get('/listings/stats')
      set({ stats: data })
    } catch {
      set({ stats: null })
    } finally {
      set((s) => ({ loading: { ...s.loading, stats: false } }))
    }
  },

  createListing: async (payload) => {
    set((s) => ({
      loading: { ...s.loading, create: true },
      errors: { ...s.errors, create: null },
    }))
    try {
      const { data } = await api.post('/listings/', payload)
      set((s) => ({
        listings: [data, ...s.listings],
        totalListings: s.totalListings + 1,
      }))
      return data
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to create listing'
      set((s) => ({ errors: { ...s.errors, create: message } }))
      throw err
    } finally {
      set((s) => ({ loading: { ...s.loading, create: false } }))
    }
  },

  publishListing: async (listingId) => {
    set((s) => ({
      loading: { ...s.loading, publish: true },
      errors: { ...s.errors, publish: null },
    }))
    try {
      const { data } = await api.post(`/listings/${listingId}/publish`)
      // 상태 업데이트
      set((s) => ({
        listings: s.listings.map((l) =>
          l.id === listingId ? data.listing : l
        ),
      }))
      return data
    } catch (err) {
      const message = err.response?.data?.detail || 'Publish failed'
      set((s) => ({ errors: { ...s.errors, publish: message } }))
      throw err
    } finally {
      set((s) => ({ loading: { ...s.loading, publish: false } }))
    }
  },

  updateListing: async (listingId, payload) => {
    try {
      const { data } = await api.put(`/listings/${listingId}`, payload)
      set((s) => ({
        listings: s.listings.map((l) => (l.id === listingId ? data : l)),
      }))
      return data
    } catch (err) {
      console.error('Failed to update listing:', err)
      throw err
    }
  },

  deleteListing: async (listingId) => {
    try {
      await api.delete(`/listings/${listingId}`)
      set((s) => ({
        listings: s.listings.filter((l) => l.id !== listingId),
        totalListings: s.totalListings - 1,
      }))
    } catch (err) {
      console.error('Failed to delete listing:', err)
    }
  },
}))

export default useListingStore
