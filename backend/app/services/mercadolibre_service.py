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
- PUT  /items/{item_id}                   → Actualizar stock / pausar una publicación
- POST /items                             → Crear una publicación nueva
- POST /items/{item_id}/description       → Ponerle descripción a la publicación
- GET  /sites/MLM/domain_discovery/search → Adivinar la categoría a partir del título
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

    # Sitio de Mercado Libre México. Todo lo de categorías y publicaciones va
    # por sitio: una categoría de MLM no existe en MLA (Argentina).
    SITE_ID = 'MLM'

    # ─── Defaults de publicación ─────────────────────────────
    # El usuario que atendemos no sabe (ni tiene por qué saber) qué es un
    # listing_type ni un buying_mode. Estos valores cubren el caso normal:
    #   gold_special = "Clásica", la publicación estándar de MLM
    #   buy_it_now   = compra directa (no subasta)
    #   new          = producto nuevo
    # Se pueden sobreescribir desde product_data si algún día hace falta.
    DEFAULT_LISTING_TYPE = 'gold_special'
    DEFAULT_CONDITION = 'new'
    DEFAULT_CURRENCY = 'MXN'

    # ML corta los títulos a 60 caracteres. Lo aplicamos nosotros para no
    # depender de que el texto llegue ya recortado desde la IA o de la UI.
    MAX_TITLE_CHARS = 60

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
    # API: DEDUCIR LA CATEGORÍA
    # ═══════════════════════════════════════════════════════════

    def predict_category(self, access_token: str, query: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Deduce la categoría de ML a partir del título del producto.

        ML exige un `category_id` para publicar y el árbol de MLM tiene miles
        de nodos. Preguntárselo al usuario sería mandarlo a navegar ese árbol;
        en vez de eso usamos el mismo predictor que ML usa en su propio
        formulario de publicación.

        Args:
            access_token: Token válido
            query:        Título del producto (entre más descriptivo, mejor)

        Returns:
            (categoria, error) — categoria trae category_id, category_name y domain_id
        """
        if not query or not query.strip():
            return None, 'Se necesita el título del producto para deducir la categoría'

        url = f"{self.BASE_URL}/sites/{self.SITE_ID}/domain_discovery/search"

        try:
            response = requests.get(
                url,
                headers={'Authorization': f'Bearer {access_token}'},
                params={'q': query.strip(), 'limit': 1},
                timeout=10
            )

            if response.status_code != 200:
                return None, self._mensaje_de_error(response)

            resultados = response.json() or []
            if not resultados:
                return None, ('No pudimos deducir la categoría con ese título. '
                              'Hazlo más descriptivo (ej: "Camara de accion 5.3K" '
                              'en vez de solo la marca).')

            mejor = resultados[0]
            if not mejor.get('category_id'):
                return None, 'Mercado Libre no devolvió una categoría para ese título'

            return {
                'category_id': mejor.get('category_id'),
                'category_name': mejor.get('category_name', ''),
                'domain_id': mejor.get('domain_id', ''),
            }, None

        except requests.exceptions.RequestException as e:
            return None, f"Error de conexión: {str(e)}"

    # ═══════════════════════════════════════════════════════════
    # API: CREAR PUBLICACIÓN
    # ═══════════════════════════════════════════════════════════

    def create_product(self, access_token: str, product_data: dict) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Publica un producto en Mercado Libre con el contenido de la IA.

        CAMPOS SOPORTADOS
        -----------------
        title        → máx 60 chars (se recorta aquí, sin partir palabras)
        description  → texto plano SIN HTML (va en una llamada aparte)
        category_id  → opcional; si no viene se deduce con predict_category()
        price        → MXN
        quantity     → stock inicial
        sku          → se guarda como atributo SELLER_SKU, que es justo lo que
                       lee normalize_items() cuando reimportamos desde ML
        brand, model → atributos; ML los pide en casi todas las categorías
        image_urls   → lista de URLs, ML las descarga (la primera es la portada)

        ¿POR QUÉ QUEDA PAUSADA?
        -----------------------
        Mismo criterio que el `draft` de Shopify: el usuario revisa antes de
        quedar expuesto al público. ML no tiene borradores, así que creamos y
        pausamos enseguida — son dos llamadas porque es el flujo que la API
        soporta. Si la pausa fallara, devolvemos el status REAL en el
        resultado; no damos por hecho que quedó pausada.

        Returns:
            (item, error) — item es el JSON de ML más `description_ok`
        """
        # ─── 1. Validar lo mínimo indispensable ──────────────
        title = self._recortar_titulo(product_data.get('title', ''))
        if not title:
            return None, 'El título es requerido para publicar en Mercado Libre'

        try:
            price = float(product_data.get('price', 0) or 0)
        except (TypeError, ValueError):
            price = 0
        if price <= 0:
            return None, 'El precio debe ser mayor a cero'

        imagenes = [url for url in (product_data.get('image_urls') or []) if url]
        if not imagenes:
            return None, ('Mercado Libre exige al menos una imagen para publicar. '
                          'Agrega la URL de una foto del producto.')

        # ─── 2. Categoría: la que venga, o la que deduzcamos ──
        category_id = product_data.get('category_id')
        categoria_deducida = None
        if not category_id:
            categoria_deducida, error = self.predict_category(access_token, title)
            if error:
                return None, error
            category_id = categoria_deducida['category_id']

        # ─── 3. Armar el payload ─────────────────────────────
        payload = {
            'title': title,
            'category_id': category_id,
            'price': price,
            'currency_id': product_data.get('currency_id', self.DEFAULT_CURRENCY),
            'available_quantity': max(1, int(product_data.get('quantity', 1) or 1)),
            'buying_mode': 'buy_it_now',
            'condition': product_data.get('condition', self.DEFAULT_CONDITION),
            'listing_type_id': product_data.get('listing_type_id', self.DEFAULT_LISTING_TYPE),
            'pictures': [{'source': url} for url in imagenes],
            'attributes': self._armar_atributos(product_data),
        }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(
                f"{self.BASE_URL}/items", headers=headers, json=payload, timeout=30
            )
        except requests.exceptions.RequestException as e:
            return None, f"Error de conexión: {str(e)}"

        if response.status_code not in (200, 201):
            return None, self._mensaje_de_error(response)

        item = response.json()
        item_id = item.get('id')

        # ─── 4. La descripción va aparte ─────────────────────
        # Ya existe la publicación: si esto falla no tiramos todo el trabajo,
        # solo lo reportamos para que la UI lo diga.
        item['description_ok'] = True
        descripcion = (product_data.get('description') or '').strip()
        if descripcion and item_id:
            ok, _ = self.add_description(access_token, item_id, descripcion)
            item['description_ok'] = ok

        # ─── 5. Pausarla para que el usuario la revise ───────
        if item_id and item.get('status') != 'paused':
            pausada, _ = self.pause_item(access_token, item_id)
            if pausada:
                item['status'] = 'paused'

        if categoria_deducida:
            item['category_name'] = categoria_deducida.get('category_name', '')

        return item, None

    def add_description(self, access_token: str, item_id: str, texto: str) -> Tuple[bool, str]:
        """
        Le pone la descripción a una publicación.

        En ML la descripción NO va en el POST /items: es un recurso aparte y
        solo acepta texto plano (por eso el prompt de ML prohíbe HTML).
        """
        try:
            response = requests.post(
                f"{self.BASE_URL}/items/{item_id}/description",
                headers={'Authorization': f'Bearer {access_token}',
                         'Content-Type': 'application/json'},
                json={'plain_text': texto},
                timeout=15
            )
            if response.status_code in (200, 201):
                return True, 'Descripción publicada'
            return False, self._mensaje_de_error(response)
        except requests.exceptions.RequestException as e:
            return False, f"Error de conexión: {str(e)}"

    def pause_item(self, access_token: str, item_id: str) -> Tuple[bool, str]:
        """Pausa una publicación: deja de estar visible sin borrarla."""
        try:
            response = requests.put(
                f"{self.BASE_URL}/items/{item_id}",
                headers={'Authorization': f'Bearer {access_token}',
                         'Content-Type': 'application/json'},
                json={'status': 'paused'},
                timeout=15
            )
            if response.status_code == 200:
                return True, 'Publicación pausada'
            return False, self._mensaje_de_error(response)
        except requests.exceptions.RequestException as e:
            return False, f"Error de conexión: {str(e)}"

    # ─── Auxiliares de publicación ───────────────────────────

    @classmethod
    def _recortar_titulo(cls, titulo: str) -> str:
        """60 caracteres, sin partir la última palabra a la mitad."""
        titulo = ' '.join((titulo or '').split())
        if len(titulo) <= cls.MAX_TITLE_CHARS:
            return titulo
        cortado = titulo[:cls.MAX_TITLE_CHARS]
        if ' ' in cortado:
            cortado = cortado.rsplit(' ', 1)[0]
        return cortado.rstrip(' ,-|')

    def _armar_atributos(self, product_data: dict) -> List[Dict]:
        """
        Atributos de la publicación.

        BRAND va siempre: ML lo pide como obligatorio en casi todas las
        categorías de producto físico y rechazar la publicación por eso sería
        mandarle al usuario un error que no sabe resolver. Sin marca capturada,
        "Genérico" es el valor que ML mismo sugiere.

        SELLER_SKU cierra el círculo con normalize_items(): es de donde
        sacamos el SKU cuando reimportamos la publicación desde ML.
        """
        atributos = [
            {'id': 'BRAND', 'value_name': (product_data.get('brand') or '').strip() or 'Genérico'},
        ]

        modelo = (product_data.get('model') or '').strip()
        if modelo:
            atributos.append({'id': 'MODEL', 'value_name': modelo})

        sku = (product_data.get('sku') or '').strip()
        if sku:
            atributos.append({'id': 'SELLER_SKU', 'value_name': sku.upper()})

        return atributos

    @staticmethod
    def _mensaje_de_error(response) -> str:
        """
        ML manda el detalle útil en `cause`, no en `message`.

        Sin desdoblar `cause` el usuario ve "Bad Request" y no se entera de que
        le faltó, por ejemplo, el atributo obligatorio de la categoría.
        """
        try:
            data = response.json()
        except ValueError:
            return f"Error {response.status_code}: {response.text[:200]}"

        detalles = []
        for causa in (data.get('cause') or []):
            texto = causa.get('message') if isinstance(causa, dict) else str(causa)
            if texto:
                detalles.append(texto)

        detalle = ' | '.join(detalles) or data.get('message') or response.text[:200]
        return f"Error {response.status_code}: {detalle}"

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
