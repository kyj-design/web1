import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import MarketResearch from './pages/MarketResearch'
import Bestsellers from './pages/Bestsellers'
import Templates from './pages/Templates'
import Listings from './pages/Listings'
import './App.css'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/market" element={<MarketResearch />} />
            <Route path="/bestsellers" element={<Bestsellers />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/listings" element={<Listings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
