"""
VendeFlow - Servicio de Inteligencia Artificial con Ollama
===========================================================

FILOSOFÍA:
1. El título es SAGRADO → siempre usa exactamente el nombre del usuario
2. La descripción base es la MATERIA PRIMA → la IA la convierte en
   contenido profesional. Se limita a 800 chars para que Llama 3.2
   pueda generar JSON válido sin cortarse.
3. La IA NO inventa información → solo organiza, mejora y optimiza

MODELO: llama3.2:latest (local, gratis, sin dependencias)
"""

import json
import datetime
import requests


class AIService:

    OLLAMA_URL = "http://localhost:11434/api/generate"
    MODEL = "llama3.2:latest"

    # Máximo de caracteres de descripción que Llama 3.2 puede procesar
    # y aún así generar JSON válido completo
    MAX_DESCRIPTION_CHARS = 800

    def generate_listing(self, name, description='', category='', brand='', price=0.0, platforms=None):
        if platforms is None:
            platforms = ['shopify', 'mercadolibre', 'amazon']

        # Truncar descripción para que Llama pueda procesarla
        desc_truncated = (description or '')[:self.MAX_DESCRIPTION_CHARS]

        result = {}
        for platform in platforms:
            try:
                result[platform] = self._generate_for_platform(
                    platform, name, desc_truncated, category, brand, price
                )
            except Exception as e:
                result[platform] = {'error': str(e)}

        result['generated_at'] = datetime.datetime.utcnow().isoformat()
        result['platforms'] = platforms
        result['model'] = self.MODEL
        return result

    def _generate_for_platform(self, platform, name, description, category, brand, price):
        """Genera contenido profesional para una plataforma específica."""

        prompts = {
            'shopify': f"""Eres copywriter experto en e-commerce LATAM. Genera contenido para Shopify en español de México.

Producto: {name}
Info: {description or 'No proporcionada'}
Categoría: {category or 'General'}
Marca: {brand or 'Sin marca'}
Precio: ${price:.2f} MXN

REGLAS ESTRICTAS:
- El title DEBE ser EXACTAMENTE: "{name}"
- Crea descripción HTML atractiva basada SOLO en la info proporcionada
- No inventes características que no estén en la info

Responde SOLO con este JSON válido (sin texto extra, sin ```, sin explicaciones):
{{"title":"{name}","description_html":"<h2>Descripción</h2><p>Intro atractiva del producto.</p><h2>Características</h2><ul><li><strong>Característica 1:</strong> detalle</li><li><strong>Característica 2:</strong> detalle</li></ul><h2>Beneficios</h2><ul><li>Beneficio para el comprador 1</li><li>Beneficio para el comprador 2</li></ul>","tags":["tag1","tag2","tag3","tag4","tag5"],"seo_title":"título SEO max 70 chars","seo_description":"meta description max 160 chars"}}""",

            'mercadolibre': f"""Eres experto en Mercado Libre México. Genera contenido optimizado en español.

Producto: {name}
Info: {description or 'No proporcionada'}
Categoría: {category or 'General'}
Marca: {brand or 'Sin marca'}
Precio: ${price:.2f} MXN

REGLAS ESTRICTAS:
- El title DEBE tener MÁXIMO 60 CARACTERES exactos incluyendo espacios
- La description debe ser texto plano SIN HTML

Responde SOLO con este JSON válido (sin texto extra, sin ```, sin explicaciones):
{{"title":"título max 60 chars","description":"descripción texto plano 100-200 palabras sin HTML","category_hint":"Categoría sugerida","keywords":["kw1","kw2","kw3","kw4","kw5"]}}""",

            'amazon': f"""Eres experto en Amazon México. Genera contenido para el algoritmo A9/A10 en español.

Producto: {name}
Info: {description or 'No proporcionada'}
Categoría: {category or 'General'}
Marca: {brand or 'Sin marca'}
Precio: ${price:.2f} MXN

REGLAS ESTRICTAS:
- Genera EXACTAMENTE 5 bullet points, ni más ni menos
- Cada bullet empieza con TÉRMINO EN MAYÚSCULAS seguido de dos puntos

Responde SOLO con este JSON válido (sin texto extra, sin ```, sin explicaciones):
{{"title":"título Amazon max 200 chars","bullet_points":["PUNTO 1: beneficio","PUNTO 2: beneficio","PUNTO 3: beneficio","PUNTO 4: beneficio","PUNTO 5: beneficio"],"description":"descripción SEO 200 palabras","backend_keywords":"keywords sin repetir del título"}}"""
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
                        "temperature": 0.3,   # Más determinista → JSON más consistente
                        "num_predict": 1500
                    }
                },
                timeout=180
            )

            if response.status_code != 200:
                raise ValueError(f"Error de Ollama: {response.status_code}")

            response_text = response.json().get('response', '')
            result = self._parse_response(response_text, platform)

            # Garantizar título exacto en Shopify
            if platform == 'shopify':
                result['title'] = name

            return result

        except requests.exceptions.ConnectionError:
            raise ValueError("Ollama no está corriendo.")

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
            raise ValueError(f"JSON inválido: {e}\nRespuesta: {json_text[:300]}")

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
                data['bullet_points'].append(
                    "CALIDAD GARANTIZADA: Producto verificado de alta calidad."
                )

        return data

    def improve_description(self, current_description, platform):
        """Convierte descripción técnica en contenido profesional."""
        rules = {
            'shopify': "en HTML con h2, ul, strong. Profesional y atractiva.",
            'mercadolibre': "en texto plano SIN HTML. Clara y persuasiva.",
            'amazon': "optimizada para SEO. 200-300 palabras."
        }.get(platform, "clara y persuasiva")

        prompt = f"""Copywriter experto e-commerce LATAM. Mejora para {platform.upper()}.

Info: {current_description[:500]}

Escribe descripción {rules} en español de México. Solo la descripción, sin explicaciones."""

        try:
            response = requests.post(
                self.OLLAMA_URL,
                json={
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.5, "num_predict": 1000}
                },
                timeout=120
            )
            return response.json().get('response', '').strip()
        except Exception as e:
            raise ValueError(f"Error: {str(e)}")

    def health_check(self):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = [m['name'] for m in response.json().get('models', [])]
                if self.MODEL in models:
                    return True, f"Ollama corriendo con {self.MODEL}"
                return False, f"Modelo no encontrado. Disponibles: {models}"
            return False, "Ollama no responde"
        except requests.exceptions.ConnectionError:
            return False, "Ollama no está corriendo"


ai_service = AIService()
