"""
VendeFlow - State firmado para OAuth
======================================

El parámetro `state` de OAuth viaja por el navegador del usuario: sale en la
URL de autorización y regresa en el callback. Cualquiera puede leerlo y —si no
está protegido— fabricarlo.

EL PROBLEMA QUE RESUELVE
-------------------------
Antes el state era texto plano: "random:user_id:shop". Como el callback solo lo
partía en pedazos y confiaba en el user_id que venía dentro, un atacante podía
visitar el callback con un state fabricado y colgar SU tienda a la cuenta de
OTRO usuario (o la tienda de la víctima a su propia cuenta).

LA SOLUCIÓN
-----------
Firmamos el state con SECRET_KEY usando itsdangerous (viene con Flask). La firma
va anexada al payload:

    payload {user_id, shop} → serializar → "eyJ1c2VyX2lk...".timestamp.firma

Si alguien cambia un solo byte del payload, la firma deja de cuadrar y
verify_state() rechaza el callback. Y como la firma lleva timestamp, el state
caduca a los 10 minutos — un flujo OAuth que quedó a medias no sirve para
siempre.

No necesitamos guardar nada en servidor (ni sesión, ni Redis): la firma ES la
prueba de que el state lo emitimos nosotros.
"""

from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# Vida máxima del state: el usuario tiene 10 min para completar el OAuth
STATE_MAX_AGE_SECONDS = 600


def _serializer(platform: str) -> URLSafeTimedSerializer:
    """
    Crea el serializador para una plataforma.

    El `salt` distinto por plataforma evita que un state emitido para Shopify
    pueda reutilizarse en el callback de Mercado Libre.
    """
    return URLSafeTimedSerializer(
        secret_key=current_app.config['SECRET_KEY'],
        salt=f'vendeflow-oauth-{platform}'
    )


def generate_state(platform: str, payload: dict) -> str:
    """
    Genera un state firmado para iniciar el flujo OAuth.

    Args:
        platform: 'shopify' o 'mercadolibre'
        payload:  Datos a transportar (ej: {'user_id': 1, 'shop': 'mi-tienda'})

    Returns:
        String firmado, seguro para poner en una URL
    """
    return _serializer(platform).dumps(payload)


def verify_state(platform: str, state: str) -> tuple[dict | None, str | None]:
    """
    Verifica la firma del state y devuelve el payload original.

    Args:
        platform: 'shopify' o 'mercadolibre'
        state:    El state recibido en el callback

    Returns:
        (payload, None)  si la firma es válida y no expiró
        (None, motivo)   si algo falló
    """
    if not state:
        return None, 'missing_state'

    try:
        payload = _serializer(platform).loads(state, max_age=STATE_MAX_AGE_SECONDS)
    except SignatureExpired:
        return None, 'expired_state'
    except BadSignature:
        return None, 'invalid_state'

    if not isinstance(payload, dict):
        return None, 'invalid_state'

    return payload, None
