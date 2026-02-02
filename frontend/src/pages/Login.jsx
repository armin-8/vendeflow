/**
 * VendeFlow - Página de Login
 * ===========================
 * 
 * Formulario para iniciar sesión.
 * 
 * COMPARACIÓN CON REVÍSTETE:
 * --------------------------
 * - Usamos Zustand en lugar de dispatch
 * - El servicio de API está centralizado
 * - Tailwind en lugar de Bootstrap
 */

import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store'
import { authService } from '../services/api'

function Login() {
  // Estado local del formulario
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  // Zustand store
  const { login } = useAuthStore()
  
  // Navegación
  const navigate = useNavigate()
  const location = useLocation()
  
  // ¿De dónde venía el usuario? (para redirigir después del login)
  const from = location.state?.from?.pathname || '/dashboard'
  
  // Manejar cambios en inputs
  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    // Limpiar error al escribir
    if (error) setError('')
  }
  
  // Manejar envío del formulario
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    
    try {
      // Llamar al servicio de API
      const response = await authService.login(formData)
      
      // Guardar en el store
      login(response.token, response.user)
      
      // Redirigir
      navigate(from, { replace: true })
      
    } catch (err) {
      setError(err.message || 'Error al iniciar sesión')
    } finally {
      setIsLoading(false)
    }
  }
  
  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full">
        {/* Encabezado */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Bienvenido de nuevo
          </h1>
          <p className="text-gray-600 mt-2">
            Ingresa tus credenciales para acceder
          </p>
        </div>
        
        {/* Card del formulario */}
        <div className="card">
          {/* Mostrar error si existe */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}
          
          {/* Formulario */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email */}
            <div>
              <label 
                htmlFor="email" 
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleChange}
                className="input-field"
                placeholder="tu@email.com"
              />
            </div>
            
            {/* Password */}
            <div>
              <label 
                htmlFor="password" 
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Contraseña
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                className="input-field"
                placeholder="••••••••"
              />
            </div>
            
            {/* Botón de submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary py-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Ingresando...
                </span>
              ) : (
                'Iniciar Sesión'
              )}
            </button>
          </form>
          
          {/* Link a registro */}
          <p className="text-center text-gray-600 mt-6">
            ¿No tienes cuenta?{' '}
            <Link to="/register" className="text-primary-500 hover:text-primary-600 font-medium">
              Regístrate aquí
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login
