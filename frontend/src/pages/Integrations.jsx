/**
 * VendeFlow - Página de Integraciones
 * =====================================
 * 
 * Permite conectar y gestionar plataformas externas:
 * - Shopify       ✅ Funcional
 * - Mercado Libre ✅ Funcional
 * - Amazon           Próximamente
 */

import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { shopifyService, mercadoLibreService } from '../services/api'

// ═══════════════════════════════════════════════════════════
// ICONOS
// ═══════════════════════════════════════════════════════════

const ShopifyIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="currentColor">
    <path d="M15.337 3.415c-.193-.016-.374.105-.447.282l-.447 1.13c-.282-.087-.58-.15-.893-.182-.017-.614-.073-1.237-.169-1.783-.313-1.79-1.27-2.657-2.554-2.657-.073 0-.145 0-.218.008-.048-.056-.097-.113-.153-.161C10.026.052 9.533 0 8.963 0 7.225 0 5.553 1.26 4.249 3.54c-.92 1.607-1.618 3.627-1.817 5.19l-2.169.672c-.671.21-.692.231-.78.863L0 18.255l12.192 2.12L24 18.07c0-.008-7.13-14.354-8.663-14.655zM11.602 5.296l-.002.012-1.372.425c.166-.846.482-1.696.865-2.347.144-.246.345-.516.59-.721.245.73.333 1.754.004 2.631h-.085zm-1.893-2.842c.193 0 .354.032.49.097-.222.12-.433.289-.628.507-.521.575-.922 1.472-1.084 2.336l-1.155.358c.322-1.563 1.186-3.298 2.377-3.298zm-.386 9.192l-.508 1.57s-.563-.403-1.24-.403c-1.004 0-1.053.63-1.053.79 0 .862 2.27 1.194 2.27 3.227 0 1.596-1.012 2.622-2.377 2.622-1.637 0-2.473-1.02-2.473-1.02l.435-1.443s.86.74 1.586.74c.475 0 .668-.372.668-.647 0-1.13-1.863-1.18-1.863-3.036 0-1.56 1.12-3.07 3.382-3.07.872 0 1.173.258 1.173.258v.412zm2.006-6.675c-.378 0-.79.089-1.203.266l.12-.457c.23-.867.685-1.758 1.083-2.254.156-.193.38-.427.635-.579.256.828.256 2.004-.635 3.024z"/>
  </svg>
)

const MercadoLibreIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="currentColor">
    <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 2.182c5.423 0 9.818 4.395 9.818 9.818S17.423 21.818 12 21.818 2.182 17.423 2.182 12 6.577 2.182 12 2.182zm3.273 4.363c-1.8 0-3.273 1.473-3.273 3.273v4.364c0 .602.489 1.09 1.09 1.09h4.365c.601 0 1.09-.488 1.09-1.09v-4.364c0-1.8-1.472-3.273-3.272-3.273zm-6.546 0c-1.8 0-3.272 1.473-3.272 3.273v4.364c0 .602.488 1.09 1.09 1.09h4.364c.602 0 1.091-.488 1.091-1.09v-4.364c0-1.8-1.473-3.273-3.273-3.273z"/>
  </svg>
)

const AmazonIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="currentColor">
    <path d="M.045 18.02c.072-.116.187-.124.348-.022 3.636 2.11 7.594 3.166 11.87 3.166 2.852 0 5.668-.533 8.447-1.595l.315-.14c.138-.06.234-.1.293-.13.226-.088.39-.046.503.14.13.212.09.385-.12.517-.56.34-1.32.776-2.29 1.31-1.5.82-3.15 1.46-4.96 1.91-1.81.45-3.63.68-5.46.68-2.06 0-4.03-.31-5.92-.94-1.89-.63-3.58-1.497-5.07-2.6-.12-.09-.16-.2-.12-.33.04-.14.12-.21.24-.22l.02.02zm21.83-2.94c.18.19.17.39-.03.6-.78.79-1.88 1.5-3.31 2.13-.28.12-.55.08-.8-.12-.1-.08-.15-.19-.14-.33.01-.14.08-.24.2-.3l.28-.14c.93-.44 1.63-.85 2.11-1.24.4-.33.73-.7.99-1.1.05-.08.11-.13.18-.15.07-.02.14 0 .22.07l.3.28v.3zm-8.13-9.71c0-1.08.36-2 1.08-2.75.72-.75 1.63-1.12 2.7-1.12 1.08 0 1.99.37 2.72 1.12s1.1 1.67 1.1 2.75c0 1.08-.37 2-1.1 2.75-.73.75-1.64 1.12-2.72 1.12-1.08 0-1.98-.37-2.7-1.12-.72-.75-1.08-1.67-1.08-2.75zm-6.55 7.1c-.35.73-.88 1.31-1.59 1.73-.71.42-1.5.63-2.38.63-1.37 0-2.5-.45-3.41-1.36C.92 12.49.47 11.37.47 10.02c0-1.35.45-2.48 1.36-3.39.9-.91 2.04-1.37 3.41-1.37.87 0 1.66.21 2.38.63.71.42 1.24 1 1.59 1.73l-1.6.92c-.18-.42-.47-.76-.87-1.02-.4-.26-.85-.39-1.35-.39-.7 0-1.28.24-1.74.72-.46.48-.69 1.08-.69 1.8 0 .72.23 1.32.69 1.8.46.48 1.04.72 1.74.72.5 0 .95-.13 1.35-.39.4-.26.69-.6.87-1.02l1.6.92v-.07z"/>
  </svg>
)

