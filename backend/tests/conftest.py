"""
VendeFlow - Configuración de Tests
====================================

conftest.py es el archivo especial de pytest donde definimos
los "fixtures" — objetos reutilizables entre todos los tests.

¿QUÉ ES UN FIXTURE?
--------------------
Es una función que prepara algo que los tests necesitan.
Por ejemplo: una app configurada para testing, un cliente HTTP,
un usuario ya registrado con su token JWT, etc.

pytest los inyecta automáticamente en cada test que los necesite:

    def test_algo(client, auth_headers):
                   ^         ^
              fixture      fixture
"""

import pytest
from app import create_app, db
from app.config import TestingConfig


# ═══════════════════════════════════════════════════════════
# FIXTURE: APP DE TESTING
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def app():
    """
    Crea una instancia de la app configurada para testing.
    
    Usa SQLite en memoria — no toca la BD real de desarrollo.
    Cada test empieza con una BD limpia y la destruye al terminar.
    """
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


# ═══════════════════════════════════════════════════════════
# FIXTURE: CLIENTE HTTP
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def client(app):
    """
    Cliente HTTP para hacer requests a la app sin levantar servidor.

    Uso en tests:
        response = client.post('/api/auth/login', json={...})
        assert response.status_code == 200
    """
    return app.test_client()


# ═══════════════════════════════════════════════════════════
# FIXTURE: USUARIO REGISTRADO + TOKEN JWT
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def auth_headers(client):
    """
    Registra un usuario de prueba y retorna headers con JWT.

    Uso en tests:
        response = client.get('/api/inventory', headers=auth_headers)
    """
    response = client.post('/api/auth/register', json={
        'email': 'test@vendeflow.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User'
    })

    token = response.json['token']
    return {'Authorization': f'Bearer {token}'}


# ═══════════════════════════════════════════════════════════
# FIXTURE: PRODUCTO DE PRUEBA
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def sample_product(client, auth_headers):
    """
    Crea un producto de prueba y lo retorna.

    Uso en tests:
        def test_update(client, auth_headers, sample_product):
            response = client.put(f'/api/inventory/{sample_product["id"]}', ...)
    """
    response = client.post('/api/inventory', json={
        'sku': 'TEST-001',
        'name': 'Producto de Prueba',
        'price': 99.99,
        'quantity': 10,
        'min_stock': 2
    }, headers=auth_headers)

    return response.json['product']
