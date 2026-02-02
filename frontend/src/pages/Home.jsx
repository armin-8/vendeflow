/**
 * VendeFlow - Página de Inicio
 * ============================
 * 
 * Landing page que muestra las características del producto.
 */

import { Link } from 'react-router-dom'

function Home() {
  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-primary-600 to-primary-800 text-white py-20">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            Gestiona tu inventario en un solo lugar
          </h1>
          <p className="text-xl md:text-2xl mb-8 text-primary-100 max-w-3xl mx-auto">
            Sincroniza automáticamente tu stock con Shopify, Amazon y Mercado Libre. 
            Olvídate de los Excel y los errores manuales.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              to="/register" 
              className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-primary-50 transition-colors"
            >
              Comenzar Gratis
            </Link>
            <a 
              href="#features" 
              className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-primary-600 transition-colors"
            >
              Ver Características
            </a>
          </div>
        </div>
      </section>
      
      {/* Problema que resolvemos */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">
            ¿Te suena familiar?
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {/* Problema 1 */}
            <div className="bg-white p-6 rounded-xl shadow-md">
              <div className="text-4xl mb-4">😫</div>
              <h3 className="text-xl font-semibold mb-2">Horas en Excel</h3>
              <p className="text-gray-600">
                Descargas el inventario de Odoo, usas BUSCARV, y luego lo subes a cada plataforma manualmente.
              </p>
            </div>
            
            {/* Problema 2 */}
            <div className="bg-white p-6 rounded-xl shadow-md">
              <div className="text-4xl mb-4">❌</div>
              <h3 className="text-xl font-semibold mb-2">Errores constantes</h3>
              <p className="text-gray-600">
                Vendes algo que ya no tienes en stock porque el inventario no estaba actualizado.
              </p>
            </div>
            
            {/* Problema 3 */}
            <div className="bg-white p-6 rounded-xl shadow-md">
              <div className="text-4xl mb-4">🔄</div>
              <h3 className="text-xl font-semibold mb-2">Formatos diferentes</h3>
              <p className="text-gray-600">
                Cada plataforma pide los datos en un formato distinto. Shopify, Amazon, ML... todos diferentes.
              </p>
            </div>
          </div>
        </div>
      </section>
      
      {/* Características */}
      <section id="features" className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-4">
            VendeFlow lo resuelve
          </h2>
          <p className="text-gray-600 text-center mb-12 max-w-2xl mx-auto">
            Una plataforma centralizada para gestionar tu inventario y sincronizarlo automáticamente con todos tus canales de venta.
          </p>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">Inventario Centralizado</h3>
              <p className="text-gray-600">
                Un solo lugar para ver y gestionar todo tu stock.
              </p>
            </div>
            
            {/* Feature 2 */}
            <div className="text-center">
              <div className="w-16 h-16 bg-secondary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-secondary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">Sincronización Automática</h3>
              <p className="text-gray-600">
                Actualiza tu inventario en todas las plataformas con un clic.
              </p>
            </div>
            
            {/* Feature 3 */}
            <div className="text-center">
              <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">Importa desde Excel</h3>
              <p className="text-gray-600">
                ¿Tienes tu inventario en Excel? Impórtalo fácilmente.
              </p>
            </div>
          </div>
        </div>
      </section>
      
      {/* CTA Final */}
      <section className="py-16 bg-gray-800 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">
            ¿Listo para simplificar tu e-commerce?
          </h2>
          <p className="text-gray-300 mb-8 max-w-2xl mx-auto">
            Únete a los vendedores de LATAM que ya gestionan su inventario de forma inteligente.
          </p>
          <Link 
            to="/register" 
            className="bg-primary-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-primary-600 transition-colors inline-block"
          >
            Crear Cuenta Gratis
          </Link>
        </div>
      </section>
    </div>
  )
}

export default Home
