/**
 * VendeFlow - Página 404
 * ======================
 * 
 * Se muestra cuando el usuario navega a una ruta que no existe.
 */

import { Link } from 'react-router-dom'

function NotFound() {
  return (
    <div className="min-h-[70vh] flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-gray-200">404</h1>
        <h2 className="text-2xl font-semibold text-gray-800 mt-4">
          Página no encontrada
        </h2>
        <p className="text-gray-600 mt-2 mb-8">
          La página que buscas no existe o ha sido movida.
        </p>
        <Link to="/" className="btn-primary">
          Volver al inicio
        </Link>
      </div>
    </div>
  )
}

export default NotFound
