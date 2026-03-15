"""
VendeFlow - Rutas de Mercado Libre con OAuth
=============================================

Mismo patrón que shopify_routes.py, adaptado a las diferencias de ML.

FLUJO OAUTH:
------------
1. GET  /api/mercadolibre/connect       → Inicia OAuth, redirige a ML
2. GET  /api/mercadolibre/callback      → ML regresa aquí con código
3. GET  /api/mercadolibre/status        → Verificar si está conectado
4. GET  /api/mercadolibre/products      → Obtener publicaciones de ML
5. POST /api/mercadolibre/import        → Importar publicaciones a VendeFlow
6. POST /api/mercadolibre/sync          → Sincronizar stock → ML
7. DELETE /api/mercadolibre/disconnect  → Desconectar cuenta

¿QUÉ ES DIFERENTE A SHOPIFY?
------------------------------
- connect: No necesita 'shop', ML es una sola plataforma global
- callback: Guarda refresh_token, external_user_id y token_expires_at
- status:   Usa get_valid_token() por si el token expiró
- sync:     Actualiza 'available_quantity' en cada publicación de ML
"""

import os
import secrets
from datetime import datetime
from flask import Blueprint, jsonify, request, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.product import Product
from app.models.platform_connection import PlatformConnection
from app.services.mercadolibre_service import mercadolibre_service

bp = Blueprint('mercadolibre', __name__, url_prefix='/api/mercadolibre')


# ═══════════════════════════════════════════════════════════
# ENDPOINT 1: INICIAR CONEXIÓN (OAuth Paso 1)
# ═══════════════════════════════════════════════════════════

@bp.route('/connect', methods=['GET'])
@jwt_required()
def connect_mercadolibre():
    """
    Inicia el flujo OAuth con Mercado Libre.

    A diferencia de Shopify, NO necesitamos el nombre de una tienda.
    ML es una plataforma única — el usuario autoriza su cuenta personal.

    Codificamos el user_id en el 'state' para recuperarlo en el callback
    sin depender de sesiones del servidor.
    """
    user_id = get_jwt_identity()

    # Generamos un token aleatorio + user_id en el state
    # Formato: random_token:user_id
    random_token = secrets.token_urlsafe(16)
    state = f"{random_token}:{user_id}"

    auth_url = mercadolibre_service.get_auth_url(state)

    return jsonify({
        'success': True,
        'auth_url': auth_url
    }), 200


# ═══════════════════════════════════════════════════════════
# ENDPOINT 2: CALLBACK DE ML (OAuth Paso 2)
# ═══════════════════════════════════════════════════════════

@bp.route('/callback', methods=['GET'])
def mercadolibre_callback():
    """
    ML redirige aquí después de que el usuario autoriza.

    ML nos envía:
    - code:  Código de autorización (lo intercambiamos por tokens)
    - state: El mismo state que enviamos en /connect

    Diferencias con Shopify:
    - Guardamos refresh_token (ML lo requiere para renovar)
    - Guardamos external_user_id (ID del usuario en ML)
    - Guardamos token_expires_at (ML expira en 6 horas)
    - store_name = nickname del usuario en ML (no es un dominio)
    """
    code = request.args.get('code')
    state = request.args.get('state', '')
    error = request.args.get('error')

    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')

    # Si ML devolvió un error (ej: usuario canceló)
    if error:
        return redirect(f"{frontend_url}/integrations?error=ml_auth_denied")

    if not code:
        return redirect(f"{frontend_url}/integrations?error=no_code")

    # Decodificar state → formato: random_token:user_id
    try:
        parts = state.split(':')
        if len(parts) != 2:
            raise ValueError("State inválido")
        _, user_id = parts
        user_id = int(user_id)
    except Exception:
        return redirect(f"{frontend_url}/integrations?error=invalid_state")

    # Intercambiar código por tokens
    token_data, error_msg = mercadolibre_service.exchange_code_for_token(code)

    if error_msg:
        print(f"[ML] Error al intercambiar código: {error_msg}")
        return redirect(f"{frontend_url}/integrations?error=token_exchange_failed")

    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    expires_at = token_data.get('expires_at')
    ml_user_id = str(token_data.get('user_id', ''))

    # Obtener info del usuario para usar su nickname como store_name
    user_info, info_error = mercadolibre_service.get_user_info(access_token)

    if info_error or not user_info:
        print(f"[ML] Error al obtener info de usuario: {info_error}")
        return redirect(f"{frontend_url}/integrations?error=user_info_failed")

    nickname = user_info.get('nickname', f'ML_{ml_user_id}')

    # Guardar o actualizar la conexión en base de datos
    try:
        existing = PlatformConnection.query.filter_by(
            user_id=user_id,
            platform='mercadolibre',
        ).first()

        if existing:
            # Actualizar tokens existentes
            existing.access_token = access_token
            existing.refresh_token = refresh_token
            existing.token_expires_at = expires_at
            existing.external_user_id = ml_user_id
            existing.store_name = nickname
            existing.is_active = True
            existing.connected_at = datetime.utcnow()
        else:
            # Crear nueva conexión
            connection = PlatformConnection(
                user_id=user_id,
                platform='mercadolibre',
                store_name=nickname,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=expires_at,
                external_user_id=ml_user_id,
                is_active=True
            )
            db.session.add(connection)

        db.session.commit()
        print(f"[ML] Conexión guardada: user_id={user_id}, nickname={nickname}")

        return redirect(f"{frontend_url}/integrations?success=ml_connected&account={nickname}")

    except Exception as e:
        db.session.rollback()
        print(f"[ML] Error al guardar conexión: {e}")
        return redirect(f"{frontend_url}/integrations?error=database_error")


