/**
 * VendeFlow - Tabla de Productos
 * ===============================
 * 
 * Componente reutilizable que muestra la lista de productos.
 * Recibe los productos como props y emite eventos de editar/eliminar.
 * 
 * PROPS:
 * - products:  Array de productos a mostrar
 * - onEdit:    Función que se llama al hacer clic en editar
 * - onDelete:  Función que se llama al hacer clic en eliminar
 * 
 * NUEVO — Botón de sincronización por SKU:
 * - Aparece solo si el producto tiene shopify_id o mercadolibre_id
 * - Muestra las plataformas disponibles del producto
 * - Llama a syncBySku() de la plataforma correspondiente
 * - Muestra feedback inline (éxito/error) sin recargar la tabla
 */

import { useState } from 'react'
import { shopifyService, mercadoLibreService } from '../services/api'

// ═══════════════════════════════════════════════════════════
// COMPONENTE: BOTÓN DE SINCRONIZACIÓN POR SKU
// ═══════════════════════════════════════════════════════════
//
// ¿POR QUÉ UN COMPONENTE SEPARADO?
// ----------------------------------
// Cada fila tiene su propio estado de loading/feedback.
// Si lo ponemos en ProductTable, un solo estado afectaría
// a toda la tabla. Con un componente por fila, cada botón
// es independiente — puedes sincronizar múltiples productos
// al mismo tiempo sin que interfieran entre sí.

function SyncButton({ product }) {
  const [loading, setLoading] = useState(null)   // null | 'shopify' | 'mercadolibre'
  const [feedback, setFeedback] = useState(null) // { type: 'success'|'error', text: string }

  // ¿A qué plataformas está vinculado este producto?
  const hasShopify = !!product.shopify_id
  const hasMercadoLibre = !!product.mercadolibre_id

  // Si no está vinculado a ninguna plataforma, no mostramos nada
  if (!hasShopify && !hasMercadoLibre) return null

  const handleSync = async (platform) => {
    setLoading(platform)
    setFeedback(null)

    try {
      let result

      if (platform === 'shopify') {
        result = await shopifyService.syncBySku(product.sku)
      } else if (platform === 'mercadolibre') {
        result = await mercadoLibreService.syncBySku(product.sku)
      }

      // Mostrar mensaje de éxito por 3 segundos y luego limpiar
      setFeedback({ type: 'success', text: `✅ ${result.synced} sincronizado` })
      setTimeout(() => setFeedback(null), 3000)

    } catch (error) {
      setFeedback({ type: 'error', text: `❌ ${error.message}` })
      setTimeout(() => setFeedback(null), 4000)
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex gap-1">
        {/* Botón Shopify — solo si el producto tiene shopify_id */}
        {hasShopify && (
          <button
            onClick={() => handleSync('shopify')}
            disabled={!!loading}
            title={`Sincronizar ${product.sku} a Shopify`}
            className="px-2 py-1 text-xs bg-green-50 text-green-700 border border-green-200 rounded hover:bg-green-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading === 'shopify' ? '⏳' : '🛒 Sync'}
          </button>
        )}

        {/* Botón ML — solo si el producto tiene mercadolibre_id */}
        {hasMercadoLibre && (
          <button
            onClick={() => handleSync('mercadolibre')}
            disabled={!!loading}
            title={`Sincronizar ${product.sku} a Mercado Libre`}
            className="px-2 py-1 text-xs bg-yellow-50 text-yellow-700 border border-yellow-200 rounded hover:bg-yellow-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading === 'mercadolibre' ? '⏳' : '🤝 Sync'}
          </button>
        )}
      </div>

      {/* Feedback inline — aparece debajo de los botones */}
      {feedback && (
        <span className={`text-xs ${
          feedback.type === 'success' ? 'text-green-600' : 'text-red-600'
        }`}>
          {feedback.text}
        </span>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL: TABLA DE PRODUCTOS
// ═══════════════════════════════════════════════════════════

function ProductTable({ products, onEdit, onDelete }) {
  return (
    <div className="card overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full">
          {/* Encabezados */}
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Producto
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                SKU
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Precio
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Stock
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Plataformas
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Acciones
              </th>
            </tr>
          </thead>

          {/* Cuerpo de la tabla */}
          <tbody className="bg-white divide-y divide-gray-200">
            {products.map((product) => (
              <tr key={product.id} className="hover:bg-gray-50">

                {/* Producto (imagen + nombre) */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      {product.image_url ? (
                        <img
                          className="h-10 w-10 rounded-lg object-cover"
                          src={product.image_url}
                          alt={product.name}
                        />
                      ) : (
                        <div className="h-10 w-10 rounded-lg bg-gray-200 flex items-center justify-center">
                          <svg className="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                          </svg>
                        </div>
                      )}
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {product.name}
                      </div>
                      {product.category && (
                        <div className="text-sm text-gray-500">
                          {product.category}
                        </div>
                      )}
                    </div>
                  </div>
                </td>

                {/* SKU */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-900 font-mono">
                    {product.sku}
                  </span>
                </td>

                {/* Precio */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    ${product.price?.toLocaleString()}
                  </div>
                  {product.cost && (
                    <div className="text-xs text-gray-500">
                      Costo: ${product.cost?.toLocaleString()}
                    </div>
                  )}
                </td>

                {/* Stock */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    product.quantity === 0
                      ? 'bg-red-100 text-red-800'
                      : product.is_low_stock
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-green-100 text-green-800'
                  }`}>
                    {product.quantity} unidades
                  </span>
                </td>

                {/* Plataformas conectadas */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex gap-1">
                    {product.platforms_connected?.length > 0 ? (
                      product.platforms_connected.map((platform) => (
                        <span
                          key={platform}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {platform === 'shopify' && '🛒'}
                          {platform === 'amazon' && '📦'}
                          {platform === 'mercadolibre' && '🤝'}
                          {platform.charAt(0).toUpperCase() + platform.slice(1)}
                        </span>
                      ))
                    ) : (
                      <span className="text-sm text-gray-400">Sin conectar</span>
                    )}
                  </div>
                </td>

                {/* Acciones: Editar | Eliminar | Sync por plataforma */}
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex items-center justify-end gap-3">
                    {/* Botones de sincronización por plataforma */}
                    <SyncButton product={product} />

                    {/* Editar */}
                    <button
                      onClick={() => onEdit(product)}
                      className="text-primary-600 hover:text-primary-900"
                    >
                      Editar
                    </button>

                    {/* Eliminar */}
                    <button
                      onClick={() => onDelete(product.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Eliminar
                    </button>
                  </div>
                </td>

              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default ProductTable
