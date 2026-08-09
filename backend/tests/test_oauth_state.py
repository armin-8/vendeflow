"""
VendeFlow - Tests del state firmado de OAuth
==============================================

Estos tests cubren el agujero que tenía el OAuth: el state viajaba en texto
plano ("random:user_id:shop") y el callback confiaba en el user_id que venía
dentro, así que cualquiera podía fabricar uno y colgar una tienda a la cuenta
de otro usuario.

Ahora el state va firmado con SECRET_KEY. Si alguien lo altera, no pasa.
"""

import time
import hmac
import hashlib
from urllib.parse import urlencode

import pytest

from app.utils.oauth_state import generate_state, verify_state
from app.services.shopify_service import ShopifyService


# ═══════════════════════════════════════════════════════════
# STATE FIRMADO
# ═══════════════════════════════════════════════════════════

def test_state_valido_devuelve_el_payload(app):
    """Un state que emitimos nosotros se verifica y devuelve sus datos."""
    with app.app_context():
        state = generate_state('shopify', {'user_id': 7, 'shop': 'mi-tienda'})
        payload, error = verify_state('shopify', state)

    assert error is None
    assert payload == {'user_id': 7, 'shop': 'mi-tienda'}


def test_state_alterado_es_rechazado(app):
    """
    El ataque original: cambiar el user_id del state para colgar la tienda
    a otra cuenta. Con la firma, el state deja de ser válido.
    """
    with app.app_context():
        state = generate_state('shopify', {'user_id': 7, 'shop': 'mi-tienda'})

        # Un atacante manipula el payload (cualquier byte sirve)
        alterado = state[:-1] + ('A' if state[-1] != 'A' else 'B')

        payload, error = verify_state('shopify', alterado)

    assert payload is None
    assert error == 'invalid_state'


def test_state_fabricado_desde_cero_es_rechazado(app):
    """Un state inventado sin la SECRET_KEY no pasa la verificación."""
    with app.app_context():
        payload, error = verify_state('shopify', 'random:99:tienda-del-atacante')

    assert payload is None
    assert error == 'invalid_state'


def test_state_vacio_es_rechazado(app):
    with app.app_context():
        payload, error = verify_state('shopify', '')

    assert payload is None
    assert error == 'missing_state'


def test_state_de_shopify_no_sirve_en_mercadolibre(app):
    """El salt por plataforma evita reutilizar un state entre callbacks."""
    with app.app_context():
        state = generate_state('shopify', {'user_id': 7, 'shop': 'mi-tienda'})
        payload, error = verify_state('mercadolibre', state)

    assert payload is None
    assert error == 'invalid_state'


def test_state_expirado_es_rechazado(app, monkeypatch):
    """Un flujo OAuth que quedó a medias no sirve para siempre."""
    with app.app_context():
        state = generate_state('shopify', {'user_id': 7, 'shop': 'mi-tienda'})

        # Simulamos que pasaron 11 minutos (el límite son 10)
        real_time = time.time
        monkeypatch.setattr(time, 'time', lambda: real_time() + 660)

        payload, error = verify_state('shopify', state)

    assert payload is None
    assert error == 'expired_state'


# ═══════════════════════════════════════════════════════════
# HMAC DE SHOPIFY
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def shopify(monkeypatch):
    """Servicio de Shopify con un secret conocido para firmar de prueba."""
    monkeypatch.setenv('SHOPIFY_API_SECRET', 'secret-de-prueba')
    return ShopifyService()


def _firmar(params: dict, secret: str) -> str:
    """Construye una query string firmada igual que lo hace Shopify."""
    message = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
    firma = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return f'{message}&hmac={firma}'


def test_hmac_valido_pasa(shopify):
    query = _firmar(
        {'code': 'abc123', 'shop': 'mi-tienda.myshopify.com', 'timestamp': '1700000000'},
        'secret-de-prueba'
    )
    assert shopify.verify_hmac(query) is True


def test_hmac_invalido_no_pasa(shopify):
    """Alguien golpea el callback a mano, sin firma válida."""
    query = urlencode({
        'code': 'abc123',
        'shop': 'mi-tienda.myshopify.com',
        'hmac': 'firma-inventada'
    })
    assert shopify.verify_hmac(query) is False


def test_hmac_no_pasa_si_alteran_un_parametro(shopify):
    """Si cambian el `code` después de firmar, la firma deja de cuadrar."""
    query = _firmar(
        {'code': 'abc123', 'shop': 'mi-tienda.myshopify.com'},
        'secret-de-prueba'
    ).replace('code=abc123', 'code=code-del-atacante')

    assert shopify.verify_hmac(query) is False


def test_hmac_sin_firma_no_pasa(shopify):
    assert shopify.verify_hmac('code=abc123&shop=mi-tienda') is False


def test_hmac_sin_secret_configurado_no_pasa(monkeypatch):
    """Sin SHOPIFY_API_SECRET no podemos verificar nada — rechazamos."""
    monkeypatch.delenv('SHOPIFY_API_SECRET', raising=False)
    servicio = ShopifyService()
    assert servicio.verify_hmac('code=abc&hmac=loquesea') is False
