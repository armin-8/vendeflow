/**
 * VendeFlow - Página de Inventario
 * =================================
 * 
 * Página principal para gestionar productos.
 * Muestra: estadísticas, tabla de productos, botón de agregar.
 * 
 * CONCEPTOS DE REACT QUE USAMOS:
 * - useState: Para manejar estado local (productos, loading, etc.)
 * - useEffect: Para cargar datos al montar el componente
 * - Conditional rendering: Mostrar loading, error, o datos
 */

import { useState, useEffect } from 'react'
import { inventoryService } from '../services/api'
import ProductTable from '../components/ProductTable'
import ProductForm from '../components/ProductForm'

function Inventory() {
  // ═══════════════════════════════════════════════════════════
  // ESTADO
  // ═══════════════════════════════════════════════════════════
  
  const [products, setProducts] = useState([])
  const [stats, setStats] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Paginación
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  
  // Filtros
  const [search, setSearch] = useState('')
  const [showLowStock, setShowLowStock] = useState(false)
  
  // Modal de formulario
  const [showForm, setShowForm] = useState(false)
  const [editingProduct, setEditingProduct] = useState(null)
  
  // ═══════════════════════════════════════════════════════════
  // CARGAR DATOS
  // ═══════════════════════════════════════════════════════════
  
  // Cargar productos
  const loadProducts = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const response = await inventoryService.getAll({
        page,
        per_page: 20,
        search: search || undefined,
        low_stock: showLowStock || undefined
      })
      
      setProducts(response.products)
      setTotalPages(response.pages)
      
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }
  
  // Cargar estadísticas
  const loadStats = async () => {
    try {
      const response = await inventoryService.getStats()
      setStats(response.stats)
    } catch (err) {
      console.error('Error cargando stats:', err)
    }
  }
  
  // Cargar al montar y cuando cambien filtros
  useEffect(() => {
    loadProducts()
  }, [page, search, showLowStock])
  
  useEffect(() => {
    loadStats()
  }, [])
  
  // ═══════════════════════════════════════════════════════════
  // HANDLERS
  // ═══════════════════════════════════════════════════════════
  
  // Buscar (con debounce simple)
  const handleSearch = (e) => {
    setSearch(e.target.value)
    setPage(1) // Resetear a página 1
  }
  
  // Abrir formulario para crear
  const handleCreate = () => {
    setEditingProduct(null)
    setShowForm(true)
  }
  
  // Abrir formulario para editar
  const handleEdit = (product) => {
    setEditingProduct(product)
    setShowForm(true)
  }
  
  // Cerrar formulario
  const handleCloseForm = () => {
    setShowForm(false)
    setEditingProduct(null)
  }
  
  // Después de guardar producto
  const handleSaveSuccess = () => {
    handleCloseForm()
    loadProducts()
    loadStats()
  }
  
  // Eliminar producto
  const handleDelete = async (productId) => {
    if (!confirm('¿Estás seguro de eliminar este producto?')) {
      return
    }
    
    try {
      await inventoryService.delete(productId)
      loadProducts()
      loadStats()
    } catch (err) {
      alert('Error al eliminar: ' + err.message)
    }
  }
  
  // ═══════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════
  
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Encabezado */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Inventario</h1>
          <p className="text-gray-600 mt-1">Gestiona tus productos</p>
        </div>
        <button
          onClick={handleCreate}
          className="mt-4 md:mt-0 btn-primary flex items-center"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Agregar Producto
        </button>
      </div>
      
      {/* Tarjetas de estadísticas */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="card">
            <p className="text-gray-500 text-sm">Total Productos</p>
            <p className="text-2xl font-bold">{stats.total_products}</p>
          </div>
          <div className="card">
            <p className="text-gray-500 text-sm">Stock Bajo</p>
            <p className="text-2xl font-bold text-yellow-600">{stats.low_stock_count}</p>
          </div>
          <div className="card">
            <p className="text-gray-500 text-sm">Sin Stock</p>
            <p className="text-2xl font-bold text-red-600">{stats.out_of_stock}</p>
          </div>
          <div className="card">
            <p className="text-gray-500 text-sm">Valor Total</p>
            <p className="text-2xl font-bold text-green-600">
              ${stats.total_value?.toLocaleString()}
            </p>
          </div>
        </div>
      )}
      
      {/* Filtros */}
      <div className="card mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Búsqueda */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Buscar por nombre o SKU..."
              value={search}
              onChange={handleSearch}
              className="input-field"
            />
          </div>
          
          {/* Filtro stock bajo */}
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={showLowStock}
              onChange={(e) => {
                setShowLowStock(e.target.checked)
                setPage(1)
              }}
              className="w-4 h-4 text-primary-500 rounded focus:ring-primary-500"
            />
            <span className="ml-2 text-gray-700">Solo stock bajo</span>
          </label>
        </div>
      </div>
      
      {/* Contenido principal */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
          <p className="text-gray-500 mt-4">Cargando productos...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      ) : products.length === 0 ? (
        <div className="card text-center py-12">
          <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900">No hay productos</h3>
          <p className="text-gray-500 mt-1">
            {search ? 'No se encontraron productos con ese criterio' : 'Comienza agregando tu primer producto'}
          </p>
          {!search && (
            <button onClick={handleCreate} className="btn-primary mt-4">
              Agregar Producto
            </button>
          )}
        </div>
      ) : (
        <>
          {/* Tabla de productos */}
          <ProductTable
            products={products}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
          
          {/* Paginación */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-6">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Anterior
              </button>
              <span className="px-4 py-2">
                Página {page} de {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Siguiente
              </button>
            </div>
          )}
        </>
      )}
      
      {/* Modal del formulario */}
      {showForm && (
        <ProductForm
          product={editingProduct}
          onClose={handleCloseForm}
          onSuccess={handleSaveSuccess}
        />
      )}
    </div>
  )
}

export default Inventory
