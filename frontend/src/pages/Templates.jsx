import { useState, useEffect, useRef } from 'react'
import {
  Plus,
  FileText,
  Download,
  Trash2,
  Upload,
  ExternalLink,
  X,
  Edit2,
  Layers,
} from 'lucide-react'
import useTemplateStore from '../store/templateStore'

const CATEGORIES = [
  'Planner & Organizer',
  'Resume & Career',
  'Wedding & Events',
  'Home Decor',
  'Finance & Planner',
  'Health & Wellness',
  'Stickers & Labels',
  'Digital Graphics',
  'Printables',
  'General',
]

// ── 메인 페이지 ──────────────────────────────────────

export default function Templates() {
  const {
    templates,
    totalTemplates,
    niches,
    loading,
    errors,
    fetchTemplates,
    fetchNichesForSelect,
    deleteTemplate,
    generatePDF,
    downloadPDF,
    uploadPreview,
  } = useTemplateStore()

  const [showAddModal, setShowAddModal] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState(null)
  const [pdfResult, setPdfResult] = useState(null)
  const [pdfTemplateId, setPdfTemplateId] = useState(null)

  useEffect(() => {
    fetchTemplates()
    fetchNichesForSelect()
  }, [])

  const handleGeneratePDF = async (template) => {
    setPdfTemplateId(template.id)
    setPdfResult(null)
    try {
      const pdf = await generatePDF(template.id)
      setPdfResult({ pdf, templateId: template.id })
    } catch {
      // 에러는 store에서 처리
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold text-gray-900">Template Management</h1>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Template
        </button>
      </div>
      <p className="text-gray-500 text-sm mb-6">
        Register your Canva template links and generate delivery PDFs.
      </p>

      {/* PDF 생성 결과 알림 */}
      {pdfResult && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 flex items-center justify-between">
          <div>
            <p className="font-medium text-green-800 text-sm">PDF generated successfully!</p>
            <p className="text-green-600 text-xs mt-0.5">
              {pdfResult.pdf.file_size_kb} KB
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => downloadPDF(pdfResult.templateId, pdfResult.pdf.id)}
              className="flex items-center gap-1.5 bg-green-600 text-white text-xs px-3 py-1.5 rounded-lg hover:bg-green-700 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              Download PDF
            </button>
            <button
              onClick={() => setPdfResult(null)}
              className="text-green-600 hover:text-green-800 p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* 오류 알림 */}
      {errors.pdf && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-600">
          {errors.pdf}
        </div>
      )}

      {/* 템플릿 목록 */}
      {loading.list ? (
        <div className="text-center py-12 text-gray-400">
          <div className="animate-spin w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
          Loading templates...
        </div>
      ) : templates.length === 0 ? (
        <EmptyState onAdd={() => setShowAddModal(true)} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((t) => (
            <TemplateCard
              key={t.id}
              template={t}
              onEdit={() => setEditingTemplate(t)}
              onDelete={() => deleteTemplate(t.id)}
              onGeneratePDF={() => handleGeneratePDF(t)}
              onUploadPreview={uploadPreview}
              isGeneratingPDF={loading.pdf && pdfTemplateId === t.id}
            />
          ))}
        </div>
      )}

      {/* 추가 모달 */}
      {showAddModal && (
        <TemplateModal
          niches={niches}
          onClose={() => setShowAddModal(false)}
          onSaved={() => {
            setShowAddModal(false)
            fetchTemplates()
          }}
        />
      )}

      {/* 수정 모달 */}
      {editingTemplate && (
        <TemplateModal
          niches={niches}
          initialData={editingTemplate}
          onClose={() => setEditingTemplate(null)}
          onSaved={() => {
            setEditingTemplate(null)
            fetchTemplates()
          }}
        />
      )}
    </div>
  )
}

// ── 빈 상태 ──────────────────────────────────────────

function EmptyState({ onAdd }) {
  return (
    <div className="text-center py-16 text-gray-400">
      <Layers className="w-14 h-14 mx-auto mb-3 opacity-20" />
      <p className="text-base font-medium text-gray-500">No templates yet</p>
      <p className="text-sm mt-1 mb-5">
        Add your first Canva template to get started.
      </p>
      <button
        onClick={onAdd}
        className="inline-flex items-center gap-2 bg-purple-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors"
      >
        <Plus className="w-4 h-4" />
        Add Template
      </button>
    </div>
  )
}

// ── 템플릿 카드 ──────────────────────────────────────

