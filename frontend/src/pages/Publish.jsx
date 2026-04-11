/**
 * VendeFlow - Página de Publicación con IA
 * ==========================================
 * 
 * Permite generar contenido optimizado para múltiples plataformas
 * usando Claude API. El flujo es:
 * 
 * 1. Usuario llena datos básicos del producto
 * 2. Claude genera contenido optimizado por plataforma
 * 3. Usuario revisa y edita (human in the loop)
 * 4. Usuario confirma → se publica (próxima fase)
 */

import { useState } from 'react'
import { shopifyService, mercadoLibreService } from '../services/api'

const API_URL = import.meta.env.VITE_API_URL || '/api'

// ─── Servicio de IA ───────────────────────────────────────
const aiService = {
  generateListing: async (data) => {
    const authData = JSON.parse(localStorage.getItem('vendeflow-auth') || '{}')
    const token = authData?.state?.token

    const response = await fetch(`${API_URL}/ai/generate-listing`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    })

    const result = await response.json()
    if (!response.ok) throw new Error(result.error || 'Error al generar contenido')
    return result
  }
}

// ─── Componente de Preview por Plataforma ─────────────────
function PlatformPreview({ platform, data, onEdit }) {
  const configs = {
    shopify: {
      name: 'Shopify',
      color: 'green',
      icon: '🛒',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      badgeColor: 'bg-green-100 text-green-700'
    },
    mercadolibre: {
      name: 'Mercado Libre',
      color: 'yellow',
      icon: '🤝',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      badgeColor: 'bg-yellow-100 text-yellow-700'
    },
    amazon: {
      name: 'Amazon',
      color: 'orange',
      icon: '📦',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200',
      badgeColor: 'bg-orange-100 text-orange-700'
    }
  }

  const config = configs[platform]

  return (
    <div className={`border ${config.borderColor} rounded-xl overflow-hidden`}>
      {/* Header */}
      <div className={`${config.bgColor} px-4 py-3 flex items-center justify-between border-b ${config.borderColor}`}>
        <div className="flex items-center gap-2">
          <span className="text-lg">{config.icon}</span>
          <span className="font-semibold text-gray-800">{config.name}</span>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${config.badgeColor}`}>
          ✅ Generado
        </span>
      </div>

      {/* Contenido */}
      <div className="p-4 space-y-4 bg-white">

        {/* Título */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Título</label>
            {platform === 'mercadolibre' && (
              <span className={`text-xs font-mono ${data.title?.length > 60 ? 'text-red-600' : 'text-green-600'}`}>
                {data.title?.length || 0}/60 chars
              </span>
            )}
          </div>
          <textarea
            value={data.title || ''}
            onChange={(e) => onEdit(platform, 'title', e.target.value)}
            rows={2}
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
          />
        </div>

        {/* Descripción */}
        {(platform === 'shopify' || platform === 'mercadolibre') && (
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">
              {platform === 'shopify' ? 'Descripción (HTML)' : 'Descripción (Texto plano)'}
            </label>
            <textarea
              value={platform === 'shopify' ? (data.description_html || '') : (data.description || '')}
              onChange={(e) => onEdit(
                platform,
                platform === 'shopify' ? 'description_html' : 'description',
                e.target.value
              )}
              rows={5}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none font-mono"
            />
          </div>
        )}

        {/* Bullet Points (Amazon) */}
        {platform === 'amazon' && data.bullet_points && (
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">
              Bullet Points (5 exactos)
            </label>
            <div className="space-y-2">
              {data.bullet_points.map((bullet, i) => (
                <textarea
                  key={i}
                  value={bullet}
                  onChange={(e) => {
                    const newBullets = [...data.bullet_points]
                    newBullets[i] = e.target.value
                    onEdit(platform, 'bullet_points', newBullets)
                  }}
                  rows={2}
                  className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  placeholder={`Bullet ${i + 1}`}
                />
              ))}
            </div>
          </div>
        )}

        {/* Tags (Shopify) */}
        {platform === 'shopify' && data.tags && (
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">Tags</label>
            <div className="flex flex-wrap gap-1">
              {data.tags.map((tag, i) => (
                <span key={i} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Keywords (ML) */}
        {platform === 'mercadolibre' && data.keywords && (
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">Keywords</label>
            <div className="flex flex-wrap gap-1">
              {data.keywords.map((kw, i) => (
                <span key={i} className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* SEO (Shopify) */}
        {platform === 'shopify' && (
          <div className="border-t pt-3">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">SEO</p>
            <p className="text-xs text-gray-500 mb-1">Meta Title ({data.seo_title?.length || 0}/70)</p>
            <input
              type="text"
              value={data.seo_title || ''}
              onChange={(e) => onEdit(platform, 'seo_title', e.target.value)}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 mb-2"
            />
            <p className="text-xs text-gray-500 mb-1">Meta Description ({data.seo_description?.length || 0}/160)</p>
            <textarea
              value={data.seo_description || ''}
              onChange={(e) => onEdit(platform, 'seo_description', e.target.value)}
              rows={2}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>
        )}

      </div>
    </div>
  )
}

// ─── Componente Principal ─────────────────────────────────
export default function Publish() {
  // Formulario del producto
  const [form, setForm] = useState({
    name: '',
    description: '',
    category: '',
    brand: '',
    price: '',
    platforms: ['shopify', 'mercadolibre']
  })

  // Estado de la generación
  const [loading, setLoading] = useState(false)
  const [listing, setListing] = useState(null)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState(null)

  const handleFormChange = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  const handlePlatformToggle = (platform) => {
    setForm(prev => ({
      ...prev,
      platforms: prev.platforms.includes(platform)
        ? prev.platforms.filter(p => p !== platform)
        : [...prev.platforms, platform]
    }))
  }

  // Editar contenido generado por la IA
  const handleEdit = (platform, field, value) => {
    setListing(prev => ({
      ...prev,
      [platform]: {
        ...prev[platform],
        [field]: value
      }
    }))
  }

  // Generar contenido con IA
  const handleGenerate = async () => {
    if (!form.name.trim()) {
      setError('El nombre del producto es requerido')
      return
    }
    if (form.platforms.length === 0) {
      setError('Selecciona al menos una plataforma')
      return
    }

    setLoading(true)
    setError(null)
    setListing(null)

    try {
      const result = await aiService.generateListing({
        name: form.name,
        description: form.description,
        category: form.category,
        brand: form.brand,
        price: parseFloat(form.price) || 0,
        platforms: form.platforms
      })

      setListing(result.listing)
      setMessage({ type: 'success', text: '✅ Contenido generado correctamente. Revisa y edita antes de publicar.' })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto">

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">🤖</span>
          <h1 className="text-2xl font-bold text-gray-900">Publicar con IA</h1>
        </div>
        <p className="text-gray-600">
          Ingresa los datos básicos de tu producto y Claude generará contenido optimizado para cada plataforma automáticamente.
        </p>
      </div>

      {/* Mensaje */}
      {message && (
        <div className={`mb-6 p-4 rounded-lg ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {message.text}
          <button onClick={() => setMessage(null)} className="float-right font-bold">×</button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 text-red-700 border border-red-200">
          {error}
          <button onClick={() => setError(null)} className="float-right font-bold">×</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* ─── Formulario ─────────────────────────────────── */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-24">
            <h2 className="font-semibold text-gray-900 mb-4">📝 Datos del Producto</h2>

            <div className="space-y-4">

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => handleFormChange('name', e.target.value)}
                  placeholder="Ej: Filtro Polar Pro Hero 8"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descripción base</label>
                <textarea
                  value={form.description}
                  onChange={(e) => handleFormChange('description', e.target.value)}
                  placeholder="Describe brevemente el producto..."
                  rows={3}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Categoría</label>
                <input
                  type="text"
                  value={form.category}
                  onChange={(e) => handleFormChange('category', e.target.value)}
                  placeholder="Ej: Fotografía y Video"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Marca</label>
                <input
                  type="text"
                  value={form.brand}
                  onChange={(e) => handleFormChange('brand', e.target.value)}
                  placeholder="Ej: Polar Pro"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Precio (MXN)</label>
                <input
                  type="number"
                  value={form.price}
                  onChange={(e) => handleFormChange('price', e.target.value)}
                  placeholder="899.00"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Plataformas */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Plataformas</label>
                <div className="space-y-2">
                  {[
                    { id: 'shopify', label: '🛒 Shopify' },
                    { id: 'mercadolibre', label: '🤝 Mercado Libre' },
                    { id: 'amazon', label: '📦 Amazon' }
                  ].map(p => (
                    <label key={p.id} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={form.platforms.includes(p.id)}
                        onChange={() => handlePlatformToggle(p.id)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{p.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Botón Generar */}
              <button
                onClick={handleGenerate}
                disabled={loading || !form.name.trim()}
                className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                    Generando con IA...
                  </>
                ) : (
                  <>🤖 Generar con IA</>
                )}
              </button>

              {loading && (
                <p className="text-xs text-gray-500 text-center">
                  Claude está analizando tu producto... (10-20 segundos)
                </p>
              )}
            </div>
          </div>
        </div>

        {/* ─── Preview del contenido generado ─────────────── */}
        <div className="lg:col-span-2">
          {!listing && !loading && (
            <div className="bg-white rounded-xl border border-dashed border-gray-300 p-12 text-center">
              <span className="text-5xl mb-4 block">🤖</span>
              <h3 className="text-lg font-medium text-gray-700 mb-2">
                Listo para generar
              </h3>
              <p className="text-gray-500 text-sm">
                Llena los datos del producto y haz clic en "Generar con IA" para ver el contenido optimizado para cada plataforma.
              </p>
            </div>
          )}

          {loading && (
            <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <h3 className="text-lg font-medium text-gray-700 mb-2">Claude está trabajando...</h3>
              <p className="text-gray-500 text-sm">
                Analizando tu producto y generando contenido optimizado para {form.platforms.length} plataforma{form.platforms.length !== 1 ? 's' : ''}.
              </p>
            </div>
          )}

          {listing && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-gray-900">📋 Contenido Generado — Revisa y edita</h2>
                <button
                  onClick={handleGenerate}
                  disabled={loading}
                  className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                >
                  🔄 Regenerar
                </button>
              </div>

              {form.platforms.map(platform => (
                listing[platform] && (
                  <PlatformPreview
                    key={platform}
                    platform={platform}
                    data={listing[platform]}
                    onEdit={handleEdit}
                  />
                )
              ))}

              {/* Botón Publicar (próxima fase) */}
              <div className="bg-gray-50 rounded-xl border border-gray-200 p-4 text-center">
                <p className="text-sm text-gray-500 mb-3">
                  ¿El contenido está listo? Próximamente podrás publicar en todas las plataformas con un solo clic.
                </p>
                <button
                  disabled
                  className="px-6 py-2 bg-gray-300 text-gray-500 rounded-lg text-sm cursor-not-allowed"
                >
                  🚀 Publicar en todas las plataformas (Próximamente)
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
