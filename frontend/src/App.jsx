import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login     from './pages/Login'
import Demo      from './pages/Demo'
import Dashboard from './pages/Dashboard'
import Cases     from './pages/Cases'
import CaseDetail from './pages/CaseDetail'
import Analytics from './pages/Analytics'

function Protected({ children }) {
  const { user } = useAuth()
  return user ? children : <Navigate to="/login" replace />
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={
            <Protected>
              <Layout>
                <Routes>
                  <Route index                element={<Navigate to="/demo" replace />} />
                  <Route path="demo"          element={<Demo />} />
                  <Route path="dashboard"     element={<Dashboard />} />
                  <Route path="cases"         element={<Cases />} />
                  <Route path="cases/:id"     element={<CaseDetail />} />
                  <Route path="analytics"     element={<Analytics />} />
                  <Route path="*"             element={<Navigate to="/demo" replace />} />
                </Routes>
              </Layout>
            </Protected>
          } />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
