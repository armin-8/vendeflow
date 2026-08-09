"""
VendeFlow - Tests del flujo de importación
===========================================

/confirm recibe los productos en el body (antes los leía de la sesión de
Flask, que es una cookie de ~4KB y encima no viaja en llamadas cross-origin,
así que la importación fallaba siempre en el flujo real).
"""


def test_confirm_crea_los_productos_del_body(client, auth_headers):
    response = client.post('/api/import/confirm', json={
        'products': [
            {'sku': 'IMP-001', 'name': 'Producto uno', 'price': 100.0, 'quantity': 5},
            {'sku': 'IMP-002', 'name': 'Producto dos', 'price': 200.0, 'quantity': 3},
        ]
    }, headers=auth_headers)

    assert response.status_code == 200
    assert response.json['created'] == 2
    assert response.json['updated'] == 0

    # Y de verdad quedaron en el inventario
    inventario = client.get('/api/inventory', headers=auth_headers)
    skus = {p['sku'] for p in inventario.json['products']}
    assert skus == {'IMP-001', 'IMP-002'}


def test_confirm_sin_productos_da_error(client, auth_headers):
    response = client.post('/api/import/confirm', json={}, headers=auth_headers)

    assert response.status_code == 400
    assert 'No hay datos para importar' in response.json['error']


def test_confirm_omite_existentes_si_no_se_pide_actualizar(client, auth_headers, sample_product):
    response = client.post('/api/import/confirm', json={
        'products': [
            {'sku': 'TEST-001', 'name': 'Nombre nuevo', 'price': 555.0},
        ],
        'update_existing': False
    }, headers=auth_headers)

    assert response.status_code == 200
    assert response.json['skipped'] == 1
    assert response.json['updated'] == 0


def test_confirm_actualiza_existentes_si_se_pide(client, auth_headers, sample_product):
    response = client.post('/api/import/confirm', json={
        'products': [
            {'sku': 'TEST-001', 'name': 'Nombre nuevo', 'price': 555.0},
        ],
        'update_existing': True
    }, headers=auth_headers)

    assert response.status_code == 200
    assert response.json['updated'] == 1

    producto = client.get(f'/api/inventory/{sample_product["id"]}', headers=auth_headers)
    assert producto.json['product']['name'] == 'Nombre nuevo'
    assert producto.json['product']['price'] == 555.0


def test_confirm_revalida_lo_que_llega(client, auth_headers):
    """
    Los productos vienen del cliente, así que se revalidan aquí: uno con
    precio negativo no debe entrar aunque el cliente lo mande.
    """
    response = client.post('/api/import/confirm', json={
        'products': [
            {'sku': 'OK-001', 'name': 'Válido', 'price': 100.0},
            {'sku': 'MAL-001', 'name': 'Precio negativo', 'price': -50.0},
        ]
    }, headers=auth_headers)

    assert response.status_code == 200
    assert response.json['created'] == 1
    assert len(response.json['errors']) == 1
    assert 'MAL-001' in response.json['errors'][0]


def test_confirm_requiere_autenticacion(client):
    response = client.post('/api/import/confirm', json={
        'products': [{'sku': 'X-1', 'name': 'X', 'price': 1.0}]
    })
    assert response.status_code == 401
