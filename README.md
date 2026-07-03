# 🚀 VendeFlow

> **El hub de e-commerce más inteligente de LATAM**
> Conecta cualquier ERP con cualquier plataforma de venta. La IA se encarga de la operación, tú tomas las decisiones clave.

---

## 🎯 Problema que resuelve

Los e-commerce managers en LATAM pierden horas sincronizando inventario manualmente entre sistemas y creando listings para cada plataforma. VendeFlow lo automatiza con IA.

```
Odoo / SAP / Excel
       ↓
   VendeFlow (Hub inteligente)
       ↓
Shopify / Mercado Libre / Amazon
```

---

## 📊 Estado del Proyecto

### ✅ Completado

| Fase | Descripción | Estado |
|------|-------------|--------|
| Fase 1 | Setup + Auth (JWT, registro, login) | ✅ |
| Fase 2 | CRUD Inventario completo | ✅ |
| Fase 3 | Importación Excel/CSV | ✅ |
| Fase 4 | Integración Shopify (OAuth + sync) | ✅ |
| Fase 5 | Integración Mercado Libre (OAuth + refresh token) | ✅ |
| Seguridad | Encriptación de tokens en BD (Fernet AES-128) | ✅ |
| Testing | 23/23 tests pasando (pytest) | ✅ |
| Logs | Logs de sincronización con stats | ✅ |
| Migraciones | Flask-Migrate configurado | ✅ |
| V1.5 IA | Publicación multi-canal con Llama 3.2 (Ollama) | ✅ |

### 🎯 Pendiente

| Feature | Descripción | Prioridad |
|---------|-------------|-----------|
| Botón Publicar | Conectar "Publicar" con Shopify y ML | 🔴 Alta |
| Fase 6 | Integración Amazon | 🟡 Media |
| V2 Analytics | Dashboard de ventas con IA | 🟡 Media |
| Odoo | Integración como fuente de verdad | 🟡 Media |
| V3 Chat | Asistente conversacional | 🟢 Baja |

---

## 🤖 Roadmap de IA

### Capa 1 — Publicación Multi-Canal (V1.5) ✅
Usuario sube producto → IA genera contenido optimizado → publica en todas las plataformas con 1 click.

**Tecnología:** Llama 3.2 via Ollama (local, gratis, sin dependencias)

### Capa 2 — Analytics Inteligente (V2) 🔜
```
Datos de ventas + inventario → IA analiza → insights en lenguaje natural

Ejemplos:
- "Tus ventas suben 40% los domingos en ML"
- "Te quedas sin stock del SKU H8-1016-PROT en 8 días"
- "Tu ticket en Shopify es 35% mayor que en ML"
```

### Capa 3 — Asistente Conversacional (V3) 🔜
Chat dentro de VendeFlow para consultas en lenguaje natural sobre inventario y ventas.

---

## 🛠️ Stack Tecnológico

### Backend
- **Framework:** Flask 3.1 (Python 3.13)
- **Base de datos:** SQLite (dev) / PostgreSQL (prod)
- **ORM:** SQLAlchemy + Flask-Migrate
- **Auth:** JWT (flask-jwt-extended)
- **Seguridad:** Fernet AES-128 (cryptography)
- **IA:** Llama 3.2 via Ollama (local)
- **Testing:** pytest + pytest-flask

### Frontend
- **Framework:** React + Vite
- **Estilos:** Tailwind CSS
- **Estado:** Zustand
- **HTTP:** Fetch API centralizado en api.js

### Integraciones
- **Shopify:** OAuth 2.0 + REST API
- **Mercado Libre:** OAuth 2.0 + refresh token automático
- **Amazon:** Próximamente (SP-API)

---

## 🚀 Arranque del Proyecto

### Requisitos
- Python 3.13+
- Node.js 18+
- Ollama instalado con modelo `llama3.2:latest`

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### IA (Ollama)
```bash
# Verificar que Ollama está corriendo
ollama list

# Si no está corriendo
ollama serve
```

