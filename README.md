# 🚀 VendeFlow

> **El hub de e-commerce más inteligente de LATAM**
> Conecta cualquier ERP con cualquier plataforma de venta. La IA se encarga de la operación, tú tomas las decisiones clave.

---

## 🎯 Problema que resuelve

Los e-commerce managers en LATAM pierden horas sincronizando inventario manualmente entre sistemas y creando listings para cada plataforma. VendeFlow lo automatiza con IA.

```
Odoo / SAP / Excel
       ↓
   VendeFlow (Hub inteligente con IA)
       ↓
Shopify / Mercado Libre / Amazon
```

---

## 🏆 Hitos Logrados

```
3 Jul 2026 — PRIMER PRODUCTO PUBLICADO EN SHOPIFY CON IA 🎉
  → Usuario llena nombre, SKU, precio (2 min)
  → Llama 3.2 genera título, descripción HTML, tags, SEO (20 seg)
  → Producto creado en Shopify como borrador ✅
  → Ahorro: 48 minutos por producto
  → Con 100 productos/mes → 80 horas ahorradas
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
| V1.5 IA | Publicación en Shopify con IA (Llama 3.2 local) | ✅ 🎉 |

### 🎯 Pendiente

| Feature | Descripción | Prioridad |
|---------|-------------|-----------|
| V1.5 IA ML | Publicar en Mercado Libre desde IA | 🔴 Alta |
| Fase 6 | Integración Amazon | 🟡 Media |
| V2 Analytics | Dashboard de ventas con IA | 🟡 Media |
| Odoo | Integración como fuente de verdad | 🟡 Media |
| V3 Chat | Asistente conversacional | 🟢 Baja |

---

## 🤖 Roadmap de IA

### Capa 1 — Publicación Multi-Canal (V1.5) ✅ ACTIVA
Usuario llena datos básicos → IA genera contenido optimizado → publica en todas las plataformas.

**Tecnología:** Llama 3.2 via Ollama (local, gratis, sin dependencias)

**Funcionando:**
- ✅ Shopify: título, descripción HTML, tags, SEO — publicación como borrador
- 🔜 Mercado Libre: título máx 60 chars, descripción texto plano
- 🔜 Amazon: 5 bullet points, backend keywords

**Impacto:**
```
Sin IA:    50 min por producto
Con IA:     2 min por producto
Ahorro:    96% del tiempo ✅
```

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
- **IA:** Llama 3.2 via Ollama (local, gratis)
- **Testing:** pytest + pytest-flask (23/23 ✅)

### Frontend
- **Framework:** React + Vite
- **Estilos:** Tailwind CSS
- **Estado:** Zustand
- **HTTP:** Fetch API centralizado en api.js

### Integraciones
- **Shopify:** OAuth 2.0 + REST API + publicación con IA ✅
- **Mercado Libre:** OAuth 2.0 + refresh token automático ✅
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
# Ollama arranca automáticamente con el Mac
# Verificar que está corriendo:
ollama list

# Si no está corriendo:
ollama serve
```

### Variables de entorno (.env)
```bash
FLASK_APP=run.py
FLASK_DEBUG=1
SECRET_KEY=tu-secret-key
JWT_SECRET_KEY=tu-jwt-secret-key
DATABASE_URL=sqlite:///vendeflow_dev.db
FRONTEND_URL=http://localhost:5173
SHOPIFY_API_KEY=tu-shopify-api-key
SHOPIFY_API_SECRET=tu-shopify-api-secret
SHOPIFY_REDIRECT_URI=http://localhost:5001/api/shopify/callback
MERCADOLIBRE_APP_ID=tu-ml-app-id
MERCADOLIBRE_SECRET_KEY=tu-ml-secret-key
MERCADOLIBRE_REDIRECT_URI=https://tu-ngrok-url/api/mercadolibre/callback
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
│   │   │   ├── shopify_routes.py       # + create-product IA
│   │   │   ├── mercadolibre_routes.py
│   │   │   ├── ai_routes.py            # /api/ai/*
│   │   │   └── logs_routes.py
│   │   ├── services/
│   │   │   ├── shopify_service.py      # + create_product()
│   │   │   ├── mercadolibre_service.py
│   │   │   └── ai_service.py           # Llama 3.2 via Ollama
│   │   └── utils/
│   │       ├── encryption.py           # Fernet AES-128
│   │       └── log_helper.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py                # 10 tests
│   │   └── test_inventory.py           # 13 tests
│   ├── migrations/
│   └── scripts/
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Inventory.jsx
│       │   ├── Integrations.jsx
│       │   ├── Import.jsx
│       │   └── Publish.jsx             # IA → Shopify ✅
│       ├── components/
│       │   ├── ProductTable.jsx        # Botón sync por SKU
│       │   └── Navbar.jsx
│       └── services/
│           └── api.js
└── README.md
```

---

## 🔐 Seguridad

- Tokens de Shopify y ML encriptados con **Fernet AES-128** en la BD
- JWT para autenticación de rutas protegidas
- Variables sensibles solo en `.env`
- GitHub Push Protection activado
- Productos siempre como **borrador** antes de publicar

---

## 📋 Requisitos de Publicación por Plataforma

| Plataforma | Título | Descripción | Notas |
|------------|--------|-------------|-------|
| Shopify | Máx 255 chars | HTML permitido | Publicación IA ✅ |
| Mercado Libre | **Máx 60 chars** ⚠️ | Texto plano, sin HTML | Próximamente |
| Amazon | Máx 200 chars | 5 bullet points | Próximamente |

---

## 📝 Decisiones Técnicas

- **Ollama en lugar de Anthropic API** → gratis, local, sin dependencias
- **Una llamada por plataforma** → evita JSON truncado por límite de tokens
- **Tokens encriptados en BD** → seguridad en reposo
- **Flask-Migrate** → nunca más borrar la BD para cambiar modelos
- **Productos como borrador** → el usuario revisa antes de activar en Shopify
- **Refresh token automático en ML** → tokens duran 6h, se renuevan sin que el usuario note

## 🐛 Problemas Resueltos

- ML no acepta `localhost` → usar ngrok para desarrollo
- JSON truncado en Ollama → generar por plataforma, no todo junto
- Tokens en texto plano → Fernet AES-128
- BD se rompía al agregar columnas → Flask-Migrate

---

## 👨‍💻 Equipo

- **Armin Pérez** — Founder & E-commerce Manager
- **VendeFlow** — Startup enfocada en e-commerce LATAM

---

*Última actualización: 3 Julio 2026 — Primer producto publicado en Shopify con IA 🎉*
