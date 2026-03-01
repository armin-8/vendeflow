"""
VendeFlow - Rutas de Shopify con OAuth
=======================================

FLUJO OAUTH:
------------
1. GET  /api/shopify/connect?shop=tienda    → Inicia OAuth, redirige a Shopify
2. GET  /api/shopify/callback               → Shopify regresa aquí con código
3. GET  /api/shopify/status                 → Verificar si está conectado
4. GET  /api/shopify/products               → Obtener productos
5. POST /api/shopify/import                 → Importar productos a VendeFlow
6. POST /api/shopify/sync                   → Sincronizar inventario → Shopify
7. DELETE /api/shopify/disconnect           → Desconectar tienda
"""

import os
import secrets
from datetime import datetime
from flask import Blueprint, jsonify, request, redirect

from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.product import Product
from app.models.platform_connection import PlatformConnection
from app.services.shopify_service import shopify_service

bp = Blueprint('shopify', __name__, url_prefix='/api/shopify')


# ═══════════════════════════════════════════════════════════
# ENDPOINT: INICIAR CONEXIÓN (OAuth Step 1)
# ═══════════════════════════════════════════════════════════

@bp.route('/connect', methods=['GET'])
@jwt_required()
def connect_shopify():
    """
    Inicia el flujo OAuth con Shopify.
    """
    user_id = get_jwt_identity()
    shop = request.args.get('shop', '').strip()
    
    if not shop:
        return jsonify({
            'success': False,
            'error': 'Se requiere el nombre de la tienda (shop)'
        }), 400
    
    # Limpiar nombre de tienda
    shop = shop.replace('.myshopify.com', '').replace('https://', '').replace('http://', '')
    
    # Codificar user_id y shop en el state (para no depender de sesiones)
    # Formato: random_token:user_id:shop
    random_token = secrets.token_urlsafe(16)
    state = f"{random_token}:{user_id}:{shop}"
    
    # Obtener URL de autorización
    auth_url = shopify_service.get_auth_url(shop, state)
    
    # Retornar URL (el frontend redirigirá)
    return jsonify({
        'success': True,
        'auth_url': auth_url,
        'shop': shop
    }), 200


# ═══════════════════════════════════════════════════════════
# ENDPOINT: CALLBACK DE SHOPIFY (OAuth Step 2)
# ═══════════════════════════════════════════════════════════

@bp.route('/callback', methods=['GET'])
def shopify_callback():
    """
    Shopify redirige aquí después de que el usuario autoriza.
    """
    # Obtener parámetros
    code = request.args.get('code')
    shop = request.args.get('shop', '').replace('.myshopify.com', '')
    state = request.args.get('state')
    
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    
    # Decodificar state (formato: random_token:user_id:shop)
    if not state:
        return redirect(f"{frontend_url}/integrations?error=invalid_state")
    
    try:
        state_parts = state.split(':')
        if len(state_parts) != 3:
            raise ValueError("Invalid state format")
        _, user_id, saved_shop = state_parts
    except:
        return redirect(f"{frontend_url}/integrations?error=invalid_state")
    
    # Verificar shop
    if not shop or shop != saved_shop:
        return redirect(f"{frontend_url}/integrations?error=invalid_shop")
    
    # Intercambiar código por token
    access_token, scope, error = shopify_service.exchange_code_for_token(shop, code)
    
    if error:
        print(f"Token exchange error: {error}")
        return redirect(f"{frontend_url}/integrations?error=token_exchange_failed")
    
    # Verificar que el token funciona
    success, message = shopify_service.test_connection(shop, access_token)
    
    if not success:
        print(f"Connection test failed: {message}")
        return redirect(f"{frontend_url}/integrations?error=connection_test_failed")
    
    # Guardar conexión en base de datos
    try:
        # Verificar si ya existe una conexión para esta tienda
        existing = PlatformConnection.query.filter_by(
            user_id=int(user_id),
            platform='shopify',
            store_name=shop
        ).first()
        
        if existing:
            # Actualizar token existente
            existing.access_token = access_token
            existing.scope = scope
            existing.is_active = True
            existing.connected_at = datetime.utcnow()
        else:
            # Crear nueva conexión
            connection = PlatformConnection(
                user_id=int(user_id),
                platform='shopify',
                store_name=shop,
                access_token=access_token,
                scope=scope,
                is_active=True
            )
            db.session.add(connection)
        
        db.session.commit()
        print(f"Connection saved for user {user_id}, shop {shop}")
        
        # Redirigir al frontend con éxito
        return redirect(f"{frontend_url}/integrations?success=shopify_connected&shop={shop}")
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return redirect(f"{frontend_url}/integrations?error=database_error")


