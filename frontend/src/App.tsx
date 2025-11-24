import { Routes, Route, Navigate } from 'react-router-dom'
import { CalendarPage } from './pages/CalendarPage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { ProfilePage } from './pages/ProfilePage'
import { AdminWhitelistPage } from './pages/AdminWhitelistPage'
import { ReservationRequestPage } from './pages/ReservationRequestPage'
import { AdminReservationListPage } from './pages/AdminReservationListPage'
import { useAuth } from './context/AuthContext'
import './App.css'

function App() {
  const { user, isInitializing } = useAuth()

  if (isInitializing) {
    // スタイルを調整して画面中央に表示
    return (
      <div className="loading" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        Loading...
      </div>
    )
  }

  return (
    <Routes>
      <Route 
        path="/" 
        element={user ? <CalendarPage /> : <Navigate to="/login" replace />} 
      />
      <Route 
        path="/login" 
        element={user ? <Navigate to="/" replace /> : <LoginPage />} 
      />
      <Route 
        path="/register" 
        element={user ? <Navigate to="/" replace /> : <RegisterPage />} 
      />
      <Route
        path="/profile"
        element={user ? <ProfilePage /> : <Navigate to="/login" replace />}
      />
      <Route
        path="/reservations/new"
        element={user ? <ReservationRequestPage /> : <Navigate to="/login" replace />}
      />
      <Route
        path="/admin/whitelist"
        element={user?.isAdmin ? <AdminWhitelistPage /> : <Navigate to="/" replace />}
      />
      <Route
        path="/admin/reservations"
        element={user?.isAdmin ? <AdminReservationListPage /> : <Navigate to="/" replace />}
      />
      {/* 追加: 存在しないパスはルートへリダイレクト */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App

