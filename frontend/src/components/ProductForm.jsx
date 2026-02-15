/**
 * VendeFlow - Formulario de Producto
 * ===================================
 * 
 * Modal para crear o editar un producto.
 * 
 * PROPS:
 * - product: Si existe, es modo edición. Si es null, es modo creación.
 * - onClose: Función para cerrar el modal
 * - onSuccess: Función que se llama al guardar exitosamente
 * 
 * CONCEPTOS DE TAILWIND:
 * - fixed inset-0: Cubre toda la pantalla (para el overlay)
 * - z-50: Asegura que esté encima de todo
 * - max-w-2xl: Ancho máximo del modal
 * - overflow-y-auto: Scroll si el contenido es muy largo
 */

import { useState, useEffect } from 'react'
import { inventoryService } from '../services/api'

function ProductForm({ product, onClose, onSuccess }) {
  // ═══════════════════════════════════════════════════════════
  // ESTADO
  // ═══════════════════════════════════════════════════════════
  
  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    description: '',
    price: '',
    cost: '',
    quantity: '',
    min_stock: '5',
    category: '',
    brand: '',
    image_url: ''
  })
  
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Determinar si es modo edición
  const isEditing = !!product
  
  // ═══════════════════════════════════════════════════════════
  // CARGAR DATOS SI ES EDICIÓN
  // ═══════════════════════════════════════════════════════════
  
  useEffect(() => {
    if (product) {
      setFormData({
        sku: product.sku || '',
        name: product.name || '',
        description: product.description || '',
        price: product.price?.toString() || '',
        cost: product.cost?.toString() || '',
        quantity: product.quantity?.toString() || '',
        min_stock: product.min_stock?.toString() || '5',
        category: product.category || '',
        brand: product.brand || '',
        image_url: product.image_url || ''
      })
    }
  }, [product])
  
  // ═══════════════════════════════════════════════════════════
  // HANDLERS
  // ═══════════════════════════════════════════════════════════
  
  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    if (error) setError(null)
  }
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)
    
    try {
      // Preparar datos (convertir strings a números)
      const dataToSend = {
        sku: formData.sku.trim(),
        name: formData.name.trim(),
        description: formData.description.trim() || null,
        price: parseFloat(formData.price) || 0,
        cost: formData.cost ? parseFloat(formData.cost) : null,
        quantity: parseInt(formData.quantity) || 0,
        min_stock: parseInt(formData.min_stock) || 5,
        category: formData.category.trim() || null,
        brand: formData.brand.trim() || null,
        image_url: formData.image_url.trim() || null
      }
      
      if (isEditing) {
        await inventoryService.update(product.id, dataToSend)
      } else {
        await inventoryService.create(dataToSend)
      }
      
      onSuccess()
      
    } catch (err) {
      setError(err.message || 'Error al guardar el producto')
    } finally {
      setIsLoading(false)
    }
  }
  
  // ═══════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════
  
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Overlay oscuro */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              {isEditing ? 'Editar Producto' : 'Nuevo Producto'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {/* Formulario */}
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Error */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}
            
            {/* Fila 1: SKU y Nombre */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  SKU *
                </label>
                <input
                  type="text"
                  name="sku"
                  value={formData.sku}
                  onChange={handleChange}
                  required
                  placeholder="PROD-001"
                  className="input-field font-mono uppercase"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Código único del producto
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  placeholder="Nombre del producto"
                  className="input-field"
                />
              </div>
            </div>
            
            {/* Descripción */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Descripción
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={3}
                placeholder="Descripción del producto..."
                className="input-field resize-none"
              />
            </div>
            
            {/* Fila 2: Precio y Costo */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Precio de Venta *
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-gray-500">$</span>
                  <input
                    type="number"
                    name="price"
                    value={formData.price}
                    onChange={handleChange}
                    required
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                    className="input-field pl-7"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Costo
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-gray-500">$</span>
                  <input
                    type="number"
                    name="cost"
                    value={formData.cost}
                    onChange={handleChange}
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                    className="input-field pl-7"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Opcional, para calcular margen
                </p>
              </div>
            </div>
            
            {/* Fila 3: Cantidad y Stock mínimo */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cantidad en Stock
                </label>
                <input
                  type="number"
                  name="quantity"
                  value={formData.quantity}
                  onChange={handleChange}
                  min="0"
                  placeholder="0"
                  className="input-field"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Stock Mínimo (alerta)
                </label>
                <input
                  type="number"
                  name="min_stock"
                  value={formData.min_stock}
                  onChange={handleChange}
                  min="0"
                  placeholder="5"
                  className="input-field"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Te alertaremos cuando llegue a este nivel
                </p>
              </div>
            </div>
            
            {/* Fila 4: Categoría y Marca */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Categoría
                </label>
                <input
                  type="text"
                  name="category"
                  value={formData.category}
                  onChange={handleChange}
                  placeholder="Ej: Electrónicos"
                  className="input-field"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Marca
                </label>
                <input
                  type="text"
                  name="brand"
                  value={formData.brand}
                  onChange={handleChange}
                  placeholder="Ej: Samsung"
                  className="input-field"
                />
              </div>
            </div>
            
            {/* URL de imagen */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                URL de Imagen
              </label>
              <input
                type="url"
                name="image_url"
                value={formData.image_url}
                onChange={handleChange}
                placeholder="https://ejemplo.com/imagen.jpg"
                className="input-field"
              />
            </div>
            
            {/* Botones */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <button
                type="button"
                onClick={onClose}
                className="btn-secondary"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary disabled:opacity-50"
              >
                {isLoading ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Guardando...
                  </span>
                ) : (
                  isEditing ? 'Guardar Cambios' : 'Crear Producto'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default ProductForm
