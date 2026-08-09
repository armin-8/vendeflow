"""
VendeFlow - Rutas de Importación
=================================

Endpoints para importar productos masivamente desde Excel/CSV.

FLUJO DE IMPORTACIÓN:
---------------------
1. Usuario sube archivo → POST /api/import/preview
2. Sistema lee y valida → Retorna vista previa
3. Usuario revisa y confirma → POST /api/import/confirm
4. Sistema guarda en BD → Retorna productos creados

¿POR QUÉ DOS PASOS?
-------------------
Separamos en "preview" y "confirm" para que el usuario pueda:
- Ver los datos antes de guardarlos
- Detectar errores antes de crear productos
- Cancelar si algo está mal
"""

import io
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError

from app import db
from app.models.product import Product
from app.schemas.product_schema import ProductCreate
from app.services.import_service import read_import_file, get_template_columns

# Crear Blueprint para agrupar estas rutas
bp = Blueprint('import', __name__, url_prefix='/api/import')


# ═══════════════════════════════════════════════════════════
# ENDPOINT: VISTA PREVIA
# ═══════════════════════════════════════════════════════════

@bp.route('/preview', methods=['POST'])
@jwt_required()
def preview_import():
    """
    Recibe un archivo Excel/CSV y retorna vista previa de los productos.
    
    ¿CÓMO FUNCIONA?
    ---------------
    1. Recibe el archivo desde el frontend (multipart/form-data)
    2. Usa el servicio import_service para leer el archivo
    3. Retorna los productos encontrados + errores
    
    REQUEST:
    --------
    - Content-Type: multipart/form-data
    - Body: file (archivo Excel o CSV)
    
    RESPONSE:
    ---------
    {
        "success": true,
        "products": [...],      // Lista de productos leídos
        "total": 150,           // Total de productos
        "errors": [...],        // Errores/advertencias
        "errors_count": 3
    }
    """
    
    user_id = get_jwt_identity()
    
    # ─────────────────────────────────────────────────────────
    # PASO 1: Verificar que se envió un archivo
    # ─────────────────────────────────────────────────────────
    
    # request.files contiene los archivos enviados
    # 'file' es el nombre del campo en el formulario
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No se envió ningún archivo'
        }), 400
    
    file = request.files['file']
    
    # Verificar que tiene nombre (no está vacío)
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'El archivo está vacío'
        }), 400
    
    # ─────────────────────────────────────────────────────────
    # PASO 2: Leer el archivo con nuestro servicio
    # ─────────────────────────────────────────────────────────
    
    products, errors = read_import_file(file)
    
    # Si no hay productos, es un error
    if not products:
        return jsonify({
            'success': False,
            'error': 'No se pudieron leer productos del archivo',
            'errors': errors
        }), 400
    
    # ─────────────────────────────────────────────────────────
    # PASO 3: Verificar SKUs duplicados en el archivo
    # ─────────────────────────────────────────────────────────
    
    seen_skus = set()
    duplicate_skus = []
    
    for product in products:
        sku = product['sku']
        if sku in seen_skus:
            duplicate_skus.append(sku)
        seen_skus.add(sku)
    
    if duplicate_skus:
        errors.append(f'SKUs duplicados en el archivo: {", ".join(duplicate_skus[:5])}')
    
    # ─────────────────────────────────────────────────────────
    # PASO 4: Verificar cuáles SKUs ya existen en la BD
    # ─────────────────────────────────────────────────────────
    
    skus_in_file = [p['sku'] for p in products]
    
    existing_products = Product.query.filter(
        Product.user_id == int(user_id),
        Product.sku.in_(skus_in_file),
        Product.is_active == True
    ).all()
    
    existing_skus = {p.sku for p in existing_products}
    
    # Marcar cada producto como nuevo o existente
    for product in products:
        product['exists'] = product['sku'] in existing_skus
        product['action'] = 'update' if product['exists'] else 'create'
    
    # ─────────────────────────────────────────────────────────
    # PASO 5: Retornar respuesta
    # ─────────────────────────────────────────────────────────
    #
    # Los productos viajan de vuelta al cliente y regresan en el body de
    # /confirm. NO los guardamos en servidor: la sesión de Flask es una
    # cookie firmada de ~4KB (no le caben 150 productos) y encima no viaja
    # en llamadas cross-origin, que es como el frontend habla con la API.
    
    # Contar nuevos vs actualizaciones
    new_count = sum(1 for p in products if p['action'] == 'create')
    update_count = sum(1 for p in products if p['action'] == 'update')
    
    return jsonify({
        'success': True,
        'products': products,
        'total': len(products),
        'new_count': new_count,
        'update_count': update_count,
        'errors': errors,
        'errors_count': len(errors)
    }), 200


