"""
VendeFlow - Servicio de Inteligencia Artificial
================================================

Usa Claude API (Anthropic) para generar contenido optimizado
de productos para cada plataforma de e-commerce.

¿POR QUÉ CLAUDE API?
---------------------
Cada plataforma tiene requisitos diferentes y estrictos:
  - Shopify:       título libre, descripción HTML, tags SEO
  - Mercado Libre: título MÁXIMO 60 chars, sin HTML, palabras clave al inicio
  - Amazon:        exactamente 5 bullet points, keywords backend, fondo blanco

Un humano tarda 30-60 minutos en crear contenido para las 3 plataformas.
Claude lo hace en segundos con conocimiento de e-commerce LATAM.

FLUJO:
------
1. Usuario llena datos básicos del producto
2. ai_service genera contenido con Claude API
3. Usuario REVISA y EDITA (human in the loop)
4. Usuario confirma → se publica en todas las plataformas
"""

import os
import json
import anthropic
from typing import Optional


class AIService:
    """
    Servicio de IA para generación de contenido de productos.
    """

    # Modelo de Claude a usar
    MODEL = "claude-sonnet-4-20250514"

    def __init__(self):
        """
        Inicializa el cliente de Anthropic con la API key del .env
        """
        self.client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )

    # ═══════════════════════════════════════════════════════════
    # MÉTODO PRINCIPAL: GENERAR LISTING MULTI-PLATAFORMA
    # ═══════════════════════════════════════════════════════════

    def generate_listing(
        self,
        name: str,
        description: str = '',
        category: str = '',
        brand: str = '',
        price: float = 0.0,
        platforms: list = None
    ) -> dict:
        """
        Genera contenido optimizado para múltiples plataformas con Claude.

        Args:
            name:        Nombre base del producto
            description: Descripción corta opcional del usuario
            category:    Categoría del producto
            brand:       Marca del producto
            price:       Precio en MXN
            platforms:   Lista de plataformas ['shopify', 'mercadolibre', 'amazon']
                         Si es None, genera para todas

        Returns:
            Dict con contenido optimizado por plataforma:
            {
                "shopify": {
                    "title": "...",
                    "description_html": "...",
                    "tags": [...],
                    "seo_title": "...",
                    "seo_description": "..."
                },
                "mercadolibre": {
                    "title": "...",          ← máx 60 chars
                    "description": "...",    ← texto plano, sin HTML
                    "category_hint": "...",
                    "keywords": [...]
                },
                "amazon": {
                    "title": "...",
                    "bullet_points": [...],  ← exactamente 5
                    "description": "...",
                    "backend_keywords": "..."
                }
            }
        """
        if platforms is None:
            platforms = ['shopify', 'mercadolibre', 'amazon']

        # Construir el prompt con todos los requisitos
        prompt = self._build_prompt(name, description, category, brand, price, platforms)

        try:
            message = self.client.messages.create(
                model=self.MODEL,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extraer el texto de la respuesta
            response_text = message.content[0].text

            # Parsear el JSON que Claude generó
            result = self._parse_response(response_text, platforms)
            return result

        except anthropic.APIError as e:
            raise ValueError(f"Error de Anthropic API: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error al generar contenido: {str(e)}")

    # ═══════════════════════════════════════════════════════════
    # CONSTRUIR PROMPT
    # ═══════════════════════════════════════════════════════════

    def _build_prompt(
        self,
        name: str,
        description: str,
        category: str,
        brand: str,
        price: float,
        platforms: list
    ) -> str:
        """
        Construye el prompt con los requisitos específicos de cada plataforma.

        ¿POR QUÉ UN PROMPT TAN DETALLADO?
        -----------------------------------
        Si el prompt es vago → Claude genera contenido genérico
        Si el prompt es específico → Claude respeta los límites de cada plataforma

        Los requisitos más críticos:
        - ML: título EXACTAMENTE máx 60 chars (Claude a veces se pasa)
        - Amazon: EXACTAMENTE 5 bullet points (ni más ni menos)
        - Shopify: descripción en HTML válido (h2, ul, strong)
        """

        # Construir sección de plataformas solicitadas
        platforms_section = self._build_platforms_requirements(platforms)

        # Construir sección de datos del producto
        product_info = f"""
Producto:
- Nombre: {name}
- Descripción base: {description if description else 'No proporcionada'}
- Categoría: {category if category else 'No especificada'}
- Marca: {brand if brand else 'No especificada'}
- Precio: ${price:.2f} MXN
"""

        prompt = f"""Eres un experto en e-commerce para LATAM con 10+ años de experiencia optimizando listings en Shopify, Mercado Libre y Amazon México. Conoces perfectamente los algoritmos de búsqueda y los requisitos técnicos de cada plataforma.

{product_info}

Genera contenido de producto optimizado ÚNICAMENTE para estas plataformas: {', '.join(platforms)}

{platforms_section}

REGLAS GENERALES:
- Usa español de México (MX) natural y persuasivo
- Enfócate en los beneficios para el comprador, no solo características
- Incluye palabras clave relevantes de forma natural
- Si la marca no está especificada, no la inventes

FORMATO DE RESPUESTA:
Responde ÚNICAMENTE con un JSON válido, sin texto adicional, sin ```json, sin explicaciones.
El JSON debe tener exactamente esta estructura:
{{
  {self._build_json_structure(platforms)}
}}"""

        return prompt

    def _build_platforms_requirements(self, platforms: list) -> str:
        """Construye los requisitos específicos de cada plataforma solicitada."""

        requirements = []

        if 'shopify' in platforms:
            requirements.append("""
SHOPIFY (requisitos):
- title: Título atractivo, máx 255 chars, incluir marca y modelo
- description_html: Descripción completa en HTML con:
    * <h2> para secciones principales (Características, Beneficios, Especificaciones)
    * <ul><li> para listas de puntos
    * <strong> para términos importantes
    * Mínimo 150 palabras
- tags: Array de 8-12 tags relevantes para búsqueda interna (strings en minúsculas)
- seo_title: Optimizado para Google, máx 70 chars
- seo_description: Meta description atractiva, máx 160 chars""")

        if 'mercadolibre' in platforms:
            requirements.append("""
MERCADO LIBRE (requisitos — MUY ESTRICTOS):
- title: ⚠️ MÁXIMO 60 CARACTERES (cuenta exactamente, incluyendo espacios)
    * Fórmula: [Marca] + [Producto] + [Característica principal] + [Modelo]
    * Las palabras más buscadas deben ir AL INICIO
    * NO uses signos de puntuación innecesarios
- description: Texto plano SIN HTML, SIN etiquetas, SIN markdown
    * Mínimo 100 palabras, máximo 500
    * Párrafos separados por salto de línea
    * Menciona compatibilidad, materiales, contenido del paquete
- category_hint: Categoría sugerida en español (ej: "Fotografía y Video > Accesorios GoPro")
- keywords: Array de 5-8 palabras clave más buscadas para este producto""")

        if 'amazon' in platforms:
            requirements.append("""
AMAZON MÉXICO (requisitos):
- title: Fórmula: [Marca] [Producto] [Material/Característica] [Color] [Cantidad]
    * Máx 200 chars, incluir keywords principales
- bullet_points: Array de EXACTAMENTE 5 strings, cada uno:
    * Empieza con término en MAYÚSCULAS seguido de dos puntos
    * Describe un beneficio específico orientado al comprador
    * Entre 100-250 chars por bullet
    * Ejemplo: "COMPATIBILIDAD GARANTIZADA: Compatible con GoPro Hero 8 Black..."
- description: Descripción optimizada para SEO, 250-500 palabras
    * Puede incluir HTML básico (<b>, <br>)
- backend_keywords: String de keywords separadas por espacio
    * NO repetir palabras ya usadas en el título
    * Máx 250 bytes""")

        return '\n'.join(requirements)

    def _build_json_structure(self, platforms: list) -> str:
        """Construye la estructura JSON esperada según las plataformas."""

        parts = []

        if 'shopify' in platforms:
            parts.append('''"shopify": {
    "title": "string",
    "description_html": "string con HTML",
    "tags": ["tag1", "tag2"],
    "seo_title": "string max 70 chars",
    "seo_description": "string max 160 chars"
  }''')

        if 'mercadolibre' in platforms:
            parts.append('''"mercadolibre": {
    "title": "string MÁXIMO 60 chars",
    "description": "string texto plano sin HTML",
    "category_hint": "string",
    "keywords": ["keyword1", "keyword2"]
  }''')

        if 'amazon' in platforms:
            parts.append('''"amazon": {
    "title": "string max 200 chars",
    "bullet_points": ["bullet 1", "bullet 2", "bullet 3", "bullet 4", "bullet 5"],
    "description": "string",
    "backend_keywords": "string"
  }''')

        return ',\n  '.join(parts)

    # ═══════════════════════════════════════════════════════════
    # PARSEAR RESPUESTA DE CLAUDE
    # ═══════════════════════════════════════════════════════════

    def _parse_response(self, response_text: str, platforms: list) -> dict:
        """
        Parsea la respuesta JSON de Claude y valida los campos críticos.

        ¿POR QUÉ VALIDAR DESPUÉS DE PARSEAR?
        --------------------------------------
        Claude a veces se pasa del límite de 60 chars en ML aunque
        se lo digamos en el prompt. Por eso validamos y truncamos
        si es necesario — mejor truncar que fallar.
        """
        # Limpiar posibles backticks que Claude pueda agregar
        clean_text = response_text.strip()
        if clean_text.startswith('```'):
            clean_text = clean_text.split('\n', 1)[1]
        if clean_text.endswith('```'):
            clean_text = clean_text.rsplit('```', 1)[0]
        clean_text = clean_text.strip()

        try:
            data = json.loads(clean_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Claude no devolvió JSON válido: {e}\nRespuesta: {response_text[:200]}")

        # ─── Validaciones críticas ────────────────────────────

        # ML: título máx 60 chars (validación de seguridad)
        if 'mercadolibre' in data and 'title' in data['mercadolibre']:
            ml_title = data['mercadolibre']['title']
            if len(ml_title) > 60:
                data['mercadolibre']['title'] = ml_title[:60].rsplit(' ', 1)[0]
                data['mercadolibre']['title_truncated'] = True

        # Amazon: exactamente 5 bullet points
        if 'amazon' in data and 'bullet_points' in data['amazon']:
            bullets = data['amazon']['bullet_points']
            if len(bullets) > 5:
                data['amazon']['bullet_points'] = bullets[:5]
            elif len(bullets) < 5:
                # Rellenar si faltan
                while len(data['amazon']['bullet_points']) < 5:
                    data['amazon']['bullet_points'].append(
                        f"CALIDAD GARANTIZADA: Producto de alta calidad verificado."
                    )

        # Agregar metadata
        data['generated_at'] = __import__('datetime').datetime.utcnow().isoformat()
        data['platforms'] = platforms

        return data

    # ═══════════════════════════════════════════════════════════
    # MÉTODO: MEJORAR DESCRIPCIÓN EXISTENTE
    # ═══════════════════════════════════════════════════════════

    def improve_description(self, current_description: str, platform: str) -> str:
        """
        Mejora una descripción existente para una plataforma específica.

        Útil cuando el usuario ya tiene un producto en VendeFlow
        y quiere mejorar solo la descripción para una plataforma.

        Args:
            current_description: Descripción actual del producto
            platform: 'shopify', 'mercadolibre' o 'amazon'

        Returns:
            Descripción mejorada como string
        """
        platform_rules = {
            'shopify': "en HTML con h2, ul, strong. Mínimo 150 palabras.",
            'mercadolibre': "en texto plano SIN HTML. Entre 100-500 palabras.",
            'amazon': "optimizada para SEO con keywords naturales. 250-500 palabras."
        }

        rules = platform_rules.get(platform, "clara y persuasiva")

        prompt = f"""Mejora esta descripción de producto para {platform.upper()}:

Descripción actual:
{current_description}

Reglas para {platform}:
- Escribe {rules}
- Usa español de México natural y persuasivo
- Enfócate en beneficios para el comprador

Responde ÚNICAMENTE con la descripción mejorada, sin explicaciones."""

        try:
            message = self.client.messages.create(
                model=self.MODEL,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            raise ValueError(f"Error al mejorar descripción: {str(e)}")


# Instancia global del servicio
ai_service = AIService()
