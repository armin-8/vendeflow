/**
 * VendeFlow - Layout Principal
 * ============================
 * 
 * Estructura base que envuelve todas las páginas.
 * Incluye: Navbar + Contenido + Footer
 */

import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'

function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Navbar fijo arriba */}
      <Navbar />
      
      {/* Contenido principal (Outlet renderiza la página actual) */}
      <main className="flex-grow">
        <Outlet />
      </main>
      
      {/* Footer */}
      <footer className="bg-gray-800 text-white py-6">
        <div className="container mx-auto px-4 text-center">
          <p>&copy; 2024 VendeFlow. Todos los derechos reservados.</p>
          <p className="text-gray-400 text-sm mt-2">
            Gestión de inventario multi-canal para LATAM
          </p>
        </div>
      </footer>
    </div>
  )
}

export default Layout
