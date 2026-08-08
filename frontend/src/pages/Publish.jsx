/**
 * VendeFlow - Página de Publicación con IA
 * ==========================================
 * 
 * Flujo:
 * 1. Usuario llena datos básicos + URLs de imágenes
 * 2. IA genera contenido optimizado por plataforma
 * 3. Usuario revisa y edita (human in the loop)
 * 4. Usuario publica en Shopify como BORRADOR
 */

import { useState } from 'react'
import { shopifyService } from '../services/api'

const API_URL = import.meta.env.VITE_API_URL || '/api'

const aiService = {
  generateListing: async (data) => {
    const authData = JSON.parse(localStorage.getItem('vendeflow-auth') || '{}')
    const token = authData?.state?.token
    const response = await fetch(`${API_URL}/ai/generate-listing`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(data)
    })
    const result = await response.json()
    if (!response.ok) throw new Error(result.error || 'Error al generar contenido')
    return result
  }
}

// ─── Componente: Sección de Imágenes ─────────────────────
function ImageSection({ imageUrls, onChange }) {
  const [newUrl, setNewUrl] = useState('')

  const addImage = () => {
    const url = newUrl.trim()
    if (!url) return
    if (imageUrls.includes(url)) return
    onChange([...imageUrls, url])
    setNewUrl('')
  }

  const removeImage = (index) => {
    onChange(imageUrls.filter((_, i) => i !== index))
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); addImage() }
  }

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Imágenes del Producto
      </label>
      <p className="text-xs text-gray-500 mb-2">
        Shopify recomienda <strong>2048x2048px</strong> JPG o PNG.
        La primera imagen es la principal.
      </p>

      {/* Input para agregar URL */}
      <div className="flex gap-2 mb-3">
        <input
          type="url"
          value={newUrl}
          onChange={(e) => setNewUrl(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="https://ejemplo.com/imagen.jpg"
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="button"
          onClick={addImage}
          disabled={!newUrl.trim()}
          className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          + Agregar
        </button>
      </div>

      {/* Preview de imágenes agregadas */}
      {imageUrls.length > 0 && (
        <div className="space-y-2">
          {imageUrls.map((url, index) => (
            <div key={index} className="flex items-center gap-3 bg-gray-50 rounded-lg p-2">
              {/* Preview de la imagen */}
              <img
                src={url}
                alt={`Imagen ${index + 1}`}
                className="w-12 h-12 object-cover rounded-lg border border-gray-200"
                onError={(e) => { e.target.src = 'https://via.placeholder.com/48?text=?' }}
              />
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-600 truncate">{url}</p>
                {index === 0 && (
                  <span className="text-xs text-green-600 font-medium">⭐ Imagen principal</span>
                )}
              </div>
              <button
                onClick={() => removeImage(index)}
                className="text-red-400 hover:text-red-600 text-lg font-bold flex-shrink-0"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {imageUrls.length === 0 && (
        <p className="text-xs text-gray-400 italic">Sin imágenes agregadas (opcional)</p>
      )}
    </div>
  )
}

// ─── Preview por Plataforma ───────────────────────────────
function PlatformPreview({ platform, data, onEdit }) {
  const configs = {
    shopify: { name: 'Shopify', icon: '🛒', bgColor: 'bg-green-50', borderColor: 'border-green-200', badgeColor: 'bg-green-100 text-green-700' },
    mercadolibre: { name: 'Mercado Libre', icon: '🤝', bgColor: 'bg-yellow-50', borderColor: 'border-yellow-200', badgeColor: 'bg-yellow-100 text-yellow-700' },
    amazon: { name: 'Amazon', icon: '📦', bgColor: 'bg-orange-50', borderColor: 'border-orange-200', badgeColor: 'bg-orange-100 text-orange-700' }
  }
  const config = configs[platform]

  return (
    <div className={`border ${config.borderColor} rounded-xl overflow-hidden`}>
      <div className={`${config.bgColor} px-4 py-3 flex items-center justify-between border-b ${config.borderColor}`}>
        <div className="flex items-center gap-2">
          <span className="text-lg">{config.icon}</span>
          <span className="font-semibold text-gray-800">{config.name}</span>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${config.badgeColor}`}>✅ Generado</span>
      </div>

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
          <textarea value={data.title || ''} onChange={(e) => onEdit(platform, 'title', e.target.value)}
            rows={2} className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 resize-none" />
        </div>

        {/* Descripción */}
        {(platform === 'shopify' || platform === 'mercadolibre') && (
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">
              {platform === 'shopify' ? 'Descripción (HTML)' : 'Descripción (Texto plano)'}
            </label>
            <textarea
              value={platform === 'shopify' ? (data.description_html || '') : (data.description || '')}
              onChange={(e) => onEdit(platform, platform === 'shopify' ? 'description_html' : 'description', e.target.value)}
              rows={5} className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 resize-none font-mono" />
          </div>
        )}

        {/* Bullet Points Amazon */}
        {platform === 'amazon' && data.bullet_points && (
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">Bullet Points (5 exactos)</label>
            <div className="space-y-2">
              {data.bullet_points.map((bullet, i) => (
                <textarea key={i} value={bullet}
                  onChange={(e) => { const b = [...data.bullet_points]; b[i] = e.target.value; onEdit(platform, 'bullet_points', b) }}
                  rows={2} className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 resize-none" />
              ))}
            </div>
          </div>
        )}

        {/* Tags Shopify */}
        {platform === 'shopify' && data.tags && (
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">Tags</label>
            <div className="flex flex-wrap gap-1">
              {data.tags.map((tag, i) => <span key={i} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">{tag}</span>)}
            </div>
          </div>
        )}

        {/* Keywords ML */}
        {platform === 'mercadolibre' && data.keywords && (
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">Keywords</label>
            <div className="flex flex-wrap gap-1">
              {data.keywords.map((kw, i) => <span key={i} className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">{kw}</span>)}
            </div>
          </div>
        )}

        {/* SEO Shopify */}
        {platform === 'shopify' && (
          <div className="border-t pt-3">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">SEO</p>
            <p className="text-xs text-gray-500 mb-1">Meta Title ({data.seo_title?.length || 0}/70)</p>
            <input type="text" value={data.seo_title || ''} onChange={(e) => onEdit(platform, 'seo_title', e.target.value)}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 mb-2" />
            <p className="text-xs text-gray-500 mb-1">Meta Description ({data.seo_description?.length || 0}/160)</p>
            <textarea value={data.seo_description || ''} onChange={(e) => onEdit(platform, 'seo_description', e.target.value)}
              rows={2} className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 resize-none" />
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Componente Principal ─────────────────────────────────
export default function Publish() {
  const [form, setForm] = useState({
    name: '', description: '', category: '', brand: '',
    price: '', sku: '', quantity: '',
    weight: '', barcode: '',
    imageUrls: [],
    platforms: ['shopify']
  })

  const [loading, setLoading] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [listing, setListing] = useState(null)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState(null)

  const handleFormChange = (field, value) => setForm(prev => ({ ...prev, [field]: value }))

  const handlePlatformToggle = (platform) => {
    setForm(prev => ({
      ...prev,
      platforms: prev.platforms.includes(platform)
        ? prev.platforms.filter(p => p !== platform)
        : [...prev.platforms, platform]
    }))
  }

  const handleEdit = (platform, field, value) => {
    setListing(prev => ({ ...prev, [platform]: { ...prev[platform], [field]: value } }))
  }

  const handleGenerate = async () => {
    if (!form.name.trim()) return setError('El nombre del producto es requerido')
    if (form.platforms.length === 0) return setError('Selecciona al menos una plataforma')

    setLoading(true)
    setError(null)
    setListing(null)
    setMessage(null)

    try {
      const result = await aiService.generateListing({
        name: form.name, description: form.description,
        category: form.category, brand: form.brand,
        price: parseFloat(form.price) || 0,
        platforms: form.platforms
      })
      setListing(result.listing)
      setMessage({ type: 'success', text: '✅ Contenido generado. Revisa y edita antes de publicar.' })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handlePublishShopify = async () => {
    if (!form.sku.trim()) return setError('El SKU es requerido para publicar')
    if (!form.price) return setError('El precio es requerido para publicar')

    setPublishing(true)
    setError(null)

    try {
      const shopifyData = listing?.shopify || {}
      const result = await shopifyService.createProduct({
        title: shopifyData.title || form.name,
        body_html: shopifyData.description_html || '',
        vendor: form.brand || '',
        product_type: form.category || '',
        tags: shopifyData.tags || [],
        sku: form.sku.toUpperCase(),
        price: parseFloat(form.price) || 0,
        quantity: parseInt(form.quantity) || 0,
        weight: parseFloat(form.weight) || 0,
        weight_unit: 'kg',
        barcode: form.barcode || '',
        seo_title: shopifyData.seo_title || '',
        seo_description: shopifyData.seo_description || '',
        image_urls: form.imageUrls   // ← imágenes enviadas a Shopify
      })

      setMessage({
        type: 'success',
        text: `✅ ${result.message}`,
        link: result.admin_url
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setPublishing(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">🤖</span>
          <h1 className="text-2xl font-bold text-gray-900">Publicar con IA</h1>
        </div>
        <p className="text-gray-600">La IA genera contenido optimizado para cada plataforma. Tú revisas y publicas.</p>
      </div>

      {message && (
        <div className={`mb-6 p-4 rounded-lg ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {message.text}
          {message.link && (
            <a href={message.link} target="_blank" rel="noreferrer" className="ml-2 underline font-medium">
              Ver en Shopify →
            </a>
          )}
          <button onClick={() => setMessage(null)} className="float-right font-bold">×</button>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 text-red-700 border border-red-200">
          {error}
          <button onClick={() => setError(null)} className="float-right font-bold">×</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* ─── Formulario ─────────────────────────────────── */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-24 max-h-screen overflow-y-auto">
            <h2 className="font-semibold text-gray-900 mb-4">📝 Datos del Producto</h2>
            <div className="space-y-4">

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre <span className="text-red-500">*</span></label>
                <input type="text" value={form.name} onChange={(e) => handleFormChange('name', e.target.value)}
                  placeholder="Ej: Filtro Polar Pro Hero 8"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">SKU <span className="text-red-500">*</span></label>
                  <input type="text" value={form.sku} onChange={(e) => handleFormChange('sku', e.target.value)}
                    placeholder="H8-001"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Stock</label>
                  <input type="number" value={form.quantity} onChange={(e) => handleFormChange('quantity', e.target.value)}
                    placeholder="10"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Precio (MXN) <span className="text-red-500">*</span></label>
                <input type="number" value={form.price} onChange={(e) => handleFormChange('price', e.target.value)}
                  placeholder="899.00"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Peso (kg)</label>
                  <input type="number" value={form.weight} onChange={(e) => handleFormChange('weight', e.target.value)}
                    placeholder="0.5"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Código de barras</label>
                  <input type="text" value={form.barcode} onChange={(e) => handleFormChange('barcode', e.target.value)}
                    placeholder="EAN / UPC"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Marca</label>
                <input type="text" value={form.brand} onChange={(e) => handleFormChange('brand', e.target.value)}
                  placeholder="Ej: Polar Pro"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Categoría</label>
                <input type="text" value={form.category} onChange={(e) => handleFormChange('category', e.target.value)}
                  placeholder="Ej: Fotografía y Video"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descripción base</label>
                <textarea value={form.description} onChange={(e) => handleFormChange('description', e.target.value)}
                  placeholder="Describe brevemente el producto..." rows={2}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 resize-none" />
              </div>

              {/* ─── Imágenes ─────────────────────────────── */}
              <ImageSection
                imageUrls={form.imageUrls}
                onChange={(urls) => handleFormChange('imageUrls', urls)}
              />

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
                      <input type="checkbox" checked={form.platforms.includes(p.id)}
                        onChange={() => handlePlatformToggle(p.id)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" />
                      <span className="text-sm text-gray-700">{p.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <button onClick={handleGenerate} disabled={loading || !form.name.trim()}
                className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                {loading ? (
                  <><svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                  </svg>Generando...</>
                ) : <>🤖 Generar con IA</>}
              </button>

              {loading && <p className="text-xs text-gray-500 text-center">Llama está analizando... (15-30 seg)</p>}
            </div>
          </div>
        </div>

        {/* ─── Preview ──────────────────────────────────────── */}
        <div className="lg:col-span-2">
          {!listing && !loading && (
            <div className="bg-white rounded-xl border border-dashed border-gray-300 p-12 text-center">
              <span className="text-5xl mb-4 block">🤖</span>
              <h3 className="text-lg font-medium text-gray-700 mb-2">Listo para generar</h3>
              <p className="text-gray-500 text-sm">Llena los datos y haz clic en "Generar con IA".</p>
            </div>
          )}

          {loading && (
            <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <h3 className="text-lg font-medium text-gray-700 mb-2">Generando contenido...</h3>
              <p className="text-gray-500 text-sm">Llama 3.2 optimizando para {form.platforms.length} plataforma{form.platforms.length !== 1 ? 's' : ''}.</p>
            </div>
          )}

          {listing && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-gray-900">📋 Contenido Generado — Revisa y edita</h2>
                <button onClick={handleGenerate} disabled={loading} className="text-sm text-blue-600 hover:text-blue-700">🔄 Regenerar</button>
              </div>

              {/* Preview de imágenes seleccionadas */}
              {form.imageUrls.length > 0 && (
                <div className="bg-gray-50 rounded-xl border border-gray-200 p-4">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
                    📸 Imágenes a publicar ({form.imageUrls.length})
                  </p>
                  <div className="flex gap-3 flex-wrap">
                    {form.imageUrls.map((url, i) => (
                      <div key={i} className="relative">
                        <img src={url} alt={`img ${i+1}`}
                          className="w-20 h-20 object-cover rounded-lg border border-gray-200"
                          onError={(e) => { e.target.src = 'https://via.placeholder.com/80?text=?' }} />
                        {i === 0 && (
                          <span className="absolute -top-1 -right-1 bg-green-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">★</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {form.platforms.map(platform => (
                listing[platform] && (
                  <PlatformPreview key={platform} platform={platform} data={listing[platform]} onEdit={handleEdit} />
                )
              ))}

              {/* Botón Publicar Shopify */}
              {form.platforms.includes('shopify') && listing?.shopify && (
                <div className="bg-green-50 rounded-xl border border-green-200 p-5">
                  <h3 className="font-semibold text-green-800 mb-1">🛒 Publicar en Shopify</h3>
                  <p className="text-sm text-green-700 mb-3">
                    El producto se creará como <strong>borrador</strong> con{' '}
                    {form.imageUrls.length > 0
                      ? <><strong>{form.imageUrls.length} imagen{form.imageUrls.length > 1 ? 'es' : ''}</strong> incluida{form.imageUrls.length > 1 ? 's' : ''}.</>
                      : 'sin imágenes (puedes agregarlas después en el admin de Shopify).'}
                  </p>

                  {(!form.sku || !form.price) && (
                    <p className="text-xs text-orange-600 mb-3">⚠️ Necesitas SKU y Precio para publicar.</p>
                  )}

                  <button
                    onClick={handlePublishShopify}
                    disabled={publishing || !form.sku || !form.price}
                    className="w-full py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {publishing ? (
                      <><svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                      </svg>Publicando en Shopify...</>
                    ) : <>🚀 Publicar en Shopify como Borrador</>}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
