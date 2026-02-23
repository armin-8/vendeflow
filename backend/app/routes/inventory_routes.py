"""
VendeFlow - Rutas de Inventario
===============================
Endpoints para gestión de productos e inventario.

ENDPOINTS:
- GET    /api/inventory           - Listar productos (con paginación)
- POST   /api/inventory           - Crear producto
- GET    /api/inventory/<id>      - Obtener un producto
- PUT    /api/inventory/<id>      - Actualizar producto
- DELETE /api/inventory/<id>      - Eliminar producto
- GET    /api/inventory/stats     - Estadísticas del inventario
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError

from app import db
from app.models.product import Product
from app.schemas.product_schema import ProductCreate, ProductUpdate

bp = Blueprint('inventory', __name__, url_prefix='/api/inventory')
bp.strict_slashes = False  # Evita redirects por trailing slash


# ═══════════════════════════════════════════════════════════
# LISTAR PRODUCTOS
# ═══════════════════════════════════════════════════════════

@bp.route('', methods=['GET'])
@jwt_required()
def get_products():
    """
    Lista todos los productos del usuario con paginación.
    
    Query params:
        - page: Número de página (default: 1)
        - per_page: Productos por página (default: 20, max: 100)
        - search: Buscar por nombre o SKU
        - category: Filtrar por categoría
        - low_stock: Si es 'true', solo productos con stock bajo
    
    Returns:
        200: Lista de productos paginada
    """
    user_id = get_jwt_identity()
    
    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    # Filtros
    search = request.args.get('search', '', type=str)
    category = request.args.get('category', '', type=str)
    low_stock = request.args.get('low_stock', 'false').lower() == 'true'
    
    # Query base: productos del usuario
    query = Product.query.filter_by(user_id=int(user_id), is_active=True)
    
    # Aplicar filtros
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                Product.name.ilike(search_filter),
                Product.sku.ilike(search_filter)
            )
        )
    
    if category:
        query = query.filter(Product.category == category)
    
    if low_stock:
        query = query.filter(Product.quantity <= Product.min_stock)
    
    # Ordenar por fecha de actualización (más recientes primero)
    query = query.order_by(Product.updated_at.desc())
    
    # Paginar
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'products': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    }), 200


# ═══════════════════════════════════════════════════════════
# CREAR PRODUCTO
# ═══════════════════════════════════════════════════════════

@bp.route('', methods=['POST'])
@jwt_required()
def create_product():
    """
    Crea un nuevo producto.
    
    Request Body:
        {
            "sku": "PROD-001",
            "name": "Producto de ejemplo",
            "description": "Descripción...",
            "price": 99.99,
            "cost": 50.00,
            "quantity": 100,
            "min_stock": 10,
            "category": "Electrónicos",
            "brand": "MiMarca"
        }
    
    Returns:
        201: Producto creado
        400: Error de validación
        409: SKU ya existe
    """
    user_id = get_jwt_identity()
    
    # Validar JSON
    if not request.is_json:
        return jsonify({'error': 'Se requiere JSON en el request'}), 400
    
    # Validar datos con Pydantic
    try:
        data = request.get_json()
        product_data = ProductCreate(**data)
    except ValidationError as e:
        return jsonify({
            'error': 'Error de validación',
            'details': e.errors()
        }), 400
    
    # Verificar si el SKU ya existe para este usuario
    existing = Product.query.filter_by(
        user_id=int(user_id), 
        sku=product_data.sku
    ).first()
    
    if existing:
        return jsonify({'error': f'Ya existe un producto con el SKU: {product_data.sku}'}), 409
    
    # Crear producto
    new_product = Product(
        user_id=int(user_id),
        sku=product_data.sku,
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        cost=product_data.cost,
        quantity=product_data.quantity,
        min_stock=product_data.min_stock,
        category=product_data.category,
        brand=product_data.brand,
        image_url=product_data.image_url
    )
    
    try:
        db.session.add(new_product)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear producto: {str(e)}'}), 500
    
    return jsonify({
        'message': 'Producto creado exitosamente',
        'product': new_product.to_dict()
    }), 201


# ═══════════════════════════════════════════════════════════
# OBTENER UN PRODUCTO
# ═══════════════════════════════════════════════════════════

@bp.route('/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    """
    Obtiene un producto por su ID.
    
    Returns:
        200: Datos del producto
        404: Producto no encontrado
    """
    user_id = get_jwt_identity()
    
    product = Product.query.filter_by(
        id=product_id, 
        user_id=int(user_id)
    ).first()
    
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    return jsonify({'product': product.to_dict()}), 200


# ═══════════════════════════════════════════════════════════
# ACTUALIZAR PRODUCTO
# ═══════════════════════════════════════════════════════════

@bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """
    Actualiza un producto existente.
    
    Returns:
        200: Producto actualizado
        400: Error de validación
        404: Producto no encontrado
        409: SKU ya existe (si se intenta cambiar)
    """
    user_id = get_jwt_identity()
    
    # Buscar producto
    product = Product.query.filter_by(
        id=product_id, 
        user_id=int(user_id)
    ).first()
    
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    # Validar JSON
    if not request.is_json:
        return jsonify({'error': 'Se requiere JSON en el request'}), 400
    
    # Validar datos
    try:
        data = request.get_json()
        update_data = ProductUpdate(**data)
    except ValidationError as e:
        return jsonify({
            'error': 'Error de validación',
            'details': e.errors()
        }), 400
    
    # Si se cambia el SKU, verificar que no exista otro
    if update_data.sku and update_data.sku != product.sku:
        existing = Product.query.filter_by(
            user_id=int(user_id), 
            sku=update_data.sku
        ).first()
        if existing:
            return jsonify({'error': f'Ya existe un producto con el SKU: {update_data.sku}'}), 409
    
    # Actualizar campos proporcionados
    update_fields = update_data.model_dump(exclude_unset=True)
    
    for field, value in update_fields.items():
        if hasattr(product, field):
            setattr(product, field, value)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar: {str(e)}'}), 500
    
    return jsonify({
        'message': 'Producto actualizado exitosamente',
        'product': product.to_dict()
    }), 200


# ═══════════════════════════════════════════════════════════
# ELIMINAR PRODUCTO
# ═══════════════════════════════════════════════════════════

@bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """
    Elimina un producto (soft delete - lo marca como inactivo).
    
    Returns:
        200: Producto eliminado
        404: Producto no encontrado
    """
    user_id = get_jwt_identity()
    
    product = Product.query.filter_by(
        id=product_id, 
        user_id=int(user_id)
    ).first()
    
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    # Soft delete: marcar como inactivo
    product.is_active = False
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar: {str(e)}'}), 500
    
    return jsonify({
        'message': 'Producto eliminado exitosamente'
    }), 200


# ═══════════════════════════════════════════════════════════
# ESTADÍSTICAS DEL INVENTARIO
# ═══════════════════════════════════════════════════════════

@bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """
    Obtiene estadísticas del inventario del usuario.
    
    Returns:
        200: Estadísticas
    """
    user_id = get_jwt_identity()
    
    # Query base
    base_query = Product.query.filter_by(user_id=int(user_id), is_active=True)
    
    # Total de productos
    total_products = base_query.count()
    
    # Productos con stock bajo
    low_stock_count = base_query.filter(Product.quantity <= Product.min_stock).count()
    
    # Productos sin stock
    out_of_stock = base_query.filter(Product.quantity == 0).count()
    
    # Valor total del inventario (precio * cantidad)
    products = base_query.all()
    total_value = sum(p.price * p.quantity for p in products)
    total_cost = sum((p.cost or 0) * p.quantity for p in products)
    
    # Categorías únicas
    categories = db.session.query(Product.category).filter(
        Product.user_id == int(user_id),
        Product.is_active == True,
        Product.category.isnot(None)
    ).distinct().count()
    
    return jsonify({
        'stats': {
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            'out_of_stock': out_of_stock,
            'total_value': round(total_value, 2),
            'total_cost': round(total_cost, 2),
            'potential_profit': round(total_value - total_cost, 2),
            'categories': categories
        }
    }), 200
