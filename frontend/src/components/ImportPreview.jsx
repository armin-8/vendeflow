/**
 * VendeFlow - Componente Vista Previa de Importación
 * ===================================================
 * 
 * Muestra una tabla con los productos que se van a importar.
 * 
 * Indicadores visuales:
 * - 🟢 Verde: Producto nuevo (se creará)
 * - 🟡 Amarillo: Producto existente (se puede actualizar)
 * 
 * PROPS:
 * ------
 * - products: Array de productos de la vista previa
 */

function ImportPreview({ products }) {
  // Si no hay productos, no mostrar nada
  if (!products || products.length === 0) {
    return null
  }
  
  // Limitar a 100 productos en la vista previa
  // (para no saturar el navegador si hay miles)
  const displayProducts = products.slice(0, 100)
  const hasMore = products.length > 100
  
  return (
    <div className="card overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full">
          {/* Encabezados */}
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Estado
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                SKU
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Nombre
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Precio
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Cantidad
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Categoría
              </th>
            </tr>
          </thead>
          
          {/* Cuerpo */}
          <tbody className="bg-white divide-y divide-gray-200">
            {displayProducts.map((product, index) => (
              <tr key={index} className="hover:bg-gray-50">
                {/* Estado (nuevo o existente) */}
                <td className="px-4 py-3 whitespace-nowrap">
                  {product.exists ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                      Ya existe
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                      Nuevo
                    </span>
                  )}
                </td>
                
                {/* SKU */}
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className="font-mono text-sm text-gray-900">
                    {product.sku}
                  </span>
                </td>
                
                {/* Nombre */}
                <td className="px-4 py-3">
                  <div className="text-sm text-gray-900 max-w-xs truncate">
                    {product.name}
                  </div>
                </td>
                
                {/* Precio */}
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className="text-sm text-gray-900">
                    ${product.price?.toLocaleString()}
                  </span>
                </td>
                
                {/* Cantidad */}
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className="text-sm text-gray-900">
                    {product.quantity || 0}
                  </span>
                </td>
                
                {/* Categoría */}
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className="text-sm text-gray-500">
                    {product.category || '-'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Mensaje si hay más productos */}
      {hasMore && (
        <div className="px-4 py-3 bg-gray-50 border-t text-center text-sm text-gray-500">
          Mostrando {displayProducts.length} de {products.length} productos
        </div>
      )}
    </div>
  )
}

export default ImportPreview
