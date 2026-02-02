/**
 * VendeFlow - Dashboard
 * =====================
 * 
 * Panel principal después del login.
 * Por ahora es básico, lo expandiremos en las siguientes fases.
 */

import { useAuthStore } from '../store'

function Dashboard() {
  const { user } = useAuthStore()
  
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
      
      {/* Cards de estadísticas (placeholder) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
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
              <p className="text-2xl font-bold">0</p>
            </div>
          </div>
        </div>
        
        {/* Sincronizaciones */}
        <div className="card">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center mr-4">
              <svg className="w-6 h-6 text-secondary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
            <div>
              <p className="text-gray-500 text-sm">Sincronizaciones</p>
              <p className="text-2xl font-bold">0</p>
            </div>
          </div>
        </div>
        
        {/* Plataformas conectadas */}
        <div className="card">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mr-4">
              <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </div>
            <div>
              <p className="text-gray-500 text-sm">Plataformas</p>
              <p className="text-2xl font-bold">0/3</p>
            </div>
          </div>
        </div>
        
        {/* Alertas */}
        <div className="card">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mr-4">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div>
              <p className="text-gray-500 text-sm">Alertas</p>
              <p className="text-2xl font-bold">0</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Mensaje de bienvenida / Getting started */}
      <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-xl p-8 text-white">
        <h2 className="text-2xl font-bold mb-4">
          🚀 ¡Empecemos!
        </h2>
        <p className="text-primary-100 mb-6 max-w-2xl">
          Tu cuenta está lista. El siguiente paso es agregar tus productos y conectar tus plataformas de venta. 
          ¿Por dónde quieres empezar?
        </p>
        <div className="flex flex-wrap gap-4">
          <button className="bg-white text-primary-600 px-6 py-2 rounded-lg font-medium hover:bg-primary-50 transition-colors">
            + Agregar Productos
          </button>
          <button className="border-2 border-white text-white px-6 py-2 rounded-lg font-medium hover:bg-white hover:text-primary-600 transition-colors">
            Conectar Plataforma
          </button>
          <button className="border-2 border-white text-white px-6 py-2 rounded-lg font-medium hover:bg-white hover:text-primary-600 transition-colors">
            Importar desde Excel
          </button>
        </div>
      </div>
      
      {/* Sección de actividad reciente (placeholder) */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Actividad Reciente</h2>
        <div className="card text-center py-12 text-gray-500">
          <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p>Aún no hay actividad</p>
          <p className="text-sm mt-2">Cuando empieces a usar VendeFlow, aquí verás tu historial</p>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
