# 🚀 VendeFlow

**Plataforma centralizada de gestión de inventario multi-canal para e-commerce en LATAM.**

## 📋 Descripción

VendeFlow permite a vendedores gestionar su inventario desde un solo lugar y sincronizarlo automáticamente con múltiples marketplaces: Shopify, Amazon y Mercado Libre.

## 🎯 Funcionalidades MVP

- [ ] Autenticación de usuarios (Registro/Login)
- [ ] CRUD de productos (inventario propio)
- [ ] Importación desde Excel/CSV
- [ ] Conexión con Shopify
- [ ] Conexión con Mercado Libre
- [ ] Conexión con Amazon
- [ ] Dashboard de inventario
- [ ] Alertas de stock bajo

## 🛠️ Stack Tecnológico

### Frontend
- React 18
- Vite
- React Router 6
- Tailwind CSS
- Zustand (estado global)

### Backend
- Flask 3.0
- SQLAlchemy 2.0
- Flask-JWT-Extended
- PostgreSQL
- Celery + Redis (futuro)

## 📁 Estructura del Proyecto

```
vendeflow/
├── backend/
│   ├── app/
│   │   ├── models/          # Modelos SQLAlchemy
│   │   ├── schemas/         # Validación con Pydantic
│   │   ├── services/        # Lógica de negocio
│   │   ├── routes/          # Endpoints API
│   │   └── utils/           # Utilidades
│   ├── tests/               # Tests con pytest
│   ├── requirements.txt
│   └── run.py
│
├── frontend/
│   ├── src/
│   │   ├── components/      # Componentes reutilizables
│   │   ├── pages/           # Páginas/Vistas
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/        # Llamadas API
│   │   ├── store/           # Estado global (Zustand)
│   │   └── utils/           # Utilidades
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## 🚀 Instalación

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
flask run
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 👨‍💻 Autor

Desarrollado por Armin Pérez Sánchez

## 📄 Licencia

Este proyecto es privado y de uso personal.
