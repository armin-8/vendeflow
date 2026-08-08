"""
VendeFlow - Servicio de Shopify con OAuth
==========================================

Este servicio maneja:
1. Flujo OAuth para conectar tiendas
2. Comunicación con la API de Shopify
3. Sincronización de productos e inventario
4. Creación de productos desde la IA con imágenes
"""

import os
import hmac
import hashlib
import requests
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlencode


class ShopifyService:

    def __init__(self):
        self.api_key = os.getenv('SHOPIFY_API_KEY')
        self.api_secret = os.getenv('SHOPIFY_API_SECRET')
        self.scopes = os.getenv('SHOPIFY_SCOPES', 'read_products,write_products,read_inventory,write_inventory')
        self.redirect_uri = os.getenv('SHOPIFY_REDIRECT_URI', 'http://localhost:5001/api/shopify/callback')
        self.api_version = '2024-01'

    # ═══════════════════════════════════════════════════════════
    # OAUTH
    # ═══════════════════════════════════════════════════════════

    def get_auth_url(self, shop_name: str, state: str) -> str:
        params = {
            'client_id': self.api_key,
            'scope': self.scopes,
            'redirect_uri': self.redirect_uri,
            'state': state,
        }
        shop_name = shop_name.replace('.myshopify.com', '').strip()
        return f"https://{shop_name}.myshopify.com/admin/oauth/authorize?{urlencode(params)}"

    def exchange_code_for_token(self, shop_name: str, code: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        shop_name = shop_name.replace('.myshopify.com', '').strip()
        url = f"https://{shop_name}.myshopify.com/admin/oauth/access_token"
        payload = {'client_id': self.api_key, 'client_secret': self.api_secret, 'code': code}
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('access_token'), data.get('scope'), None
            return None, None, f"Error {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return None, None, f"Error de conexión: {str(e)}"

    def verify_hmac(self, query_params: dict) -> bool:
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
        shop_name = shop_name.replace('.myshopify.com', '').strip()
        url = f"https://{shop_name}.myshopify.com/admin/api/{self.api_version}/shop.json"
        headers = {'X-Shopify-Access-Token': access_token, 'Content-Type': 'application/json'}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                name = response.json().get('shop', {}).get('name', 'Tienda')
                return True, f"Conectado a: {name}"
            return False, f"Error {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Error de conexión: {str(e)}"

    # ═══════════════════════════════════════════════════════════
    # API: OBTENER PRODUCTOS
    # ═══════════════════════════════════════════════════════════

    def get_products(self, shop_name: str, access_token: str, limit: int = 250) -> Tuple[List[Dict], Optional[str]]:
        shop_name = shop_name.replace('.myshopify.com', '').strip()
        headers = {'X-Shopify-Access-Token': access_token, 'Content-Type': 'application/json'}
        try:
            products = []
            url = f"https://{shop_name}.myshopify.com/admin/api/{self.api_version}/products.json?limit={limit}"
            while url:
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code != 200:
                    return [], f"Error {response.status_code}: {response.text}"
                data = response.json()
                products.extend(data.get('products', []))
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
        normalized = []
        for product in shopify_products:
            product_title = product.get('title', '')
            product_description = product.get('body_html', '')
            product_vendor = product.get('vendor', '')
            product_type = product.get('product_type', '')
            images = product.get('images', [])
            image_url = images[0].get('src', '') if images else None
            for variant in product.get('variants', []):
                sku = variant.get('sku') or ''
                sku = sku.strip() if isinstance(sku, str) else ''
                if not sku:
                    continue
                variant_title = variant.get('title', '')
                name = f"{product_title} - {variant_title}" if variant_title and variant_title != 'Default Title' else product_title
                normalized.append({
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
                })
        return normalized

    # ═══════════════════════════════════════════════════════════
    # API: OBTENER UBICACIONES
    # ═══════════════════════════════════════════════════════════

    def get_locations(self, shop_name: str, access_token: str) -> Tuple[List[Dict], Optional[str]]:
        shop_name = shop_name.replace('.myshopify.com', '').strip()
        headers = {'X-Shopify-Access-Token': access_token, 'Content-Type': 'application/json'}
        try:
            url = f"https://{shop_name}.myshopify.com/admin/api/{self.api_version}/locations.json"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return [], f"Error {response.status_code}: {response.text}"
            return response.json().get('locations', []), None
        except requests.exceptions.RequestException as e:
            return [], f"Error de conexión: {str(e)}"

    # ═══════════════════════════════════════════════════════════
    # API: ACTUALIZAR INVENTARIO
    # ═══════════════════════════════════════════════════════════

    def update_inventory(self, shop_name: str, access_token: str,
                         inventory_item_id: int, location_id: int, quantity: int) -> Tuple[bool, str]:
        shop_name = shop_name.replace('.myshopify.com', '').strip()
        headers = {'X-Shopify-Access-Token': access_token, 'Content-Type': 'application/json'}
        try:
            url = f"https://{shop_name}.myshopify.com/admin/api/{self.api_version}/inventory_levels/set.json"
            response = requests.post(url, headers=headers, json={
                'location_id': location_id,
                'inventory_item_id': inventory_item_id,
                'available': quantity
            }, timeout=10)
            if response.status_code == 200:
                return True, "Inventario actualizado"
            return False, f"Error {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Error de conexión: {str(e)}"

    # ═══════════════════════════════════════════════════════════
    # API: CREAR PRODUCTO EN SHOPIFY (desde IA) con imágenes
    # ═══════════════════════════════════════════════════════════

    def create_product(self, shop_name: str, access_token: str, product_data: dict) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Crea un producto en Shopify con contenido de IA e imágenes.

        CAMPOS SOPORTADOS:
        ------------------
        title          → Título del producto
        body_html      → Descripción en HTML (generada por IA)
        vendor         → Marca
        product_type   → Categoría
        tags           → Lista de tags
        sku            → SKU único
        price          → Precio en MXN
        quantity       → Stock inicial
        weight         → Peso (para cálculo de envío)
        weight_unit    → 'kg', 'g', 'lb', 'oz'
        barcode        → Código de barras (EAN, UPC, ISBN)
        seo_title      → Meta title (max 70 chars)
        seo_description→ Meta description (max 160 chars)
        image_urls     → Lista de URLs de imágenes
                         Shopify recomienda 2048x2048px
                         La primera URL es la imagen principal

        ¿POR QUÉ DRAFT?
        ----------------
        El producto se crea como borrador para que el usuario
        lo revise y active en el admin de Shopify.
        """
        shop_name = shop_name.replace('.myshopify.com', '').strip()
        headers = {'X-Shopify-Access-Token': access_token, 'Content-Type': 'application/json'}

        # ─── Construir variante ───────────────────────────────
        variant = {
            "sku": product_data.get('sku', ''),
            "price": str(product_data.get('price', '0.00')),
            "inventory_management": "shopify",
            "inventory_quantity": int(product_data.get('quantity', 0)),
            "fulfillment_service": "manual",
        }

        # Peso (opcional pero recomendado para cálculo de envío)
        if product_data.get('weight'):
            variant['weight'] = float(product_data.get('weight', 0))
            variant['weight_unit'] = product_data.get('weight_unit', 'kg')

        # Código de barras (opcional)
        if product_data.get('barcode'):
            variant['barcode'] = product_data.get('barcode', '')

        # ─── Construir payload principal ─────────────────────
        payload = {
            "product": {
                "title": product_data.get('title', ''),
                "body_html": product_data.get('body_html', ''),
                "vendor": product_data.get('vendor', ''),
                "product_type": product_data.get('product_type', ''),
                "tags": ', '.join(product_data.get('tags', [])),
                "status": "draft",
                "variants": [variant],
                "metafields": [
                    {
                        "namespace": "global",
                        "key": "title_tag",
                        "value": product_data.get('seo_title', ''),
                        "type": "single_line_text_field"
                    },
                    {
                        "namespace": "global",
                        "key": "description_tag",
                        "value": product_data.get('seo_description', ''),
                        "type": "single_line_text_field"
                    }
                ]
            }
        }

        # ─── IMÁGENES ─────────────────────────────────────────
        # Shopify descarga las imágenes desde las URLs automáticamente.
        # Recomienda 2048x2048px JPG o PNG para alta calidad.
        # La primera imagen de la lista es la imagen principal del producto.
        #
        # Shopify las procesa y almacena en su CDN → no importa
        # el tamaño original, pero a mayor resolución mejor calidad.
        # ─────────────────────────────────────────────────────
        image_urls = product_data.get('image_urls', [])
        if image_urls:
            payload["product"]["images"] = [
                {
                    "src": url.strip(),
                    "alt": product_data.get('title', '')
                }
                for url in image_urls
                if url and url.strip()
            ]

        try:
            url = f"https://{shop_name}.myshopify.com/admin/api/{self.api_version}/products.json"
            response = requests.post(url, headers=headers, json=payload, timeout=15)

            if response.status_code == 201:
                created = response.json().get('product', {})
                return created, None
            else:
                errors = response.json().get('errors', response.text)
                return None, f"Error {response.status_code}: {errors}"

        except requests.exceptions.RequestException as e:
            return None, f"Error de conexión: {str(e)}"


# Instancia global
shopify_service = ShopifyService()
