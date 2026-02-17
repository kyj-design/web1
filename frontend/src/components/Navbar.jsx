import { NavLink } from 'react-router-dom'
import { BarChart2, Search, TrendingUp, LayoutDashboard, Layers, ShoppingBag } from 'lucide-react'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/market', label: 'Market Research', icon: Search },
  { to: '/bestsellers', label: 'Bestsellers', icon: TrendingUp },
  { to: '/templates', label: 'Templates', icon: Layers },
  { to: '/listings', label: 'Listings', icon: ShoppingBag },
]

export default function Navbar() {
  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <BarChart2 className="w-6 h-6 text-purple-600" />
            <span className="font-bold text-lg text-gray-900">Canva-Etsy</span>
            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full ml-1">
              Phase 4
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
        </div>
      </div>
    </nav>
  )
}
