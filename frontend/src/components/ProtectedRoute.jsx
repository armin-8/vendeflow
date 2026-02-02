/**
 * VendeFlow - Ruta Protegida
 * ==========================
 * 
 * Componente que protege rutas que requieren autenticación.
 * Si el usuario no está autenticado, lo redirige al login.
 * 
 * USO:
 * ----
 * <Route element={<ProtectedRoute />}>
 *   <Route path="dashboard" element={<Dashboard />} />
 * </Route>
 */

import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store'

function ProtectedRoute() {
  const { isAuthenticated } = useAuthStore()
  const location = useLocation()
  
  // Si no está autenticado, redirigir a login
  // Guardamos la ubicación actual para redirigir después del login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  
  // Si está autenticado, renderizar la ruta hija
  return <Outlet />
}

export default ProtectedRoute