# ═══════════════════════════════════════════════════════════
# ENDPOINT: VERIFICAR ESTADO DE CONEXIÓN
# ═══════════════════════════════════════════════════════════

@bp.route('/status', methods=['GET'])
@jwt_required()
def check_status():
    """
    Verifica si el usuario tiene una tienda Shopify conectada.
    """
    user_id = get_jwt_identity()
    
    # Buscar conexión activa
    connection = PlatformConnection.query.filter_by(
        user_id=int(user_id),
        platform='shopify',
        is_active=True
    ).first()
    
    if not connection:
        return jsonify({
            'connected': False,
            'message': 'No hay tienda Shopify conectada'
        }), 200
    
    # Verificar que el token sigue funcionando
    success, message = shopify_service.test_connection(
        connection.store_name, 
        connection.access_token
    )
    
    if not success:
        return jsonify({
            'connected': False,
            'message': 'La conexión expiró. Reconecta tu tienda.',
            'store_name': connection.store_name
        }), 200
    
    return jsonify({
        'connected': True,
        'message': message,
        'store_name': connection.store_name,
        'connected_at': connection.connected_at.isoformat() if connection.connected_at else None,
        'last_synced_at': connection.last_synced_at.isoformat() if connection.last_synced_at else None
    }), 200


# ═══════════════════════════════════════════════════════════
# ENDPOINT: OBTENER PRODUCTOS DE SHOPIFY
# ═══════════════════════════════════════════════════════════

@bp.route('/products', methods=['GET'])
@jwt_required()
def get_shopify_products():
    """
    Obtiene la lista de productos de Shopify.
    """
    user_id = get_jwt_identity()
    
    # Obtener conexión
    connection = PlatformConnection.query.filter_by(
        user_id=int(user_id),
        platform='shopify',
        is_active=True
    ).first()
    
    if not connection:
        return jsonify({
            'success': False,
            'error': 'No hay tienda Shopify conectada'
        }), 400
    
    # Obtener productos
    shopify_products, error = shopify_service.get_products(
        connection.store_name,
        connection.access_token
    )
    
    if error:
        return jsonify({
            'success': False,
            'error': error
        }), 400
    
    # Normalizar
    normalized = shopify_service.normalize_products(shopify_products)
    
    return jsonify({
        'success': True,
        'products': normalized,
        'total': len(normalized),
        'store_name': connection.store_name
    }), 200


# ═══════════════════════════════════════════════════════════
# ENDPOINT: IMPORTAR PRODUCTOS A VENDEFLOW
# ═══════════════════════════════════════════════════════════

