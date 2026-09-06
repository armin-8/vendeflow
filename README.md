# 🚀 VendeFlow

> **La plataforma de e-commerce para emprendedores que están empezando**
> Tú decides qué vender y a qué precio. La operación la hace el software.

---

## 🎯 Para quién es

Para el emprendedor que está arrancando su e-commerce y **no tiene nada montado**:
ni catálogo, ni ERP, ni proceso. Que quiere vender en Shopify,Amazon. y Mercado Libre pero
se le van los días creando listings uno por uno, cuidando que el stock cuadre entre
canales y peleando con el admin de cada plataforma.

VendeFlow le da la base de datos de productos que no tiene y se encarga de la parte
operativa, para que él solo se dedique a lo que sí mueve el negocio: **qué vender, a
qué precio y con qué estrategia.**

```
                Un producto, un clic
                        ↓
        VendeFlow (tu base de datos + IA)
                        ↓
        Shopify · Mercado Libre · Amazon
             publicado en todos
```

**La promesa:** un clic hace muchas cosas. Generar el contenido optimizado para cada
canal, publicarlo en todos, y mantener el stock sincronizado sin que el usuario toque
nada.

### Por qué este cliente y no el otro

Una empresa establecida ya tiene un Odoo o un SAP siendo su fuente de verdad, y
entrar ahí significa pelear contra un sistema instalado. Un emprendedor que arranca
no tiene ninguno: **VendeFlow es su fuente de verdad desde el primer producto que
carga.** Entrada más fácil, permanencia más larga.

---

## 🏆 Hitos Logrados

```
3 Jul 2026 — PRIMER PRODUCTO PUBLICADO EN SHOPIFY CON IA 🎉
  → Usuario llena nombre, SKU, precio (2 min)
  → Llama 3.2 genera título, descripción HTML, tags, SEO (20 seg)
  → Producto creado en Shopify como borrador ✅
  → Ahorro: 48 minutos por producto
  → Un catálogo inicial de 30 productos: de 25 horas a 1 hora
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
| Testing | 83/83 tests pasando (pytest) | ✅ |
| Logs | Logs de sincronización con stats | ✅ |
| Migraciones | Flask-Migrate configurado | ✅ |
| V1.5 IA | Publicación en Shopify con IA (Llama 3.2 local) | ✅ 🎉 |
| V1.5 IA | Publicación en Mercado Libre con IA | ✅ 🎉 |
| V1.5 IA | Publicación en Amazon (SP-API) | 🟡 Pendiente |

### 🎯 Pendiente

| Feature | Descripción | Prioridad |
|---------|-------------|-----------|
| Onboarding | Conectar tiendas sin fricción técnica (hoy ML pide ngrok) | 🔴 Alta |
| Fase 6 | Integración Amazon | 🟡 Media |
| V2 Analytics | Dashboard de ventas con IA | 🟡 Media |
| V3 Chat | Asistente conversacional | 🟢 Baja |
| Odoo | Integración como fuente de verdad | ⚪️ Descartado por ahora |

> **Nota de prioridades.** El flujo ya publica en los dos canales que tenemos
> conectados: el usuario genera con IA y manda a Shopify y a Mercado Libre. Amazon
> baja de prioridad porque ni siquiera tiene OAuth todavía; el siguiente cuello de
> botella real es el onboarding.
>
> Falta cerrar el círculo de verdad: hoy son **dos botones**, uno por canal. "Un clic
> hace muchas cosas" es un solo botón que manda a todos lados a la vez.
>
> Odoo baja porque servía al cliente anterior (empresa con ERP instalado). El
> emprendedor que arranca no tiene ERP: la importación de Excel/CSV cubre el caso de
> "ya tengo una lista en algún lado" y el resto lo crea desde cero con IA.
>
> El onboarding sube porque este cliente no es técnico. Si el primer contacto con el
> producto es una pantalla pidiendo credenciales de API, lo perdemos antes de que vea
> la magia. Para este ICP, **el onboarding es el producto.**

---

## 🤖 Roadmap de IA

### Capa 1 — Publicación Multi-Canal (V1.5) 🟢 CASI
Usuario llena datos básicos → IA genera contenido optimizado → publica en todas las plataformas.

⚠️ **Falta el clic único.** Shopify y Mercado Libre ya reciben publicación desde la
IA, pero cada uno con su propio botón. El siguiente paso es un único "Publicar en
todos mis canales" — y Amazon, que todavía no tiene ni OAuth.

**Tecnología:** Llama 3.2 via Ollama (local, gratis, sin dependencias)

**Funcionando:**
- ✅ Shopify: título, descripción HTML, tags, SEO — publicación como borrador
- ✅ Mercado Libre: título máx 60 chars, descripción texto plano — publicación
  pausada, con la categoría deducida sola del título (el usuario nunca la elige)
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
- **Testing:** pytest + pytest-flask (83/83 ✅)

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
flask db upgrade   # crea/actualiza el esquema de la BD
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
│   │   ├── test_inventory.py           # 13 tests
│   │   ├── test_import.py              # 6 tests
│   │   └── test_oauth_state.py         # 11 tests
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
- **Llama 3.2 base, sin fine-tune todavía** → ver nota abajo
- **Una llamada por plataforma** → evita JSON truncado por límite de tokens
- **Tokens encriptados en BD** → seguridad en reposo
- **Flask-Migrate** → nunca más borrar la BD para cambiar modelos
- **Productos como borrador** → el usuario revisa antes de activar en Shopify
- **Refresh token automático en ML** → tokens duran 6h, se renuevan sin que el usuario note

### ¿Por qué no entrenamos nuestro propio modelo todavía?

Entrenar desde cero cuesta millones y daría un modelo **peor** que Llama 3.2 gratis.
La opción real es hacerle fine-tuning (LoRA) a un modelo abierto — corre en una
MacBook M2 Pro con `mlx-lm`, sale casi gratis y arreglaría de raíz los parches que
hoy tenemos: tener que generar una llamada por plataforma, y que el modelo necesite
instrucciones explícitas para no acortar las descripciones.

**Pero un fine-tune necesita datos que todavía no existen.** Los ejemplos buenos son
"así lo generó la IA / así lo corrigió el humano", y eso solo aparece con usuarios
reales usando el producto.

Además, el foso nunca fueron los pesos del modelo — esos cualquiera se los baja. El
foso es el dataset propio: qué títulos se editaron, qué publicaciones vendieron, qué
categoría de ML corresponde a qué producto en México.

**Decisión:** seguimos con Llama 3.2 base. Cuando haya volumen de uso, se reevalúa.
Mientras tanto, la prioridad es **empezar a guardar esos datos desde ya** — hoy las
correcciones del usuario en `Publish.jsx` se tiran a la basura, y son justamente el
material de entrenamiento del futuro.

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

*Última actualización: 9 Agosto 2026 — Reposicionamiento: el cliente es el emprendedor que arranca*
