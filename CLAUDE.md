# VendeFlow — contexto para Claude

Hub de e-commerce: VendeFlow es el **inventario canónico** y sincroniza en ambas
direcciones con Shopify y Mercado Libre. Una capa de IA local genera los listings.

```
Excel/CSV ─┐
Shopify ───┼──► VendeFlow (fuente de verdad) ──► Shopify / ML
ML ────────┘         ▲
                     └── Llama 3.2 (Ollama local) genera contenido
```

Todo el producto está en español de México (código, comentarios, mensajes de API
y UI). Escribe en español.

Estado, roadmap y setup detallado viven en `README.md` — no los dupliques aquí.

---

## Para quién construimos (esto decide los tradeoffs)

El cliente es el **emprendedor que está arrancando y no tiene nada montado**: ni
catálogo, ni ERP, ni proceso, ni conocimientos técnicos. No es el e-commerce manager
de una empresa con 500 SKUs — ese era el ICP anterior y ya no aplica.

Él pone las decisiones (qué vender, a qué precio, con qué estrategia). Nosotros
ponemos la base de datos y toda la operación.

**La promesa es "un clic hace muchas cosas."** Un producto capturado una vez debe
salir publicado y sincronizado en todos los canales sin trabajo adicional.

### Filtro para resolver disyuntivas

Cuando haya que elegir entre dos caminos, gana el que:

1. **Le quite trabajo operativo al usuario**, aunque nos cueste más código. Si una
   decisión se puede inferir, se infiere; no se le pregunta.
2. **No exija que entienda nada técnico.** Nada de OAuth, API keys, webhooks o SKUs
   bien formados como requisito para avanzar. Si un concepto técnico tiene que
   asomarse a la UI, es un bug de diseño.
3. **Acerque a VendeFlow a ser su fuente de verdad.** Somos su sistema de registro
   desde el primer producto; nada debe empujarlo a administrar catálogo en el admin
   de Shopify o de ML.
4. **Funcione con cero configuración previa.** El usuario llega sin catálogo: los
   defaults tienen que ser buenos, no vacíos.

Corolario: **valores por defecto sensatos > pantallas de configuración**, y
**un flujo que hace todo > varios flujos que hacen cada cosa.**

---

## Reglas de arquitectura

El backend tiene 4 capas y el límite entre ellas **no es negociable**:

| Capa | Hace | NO hace |
|---|---|---|
| `routes/` | HTTP, validación Pydantic, autorización JWT | Nunca llama APIs externas ni arma requests |
| `services/` | Lógica de negocio y **todas** las llamadas salientes (Shopify, ML, Ollama) | No conoce `request` ni `jsonify` |
| `models/` | Persistencia + lógica de dominio (`is_low_stock`, `profit_margin`) | — |
| `schemas/` | Contratos de entrada con Pydantic v2 | — |

Si una ruta necesita hablar con una plataforma, el método va en el service.

**Multi-tenancy:** cada query filtra por `user_id` sacado de `get_jwt_identity()`.
Nunca consultes `Product` o `PlatformConnection` sin ese filtro — es lo único que
separa los datos entre usuarios.

### Contrato de los servicios de plataforma

`shopify_service.py` y `mercadolibre_service.py` implementan la misma forma. Si
agregas Amazon (SP-API), **síguela**: es lo que hace que las rutas sean casi
idénticas entre plataformas.

```
get_auth_url(state) → exchange_code_for_token(code) → test_connection(token)
get_products() / get_user_items()  →  normalize_*()  →  dict con forma de Product
update_inventory() / update_stock()  ←  sync de vuelta
```

`normalize_*()` es la pieza clave: traduce el formato de la plataforma al de
`Product` (sku, name, price, quantity, image_url, `<plataforma>_id`).

Los servicios devuelven **tuplas `(resultado, error)`** en vez de lanzar
excepciones. Respeta ese estilo.

---

## Gotchas — cosas que muerden

**Tokens cifrados de forma transparente.** `PlatformConnection._access_token` y
`._refresh_token` guardan Fernet en la BD; las `@property` `access_token` /
`refresh_token` cifran y descifran solas. **Nunca leas ni escribas los campos con
guion bajo** — te llevas texto cifrado o rompes el cifrado en reposo. Necesita
`ENCRYPTION_KEY` en el `.env`.

**Los tokens de Mercado Libre expiran en 6 horas.** Jamás uses
`connection.access_token` directo para llamar a ML: pasa siempre por
`mercadolibre_service.get_valid_token(connection)`, que refresca solo con 5 min de
margen. Shopify no expira, por eso ahí sí se usa directo.

