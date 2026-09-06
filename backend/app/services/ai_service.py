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

    # Máximo de caracteres de descripción que aceptamos como entrada.
    #
    # Antes eran 800 y era demasiado agresivo: si el usuario escribía varios
    # párrafos, todo lo que pasaba del carácter 800 se tiraba ANTES de llamar al
    # modelo, así que la descripción "se encogía" sin que nada lo avisara.
    # Llama 3.2 tiene 128k de contexto — el cuello de botella nunca fue ese.
    MAX_DESCRIPTION_CHARS = 4000

    # Ventana de contexto explícita. Sin esto queda a merced del default de
    # Ollama, que cambia entre versiones y podría recortar prompts largos en
    # silencio.
    NUM_CTX = 8192

    # Tokens de salida por plataforma. Shopify necesita muchos más: genera HTML
    # (las etiquetas consumen tokens) y es la descripción larga de verdad.
    NUM_PREDICT = {
        'shopify': 3000,
        'mercadolibre': 1200,
        'amazon': 1500,
    }

    # ═══════════════════════════════════════════════════════════
    # ESQUEMAS DE SALIDA (structured outputs de Ollama)
    # ═══════════════════════════════════════════════════════════
    #
    # ¿POR QUÉ UN ESQUEMA Y NO SOLO format:"json"?
    # ---------------------------------------------
    # format:"json" garantiza que la salida sea JSON *sintácticamente* válido,
    # pero NO que traiga todos los campos. Al pedir descripciones largas, el
    # modelo se gastaba en `description_html` y cerraba el objeto antes de
    # escribir `seo_title`, `seo_description` y `tags` — JSON perfectamente
    # válido, pero incompleto.
    #
    # Pasando el esquema, Ollama restringe la decodificación campo por campo y
    # los `required` dejan de ser opcionales. No los quites.

    SCHEMAS = {
        'shopify': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'description_html': {'type': 'string'},
                'tags': {'type': 'array', 'items': {'type': 'string'}},
                'seo_title': {'type': 'string'},
                'seo_description': {'type': 'string'},
            },
            'required': ['title', 'description_html', 'tags', 'seo_title', 'seo_description'],
        },
        'mercadolibre': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'description': {'type': 'string'},
                'category_hint': {'type': 'string'},
                'keywords': {'type': 'array', 'items': {'type': 'string'}},
            },
            'required': ['title', 'description', 'category_hint', 'keywords'],
        },
        'amazon': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'bullet_points': {'type': 'array', 'items': {'type': 'string'}},
                'description': {'type': 'string'},
                'backend_keywords': {'type': 'string'},
            },
            'required': ['title', 'bullet_points', 'description', 'backend_keywords'],
        },
    }

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
- USA TODA la información de "Info". No resumas, no omitas datos, no acortes.
  Cada dato que el usuario escribió debe aparecer en la descripción.
- Desarrolla cada punto en oraciones completas y persuasivas. Una descripción
  RICA Y LARGA vende más que una corta.
- Genera TODAS las características que se desprendan de la info (no te limites
  a dos) y al menos 4 beneficios para el comprador.
- La intro debe ser de 2 a 3 párrafos, no una línea.
- NO inventes características que no estén en la info. Organiza, desarrolla y
  redacta lo que el usuario te dio — pero no agregues datos nuevos.

FORMATO OBLIGATORIO DEL seo_title:
  Nombre | Descriptor con palabra clave + Gancho
  Ejemplo de la ESTRUCTURA (no copies su contenido, es otro producto):
    Mochila Trekking 40L | Mochila Impermeable Senderismo + Funda Incluida
  - Empieza con el nombre del producto, tal cual.
  - Después de la barra va el descriptor: qué ES el producto y su característica
    más buscada (la palabra clave por la que alguien lo buscaría en Google).
  - Después del signo mas va un gancho corto: accesorio incluido, garantía o
    envío. SOLO si aparece en la info de ESTE producto. Si la info no menciona
    nada que ofrecer, OMITE el gancho y usa ese espacio en el descriptor.
  - Usa entre 60 y 70 caracteres. NUNCA lo dejes en 20 o 30 — desperdicias
    espacio que Google sí muestra.

EL seo_description ES TEXTO DE VENTA, no una explicación:
  - Le hablas al COMPRADOR sobre el producto. Menciona el producto, 2 beneficios
    concretos y cierra invitando a comprar.
  - NUNCA empieces con "Meta descripción", "Descripción SEO", "Descripción para
    la página" ni nada que hable del campo mismo. Escribe la descripción, no
    escribas SOBRE la descripción.
  - Máximo 160 caracteres.

NUNCA uses el carácter de comilla doble dentro de ningún valor de texto: rompe
el JSON y el campo se corta ahí mismo. Para medidas en pulgadas escribe
"1 pulgada" o "1 pulg", jamás el símbolo.

