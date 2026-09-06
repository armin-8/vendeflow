/**
 * VendeFlow - Servicio de API
 * ============================
 * Centraliza todas las llamadas HTTP al backend.
 */

const API_URL = import.meta.env.VITE_API_URL || '/api'

async function request(endpoint, options = {}) {
  const authData = JSON.parse(localStorage.getItem('vendeflow-auth') || '{}')
  const token = authData?.state?.token
  const headers = { ...options.headers }
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const response = await fetch(`${API_URL}${endpoint}`, { ...options, headers })
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.error || 'Error en la petición')
  }
  return data
}

export const authService = {
  register: async (userData) => request('/auth/register', { method: 'POST', body: JSON.stringify(userData) }),
  login: async (credentials) => request('/auth/login', { method: 'POST', body: JSON.stringify(credentials) }),
  getMe: async () => request('/auth/me'),
  updateProfile: async (data) => request('/auth/me', { method: 'PUT', body: JSON.stringify(data) })
}

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
  getById: async (productId) => request(`/inventory/${productId}`),
  create: async (productData) => request('/inventory', { method: 'POST', body: JSON.stringify(productData) }),
  update: async (productId, productData) => request(`/inventory/${productId}`, { method: 'PUT', body: JSON.stringify(productData) }),
  delete: async (productId) => request(`/inventory/${productId}`, { method: 'DELETE' }),
  getStats: async () => request('/inventory/stats')
}

export const shopifyService = {
  getStatus: async () => request('/shopify/status'),
  connect: async (shopName) => request(`/shopify/connect?shop=${encodeURIComponent(shopName)}`),
  disconnect: async () => request('/shopify/disconnect', { method: 'DELETE' }),
  getProducts: async () => request('/shopify/products'),
  importProducts: async (updateExisting = true) => request('/shopify/import', { method: 'POST', body: JSON.stringify({ update_existing: updateExisting }) }),
  syncInventory: async () => request('/shopify/sync', { method: 'POST' }),
  syncBySku: async (sku) => request('/shopify/sync', { method: 'POST', body: JSON.stringify({ sku }) }),

  /**
   * Crear producto en Shopify desde el contenido generado por la IA.
   * El producto se crea como BORRADOR (draft) para que el usuario
   * lo revise en el admin de Shopify antes de publicarlo.
   */
  createProduct: async (productData) => request('/shopify/create-product', { method: 'POST', body: JSON.stringify(productData) })
}

export const mercadoLibreService = {
  getStatus: async () => request('/mercadolibre/status'),
  connect: async () => request('/mercadolibre/connect'),
  disconnect: async () => request('/mercadolibre/disconnect', { method: 'DELETE' }),
  getProducts: async () => request('/mercadolibre/products'),
  importProducts: async (updateExisting = true) => request('/mercadolibre/import', { method: 'POST', body: JSON.stringify({ update_existing: updateExisting }) }),
  syncInventory: async () => request('/mercadolibre/sync', { method: 'POST' }),
  syncBySku: async (sku) => request('/mercadolibre/sync', { method: 'POST', body: JSON.stringify({ sku }) }),

  /**
   * Publicar en Mercado Libre desde el contenido generado por la IA.
   * La publicación queda PAUSADA (ML no tiene borradores) para que el
   * usuario la revise antes de que sea visible al público.
   * La categoría se deduce sola del título: no se pide.
   */
  createProduct: async (productData) => request('/mercadolibre/create-product', { method: 'POST', body: JSON.stringify(productData) })
}

export const aiService = {
  getStatus: async () => request('/ai/status'),
  generateListing: async (data) => request('/ai/generate-listing', { method: 'POST', body: JSON.stringify(data) }),
  improveDescription: async (data) => request('/ai/improve-description', { method: 'POST', body: JSON.stringify(data) })
}

export const importService = {
  preview: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request('/import/preview', { method: 'POST', body: formData })
  },
  /**
   * Confirma la importación.
   * Los productos van en el body: son los mismos que devolvió preview().
   */
  confirm: async (products, updateExisting = false) => request('/import/confirm', {
    method: 'POST',
    body: JSON.stringify({ products, update_existing: updateExisting })
  }),
  getTemplate: async () => request('/import/template')
}