# ═══════════════════════════════════════════════════════════
# ENDPOINT: CONFIRMAR IMPORTACIÓN
# ═══════════════════════════════════════════════════════════

@bp.route('/confirm', methods=['POST'])
@jwt_required()
def confirm_import():
    """
    Confirma la importación y guarda los productos en la base de datos.
    
    REQUEST:
    --------
    {
        "products": [...],             // Los productos que devolvió /preview
        "update_existing": true/false  // Si actualizar productos existentes
    }

    RESPONSE:
    ---------
    {
        "success": true,
        "created": 100,     // Productos nuevos creados
        "updated": 50,      // Productos actualizados
        "skipped": 5,       // Productos omitidos
        "errors": [...]     // Errores durante la creación
    }
    """

    user_id = get_jwt_identity()

    # ─────────────────────────────────────────────────────────
    # PASO 1: Leer los productos del body
    # ─────────────────────────────────────────────────────────

    data = request.get_json() or {}
    raw_products = data.get('products')
    update_existing = data.get('update_existing', False)

    if not raw_products or not isinstance(raw_products, list):
        return jsonify({
            'success': False,
            'error': 'No hay datos para importar. Sube un archivo primero.'
        }), 400

    # ─────────────────────────────────────────────────────────
    # PASO 2: Revalidar TODO lo que llega
    # ─────────────────────────────────────────────────────────
    #
    # Los productos pasaron por /preview, pero vienen del cliente: hay que
    # validarlos de nuevo aquí. Pydantic además normaliza (SKU a mayúsculas,
    # espacios recortados) igual que en el CRUD normal de inventario.

    products = []
    errors = []

    for index, item in enumerate(raw_products):
        try:
            products.append(ProductCreate(**item).model_dump())
        except (ValidationError, TypeError) as e:
            sku = item.get('sku', f'fila {index + 1}') if isinstance(item, dict) else f'fila {index + 1}'
            errors.append(f'Producto inválido ({sku}): {str(e)}')

    if not products:
        return jsonify({
            'success': False,
            'error': 'Ningún producto pasó la validación',
            'errors': errors
        }), 400

    # ─────────────────────────────────────────────────────────
    # PASO 3: Procesar cada producto
    # ─────────────────────────────────────────────────────────

    created = 0
    updated = 0
    skipped = 0

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
                # Producto ya existe
                if update_existing:
                    # Actualizar campos
                    existing.name = product_data['name']
                    existing.description = product_data.get('description')
                    existing.price = product_data['price']
                    existing.cost = product_data.get('cost')
                    existing.quantity = product_data.get('quantity', 0)
                    existing.min_stock = product_data.get('min_stock', 5)
                    existing.category = product_data.get('category')
                    existing.brand = product_data.get('brand')
                    existing.image_url = product_data.get('image_url')
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
                    min_stock=product_data.get('min_stock', 5),
                    category=product_data.get('category'),
                    brand=product_data.get('brand'),
                    image_url=product_data.get('image_url')
                )
                db.session.add(new_product)
                created += 1
        
        except Exception as e:
            errors.append(f'Error con SKU {sku}: {str(e)}')
    
    # ─────────────────────────────────────────────────────────
    # PASO 4: Guardar cambios en la base de datos
    # ─────────────────────────────────────────────────────────
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Error al guardar en la base de datos: {str(e)}'
        }), 500
    
    # ─────────────────────────────────────────────────────────
    # PASO 5: Retornar resultados
    # ─────────────────────────────────────────────────────────
    
    return jsonify({
        'success': True,
        'created': created,
        'updated': updated,
        'skipped': skipped,
        'errors': errors,
        'message': f'Importación completada: {created} creados, {updated} actualizados, {skipped} omitidos'
    }), 200


# ═══════════════════════════════════════════════════════════
# ENDPOINT: INFORMACIÓN DE PLANTILLA
# ═══════════════════════════════════════════════════════════

@bp.route('/template', methods=['GET'])
@jwt_required()
def get_template():
    """
    Retorna información sobre las columnas esperadas en el archivo.
    
    El frontend puede usar esto para:
    - Mostrar instrucciones al usuario
    - Generar una plantilla de ejemplo
    
    RESPONSE:
    ---------
    {
        "required": ["sku", "name", "price"],
        "optional": ["description", "cost", ...],
        "example": {...}
    }
    """
    
    return jsonify(get_template_columns()), 200
