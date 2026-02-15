/**
 * VendeFlow - Navbar
 * ==================
 * 
 * Barra de navegación superior.
 * Muestra diferentes opciones según si el usuario está autenticado o no.
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
                {/* Links de navegación */}
                <Link 
                  to="/dashboard" 
                  className="text-gray-600 hover:text-primary-500 transition-colors"
                >
                  Dashboard
                </Link>
                <Link 
                  to="/inventory" 
                  className="text-gray-600 hover:text-primary-500 transition-colors"
                >
                  Inventario
                </Link>
                <Link 
                  to="/import" 
                  className="text-gray-600 hover:text-primary-500 transition-colors"
                >
                  Importar
                </Link>
                
                {/* Separador */}
                <div className="h-6 w-px bg-gray-300"></div>
                
                {/* Usuario */}
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
