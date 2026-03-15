"""
VendeFlow - Servicio de Mercado Libre con OAuth
================================================

Este servicio maneja:
1. Flujo OAuth para conectar la cuenta de ML
2. Renovación automática de tokens (cada 6 horas)
3. Comunicación con la API de ML
4. Sincronización de productos e inventario

¿POR QUÉ ES DIFERENTE A SHOPIFY?
----------------------------------
Shopify:       access_token permanente, no expira
Mercado Libre: access_token dura 6 horas → necesitamos refresh_token

FLUJO OAUTH:
------------
1. get_auth_url()              → URL para redirigir al usuario a ML
2. exchange_code_for_token()   → Intercambiar código por access_token + refresh_token
3. refresh_access_token()      → Renovar token cuando expira (automático)
4. Guardar todo en PlatformConnection

ENDPOINTS DE ML QUE USAMOS:
----------------------------
- GET  /users/me                          → Info del usuario (para obtener su ID)
- GET  /users/{user_id}/items/search      → Listar publicaciones
- GET  /items/{item_id}                   → Detalle de una publicación
- PUT  /items/{item_id}                   → Actualizar stock de una publicación
"""

import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlencode


class MercadoLibreService:
    """
    Servicio para interactuar con la API de Mercado Libre usando OAuth 2.0.
    """

    # URL base de la API de ML para México
    BASE_URL = 'https://api.mercadolibre.com'

    # URL de autorización OAuth
    AUTH_URL = 'https://auth.mercadolibre.com.mx/authorization'

    # URL para intercambiar/refrescar tokens
    TOKEN_URL = 'https://api.mercadolibre.com/oauth/token'

    def __init__(self):
        """
        Inicializa el servicio con las credenciales del .env
        """
        self.app_id = os.getenv('MERCADOLIBRE_APP_ID')
        self.secret_key = os.getenv('MERCADOLIBRE_SECRET_KEY')
        self.redirect_uri = os.getenv('MERCADOLIBRE_REDIRECT_URI')

    # ═══════════════════════════════════════════════════════════
    # OAUTH PASO 1: GENERAR URL DE AUTORIZACIÓN
    # ═══════════════════════════════════════════════════════════

    def get_auth_url(self, state: str) -> str:
        """
        Genera la URL para redirigir al usuario a Mercado Libre.

        A diferencia de Shopify, ML tiene UNA sola URL de auth para todos
        los usuarios. No varía por tienda.

        Args:
            state: Token aleatorio para validar que el callback es legítimo.
                   Lo codificamos con el user_id para recuperarlo después.

        Returns:
            URL completa a la que redirigir al usuario
        """
        params = {
            'response_type': 'code',
            'client_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'state': state,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    # ═══════════════════════════════════════════════════════════
    # OAUTH PASO 2: INTERCAMBIAR CÓDIGO POR TOKENS
    # ═══════════════════════════════════════════════════════════

    def exchange_code_for_token(self, code: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Intercambia el código de autorización por access_token y refresh_token.

        ML nos devuelve:
        - access_token:  Token de acceso, dura 6 horas
        - refresh_token: Token de refresco, dura 6 meses
        - expires_in:    Segundos hasta que expira el access_token (21600 = 6h)
        - user_id:       ID numérico del usuario en ML

        Args:
            code: Código que ML envía al callback URL

        Returns:
            (token_data, error) — token_data es None si hubo error
        """
        payload = {
            'grant_type': 'authorization_code',
            'client_id': self.app_id,
            'client_secret': self.secret_key,
            'code': code,
            'redirect_uri': self.redirect_uri,
        }

        try:
            response = requests.post(self.TOKEN_URL, data=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Calculamos la fecha exacta de expiración
                # expires_in viene en segundos (normalmente 21600 = 6 horas)
                expires_in = data.get('expires_in', 21600)
                data['expires_at'] = datetime.utcnow() + timedelta(seconds=expires_in)
                return data, None
            else:
                error_msg = response.json().get('message', response.text)
                return None, f"Error {response.status_code}: {error_msg}"

        except requests.exceptions.RequestException as e:
            return None, f"Error de conexión: {str(e)}"

    # ═══════════════════════════════════════════════════════════
    # OAUTH PASO 3: REFRESCAR TOKEN (AUTOMÁTICO)
    # ═══════════════════════════════════════════════════════════

    def refresh_access_token(self, refresh_token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Renueva el access_token usando el refresh_token.

        Se llama AUTOMÁTICAMENTE cuando detectamos que el token expiró.
        El usuario nunca tiene que reconectar su cuenta.

        Args:
            refresh_token: El refresh_token guardado en PlatformConnection

        Returns:
            (token_data, error)
        """
        payload = {
            'grant_type': 'refresh_token',
            'client_id': self.app_id,
            'client_secret': self.secret_key,
            'refresh_token': refresh_token,
        }

        try:
            response = requests.post(self.TOKEN_URL, data=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                expires_in = data.get('expires_in', 21600)
                data['expires_at'] = datetime.utcnow() + timedelta(seconds=expires_in)
                return data, None
            else:
                error_msg = response.json().get('message', response.text)
                return None, f"Error al refrescar token: {error_msg}"

        except requests.exceptions.RequestException as e:
            return None, f"Error de conexión: {str(e)}"

    # ═══════════════════════════════════════════════════════════
    # HELPER: OBTENER TOKEN VÁLIDO (refresca si es necesario)
    # ═══════════════════════════════════════════════════════════

    def get_valid_token(self, connection) -> Tuple[Optional[str], Optional[str]]:
        """
        Retorna un access_token válido. Si expiró, lo refresca automáticamente.

        Este método es la clave de la integración con ML. Antes de CADA
        llamada a la API, usamos este método en lugar del token directo.

        Flujo:
            1. ¿El token expiró? (usando is_token_expired del modelo)
            2. Si SÍ  → refresh_access_token() → guardar nuevos tokens
            3. Si NO  → usar el token actual

        Args:
            connection: Instancia de PlatformConnection de la base de datos

        Returns:
            (access_token, error)
        """
        # Si el token sigue válido, lo usamos directamente
        if not connection.is_token_expired:
            return connection.access_token, None

        # Si expiró, lo refrescamos
        if not connection.refresh_token:
            return None, "No hay refresh_token. El usuario debe reconectar su cuenta."

        token_data, error = self.refresh_access_token(connection.refresh_token)

        if error:
            return None, error

        # Actualizar los tokens en la base de datos
        # Importamos db aquí para evitar importación circular
        from app import db

        connection.access_token = token_data['access_token']
        connection.refresh_token = token_data.get('refresh_token', connection.refresh_token)
        connection.token_expires_at = token_data['expires_at']

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return None, f"Error al guardar token renovado: {str(e)}"

        return connection.access_token, None

    # ═══════════════════════════════════════════════════════════
    # API: OBTENER INFO DEL USUARIO
    # ═══════════════════════════════════════════════════════════

    def get_user_info(self, access_token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Obtiene la información del usuario autenticado en ML.

        Lo usamos para:
        - Verificar que la conexión funciona
        - Obtener el user_id numérico (necesario para otras APIs)
        - Mostrar el nickname de la cuenta conectada

        Args:
            access_token: Token de acceso válido

        Returns:
            (user_info, error)
        """
        headers = {'Authorization': f'Bearer {access_token}'}

        try:
            response = requests.get(
                f"{self.BASE_URL}/users/me",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f"Error {response.status_code}: {response.text}"

        except requests.exceptions.RequestException as e:
            return None, f"Error de conexión: {str(e)}"

    # ═══════════════════════════════════════════════════════════
    # API: OBTENER PUBLICACIONES DEL USUARIO
    # ═══════════════════════════════════════════════════════════

    def get_user_items(self, access_token: str, ml_user_id: str) -> Tuple[List[str], Optional[str]]:
        """
        Obtiene la lista de IDs de publicaciones del usuario.

        La API de ML no devuelve los detalles directamente, solo los IDs.
        Después hay que pedir el detalle de cada uno (get_item_details).

        ML pagina de 50 en 50. Iteramos hasta obtener todos.

        Args:
            access_token: Token de acceso válido
            ml_user_id:   ID numérico del usuario en ML

        Returns:
            (lista_de_item_ids, error)
        """
        headers = {'Authorization': f'Bearer {access_token}'}
        all_item_ids = []
        offset = 0
        limit = 50  # Máximo permitido por ML

        try:
            while True:
                url = (
                    f"{self.BASE_URL}/users/{ml_user_id}/items/search"
                    f"?limit={limit}&offset={offset}"
                )
                response = requests.get(url, headers=headers, timeout=15)

                if response.status_code != 200:
                    return [], f"Error {response.status_code}: {response.text}"

                data = response.json()
                results = data.get('results', [])

                if not results:
                    break  # No hay más publicaciones

                all_item_ids.extend(results)

                # Si obtuvimos menos del límite, ya llegamos al final
                if len(results) < limit:
                    break

                offset += limit

            return all_item_ids, None

        except requests.exceptions.RequestException as e:
            return [], f"Error de conexión: {str(e)}"

    # ═══════════════════════════════════════════════════════════
    # API: OBTENER DETALLES DE PUBLICACIONES (en lote)
    # ═══════════════════════════════════════════════════════════

    def get_items_details(self, access_token: str, item_ids: List[str]) -> Tuple[List[Dict], Optional[str]]:
        """
        Obtiene los detalles de múltiples publicaciones en una sola llamada.

        ML permite pedir hasta 20 items a la vez con el endpoint /items?ids=...
        Esto es más eficiente que hacer una llamada por item.

        Args:
            access_token: Token de acceso válido
            item_ids:     Lista de IDs de publicaciones

        Returns:
            (lista_de_items, error)
        """
        headers = {'Authorization': f'Bearer {access_token}'}
        all_items = []

        # Dividir en lotes de 20 (límite de ML)
        batch_size = 20
        batches = [item_ids[i:i + batch_size] for i in range(0, len(item_ids), batch_size)]

        try:
            for batch in batches:
                ids_param = ','.join(batch)
                url = f"{self.BASE_URL}/items?ids={ids_param}"

                response = requests.get(url, headers=headers, timeout=15)

                if response.status_code != 200:
                    return [], f"Error {response.status_code}: {response.text}"

                results = response.json()

                # ML devuelve [{code: 200, body: {...}}, ...]
                for result in results:
                    if result.get('code') == 200:
                        all_items.append(result.get('body', {}))

            return all_items, None

        except requests.exceptions.RequestException as e:
            return [], f"Error de conexión: {str(e)}"

    # ═══════════════════════════════════════════════════════════
    # API: NORMALIZAR PRODUCTOS AL FORMATO VENDEFLOW
    # ═══════════════════════════════════════════════════════════

    def normalize_items(self, ml_items: List[Dict]) -> List[Dict]:
        """
        Convierte publicaciones de ML al formato interno de VendeFlow.

        Esto se llama "normalización" — cada plataforma tiene su propio
        formato, y nosotros los unificamos en el formato de VendeFlow.

        Args:
            ml_items: Lista de publicaciones en formato de ML

        Returns:
            Lista de productos en formato VendeFlow
        """
        normalized = []

        for item in ml_items:
            # Intentar obtener el SKU del seller_custom_field
            # o del atributo SELLER_SKU
            sku = item.get('seller_custom_field') or ''

            if not sku:
                # Buscar en atributos
                for attr in item.get('attributes', []):
                    if attr.get('id') == 'SELLER_SKU':
                        sku = attr.get('value_name', '')
                        break

            # Si no tiene SKU definido, usamos el ID de ML como SKU
            if not sku:
                sku = item.get('id', '')

            if not sku:
                continue

            # Obtener imágenes
            pictures = item.get('pictures', [])
            image_url = pictures[0].get('url', '') if pictures else None

            normalized_product = {
                'sku': str(sku).upper().strip(),
                'name': item.get('title', ''),
                'description': '',  # ML no devuelve descripción en este endpoint
                'price': float(item.get('price', 0) or 0),
                'cost': None,  # ML no tiene concepto de costo
                'quantity': int(item.get('available_quantity', 0) or 0),
                'category': item.get('category_id', ''),
                'brand': None,
                'image_url': image_url,
                'mercadolibre_item_id': item.get('id'),
                'mercadolibre_status': item.get('status'),  # active, paused, closed
            }

            normalized.append(normalized_product)

        return normalized

    # ═══════════════════════════════════════════════════════════
    # API: ACTUALIZAR STOCK EN ML
    # ═══════════════════════════════════════════════════════════

    def update_stock(self, access_token: str, item_id: str, quantity: int) -> Tuple[bool, str]:
        """
        Actualiza el stock disponible de una publicación en ML.

        En ML, el stock se actualiza modificando la publicación
        con el campo 'available_quantity'.

        Args:
            access_token: Token de acceso válido
            item_id:      ID de la publicación en ML (ej: MLM123456789)
            quantity:     Nueva cantidad disponible

        Returns:
            (success, message)
        """
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

        try:
            url = f"{self.BASE_URL}/items/{item_id}"
            response = requests.put(
                url,
                headers=headers,
                json={'available_quantity': quantity},
                timeout=10
            )

            if response.status_code == 200:
                return True, f"Stock actualizado a {quantity} unidades"
            else:
                error_data = response.json()
                msg = error_data.get('message', response.text)
                return False, f"Error {response.status_code}: {msg}"

        except requests.exceptions.RequestException as e:
            return False, f"Error de conexión: {str(e)}"

    # ═══════════════════════════════════════════════════════════
    # API: VERIFICAR CONEXIÓN
    # ═══════════════════════════════════════════════════════════

    def test_connection(self, access_token: str) -> Tuple[bool, str]:
        """
        Prueba que la conexión con ML funciona correctamente.

        Args:
            access_token: Token de acceso válido

        Returns:
            (success, message)
        """
        user_info, error = self.get_user_info(access_token)

        if error:
            return False, error

        nickname = user_info.get('nickname', 'Usuario')
        return True, f"Conectado como: {nickname}"


# Instancia global del servicio
mercadolibre_service = MercadoLibreService()
