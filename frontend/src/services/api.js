/**
 * VendeFlow - Servicio de API
 * ============================
 * 
 * Centraliza todas las llamadas HTTP al backend.
 * 
 * DIFERENCIA CON REVÍSTETE:
 * -------------------------
 * En Revístete, las llamadas fetch estaban dispersas en cada componente.
 * Aquí las centralizamos para:
 * - Reutilizar código
 * - Manejar errores en un solo lugar
 * - Agregar el token automáticamente
 */

// URL base del backend
const API_URL = import.meta.env.VITE_API_URL || '/api'

/**
 * Función base para hacer requests HTTP.
 * Agrega automáticamente el token si existe.
 */
async function request(endpoint, options = {}) {
  // Obtener token del localStorage (Zustand lo guarda ahí)
  const authData = JSON.parse(localStorage.getItem('vendeflow-auth') || '{}')
  const token = authData?.state?.token
  
  // Configurar headers
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  }
  
  // Agregar token si existe
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  // Hacer la petición
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers
  })
  
  // Parsear respuesta
  const data = await response.json()
  
  // Si hay error, lanzar excepción
  if (!response.ok) {
    throw new Error(data.error || 'Error en la petición')
  }
  
  return data
}

// ═══════════════════════════════════════════════════════════
// SERVICIOS DE AUTENTICACIÓN
// ═══════════════════════════════════════════════════════════

export const authService = {
  /**
   * Registrar nuevo usuario.
   */
  register: async (userData) => {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    })
  },
  
  /**
   * Iniciar sesión.
   */
  login: async (credentials) => {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    })
  },
  
  /**
   * Obtener datos del usuario actual.
   */
  getMe: async () => {
    return request('/auth/me')
  },
  
  /**
   * Actualizar perfil.
   */
  updateProfile: async (data) => {
    return request('/auth/me', {
      method: 'PUT',
      body: JSON.stringify(data)
    })
  }
}

// ═══════════════════════════════════════════════════════════
// SERVICIOS DE INVENTARIO (para después)
// ═══════════════════════════════════════════════════════════

export const inventoryService = {
  /**
   * Obtener todos los productos.
   */
  getAll: async () => {
    return request('/inventory')
  },
  
  // Aquí agregaremos más métodos...
}