@bp.route('/import', methods=['POST'])
@jwt_required()
def import_from_shopify():
    """
    Importa productos de Shopify a VendeFlow.
    """
    user_id = get_jwt_identity()
    
    # Obtener conexión
    connection = PlatformConnection.query.filter_by(
        user_id=int(user_id),
        platform='shopify',
        is_active=True
    ).first()
    
    if not connection:
        return jsonify({
            'success': False,
            'error': 'No hay tienda Shopify conectada'
        }), 400
    
    # Obtener opciones
    data = request.get_json() or {}
    update_existing = data.get('update_existing', True)
    
    # Obtener productos de Shopify
    shopify_products, error = shopify_service.get_products(
        connection.store_name,
        connection.access_token
    )
    
    if error:
        return jsonify({
            'success': False,
            'error': f'Error al obtener productos: {error}'
        }), 400
    
    # Normalizar
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
            existing = Product.query.filter_by(
                user_id=int(user_id),
                sku=sku,
                is_active=True
            ).first()
            
            if existing:
                if update_existing:
                    existing.name = product_data['name']
                    existing.description = product_data.get('description')
                    existing.price = product_data['price']
                    existing.cost = product_data.get('cost')
                    existing.quantity = product_data.get('quantity', 0)
                    existing.category = product_data.get('category')
                    existing.brand = product_data.get('brand')
                    existing.image_url = product_data.get('image_url')
                    existing.shopify_id = str(product_data.get('shopify_variant_id'))
                    updated += 1
                else:
                    skipped += 1
            else:
                new_product = Product(
                    user_id=int(user_id),
                    sku=sku,
                    name=product_data['name'],
                    description=product_data.get('description'),
                    price=product_data['price'],
                    cost=product_data.get('cost'),
                    quantity=product_data.get('quantity', 0),
                    min_stock=5,
                    category=product_data.get('category'),
                    brand=product_data.get('brand'),
                    image_url=product_data.get('image_url'),
                    shopify_id=str(product_data.get('shopify_variant_id'))
                )
                db.session.add(new_product)
                created += 1
        
        except Exception as e:
            errors.append(f'Error con SKU {sku}: {str(e)}')
    
    # Guardar y actualizar last_synced_at
    try:
        connection.last_synced_at = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Error al guardar: {str(e)}'
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
    
    BODY (opcional):
    {
        "sku": "ABC-123"  // Si se proporciona, solo sincroniza ese SKU
    }
    """
    user_id = get_jwt_identity()
    
    # Obtener SKU específico si se proporcionó
    data = request.get_json() or {}
    single_sku = data.get('sku')
    
    # Obtener conexión
    connection = PlatformConnection.query.filter_by(
        user_id=int(user_id),
        platform='shopify',
        is_active=True
    ).first()
    
    if not connection:
        return jsonify({
            'success': False,
            'error': 'No hay tienda Shopify conectada'
        }), 400
    
    # Obtener ubicaciones
    locations, error = shopify_service.get_locations(
        connection.store_name,
        connection.access_token
    )
    
    if error or not locations:
        return jsonify({
            'success': False,
            'error': 'No se pudieron obtener las ubicaciones de Shopify'
        }), 400
    
    location_id = locations[0].get('id')
    
    # Obtener productos vinculados
    query = Product.query.filter(
        Product.user_id == int(user_id),
        Product.is_active == True,
        Product.shopify_id != None
    )
    
    # Si hay SKU específico, filtrar solo ese
    if single_sku:
        query = query.filter(Product.sku == single_sku.upper())
    
    products = query.all()
    
    if not products:
        return jsonify({
            'success': False,
            'error': f'No se encontró el producto con SKU: {single_sku}' if single_sku else 'No hay productos vinculados con Shopify'
        }), 400
    
    # Mapear variant_id -> inventory_item_id
    shopify_products, _ = shopify_service.get_products(
        connection.store_name,
        connection.access_token
    )
    
    variant_to_inventory = {}
    for product in shopify_products:
        for variant in product.get('variants', []):
            variant_id = str(variant.get('id'))
            inventory_item_id = variant.get('inventory_item_id')
            variant_to_inventory[variant_id] = inventory_item_id
    
    # Sincronizar
    synced = 0
    failed = 0
    errors = []
    
    for product in products:
        try:
            inventory_item_id = variant_to_inventory.get(product.shopify_id)
            
            if not inventory_item_id:
                errors.append(f'SKU {product.sku}: No se encontró en Shopify')
                failed += 1
                continue
            
            success, message = shopify_service.update_inventory(
                connection.store_name,
                connection.access_token,
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
    
    # Actualizar last_synced_at
    connection.last_synced_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'synced': synced,
        'failed': failed,
        'errors': errors,
        'message': f'Sincronización completada: {synced} actualizados, {failed} fallidos'
    }), 200


# ═══════════════════════════════════════════════════════════
# ENDPOINT: DESCONECTAR TIENDA
# ═══════════════════════════════════════════════════════════

@bp.route('/disconnect', methods=['DELETE'])
@jwt_required()
def disconnect_shopify():
    """
    Desconecta la tienda Shopify del usuario.
    """
    user_id = get_jwt_identity()
    
    connection = PlatformConnection.query.filter_by(
        user_id=int(user_id),
        platform='shopify',
        is_active=True
    ).first()
    
    if not connection:
        return jsonify({
            'success': False,
            'error': 'No hay tienda conectada'
        }), 400
    
    # Desactivar (soft delete)
    connection.is_active = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Tienda {connection.store_name} desconectada'
    }), 200
