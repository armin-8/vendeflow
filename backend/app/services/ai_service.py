"""
VendeFlow - Servicio de Inteligencia Artificial con Ollama
===========================================================

Usa Ollama (local) para generar contenido optimizado de productos.

FILOSOFÍA DE LA IA EN VENDEFLOW:
---------------------------------
1. El título es SAGRADO → siempre usa exactamente el nombre del usuario
2. La descripción base es la MATERIA PRIMA → la IA la convierte en
   contenido profesional y atractivo para cada plataforma
3. La IA NO inventa información → solo organiza, mejora y optimiza
   lo que el usuario proporcionó

MODELO: llama3.2:latest (local, gratis, sin dependencias)
"""

import json
import datetime
import requests


class AIService:

    OLLAMA_URL = "http://localhost:11434/api/generate"
    MODEL = "llama3.2:latest"

    # ═══════════════════════════════════════════════════════════
    # MÉTODO PRINCIPAL
    # ═══════════════════════════════════════════════════════════

    def generate_listing(self, name, description='', category='', brand='', price=0.0, platforms=None):
        """
        Genera contenido profesional para múltiples plataformas.

        REGLA DE ORO:
        - El nombre del producto NUNCA se modifica
        - La descripción se transforma en contenido profesional
        - La IA organiza y mejora, nunca inventa
        """
        if platforms is None:
            platforms = ['shopify', 'mercadolibre', 'amazon']

        result = {}
        for platform in platforms:
            try:
                result[platform] = self._generate_for_platform(
                    platform, name, description, category, brand, price
                )
            except Exception as e:
                result[platform] = {'error': str(e)}

        result['generated_at'] = datetime.datetime.utcnow().isoformat()
        result['platforms'] = platforms
        result['model'] = self.MODEL
        return result

    # ═══════════════════════════════════════════════════════════
    # GENERAR POR PLATAFORMA
    # ═══════════════════════════════════════════════════════════

    def _generate_for_platform(self, platform, name, description, category, brand, price):
        """Genera contenido profesional para una plataforma específica."""

        prompts = {

            # ─── SHOPIFY ──────────────────────────────────────
            # El título es EXACTAMENTE el nombre del usuario.
            # La descripción se convierte en HTML profesional y atractivo.
            # ─────────────────────────────────────────────────
            'shopify': f"""Eres un copywriter experto en e-commerce para LATAM con 10 años de experiencia.
Tu misión: convertir información técnica en descripciones irresistibles que convencen al comprador.

PRODUCTO:
Nombre: {name}
Información del producto: {description or 'No proporcionada'}
Categoría: {category or 'No especificada'}
Marca: {brand or 'No especificada'}
Precio: ${price:.2f} MXN

INSTRUCCIONES:
1. El campo "title" debe ser EXACTAMENTE: "{name}" (no lo cambies, no lo modifiques)
2. Crea una descripción HTML profesional y atractiva basada en la información del producto
3. La descripción debe convencer al comprador destacando beneficios reales
4. Usa solo información que esté en la descripción proporcionada, no inventes
5. Estructura: introducción atractiva, características clave, beneficios para el usuario

Genera ÚNICAMENTE este JSON (sin texto adicional, sin explicaciones, sin ```):
{{
  "title": "{name}",
  "description_html": "<h2>Descripción atractiva aquí</h2><p>Párrafo introductorio convincente</p><h2>Características Principales</h2><ul><li><strong>Característica 1:</strong> descripción</li><li><strong>Característica 2:</strong> descripción</li></ul><h2>¿Por qué elegirlo?</h2><ul><li>Beneficio 1 orientado al comprador</li><li>Beneficio 2 orientado al comprador</li></ul>",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
  "seo_title": "título SEO máximo 70 caracteres con keywords principales",
  "seo_description": "meta description atractiva máximo 160 caracteres que invita al clic"
}}""",

            # ─── MERCADO LIBRE ────────────────────────────────
            # Título MÁXIMO 60 chars con keywords al inicio.
            # Descripción en texto plano, directa y persuasiva.
            # ─────────────────────────────────────────────────
            'mercadolibre': f"""Eres experto en Mercado Libre México con 10 años optimizando listings.
Conoces el algoritmo de búsqueda de ML y cómo posicionar productos.

PRODUCTO:
Nombre base: {name}
Información: {description or 'No proporcionada'}
Categoría: {category or 'No especificada'}
Marca: {brand or 'No especificada'}
Precio: ${price:.2f} MXN

INSTRUCCIONES:
1. El título DEBE tener MÁXIMO 60 CARACTERES (cuenta cada espacio y letra)
2. Pon las palabras más buscadas AL INICIO del título
3. La descripción debe ser texto plano SIN HTML, persuasiva y clara
4. Usa solo información real del producto, no inventes especificaciones
5. Los keywords deben ser los términos que los compradores buscan en ML

Genera ÚNICAMENTE este JSON (sin texto adicional, sin explicaciones, sin ```):
{{
  "title": "título exactamente máximo 60 chars aquí",
  "description": "descripción profesional en texto plano entre 150 y 300 palabras que convence al comprador sin usar HTML",
  "category_hint": "Categoría > Subcategoría sugerida",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
}}""",

            # ─── AMAZON ───────────────────────────────────────
            # Título con fórmula Amazon.
            # 5 bullet points que convierten visitas en ventas.
            # ─────────────────────────────────────────────────
            'amazon': f"""Eres experto en Amazon México con 10 años optimizando listings para el algoritmo A9/A10.
Sabes exactamente cómo escribir bullet points que convierten visitas en ventas.

PRODUCTO:
Nombre: {name}
Información: {description or 'No proporcionada'}
Categoría: {category or 'No especificada'}
Marca: {brand or 'No especificada'}
Precio: ${price:.2f} MXN

INSTRUCCIONES:
1. El título debe seguir la fórmula Amazon: [Marca] [Producto] [Característica principal] [Modelo]
2. Los 5 bullet points deben empezar con TÉRMINO EN MAYÚSCULAS seguido de dos puntos
3. Cada bullet debe enfocarse en UN beneficio específico para el comprador
4. La descripción debe incluir keywords naturalmente para SEO
5. Los backend_keywords no deben repetir palabras ya usadas en el título

Genera ÚNICAMENTE este JSON (sin texto adicional, sin explicaciones, sin ```):
{{
  "title": "título Amazon máximo 200 chars con marca modelo y característica principal",
  "bullet_points": [
    "CARACTERÍSTICA PRINCIPAL: descripción del beneficio más importante para el comprador",
    "TECNOLOGÍA/MATERIAL: descripción de la tecnología o material y su beneficio",
    "COMPATIBILIDAD/USO: para quién es ideal y en qué situaciones",
    "GARANTÍA/CALIDAD: respaldo de calidad y confianza",
    "INCLUYE/CONTENIDO: qué viene en el paquete o qué valor adicional ofrece"
  ],
  "description": "descripción SEO de 200-400 palabras con keywords integradas naturalmente",
  "backend_keywords": "keywords adicionales separadas por espacio sin repetir del título máximo 200 chars"
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
                        "num_predict": 2000
                    }
                },
                timeout=180
            )

            if response.status_code != 200:
                raise ValueError(f"Error de Ollama: {response.status_code}")

            response_text = response.json().get('response', '')
            result = self._parse_response(response_text, platform)

            # ─── GARANTIZAR TÍTULO EXACTO EN SHOPIFY ──────────
            # Por seguridad, aunque el prompt lo dice, forzamos
            # el título exacto del usuario en el resultado final.
            if platform == 'shopify':
                result['title'] = name

            return result

        except requests.exceptions.ConnectionError:
            raise ValueError("Ollama no está corriendo. Verifica que esté activo.")

    # ═══════════════════════════════════════════════════════════
    # PARSEAR RESPUESTA
    # ═══════════════════════════════════════════════════════════

    def _parse_response(self, response_text, platform):
        """Parsea el JSON de Ollama y valida campos críticos."""
        clean_text = response_text.strip()

        # Limpiar backticks
        if '```json' in clean_text:
            clean_text = clean_text.split('```json')[1].split('```')[0].strip()
        elif '```' in clean_text:
            clean_text = clean_text.split('```')[1].split('```')[0].strip()

        # Extraer JSON
        start = clean_text.find('{')
        end = clean_text.rfind('}')
        if start == -1 or end == -1:
            raise ValueError("No se encontró JSON en la respuesta de Ollama")

        json_text = clean_text[start:end+1]

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido: {e}\nRespuesta: {json_text[:200]}")

        # ─── Validaciones críticas ────────────────────────────

        # ML: título máx 60 chars — crítico para que no se corte
        if platform == 'mercadolibre' and 'title' in data:
            if len(data['title']) > 60:
                data['title'] = data['title'][:60].rsplit(' ', 1)[0]

        # Amazon: exactamente 5 bullet points
        if platform == 'amazon' and 'bullet_points' in data:
            bullets = data['bullet_points']
            if len(bullets) > 5:
                data['bullet_points'] = bullets[:5]
            while len(data['bullet_points']) < 5:
                data['bullet_points'].append(
                    "CALIDAD GARANTIZADA: Producto verificado y de alta calidad para tu satisfacción."
                )

        return data

    # ═══════════════════════════════════════════════════════════
    # MEJORAR DESCRIPCIÓN EXISTENTE
    # ═══════════════════════════════════════════════════════════

    def improve_description(self, current_description, platform):
        """Convierte una descripción técnica en contenido profesional."""
        rules = {
            'shopify': "en HTML con h2, p, ul, strong. Mínima 150 palabras. Profesional y atractiva.",
            'mercadolibre': "en texto plano SIN HTML. Entre 150-300 palabras. Clara y persuasiva.",
            'amazon': "optimizada para SEO con keywords. 200-400 palabras."
        }.get(platform, "clara, profesional y persuasiva")

        prompt = f"""Eres un copywriter experto en e-commerce LATAM.
Convierte esta información en una descripción profesional y atractiva para {platform.upper()}.

Información del producto:
{current_description}

REGLAS:
- Escribe {rules}
- Usa español de México natural y persuasivo
- Enfócate en beneficios para el comprador
- No inventes información que no esté en el texto original
- Hazla irresistible para el comprador

Responde ÚNICAMENTE con la descripción mejorada, sin explicaciones ni texto adicional."""

        try:
            response = requests.post(
                self.OLLAMA_URL,
                json={
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 1500}
                },
                timeout=120
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
