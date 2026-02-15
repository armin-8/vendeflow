/**
 * VendeFlow - Navbar Responsive
 * ==============================
 * 
 * Barra de navegación que se adapta a móvil y desktop.
 * 
 * CONCEPTOS DE TAILWIND RESPONSIVE:
 * ----------------------------------
 * Tailwind usa "mobile-first", significa que:
 * - Las clases sin prefijo aplican a móvil
 * - md: aplica desde 768px (tablet/desktop)
 * - lg: aplica desde 1024px (desktop grande)
 * 
 * EJEMPLOS:
 * - "hidden md:flex" = oculto en móvil, visible en desktop
 * - "flex md:hidden" = visible en móvil, oculto en desktop
 * 
 * ESTRUCTURA:
 * -----------
 * - Móvil: Logo + botón hamburguesa + menú desplegable
 * - Desktop: Logo + links horizontales + usuario
 */

import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store'

function Navbar() {
  // ═══════════════════════════════════════════════════════════
  // ESTADO Y HOOKS
  // ═══════════════════════════════════════════════════════════
  
  const { isAuthenticated, user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation() // Para saber qué página está activa
  
  // Estado para el menú móvil (abierto/cerrado)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  
  // ═══════════════════════════════════════════════════════════
  // HANDLERS
  // ═══════════════════════════════════════════════════════════
  
  const handleLogout = () => {
    logout()
    setIsMobileMenuOpen(false)
    navigate('/login')
  }
  
  // Cerrar menú al navegar
  const handleNavClick = () => {
    setIsMobileMenuOpen(false)
  }
  
  // Toggle menú móvil
  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen)
  }
  
  // Verificar si un link está activo
  const isActive = (path) => {
    return location.pathname === path
  }
  
  // ═══════════════════════════════════════════════════════════
  // ESTILOS DE LINKS
  // ═══════════════════════════════════════════════════════════
  
  // Estilo base para links de desktop
  const linkStyle = (path) => `
    transition-colors duration-200
    ${isActive(path) 
      ? 'text-primary-600 font-medium' 
      : 'text-gray-600 hover:text-primary-500'
    }
  `
  
  // Estilo para links del menú móvil
  const mobileLinkStyle = (path) => `
    block px-4 py-3 text-base transition-colors duration-200
    ${isActive(path)
      ? 'text-primary-600 bg-primary-50 font-medium'
      : 'text-gray-600 hover:bg-gray-50 hover:text-primary-500'
    }
  `
  
  // ═══════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════
  
  return (
    <nav className="bg-white shadow-md sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          
          {/* ════════════════════════════════════════════════════
              LOGO (visible siempre)
              ════════════════════════════════════════════════════ */}
          <Link 
            to="/" 
            className="flex items-center space-x-2"
            onClick={handleNavClick}
          >
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
          
          {/* ════════════════════════════════════════════════════
              MENÚ DESKTOP (oculto en móvil, visible desde md:)
              ════════════════════════════════════════════════════ */}
          <div className="hidden md:flex items-center space-x-6">
            {isAuthenticated ? (
              <>
                {/* Links de navegación */}
                <Link to="/dashboard" className={linkStyle('/dashboard')}>
                  Dashboard
                </Link>
                <Link to="/inventory" className={linkStyle('/inventory')}>
                  Inventario
                </Link>
                <Link to="/import" className={linkStyle('/import')}>
                  Importar
                </Link>
                
                {/* Separador vertical */}
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
                <Link to="/login" className={linkStyle('/login')}>
                  Iniciar Sesión
                </Link>
                <Link to="/register" className="btn-primary">
                  Registrarse
                </Link>
              </>
            )}
          </div>
          
          {/* ════════════════════════════════════════════════════
              BOTÓN HAMBURGUESA (visible en móvil, oculto desde md:)
              ════════════════════════════════════════════════════ */}
          <button
            onClick={toggleMobileMenu}
            className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
            aria-label="Abrir menú"
          >
            {/* Icono hamburguesa o X dependiendo del estado */}
            {isMobileMenuOpen ? (
              // Icono X (cerrar)
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              // Icono hamburguesa (abrir)
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>
      </div>
      
      {/* ════════════════════════════════════════════════════════
          MENÚ MÓVIL DESPLEGABLE
          
          - Solo se muestra cuando isMobileMenuOpen es true
          - Solo existe en móvil (md:hidden)
          - Tiene animación de entrada
          ════════════════════════════════════════════════════════ */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t bg-white">
          {isAuthenticated ? (
            <div className="py-2">
              {/* Info del usuario */}
              <div className="px-4 py-3 border-b bg-gray-50">
                <p className="text-sm text-gray-500">Sesión iniciada como</p>
                <p className="font-medium text-gray-900">{user?.first_name} {user?.last_name}</p>
                <p className="text-sm text-gray-500">{user?.email}</p>
              </div>
              
              {/* Links de navegación */}
              <Link 
                to="/dashboard" 
                className={mobileLinkStyle('/dashboard')}
                onClick={handleNavClick}
              >
                <span className="flex items-center">
                  <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                  Dashboard
                </span>
              </Link>
              
              <Link 
                to="/inventory" 
                className={mobileLinkStyle('/inventory')}
                onClick={handleNavClick}
              >
                <span className="flex items-center">
                  <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                  Inventario
                </span>
              </Link>
              
              <Link 
                to="/import" 
                className={mobileLinkStyle('/import')}
                onClick={handleNavClick}
              >
                <span className="flex items-center">
                  <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Importar
                </span>
              </Link>
              
              {/* Separador */}
              <div className="my-2 border-t"></div>
              
              {/* Botón de salir */}
              <button
                onClick={handleLogout}
                className="w-full text-left px-4 py-3 text-red-600 hover:bg-red-50 transition-colors flex items-center"
              >
                <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Cerrar Sesión
              </button>
            </div>
          ) : (
            <div className="py-2">
              {/* Usuario no autenticado */}
              <Link 
                to="/login" 
                className={mobileLinkStyle('/login')}
                onClick={handleNavClick}
              >
                Iniciar Sesión
              </Link>
              <Link 
                to="/register" 
                className={mobileLinkStyle('/register')}
                onClick={handleNavClick}
              >
                Registrarse
              </Link>
            </div>
          )}
        </div>
      )}
    </nav>
  )
}

export default Navbar