**El `state` de OAuth va firmado** (`app/utils/oauth_state.py`, itsdangerous +
`SECRET_KEY`, caduca a los 10 min, salt por plataforma). Transporta el `user_id`.
Si tocas un callback, no vuelvas a parsear el state a mano — usa
`verify_state()`. El callback de Shopify además valida el HMAC sobre la query
string **cruda** (`request.query_string`), no sobre `request.args`: re-codificar
rompe la firma en requests legítimos.

**El frontend habla cross-origin.** `VITE_API_URL` apunta directo a
`localhost:5001`, saltándose el proxy de Vite, y `fetch` no manda credenciales →
**las cookies no viajan**. La autenticación es JWT en `localStorage`
(`vendeflow-auth`, escrito por el middleware `persist` de Zustand). No metas nada
que dependa de cookies o de la sesión de Flask; por eso `/api/import/confirm`
recibe los productos en el body en vez de guardarlos en sesión.

**Ollama corre local en `localhost:11434`** con `llama3.2:latest`. Si no está
arriba, `/api/ai/*` falla — no es un bug del código. Timeout de 180s.

**Mercado Libre no acepta `localhost`** como redirect URI. En desarrollo hay que
levantar ngrok y poner esa URL en `MERCADOLIBRE_REDIRECT_URI`.

**Publicar en ML son tres llamadas, no una.** `POST /items` crea la publicación,
`POST /items/{id}/description` le pone la descripción (es un recurso aparte y solo
acepta texto plano — por eso el prompt de ML prohíbe HTML) y `PUT /items/{id}` la
pausa. Si falla la descripción **no** se tira la publicación: ya existe, se reporta
en `description_ok` y la UI avisa.

**La categoría de ML no se le pregunta al usuario.** ML exige un `category_id` de un
árbol de miles de nodos; `predict_category()` lo deduce del título con el mismo
predictor que usa ML en su formulario. Por eso el título de ML importa el doble: es
contenido Y es la entrada del predictor. Si el título sale con eslogan, la categoría
sale mal.

**Los errores de ML vienen en `cause`, no en `message`.** Sin desdoblar ese arreglo
(`_mensaje_de_error()`) el usuario solo ve "Bad Request" y no se entera de que le
faltó un atributo obligatorio de la categoría.

---

## Prohibiciones

- **Nunca `db.create_all()`** en código de aplicación. El esquema lo maneja
  Flask-Migrate; `create_all()` crea tablas por su cuenta y deja las migraciones
  fuera de sincronía. (Los tests sí lo usan, en `conftest.py`, contra una BD
  desechable — eso está bien.)
- **Nunca publiques productos activos.** En Shopify siempre `status: draft`; en
  Mercado Libre, que no tiene borradores, se crea y se pausa acto seguido
  (`create_product` lo hace y devuelve el status REAL — si la pausa falla, la ruta
  lo dice en el mensaje en vez de asumir). Es una decisión de producto: el usuario
  revisa antes de quedar expuesto al público.
- **Nunca borres productos con `DELETE` real.** Es soft delete: `is_active = False`.
  Y toda query de lectura filtra `is_active == True`.
- **Nunca dejes que la IA invente datos del producto.** Los prompts organizan y
  redactan la información que da el usuario; no agregan características.
- No metas secretos al repo: todo va por `.env` (hay `.env.example` como plantilla).

---

## Reglas de la capa de IA

Vive en `services/ai_service.py`. Decisiones que parecen arbitrarias pero no lo son:

- **Una llamada a Ollama por plataforma**, nunca todas juntas — el JSON se truncaba
  por límite de tokens.
- **Se manda un ESQUEMA en `format`, no `"json"` a secas** (`SCHEMAS` por
  plataforma). `format:"json"` solo garantiza sintaxis válida, no que vengan todos
  los campos: con descripciones largas el modelo se gastaba en `description_html`
  y cerraba el objeto sin `seo_title`, `seo_description` ni `tags` — JSON válido
  pero incompleto. El esquema hace que los `required` no sean opcionales. Si
  agregas un campo a un prompt, **agrégalo también al esquema** o llegará vacío.
- **`MAX_DESCRIPTION_CHARS = 4000`** limita la descripción de ENTRADA. Estuvo en 800
  y era un recorte silencioso: si el usuario escribía varios párrafos, todo lo que
  pasaba del carácter 800 se tiraba antes de llamar al modelo y la descripción
  "se encogía" sin aviso. Llama 3.2 tiene 128k de contexto — ese nunca fue el límite.
- **`num_ctx` y `num_predict` van explícitos** (`NUM_CTX`, `NUM_PREDICT` por
  plataforma). El default de Ollama cambia entre versiones; sin fijarlos, un prompt
  largo se recorta en silencio. Shopify necesita el triple que las otras porque
  genera HTML y las etiquetas consumen tokens.
