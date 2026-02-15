/**
 * VendeFlow - Dashboard
 * =====================
 * 
 * Panel principal después del login.
 * Muestra estadísticas y accesos rápidos.
 */

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../store'
import { inventoryService } from '../services/api'

function Dashboard() {
  const { user } = useAuthStore()
  const [stats, setStats] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  
  // Cargar estadísticas al montar
  useEffect(() => {
    const loadStats = async () => {
      try {
        const response = await inventoryService.getStats()
        setStats(response.stats)
      } catch (err) {
        console.error('Error cargando stats:', err)
      } finally {
        setIsLoading(false)
      }
    }
    
    loadStats()
  }, [])
  
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Encabezado de bienvenida */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          ¡Hola, {user?.first_name}! 👋
        </h1>
        <p className="text-gray-600 mt-2">
          Bienvenido a tu panel de VendeFlow
        </p>
      </div>
      
      {/* Cards de estadísticas */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
        {/* Productos */}
        <div className="card">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mr-4">
              <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            </div>
            <div>
              <p className="text-gray-500 text-sm">Productos</p>
              <p className="text-2xl font-bold">
                {isLoading ? '-' : stats?.total_products || 0}
              </p>
            </div>
          </div>
        </div>
        
        {/* Stock Bajo */}
        <div className="card">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mr-4">
              <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div>
              <p className="text-gray-500 text-sm">Stock Bajo</p>
              <p className="text-2xl font-bold text-yellow-600">
                {isLoading ? '-' : stats?.low_stock_count || 0}
              </p>
            </div>
          </div>
        </div>
        
        {/* Sin Stock */}
        <div className="card">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mr-4">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
            </div>
            <div>
              <p className="text-gray-500 text-sm">Sin Stock</p>
              <p className="text-2xl font-bold text-red-600">
                {isLoading ? '-' : stats?.out_of_stock || 0}
              </p>
            </div>
          </div>
        </div>
        
        {/* Valor Total */}
        <div className="card">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mr-4">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-gray-500 text-sm">Valor Total</p>
              <p className="text-2xl font-bold text-green-600">
                ${isLoading ? '-' : (stats?.total_value?.toLocaleString() || 0)}
              </p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Acciones rápidas */}
      <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-xl p-8 text-white">
        <h2 className="text-2xl font-bold mb-4">
          🚀 Acciones Rápidas
        </h2>
        <p className="text-primary-100 mb-6 max-w-2xl">
          Gestiona tu inventario y mantén todo sincronizado.
        </p>
        <div className="flex flex-wrap gap-4">
          <Link 
            to="/inventory"
            className="bg-white text-primary-600 px-6 py-2 rounded-lg font-medium hover:bg-primary-50 transition-colors"
          >
            Ver Inventario
          </Link>
          <Link 
            to="/inventory"
            className="border-2 border-white text-white px-6 py-2 rounded-lg font-medium hover:bg-white hover:text-primary-600 transition-colors"
          >
            + Agregar Producto
          </Link>
        </div>
      </div>
      
      {/* Información de plataformas */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Plataformas Conectadas</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Shopify */}
          <div className="card flex items-center justify-between">
            <div className="flex items-center">
              <span className="text-2xl mr-3">🛒</span>
              <div>
                <p className="font-medium">Shopify</p>
                <p className="text-sm text-gray-500">Próximamente</p>
              </div>
            </div>
            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
              Pendiente
            </span>
          </div>
          
          {/* Amazon */}
          <div className="card flex items-center justify-between">
            <div className="flex items-center">
              <span className="text-2xl mr-3">📦</span>
              <div>
                <p className="font-medium">Amazon</p>
                <p className="text-sm text-gray-500">Próximamente</p>
              </div>
            </div>
            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
              Pendiente
            </span>
          </div>
          
          {/* Mercado Libre */}
          <div className="card flex items-center justify-between">
            <div className="flex items-center">
              <span className="text-2xl mr-3">🤝</span>
              <div>
                <p className="font-medium">Mercado Libre</p>
                <p className="text-sm text-gray-500">Próximamente</p>
              </div>
            </div>
            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
              Pendiente
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
