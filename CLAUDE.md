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

---

## Prohibiciones

- **Nunca `db.create_all()`** en código de aplicación. El esquema lo maneja
  Flask-Migrate; `create_all()` crea tablas por su cuenta y deja las migraciones
  fuera de sincronía. (Los tests sí lo usan, en `conftest.py`, contra una BD
  desechable — eso está bien.)
- **Nunca publiques productos activos en Shopify.** Siempre `status: draft`, para
  que el usuario revise en su admin antes de publicar. Es una decisión de
  producto, no un detalle técnico.
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
- **La descripción se recorta a 800 chars** (`MAX_DESCRIPTION_CHARS`) para que
  Llama 3.2 alcance a cerrar el JSON.
- `temperature: 0.3` — más determinista, JSON más parseable.
- **El título de Shopify es sagrado**: se sobreescribe con el nombre exacto que
  escribió el usuario, sin importar lo que devuelva el modelo.

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
python -m pytest tests/ -q          # 40 tests

# Ollama tiene que estar corriendo para /api/ai/*
ollama list   # verificar; si no responde: ollama serve
```

`npm run lint` en el frontend **está roto**: el script y los plugins existen pero
no hay archivo de configuración de ESLint en el repo. Usa `npm run build` para
validar. No es una regresión.

---

## Pendientes conocidos

- `Product.amazon_id` existe en el modelo pero no hay integración con Amazon todavía.
- Publicar en Mercado Libre desde la IA es lo siguiente del roadmap: los prompts de
  ML ya están en `ai_service.py`, falta el endpoint `create-product` equivalente al
  de Shopify.
