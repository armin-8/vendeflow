"""
VendeFlow - Helper de Encriptación
====================================

Encripta y desencripta tokens sensibles (Shopify, ML) antes de guardarlos
en la base de datos.

¿POR QUÉ ENCRIPTAR?
--------------------
Si alguien accede a la BD (hack, backup expuesto, empleado):
  SIN encriptación → ve los tokens reales → acceso total a las tiendas
  CON encriptación → ve texto cifrado → no puede hacer nada

¿QUÉ ES FERNET?
----------------
Fernet es encriptación simétrica AES-128-CBC con verificación de integridad.
La misma clave encripta y desencripta. Es el estándar de la industria para
este tipo de datos en aplicaciones web.

FLUJO:
------
Guardar:    token_real → encrypt() → "gAAAAABh3x...cifrado..." → BD
Usar:       BD → "gAAAAABh3x...cifrado..." → decrypt() → token_real → API
"""

import os
from cryptography.fernet import Fernet, InvalidToken


def _get_cipher():
    """
    Obtiene el objeto Fernet usando la clave del .env.

    ¿POR QUÉ UNA FUNCIÓN PRIVADA?
    Así la clave se lee del .env cada vez que se necesita,
    sin exponerla como variable global en memoria.
    """
    key = os.getenv('ENCRYPTION_KEY')

    if not key:
        raise ValueError(
            "ENCRYPTION_KEY no está configurada en el .env. "
            "Genera una con: python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )

    return Fernet(key.encode())


def encrypt_token(token: str) -> str:
    """
    Encripta un token para guardarlo en la BD.

    Args:
        token: El token en texto plano

    Returns:
        Token encriptado como string (empieza con 'gAAAAA')
    """
    if not token:
        return token

    cipher = _get_cipher()
    return cipher.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """
    Desencripta un token para usarlo en llamadas a APIs externas.

    Args:
        encrypted_token: Token encriptado desde la BD

    Returns:
        Token original en texto plano

    Raises:
        ValueError: Si el token no puede desencriptarse
    """
    if not encrypted_token:
        return encrypted_token

    try:
        cipher = _get_cipher()
        return cipher.decrypt(encrypted_token.encode()).decode()
    except InvalidToken:
        raise ValueError(
            "No se pudo desencriptar el token. "
            "Verifica que ENCRYPTION_KEY en el .env sea la correcta."
        )


def is_encrypted(token: str) -> bool:
    """
    Detecta si un token ya está encriptado.

    Los tokens Fernet siempre empiezan con 'gAAAAA'.
    Útil para migrar tokens existentes sin re-encriptar los que ya lo están.

    Args:
        token: Token a verificar

    Returns:
        True si ya está encriptado, False si está en texto plano
    """
    if not token:
        return False
    return token.startswith('gAAAAA')
