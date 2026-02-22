"""
VendeFlow - Inicialización de la Aplicación
============================================
Este archivo crea y configura la aplicación Flask.
Usa el patrón "Application Factory" para mayor flexibilidad.
"""

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from app.config import get_config

# Inicializar extensiones sin app (se conectan después)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_class=None):
    """
    Application Factory - Crea y configura la aplicación Flask.
    """
    
    # Crear la aplicación Flask
    app = Flask(__name__)
    
    # Cargar configuración
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)
    
    # Inicializar extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Configurar CORS (permitir cookies/credentials para OAuth)
    CORS(app, 
         resources={r"/api/*": {"origins": [app.config['FRONTEND_URL']]}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # ═══════════════════════════════════════════════════════════
    # REGISTRAR BLUEPRINTS (RUTAS)
    # ═══════════════════════════════════════════════════════════
    
    from app.routes import auth_routes, inventory_routes, import_routes, shopify_routes
    
    app.register_blueprint(auth_routes.bp)        # /api/auth/*
    app.register_blueprint(inventory_routes.bp)   # /api/inventory/*
    app.register_blueprint(import_routes.bp)      # /api/import/*
    app.register_blueprint(shopify_routes.bp)     # /api/shopify/*
    
    # Ruta de health check
    @app.route('/api/health')
    def health_check():
        return {'status': 'ok', 'message': 'VendeFlow API is running'}
    
    # Importar modelos y crear tablas en desarrollo
    with app.app_context():
        from app.models import User, Product, PlatformConnection
        db.create_all()
    
    return app
