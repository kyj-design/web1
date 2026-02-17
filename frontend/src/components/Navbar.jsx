import { useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import {
  BarChart2, Search, TrendingUp, LayoutDashboard,
  Layers, ShoppingBag, Settings, CheckCircle, XCircle,
} from 'lucide-react'
import useAuthStore from '../store/authStore'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/market', label: 'Market Research', icon: Search },
  { to: '/bestsellers', label: 'Bestsellers', icon: TrendingUp },
  { to: '/templates', label: 'Templates', icon: Layers },
  { to: '/listings', label: 'Listings', icon: ShoppingBag },
]

export default function Navbar() {
  const { authenticated, shopName, fetchAuthStatus } = useAuthStore()

  useEffect(() => {
    fetchAuthStatus()
  }, [])

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <BarChart2 className="w-6 h-6 text-purple-600" />
            <span className="font-bold text-lg text-gray-900">Canva-Etsy</span>
            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full ml-1">
              Phase 5
            </span>
          </div>

          {/* Nav Links */}
          <div className="flex gap-1">
            {navItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-purple-100 text-purple-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`
                }
              >
                <Icon className="w-4 h-4" />
                {label}
              </NavLink>
            ))}
          </div>

          {/* 우측: Etsy 연결 상태 + Settings */}
          <div className="flex items-center gap-2">
            {/* Etsy 연결 상태 배지 */}
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-purple-100 text-purple-700'
                    : 'hover:bg-gray-100'
                } ${authenticated ? 'text-green-600' : 'text-gray-400'}`
              }
              title={authenticated ? `Etsy 연결됨: ${shopName || ''}` : 'Etsy 미연결 - 클릭하여 설정'}
            >
              {authenticated ? (
                <>
                  <CheckCircle className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">{shopName || 'Etsy 연결됨'}</span>
                </>
              ) : (
                <>
                  <XCircle className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Etsy 미연결</span>
                </>
              )}
            </NavLink>

            {/* Settings 아이콘 버튼 */}
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `p-2 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-purple-100 text-purple-700'
                    : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
                }`
              }
              title="Settings"
            >
              <Settings className="w-4 h-4" />
            </NavLink>
          </div>
        </div>
      </div>
    </nav>
  )
}
