/**
 * VendeFlow - Página de Importación
 * ===================================
 * 
 * Permite importar productos masivamente desde Excel o CSV.
 * 
 * FLUJO DE LA PÁGINA:
 * -------------------
 * 1. Usuario ve instrucciones y botón "Seleccionar archivo"
 * 2. Selecciona un archivo Excel/CSV
 * 3. Se muestra vista previa de los productos
 * 4. Usuario confirma y se importan
 * 
 * CONCEPTOS DE REACT:
 * -------------------
 * - useRef: Nos permite acceder directamente a un elemento del DOM
 *   Lo usamos para "clickear" el input de archivo programáticamente
 * 
 * - useState: Guarda el estado del componente
 *   Cada vez que cambia, React re-renderiza
 */

import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { importService } from '../services/api'
import ImportPreview from '../components/ImportPreview'

function Import() {
  // ═══════════════════════════════════════════════════════════
  // ESTADO
  // ═══════════════════════════════════════════════════════════
  
  // Archivo seleccionado
  const [selectedFile, setSelectedFile] = useState(null)
  
  // Estados del proceso
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Datos de la vista previa
  const [previewData, setPreviewData] = useState(null)
  
  // Estado de confirmación
  const [isConfirming, setIsConfirming] = useState(false)
  const [importResult, setImportResult] = useState(null)
  
  // Opción: actualizar productos existentes
  const [updateExisting, setUpdateExisting] = useState(false)
  
  // ═══════════════════════════════════════════════════════════
  // REFERENCIAS
  // ═══════════════════════════════════════════════════════════
  
  // useRef nos da acceso directo al elemento <input type="file">
  // Lo usamos porque queremos abrir el selector de archivos
  // cuando el usuario hace clic en nuestro botón personalizado
  const fileInputRef = useRef(null)
  
  // Para navegación
  const navigate = useNavigate()
  
  // ═══════════════════════════════════════════════════════════
  // HANDLERS
  // ═══════════════════════════════════════════════════════════
  
  /**
   * Abre el selector de archivos.
   * 
   * ¿Por qué no usamos el input directamente?
   * Porque queremos un botón bonito, no el input feo del navegador.
   */
  const handleSelectFile = () => {
    fileInputRef.current.click()
  }
  
  /**
   * Se ejecuta cuando el usuario selecciona un archivo.
   * 
   * El evento contiene:
   * - e.target.files: Array de archivos seleccionados
   * - e.target.files[0]: El primer archivo (solo permitimos uno)
   */
  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    
    if (!file) return
    
    // Validar tipo de archivo
    const validTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
      'application/vnd.ms-excel', // .xls
      'text/csv' // .csv
    ]
    
    // También validamos por extensión (más confiable)
    const extension = file.name.split('.').pop().toLowerCase()
    const validExtensions = ['xlsx', 'xls', 'csv']
    
    if (!validExtensions.includes(extension)) {
      setError('Solo se permiten archivos Excel (.xlsx, .xls) o CSV (.csv)')
      return
    }
    
    // Guardar archivo y limpiar estados anteriores
    setSelectedFile(file)
    setError(null)
    setPreviewData(null)
    setImportResult(null)
    
    // Subir archivo para obtener vista previa
    await uploadForPreview(file)
  }
  
  /**
   * Sube el archivo al backend para obtener vista previa.
   */
  const uploadForPreview = async (file) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await importService.preview(file)
      setPreviewData(response)
    } catch (err) {
      setError(err.message || 'Error al procesar el archivo')
      setSelectedFile(null)
    } finally {
      setIsLoading(false)
    }
  }
  
  /**
   * Confirma la importación y guarda los productos.
   */
  const handleConfirm = async () => {
    setIsConfirming(true)
    setError(null)
    
    try {
      const result = await importService.confirm(updateExisting)
      setImportResult(result)
      setPreviewData(null) // Limpiar vista previa
    } catch (err) {
      setError(err.message || 'Error al importar productos')
    } finally {
      setIsConfirming(false)
    }
  }
  
  /**
   * Cancela y limpia todo.
   */
  const handleCancel = () => {
    setSelectedFile(null)
    setPreviewData(null)
    setError(null)
    setImportResult(null)
    // Limpiar el input de archivo
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }
  
  /**
   * Va al inventario después de importar.
   */
  const handleGoToInventory = () => {
    navigate('/inventory')
  }
  
  // ═══════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════
  
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Encabezado */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Importar Productos</h1>
        <p className="text-gray-600 mt-1">
          Sube un archivo Excel o CSV para agregar productos masivamente
        </p>
      </div>
      
      {/* ═══════════════════════════════════════════════════════
          ESTADO 1: RESULTADO DE IMPORTACIÓN EXITOSA
          ═══════════════════════════════════════════════════════ */}
      {importResult && (
        <div className="card bg-green-50 border border-green-200">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-8 w-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4 flex-1">
              <h3 className="text-lg font-semibold text-green-800">
                ¡Importación Completada!
              </h3>
              <div className="mt-2 text-green-700">
                <p>✅ <strong>{importResult.created}</strong> productos creados</p>
                <p>🔄 <strong>{importResult.updated}</strong> productos actualizados</p>
                {importResult.skipped > 0 && (
                  <p>⏭️ <strong>{importResult.skipped}</strong> productos omitidos (ya existían)</p>
                )}
              </div>
              {importResult.errors?.length > 0 && (
                <div className="mt-3 p-3 bg-yellow-50 rounded-lg">
                  <p className="text-yellow-800 font-medium">Advertencias:</p>
                  <ul className="text-yellow-700 text-sm mt-1">
                    {importResult.errors.slice(0, 5).map((err, i) => (
                      <li key={i}>• {err}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="mt-4 flex gap-3">
                <button
                  onClick={handleGoToInventory}
                  className="btn-primary"
                >
                  Ver Inventario
                </button>
                <button
                  onClick={handleCancel}
                  className="btn-secondary"
                >
                  Importar Otro Archivo
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* ═══════════════════════════════════════════════════════
          ESTADO 2: VISTA PREVIA DE PRODUCTOS
          ═══════════════════════════════════════════════════════ */}
      {previewData && !importResult && (
        <div>
          {/* Resumen */}
          <div className="card mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">Vista Previa</h2>
                <p className="text-gray-600 mt-1">
                  Archivo: <span className="font-medium">{selectedFile?.name}</span>
                </p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-primary-600">{previewData.total}</p>
                <p className="text-sm text-gray-500">productos encontrados</p>
              </div>
            </div>
            
            {/* Estadísticas */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{previewData.new_count}</p>
                <p className="text-sm text-gray-500">Nuevos</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-600">{previewData.update_count}</p>
                <p className="text-sm text-gray-500">Ya existen</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{previewData.errors_count}</p>
                <p className="text-sm text-gray-500">Errores</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-600">{previewData.total}</p>
                <p className="text-sm text-gray-500">Total</p>
              </div>
            </div>
          </div>
          
          {/* Errores/Advertencias */}
          {previewData.errors?.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
              <h3 className="font-medium text-yellow-800">Advertencias:</h3>
              <ul className="mt-2 text-yellow-700 text-sm">
                {previewData.errors.map((err, i) => (
                  <li key={i}>• {err}</li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Tabla de vista previa */}
          <ImportPreview products={previewData.products} />
          
          {/* Opciones y botones de acción */}
          <div className="card mt-6">
            {/* Opción: actualizar existentes */}
            {previewData.update_count > 0 && (
              <label className="flex items-center mb-4 cursor-pointer">
                <input
                  type="checkbox"
                  checked={updateExisting}
                  onChange={(e) => setUpdateExisting(e.target.checked)}
                  className="w-4 h-4 text-primary-500 rounded focus:ring-primary-500"
                />
                <span className="ml-2 text-gray-700">
                  Actualizar {previewData.update_count} productos que ya existen
                </span>
              </label>
            )}
            
            {/* Error */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
                {error}
              </div>
            )}
            
            {/* Botones */}
            <div className="flex gap-3">
              <button
                onClick={handleConfirm}
                disabled={isConfirming}
                className="btn-primary disabled:opacity-50"
              >
                {isConfirming ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                    </svg>
                    Importando...
                  </span>
                ) : (
                  `Importar ${previewData.new_count + (updateExisting ? previewData.update_count : 0)} Productos`
                )}
              </button>
              <button
                onClick={handleCancel}
                disabled={isConfirming}
                className="btn-secondary"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* ═══════════════════════════════════════════════════════
          ESTADO 3: SELECCIONAR ARCHIVO (estado inicial)
          ═══════════════════════════════════════════════════════ */}
      {!previewData && !importResult && (
        <div className="grid md:grid-cols-2 gap-8">
          {/* Zona de subida */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Subir Archivo</h2>
            
            {/* Input oculto (lo activamos con el botón) */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={handleFileChange}
              className="hidden"
            />
            
            {/* Zona de drop/click */}
            <div
              onClick={handleSelectFile}
              className={`
                border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
                transition-colors duration-200
                ${isLoading 
                  ? 'border-primary-300 bg-primary-50' 
                  : 'border-gray-300 hover:border-primary-500 hover:bg-gray-50'
                }
              `}
            >
              {isLoading ? (
                <div>
                  <svg className="animate-spin h-12 w-12 text-primary-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                  </svg>
                  <p className="text-primary-600 font-medium">Procesando archivo...</p>
                </div>
              ) : (
                <div>
                  <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="text-gray-600 font-medium">
                    Haz clic para seleccionar un archivo
                  </p>
                  <p className="text-gray-400 text-sm mt-2">
                    Excel (.xlsx, .xls) o CSV (.csv)
                  </p>
                </div>
              )}
            </div>
            
            {/* Error */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mt-4">
                {error}
              </div>
            )}
          </div>
          
          {/* Instrucciones */}
          <div className="card bg-gray-50">
            <h2 className="text-xl font-semibold mb-4">📋 Instrucciones</h2>
            
            <div className="space-y-4 text-gray-700">
              <div>
                <h3 className="font-medium text-gray-900">Columnas Requeridas:</h3>
                <ul className="mt-1 text-sm">
                  <li>• <code className="bg-gray-200 px-1 rounded">sku</code> - Código único del producto</li>
                  <li>• <code className="bg-gray-200 px-1 rounded">name</code> - Nombre del producto</li>
                  <li>• <code className="bg-gray-200 px-1 rounded">price</code> - Precio de venta</li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-medium text-gray-900">Columnas Opcionales:</h3>
                <ul className="mt-1 text-sm">
                  <li>• <code className="bg-gray-200 px-1 rounded">description</code> - Descripción</li>
                  <li>• <code className="bg-gray-200 px-1 rounded">cost</code> - Costo de adquisición</li>
                  <li>• <code className="bg-gray-200 px-1 rounded">quantity</code> - Cantidad en stock</li>
                  <li>• <code className="bg-gray-200 px-1 rounded">min_stock</code> - Stock mínimo</li>
                  <li>• <code className="bg-gray-200 px-1 rounded">category</code> - Categoría</li>
                  <li>• <code className="bg-gray-200 px-1 rounded">brand</code> - Marca</li>
                  <li>• <code className="bg-gray-200 px-1 rounded">image_url</code> - URL de imagen</li>
                </ul>
              </div>
              
              <div className="pt-4 border-t">
                <h3 className="font-medium text-gray-900">💡 Consejos:</h3>
                <ul className="mt-1 text-sm">
                  <li>• Los SKUs se convertirán a MAYÚSCULAS</li>
                  <li>• Los productos con SKU existente se pueden actualizar</li>
                  <li>• Revisa la vista previa antes de confirmar</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Import
