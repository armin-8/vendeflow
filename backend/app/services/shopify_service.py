"""
VendeFlow - Servicio de Shopify
================================

Este servicio maneja la comunicación con la API de Shopify.

ENDPOINTS QUE USAMOS:
---------------------
- GET  /products.json         → Obtener productos
- GET  /inventory_levels.json → Obtener niveles de inventario
- POST /inventory_levels/set  → Actualizar inventario

AUTENTICACIÓN:
--------------
Shopify usa un Access Token que se envía en el header:
X-Shopify-Access-Token: {token}

ESTRUCTURA DE PRODUCTO EN SHOPIFY:
----------------------------------
{
    "id": 123456789,
    "title": "Cámara Sony",
    "variants": [
        {
            "id": 987654321,
            "sku": "CAM-001",
            "price": "999.99",
            "inventory_item_id": 111222333,
            "inventory_quantity": 10
        }
    ]
}

Nota: Un producto puede tener múltiples variantes (tallas, colores, etc.)
Cada variante tiene su propio SKU e inventario.
"""

import os
import requests
from typing import List, Dict, Optional, Tuple


class ShopifyService:
    """
    Servicio para interactuar con la API de Shopify.
    """
    
    def __init__(self):
        """
        Inicializa el servicio con las credenciales del .env
        """
        self.store_name = os.getenv('SHOPIFY_STORE_NAME')
        self.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        self.api_version = '2024-01'  # Versión de la API
        
        # URL base de la API
        self.base_url = f"https://{self.store_name}.myshopify.com/admin/api/{self.api_version}"
        
        # Headers para todas las peticiones
        self.headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
    
    # ═══════════════════════════════════════════════════════════
    # VERIFICAR CONEXIÓN
    # ═══════════════════════════════════════════════════════════
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Prueba la conexión con Shopify.
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            # Intentamos obtener info de la tienda
            response = requests.get(
                f"{self.base_url}/shop.json",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                shop_data = response.json().get('shop', {})
                shop_name = shop_data.get('name', 'Tienda')
                return True, f"Conectado a: {shop_name}"
            else:
                return False, f"Error {response.status_code}: {response.text}"
        
        except requests.exceptions.RequestException as e:
            return False, f"Error de conexión: {str(e)}"
    
    # ═══════════════════════════════════════════════════════════
    # OBTENER PRODUCTOS
    # ═══════════════════════════════════════════════════════════
    
    def get_products(self, limit: int = 250) -> Tuple[List[Dict], Optional[str]]:
        """
        Obtiene todos los productos de Shopify.
        
        ¿POR QUÉ 250?
        Shopify limita a 250 productos por petición.
        Para tiendas con más productos, hay que paginar.
        
        Args:
            limit: Número máximo de productos (max 250)
        
        Returns:
            Tuple[List[Dict], Optional[str]]: (productos, error)
        """
        try:
            products = []
            url = f"{self.base_url}/products.json?limit={limit}"
            
            while url:
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code != 200:
                    return [], f"Error {response.status_code}: {response.text}"
                
                data = response.json()
                products.extend(data.get('products', []))
                
                # Verificar si hay más páginas (paginación de Shopify)
                link_header = response.headers.get('Link', '')
                if 'rel="next"' in link_header:
                    # Extraer URL de la siguiente página
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
    # CONVERTIR PRODUCTOS DE SHOPIFY A FORMATO VENDEFLOW
    # ═══════════════════════════════════════════════════════════
    
    def normalize_products(self, shopify_products: List[Dict]) -> List[Dict]:
        """
        Convierte productos de Shopify al formato de VendeFlow.
        
        IMPORTANTE:
        - Un producto de Shopify puede tener múltiples variantes
        - Cada variante es un "producto" en VendeFlow
        - Usamos el SKU de la variante como identificador
        
        Args:
            shopify_products: Lista de productos de Shopify
        
        Returns:
            List[Dict]: Lista de productos en formato VendeFlow
        """
        normalized = []
        
        for product in shopify_products:
            # Datos comunes del producto
            product_title = product.get('title', '')
            product_description = product.get('body_html', '')
            product_vendor = product.get('vendor', '')  # Marca
            product_type = product.get('product_type', '')  # Categoría
            
            # Imagen principal (si existe)
            images = product.get('images', [])
            image_url = images[0].get('src', '') if images else None
            
            # Procesar cada variante
            for variant in product.get('variants', []):
                sku = variant.get('sku', '').strip()
                
                # Si no tiene SKU, saltar esta variante
                if not sku:
                    continue
                
                # Crear nombre del producto
                # Si tiene variante (talla, color), agregarlo al nombre
                variant_title = variant.get('title', '')
                if variant_title and variant_title != 'Default Title':
                    name = f"{product_title} - {variant_title}"
                else:
                    name = product_title
                
                normalized_product = {
                    'sku': sku.upper(),
                    'name': name,
                    'description': product_description,
                    'price': float(variant.get('price', 0)),
                    'cost': float(variant.get('cost', 0) or 0),
                    'quantity': variant.get('inventory_quantity', 0),
                    'category': product_type,
                    'brand': product_vendor,
                    'image_url': image_url,
                    # IDs de Shopify para sincronización
                    'shopify_product_id': product.get('id'),
                    'shopify_variant_id': variant.get('id'),
                    'shopify_inventory_item_id': variant.get('inventory_item_id'),
                }
                
                normalized.append(normalized_product)
        
        return normalized
    
    # ═══════════════════════════════════════════════════════════
    # OBTENER UBICACIONES DE INVENTARIO
    # ═══════════════════════════════════════════════════════════
    
    def get_locations(self) -> Tuple[List[Dict], Optional[str]]:
        """
        Obtiene las ubicaciones de inventario de Shopify.
        
        ¿QUÉ ES UNA UBICACIÓN?
        En Shopify, el inventario se almacena en "ubicaciones"
        (bodegas, tiendas físicas, etc.)
        Necesitamos el ID de la ubicación para actualizar stock.
        
        Returns:
            Tuple[List[Dict], Optional[str]]: (ubicaciones, error)
        """
        try:
            response = requests.get(
                f"{self.base_url}/locations.json",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code != 200:
                return [], f"Error {response.status_code}: {response.text}"
            
            locations = response.json().get('locations', [])
            return locations, None
        
        except requests.exceptions.RequestException as e:
            return [], f"Error de conexión: {str(e)}"
    
    # ═══════════════════════════════════════════════════════════
    # ACTUALIZAR INVENTARIO
    # ═══════════════════════════════════════════════════════════
    
    def update_inventory(self, inventory_item_id: int, location_id: int, quantity: int) -> Tuple[bool, str]:
        """
        Actualiza el nivel de inventario de un producto en Shopify.
        
        Args:
            inventory_item_id: ID del item de inventario (de la variante)
            location_id: ID de la ubicación
            quantity: Nueva cantidad
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            response = requests.post(
                f"{self.base_url}/inventory_levels/set.json",
                headers=self.headers,
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


# ═══════════════════════════════════════════════════════════
# INSTANCIA GLOBAL DEL SERVICIO
# ═══════════════════════════════════════════════════════════

# Creamos una instancia que se puede importar en otros archivos
shopify_service = ShopifyService()
