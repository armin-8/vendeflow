"""
VendeFlow - Tests de publicación en Mercado Libre
==================================================

Publicar en ML tiene tres diferencias con Shopify que estos tests fijan:

1. ML exige `category_id` de un árbol de miles de nodos → se deduce del título.
   El usuario nunca ve esa decisión (es la promesa del "un clic").
2. ML no tiene borradores → se crea y se pausa, para que el usuario revise
   antes de quedar visible.
3. La descripción es un recurso aparte (`POST /items/{id}/description`) y solo
   acepta texto plano.

Nada aquí toca la red: `requests` va monkeypatcheado.
"""

import pytest

from app.services.mercadolibre_service import MercadoLibreService, mercadolibre_service
from app.models.platform_connection import PlatformConnection
from app import db


SERVICIO = MercadoLibreService()

BASE = {
    'title': 'GoPro Hero Mission Pro camara de accion 5.3K',
    'description': 'Camara de accion con estabilizacion HyperSmooth.',
    'sku': 'gopro-001',
    'price': 8999.0,
    'quantity': 3,
    'brand': 'GoPro',
    'image_urls': ['https://cdn.ejemplo.com/gopro.jpg'],
}


# ═══════════════════════════════════════════════════════════
# DOBLES DE `requests`
# ═══════════════════════════════════════════════════════════

class RespuestaFalsa:
    def __init__(self, status_code, payload=None, text=''):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError('sin JSON')
        return self._payload


class MLFalso:
    """
    Simula la API de ML. Registra las llamadas para poder afirmar sobre ellas.

    `fallas` permite forzar un error en un paso concreto ('crear',
    'descripcion', 'pausar', 'categoria').
    """

    def __init__(self, fallas=()):
        self.fallas = set(fallas)
        self.gets = []
        self.posts = []
        self.puts = []

    def get(self, url, **kwargs):
        self.gets.append((url, kwargs))
        if 'categoria' in self.fallas:
            return RespuestaFalsa(200, [])
        return RespuestaFalsa(200, [{
            'category_id': 'MLM1000',
            'category_name': 'Cámaras Deportivas',
            'domain_id': 'MLM-ACTION_CAMERAS',
        }])

    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        if url.endswith('/description'):
            if 'descripcion' in self.fallas:
                return RespuestaFalsa(400, {'message': 'Bad Request', 'cause': []})
            return RespuestaFalsa(201, {'plain_text': 'ok'})
        if 'crear' in self.fallas:
            return RespuestaFalsa(400, {
                'message': 'Bad Request',
                'cause': [{'code': 'item.attributes.missing', 'message': 'Falta el atributo BRAND'}]
            })
        return RespuestaFalsa(201, {
            'id': 'MLM123456789',
            'status': 'active',
            'permalink': 'https://articulo.mercadolibre.com.mx/MLM123456789',
            'category_id': kwargs['json'].get('category_id'),
        })

    def put(self, url, **kwargs):
        self.puts.append((url, kwargs))
        if 'pausar' in self.fallas:
            return RespuestaFalsa(400, {'message': 'No se pudo pausar', 'cause': []})
        return RespuestaFalsa(200, {'id': 'MLM123456789', 'status': 'paused'})


@pytest.fixture
def ml_falso(monkeypatch):
    def _fabricar(fallas=()):
        doble = MLFalso(fallas)
        monkeypatch.setattr(
            'app.services.mercadolibre_service.requests', doble
        )
        return doble
    return _fabricar


# ═══════════════════════════════════════════════════════════
# TÍTULO: MÁXIMO 60 CHARS
# ═══════════════════════════════════════════════════════════

def test_recorta_el_titulo_a_60():
    largo = 'GoPro Hero Mission Pro camara de accion 5.3K con estabilizacion HyperSmooth'
    assert len(SERVICIO._recortar_titulo(largo)) <= 60


def test_no_parte_la_ultima_palabra():
    largo = 'GoPro Hero Mission Pro camara de accion 5.3K estabilizacion avanzada'
    resultado = SERVICIO._recortar_titulo(largo)

    assert resultado in largo
    assert not largo[len(resultado):].startswith(('a', 'e', 'i', 'o', 'u', 'n'))


def test_un_titulo_que_ya_cabe_no_se_toca():
    corto = 'GoPro Hero Mission Pro'
    assert SERVICIO._recortar_titulo(corto) == corto


def test_normaliza_espacios():
    assert SERVICIO._recortar_titulo('  GoPro   Hero  ') == 'GoPro Hero'


# ═══════════════════════════════════════════════════════════
# ATRIBUTOS
# ═══════════════════════════════════════════════════════════

