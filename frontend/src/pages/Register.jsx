/**
 * VendeFlow - Página de Registro
 * ==============================
 * 
 * Formulario para crear una nueva cuenta.
 */

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store'
import { authService } from '../services/api'

function Register() {
  // Estado local del formulario
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    company_name: '',
    phone: ''
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  // Zustand store
  const { login } = useAuthStore()
  
  // Navegación
  const navigate = useNavigate()
  
  // Manejar cambios en inputs
  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    if (error) setError('')
  }
  
  // Manejar envío del formulario
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    
    // Validar que las contraseñas coincidan
    if (formData.password !== formData.confirmPassword) {
      setError('Las contraseñas no coinciden')
      return
    }
    
    // Validar longitud de contraseña
    if (formData.password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres')
      return
    }
    
    setIsLoading(true)
    
    try {
      // Preparar datos (sin confirmPassword)
      const { confirmPassword, ...userData } = formData
      
      // Llamar al servicio de API
      const response = await authService.register(userData)
      
      // Guardar en el store
      login(response.token, response.user)
      
      // Redirigir al dashboard
      navigate('/dashboard')
      
    } catch (err) {
      setError(err.message || 'Error al crear la cuenta')
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
            Crea tu cuenta
          </h1>
          <p className="text-gray-600 mt-2">
            Empieza a gestionar tu inventario hoy
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
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Nombre y Apellido en una fila */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label 
                  htmlFor="first_name" 
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Nombre *
                </label>
                <input
                  id="first_name"
                  name="first_name"
                  type="text"
                  required
                  value={formData.first_name}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="Juan"
                />
              </div>
              <div>
                <label 
                  htmlFor="last_name" 
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Apellido *
                </label>
                <input
                  id="last_name"
                  name="last_name"
                  type="text"
                  required
                  value={formData.last_name}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="Pérez"
                />
              </div>
            </div>
            
            {/* Email */}
            <div>
              <label 
                htmlFor="email" 
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Email *
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
            
            {/* Empresa (opcional) */}
            <div>
              <label 
                htmlFor="company_name" 
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Empresa <span className="text-gray-400">(opcional)</span>
              </label>
              <input
                id="company_name"
                name="company_name"
                type="text"
                value={formData.company_name}
                onChange={handleChange}
                className="input-field"
                placeholder="Mi Empresa S.A."
              />
            </div>
            
            {/* Teléfono (opcional) */}
            <div>
              <label 
                htmlFor="phone" 
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Teléfono <span className="text-gray-400">(opcional)</span>
              </label>
              <input
                id="phone"
                name="phone"
                type="tel"
                value={formData.phone}
                onChange={handleChange}
                className="input-field"
                placeholder="+52 123 456 7890"
              />
            </div>
            
            {/* Contraseñas */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label 
                  htmlFor="password" 
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Contraseña *
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
              <div>
                <label 
                  htmlFor="confirmPassword" 
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Confirmar *
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  required
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="••••••••"
                />
              </div>
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
                  Creando cuenta...
                </span>
              ) : (
                'Crear Cuenta'
              )}
            </button>
          </form>
          
          {/* Link a login */}
          <p className="text-center text-gray-600 mt-6">
            ¿Ya tienes cuenta?{' '}
            <Link to="/login" className="text-primary-500 hover:text-primary-600 font-medium">
              Inicia sesión
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Register
