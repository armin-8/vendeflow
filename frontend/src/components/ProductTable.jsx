/**
 * VendeFlow - Tabla de Productos
 * ===============================
 * 
 * Componente reutilizable que muestra la lista de productos.
 * Recibe los productos como props y emite eventos de editar/eliminar.
 * 
 * PROPS:
 * - products: Array de productos a mostrar
 * - onEdit: Función que se llama al hacer clic en editar
 * - onDelete: Función que se llama al hacer clic en eliminar
 */

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
                    {/* Imagen o placeholder */}
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
                    {/* Nombre y categoría */}
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
                      <span className="text-sm text-gray-400">
                        Sin conectar
                      </span>
                    )}
                  </div>
                </td>
                
                {/* Acciones */}
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    onClick={() => onEdit(product)}
                    className="text-primary-600 hover:text-primary-900 mr-4"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => onDelete(product.id)}
                    className="text-red-600 hover:text-red-900"
                  >
                    Eliminar
                  </button>
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
