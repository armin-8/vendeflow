"""
VendeFlow - Servicio de Shopify con OAuth
==========================================

Este servicio maneja:
1. Flujo OAuth para conectar tiendas
2. Comunicación con la API de Shopify
3. Sincronización de productos e inventario

FLUJO OAUTH:
------------
1. get_auth_url() → URL para redirigir al usuario a Shopify
2. exchange_code_for_token() → Intercambiar código por access_token
3. Guardar token en PlatformConnection

ENDPOINTS DE SHOPIFY QUE USAMOS:
---------------------------------
- GET  /products.json         → Obtener productos
- GET  /inventory_levels.json → Obtener niveles de inventario
- POST /inventory_levels/set  → Actualizar inventario
"""

import os
import hmac
import hashlib
import requests
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlencode


class ShopifyService:
    """
    Servicio para interactuar con la API de Shopify usando OAuth.
    """
    
    def __init__(self):
        """
        Inicializa el servicio con las credenciales OAuth del .env
        """
        self.api_key = os.getenv('SHOPIFY_API_KEY')
        self.api_secret = os.getenv('SHOPIFY_API_SECRET')
        self.scopes = os.getenv('SHOPIFY_SCOPES', 'read_products,write_products,read_inventory,write_inventory')
        self.redirect_uri = os.getenv('SHOPIFY_REDIRECT_URI', 'http://localhost:5001/api/shopify/callback')
        self.api_version = '2024-01'
    
    # ═══════════════════════════════════════════════════════════
    # OAUTH: GENERAR URL DE AUTORIZACIÓN
    # ═══════════════════════════════════════════════════════════
    
    def get_auth_url(self, shop_name: str, state: str) -> str:
        """
        Genera la URL para redirigir al usuario a Shopify para autorización.
        """
        params = {
            'client_id': self.api_key,
            'scope': self.scopes,
            'redirect_uri': self.redirect_uri,
            'state': state,
        }
        
        shop_name = shop_name.replace('.myshopify.com', '').strip()
        
        return f"https://{shop_name}.myshopify.com/admin/oauth/authorize?{urlencode(params)}"
    
    # ═══════════════════════════════════════════════════════════
    # OAUTH: INTERCAMBIAR CÓDIGO POR TOKEN
    # ═══════════════════════════════════════════════════════════
    
    def exchange_code_for_token(self, shop_name: str, code: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Intercambia el código de autorización por un access token.
        """
        shop_name = shop_name.replace('.myshopify.com', '').strip()
        
        url = f"https://{shop_name}.myshopify.com/admin/oauth/access_token"
        
        payload = {
            'client_id': self.api_key,
            'client_secret': self.api_secret,
            'code': code,
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get('access_token')
                scope = data.get('scope')
                return access_token, scope, None
            else:
                return None, None, f"Error {response.status_code}: {response.text}"
        
        except requests.exceptions.RequestException as e:
            return None, None, f"Error de conexión: {str(e)}"
    
    # ═══════════════════════════════════════════════════════════
    # OAUTH: VERIFICAR HMAC (SEGURIDAD)
    # ═══════════════════════════════════════════════════════════
    
    def verify_hmac(self, query_params: dict) -> bool:
        """
        Verifica que la solicitud viene realmente de Shopify.
        """
        hmac_value = query_params.get('hmac', '')
        
        params = {k: v for k, v in query_params.items() if k != 'hmac'}
        sorted_params = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        
        calculated_hmac = hmac.new(
            self.api_secret.encode('utf-8'),
            sorted_params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(calculated_hmac, hmac_value)
    
    # ═══════════════════════════════════════════════════════════
    # API: VERIFICAR CONEXIÓN
    # ═══════════════════════════════════════════════════════════
    
    def test_connection(self, shop_name: str, access_token: str) -> Tuple[bool, str]:
        """
        Prueba la conexión con una tienda de Shopify.
        """
        shop_name = shop_name.replace('.myshopify.com', '').strip()
        
        url = f"https://{shop_name}.myshopify.com/admin/api/{self.api_version}/shop.json"
        headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                shop_data = response.json().get('shop', {})
                name = shop_data.get('name', 'Tienda')
                return True, f"Conectado a: {name}"
            else:
                return False, f"Error {response.status_code}: {response.text}"
        
        except requests.exceptions.RequestException as e:
            return False, f"Error de conexión: {str(e)}"
    
    # ═══════════════════════════════════════════════════════════
    # API: OBTENER PRODUCTOS
    # ═══════════════════════════════════════════════════════════
    
    def get_products(self, shop_name: str, access_token: str, limit: int = 250) -> Tuple[List[Dict], Optional[str]]:
        """
        Obtiene todos los productos de una tienda Shopify.
        """
        shop_name = shop_name.replace('.myshopify.com', '').strip()
        
        headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
        
        try:
            products = []
            url = f"https://{shop_name}.myshopify.com/admin/api/{self.api_version}/products.json?limit={limit}"
            
            while url:
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code != 200:
                    return [], f"Error {response.status_code}: {response.text}"
                
                data = response.json()
                products.extend(data.get('products', []))
                
                # Paginación
                link_header = response.headers.get('Link', '')
                if 'rel="next"' in link_header:
                    for link in link_header.split(','):
                        if 'rel="next"' in link:
                            url = link.split(';')[0].strip('<> ')
                            break
                else:
                    url = None
            
            return products, None
        
        except requests.exceptions.RequestException as e:
            return [], f"Error de conexión: {str(e)}"
    
    # ═══════════════════════════════════════════════════════════
    # API: NORMALIZAR PRODUCTOS
    # ═══════════════════════════════════════════════════════════
    
    def normalize_products(self, shopify_products: List[Dict]) -> List[Dict]:
        """
        Convierte productos de Shopify al formato de VendeFlow.
        """
        normalized = []
        
        for product in shopify_products:
            product_title = product.get('title', '')
            product_description = product.get('body_html', '')
            product_vendor = product.get('vendor', '')
            product_type = product.get('product_type', '')
            
            images = product.get('images', [])
            image_url = images[0].get('src', '') if images else None
            
            for variant in product.get('variants', []):
                # Manejar SKU que puede ser None
                sku = variant.get('sku') or ''
                sku = sku.strip() if isinstance(sku, str) else ''
                
                if not sku:
                    continue
                
                variant_title = variant.get('title', '')
                if variant_title and variant_title != 'Default Title':
                    name = f"{product_title} - {variant_title}"
                else:
                    name = product_title
                
                normalized_product = {
                    'sku': sku.upper(),
                    'name': name,
                    'description': product_description,
                    'price': float(variant.get('price', 0) or 0),
                    'cost': float(variant.get('cost', 0) or 0),
                    'quantity': variant.get('inventory_quantity', 0) or 0,
                    'category': product_type,
                    'brand': product_vendor,
                    'image_url': image_url,
                    'shopify_product_id': product.get('id'),
                    'shopify_variant_id': variant.get('id'),
                    'shopify_inventory_item_id': variant.get('inventory_item_id'),
                }
                
                normalized.append(normalized_product)
        
        return normalized
    
    # ═══════════════════════════════════════════════════════════
    # API: OBTENER UBICACIONES
    # ═══════════════════════════════════════════════════════════
    
    def get_locations(self, shop_name: str, access_token: str) -> Tuple[List[Dict], Optional[str]]:
        """
        Obtiene las ubicaciones de inventario de Shopify.
        """
        shop_name = shop_name.replace('.myshopify.com', '').strip()
        
        headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
        
        try:
            url = f"https://{shop_name}.myshopify.com/admin/api/{self.api_version}/locations.json"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return [], f"Error {response.status_code}: {response.text}"
            
            locations = response.json().get('locations', [])
            return locations, None
        
        except requests.exceptions.RequestException as e:
            return [], f"Error de conexión: {str(e)}"
    
    # ═══════════════════════════════════════════════════════════
    # API: ACTUALIZAR INVENTARIO
    # ═══════════════════════════════════════════════════════════
    
    def update_inventory(self, shop_name: str, access_token: str, 
                        inventory_item_id: int, location_id: int, quantity: int) -> Tuple[bool, str]:
        """
        Actualiza el nivel de inventario de un producto en Shopify.
        """
        shop_name = shop_name.replace('.myshopify.com', '').strip()
        
        headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
        
        try:
            url = f"https://{shop_name}.myshopify.com/admin/api/{self.api_version}/inventory_levels/set.json"
            
            response = requests.post(
                url,
                headers=headers,
                json={
                    'location_id': location_id,
                    'inventory_item_id': inventory_item_id,
                    'available': quantity
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "Inventario actualizado"
            else:
                return False, f"Error {response.status_code}: {response.text}"
        
        except requests.exceptions.RequestException as e:
            return False, f"Error de conexión: {str(e)}"


# Instancia global
shopify_service = ShopifyService()
