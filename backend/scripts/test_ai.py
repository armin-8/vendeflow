"""
Script para probar el endpoint de IA sin necesitar el frontend.
Obtiene un token JWT y llama al endpoint de generación de listing.

Uso:
    cd ~/Desktop/vendeflow/backend
    source venv/bin/activate
    PYTHONPATH=. python scripts/test_ai.py
"""
import requests
import json

BASE_URL = "http://localhost:5001/api"

# ─── PASO 1: Obtener token JWT ────────────────────────────
print("🔐 Obteniendo token JWT...")

login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "armin.perez@ardistribucion.mx",
    "password": "tu_password_aqui"  # ← cambia esto
})

if login_response.status_code != 200:
    # Si no funciona el login, intenta registrar
    print("Login falló, intentando registrar usuario de prueba...")
    reg_response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": "test_ai@vendeflow.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "AI"
    })
    token = reg_response.json().get("token")
else:
    token = login_response.json().get("token")

if not token:
    print("❌ No se pudo obtener token. Verifica que el backend esté corriendo.")
    exit(1)

print(f"✅ Token obtenido")

# ─── PASO 2: Llamar al endpoint de IA ────────────────────
print("\n🤖 Llamando a Claude API para generar listing...")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

payload = {
    "name": "Filtro Polar Pro GoPro Hero 8",
    "description": "Filtro para buceo y fotografía submarina, elimina reflejos",
    "category": "Fotografía y Video",
    "brand": "Polar Pro",
    "price": 899.00,
    "platforms": ["shopify", "mercadolibre"]
}

response = requests.post(
    f"{BASE_URL}/ai/generate-listing",
    headers=headers,
    json=payload
)

# ─── PASO 3: Mostrar resultado ────────────────────────────
print(f"\nStatus: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    listing = data.get("listing", {})

    print("\n" + "="*60)
    print("✅ SHOPIFY")
    print("="*60)
    shopify = listing.get("shopify", {})
    print(f"Título: {shopify.get('title', '')}")
    print(f"SEO Title: {shopify.get('seo_title', '')}")
    print(f"Tags: {shopify.get('tags', [])}")
    print(f"Descripción HTML (primeros 200 chars):")
    print(shopify.get('description_html', '')[:200] + "...")

    print("\n" + "="*60)
    print("✅ MERCADO LIBRE")
    print("="*60)
    ml = listing.get("mercadolibre", {})
    titulo_ml = ml.get('title', '')
    print(f"Título: {titulo_ml}")
    print(f"Caracteres: {len(titulo_ml)} {'✅' if len(titulo_ml) <= 60 else '❌ EXCEDE 60'}")
    print(f"Category hint: {ml.get('category_hint', '')}")
    print(f"Keywords: {ml.get('keywords', [])}")

    print("\n📄 JSON completo guardado en: scripts/test_ai_result.json")
    with open("scripts/test_ai_result.json", "w", encoding="utf-8") as f:
        json.dump(listing, f, ensure_ascii=False, indent=2)
else:
    print(f"❌ Error: {response.json()}")