// ═══════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ═══════════════════════════════════════════════════════════

export default function Integrations() {
  const [searchParams] = useSearchParams()

  // Estado de Shopify
  const [shopifyStatus, setShopifyStatus] = useState(null)
  const [shopifyLoading, setShopifyLoading] = useState(true)
  const [shopifyActionLoading, setShopifyActionLoading] = useState(null)
  const [shopName, setShopName] = useState('')
  const [showShopifyInput, setShowShopifyInput] = useState(false)

  // Estado de Mercado Libre
  const [mlStatus, setMlStatus] = useState(null)
  const [mlLoading, setMlLoading] = useState(true)
  const [mlActionLoading, setMlActionLoading] = useState(null)

  // Mensaje global (éxito / error)
  const [message, setMessage] = useState(null)

  // ─────────────────────────────────────────────────────────
  // Leer parámetros del callback OAuth al cargar la página
  //
  // Cuando Shopify o ML redirigen de vuelta al frontend,
  // vienen con ?success=... o ?error=... en la URL.
  // Los capturamos aquí para mostrar el mensaje correcto.
  // ─────────────────────────────────────────────────────────
  useEffect(() => {
    const success = searchParams.get('success')
    const error = searchParams.get('error')
    const shop = searchParams.get('shop')
    const account = searchParams.get('account')

    if (success === 'shopify_connected') {
      setMessage({ type: 'success', text: `¡Tienda ${shop || 'Shopify'} conectada exitosamente!` })
    } else if (success === 'ml_connected') {
      setMessage({ type: 'success', text: `¡Cuenta ${account || 'Mercado Libre'} conectada exitosamente!` })
    } else if (error) {
      const errorMessages = {
        'invalid_state':          'Error de seguridad. Intenta de nuevo.',
        'invalid_shop':           'Tienda inválida.',
        'token_exchange_failed':  'Error al obtener acceso. Intenta de nuevo.',
        'connection_test_failed': 'No se pudo verificar la conexión.',
        'database_error':         'Error al guardar. Intenta de nuevo.',
        'session_expired':        'Sesión expirada. Intenta de nuevo.',
        'ml_auth_denied':         'Cancelaste la conexión con Mercado Libre.',
        'no_code':                'No se recibió código de autorización.',
        'user_info_failed':       'No se pudo obtener info de tu cuenta de ML.',
      }
      setMessage({ type: 'error', text: errorMessages[error] || `Error: ${error}` })
    }
  }, [searchParams])

  // ─────────────────────────────────────────────────────────
  // Cargar estado de ambas plataformas al montar
  // ─────────────────────────────────────────────────────────
  useEffect(() => {
    loadShopifyStatus()
    loadMlStatus()
  }, [])

  // ═══════════════════════════════════════════════════════════
  // HANDLERS DE SHOPIFY
  // ═══════════════════════════════════════════════════════════

  const loadShopifyStatus = async () => {
    try {
      setShopifyLoading(true)
      const data = await shopifyService.getStatus()
      setShopifyStatus(data)
    } catch (error) {
      setShopifyStatus({ connected: false })
    } finally {
      setShopifyLoading(false)
    }
  }

  const handleConnectShopify = async () => {
    if (!shopName.trim()) {
      setMessage({ type: 'error', text: 'Ingresa el nombre de tu tienda' })
      return
    }
    try {
      setShopifyActionLoading('connect')
      const data = await shopifyService.connect(shopName.trim())
      if (data.auth_url) window.location.href = data.auth_url
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
      setShopifyActionLoading(null)
    }
  }

  const handleDisconnectShopify = async () => {
    if (!confirm('¿Estás seguro de desconectar esta tienda?')) return
    try {
      setShopifyActionLoading('disconnect')
      await shopifyService.disconnect()
      setShopifyStatus({ connected: false })
      setMessage({ type: 'success', text: 'Tienda Shopify desconectada' })
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
    } finally {
      setShopifyActionLoading(null)
    }
  }

  const handleImportShopify = async () => {
    try {
      setShopifyActionLoading('import')
      const data = await shopifyService.importProducts()
      setMessage({ type: 'success', text: `Shopify: ${data.created} creados, ${data.updated} actualizados` })
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
    } finally {
      setShopifyActionLoading(null)
    }
  }

  const handleSyncShopify = async () => {
    try {
      setShopifyActionLoading('sync')
      const data = await shopifyService.syncInventory()
      setMessage({ type: 'success', text: `Shopify: ${data.synced} productos sincronizados` })
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
    } finally {
      setShopifyActionLoading(null)
    }
  }

  // ═══════════════════════════════════════════════════════════
  // HANDLERS DE MERCADO LIBRE
  // ═══════════════════════════════════════════════════════════

  const loadMlStatus = async () => {
    try {
      setMlLoading(true)
      const data = await mercadoLibreService.getStatus()
      setMlStatus(data)
    } catch (error) {
      setMlStatus({ connected: false })
    } finally {
      setMlLoading(false)
    }
  }

  const handleConnectML = async () => {
    try {
      setMlActionLoading('connect')
      const data = await mercadoLibreService.connect()
      // El backend devuelve la URL de autorización de ML
      // Redirigimos al usuario a esa URL (igual que Shopify)
      if (data.auth_url) window.location.href = data.auth_url
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
      setMlActionLoading(null)
    }
  }

  const handleDisconnectML = async () => {
    if (!confirm('¿Estás seguro de desconectar tu cuenta de Mercado Libre?')) return
    try {
      setMlActionLoading('disconnect')
      await mercadoLibreService.disconnect()
      setMlStatus({ connected: false })
      setMessage({ type: 'success', text: 'Cuenta de Mercado Libre desconectada' })
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
    } finally {
      setMlActionLoading(null)
    }
  }

  const handleImportML = async () => {
    try {
      setMlActionLoading('import')
      const data = await mercadoLibreService.importProducts()
      setMessage({ type: 'success', text: `Mercado Libre: ${data.created} creados, ${data.updated} actualizados` })
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
    } finally {
      setMlActionLoading(null)
    }
  }

  const handleSyncML = async () => {
    try {
      setMlActionLoading('sync')
      const data = await mercadoLibreService.syncInventory()
      setMessage({ type: 'success', text: `Mercado Libre: ${data.synced} productos sincronizados` })
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
    } finally {
      setMlActionLoading(null)
    }
  }

  // ═══════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Integraciones</h1>
      <p className="text-gray-600 mb-8">Conecta tus canales de venta para sincronizar inventario</p>

      {/* Mensaje de éxito o error */}
      {message && (
        <div className={`mb-6 p-4 rounded-lg ${
          message.type === 'success'
            ? 'bg-green-50 text-green-700 border border-green-200'
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message.text}
          <button onClick={() => setMessage(null)} className="float-right font-bold">×</button>
        </div>
      )}

      <div className="grid gap-6">

        {/* ═══════════════════════════════════════════════════════════ */}
        {/* SHOPIFY */}
        {/* ═══════════════════════════════════════════════════════════ */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg text-green-600">
                <ShopifyIcon />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-lg">Shopify</h3>
                <p className="text-gray-500 text-sm">
                  {shopifyLoading ? 'Cargando...' : (
                    shopifyStatus?.connected
                      ? `Conectado a: ${shopifyStatus.store_name}`
                      : 'No conectado'
                  )}
                </p>
              </div>
            </div>

            {!shopifyLoading && (
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                shopifyStatus?.connected
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {shopifyStatus?.connected ? '● Conectado' : '○ Desconectado'}
              </span>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-gray-100">
            {shopifyLoading ? (
              <div className="text-gray-500 text-sm">Cargando estado...</div>
            ) : shopifyStatus?.connected ? (
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={handleImportShopify}
                  disabled={!!shopifyActionLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  {shopifyActionLoading === 'import' ? 'Importando...' : '📥 Importar Productos'}
                </button>
                <button
                  onClick={handleSyncShopify}
                  disabled={!!shopifyActionLoading}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  {shopifyActionLoading === 'sync' ? 'Sincronizando...' : '🔄 Sincronizar Inventario'}
                </button>
                <button
                  onClick={handleDisconnectShopify}
                  disabled={!!shopifyActionLoading}
                  className="px-4 py-2 bg-white text-red-600 border border-red-300 rounded-lg hover:bg-red-50 disabled:opacity-50 text-sm"
                >
                  {shopifyActionLoading === 'disconnect' ? 'Desconectando...' : 'Desconectar'}
                </button>
              </div>
            ) : (
              <div>
                {showShopifyInput ? (
                  <div className="flex gap-3 items-center">
                    <input
                      type="text"
                      value={shopName}
                      onChange={(e) => setShopName(e.target.value)}
                      placeholder="tu-tienda (sin .myshopify.com)"
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    />
                    <button
                      onClick={handleConnectShopify}
                      disabled={shopifyActionLoading === 'connect'}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm"
                    >
                      {shopifyActionLoading === 'connect' ? 'Conectando...' : 'Conectar'}
                    </button>
                    <button
                      onClick={() => setShowShopifyInput(false)}
                      className="px-4 py-2 text-gray-600 hover:text-gray-800 text-sm"
                    >
                      Cancelar
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setShowShopifyInput(true)}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                  >
                    🔗 Conectar Shopify
                  </button>
                )}
              </div>
            )}
          </div>

          {shopifyStatus?.connected && shopifyStatus.last_synced_at && (
            <p className="mt-4 text-xs text-gray-400">
              Última sincronización: {new Date(shopifyStatus.last_synced_at).toLocaleString()}
            </p>
          )}
        </div>

        {/* ═══════════════════════════════════════════════════════════ */}
        {/* MERCADO LIBRE */}
        {/* ═══════════════════════════════════════════════════════════ */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-yellow-100 rounded-lg text-yellow-600">
                <MercadoLibreIcon />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-lg">Mercado Libre</h3>
                <p className="text-gray-500 text-sm">
                  {mlLoading ? 'Cargando...' : (
                    mlStatus?.connected
                      ? `Conectado como: ${mlStatus.account}`
                      : 'No conectado'
                  )}
                </p>
              </div>
            </div>

            {!mlLoading && (
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                mlStatus?.connected
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {mlStatus?.connected ? '● Conectado' : '○ Desconectado'}
              </span>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-gray-100">
            {mlLoading ? (
              <div className="text-gray-500 text-sm">Cargando estado...</div>
            ) : mlStatus?.connected ? (
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={handleImportML}
                  disabled={!!mlActionLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  {mlActionLoading === 'import' ? 'Importando...' : '📥 Importar Publicaciones'}
                </button>
                <button
                  onClick={handleSyncML}
                  disabled={!!mlActionLoading}
                  className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  {mlActionLoading === 'sync' ? 'Sincronizando...' : '🔄 Sincronizar Inventario'}
                </button>
                <button
                  onClick={handleDisconnectML}
                  disabled={!!mlActionLoading}
                  className="px-4 py-2 bg-white text-red-600 border border-red-300 rounded-lg hover:bg-red-50 disabled:opacity-50 text-sm"
                >
                  {mlActionLoading === 'disconnect' ? 'Desconectando...' : 'Desconectar'}
                </button>
              </div>
            ) : (
              // Sin necesitar input — ML no requiere nombre de tienda
              <button
                onClick={handleConnectML}
                disabled={mlActionLoading === 'connect'}
                className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 disabled:opacity-50 text-sm"
              >
                {mlActionLoading === 'connect' ? 'Redirigiendo...' : '🔗 Conectar Mercado Libre'}
              </button>
            )}
          </div>

          {mlStatus?.connected && mlStatus.last_synced_at && (
            <p className="mt-4 text-xs text-gray-400">
              Última sincronización: {new Date(mlStatus.last_synced_at).toLocaleString()}
            </p>
          )}

          {/* Nota sobre ngrok para el desarrollador */}
          {!mlStatus?.connected && (
            <p className="mt-4 text-xs text-gray-400 bg-gray-50 rounded p-2">
              💡 Para pruebas locales necesitas configurar ngrok. Consulta el .env del backend.
            </p>
          )}
        </div>

        {/* ═══════════════════════════════════════════════════════════ */}
        {/* AMAZON — Próximamente */}
        {/* ═══════════════════════════════════════════════════════════ */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 opacity-60">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-orange-100 rounded-lg text-orange-600">
                <AmazonIcon />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-lg">Amazon</h3>
                <p className="text-gray-500 text-sm">Próximamente</p>
              </div>
            </div>
            <span className="px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-500">
              🚧 En desarrollo
            </span>
          </div>
        </div>

      </div>
    </div>
  )
}