# ═══════════════════════════════════════════════════════════
# ENDPOINT 3: VERIFICAR ESTADO DE CONEXIÓN
# ═══════════════════════════════════════════════════════════

@bp.route('/status', methods=['GET'])
@jwt_required()
def check_status():
    """
    Verifica si el usuario tiene una cuenta de ML conectada.

    Diferencia con Shopify: usamos get_valid_token() en lugar del
    access_token directo, porque el token puede haber expirado.
    """
    user_id = get_jwt_identity()

    connection = PlatformConnection.query.filter_by(
        user_id=int(user_id),
        platform='mercadolibre',
        is_active=True
    ).first()

    if not connection:
        return jsonify({
            'connected': False,
            'message': 'No hay cuenta de Mercado Libre conectada'
        }), 200

    # Obtener token válido (refresca automáticamente si expiró)
    access_token, token_error = mercadolibre_service.get_valid_token(connection)

    if token_error:
        return jsonify({
            'connected': False,
            'message': 'La sesión expiró. Reconecta tu cuenta de Mercado Libre.',
            'account': connection.store_name
        }), 200

    # Verificar que el token funciona realmente
    success, message = mercadolibre_service.test_connection(access_token)

    if not success:
        return jsonify({
            'connected': False,
            'message': 'La conexión falló. Reconecta tu cuenta.',
            'account': connection.store_name
        }), 200

    return jsonify({
        'connected': True,
        'message': message,
        'account': connection.store_name,
        'ml_user_id': connection.external_user_id,
        'connected_at': connection.connected_at.isoformat() if connection.connected_at else None,
        'last_synced_at': connection.last_synced_at.isoformat() if connection.last_synced_at else None,
        'token_expires_at': connection.token_expires_at.isoformat() if connection.token_expires_at else None,
    }), 200


# ═══════════════════════════════════════════════════════════
# ENDPOINT 4: OBTENER PUBLICACIONES DE ML
# ═══════════════════════════════════════════════════════════

@bp.route('/products', methods=['GET'])
@jwt_required()
def get_ml_products():
    """
    Obtiene las publicaciones activas del usuario en ML.

    Proceso:
    1. Obtener token válido
    2. Obtener lista de IDs de publicaciones
    3. Obtener detalles de cada publicación (en lotes de 20)
    4. Normalizar al formato VendeFlow
    """
    user_id = get_jwt_identity()

    connection = PlatformConnection.query.filter_by(
        user_id=int(user_id),
        platform='mercadolibre',
        is_active=True
    ).first()

    if not connection:
        return jsonify({
            'success': False,
            'error': 'No hay cuenta de Mercado Libre conectada'
        }), 400

    # Token válido (auto-refresca si expiró)
    access_token, token_error = mercadolibre_service.get_valid_token(connection)
    if token_error:
        return jsonify({'success': False, 'error': token_error}), 401

    # Obtener IDs de publicaciones
    item_ids, error = mercadolibre_service.get_user_items(
        access_token,
        connection.external_user_id
    )

    if error:
        return jsonify({'success': False, 'error': error}), 400

    if not item_ids:
        return jsonify({
            'success': True,
            'products': [],
            'total': 0,
            'message': 'No se encontraron publicaciones en Mercado Libre'
        }), 200

    # Obtener detalles de cada publicación
    items, error = mercadolibre_service.get_items_details(access_token, item_ids)

    if error:
        return jsonify({'success': False, 'error': error}), 400

    # Normalizar al formato VendeFlow
    normalized = mercadolibre_service.normalize_items(items)

    return jsonify({
        'success': True,
        'products': normalized,
        'total': len(normalized),
        'account': connection.store_name
    }), 200


# ═══════════════════════════════════════════════════════════
# ENDPOINT 5: IMPORTAR PUBLICACIONES A VENDEFLOW
# ═══════════════════════════════════════════════════════════