Responde SOLO con este JSON válido (sin texto extra, sin ```, sin explicaciones).
El ejemplo muestra la ESTRUCTURA; tu contenido debe ser mucho más extenso:
{{"title":"{name}","description_html":"<h2>Descripción</h2><p>Primer párrafo largo que presenta el producto y su propósito.</p><p>Segundo párrafo que profundiza en el uso y el contexto.</p><h2>Características</h2><ul><li><strong>Característica:</strong> explicación desarrollada en una o dos oraciones</li><li><strong>Otra característica:</strong> explicación desarrollada</li><li><strong>Y así con TODAS las que haya en la info</strong></li></ul><h2>Beneficios</h2><ul><li>Beneficio explicado desde lo que gana el comprador</li><li>Otro beneficio desarrollado</li><li>Tercer beneficio</li><li>Cuarto beneficio</li></ul><h2>Ideal para</h2><p>Párrafo sobre para quién es este producto.</p>","tags":["tag1","tag2","tag3","tag4","tag5"],"seo_title":"{name} | Descriptor con la palabra clave + Gancho si la info lo respalda","seo_description":"Descubre la Mochila Trekking 40L: impermeable, ligera y con funda de lluvia incluida. Ideal para senderismo. Envio a todo Mexico."}}""",

            'mercadolibre': f"""Eres experto en Mercado Libre México. Genera contenido optimizado en español.

Producto: {name}
Info: {description or 'No proporcionada'}
Categoría: {category or 'General'}
Marca: {brand or 'Sin marca'}
Precio: ${price:.2f} MXN

REGLAS ESTRICTAS:
- El title DEBE tener MÁXIMO 60 CARACTERES exactos incluyendo espacios
- El title se escribe como lo pide Mercado Libre:
      Producto + Marca + Modelo + la característica más buscada
  NADA de eslóganes ni frases publicitarias. Nada de dos puntos ni guiones
  para meter una frase bonita. Cada palabra debe ser una que el comprador
  escribiría en el buscador.
  MAL:  Mochila Trekking: la aventura empieza aqui
  BIEN: Mochila Trekking 40L Impermeable Senderismo
- La description debe ser texto plano SIN HTML
- La description usa TODA la info: características, lo que incluye, garantía
  y envío. Desarrolla en varias oraciones, no la resumas a dos líneas.
- NO inventes datos que no estén en la info.

Responde SOLO con este JSON válido (sin texto extra, sin ```, sin explicaciones).
El ejemplo es de OTRO producto: copia la estructura, nunca su contenido.
{{"title":"Mochila Trekking 40L Impermeable Senderismo Funda Lluvia","description":"Mochila de trekking de 40 litros fabricada en poliester impermeable, pensada para rutas de varios dias. Su sistema de ventilacion en la espalda reduce el sudor y el cinturon lumbar reparte el peso para que puedas caminar horas sin cansarte. Incluye funda de lluvia y bolsillos laterales para botellas. Envio a todo Mexico.","category_hint":"Deportes y Fitness","keywords":["mochila trekking","mochila impermeable","senderismo","40 litros","funda de lluvia"]}}""",

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
                    # Decodificación restringida por esquema: garantiza JSON válido
                    # Y que vengan todos los campos requeridos (ver SCHEMAS).
                    "format": self.SCHEMAS.get(platform, 'json'),
                    "options": {
                        "temperature": 0.3,   # Más determinista → JSON más consistente
                        "num_ctx": self.NUM_CTX,
                        "num_predict": self.NUM_PREDICT.get(platform, 1500)
                    }
                },
                timeout=180
            )

            if response.status_code != 200:
                raise ValueError(f"Error de Ollama: {response.status_code}")

            response_text = response.json().get('response', '')
            result = self._parse_response(response_text, platform)

            # Garantizar título exacto en Shopify y dejar el seo_title presentable
            if platform == 'shopify':
                result['title'] = name
                result['seo_title'] = self._ajustar_seo_title(
                    result.get('seo_title', ''), description
                )
                result['seo_description'] = self._ajustar_seo_description(
                    result.get('seo_description', ''), name, description
                )

            return result

        except requests.exceptions.ConnectionError:
            raise ValueError("Ollama no está corriendo.")

    # Palabras que no pueden quedar al final de un título: si el recorte las deja
    # colgando, el título se lee partido ("...sensor de 1 pulgada y").
    CONECTORES = {
        'y', 'o', 'de', 'del', 'con', 'sin', 'para', 'por', 'a', 'al', 'el', 'la',
        'los', 'las', 'un', 'una', 'unos', 'unas', 'en', 'que', 'su', 'sus', 'más',
    }

    def _ajustar_seo_title(self, titulo: str, descripcion: str, limite: int = 70) -> str:
        """
        Deja el seo_title presentable y honesto.

        Hace tres cosas que el modelo no hace confiable por sí solo:

        1. Recorta a `limite` sin partir palabras.
        2. Si el recorte mutiló el gancho ("... + Acceso"), quita el gancho entero
           en vez de dejar un fragmento sin sentido.
        3. Verifica que el gancho tenga respaldo en la descripción del usuario. Si
           el modelo lo inventó (un "+ Accesorio" que nadie mencionó), lo elimina —
           la IA organiza la información del usuario, no la inventa.
        """
        titulo = ' '.join((titulo or '').split())
        if not titulo:
            return titulo

        # ─── 3. El gancho debe estar respaldado por la descripción ──────
        if '+' in titulo:
            base, _, gancho = titulo.partition('+')
            fuente = self._normalizar(descripcion)
            respaldado = any(
                len(palabra) > 3 and palabra in fuente
                for palabra in self._normalizar(gancho).split()
            )
            if not respaldado:
                titulo = base.strip()

        # ─── 1. Recortar sin partir palabras ────────────────────────────
        if len(titulo) > limite:
            recorte = titulo[:limite]
            if ' ' in recorte:
                recorte = recorte.rsplit(' ', 1)[0]

            # ─── 2. ¿El corte mutiló el gancho? Entonces fuera el gancho ──
            if '+' in recorte and '+' in titulo:
                gancho_completo = titulo.partition('+')[2].strip()
                gancho_cortado = recorte.partition('+')[2].strip()
                if gancho_cortado != gancho_completo:
                    recorte = recorte.partition('+')[0]

            titulo = recorte

        return self._podar_final(titulo)

    # Arranques con los que el modelo habla DE la meta descripción en vez de
    # escribirla ("Meta descripción para la página de producto de la GoPro...").
    PREFIJOS_META = (
        'meta descripcion', 'metadescripcion', 'meta description',
        'descripcion meta', 'descripcion seo', 'seo description',
        'descripcion para la pagina', 'descripcion de la pagina',
        'esta es la descripcion', 'la descripcion de',
        'descripcion del producto para',
    )

    def _ajustar_seo_description(self, texto: str, name: str,
                                 descripcion: str, limite: int = 160) -> str:
        """
        Garantiza que la meta descripción sea texto de venta y quepa en Google.

        Si el modelo se puso a describir el campo en vez de llenarlo, se descarta
        y se arma una desde la descripción que escribió el usuario — su texto es
        mejor que una explicación inútil.
        """
        texto = ' '.join((texto or '').split())

        if not texto or self._normalizar(texto).startswith(self.PREFIJOS_META):
            texto = self._meta_de_respaldo(name, descripcion)

        return self._recortar(texto, limite)

    def _meta_de_respaldo(self, name: str, descripcion: str) -> str:
        """Arma una meta descripción con el material del usuario."""
        limpia = ' '.join((descripcion or '').split())
        if not limpia:
            return f"{name}. Disponible ahora."
        return f"{name}: {limpia}"

    def _recortar(self, texto: str, limite: int) -> str:
        """Recorta sin partir palabras ni frases."""
        if len(texto) <= limite:
            return texto
        recorte = texto[:limite]
        if ' ' in recorte:
            recorte = recorte.rsplit(' ', 1)[0]
        return self._podar_final(recorte).rstrip(' ,;:-') + '.'

    def _podar_final(self, texto: str) -> str:
        """
        Quita del final lo que quede colgando tras un recorte: conectores
        ("...sensor de 1 pulgada y"), números huérfanos ("...vidrio termico 1.5")
        y separadores sueltos. Un texto cortado en conector se lee partido.
        """
        palabras = texto.split()
        while palabras:
            ultima = palabras[-1].lower().strip('|+-,.;:')
            es_numero = ultima.replace('.', '').replace(',', '').isdigit()
            if ultima in self.CONECTORES or ultima == '' or es_numero:
                palabras.pop()
            else:
                break
        return ' '.join(palabras).rstrip(' |+-,')

    @staticmethod
    def _normalizar(texto: str) -> str:
        """Minúsculas y sin acentos, para comparar palabras de forma laxa."""
        import unicodedata
        sin_acentos = unicodedata.normalize('NFD', (texto or '').lower())
        return ''.join(c for c in sin_acentos if unicodedata.category(c) != 'Mn')

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

        # Red de seguridad: el esquema ya obliga a que vengan todos los campos,
        # pero si alguno faltara devolvemos un vacío del tipo correcto en vez de
        # una clave ausente que tronaría en el frontend.
        esquema = self.SCHEMAS.get(platform)
        if esquema:
            for campo in esquema['required']:
                if data.get(campo) is None:
                    tipo = esquema['properties'][campo]['type']
                    data[campo] = [] if tipo == 'array' else ''

        # Shopify: recortar los campos SEO a lo que Google alcanza a mostrar.
        # El prompt ya pide los límites, pero el modelo se pasa seguido.
        # (seo_title y seo_description se ajustan en _generate_for_platform,
        #  donde sí tenemos el nombre y la descripción original del usuario)

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

Info: {(current_description or '')[:self.MAX_DESCRIPTION_CHARS]}

Escribe descripción {rules} en español de México. Usa TODA la información: no
resumas ni omitas datos. Solo la descripción, sin explicaciones."""

        try:
            response = requests.post(
                self.OLLAMA_URL,
                json={
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.5,
                        "num_ctx": self.NUM_CTX,
                        "num_predict": 2000
                    }
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
