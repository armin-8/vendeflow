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
    ...options.headers
  }
  
  // Solo agregar Content-Type si no es FormData
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
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
  register: async (userData) => {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    })
  },
  
  login: async (credentials) => {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    })
  },
  
  getMe: async () => {
    return request('/auth/me')
  },
  
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
  getAll: async (params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.append('page', params.page)
    if (params.per_page) queryParams.append('per_page', params.per_page)
    if (params.search) queryParams.append('search', params.search)
    if (params.category) queryParams.append('category', params.category)
    if (params.low_stock) queryParams.append('low_stock', 'true')
    const queryString = queryParams.toString()
    return request(queryString ? `/inventory?${queryString}` : '/inventory')
  },
  
  getById: async (productId) => {
    return request(`/inventory/${productId}`)
  },
  
  create: async (productData) => {
    return request('/inventory', {
      method: 'POST',
      body: JSON.stringify(productData)
    })
  },
  
  update: async (productId, productData) => {
    return request(`/inventory/${productId}`, {
      method: 'PUT',
      body: JSON.stringify(productData)
    })
  },
  
  delete: async (productId) => {
    return request(`/inventory/${productId}`, {
      method: 'DELETE'
    })
  },
  
  getStats: async () => {
    return request('/inventory/stats')
  }
}

// ═══════════════════════════════════════════════════════════
// SERVICIOS DE SHOPIFY
// ═══════════════════════════════════════════════════════════

export const shopifyService = {
  getStatus: async () => {
    return request('/shopify/status')
  },
  
  connect: async (shopName) => {
    return request(`/shopify/connect?shop=${encodeURIComponent(shopName)}`)
  },
  
  disconnect: async () => {
    return request('/shopify/disconnect', { method: 'DELETE' })
  },
  
  getProducts: async () => {
    return request('/shopify/products')
  },
  
  importProducts: async (updateExisting = true) => {
    return request('/shopify/import', {
      method: 'POST',
      body: JSON.stringify({ update_existing: updateExisting })
    })
  },
  
  /**
   * Sincronizar inventario → Shopify.
   * Sin parámetros: sincroniza TODOS los productos vinculados.
   */
  syncInventory: async () => {
    return request('/shopify/sync', { method: 'POST' })
  },

  /**
   * Sincronizar UN solo SKU → Shopify.
   * 
   * ¿POR QUÉ ESTE MÉTODO SEPARADO?
   * --------------------------------
   * La fuente de verdad del inventario real es Odoo.
   * Sincronizar masivamente podría sobreescribir stock real con datos incorrectos.
   * Con syncBySku el usuario elige exactamente qué producto sincronizar.
   * 
   * @param {string} sku - SKU del producto a sincronizar
   */
  syncBySku: async (sku) => {
    return request('/shopify/sync', {
      method: 'POST',
      body: JSON.stringify({ sku })
    })
  }
}

// ═══════════════════════════════════════════════════════════
// SERVICIOS DE MERCADO LIBRE
// ═══════════════════════════════════════════════════════════

export const mercadoLibreService = {
  getStatus: async () => {
    return request('/mercadolibre/status')
  },

  connect: async () => {
    return request('/mercadolibre/connect')
  },

  disconnect: async () => {
    return request('/mercadolibre/disconnect', { method: 'DELETE' })
  },

  getProducts: async () => {
    return request('/mercadolibre/products')
  },

  importProducts: async (updateExisting = true) => {
    return request('/mercadolibre/import', {
      method: 'POST',
      body: JSON.stringify({ update_existing: updateExisting })
    })
  },

  /**
   * Sincronizar inventario → Mercado Libre.
   * Sin parámetros: sincroniza TODOS los productos vinculados.
   */
  syncInventory: async () => {
    return request('/mercadolibre/sync', { method: 'POST' })
  },

  /**
   * Sincronizar UN solo SKU → Mercado Libre.
   * Misma lógica que shopifyService.syncBySku.
   * 
   * @param {string} sku - SKU del producto a sincronizar
   */
  syncBySku: async (sku) => {
    return request('/mercadolibre/sync', {
      method: 'POST',
      body: JSON.stringify({ sku })
    })
  }
}

// ═══════════════════════════════════════════════════════════
// SERVICIOS DE IMPORTACIÓN
// ═══════════════════════════════════════════════════════════

export const importService = {
  preview: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request('/import/preview', {
      method: 'POST',
      body: formData
    })
  },
  
  confirm: async (updateExisting = false) => {
    return request('/import/confirm', {
      method: 'POST',
      body: JSON.stringify({ update_existing: updateExisting })
    })
  },
  
  getTemplate: async () => {
    return request('/import/template')
  }
}