@bp.route('/import', methods=['POST'])
@jwt_required()
def import_from_ml():
    """
    Importa publicaciones de ML al inventario de VendeFlow.

    Mismo patrón que shopify/import:
    - Si el SKU ya existe → actualiza (si update_existing=True)
    - Si no existe        → crea nuevo producto
    - Guarda el mercadolibre_item_id para poder sincronizar después

    BODY (opcional):
    {
        "update_existing": true
    }
    """
    user_id = get_jwt_identity()

    connection = PlatformConnection.query.filter_by(
        user_id=int(user_id),
        platform='mercadolibre',
        is_active=True
    ).first()

    if not connection:
        return jsonify({'success': False, 'error': 'No hay cuenta de Mercado Libre conectada'}), 400

    data = request.get_json() or {}
    update_existing = data.get('update_existing', True)

    # Token válido
    access_token, token_error = mercadolibre_service.get_valid_token(connection)
    if token_error:
        return jsonify({'success': False, 'error': token_error}), 401

    # Obtener publicaciones
    item_ids, error = mercadolibre_service.get_user_items(access_token, connection.external_user_id)
    if error:
        return jsonify({'success': False, 'error': error}), 400

    if not item_ids:
        return jsonify({'success': False, 'error': 'No hay publicaciones en Mercado Libre'}), 400

    items, error = mercadolibre_service.get_items_details(access_token, item_ids)
    if error:
        return jsonify({'success': False, 'error': error}), 400

    products = mercadolibre_service.normalize_items(items)

    if not products:
        return jsonify({'success': False, 'error': 'No se encontraron publicaciones para importar'}), 400

    # Procesar cada producto — mismo patrón que Shopify
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
                    existing.price = product_data['price']
                    existing.quantity = product_data.get('quantity', 0)
                    existing.image_url = product_data.get('image_url')
                    existing.mercadolibre_id = product_data.get('mercadolibre_item_id')
                    updated += 1
                else:
                    skipped += 1
            else:
                new_product = Product(
                    user_id=int(user_id),
                    sku=sku,
                    name=product_data['name'],
                    price=product_data['price'],
                    quantity=product_data.get('quantity', 0),
                    min_stock=5,
                    image_url=product_data.get('image_url'),
                    mercadolibre_id=product_data.get('mercadolibre_item_id')
                )
                db.session.add(new_product)
                created += 1

        except Exception as e:
            errors.append(f'Error con SKU {sku}: {str(e)}')

    try:
        connection.last_synced_at = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error al guardar: {str(e)}'}), 500

    return jsonify({
        'success': True,
        'created': created,
        'updated': updated,
        'skipped': skipped,
        'errors': errors,
        'message': f'Importación completada: {created} creados, {updated} actualizados'
    }), 200


# ═══════════════════════════════════════════════════════════
# ENDPOINT 6: SINCRONIZAR STOCK → MERCADO LIBRE
# ═══════════════════════════════════════════════════════════

@bp.route('/sync', methods=['POST'])
@jwt_required()
def sync_to_ml():
    """
    Sincroniza el stock de VendeFlow hacia las publicaciones de ML.

    Para cada producto que tenga mercadolibre_id:
    → Actualiza 'available_quantity' en la publicación de ML

    BODY (opcional):
    {
        "sku": "ABC-123"  // Si se proporciona, solo sincroniza ese SKU
    }
    """
    user_id = get_jwt_identity()

    data = request.get_json() or {}
    single_sku = data.get('sku')

    connection = PlatformConnection.query.filter_by(
        user_id=int(user_id),
        platform='mercadolibre',
        is_active=True
    ).first()

    if not connection:
        return jsonify({'success': False, 'error': 'No hay cuenta de Mercado Libre conectada'}), 400

    # Token válido (auto-refresca si expiró)
    access_token, token_error = mercadolibre_service.get_valid_token(connection)
    if token_error:
        return jsonify({'success': False, 'error': token_error}), 401

    # Obtener productos vinculados a ML
    query = Product.query.filter(
        Product.user_id == int(user_id),
        Product.is_active == True,
        Product.mercadolibre_id != None
    )

    if single_sku:
        query = query.filter(Product.sku == single_sku.upper())

    products = query.all()

    if not products:
        msg = f'No se encontró el SKU: {single_sku}' if single_sku else 'No hay productos vinculados con Mercado Libre'
        return jsonify({'success': False, 'error': msg}), 400

    # Sincronizar stock en cada publicación
    synced = 0
    failed = 0
    errors = []

    for product in products:
        success, message = mercadolibre_service.update_stock(
            access_token,
            product.mercadolibre_id,
            product.quantity
        )

        if success:
            synced += 1
        else:
            errors.append(f'SKU {product.sku}: {message}')
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
# ENDPOINT 7: DESCONECTAR CUENTA
# ═══════════════════════════════════════════════════════════

@bp.route('/disconnect', methods=['DELETE'])
@jwt_required()
def disconnect_ml():
    """
    Desconecta la cuenta de Mercado Libre del usuario.
    Soft delete: marcamos is_active=False, no borramos el registro.
    """
    user_id = get_jwt_identity()

    connection = PlatformConnection.query.filter_by(
        user_id=int(user_id),
        platform='mercadolibre',
        is_active=True
    ).first()

    if not connection:
        return jsonify({'success': False, 'error': 'No hay cuenta conectada'}), 400

    connection.is_active = False
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Cuenta {connection.store_name} desconectada de Mercado Libre'
    }), 200