function TemplateCard({
  template,
  onEdit,
  onDelete,
  onGeneratePDF,
  onUploadPreview,
  isGeneratingPDF,
}) {
  const fileInputRef = useRef(null)
  const [uploading, setUploading] = useState(false)

  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    try {
      await onUploadPreview(template.id, file)
    } catch {
      /* 오류는 store에서 처리 */
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border overflow-hidden hover:shadow-md transition-shadow">
      {/* 미리보기 이미지 */}
      <div className="relative h-40 bg-gray-100">
        {template.preview_image_url ? (
          <img
            src={template.preview_image_url}
            alt={template.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300">
            <Layers className="w-10 h-10 opacity-40" />
          </div>
        )}
        {/* 이미지 업로드 버튼 */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="absolute bottom-2 right-2 bg-white bg-opacity-90 text-gray-600 p-1.5 rounded-lg shadow text-xs hover:bg-opacity-100 transition-all flex items-center gap-1"
          title="Upload preview image"
        >
          <Upload className="w-3 h-3" />
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={handleFileChange}
        />
        {/* 카테고리 배지 */}
        {template.category && (
          <span className="absolute top-2 left-2 bg-purple-100 text-purple-700 text-xs px-2 py-0.5 rounded-full font-medium">
            {template.category}
          </span>
        )}
      </div>

      {/* 정보 */}
      <div className="p-4">
        <h3 className="font-semibold text-gray-900 text-sm mb-1 line-clamp-1">
          {template.name}
        </h3>
        {template.niche_name && (
          <p className="text-xs text-gray-400 mb-1">Niche: {template.niche_name}</p>
        )}
        {template.description && (
          <p className="text-xs text-gray-500 line-clamp-2 mb-3 leading-relaxed">
            {template.description}
          </p>
        )}

        {/* 링크 */}
        <a
          href={template.template_link}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-xs text-purple-600 hover:text-purple-800 transition-colors mb-3 truncate"
        >
          <ExternalLink className="w-3 h-3 flex-shrink-0" />
          <span className="truncate">{template.template_link}</span>
        </a>

        {/* PDF 개수 */}
        <div className="flex items-center gap-1 text-xs text-gray-400 mb-3">
          <FileText className="w-3.5 h-3.5" />
          {template.pdf_count} PDF{template.pdf_count !== 1 ? 's' : ''} generated
        </div>

        {/* 액션 버튼들 */}
        <div className="flex gap-2">
          <button
            onClick={onGeneratePDF}
            disabled={isGeneratingPDF}
            className="flex-1 flex items-center justify-center gap-1.5 bg-purple-600 text-white text-xs px-3 py-1.5 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isGeneratingPDF ? (
              <span className="animate-spin w-3 h-3 border border-white border-t-transparent rounded-full" />
            ) : (
              <FileText className="w-3 h-3" />
            )}
            {isGeneratingPDF ? 'Generating...' : 'Gen PDF'}
          </button>
          <button
            onClick={onEdit}
            className="p-1.5 text-gray-400 hover:text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            title="Edit template"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onDelete}
            className="p-1.5 text-gray-400 hover:text-red-500 border border-gray-200 rounded-lg hover:bg-red-50 transition-colors"
            title="Delete template"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  )
}

// ── 추가/수정 모달 ──────────────────────────────────

function TemplateModal({ niches, initialData, onClose, onSaved }) {
  const { createTemplate, updateTemplate, loading, errors } = useTemplateStore()

  const [form, setForm] = useState({
    name: initialData?.name || '',
    template_link: initialData?.template_link || '',
    description: initialData?.description || '',
    category: initialData?.category || '',
    niche_id: initialData?.niche_id || '',
  })

  const isEdit = !!initialData

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((f) => ({ ...f, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const payload = {
      ...form,
      niche_id: form.niche_id ? Number(form.niche_id) : null,
    }
    try {
      if (isEdit) {
        await updateTemplate(initialData.id, payload)
      } else {
        await createTemplate(payload)
      }
      onSaved()
    } catch {
      /* 에러는 store에서 처리 */
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        {/* 헤더 */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="font-semibold text-gray-900">
            {isEdit ? 'Edit Template' : 'Add Template'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 폼 */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Template Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="name"
              value={form.name}
              onChange={handleChange}
              required
              placeholder="e.g., 2025 Weekly Planner A4"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Canva Template Link <span className="text-red-500">*</span>
            </label>
            <input
              type="url"
              name="template_link"
              value={form.template_link}
              onChange={handleChange}
              required
              placeholder="https://www.canva.com/design/..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <p className="mt-1 text-xs text-gray-400">
              Canva → Share → More → Template link
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              name="description"
              value={form.description}
              onChange={handleChange}
              rows={3}
              placeholder="Brief description of the template..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                name="category"
                value={form.category}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Select...</option>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Niche
              </label>
              <select
                name="niche_id"
                value={form.niche_id}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">None</option>
                {niches.map((n) => (
                  <option key={n.id} value={n.id}>{n.name}</option>
                ))}
              </select>
            </div>
          </div>

          {(errors.create || errors.update) && (
            <p className="text-sm text-red-600">{errors.create || errors.update}</p>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border border-gray-300 text-gray-700 text-sm font-medium py-2 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading.create || loading.update}
              className="flex-1 bg-purple-600 text-white text-sm font-medium py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
            >
              {loading.create || loading.update
                ? isEdit ? 'Saving...' : 'Adding...'
                : isEdit ? 'Save Changes' : 'Add Template'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
