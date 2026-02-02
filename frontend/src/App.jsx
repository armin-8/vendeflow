/**
 * VendeFlow - Componente Principal
 * =================================
 * 
 * Define la estructura general de la aplicación y las rutas.
 */

import { Routes, Route } from 'react-router-dom'

// Layout
import Layout from './components/Layout'

// Páginas
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import NotFound from './pages/NotFound'

// Componente de ruta protegida
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <Routes>
      {/* Rutas públicas */}
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
        
        {/* Rutas protegidas (requieren autenticación) */}
        <Route element={<ProtectedRoute />}>
          <Route path="dashboard" element={<Dashboard />} />
          {/* Aquí agregaremos más rutas protegidas */}
        </Route>
        
        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}

export default App
