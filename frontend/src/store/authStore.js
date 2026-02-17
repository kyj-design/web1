import { create } from 'zustand'
import axios from 'axios'

const api = axios.create({ baseURL: (import.meta.env.VITE_API_BASE_URL || '') + '/api' })

const useAuthStore = create((set, get) => ({
  // ── 상태 ────────────────────────────────────────
  authenticated: false,
  shopId: null,
  shopName: null,
  scope: null,
  expiresAt: null,
  canRefresh: false,
  loading: false,
  error: null,

  // ── 액션 ────────────────────────────────────────

  /** 현재 Etsy 연결 상태를 서버에서 가져옴 */
  fetchAuthStatus: async () => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/auth/status')
      set({
        authenticated: data.authenticated,
        shopId: data.shop_id,
        shopName: data.shop_name,
        scope: data.scope,
        expiresAt: data.expires_at,
        canRefresh: data.can_refresh ?? false,
        loading: false,
      })
    } catch {
      set({ loading: false, error: 'Failed to fetch auth status' })
    }
  },

  /** Etsy OAuth 인증 URL을 받아 새 창에서 열어 OAuth 흐름 시작 */
  connectEtsy: async () => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.get('/auth/etsy/login')
      // OAuth 흐름은 같은 창에서 진행 (callback → /settings 리다이렉트)
      window.location.href = data.auth_url
    } catch {
      set({ loading: false, error: 'Failed to initiate Etsy OAuth' })
    }
  },

  /** Etsy 연결 해제 */
  disconnectEtsy: async () => {
    set({ loading: true, error: null })
    try {
      await api.delete('/auth/etsy/disconnect')
      set({
        authenticated: false,
        shopId: null,
        shopName: null,
        scope: null,
        expiresAt: null,
        canRefresh: false,
        loading: false,
      })
    } catch {
      set({ loading: false, error: 'Failed to disconnect Etsy' })
    }
  },

  /** 수동 토큰 갱신 */
  refreshToken: async () => {
    set({ loading: true, error: null })
    try {
      await api.post('/auth/etsy/refresh')
      await get().fetchAuthStatus()
    } catch {
      set({ loading: false, error: 'Token refresh failed. Please reconnect.' })
    }
  },

  clearError: () => set({ error: null }),
}))

export default useAuthStore
