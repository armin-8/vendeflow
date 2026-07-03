"""
VendeFlow - Servicio de Inteligencia Artificial con Ollama
===========================================================

Usa Ollama (local) para generar contenido optimizado de productos
para cada plataforma de e-commerce. Corre 100% en tu Mac, sin
costos ni dependencias externas.

MODELO USADO: llama3.2:latest
  → 2GB, rápido en Mac M1/M2/M3
  → Excelente para generación de texto en español
"""

import json
import requests


class AIService:
    """
    Servicio de IA para generación de contenido de productos.
    Usa Ollama corriendo localmente en el puerto 11434.
    """

    OLLAMA_URL = "http://localhost:11434/api/generate"
    MODEL = "llama3.2:latest"

    # ═══════════════════════════════════════════════════════════
    # MÉTODO PRINCIPAL: GENERAR LISTING MULTI-PLATAFORMA
    # ═══════════════════════════════════════════════════════════

    def generate_listing(self, name, description='', category='', brand='', price=0.0, platforms=None):
        """
        Genera contenido optimizado para múltiples plataformas con Ollama.
        """
        if platforms is None:
            platforms = ['shopify', 'mercadolibre', 'amazon']

        # ─── MEJORA CLAVE ────────────────────────────────────
        # Pedimos por plataforma de forma independiente para evitar
        # que el JSON quede truncado por límite de tokens.
        # Es más confiable que pedir todo en una sola llamada.
        # ─────────────────────────────────────────────────────
        result = {}

        for platform in platforms:
            try:
                platform_result = self._generate_for_platform(
                    platform, name, description, category, brand, price
                )
                result[platform] = platform_result
            except Exception as e:
                result[platform] = {'error': str(e)}

        import datetime
        result['generated_at'] = datetime.datetime.utcnow().isoformat()
        result['platforms'] = platforms
        result['model'] = self.MODEL

        return result

    def _generate_for_platform(self, platform, name, description, category, brand, price):
        """
        Genera contenido para UNA sola plataforma.

        ¿POR QUÉ UNA PLATAFORMA A LA VEZ?
        ------------------------------------
        Llama 3.2 tiene un límite de contexto. Si pedimos Shopify +
        ML + Amazon juntos, el JSON queda truncado e inválido.
        Al pedir de uno en uno, cada respuesta es corta y completa.
        """
        prompts = {
            'shopify': f"""Eres experto en e-commerce LATAM. Genera contenido para Shopify en español de México.

Producto: {name}
Descripción base: {description or 'No proporcionada'}
Categoría: {category or 'No especificada'}
Marca: {brand or 'No especificada'}
Precio: ${price:.2f} MXN

Genera un JSON con exactamente esta estructura (sin texto adicional, sin explicaciones):
{{
  "title": "título atractivo máximo 255 caracteres",
  "description_html": "<h2>Características</h2><ul><li>característica 1</li><li>característica 2</li><li>característica 3</li></ul><h2>Beneficios</h2><ul><li>beneficio 1</li><li>beneficio 2</li></ul>",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "seo_title": "título SEO máximo 70 caracteres",
  "seo_description": "meta description máximo 160 caracteres"
}}""",

            'mercadolibre': f"""Eres experto en e-commerce LATAM. Genera contenido para Mercado Libre México en español.

Producto: {name}
Descripción base: {description or 'No proporcionada'}
Categoría: {category or 'No especificada'}
Marca: {brand or 'No especificada'}
Precio: ${price:.2f} MXN

IMPORTANTE: El título DEBE tener MÁXIMO 60 caracteres contando espacios.

Genera un JSON con exactamente esta estructura (sin texto adicional, sin explicaciones):
{{
  "title": "título máximo 60 caracteres aquí",
  "description": "descripción en texto plano sin HTML entre 100 y 200 palabras aquí",
  "category_hint": "Categoría sugerida",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
}}""",

            'amazon': f"""Eres experto en e-commerce LATAM. Genera contenido para Amazon México en español.

Producto: {name}
Descripción base: {description or 'No proporcionada'}
Categoría: {category or 'No especificada'}
Marca: {brand or 'No especificada'}
Precio: ${price:.2f} MXN

Genera un JSON con exactamente esta estructura (sin texto adicional, sin explicaciones):
{{
  "title": "título máximo 200 caracteres con marca y modelo",
  "bullet_points": [
    "BENEFICIO 1: descripción del primer beneficio",
    "BENEFICIO 2: descripción del segundo beneficio",
    "BENEFICIO 3: descripción del tercer beneficio",
    "BENEFICIO 4: descripción del cuarto beneficio",
    "BENEFICIO 5: descripción del quinto beneficio"
  ],
  "description": "descripción optimizada para SEO de 200 palabras",
  "backend_keywords": "keywords separadas por espacio sin repetir del título"
}}"""
        }

        prompt = prompts.get(platform)
        if not prompt:
            raise ValueError(f"Plataforma no soportada: {platform}")

        try:
            response = requests.post(
                self.OLLAMA_URL,
                json={
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 1500  # Suficiente para 1 plataforma
                    }
                },
                timeout=120
            )

            if response.status_code != 200:
                raise ValueError(f"Error de Ollama: {response.status_code}")

            response_text = response.json().get('response', '')
            return self._parse_response(response_text, platform)

        except requests.exceptions.ConnectionError:
            raise ValueError("Ollama no está corriendo. Verifica que esté activo.")

    # ═══════════════════════════════════════════════════════════
    # PARSEAR RESPUESTA
    # ═══════════════════════════════════════════════════════════

    def _parse_response(self, response_text, platform):
        """
        Parsea el JSON de Ollama y valida campos críticos.
        """
        clean_text = response_text.strip()

        # Remover backticks si los hay
        if '```json' in clean_text:
            clean_text = clean_text.split('```json')[1].split('```')[0].strip()
        elif '```' in clean_text:
            clean_text = clean_text.split('```')[1].split('```')[0].strip()

        # Buscar JSON entre llaves
        start = clean_text.find('{')
        end = clean_text.rfind('}')

        if start == -1 or end == -1:
            raise ValueError(f"No se encontró JSON en la respuesta de Ollama")

        json_text = clean_text[start:end+1]

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido: {e}\nRespuesta: {json_text[:200]}")

        # ─── Validaciones críticas ────────────────────────────

        # ML: título máx 60 chars
        if platform == 'mercadolibre' and 'title' in data:
            if len(data['title']) > 60:
                data['title'] = data['title'][:60].rsplit(' ', 1)[0]

        # Amazon: exactamente 5 bullet points
        if platform == 'amazon' and 'bullet_points' in data:
            bullets = data['bullet_points']
            if len(bullets) > 5:
                data['bullet_points'] = bullets[:5]
            while len(data['bullet_points']) < 5:
                data['bullet_points'].append("CALIDAD GARANTIZADA: Producto verificado de alta calidad.")

        return data

    # ═══════════════════════════════════════════════════════════
    # MEJORAR DESCRIPCIÓN
    # ═══════════════════════════════════════════════════════════

    def improve_description(self, current_description, platform):
        """
        Mejora una descripción existente para una plataforma específica.
        """
        rules = {
            'shopify': "en HTML con h2, ul, strong. Mínimo 100 palabras.",
            'mercadolibre': "en texto plano SIN HTML. Entre 100-200 palabras.",
            'amazon': "optimizada para SEO. 150-300 palabras."
        }.get(platform, "clara y persuasiva")

        prompt = f"""Mejora esta descripción para {platform.upper()} en español de México.

Descripción actual: {current_description}

Escribe la descripción mejorada {rules}
Responde ÚNICAMENTE con la descripción, sin explicaciones."""

        try:
            response = requests.post(
                self.OLLAMA_URL,
                json={
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 800}
                },
                timeout=60
            )
            return response.json().get('response', '').strip()
        except Exception as e:
            raise ValueError(f"Error al mejorar descripción: {str(e)}")

    # ═══════════════════════════════════════════════════════════
    # HEALTH CHECK
    # ═══════════════════════════════════════════════════════════

    def health_check(self):
        """Verifica que Ollama está corriendo y el modelo disponible."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = [m['name'] for m in response.json().get('models', [])]
                if self.MODEL in models:
                    return True, f"Ollama corriendo con modelo {self.MODEL}"
                return False, f"Modelo {self.MODEL} no encontrado. Disponibles: {models}"
            return False, "Ollama no responde"
        except requests.exceptions.ConnectionError:
            return False, "Ollama no está corriendo"


# Instancia global
ai_service = AIService()
