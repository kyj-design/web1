import { create } from 'zustand'
import axios from 'axios'

const api = axios.create({ baseURL: (import.meta.env.VITE_API_BASE_URL || '') + '/api' })

const useTemplateStore = create((set, get) => ({
  // ── 상태 ──────────────────────────────────────
  templates: [],
  totalTemplates: 0,
  currentTemplate: null,
  niches: [],  // 드롭다운용 Niche 목록

  loading: {
    list: false,
    create: false,
    update: false,
    delete: false,
    upload: false,
    pdf: false,
  },
  errors: {
    list: null,
    create: null,
    update: null,
    upload: null,
    pdf: null,
  },

  // ── 액션 ──────────────────────────────────────

  fetchTemplates: async (filters = {}) => {
    set((s) => ({ loading: { ...s.loading, list: true }, errors: { ...s.errors, list: null } }))
    try {
      const { data } = await api.get('/templates/', { params: filters })
      set({ templates: data.templates, totalTemplates: data.total })
    } catch (err) {
      set((s) => ({ errors: { ...s.errors, list: err.message } }))
    } finally {
      set((s) => ({ loading: { ...s.loading, list: false } }))
    }
  },

  fetchTemplate: async (id) => {
    try {
      const { data } = await api.get(`/templates/${id}`)
      set({ currentTemplate: data })
      return data
    } catch (err) {
      console.error('Failed to fetch template:', err)
      return null
    }
  },

  createTemplate: async (formData) => {
    set((s) => ({
      loading: { ...s.loading, create: true },
      errors: { ...s.errors, create: null },
    }))
    try {
      const { data } = await api.post('/templates/', formData)
      await get().fetchTemplates()
      return data
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to create template'
      set((s) => ({ errors: { ...s.errors, create: message } }))
      throw err
    } finally {
      set((s) => ({ loading: { ...s.loading, create: false } }))
    }
  },

  updateTemplate: async (id, formData) => {
    set((s) => ({ loading: { ...s.loading, update: true } }))
    try {
      const { data } = await api.put(`/templates/${id}`, formData)
      set((s) => ({
        templates: s.templates.map((t) => (t.id === id ? data : t)),
        currentTemplate: s.currentTemplate?.id === id ? data : s.currentTemplate,
      }))
      return data
    } catch (err) {
      console.error('Failed to update template:', err)
      throw err
    } finally {
      set((s) => ({ loading: { ...s.loading, update: false } }))
    }
  },

  deleteTemplate: async (id) => {
    set((s) => ({ loading: { ...s.loading, delete: true } }))
    try {
      await api.delete(`/templates/${id}`)
      set((s) => ({
        templates: s.templates.filter((t) => t.id !== id),
        totalTemplates: s.totalTemplates - 1,
      }))
    } catch (err) {
      console.error('Failed to delete template:', err)
    } finally {
      set((s) => ({ loading: { ...s.loading, delete: false } }))
    }
  },

  uploadPreview: async (templateId, file) => {
    set((s) => ({
      loading: { ...s.loading, upload: true },
      errors: { ...s.errors, upload: null },
    }))
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await api.post(`/templates/${templateId}/upload-preview`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      // 목록에서 해당 템플릿의 preview_image_url 업데이트
      set((s) => ({
        templates: s.templates.map((t) =>
          t.id === templateId
            ? { ...t, preview_image_url: data.preview_image_url }
            : t
        ),
      }))
      return data
    } catch (err) {
      const message = err.response?.data?.detail || 'Upload failed'
      set((s) => ({ errors: { ...s.errors, upload: message } }))
      throw err
    } finally {
      set((s) => ({ loading: { ...s.loading, upload: false } }))
    }
  },

  generatePDF: async (templateId) => {
    set((s) => ({
      loading: { ...s.loading, pdf: true },
      errors: { ...s.errors, pdf: null },
    }))
    try {
      const { data } = await api.post(`/templates/${templateId}/generate-pdf`)
      // pdf_count 증가 반영
      set((s) => ({
        templates: s.templates.map((t) =>
          t.id === templateId ? { ...t, pdf_count: (t.pdf_count || 0) + 1 } : t
        ),
      }))
      return data.pdf
    } catch (err) {
      const message = err.response?.data?.detail || 'PDF generation failed'
      set((s) => ({ errors: { ...s.errors, pdf: message } }))
      throw err
    } finally {
      set((s) => ({ loading: { ...s.loading, pdf: false } }))
    }
  },

  downloadPDF: (templateId, pdfId) => {
    // 브라우저 다운로드 트리거
    window.open(`/api/templates/${templateId}/pdfs/${pdfId}/download`, '_blank')
  },

  // Niche 목록 로드 (드롭다운용)
  fetchNichesForSelect: async () => {
    try {
      const { data } = await api.get('/market/niches', { params: { limit: 100 } })
      set({ niches: data.niches || [] })
    } catch {
      set({ niches: [] })
    }
  },
}))

export default useTemplateStore
