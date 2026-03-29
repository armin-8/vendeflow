"""
VendeFlow - Tests de Inventario
=================================

Testeamos los endpoints críticos de inventario:
- POST   /api/inventory         → crear producto
- GET    /api/inventory         → listar productos
- GET    /api/inventory/<id>    → obtener uno
- PUT    /api/inventory/<id>    → actualizar
- DELETE /api/inventory/<id>    → eliminar (soft delete)
- GET    /api/inventory/stats   → estadísticas
"""


# ═══════════════════════════════════════════════════════════
# TESTS DE CREAR PRODUCTO
# ═══════════════════════════════════════════════════════════

def test_create_product_success(client, auth_headers):
    """Crear producto con datos válidos."""
    response = client.post('/api/inventory', json={
        'sku': 'PROD-001',
        'name': 'Producto Test',
        'price': 99.99,
        'quantity': 50,
        'min_stock': 5
    }, headers=auth_headers)

    assert response.status_code == 201
    data = response.json
    assert data['product']['sku'] == 'PROD-001'
    assert data['product']['price'] == 99.99
    assert data['product']['quantity'] == 50


def test_create_product_duplicate_sku(client, auth_headers):
    """No se puede crear dos productos con el mismo SKU."""
    product_data = {
        'sku': 'DUPLICADO-001',
        'name': 'Producto Test',
        'price': 10.0,
        'quantity': 5,
        'min_stock': 1
    }

    # Primera vez — debe funcionar
    client.post('/api/inventory', json=product_data, headers=auth_headers)

    # Segunda vez — debe fallar con 409
    response = client.post('/api/inventory', json=product_data, headers=auth_headers)
    assert response.status_code == 409


def test_create_product_missing_required_fields(client, auth_headers):
    """Crear producto sin campos obligatorios debe fallar."""
    response = client.post('/api/inventory', json={
        'name': 'Sin SKU'
        # Falta sku, price, quantity
    }, headers=auth_headers)

    assert response.status_code == 400


def test_create_product_requires_auth(client):
    """Crear producto sin token debe retornar 401."""
    response = client.post('/api/inventory', json={
        'sku': 'TEST-001',
        'name': 'Test',
        'price': 10.0,
        'quantity': 1,
        'min_stock': 1
    })
    assert response.status_code == 401


# ═══════════════════════════════════════════════════════════
# TESTS DE LISTAR PRODUCTOS
# ═══════════════════════════════════════════════════════════

def test_list_products_empty(client, auth_headers):
    """Listar productos cuando no hay ninguno."""
    response = client.get('/api/inventory', headers=auth_headers)

    assert response.status_code == 200
    assert response.json['products'] == []
    assert response.json['total'] == 0


def test_list_products_with_data(client, auth_headers, sample_product):
    """Listar productos cuando hay al menos uno."""
    response = client.get('/api/inventory', headers=auth_headers)

    assert response.status_code == 200
    assert len(response.json['products']) == 1
    assert response.json['products'][0]['sku'] == 'TEST-001'


def test_list_products_search(client, auth_headers):
    """Buscar productos por SKU o nombre."""
    # Crear 2 productos
    client.post('/api/inventory', json={
        'sku': 'CAMARA-001', 'name': 'Cámara GoPro', 'price': 5000, 'quantity': 3, 'min_stock': 1
    }, headers=auth_headers)
    client.post('/api/inventory', json={
        'sku': 'FILTRO-001', 'name': 'Filtro Polar', 'price': 500, 'quantity': 10, 'min_stock': 2
    }, headers=auth_headers)

    # Buscar por nombre
    response = client.get('/api/inventory?search=GoPro', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['total'] == 1
    assert response.json['products'][0]['sku'] == 'CAMARA-001'


# ═══════════════════════════════════════════════════════════
# TESTS DE ACTUALIZAR PRODUCTO
# ═══════════════════════════════════════════════════════════

def test_update_product_success(client, auth_headers, sample_product):
    """Actualizar stock de un producto."""
    product_id = sample_product['id']

    response = client.put(f'/api/inventory/{product_id}', json={
        'quantity': 99
    }, headers=auth_headers)

    assert response.status_code == 200
    assert response.json['product']['quantity'] == 99


def test_update_product_not_found(client, auth_headers):
    """Actualizar producto que no existe debe retornar 404."""
    response = client.put('/api/inventory/99999', json={
        'quantity': 10
    }, headers=auth_headers)

    assert response.status_code == 404


def test_update_product_other_user_cant_access(client, auth_headers, sample_product):
    """
    Un usuario no puede editar productos de otro usuario.
    Creamos un segundo usuario e intentamos editar el producto del primero.
    """
    # Registrar segundo usuario
    second_response = client.post('/api/auth/register', json={
        'email': 'otro@vendeflow.com',
        'password': 'password123',
        'first_name': 'Otro',
        'last_name': 'Usuario'
    })
    other_token = second_response.json['token']
    other_headers = {'Authorization': f'Bearer {other_token}'}

    # Intentar editar producto del primer usuario
    product_id = sample_product['id']
    response = client.put(f'/api/inventory/{product_id}', json={
        'quantity': 999
    }, headers=other_headers)

    # Debe retornar 404 (para el otro usuario, el producto no existe)
    assert response.status_code == 404


# ═══════════════════════════════════════════════════════════
# TESTS DE ELIMINAR PRODUCTO
# ═══════════════════════════════════════════════════════════

def test_delete_product_success(client, auth_headers, sample_product):
    """Eliminar producto (soft delete)."""
    product_id = sample_product['id']

    response = client.delete(f'/api/inventory/{product_id}', headers=auth_headers)
    assert response.status_code == 200

    # Verificar que ya no aparece en la lista
    list_response = client.get('/api/inventory', headers=auth_headers)
    assert list_response.json['total'] == 0


# ═══════════════════════════════════════════════════════════
# TESTS DE ESTADÍSTICAS
# ═══════════════════════════════════════════════════════════

def test_stats_empty(client, auth_headers):
    """Estadísticas cuando no hay productos."""
    response = client.get('/api/inventory/stats', headers=auth_headers)

    assert response.status_code == 200
    stats = response.json['stats']
    assert stats['total_products'] == 0
    assert stats['low_stock_count'] == 0
    assert stats['out_of_stock'] == 0


def test_stats_with_low_stock(client, auth_headers):
    """Estadísticas deben detectar stock bajo correctamente."""
    # Crear producto con stock bajo (quantity <= min_stock)
    client.post('/api/inventory', json={
        'sku': 'LOW-001',
        'name': 'Stock Bajo',
        'price': 100.0,
        'quantity': 2,    # ← igual al min_stock
        'min_stock': 2
    }, headers=auth_headers)

    response = client.get('/api/inventory/stats', headers=auth_headers)
    stats = response.json['stats']

    assert stats['total_products'] == 1
    assert stats['low_stock_count'] == 1