- **Los prompts piden explícitamente descripciones largas.** Llama copia la *forma*
  del ejemplo de JSON que le das: si el esqueleto trae dos viñetas, devuelve dos
  viñetas por más material que le pases. Si acortas el ejemplo, acortas la salida.
- **Nunca metas una comilla doble en un ejemplo del prompt.** El modelo la copia y
  ahí mismo cierra la cadena JSON: un ejemplo con `1"` (pulgadas) hacía que el
  campo se cortara en el `1`. Para medidas se escribe "1 pulgada".
- **Los ejemplos del prompt se copian textual.** Usa siempre un producto distinto
  al del caso real en los ejemplos, o el modelo devuelve el contenido del ejemplo.
- **Formato del `seo_title`**: `Nombre | Descriptor con keyword + Gancho`, máx 70
  chars. El gancho (accesorio incluido, garantía, envío) **solo si la descripción
  del usuario lo respalda** — `_ajustar_seo_title()` valida palabra por palabra
  contra la descripción y borra el gancho si el modelo lo inventó. Ese método
  también recorta sin partir frases. Es determinista y está cubierto por
  `tests/test_ai_seo_title.py`; no dependas del prompt para esto.
- `temperature: 0.3` — más determinista, JSON más parseable.
- **El título de Shopify es sagrado**: se sobreescribe con el nombre exacto que
  escribió el usuario, sin importar lo que devuelva el modelo.
- **El título de ML es keyword, no eslogan**: `Producto + Marca + Modelo +
  característica más buscada`. Nada de "Nombre: la aventura empieza aquí" — cada
  palabra tiene que ser una que el comprador teclearía en el buscador. Y el ejemplo
  del prompt usa otro producto (una mochila), porque cuando usaba una GoPro el modelo
  copiaba el ejemplo y se comía palabras del nombre real.

**No propongas fine-tuning ni modelo propio.** Está evaluado y descartado por ahora
(el razonamiento completo está en `README.md`): sin usuarios no hay datos de
entrenamiento, y los pesos nunca fueron el diferenciador. Se reevalúa cuando haya
volumen de uso. Lo que sí aplica hoy es **no tirar los datos**: las correcciones que
el usuario hace sobre lo que generó la IA son el material de entrenamiento futuro.

Límites duros por plataforma (van en los prompts y hay que respetarlos):

| Plataforma | Título | Descripción | Extra |
|---|---|---|---|
| Shopify | máx 255 chars | HTML permitido | tags + SEO title/description |
| Mercado Libre | **máx 60 chars** | texto plano, sin HTML | keywords |
| Amazon | máx 200 chars | — | **exactamente** 5 bullet points |

---

## Convenciones

- **SKU**: único por usuario (constraint `unique_user_sku`), se normaliza a
  MAYÚSCULAS y solo admite `A-Z 0-9 - _`. La validación vive en
  `schemas/product_schema.py` — no la dupliques en las rutas.
- **Trazabilidad**: toda operación de sync/import registra un `SyncLog` vía
  `utils/log_helper.log_sync()`. Un fallo al guardar el log nunca debe tumbar la
  operación principal.
- **Errores de API**: `{'error': 'mensaje en español'}` con el status HTTP correcto.
  Los endpoints de plataformas además devuelven `success: true/false`.
- **Frontend**: toda llamada HTTP pasa por `services/api.js`. No uses `fetch` suelto
  en un componente — si falta un endpoint, agrégalo al service correspondiente.

---

## Comandos que no son obvios

```bash
# Backend — el venv vive dentro de backend/
cd backend && source venv/bin/activate
flask db upgrade        # OBLIGATORIO antes del primer arranque y tras cambiar modelos
flask db migrate -m "descripción"   # generar migración nueva
python -m pytest tests/ -q          # 83 tests

# Ollama tiene que estar corriendo para /api/ai/*
ollama list   # verificar; si no responde: ollama serve
```

`npm run lint` en el frontend **está roto**: el script y los plugins existen pero
no hay archivo de configuración de ESLint en el repo. Usa `npm run build` para
validar. No es una regresión.

---

## Pendientes conocidos

- `Product.amazon_id` existe en el modelo pero no hay integración con Amazon todavía.
- **Publicar es un botón por canal, no uno solo.** Shopify y ML ya funcionan desde
  la IA, pero el usuario tiene que apretar dos botones. "Un clic hace muchas cosas"
  pide un único "Publicar en todos mis canales".
- El `ai_generation_log` (guardar qué generó la IA y qué corrigió el usuario) no
  existe todavía. Es el material de entrenamiento futuro y hoy se está tirando.
