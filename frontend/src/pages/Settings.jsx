import { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Settings as SettingsIcon,
  Store,
  CheckCircle,
  XCircle,
  RefreshCw,
  LogOut,
  ExternalLink,
  AlertCircle,
  Zap,
  Info,
} from 'lucide-react'
import useAuthStore from '../store/authStore'

export default function Settings() {
  const [searchParams, setSearchParams] = useSearchParams()
  const {
    authenticated,
    shopId,
    shopName,
    scope,
    expiresAt,
    canRefresh,
    loading,
    error,
    fetchAuthStatus,
    connectEtsy,
    disconnectEtsy,
    refreshToken,
    clearError,
  } = useAuthStore()

  // 페이지 진입 시 상태 조회
  useEffect(() => {
    fetchAuthStatus()
  }, [])

  // OAuth callback 결과 처리 (URL 파라미터)
  useEffect(() => {
    const connected = searchParams.get('etsy_connected')
    const oauthError = searchParams.get('error')

    if (connected === 'true') {
      fetchAuthStatus()
      setSearchParams({})
    } else if (oauthError) {
      setSearchParams({})
    }
  }, [searchParams])

  const scopeList = scope ? scope.split(' ') : []

  const formatExpiry = (isoStr) => {
    if (!isoStr) return '만료 없음'
    const d = new Date(isoStr)
    return d.toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 px-4 py-6">
      {/* 헤더 */}
      <div className="flex items-center gap-3">
        <SettingsIcon className="w-7 h-7 text-purple-600" />
        <h1 className="text-2xl font-bold text-gray-800">Settings</h1>
      </div>

      {/* 전역 에러 배너 */}
      {(error || searchParams.get('error')) && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-lg p-4">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-700">
              {error || 'Etsy 인증에 실패했습니다. 다시 시도해 주세요.'}
            </p>
          </div>
          <button
            onClick={clearError}
            className="ml-auto text-red-400 hover:text-red-600 text-xs"
          >
            닫기
          </button>
        </div>
      )}

      {/* ── Etsy 계정 연동 섹션 ── */}
      <section className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-2">
          <Store className="w-5 h-5 text-orange-500" />
          <h2 className="font-semibold text-gray-800">Etsy 계정 연동</h2>
        </div>

        <div className="px-6 py-5 space-y-4">
          {/* 연결 상태 카드 */}
          {authenticated ? (
            <div className="flex items-start gap-4 bg-green-50 border border-green-200 rounded-lg p-4">
              <CheckCircle className="w-6 h-6 text-green-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-green-800">연결됨</p>
                {shopName && (
                  <p className="text-sm text-green-700 mt-0.5">
                    Shop: <span className="font-medium">{shopName}</span>
                    {shopId && (
                      <a
                        href={`https://www.etsy.com/shop/${shopName}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-2 inline-flex items-center gap-0.5 text-green-600 hover:underline"
                      >
                        방문 <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </p>
                )}
                {shopId && (
                  <p className="text-xs text-green-600 mt-0.5">Shop ID: {shopId}</p>
                )}
                {expiresAt && (
                  <p className="text-xs text-green-600 mt-1">
                    토큰 만료: {formatExpiry(expiresAt)}
                  </p>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-start gap-4 bg-gray-50 border border-gray-200 rounded-lg p-4">
              <XCircle className="w-6 h-6 text-gray-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-gray-600">연결 안 됨</p>
                <p className="text-sm text-gray-500 mt-0.5">
                  Etsy 계정을 연결하면 실제 리스팅을 자동으로 발행할 수 있습니다.
                </p>
              </div>
            </div>
          )}

          {/* 권한 범위 */}
          {authenticated && scopeList.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-1.5">부여된 권한</p>
              <div className="flex flex-wrap gap-1.5">
                {scopeList.map((s) => (
                  <span
                    key={s}
                    className="px-2 py-0.5 bg-purple-50 text-purple-700 rounded text-xs font-mono"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 액션 버튼 */}
          <div className="flex flex-wrap gap-3 pt-1">
            {!authenticated ? (
              <button
                onClick={connectEtsy}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg text-sm font-medium disabled:opacity-60 transition-colors"
              >
                {loading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Zap className="w-4 h-4" />
                )}
                Etsy 계정 연결
              </button>
            ) : (
              <>
                {canRefresh && (
                  <button
                    onClick={refreshToken}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium disabled:opacity-60 transition-colors"
                  >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    토큰 갱신
                  </button>
                )}
                <button
                  onClick={disconnectEtsy}
                  disabled={loading}
                  className="flex items-center gap-2 px-4 py-2 bg-white border border-red-300 hover:bg-red-50 text-red-600 rounded-lg text-sm font-medium disabled:opacity-60 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  연결 해제
                </button>
                <button
                  onClick={connectEtsy}
                  disabled={loading}
                  className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-600 rounded-lg text-sm font-medium disabled:opacity-60 transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  재인증
                </button>
              </>
            )}
          </div>
        </div>
      </section>

      {/* ── OAuth 안내 섹션 ── */}
      <section className="bg-blue-50 border border-blue-100 rounded-xl p-5 space-y-3">
        <div className="flex items-center gap-2">
          <Info className="w-5 h-5 text-blue-500" />
          <h3 className="font-semibold text-blue-800 text-sm">Etsy OAuth 인증 안내</h3>
        </div>
        <ol className="list-decimal list-inside space-y-1.5 text-sm text-blue-700 pl-1">
          <li>
            <strong>Etsy 계정 연결</strong> 버튼을 클릭하면 Etsy 공식 로그인 화면으로 이동합니다.
          </li>
          <li>
            Etsy에서 <strong>리스팅 읽기/쓰기, 스토어 읽기/쓰기</strong> 권한을 승인합니다.
          </li>
          <li>
            승인 완료 후 자동으로 이 페이지로 돌아오며, Shop ID가 저장됩니다.
          </li>
          <li>
            이후 <strong>Listings 페이지 → Publish</strong>를 누르면 실제 Etsy에 발행됩니다.
          </li>
        </ol>
        <p className="text-xs text-blue-500">
          * Etsy Developer 계정이 필요합니다. API 키는 <code>.env</code> 파일의{' '}
          <code>ETSY_API_KEY</code>에 설정되어 있어야 합니다.
        </p>
      </section>

      {/* ── LLM 설정 정보 (읽기 전용) ── */}
      <section className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-2">
          <Zap className="w-5 h-5 text-purple-500" />
          <h2 className="font-semibold text-gray-800">LLM 설정</h2>
        </div>
        <div className="px-6 py-5">
          <p className="text-sm text-gray-500 mb-3">
            SEO 콘텐츠 생성에 사용되는 LLM 설정은 서버의 <code className="bg-gray-100 px-1 rounded">.env</code> 파일에서 관리됩니다.
          </p>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-gray-50 rounded-lg px-4 py-3">
              <p className="text-xs font-medium text-gray-400 mb-0.5">LLM_PROVIDER</p>
              <p className="font-medium text-gray-700">환경변수로 설정</p>
            </div>
            <div className="bg-gray-50 rounded-lg px-4 py-3">
              <p className="text-xs font-medium text-gray-400 mb-0.5">OLLAMA_MODEL</p>
              <p className="font-medium text-gray-700">환경변수로 설정</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