### Variables de entorno (.env)
```bash
# Flask
FLASK_APP=run.py
FLASK_DEBUG=1
SECRET_KEY=tu-secret-key

# JWT
JWT_SECRET_KEY=tu-jwt-secret-key

# Database
DATABASE_URL=sqlite:///vendeflow_dev.db

# CORS
FRONTEND_URL=http://localhost:5173

# Shopify OAuth
SHOPIFY_API_KEY=tu-shopify-api-key
SHOPIFY_API_SECRET=tu-shopify-api-secret
SHOPIFY_REDIRECT_URI=http://localhost:5001/api/shopify/callback

# Mercado Libre OAuth
MERCADOLIBRE_APP_ID=tu-ml-app-id
MERCADOLIBRE_SECRET_KEY=tu-ml-secret-key
MERCADOLIBRE_REDIRECT_URI=https://tu-ngrok-url/api/mercadolibre/callback

# Seguridad
ENCRYPTION_KEY=tu-fernet-key
```

---

## 📁 Estructura del Proyecto

```
vendeflow/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── platform_connection.py  # Tokens encriptados
│   │   │   └── sync_log.py
│   │   ├── routes/
│   │   │   ├── auth_routes.py
│   │   │   ├── inventory_routes.py
│   │   │   ├── shopify_routes.py
│   │   │   ├── mercadolibre_routes.py
│   │   │   ├── ai_routes.py            # IA endpoints
│   │   │   └── logs_routes.py
│   │   ├── services/
│   │   │   ├── shopify_service.py
│   │   │   ├── mercadolibre_service.py
│   │   │   └── ai_service.py           # Llama 3.2 via Ollama
│   │   └── utils/
│   │       ├── encryption.py           # Fernet AES-128
│   │       └── log_helper.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py                # 10 tests
│   │   └── test_inventory.py           # 13 tests
│   ├── migrations/                     # Flask-Migrate
│   └── scripts/
│       ├── encrypt_existing_tokens.py
│       └── vincular_ml.py
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Inventory.jsx
│       │   ├── Integrations.jsx
│       │   ├── Import.jsx
│       │   └── Publish.jsx             # IA publicación
│       ├── components/
│       │   ├── ProductTable.jsx        # Botón sync por SKU
│       │   └── Navbar.jsx
│       └── services/
│           └── api.js                  # Servicios centralizados
└── README.md
```

---

## 🔐 Seguridad

- Tokens de Shopify y ML encriptados con **Fernet AES-128** en la BD
- JWT para autenticación de rutas protegidas
- Variables sensibles solo en `.env` (nunca en el código)
- GitHub Push Protection activado

---

## 📋 Requisitos de Publicación por Plataforma

| Plataforma | Título | Descripción | Imágenes |
|------------|--------|-------------|----------|
| Shopify | Máx 255 chars | HTML permitido | JPG/PNG |
| Mercado Libre | **Máx 60 chars** ⚠️ | Texto plano, sin HTML | Mín 500x500px |
| Amazon | Máx 200 chars | 5 bullet points | Fondo blanco obligatorio |

---

## 👨‍💻 Equipo

- **Armin Pérez** — Founder & E-commerce Manager
- **VendeFlow** — Startup enfocada en e-commerce LATAM

---

## 📝 Notas de Desarrollo

### Decisiones técnicas importantes
- **Ollama en lugar de Anthropic API** → gratis, local, sin dependencias externas
- **Una llamada por plataforma** → evita JSON truncado por límite de tokens
- **Tokens encriptados en BD** → seguridad en reposo
- **Flask-Migrate** → nunca más borrar la BD para cambiar modelos
- **SyncButton independiente por fila** → cada producto tiene su propio estado de loading
- **Refresh token automático en ML** → tokens duran 6h, se renuevan sin que el usuario note

### Problemas resueltos
- ML no acepta `localhost` → usar ngrok para desarrollo
- JSON truncado en Ollama → generar por plataforma, no todo junto
- Tokens en texto plano → Fernet AES-128
- BD se rompía al agregar columnas → Flask-Migrate

---

*Última actualización: Julio 2026*
