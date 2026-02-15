/**
 * VendeFlow - Servicio de API
 * ============================
 * 
 * Centraliza todas las llamadas HTTP al backend.
 * 
 * VENTAJAS DE CENTRALIZAR:
 * - El token se agrega automáticamente
 * - Manejo de errores en un solo lugar
 * - Fácil de mantener y actualizar
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
// SERVICIOS DE INVENTARIO
// ═══════════════════════════════════════════════════════════

export const inventoryService = {
  /**
   * Obtener todos los productos con paginación y filtros.
   * 
   * @param {Object} params - Parámetros de búsqueda
   * @param {number} params.page - Número de página
   * @param {number} params.per_page - Productos por página
   * @param {string} params.search - Buscar por nombre o SKU
   * @param {string} params.category - Filtrar por categoría
   * @param {boolean} params.low_stock - Solo productos con stock bajo
   */
  getAll: async (params = {}) => {
    // Construir query string
    const queryParams = new URLSearchParams()
    
    if (params.page) queryParams.append('page', params.page)
    if (params.per_page) queryParams.append('per_page', params.per_page)
    if (params.search) queryParams.append('search', params.search)
    if (params.category) queryParams.append('category', params.category)
    if (params.low_stock) queryParams.append('low_stock', 'true')
    
    const queryString = queryParams.toString()
    const endpoint = queryString ? `/inventory?${queryString}` : '/inventory'
    
    return request(endpoint)
  },
  
  /**
   * Obtener un producto por ID.
   */
  getById: async (productId) => {
    return request(`/inventory/${productId}`)
  },
  
  /**
   * Crear un nuevo producto.
   * 
   * @param {Object} productData - Datos del producto
   * @param {string} productData.sku - Código único
   * @param {string} productData.name - Nombre
   * @param {string} productData.description - Descripción
   * @param {number} productData.price - Precio de venta
   * @param {number} productData.cost - Costo
   * @param {number} productData.quantity - Cantidad en stock
   * @param {number} productData.min_stock - Stock mínimo para alerta
   * @param {string} productData.category - Categoría
   * @param {string} productData.brand - Marca
   */
  create: async (productData) => {
    return request('/inventory', {
      method: 'POST',
      body: JSON.stringify(productData)
    })
  },
  
  /**
   * Actualizar un producto existente.
   */
  update: async (productId, productData) => {
    return request(`/inventory/${productId}`, {
      method: 'PUT',
      body: JSON.stringify(productData)
    })
  },
  
  /**
   * Eliminar un producto.
   */
  delete: async (productId) => {
    return request(`/inventory/${productId}`, {
      method: 'DELETE'
    })
  },
  
  /**
   * Obtener estadísticas del inventario.
   */
  getStats: async () => {
    return request('/inventory/stats')
  }
}
