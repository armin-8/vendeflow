"""
VendeFlow - Tests de Autenticación
====================================

Testeamos los endpoints críticos de auth:
- POST /api/auth/register
- POST /api/auth/login
- GET  /api/auth/me

CONVENCIÓN DE NOMBRES:
    test_<qué_hace>_<condición>
    Ejemplo: test_register_success, test_login_wrong_password
"""


# ═══════════════════════════════════════════════════════════
# TESTS DE REGISTRO
# ═══════════════════════════════════════════════════════════

def test_register_success(client):
    """Registro exitoso con datos válidos."""
    response = client.post('/api/auth/register', json={
        'email': 'nuevo@vendeflow.com',
        'password': 'password123',
        'first_name': 'Juan',
        'last_name': 'Pérez'
    })

    assert response.status_code == 201
    data = response.json
    assert data['token'] is not None
    assert data['user']['email'] == 'nuevo@vendeflow.com'
    assert data['user']['first_name'] == 'Juan'
    # Nunca debe retornar la contraseña
    assert 'password' not in data['user']
    assert 'password_hash' not in data['user']


def test_register_duplicate_email(client):
    """No se puede registrar el mismo email dos veces."""
    user_data = {
        'email': 'duplicado@vendeflow.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User'
    }

    # Primera vez — debe funcionar
    client.post('/api/auth/register', json=user_data)

    # Segunda vez — debe fallar con 409
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 409
    assert 'error' in response.json


def test_register_missing_fields(client):
    """Registro sin campos obligatorios debe fallar."""
    response = client.post('/api/auth/register', json={
        'email': 'incompleto@vendeflow.com'
        # Falta password, first_name, last_name
    })

    assert response.status_code == 400
    assert 'error' in response.json


def test_register_invalid_email(client):
    """Email inválido debe rechazarse."""
    response = client.post('/api/auth/register', json={
        'email': 'esto-no-es-un-email',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User'
    })

    assert response.status_code == 400


# ═══════════════════════════════════════════════════════════
# TESTS DE LOGIN
# ═══════════════════════════════════════════════════════════

def test_login_success(client):
    """Login exitoso con credenciales correctas."""
    # Registrar primero
    client.post('/api/auth/register', json={
        'email': 'login@vendeflow.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User'
    })

    # Login
    response = client.post('/api/auth/login', json={
        'email': 'login@vendeflow.com',
        'password': 'password123'
    })

    assert response.status_code == 200
    data = response.json
    assert data['token'] is not None
    assert data['user']['email'] == 'login@vendeflow.com'


def test_login_wrong_password(client):
    """Login con contraseña incorrecta debe retornar 401."""
    client.post('/api/auth/register', json={
        'email': 'wrong@vendeflow.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User'
    })

    response = client.post('/api/auth/login', json={
        'email': 'wrong@vendeflow.com',
        'password': 'contraseña_incorrecta'
    })

    assert response.status_code == 401
    assert 'error' in response.json


def test_login_nonexistent_user(client):
    """Login con email que no existe debe retornar 401."""
    response = client.post('/api/auth/login', json={
        'email': 'noexiste@vendeflow.com',
        'password': 'password123'
    })

    assert response.status_code == 401


# ═══════════════════════════════════════════════════════════
# TESTS DE /me
# ═══════════════════════════════════════════════════════════

def test_get_me_success(client, auth_headers):
    """Obtener usuario autenticado con token válido."""
    response = client.get('/api/auth/me', headers=auth_headers)

    assert response.status_code == 200
    assert response.json['user']['email'] == 'test@vendeflow.com'


def test_get_me_no_token(client):
    """Sin token JWT debe retornar 401."""
    response = client.get('/api/auth/me')
    assert response.status_code == 401


def test_get_me_invalid_token(client):
    """
    Con token malformado Flask-JWT retorna 422.

    ¿POR QUÉ 422 Y NO 401?
    Flask-JWT-Extended distingue dos casos:
      401 → No hay token (header ausente)
      422 → Hay token pero está malformado o es inválido
    Ambos significan "no autenticado" pero con códigos diferentes.
    """
    response = client.get('/api/auth/me', headers={
        'Authorization': 'Bearer token_completamente_invalido'
    })
    assert response.status_code == 422
