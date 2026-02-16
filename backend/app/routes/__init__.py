"""
VendeFlow - Rutas de la API
===========================
Exporta todos los blueprints de rutas.
"""

from app.routes import auth_routes
from app.routes import inventory_routes
from app.routes import import_routes
from app.routes import shopify_routes

__all__ = ['auth_routes', 'inventory_routes', 'import_routes', 'shopify_routes']