def test_marca_generica_cuando_no_hay_marca():
    """ML pide BRAND obligatorio; sin default rechazaría la publicación."""
    atributos = SERVICIO._armar_atributos({'sku': 'X-1'})
    marca = next(a for a in atributos if a['id'] == 'BRAND')

    assert marca['value_name'] == 'Genérico'


def test_el_sku_viaja_como_seller_sku_en_mayusculas():
    """Es de donde normalize_items() lo lee cuando reimportamos desde ML."""
    atributos = SERVICIO._armar_atributos({'sku': 'gopro-001'})
    sku = next(a for a in atributos if a['id'] == 'SELLER_SKU')

    assert sku['value_name'] == 'GOPRO-001'


def test_el_modelo_solo_va_si_existe():
    ids = {a['id'] for a in SERVICIO._armar_atributos({'brand': 'GoPro'})}
    assert 'MODEL' not in ids

    ids = {a['id'] for a in SERVICIO._armar_atributos({'brand': 'GoPro', 'model': 'Hero 12'})}
    assert 'MODEL' in ids


# ═══════════════════════════════════════════════════════════
# MENSAJES DE ERROR
# ═══════════════════════════════════════════════════════════

def test_el_error_desdobla_la_causa():
    """Sin `cause` el usuario solo vería 'Bad Request', que no dice nada."""
    respuesta = RespuestaFalsa(400, {
        'message': 'Bad Request',
        'cause': [{'message': 'Falta el atributo BRAND'}]
    })
    assert 'Falta el atributo BRAND' in SERVICIO._mensaje_de_error(respuesta)


def test_el_error_sobrevive_a_una_respuesta_sin_json():
    respuesta = RespuestaFalsa(500, None, text='Internal Server Error')
    assert 'Internal Server Error' in SERVICIO._mensaje_de_error(respuesta)


# ═══════════════════════════════════════════════════════════
# VALIDACIONES ANTES DE LLAMAR A ML
# ═══════════════════════════════════════════════════════════

def test_sin_imagen_no_publica(ml_falso):
    """ML exige al menos una foto — mejor decirlo antes que gastar la llamada."""
    doble = ml_falso()
    item, error = SERVICIO.create_product('token', {**BASE, 'image_urls': []})

    assert item is None
    assert 'imagen' in error.lower()
    assert doble.posts == []


def test_sin_precio_no_publica(ml_falso):
    ml_falso()
    item, error = SERVICIO.create_product('token', {**BASE, 'price': 0})

    assert item is None
    assert 'precio' in error.lower()


def test_sin_titulo_no_publica(ml_falso):
    ml_falso()
    item, error = SERVICIO.create_product('token', {**BASE, 'title': '   '})

    assert item is None
    assert 'título' in error.lower()


# ═══════════════════════════════════════════════════════════
# FLUJO COMPLETO
# ═══════════════════════════════════════════════════════════

def test_deduce_la_categoria_del_titulo(ml_falso):
    """El usuario nunca elige categoría: se infiere."""
    doble = ml_falso()
    item, error = SERVICIO.create_product('token', BASE)

    assert error is None
    assert doble.gets, 'debió consultar el predictor de categorías'
    assert 'domain_discovery' in doble.gets[0][0]
    assert item['category_id'] == 'MLM1000'


def test_no_consulta_categoria_si_ya_se_la_dieron(ml_falso):
    doble = ml_falso()
    item, error = SERVICIO.create_product('token', {**BASE, 'category_id': 'MLM999'})

    assert error is None
    assert doble.gets == []
    assert item['category_id'] == 'MLM999'


def test_la_publicacion_queda_pausada(ml_falso):
    """El equivalente al borrador de Shopify: el usuario revisa antes."""
    doble = ml_falso()
    item, error = SERVICIO.create_product('token', BASE)

    assert error is None
    assert item['status'] == 'paused'
    assert doble.puts, 'debió pausar la publicación'
    assert doble.puts[0][1]['json'] == {'status': 'paused'}


def test_la_descripcion_va_en_su_propia_llamada(ml_falso):
    """En ML la descripción no viaja en el POST /items."""
    doble = ml_falso()
    SERVICIO.create_product('token', BASE)

    descripciones = [p for p in doble.posts if p[0].endswith('/description')]
    assert len(descripciones) == 1
    assert descripciones[0][1]['json']['plain_text'] == BASE['description']


def test_el_payload_lleva_los_defaults_sensatos(ml_falso):
    """Nada de pantallas de configuración: el default es la decisión."""
    doble = ml_falso()
    SERVICIO.create_product('token', BASE)

    enviado = doble.posts[0][1]['json']
    assert enviado['currency_id'] == 'MXN'
    assert enviado['condition'] == 'new'
    assert enviado['buying_mode'] == 'buy_it_now'
    assert enviado['listing_type_id'] == 'gold_special'
    assert enviado['pictures'] == [{'source': BASE['image_urls'][0]}]


