import { Routes, Route, Navigate } from 'react-router-dom'
import { Box } from '@mui/material'
import { useSelector } from 'react-redux'

// Pages
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Search from './pages/Search'
import Documents from './pages/Documents'
import Admin from './pages/Admin'
import Layout from './components/Common/Layout'

// Protected Route Component
const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { isAuthenticated, user } = useSelector((state) => state.auth)

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (adminOnly && user?.role !== 'admin') {
    return <Navigate to="/" replace />
  }

  return children
}

function App() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route path="/" element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }>
          <Route index element={<Dashboard />} />
          <Route path="search" element={<Search />} />
          <Route path="documents" element={<Documents />} />
          <Route path="admin" element={
            <ProtectedRoute adminOnly>
              <Admin />
            </ProtectedRoute>
          } />
        </Route>
      </Routes>
    </Box>
  )
}

export default App
