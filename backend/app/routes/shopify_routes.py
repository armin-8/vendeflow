"""
VendeFlow - Rutas de Shopify
=============================

Endpoints para integración con Shopify.

ENDPOINTS:
----------
GET  /api/shopify/status     → Verificar conexión
GET  /api/shopify/products   → Obtener productos de Shopify
POST /api/shopify/import     → Importar productos a VendeFlow
POST /api/shopify/sync       → Sincronizar inventario VendeFlow → Shopify
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.product import Product
from app.services.shopify_service import shopify_service

bp = Blueprint('shopify', __name__, url_prefix='/api/shopify')


# ═══════════════════════════════════════════════════════════
# ENDPOINT: VERIFICAR CONEXIÓN
# ═══════════════════════════════════════════════════════════

@bp.route('/status', methods=['GET'])
@jwt_required()
def check_status():
    """
    Verifica si la conexión con Shopify está funcionando.
    
    RESPONSE:
    ---------
    {
        "connected": true/false,
        "message": "Conectado a: Mi Tienda"
    }
    """
    success, message = shopify_service.test_connection()
    
    return jsonify({
        'connected': success,
        'message': message
    }), 200 if success else 400


# ═══════════════════════════════════════════════════════════
# ENDPOINT: OBTENER PRODUCTOS DE SHOPIFY
# ═══════════════════════════════════════════════════════════

@bp.route('/products', methods=['GET'])
@jwt_required()
def get_shopify_products():
    """
    Obtiene la lista de productos directamente de Shopify.
    
    Útil para ver qué productos hay antes de importar.
    
    RESPONSE:
    ---------
    {
        "success": true,
        "products": [...],
        "total": 150
    }
    """
    # Obtener productos de Shopify
    shopify_products, error = shopify_service.get_products()
    
    if error:
        return jsonify({
            'success': False,
            'error': error
        }), 400
    
    # Normalizar al formato VendeFlow
    normalized = shopify_service.normalize_products(shopify_products)
    
    return jsonify({
        'success': True,
        'products': normalized,
        'total': len(normalized)
    }), 200


# ═══════════════════════════════════════════════════════════
# ENDPOINT: IMPORTAR PRODUCTOS A VENDEFLOW
# ═══════════════════════════════════════════════════════════

@bp.route('/import', methods=['POST'])
@jwt_required()
def import_from_shopify():
    """
    Importa productos de Shopify a VendeFlow.
    
    PROCESO:
    --------
    1. Obtiene productos de Shopify
    2. Para cada producto:
       - Si el SKU ya existe en VendeFlow: actualiza
       - Si es nuevo: crea el producto
    3. Guarda el shopify_id para sincronización futura
    
    REQUEST:
    --------
    {
        "update_existing": true/false  // Si actualizar productos existentes
    }
    
    RESPONSE:
    ---------
    {
        "success": true,
        "created": 100,
        "updated": 50,
        "skipped": 5,
        "errors": [...]
    }
    """
    user_id = get_jwt_identity()
    
    # Obtener opciones
    data = request.get_json() or {}
    update_existing = data.get('update_existing', True)
    
    # Obtener productos de Shopify
    shopify_products, error = shopify_service.get_products()
    
    if error:
        return jsonify({
            'success': False,
            'error': f'Error al obtener productos de Shopify: {error}'
        }), 400
    
    # Normalizar productos
    products = shopify_service.normalize_products(shopify_products)
    
    if not products:
        return jsonify({
            'success': False,
            'error': 'No se encontraron productos con SKU en Shopify'
        }), 400
    
    # Procesar cada producto
    created = 0
    updated = 0
    skipped = 0
    errors = []
    
    for product_data in products:
        sku = product_data['sku']
        
        try:
            # Buscar si ya existe
            existing = Product.query.filter_by(
                user_id=int(user_id),
                sku=sku,
                is_active=True
            ).first()
            
            if existing:
                if update_existing:
                    # Actualizar producto existente
                    existing.name = product_data['name']
                    existing.description = product_data.get('description')
                    existing.price = product_data['price']
                    existing.cost = product_data.get('cost')
                    existing.quantity = product_data.get('quantity', 0)
                    existing.category = product_data.get('category')
                    existing.brand = product_data.get('brand')
                    existing.image_url = product_data.get('image_url')
                    # Guardar ID de Shopify
                    existing.shopify_id = str(product_data.get('shopify_variant_id'))
                    updated += 1
                else:
                    skipped += 1
            else:
                # Crear nuevo producto
                new_product = Product(
                    user_id=int(user_id),
                    sku=sku,
                    name=product_data['name'],
                    description=product_data.get('description'),
                    price=product_data['price'],
                    cost=product_data.get('cost'),
                    quantity=product_data.get('quantity', 0),
                    min_stock=5,  # Default
                    category=product_data.get('category'),
                    brand=product_data.get('brand'),
                    image_url=product_data.get('image_url'),
                    shopify_id=str(product_data.get('shopify_variant_id'))
                )
                db.session.add(new_product)
                created += 1
        
        except Exception as e:
            errors.append(f'Error con SKU {sku}: {str(e)}')
    
    # Guardar cambios
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Error al guardar en base de datos: {str(e)}'
        }), 500
    
    return jsonify({
        'success': True,
        'created': created,
        'updated': updated,
        'skipped': skipped,
        'errors': errors,
        'message': f'Importación completada: {created} creados, {updated} actualizados'
    }), 200


# ═══════════════════════════════════════════════════════════
# ENDPOINT: SINCRONIZAR INVENTARIO A SHOPIFY
# ═══════════════════════════════════════════════════════════

@bp.route('/sync', methods=['POST'])
@jwt_required()
def sync_to_shopify():
    """
    Sincroniza el inventario de VendeFlow hacia Shopify.
    
    PROCESO:
    --------
    1. Obtiene productos de VendeFlow que tienen shopify_id
    2. Obtiene la ubicación principal de Shopify
    3. Para cada producto: actualiza el stock en Shopify
    
    RESPONSE:
    ---------
    {
        "success": true,
        "synced": 100,
        "failed": 5,
        "errors": [...]
    }
    """
    user_id = get_jwt_identity()
    
    # Obtener ubicaciones de Shopify
    locations, error = shopify_service.get_locations()
    
    if error or not locations:
        return jsonify({
            'success': False,
            'error': 'No se pudieron obtener las ubicaciones de Shopify'
        }), 400
    
    # Usar la primera ubicación (principal)
    location_id = locations[0].get('id')
    
    # Obtener productos de VendeFlow que tienen shopify_id
    products = Product.query.filter(
        Product.user_id == int(user_id),
        Product.is_active == True,
        Product.shopify_id != None
    ).all()
    
    if not products:
        return jsonify({
            'success': False,
            'error': 'No hay productos vinculados con Shopify'
        }), 400
    
    # Sincronizar cada producto
    synced = 0
    failed = 0
    errors = []
    
    # Primero necesitamos obtener el inventory_item_id de cada variante
    # Para esto necesitamos mapear shopify_id (variant_id) -> inventory_item_id
    
    # Obtener todos los productos de Shopify para mapear
    shopify_products, _ = shopify_service.get_products()
    
    # Crear mapa de variant_id -> inventory_item_id
    variant_to_inventory = {}
    for product in shopify_products:
        for variant in product.get('variants', []):
            variant_id = str(variant.get('id'))
            inventory_item_id = variant.get('inventory_item_id')
            variant_to_inventory[variant_id] = inventory_item_id
    
    # Sincronizar
    for product in products:
        try:
            inventory_item_id = variant_to_inventory.get(product.shopify_id)
            
            if not inventory_item_id:
                errors.append(f'SKU {product.sku}: No se encontró en Shopify')
                failed += 1
                continue
            
            success, message = shopify_service.update_inventory(
                inventory_item_id=inventory_item_id,
                location_id=location_id,
                quantity=product.quantity
            )
            
            if success:
                synced += 1
            else:
                errors.append(f'SKU {product.sku}: {message}')
                failed += 1
        
        except Exception as e:
            errors.append(f'SKU {product.sku}: {str(e)}')
            failed += 1
    
    return jsonify({
        'success': True,
        'synced': synced,
        'failed': failed,
        'errors': errors,
        'message': f'Sincronización completada: {synced} actualizados, {failed} fallidos'
    }), 200