def test_si_falla_la_descripcion_la_publicacion_sobrevive(ml_falso):
    """Ya existe el item: tirar todo por la descripción sería peor."""
    ml_falso(fallas=['descripcion'])
    item, error = SERVICIO.create_product('token', BASE)

    assert error is None
    assert item['id'] == 'MLM123456789'
    assert item['description_ok'] is False


def test_si_falla_la_pausa_reporta_el_status_real(ml_falso):
    """No damos por hecho que quedó pausada — el usuario tiene que enterarse."""
    ml_falso(fallas=['pausar'])
    item, error = SERVICIO.create_product('token', BASE)

    assert error is None
    assert item['status'] == 'active'


def test_el_error_de_ml_llega_al_llamador(ml_falso):
    ml_falso(fallas=['crear'])
    item, error = SERVICIO.create_product('token', BASE)

    assert item is None
    assert 'BRAND' in error


def test_sin_categoria_deducible_avisa_que_mejore_el_titulo(ml_falso):
    ml_falso(fallas=['categoria'])
    item, error = SERVICIO.create_product('token', BASE)

    assert item is None
    assert 'categoría' in error.lower()


# ═══════════════════════════════════════════════════════════
# RUTA
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def ml_conectado(app, client, auth_headers, monkeypatch):
    """Cuenta de ML conectada + servicio sin red."""
    from flask_jwt_extended import decode_token

    user_id = int(decode_token(auth_headers['Authorization'].split()[1])['sub'])

    db.session.add(PlatformConnection(
        user_id=user_id, platform='mercadolibre', store_name='cuenta-de-prueba',
        access_token='token-falso', external_user_id='123', is_active=True
    ))
    db.session.commit()

    monkeypatch.setattr(
        mercadolibre_service, 'get_valid_token', lambda conexion: ('token-falso', None)
    )
    return user_id


def test_ruta_publica_y_guarda_el_producto_en_vendeflow(client, auth_headers, ml_conectado, monkeypatch):
    """VendeFlow es la fuente de verdad: el producto tiene que quedar aquí."""
    monkeypatch.setattr(mercadolibre_service, 'create_product', lambda token, data: ({
        'id': 'MLM123456789', 'status': 'paused', 'description_ok': True,
        'permalink': 'https://articulo.mercadolibre.com.mx/MLM123456789',
        'category_id': 'MLM1000', 'category_name': 'Cámaras Deportivas',
    }, None))

    response = client.post('/api/mercadolibre/create-product', json={
        'title': 'GoPro Hero Mission Pro camara 5.3K',
        'description': 'Camara de accion.',
        'sku': 'gopro-001', 'price': 8999.0, 'quantity': 3,
        'image_urls': ['https://cdn.ejemplo.com/gopro.jpg'],
    }, headers=auth_headers)

    assert response.status_code == 201
    assert response.json['item_id'] == 'MLM123456789'
    assert response.json['status'] == 'paused'

    inventario = client.get('/api/inventory', headers=auth_headers)
    productos = {p['sku']: p for p in inventario.json['products']}
    assert 'GOPRO-001' in productos


def test_ruta_avisa_si_la_publicacion_quedo_activa(client, auth_headers, ml_conectado, monkeypatch):
    monkeypatch.setattr(mercadolibre_service, 'create_product', lambda token, data: ({
        'id': 'MLM1', 'status': 'active', 'description_ok': True,
    }, None))

    response = client.post('/api/mercadolibre/create-product', json={
        'title': 'Producto', 'sku': 'X-1', 'price': 100.0,
    }, headers=auth_headers)

    assert response.status_code == 201
    assert 'ACTIVA' in response.json['message']


def test_ruta_sin_cuenta_conectada(client, auth_headers):
    response = client.post('/api/mercadolibre/create-product', json={
        'title': 'Producto', 'sku': 'X-1', 'price': 100.0,
    }, headers=auth_headers)

    assert response.status_code == 400
    assert 'Mercado Libre' in response.json['error']


def test_ruta_exige_sku(client, auth_headers, ml_conectado):
    response = client.post('/api/mercadolibre/create-product', json={
        'title': 'Producto', 'price': 100.0,
    }, headers=auth_headers)

    assert response.status_code == 400
    assert 'SKU' in response.json['error']


def test_ruta_requiere_autenticacion(client):
    response = client.post('/api/mercadolibre/create-product', json={'title': 'X', 'sku': 'X-1'})
    assert response.status_code == 401
