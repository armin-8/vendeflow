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
  // (FormData necesita que el navegador ponga el Content-Type automáticamente)
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
   */
  getAll: async (params = {}) => {
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

// ═══════════════════════════════════════════════════════════
// SERVICIOS DE SHOPIFY
// ═══════════════════════════════════════════════════════════

export const shopifyService = {
  /**
   * Obtener estado de conexión con Shopify.
   */
  getStatus: async () => {
    return request('/shopify/status')
  },
  
  /**
   * Iniciar conexión OAuth con Shopify.
   * @param {string} shopName - Nombre de la tienda (sin .myshopify.com)
   */
  connect: async (shopName) => {
    return request(`/shopify/connect?shop=${encodeURIComponent(shopName)}`)
  },
  
  /**
   * Desconectar tienda Shopify.
   */
  disconnect: async () => {
    return request('/shopify/disconnect', {
      method: 'DELETE'
    })
  },
  
  /**
   * Obtener productos de Shopify.
   */
  getProducts: async () => {
    return request('/shopify/products')
  },
  
  /**
   * Importar productos de Shopify a VendeFlow.
   */
  importProducts: async (updateExisting = true) => {
    return request('/shopify/import', {
      method: 'POST',
      body: JSON.stringify({ update_existing: updateExisting })
    })
  },
  
  /**
   * Sincronizar inventario de VendeFlow a Shopify.
   */
  syncInventory: async () => {
    return request('/shopify/sync', {
      method: 'POST'
    })
  }
}

// ═══════════════════════════════════════════════════════════
// SERVICIOS DE MERCADO LIBRE
// ═══════════════════════════════════════════════════════════
//
// ¿POR QUÉ connect() NO necesita parámetros?
// -------------------------------------------
// Shopify: cada usuario tiene su propio dominio (tu-tienda.myshopify.com)
//          → necesitamos el shop name para construir la URL de auth
//
// Mercado Libre: es una plataforma global, la URL de auth es siempre la misma
//          → el backend genera la URL directamente sin necesitar datos extra

export const mercadoLibreService = {
  /**
   * Obtener estado de conexión con Mercado Libre.
   */
  getStatus: async () => {
    return request('/mercadolibre/status')
  },

  /**
   * Iniciar conexión OAuth con Mercado Libre.
   * El backend genera la URL de autorización y la devuelve.
   * El frontend redirige al usuario a esa URL.
   */
  connect: async () => {
    return request('/mercadolibre/connect')
  },

  /**
   * Desconectar cuenta de Mercado Libre.
   */
  disconnect: async () => {
    return request('/mercadolibre/disconnect', {
      method: 'DELETE'
    })
  },

  /**
   * Obtener publicaciones del usuario en ML.
   */
  getProducts: async () => {
    return request('/mercadolibre/products')
  },

  /**
   * Importar publicaciones de ML al inventario de VendeFlow.
   * @param {boolean} updateExisting - Si true, actualiza productos que ya existen
   */
  importProducts: async (updateExisting = true) => {
    return request('/mercadolibre/import', {
      method: 'POST',
      body: JSON.stringify({ update_existing: updateExisting })
    })
  },

  /**
   * Sincronizar stock de VendeFlow → publicaciones de ML.
   * @param {string|null} sku - Si se pasa, solo sincroniza ese producto
   */
  syncInventory: async (sku = null) => {
    return request('/mercadolibre/sync', {
      method: 'POST',
      body: JSON.stringify(sku ? { sku } : {})
    })
  }
}

// ═══════════════════════════════════════════════════════════
// SERVICIOS DE IMPORTACIÓN
// ═══════════════════════════════════════════════════════════

export const importService = {
  /**
   * Subir archivo y obtener vista previa.
   * 
   * ¿QUÉ ES FormData?
   * -----------------
   * Es la forma de enviar archivos en JavaScript.
   * Es como un formulario HTML pero en código.
   * 
   * @param {File} file - Archivo seleccionado por el usuario
   * @returns {Promise} - Respuesta con productos leídos
   */
  preview: async (file) => {
    // Crear FormData y agregar el archivo
    const formData = new FormData()
    formData.append('file', file)
    
    return request('/import/preview', {
      method: 'POST',
      body: formData  // No usamos JSON.stringify con FormData
    })
  },
  
  /**
   * Confirmar importación y guardar productos.
   * 
   * @param {boolean} updateExisting - Si actualizar productos que ya existen
   * @returns {Promise} - Resultado de la importación
   */
  confirm: async (updateExisting = false) => {
    return request('/import/confirm', {
      method: 'POST',
      body: JSON.stringify({ update_existing: updateExisting })
    })
  },
  
  /**
   * Obtener información sobre las columnas esperadas.
   */
  getTemplate: async () => {
    return request('/import/template')
  }
}
