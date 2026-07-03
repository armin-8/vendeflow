"""
VendeFlow - Servicio de Inteligencia Artificial con Ollama
===========================================================

Usa Ollama (local) para generar contenido optimizado de productos
para cada plataforma de e-commerce. Corre 100% en tu Mac, sin
costos ni dependencias externas.

¿POR QUÉ OLLAMA?
-----------------
- Gratis y sin límites
- Corre localmente (privacidad total)
- Modelos open source (Llama 3.2)
- Misma calidad para e-commerce LATAM

MODELO USADO: llama3.2:latest
  → 2GB, rápido en Mac M1/M2/M3
  → Excelente para generación de texto en español

FLUJO:
------
1. Usuario llena datos básicos del producto
2. ai_service genera contenido con Ollama
3. Usuario REVISA y EDITA (human in the loop)
4. Usuario confirma → se publica en todas las plataformas
"""

import os
import json
import requests
from typing import Optional


class AIService:
    """
    Servicio de IA para generación de contenido de productos.
    Usa Ollama corriendo localmente en el puerto 11434.
    """

    # URL de Ollama local
    OLLAMA_URL = "http://localhost:11434/api/generate"

    # Modelo a usar
    MODEL = "llama3.2:latest"

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
        Genera contenido optimizado para múltiples plataformas con Ollama.

        Args:
            name:        Nombre base del producto
            description: Descripción corta opcional del usuario
            category:    Categoría del producto
            brand:       Marca del producto
            price:       Precio en MXN
            platforms:   Lista de plataformas ['shopify', 'mercadolibre', 'amazon']

        Returns:
            Dict con contenido optimizado por plataforma
        """
        if platforms is None:
            platforms = ['shopify', 'mercadolibre', 'amazon']

        prompt = self._build_prompt(name, description, category, brand, price, platforms)

        try:
            response = requests.post(
                self.OLLAMA_URL,
                json={
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2000
                    }
                },
                timeout=120  # Ollama puede tardar más que una API externa
            )

            if response.status_code != 200:
                raise ValueError(f"Error de Ollama: {response.status_code} - {response.text}")

            response_text = response.json().get('response', '')
            result = self._parse_response(response_text, platforms)
            return result

        except requests.exceptions.ConnectionError:
            raise ValueError(
                "No se pudo conectar con Ollama. "
                "Asegúrate de que Ollama esté corriendo con: ollama serve"
            )
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
        """

        platforms_section = self._build_platforms_requirements(platforms)
        json_structure = self._build_json_structure(platforms)

        prompt = f"""Eres un experto en e-commerce para LATAM con 10 años de experiencia optimizando listings en Shopify, Mercado Libre y Amazon México. Hablas español de México.

Producto:
- Nombre: {name}
- Descripción base: {description if description else 'No proporcionada'}
- Categoría: {category if category else 'No especificada'}
- Marca: {brand if brand else 'No especificada'}
- Precio: ${price:.2f} MXN

Genera contenido optimizado ÚNICAMENTE para estas plataformas: {', '.join(platforms)}

{platforms_section}

REGLAS IMPORTANTES:
- Usa español de México natural y persuasivo
- Enfócate en beneficios para el comprador
- Si la marca no está especificada, no la inventes
- El título de Mercado Libre DEBE tener máximo 60 caracteres (cuenta exactamente)
- Amazon necesita EXACTAMENTE 5 bullet points, ni más ni menos

RESPONDE ÚNICAMENTE con el siguiente JSON válido, sin texto adicional, sin explicaciones, sin ```json:
{json_structure}"""

        return prompt

    def _build_platforms_requirements(self, platforms: list) -> str:
        """Construye los requisitos específicos de cada plataforma."""

        requirements = []

        if 'shopify' in platforms:
            requirements.append("""
SHOPIFY:
- title: Título atractivo máx 255 chars con marca y modelo
- description_html: Descripción en HTML con <h2>, <ul><li>, <strong>. Mínimo 100 palabras
- tags: Array de 8 tags relevantes en minúsculas
- seo_title: Optimizado para Google, máx 70 chars
- seo_description: Meta description, máx 160 chars""")

        if 'mercadolibre' in platforms:
            requirements.append("""
MERCADO LIBRE (MUY IMPORTANTE):
- title: MÁXIMO 60 CARACTERES incluyendo espacios. Fórmula: [Marca] [Producto] [Característica] [Modelo]
- description: Texto plano SIN HTML. Entre 100-300 palabras
- category_hint: Categoría sugerida en español
- keywords: Array de 5 palabras clave más buscadas""")

        if 'amazon' in platforms:
            requirements.append("""
AMAZON MÉXICO:
- title: Fórmula: [Marca] [Producto] [Característica] [Color/Cantidad]. Máx 200 chars
- bullet_points: Array de EXACTAMENTE 5 strings. Cada uno empieza con TÉRMINO EN MAYÚSCULAS seguido de dos puntos
- description: 200-400 palabras optimizada para SEO
- backend_keywords: Keywords separadas por espacio, sin repetir palabras del título. Máx 200 chars""")

        return '\n'.join(requirements)

    def _build_json_structure(self, platforms: list) -> str:
        """Construye la estructura JSON esperada."""

        parts = []

        if 'shopify' in platforms:
            parts.append('''{
  "shopify": {
    "title": "título aquí",
    "description_html": "<h2>Características</h2><ul><li>punto 1</li></ul>",
    "tags": ["tag1", "tag2", "tag3"],
    "seo_title": "seo title aquí",
    "seo_description": "meta description aquí"
  }''')

        if 'mercadolibre' in platforms:
            parts.append('''{
  "mercadolibre": {
    "title": "título máx 60 chars",
    "description": "descripción texto plano",
    "category_hint": "categoría sugerida",
    "keywords": ["keyword1", "keyword2"]
  }''')

        if 'amazon' in platforms:
            parts.append('''{
  "amazon": {
    "title": "título amazon",
    "bullet_points": ["PUNTO 1: descripción", "PUNTO 2: descripción", "PUNTO 3: descripción", "PUNTO 4: descripción", "PUNTO 5: descripción"],
    "description": "descripción amazon",
    "backend_keywords": "keywords backend"
  }''')

        # Si hay múltiples plataformas, combinarlas en un solo JSON
        if len(platforms) == 1:
            return parts[0]
        else:
            combined = "{\n"
            platform_parts = []
            for platform in platforms:
                if platform == 'shopify':
                    platform_parts.append('''  "shopify": {
    "title": "título shopify",
    "description_html": "<h2>Características</h2><ul><li>punto 1</li></ul>",
    "tags": ["tag1", "tag2"],
    "seo_title": "seo title",
    "seo_description": "meta description"
  }''')
                elif platform == 'mercadolibre':
                    platform_parts.append('''  "mercadolibre": {
    "title": "título máx 60 chars",
    "description": "descripción texto plano sin HTML",
    "category_hint": "Categoría > Subcategoría",
    "keywords": ["keyword1", "keyword2"]
  }''')
                elif platform == 'amazon':
                    platform_parts.append('''  "amazon": {
    "title": "título amazon máx 200 chars",
    "bullet_points": ["COMPATIBILIDAD: descripción", "MATERIAL: descripción", "FUNCIÓN: descripción", "INSTALACIÓN: descripción", "INCLUYE: descripción"],
    "description": "descripción amazon SEO",
    "backend_keywords": "keywords sin repetir"
  }''')

            combined += ',\n'.join(platform_parts)
            combined += '\n}'
            return combined

    # ═══════════════════════════════════════════════════════════
    # PARSEAR RESPUESTA DE OLLAMA
    # ═══════════════════════════════════════════════════════════

    def _parse_response(self, response_text: str, platforms: list) -> dict:
        """
        Parsea la respuesta JSON de Ollama y valida campos críticos.

        Ollama a veces agrega texto antes o después del JSON.
        Buscamos el JSON dentro de la respuesta.
        """
        # Limpiar la respuesta
        clean_text = response_text.strip()

        # Remover backticks si los hay
        if '```json' in clean_text:
            clean_text = clean_text.split('```json')[1].split('```')[0].strip()
        elif '```' in clean_text:
            clean_text = clean_text.split('```')[1].split('```')[0].strip()

        # Buscar el JSON entre llaves
        start = clean_text.find('{')
        end = clean_text.rfind('}')

        if start == -1 or end == -1:
            raise ValueError(f"No se encontró JSON válido en la respuesta: {clean_text[:200]}")

        json_text = clean_text[start:end+1]

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError:
            # Intentar reparar JSON común con Ollama
            try:
                # A veces Ollama pone comillas simples en lugar de dobles
                json_text = json_text.replace("'", '"')
                data = json.loads(json_text)
            except json.JSONDecodeError as e:
                raise ValueError(f"No se pudo parsear el JSON: {e}\nRespuesta: {json_text[:300]}")

        # ─── Validaciones críticas ────────────────────────────

        # ML: título máx 60 chars
        if 'mercadolibre' in data and 'title' in data['mercadolibre']:
            ml_title = data['mercadolibre']['title']
            if len(ml_title) > 60:
                # Truncar en la última palabra completa
                data['mercadolibre']['title'] = ml_title[:60].rsplit(' ', 1)[0]
                data['mercadolibre']['title_truncated'] = True

        # Amazon: exactamente 5 bullet points
        if 'amazon' in data and 'bullet_points' in data['amazon']:
            bullets = data['amazon']['bullet_points']
            if len(bullets) > 5:
                data['amazon']['bullet_points'] = bullets[:5]
            elif len(bullets) < 5:
                while len(data['amazon']['bullet_points']) < 5:
                    data['amazon']['bullet_points'].append(
                        "CALIDAD GARANTIZADA: Producto verificado y de alta calidad."
                    )

        # Metadata
        data['generated_at'] = __import__('datetime').datetime.utcnow().isoformat()
        data['platforms'] = platforms
        data['model'] = self.MODEL

        return data

    # ═══════════════════════════════════════════════════════════
    # MÉTODO: MEJORAR DESCRIPCIÓN EXISTENTE
    # ═══════════════════════════════════════════════════════════

    def improve_description(self, current_description: str, platform: str) -> str:
        """
        Mejora una descripción existente para una plataforma específica.
        """
        platform_rules = {
            'shopify': "en HTML con h2, ul, strong. Mínimo 100 palabras.",
            'mercadolibre': "en texto plano SIN HTML. Entre 100-300 palabras.",
            'amazon': "optimizada para SEO con keywords. 200-400 palabras."
        }

        rules = platform_rules.get(platform, "clara y persuasiva")

        prompt = f"""Eres un experto en e-commerce para LATAM. Mejora esta descripción para {platform.upper()}.

Descripción actual:
{current_description}

Escribe la descripción mejorada {rules}
Usa español de México natural y persuasivo.
Enfócate en beneficios para el comprador.

Responde ÚNICAMENTE con la descripción mejorada, sin explicaciones ni texto adicional."""

        try:
            response = requests.post(
                self.OLLAMA_URL,
                json={
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 1000}
                },
                timeout=60
            )

            if response.status_code != 200:
                raise ValueError(f"Error de Ollama: {response.status_code}")

            return response.json().get('response', '').strip()

        except requests.exceptions.ConnectionError:
            raise ValueError("No se pudo conectar con Ollama. Corre: ollama serve")
        except Exception as e:
            raise ValueError(f"Error al mejorar descripción: {str(e)}")

    # ═══════════════════════════════════════════════════════════
    # VERIFICAR QUE OLLAMA ESTÁ CORRIENDO
    # ═══════════════════════════════════════════════════════════

    def health_check(self) -> tuple:
        """
        Verifica que Ollama está corriendo y el modelo está disponible.

        Returns:
            (success, message)
        """
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = [m['name'] for m in response.json().get('models', [])]
                if self.MODEL in models:
                    return True, f"Ollama corriendo con modelo {self.MODEL}"
                else:
                    return False, f"Modelo {self.MODEL} no encontrado. Modelos disponibles: {models}"
            return False, "Ollama no responde correctamente"
        except requests.exceptions.ConnectionError:
            return False, "Ollama no está corriendo. Ejecuta: ollama serve"


# Instancia global del servicio
ai_service = AIService()
