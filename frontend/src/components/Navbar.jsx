/**
 * VendeFlow - Navbar
 * ==================
 * 
 * Barra de navegación superior.
 * Muestra diferentes opciones según si el usuario está autenticado o no.
 * 
 * AQUÍ APRENDERÁS TAILWIND:
 * -------------------------
 * Fíjate en las clases CSS y te explico las más importantes:
 * 
 * - bg-white        → Fondo blanco
 * - shadow-md       → Sombra mediana
 * - px-4            → Padding horizontal de 1rem (16px)
 * - py-3            → Padding vertical de 0.75rem (12px)
 * - flex            → Display flex
 * - items-center    → Alinear items al centro (vertical)
 * - justify-between → Espacio entre elementos
 * - hover:bg-gray-100 → Al hacer hover, fondo gris claro
 * - rounded-lg      → Bordes redondeados
 */

import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store'

function Navbar() {
  const { isAuthenticated, user, logout } = useAuthStore()
  const navigate = useNavigate()
  
  const handleLogout = () => {
    logout()
    navigate('/login')
  }
  
  return (
    <nav className="bg-white shadow-md sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            {/* Icono simple con SVG */}
            <svg 
              className="w-8 h-8 text-primary-500" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M13 10V3L4 14h7v7l9-11h-7z" 
              />
            </svg>
            <span className="text-xl font-bold text-gray-800">
              Vende<span className="text-primary-500">Flow</span>
            </span>
          </Link>
          
          {/* Menú de navegación */}
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                {/* Usuario autenticado */}
                <Link 
                  to="/dashboard" 
                  className="text-gray-600 hover:text-primary-500 transition-colors"
                >
                  Dashboard
                </Link>
                
                {/* Dropdown de usuario (simplificado) */}
                <div className="flex items-center space-x-3">
                  <span className="text-gray-700">
                    Hola, <strong>{user?.first_name}</strong>
                  </span>
                  <button
                    onClick={handleLogout}
                    className="text-gray-600 hover:text-red-500 transition-colors"
                  >
                    Salir
                  </button>
                </div>
              </>
            ) : (
              <>
                {/* Usuario no autenticado */}
                <Link 
                  to="/login" 
                  className="text-gray-600 hover:text-primary-500 transition-colors"
                >
                  Iniciar Sesión
                </Link>
                <Link 
                  to="/register" 
                  className="btn-primary"
                >
                  Registrarse
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
