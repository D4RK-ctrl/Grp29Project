import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import TripDashboard from './pages/TripDashboard'

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/trip/:tripId" element={<TripDashboard />} />
      </Routes>
    </BrowserRouter>
  )
}
